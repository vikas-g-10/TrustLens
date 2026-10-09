import React, { useEffect, useMemo, useState } from 'react';
import { 
  X, 
  Copy, 
  Check, 
  Download, 
  Printer, 
  FileText, 
  ShieldCheck, 
  AlertTriangle,
  Lock,
  ExternalLink
} from 'lucide-react';
import { InvestigationData } from '../types/investigation';
import { buildReportMarkdown, sha256Hex } from '../lib/report';
import { verdictTheme } from '../lib/verdictTheme';

interface ReportModalProps {
  data: InvestigationData;
  isOpen: boolean;
  onClose: () => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({ data, isOpen, onClose }) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [hash, setHash] = useState<string | null>(null);
  const generatedAt = useMemo(() => new Date().toISOString(), [data, isOpen]);
  const reportBody = useMemo(() => buildReportMarkdown(data, generatedAt), [data, generatedAt]);
  const theme = verdictTheme(data.verdict.status);
  const statusLabel = data.verdict.status.replace('_', ' ');
  const urlCard = data.cards.find((c) => c.id === 'url_security');
  const mediaCard = data.cards.find((c) => c.id === 'media_forensics');

  useEffect(() => {
    let cancelled = false;
    setHash(null);
    sha256Hex(reportBody).then((h) => { if (!cancelled) setHash(h); });
    return () => { cancelled = true; };
  }, [reportBody]);

  if (!isOpen) return null;

  const markdownReport = `${reportBody}\n\n---\nSHA-256 of the report text above: ${hash ?? 'unavailable (secure context required)'}\n`;

  const handleCopy = () => {
    navigator.clipboard.writeText(markdownReport);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownload = () => {
    const blob = new Blob([markdownReport], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `TrustLens_${data.caseId}_Report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md overflow-y-auto animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden my-8">
        
        {/* Modal Top Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-950 border border-cyan-500/40 text-cyan-400">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
                INVESTIGATION DOSSIER: {data.caseId}
              </h3>
              <span className="text-[10px] text-amber-400 font-mono">
                {data.isDemo ? 'DEMO INVESTIGATION · SIMULATED ANALYSIS' : 'LIVE URL INVESTIGATION'} · EVIDENCE INVESTIGATION REPORT
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Content - Printable Dossier */}
        <div className="p-6 sm:p-8 space-y-6 max-h-[70vh] overflow-y-auto font-sans text-slate-200">
          
          {/* Executive Summary Card */}
          <div className={`rounded-xl border p-5 space-y-3 ${theme.whyBox}`}>
            <div className={`flex flex-wrap items-center justify-between gap-2 border-b pb-3 ${theme.headerBorder}`}>
              <span className={`text-xs font-mono font-bold uppercase tracking-wider ${theme.headerText}`}>
                EXECUTIVE DETERMINATION
              </span>
              <span className={`text-sm font-black font-display ${theme.whyTitle}`}>
                {statusLabel} ({data.verdict.confidence}% Confidence)
              </span>
            </div>
            <p className="text-sm sm:text-base font-medium text-slate-100">
              “{data.verdict.mainExplanation}”
            </p>
          </div>

          {/* Target Metadata Block */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
            <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
              <span className="text-cyan-400 font-bold block text-[10px] uppercase">CLAIM</span>
              <span className="text-slate-200 font-sans font-medium mt-1 block">
                “{data.claim}”
              </span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
              <span className="text-slate-400 block text-[10px] uppercase">{data.isDemo ? 'DEMO MEDIA (SIMULATED)' : 'MEDIA'}</span>
              <span className="text-cyan-400 font-bold mt-1 block truncate">
                {data.mediaName}
              </span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
              <span className="text-rose-400 font-bold block text-[10px] uppercase">SUBMITTED URL</span>
              <span className="text-cyan-400 font-bold mt-1 block truncate">
                {data.url}
              </span>
            </div>
          </div>

          {/* Section: Media & URL Findings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-2">
              <span className="text-xs font-mono font-bold text-cyan-400 block">
                MEDIA FORENSICS FINDINGS
              </span>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {(mediaCard?.summaryItems ?? []).map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-cyan-400">•</span>
                    <span>{item.text}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-2">
              <span className="text-xs font-mono font-bold text-red-400 block">
                URL SECURITY AUDIT
              </span>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {(urlCard?.summaryItems ?? []).map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-red-400">•</span>
                    <span>{item.text}</span>
                  </li>
                ))}
              </ul>
              {(data.isDemo || (urlCard?.summaryItems ?? []).some(i => /tracking/i.test(i.text))) && (
                <p className="text-[10px] text-slate-500 font-mono pt-1">
                  * Note: Potential tracking behavior detected. Actual data collection could not be independently verified.
                </p>
              )}
            </div>
          </div>

          {/* Section: Battle Synthesis */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-mono font-bold text-slate-200">
                EVIDENCE BALANCE & COUNTER-EVIDENCE
              </span>
              <span className={`text-xs font-mono ${theme.headerText}`}>
                {data.battle.supportingCount} Supporting vs {data.battle.challengingCount} Challenging
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <strong className="text-emerald-400 font-mono block mb-1">
                  Corroborating Elements:
                </strong>
                <ul className="space-y-1 text-slate-300">
                  {data.battle.supporting.length === 0 && <li>• Insufficient evidence</li>}
                  {data.battle.supporting.map(s => (
                    <li key={s.id}>• {s.claimPoint} ({s.source})</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong className="text-red-400 font-mono block mb-1">
                  Challenging / Contradicting Evidence:
                </strong>
                <ul className="space-y-1 text-slate-300">
                  {data.battle.challenging.length === 0 && <li>• Insufficient evidence</li>}
                  {data.battle.challenging.map(c => (
                    <li key={c.id}>• {c.claimPoint} ({c.source})</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Section: Source Independence */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-1.5">
            <span className="text-xs font-mono font-bold text-amber-400 block">
              SOURCE INDEPENDENCE AUDIT
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">
              {data.isDemo
                ? '(Simulated) Lineage cluster analysis reveals that multiple circulating accounts are mere retweets of a single unverified social upload. Superficial syndication does not equal independent corroboration.'
                : 'Unavailable. Only the submitted page was examined, so source independence could not be assessed.'}
            </p>
          </div>

          {/* Section: Reasoning */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-2 text-xs">
            <span className="font-mono font-bold text-cyan-400 block">
              REASONING SYNTHESIS
            </span>
            <div className="space-y-1.5 text-slate-300">
              <p><strong>Why Not Genuine:</strong> {data.verdict.whyNotGenuine}</p>
              <p><strong>Why Not High Risk:</strong> {data.verdict.whyNotHighRisk}</p>
              <p><strong>Final Reasoning:</strong> {data.verdict.finalReasoning}</p>
            </div>
          </div>

          {/* Report integrity footer */}
          <div className="rounded-xl border border-slate-800 bg-[#040813] p-4 font-mono text-[11px] text-slate-500 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-400">
              <Lock className="h-3.5 w-3.5 text-cyan-500" />
              <span>REPORT INTEGRITY HASH</span>
            </div>
            <div className="break-all">SHA-256 of report text: <span className="text-slate-400">{hash ?? 'Unavailable (secure context required)'}</span></div>
            <div>Generated: {generatedAt} · {data.isDemo ? 'DEMO INVESTIGATION · SIMULATED ANALYSIS' : data.live?.aiAvailable ? `Groq reasoning (${data.live.model})` : 'AI reasoning unavailable'}</div>
          </div>
        </div>

        {/* Modal Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 bg-slate-950 px-6 py-4">
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 hover:text-white transition-all cursor-pointer"
            >
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
              <span>{copied ? 'Copied Markdown' : 'Copy Markdown'}</span>
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 hover:text-white transition-all cursor-pointer"
            >
              <Download className="h-4 w-4" />
              <span>Download (.md)</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 rounded-lg border border-cyan-500/40 bg-cyan-950/40 px-4 py-2 text-xs font-semibold text-cyan-300 hover:bg-cyan-900/60 transition-all cursor-pointer"
            >
              <Printer className="h-4 w-4" />
              <span>Print / Save PDF</span>
            </button>
            <button
              onClick={onClose}
              className="rounded-lg bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-all cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
