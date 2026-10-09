import React from 'react';
import { 
  AlertTriangle, 
  HelpCircle, 
  ShieldAlert, 
  CheckCircle2, 
  FileSearch, 
  Crosshair, 
  Download, 
  ExternalLink,
  Info,
  Activity,
  Scale,
  GitFork,
  Layers
} from 'lucide-react';
import { InvestigationData } from '../types/investigation';
import { verdictTheme } from '../lib/verdictTheme';

interface VerdictBannerProps {
  data: InvestigationData;
  onOpenReport: () => void;
  onOpenMediaModal: () => void;
}

export const VerdictBanner: React.FC<VerdictBannerProps> = ({
  data,
  onOpenReport,
  onOpenMediaModal
}) => {
  const theme = verdictTheme(data.verdict.status);
  const StatusIcon =
    data.verdict.status === 'LIKELY_GENUINE' || data.verdict.status === 'LIKELY_AUTHENTIC' ? CheckCircle2 :
    data.verdict.status === 'LIKELY_AI_GENERATED' ? Crosshair :
    data.verdict.status === 'HIGH_RISK' || data.verdict.status === 'LIKELY_MANIPULATED' ? ShieldAlert :
    data.verdict.status === 'INCONCLUSIVE' ? HelpCircle : AlertTriangle;
  const prefix = (data.verdict.status === 'LIKELY_GENUINE' || data.verdict.status === 'LIKELY_AUTHENTIC') ? '✓' : '⚠';

  const supIds = data.live?.final?.supportingEvidenceIds || [];
  const conIds = data.live?.final?.contradictingEvidenceIds || [];

  const toPct = (val: number | undefined | null) => {
    if (val === undefined || val === null) return 0;
    return Math.min(100, Math.max(0, Math.round(val > 1 ? val : val * 100)));
  };

  // Backend Trust Triangle values are already 0-100: display them as-is (clamped for the bar only).
  const asIs = (val: number | undefined | null) =>
    val === undefined || val === null ? 0 : Math.min(100, Math.max(0, Math.round(val)));
  const manipVal = asIs(data.trustTriangle?.manipulationLikelihood);
  const strengthVal = asIs(data.trustTriangle?.evidenceStrength);
  const conflictVal = asIs(data.trustTriangle?.evidenceConflict);

  return (
    <div id="investigation-overview" className={`relative overflow-hidden rounded-2xl border p-6 sm:p-8 shadow-2xl backdrop-blur-xl ${theme.panel}`}>
      {/* Decorative forensic corner brackets */}
      <div className={`absolute top-3 left-3 h-3 w-3 border-t-2 border-l-2 ${theme.corner}`} />
      <div className={`absolute top-3 right-3 h-3 w-3 border-t-2 border-r-2 ${theme.corner}`} />
      <div className={`absolute bottom-3 left-3 h-3 w-3 border-b-2 border-l-2 ${theme.corner}`} />
      <div className={`absolute bottom-3 right-3 h-3 w-3 border-b-2 border-r-2 ${theme.corner}`} />

      {/* Top Metadata Row */}
      <div className={`flex flex-wrap items-center justify-between gap-3 border-b pb-4 text-xs font-mono text-slate-400 ${theme.headerBorder}`}>
        <div className="flex flex-wrap items-center gap-3">
          <span className={`flex items-center gap-1.5 font-semibold uppercase tracking-wider ${theme.headerText}`}>
            <ShieldAlert className="h-4 w-4" />
            FINAL VERDICT
          </span>
          <span className="text-slate-600">/</span>
          <span>Case: {data.caseId}</span>
          <span className="text-slate-600">/</span>
          {data.isDemo ? (
            <span className="text-amber-400/90">DEMO INVESTIGATION · SIMULATED ANALYSIS</span>
          ) : (
            <span className="text-cyan-400/90">LIVE INVESTIGATION · DETERMINISTIC FUSION</span>
          )}
        </div>

        {data.isDemo && (
          <div className="flex items-center gap-3">
            <button
              onClick={onOpenMediaModal}
              className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 transition-colors underline cursor-pointer"
            >
              <span>Inspect Media: {data.mediaName}</span>
              <ExternalLink className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>

      {/* Core Verdict Display */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Big Status Badge + Confidence Dial + Trust Triangle */}
        <div className="lg:col-span-5 flex flex-col items-start gap-4">
          <div className={`inline-flex items-center gap-3 rounded-xl border px-5 py-3 ${theme.badgeBox}`}>
            <StatusIcon className={`h-8 w-8 shrink-0 ${theme.badgeText}`} />
            <div>
              <span className={`text-xs uppercase tracking-widest font-mono block ${theme.badgeLabel}`}>
                Primary Assessment
              </span>
              <span className={`text-2xl sm:text-3xl font-black tracking-tight font-display ${theme.badgeText}`}>
                {prefix} {theme.label}
              </span>
            </div>
          </div>

          {/* Confidence Meter */}
          <div className="w-full max-w-sm rounded-lg border border-slate-800 bg-slate-950/70 p-3.5 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">Confidence in assessment:</span>
              <span className={`font-bold tabular-nums text-sm ${theme.confText}`}>
                {data.verdict.confidence}%
              </span>
            </div>

            <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r rounded-full transition-all duration-1000 ${theme.confBar}`}
                style={{ width: `${data.verdict.confidence}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span>0%</span>
              <span>Evidence-calibrated</span>
              <span>95% max</span>
            </div>
          </div>

          {/* Trust Triangle Metrics */}
          {data.trustTriangle && (
            <div className="w-full max-w-sm rounded-lg border border-slate-800/90 bg-slate-950/80 p-3.5 space-y-2.5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 text-xs font-mono">
                <span className="font-semibold text-cyan-400 flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5" />
                  TRUST TRIANGLE
                </span>
                <span className="text-[10px] text-slate-400">Calibrated</span>
              </div>
              <div className="space-y-2 text-xs font-mono">
                <div>
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="text-slate-400">Manipulation Likelihood:</span>
                    <span className="text-rose-400 font-bold tabular-nums">
                      {manipVal}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-rose-500 rounded-full transition-all duration-500"
                      style={{ width: `${manipVal}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="text-slate-400">Evidence Strength:</span>
                    <span className="text-emerald-400 font-bold tabular-nums">
                      {strengthVal}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                      style={{ width: `${strengthVal}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="text-slate-400">Evidence Conflict:</span>
                    <span className={`font-bold tabular-nums ${conflictVal > 30 ? 'text-amber-400' : 'text-slate-300'}`}>
                      {conflictVal}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-amber-500 rounded-full transition-all duration-500"
                      style={{ width: `${conflictVal}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {!data.isDemo && !data.trustTriangle && (
            <div className="w-full max-w-sm rounded-lg border border-slate-800/90 bg-slate-950/80 p-3.5 text-xs font-mono text-slate-400">
              <span className="font-semibold text-cyan-400">TRUST TRIANGLE</span>
              <span className="block mt-1">Unavailable: the backend returned no fusion result for this investigation.</span>
            </div>
          )}

          {/* Evidence Summary Strip */}
          {data.evidenceSummary && (
            <div className="w-full max-w-sm rounded-lg border border-slate-800/80 bg-slate-950/60 p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800/70 pb-1 text-[11px] font-mono">
                <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                  <Scale className="h-3.5 w-3.5 text-cyan-400" />
                  EVIDENCE SUMMARY
                </span>
                <span className="text-[10px] text-slate-500">Coverage {toPct(data.evidenceSummary.evidenceCoverage)}%</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono pt-0.5">
                <div className="rounded bg-slate-900/60 p-1.5 border border-slate-800/50">
                  <span className="text-slate-500 block text-[10px]">SUPPORTING</span>
                  <span className="text-emerald-400 font-bold tabular-nums">
                    {data.evidenceSummary.supportingStrength.toFixed(2)}
                  </span>
                </div>
                <div className="rounded bg-slate-900/60 p-1.5 border border-slate-800/50">
                  <span className="text-slate-500 block text-[10px]">CONTRADICTING</span>
                  <span className="text-rose-400 font-bold tabular-nums">
                    {data.evidenceSummary.contradictingStrength.toFixed(2)}
                  </span>
                </div>
                <div className="rounded bg-slate-900/60 p-1.5 border border-slate-800/50 col-span-2 flex items-center justify-between">
                  <span className="text-slate-400 text-[10px]">INDEPENDENT SOURCES</span>
                  <span className="text-cyan-300 font-bold tabular-nums text-xs">
                    {data.evidenceSummary.independentEvidenceCount}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Main Explanation, Conflict Alert, & WHY List */}
        <div className="lg:col-span-7 space-y-4">
          <div>
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
              Evidentiary Synthesis
            </span>
            <p className="text-lg sm:text-xl font-medium text-slate-100 leading-snug">
              “{data.verdict.mainExplanation}”
            </p>
          </div>

          {/* Conflict Alert Callout */}
          {data.conflict?.detected && (
            <div className="rounded-xl border border-amber-500/40 bg-amber-950/20 p-3.5 space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber-400">
                <AlertTriangle className="h-4 w-4" />
                <span>EVIDENCE CONFLICT DETECTED · SEVERITY: {data.conflict.severity} ({data.conflict.count} conflict point{data.conflict.count > 1 ? 's' : ''})</span>
              </div>
              {data.conflict.details.map((cd, idx) => (
                <p key={idx} className="text-xs text-amber-200/90 pl-6">
                  {cd.description}
                </p>
              ))}
            </div>
          )}

          {/* WHY? List */}
          <div className={`rounded-xl border p-4 space-y-2 ${theme.whyBox}`}>
            <span className={`text-xs font-mono font-bold uppercase tracking-wider block ${theme.whyTitle}`}>
              WHY?
            </span>
            <ul className="space-y-1.5 text-xs text-slate-200 font-sans">
              {data.verdict.whyBullets.map((b, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className={`font-bold ${theme.whyBullet}`}>•</span>
                  <span>{b}</span>
                </li>
              ))}
            </ul>

            {/* Traceable Provenance Section */}
            {(supIds.length > 0 || conIds.length > 0) && (
              <div className="pt-2 mt-2 border-t border-slate-800/80 text-[11px] font-mono space-y-1">
                <span className="text-slate-400 uppercase text-[10px] tracking-wider block">Evidence Provenance:</span>
                {supIds.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-emerald-400 text-[10px]">Supports:</span>
                    {supIds.map((id) => (
                      <span key={id} className="rounded bg-emerald-950/60 border border-emerald-800/50 px-1.5 py-0.5 text-[10px] text-emerald-300">
                        {id}
                      </span>
                    ))}
                  </div>
                )}
                {conIds.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-rose-400 text-[10px]">Contradicts:</span>
                    {conIds.map((id) => (
                      <span key={id} className="rounded bg-rose-950/60 border border-rose-800/50 px-1.5 py-0.5 text-[10px] text-rose-300">
                        {id}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Evidence Identification Bar: CLAIM & SUBMITTED URL */}
      <div className="mt-8 pt-5 border-t border-slate-800/80 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono min-w-0">
          <div className="rounded-lg bg-slate-950/80 p-2.5 border border-slate-800 min-w-0">
            <span className="text-[10px] text-cyan-400 font-bold block uppercase tracking-wider">
              CLAIM
            </span>
            <span className="text-slate-100 font-sans text-xs font-medium block mt-0.5 break-words">
              “{data.claim}”
            </span>
          </div>

          <div className="rounded-lg bg-slate-950/80 p-2.5 border border-slate-800 min-w-0">
            <span className="text-[10px] text-rose-400 font-bold block uppercase tracking-wider">
              SUBMITTED URL
            </span>
            <span className="text-cyan-300 font-mono text-xs block mt-0.5 truncate">
              {data.url}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={onOpenReport}
            className="flex items-center gap-2 rounded-lg bg-cyan-500 px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-black hover:bg-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all cursor-pointer whitespace-nowrap"
          >
            <Download className="h-3.5 w-3.5" />
            <span>GENERATE INVESTIGATION REPORT</span>
          </button>
        </div>
      </div>
    </div>
  );
};
