import React from 'react';
import { 
  Clock, 
  Calendar, 
  History, 
  AlertTriangle, 
  ShieldCheck, 
  Search,
  ArrowDown
} from 'lucide-react';
import { TimelineStep } from '../types/investigation';

interface EvidenceTimelineProps {
  timeline: TimelineStep[];
  isDemo: boolean;
}

export const EvidenceTimeline: React.FC<EvidenceTimelineProps> = ({ timeline, isDemo }) => {
  return (
    <div id="evidence-timeline" className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-950/40 border border-sky-500/30 text-sky-400">
              <Clock className="h-4 w-4" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white font-display">
              EVIDENCE TIMELINE
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            {isDemo
              ? 'Chronological reconstruction exposing temporal displacement and counter-evidence provenance (simulated).'
              : 'Chronological record of the steps performed during this investigation.'}
          </p>
        </div>

        <span className="text-xs font-mono text-cyan-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
          {isDemo ? 'SIMULATED · Temporal Discrepancy: ~4 Years' : `Live record · ${timeline.length} events`}
        </span>
      </div>

      {/* Sequential Flow */}
      <div className="relative pl-6 sm:pl-8 space-y-8 before:absolute before:left-3 sm:before:left-4 before:top-3 before:bottom-3 before:w-0.5 before:bg-gradient-to-b before:from-rose-500 before:via-cyan-500 before:to-amber-500">
        {timeline.map((step, idx) => {
          let dotColor = 'bg-slate-700 border-slate-500';
          let textColor = 'text-slate-200';
          let badgeColor = 'text-slate-400';

          if (step.type === 'past_archive') {
            dotColor = 'bg-rose-500 border-rose-300 ring-4 ring-rose-500/20';
            textColor = 'text-rose-300';
            badgeColor = 'text-rose-400';
          } else if (step.type === 'viral_post') {
            dotColor = 'bg-sky-500 border-sky-300';
            textColor = 'text-sky-300';
            badgeColor = 'text-sky-400';
          } else if (step.type === 'investigation') {
            dotColor = 'bg-cyan-500 border-cyan-300 ring-4 ring-cyan-500/20';
            textColor = 'text-cyan-300';
            badgeColor = 'text-cyan-400';
          } else if (step.type === 'conflict') {
            dotColor = 'bg-amber-500 border-amber-300';
            textColor = 'text-amber-300';
            badgeColor = 'text-amber-400';
          } else if (step.type === 'counter') {
            dotColor = 'bg-orange-500 border-orange-300 ring-4 ring-orange-500/20';
            textColor = 'text-orange-300';
            badgeColor = 'text-orange-400';
          } else if (step.type === 'verdict') {
            dotColor = 'bg-amber-400 border-amber-200 ring-4 ring-amber-400/30';
            textColor = 'text-amber-300';
            badgeColor = 'text-amber-400 font-bold';
          }

          return (
            <div key={step.id} className="relative group">
              {/* Timeline marker node */}
              <div 
                className={`absolute -left-6 sm:-left-8 top-1 h-4 w-4 rounded-full border-2 transition-all ${dotColor}`}
              />

              {/* Step Card */}
              <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4 transition-all group-hover:border-slate-700 group-hover:bg-slate-950/90 space-y-1.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-mono font-bold tracking-wider uppercase ${textColor}`}>
                      {step.title}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      [Stage 0{idx + 1}]
                    </span>
                  </div>
                  <span className={`text-xs font-mono ${badgeColor}`}>
                    {step.dateText}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {step.description}
                </p>
              </div>

              {idx < timeline.length - 1 && (
                <div className="hidden pl-2 text-slate-600">
                  <ArrowDown className="h-3 w-3" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
