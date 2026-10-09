/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useRef, useState } from 'react';
import { Header } from './components/Header';
import { LandingHero } from './components/LandingHero';
import { PipelineAnimation } from './components/PipelineAnimation';
import { VerdictBanner } from './components/VerdictBanner';
import { InvestigationSequenceFlow } from './components/InvestigationSequenceFlow';
import { AnalysisCardsGrid } from './components/AnalysisCardsGrid';
import { EvidenceBattle } from './components/EvidenceBattle';
import { EvidenceGraph } from './components/EvidenceGraph';
import { ExplainableReasoning } from './components/ExplainableReasoning';
import { EvidenceTimeline } from './components/EvidenceTimeline';
import { ReportModal } from './components/ReportModal';
import { LiveEvidencePanels, StatusNotices } from './components/LiveEvidencePanels';
import { MediaInspectionModal } from './components/MediaInspectionModal';
import ShortsAnalyzer from './pages/ShortsDemo';
import { DEMO_CASE, INITIAL_PIPELINE_STAGES, LIVE_PIPELINE_STAGES } from './data/demoCase';
import { buildLiveInvestigation } from './data/buildLiveInvestigation';
import { runInvestigation } from './services/investigationApi';
import { InvestigationData } from './types/investigation';

type AppState = 'landing' | 'pipeline' | 'results' | 'shorts';

// Shorts Analyzer lives inside this app. Deep link: #shorts-analyzer (legacy /shorts-demo still opens it).
const SHORTS_HASH = '#shorts-analyzer';
const wantsShorts = () =>
  window.location.hash === SHORTS_HASH || window.location.pathname.replace(/\/+$/, '') === '/shorts-demo';

export default function App() {
  const [appState, setAppState] = useState<AppState>(() => (wantsShorts() ? 'shorts' : 'landing'));
  const [claim, setClaim] = useState<string>('');
  const [mediaName, setMediaName] = useState<string>('');
  const [url, setUrl] = useState<string>('');
  const [isDemoPopulated, setIsDemoPopulated] = useState<boolean>(false);
  const [investigationData, setInvestigationData] = useState<InvestigationData>(DEMO_CASE);
  const [isLiveRun, setIsLiveRun] = useState<boolean>(false);
  const [isResultReady, setIsResultReady] = useState<boolean>(true);
  const [activeClaim, setActiveClaim] = useState<string>('');
  const requestId = useRef<number>(0);

  // Modals
  const [isReportOpen, setIsReportOpen] = useState<boolean>(false);
  const [isMediaModalOpen, setIsMediaModalOpen] = useState<boolean>(false);

  // Keep the Shorts Analyzer view in sync with browser back/forward and hash links.
  useEffect(() => {
    const sync = () => setAppState((s) => (wantsShorts() ? 'shorts' : s === 'shorts' ? 'landing' : s));
    window.addEventListener('hashchange', sync);
    window.addEventListener('popstate', sync);
    return () => {
      window.removeEventListener('hashchange', sync);
      window.removeEventListener('popstate', sync);
    };
  }, []);

  const handleOpenShorts = () => {
    requestId.current++; // discard any pending investigation result
    if (window.location.pathname !== '/') window.history.replaceState(null, '', '/');
    window.location.hash = SHORTS_HASH;
    setAppState('shorts');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // User clicks "TRY DEMO CASE"
  const handlePopulateDemo = () => {
    setClaim("This video shows today’s flood in Bengaluru.");
    setMediaName("FLOOD_VIDEO_DEMO.mp4");
    setUrl("youtube.com/shorts/demo-flood-video");
    setIsDemoPopulated(true);
  };

  // User edits the inputs: leave demo mode so custom input never reuses DEMO_CASE
  const handleClaimChange = (val: string) => {
    setClaim(val);
    setIsDemoPopulated(false);
  };
  const handleUrlChange = (val: string) => {
    setUrl(val);
    setIsDemoPopulated(false);
  };

  // User starts investigation
  const handleStartInvestigation = (
    claimText: string,
    media?: string,
    targetUrl?: string,
    isDemo?: boolean,
    file?: File | null
  ) => {
    const id = ++requestId.current;
    setActiveClaim(claimText);

    if (isDemo) {
      // Demo data is used ONLY when the user explicitly clicked TRY DEMO CASE.
      setIsLiveRun(false);
      setInvestigationData(DEMO_CASE);
      setIsResultReady(true);
    } else {
      setIsLiveRun(true);
      setIsResultReady(false);
      const submittedAt = new Date().toISOString();
      runInvestigation(claimText, targetUrl ?? '', file).then((result) => {
        if (id !== requestId.current) return; // user reset while waiting
        setInvestigationData(buildLiveInvestigation(result, submittedAt));
        setIsResultReady(true);
      });
    }
    setAppState('pipeline');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Pipeline animation finishes
  const handlePipelineComplete = () => {
    setAppState('results');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Reset back to landing
  const handleReset = () => {
    requestId.current++;
    if (wantsShorts()) window.history.replaceState(null, '', '/');
    setAppState('landing');
    setClaim('');
    setMediaName('');
    setUrl('');
    setIsDemoPopulated(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateSection = (sectionId: string) => {
    if (appState !== 'results') {
      return;
    }
    const elem = document.getElementById(sectionId);
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#070B12] text-slate-100 flex flex-col font-sans">
      {/* Top Bar Navigation */}
      <Header
        onReset={handleReset}
        onOpenReport={() => setIsReportOpen(true)}
        hasActiveCase={appState === 'results'}
        onNavigateSection={handleNavigateSection}
        onOpenShorts={handleOpenShorts}
        isShortsActive={appState === 'shorts'}
      />

      {/* Main Content Areas */}
      <main className="flex-1">
        {appState === 'shorts' && <ShortsAnalyzer />}

        {appState === 'landing' && (
          <LandingHero
            claim={claim}
            setClaim={handleClaimChange}
            mediaName={mediaName}
            setMediaName={setMediaName}
            url={url}
            setUrl={handleUrlChange}
            isDemoPopulated={isDemoPopulated}
            onPopulateDemo={handlePopulateDemo}
            onInvestigate={handleStartInvestigation}
          />
        )}

        {appState === 'pipeline' && (
          <PipelineAnimation
            stages={isLiveRun ? LIVE_PIPELINE_STAGES : INITIAL_PIPELINE_STAGES}
            onComplete={handlePipelineComplete}
            caseClaim={activeClaim}
            isReady={isResultReady}
          />
        )}

        {appState === 'results' && (
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 space-y-12">
            
            {/* The Paradigm Banner & Investigation Sequence Flow (Requirements 2 & 10) */}
            <InvestigationSequenceFlow />

            {/* Live runs only: honest backend/search/provider status notices */}
            {investigationData.live && !investigationData.isDemo && (
              <StatusNotices live={investigationData.live} />
            )}

            {/* Primary Verdict Banner */}
            <VerdictBanner
              data={investigationData}
              onOpenReport={() => setIsReportOpen(true)}
              onOpenMediaModal={() => setIsMediaModalOpen(true)}
            />

            {/* Six-Pillar Analysis Cards */}
            <AnalysisCardsGrid
              cards={investigationData.cards}
              submittedUrl={investigationData.url}
              isDemo={investigationData.isDemo}
              onInspectMedia={investigationData.isDemo ? () => setIsMediaModalOpen(true) : undefined}
            />

            {/* Live runs only: image text, web source reliability, evidence provenance (real backend data) */}
            {investigationData.live && !investigationData.isDemo && (
              <LiveEvidencePanels live={investigationData.live} />
            )}

            {/* Dialectical Evidence Battle */}
            <EvidenceBattle
              battleData={investigationData.battle}
            />

            {/* Interactive Directed Evidence Graph */}
            <EvidenceGraph
              nodes={investigationData.graph.nodes}
              edges={investigationData.graph.edges}
            />

            {/* Explainable Reasoning 7-Step Chain */}
            <ExplainableReasoning
              steps={investigationData.reasoningSteps}
              verdictStatus={investigationData.verdict.status}
              confidence={investigationData.verdict.confidence}
              isDemo={investigationData.isDemo}
              finalReasoning={investigationData.verdict.finalReasoning}
              whyNotGenuine={investigationData.verdict.whyNotGenuine}
              whyNotHighRisk={investigationData.verdict.whyNotHighRisk}
            />

            {/* Chronological Evidence Timeline */}
            <EvidenceTimeline
              timeline={investigationData.timeline}
              isDemo={investigationData.isDemo}
            />

            {/* Bottom Final Action Section */}
            <div className="rounded-2xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-950 p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-2xl">
              <div>
                <span className="text-xs font-mono font-bold tracking-widest text-cyan-400 uppercase">
                  Investigation Complete
                </span>
                <h3 className="text-xl font-bold text-white font-display mt-0.5">
                  Export Evidence Investigation Report
                </h3>
                <p className="text-xs text-slate-400 mt-1 max-w-xl">
                  Download a report with the claim, retrieved findings, evidence for and against, and the reasoning behind the verdict. Includes a SHA-256 hash of the report text.
                </p>
              </div>

              <button
                onClick={() => setIsReportOpen(true)}
                className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 px-6 py-3 text-xs font-bold uppercase tracking-wider text-black hover:from-cyan-300 hover:to-blue-400 shadow-[0_0_25px_rgba(6,182,212,0.4)] transition-all cursor-pointer whitespace-nowrap"
              >
                <span>GENERATE INVESTIGATION REPORT</span>
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-[#050811] py-8 text-center text-xs text-slate-500 font-mono">
        <div className="mx-auto max-w-7xl px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-300">TRUSTLENS</span>
            <span>·</span>
            <span>Digital Evidence Investigation Engine</span>
          </div>
          <div>
            “Don’t just detect fake content. Investigate the evidence behind it.”
          </div>
        </div>
      </footer>

      {/* Modals */}
      <ReportModal
        data={investigationData}
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
      />

      <MediaInspectionModal
        isOpen={isMediaModalOpen && investigationData.isDemo}
        onClose={() => setIsMediaModalOpen(false)}
        mediaName={investigationData.mediaName}
      />
    </div>
  );
}
