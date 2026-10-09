import React from 'react';
import { 
  FileText, 
  Video, 
  Link as LinkIcon, 
  Layers, 
  AlertOctagon, 
  Search, 
  CheckCircle,
  ArrowRight,
  ShieldCheck,
  ChevronDown
} from 'lucide-react';

interface InvestigationSequenceFlowProps {
  onScrollToSection?: (id: string) => void;
}

export const InvestigationSequenceFlow: React.FC<InvestigationSequenceFlowProps> = ({
  onScrollToSection
}) => {
  const steps = [
    { id: 'step-1', label: 'CLAIM', desc: 'Factual statement', icon: <FileText className="h-3.5 w-3.5" />, color: 'cyan' },
    { id: 'step-2', label: 'MEDIA', desc: 'Visual forensics', icon: <Video className="h-3.5 w-3.5" />, color: 'sky' },
    { id: 'step-3', label: 'URL', desc: 'Redirects & security', icon: <LinkIcon className="h-3.5 w-3.5" />, color: 'red' },
    { id: 'step-4', label: 'INDEPENDENT EVIDENCE', desc: 'Corroboration sources', icon: <Layers className="h-3.5 w-3.5" />, color: 'emerald' },
    { id: 'step-5', label: 'CONTRADICTION', desc: 'Historical collision', icon: <AlertOctagon className="h-3.5 w-3.5" />, color: 'rose' },
    { id: 'step-6', label: 'COUNTER-EVIDENCE', desc: 'Archival refutation', icon: <Search className="h-3.5 w-3.5" />, color: 'orange' },
    { id: 'step-7', label: 'FINAL ASSESSMENT', desc: 'Inconclusive synthesis', icon: <CheckCircle className="h-3.5 w-3.5" />, color: 'amber' },
  ];

  return (
    <div className="space-y-4">
      {/* Requirement 10: Strong One-Line Product Message Banner */}
      <div className="relative overflow-hidden rounded-xl border border-cyan-500/40 bg-gradient-to-r from-cyan-950/60 via-slate-900 to-slate-950 p-4 sm:p-5 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <span className="text-[11px] font-mono uppercase tracking-widest text-cyan-400 font-bold block">
              THE TRUSTLENS PARADIGM
            </span>
            <div className="text-base sm:text-lg font-display text-white">
              <span className="text-slate-300">Most AI systems ask: </span>
              <span className="font-semibold text-slate-100">“Is this fake?”</span>
              <span className="mx-2 text-cyan-500 font-bold hidden md:inline">|</span>
              <span className="text-cyan-400 font-bold block sm:inline mt-1 sm:mt-0">
                TrustLens asks: “Can I trust the evidence?”
              </span>
            </div>
          </div>

          <div className="shrink-0 flex items-center gap-2 text-xs font-mono text-cyan-300 bg-cyan-950/80 px-3 py-1.5 rounded-lg border border-cyan-500/30">
            <ShieldCheck className="h-4 w-4 text-cyan-400" />
            <span>Epistemic Evidence Engine</span>
          </div>
        </div>
      </div>

      {/* Requirement 2: Visual 7-Step Sequence Diagram for Hackathon Jury */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 sm:p-5 backdrop-blur-md">
        <div className="flex items-center justify-between mb-3 border-b border-slate-800/80 pb-2">
          <span className="text-xs font-mono font-bold tracking-wider text-slate-400 uppercase">
            EVIDENTIARY INVESTIGATION SEQUENCE
          </span>
          <span className="text-[11px] font-mono text-cyan-400">
            7 Sequential Forensics Verification Gates
          </span>
        </div>

        {/* Desktop / Tablet Horizontal Flow */}
        <div className="hidden lg:flex items-center justify-between gap-1 overflow-x-auto py-1">
          {steps.map((step, idx) => (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center text-center p-2 rounded-lg bg-slate-950/90 border border-slate-800/90 hover:border-cyan-500/40 transition-colors min-w-[125px] flex-1">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-900 border border-slate-700 text-cyan-400 mb-1.5">
                  {step.icon}
                </div>
                <span className="text-[11px] font-mono font-bold text-slate-200 tracking-wide uppercase">
                  {step.label}
                </span>
                <span className="text-[10px] text-slate-400 font-sans truncate max-w-[115px]">
                  {step.desc}
                </span>
              </div>

              {idx < steps.length - 1 && (
                <div className="text-slate-600 shrink-0 px-0.5">
                  <ArrowRight className="h-3.5 w-3.5 text-cyan-500/70" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Mobile / Small Screens Vertical Flow */}
        <div className="lg:hidden grid grid-cols-1 sm:grid-cols-2 gap-2">
          {steps.map((step, idx) => (
            <div 
              key={step.id} 
              className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs"
            >
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-slate-900 border border-slate-700 text-cyan-400 font-mono text-[10px] font-bold">
                0{idx + 1}
              </div>
              <div className="truncate">
                <span className="font-mono font-bold text-slate-200 block truncate">
                  {step.label}
                </span>
                <span className="text-[10px] text-slate-400 block truncate">
                  {step.desc}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
