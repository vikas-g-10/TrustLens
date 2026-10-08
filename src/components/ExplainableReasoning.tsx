import React from 'react';
import { VerdictStatus } from '../types/investigation';
import { verdictTheme } from '../lib/verdictTheme';
import { 
  CheckCircle2, 
  HelpCircle, 
  AlertTriangle, 
  ShieldAlert, 
  Search, 
  ArrowRight,
  ShieldCheck,
  Scale
} from 'lucide-react';

interface ReasoningStep {
  number: number;
  title: string;
  finding: string;
  status: 'neutral' | 'alert' | 'warning' | 'verified';
}

interface ExplainableReasoningProps {
  steps: ReasoningStep[];
  verdictStatus: VerdictStatus;
  confidence: number;
  isDemo: boolean;
  finalReasoning: string;
  whyNotGenuine: string;
  whyNotHighRisk: string;
}

export const ExplainableReasoning: React.FC<ExplainableReasoningProps> = ({
  steps,
  verdictStatus,
  confidence,
  isDemo,
  finalReasoning,
  whyNotGenuine,
  whyNotHighRisk
}) => {
  const theme = verdictTheme(verdictStatus);
  return (
    <div id="explainable-reasoning" className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl space-y-8">
      {/* Title */}
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-950/40 border border-amber-500/30 text-amber-400">
            <HelpCircle className="h-4 w-4" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white font-display">
            WHY THIS VERDICT?
          </h2>
        </div>
        <p className="text-xs text-slate-400 mt-1 font-sans">
          Step-by-step reasoning showing how the verdict was reached from the available evidence.
        </p>
      </div>

      {/* 7-Step Step Chain */}
      <div className="space-y-3">
        {steps.map((step) => {
          let badgeBorder = 'border-slate-800 bg-slate-950';
          let numberBg = 'bg-slate-800 text-slate-300';
          let titleColor = 'text-slate-200';

          if (step.status === 'verified') {
            badgeBorder = 'border-emerald-900/40 bg-emerald-950/20';
            numberBg = 'bg-emerald-950 border border-emerald-500/30 text-emerald-400';
            titleColor = 'text-emerald-300';
          } else if (step.status === 'alert') {
            badgeBorder = 'border-red-900/40 bg-red-950/20';
            numberBg = 'bg-red-950 border border-red-500/30 text-red-400';
            titleColor = 'text-red-300';
          } else if (step.status === 'warning') {
            badgeBorder = 'border-amber-900/40 bg-amber-950/20';
            numberBg = 'bg-amber-950 border border-amber-500/30 text-amber-400';
            titleColor = 'text-amber-300';
          }

          return (
            <div
              key={step.number}
              className={`flex items-start gap-4 rounded-xl border p-4 transition-all ${badgeBorder}`}
            >
              {/* Step Number */}
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg font-mono text-xs font-bold ${numberBg}`}>
                0{step.number}
              </div>

              {/* Step Content */}
              <div className="space-y-1">
                <span className={`text-xs font-mono font-bold tracking-wider uppercase ${titleColor}`}>
                  0{step.number} — {step.title}
                </span>
                <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans">
                  {step.finding}
                </p>
              </div>
            </div>
          );
        })}

        {/* FINAL STEP BADGE */}
        <div className={`flex items-center justify-between rounded-xl border p-4 transition-all ${theme.finalBox}`}>
          <div className="flex items-center gap-3">
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg font-mono text-xs font-black ${theme.finalIcon}`}>
              ✓
            </div>
            <div>
              <span className={`text-xs font-mono font-bold uppercase tracking-wider block ${theme.finalTitle}`}>
                FINAL RESOLUTION
              </span>
              <span className={`text-lg font-black font-display ${theme.finalText}`}>
                {verdictStatus === 'LIKELY_GENUINE' ? '✓' : '⚠'} {theme.label}
              </span>
            </div>
          </div>
          <span className={`text-xs font-mono font-bold px-3 py-1.5 rounded-lg border ${theme.finalChip}`}>
            Confidence: {confidence}%
          </span>
        </div>
      </div>

      {/* Final Reasoning Callout */}
      <div className={`rounded-xl border p-5 space-y-2 ${theme.whyBox}`}>
        <span className={`text-[11px] font-mono uppercase tracking-widest block font-bold ${theme.headerText}`}>
          Synthesized Evidentiary Conclusion:
        </span>
        <blockquote className="text-base sm:text-lg font-medium text-slate-100 font-sans italic border-l-2 border-slate-500 pl-4 py-1">
          “{finalReasoning}”
        </blockquote>
      </div>

      {/* Contrast Explanations: WHY NOT GENUINE? vs WHY NOT HIGH RISK? */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
        {/* WHY NOT GENUINE? */}
        <div className="rounded-xl border border-rose-900/40 bg-gradient-to-b from-rose-950/20 to-slate-950 p-5 space-y-3">
          <div className="flex items-center gap-2 text-rose-400 font-mono text-xs font-bold uppercase tracking-wider">
            <ShieldAlert className="h-4 w-4" />
            <span>WHY NOT GENUINE?</span>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            “{whyNotGenuine}”
          </p>
          {isDemo && (
            <div className="pt-2 border-t border-rose-900/30 text-[11px] font-mono text-slate-400">
              (Simulated) Fails calendar anchor verification despite optical authenticity.
            </div>
          )}
        </div>

        {/* WHY NOT HIGH RISK? */}
        <div className="rounded-xl border border-sky-900/40 bg-gradient-to-b from-sky-950/20 to-slate-950 p-5 space-y-3">
          <div className="flex items-center gap-2 text-sky-400 font-mono text-xs font-bold uppercase tracking-wider">
            <ShieldCheck className="h-4 w-4" />
            <span>WHY NOT HIGH RISK?</span>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            “{whyNotHighRisk}”
          </p>
          {isDemo && (
            <div className="pt-2 border-t border-sky-900/30 text-[11px] font-mono text-slate-400">
              (Simulated) Zero synthetic deepfake artifacts; non-malicious provenance repurpose.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
