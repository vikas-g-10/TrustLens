import React from 'react';
import { 
  Swords, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Scale, 
  HelpCircle,
  ShieldCheck,
  ShieldAlert
} from 'lucide-react';
import { EvidenceBattleItem } from '../types/investigation';

interface EvidenceBattleProps {
  battleData: {
    supportingCount: number;
    challengingCount: number;
    summary: string;
    supporting: EvidenceBattleItem[];
    challenging: EvidenceBattleItem[];
  };
}

export const EvidenceBattle: React.FC<EvidenceBattleProps> = ({ battleData }) => {
  const total = battleData.supportingCount + battleData.challengingCount;
  const supportPct = total ? Math.round((battleData.supportingCount / total) * 100) : 0;
  const challengePct = total ? 100 - supportPct : 0;
  const balanceLabel =
    total === 0 ? 'Insufficient evidence'
    : battleData.supportingCount === battleData.challengingCount ? 'Equilibrium / Dialectical Deadlock'
    : battleData.supportingCount > battleData.challengingCount ? 'Supporting points outnumber challenging'
    : 'Challenging points outnumber supporting';
  const conflictLabel =
    battleData.supportingCount > 0 && battleData.challengingCount > 0 ? '⚠ EVIDENCE CONFLICT'
    : total === 0 ? 'INSUFFICIENT EVIDENCE'
    : 'ONE-SIDED EVIDENCE';
  return (
    <div id="evidence-battle" className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl space-y-6">
      {/* Section Title & Tag */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-950/40 border border-red-500/30 text-red-400">
              <Swords className="h-4 w-4" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white font-display">
              ⚔ EVIDENCE BATTLE
            </h2>
          </div>
          <p className="text-xs text-slate-300 mt-1 font-sans">
            “Evidence supporting the claim vs evidence challenging the claim”
          </p>
        </div>

        {/* Dynamic Balance indicator */}
        <div className="flex items-center gap-3 bg-slate-950 px-4 py-2 rounded-lg border border-slate-800">
          <Scale className="h-4 w-4 text-amber-400" />
          <div className="text-xs font-mono">
            <span className="text-emerald-400 font-bold">SUPPORTING {battleData.supportingCount}</span>
            <span className="text-slate-600 mx-2">VS</span>
            <span className="text-red-400 font-bold">CHALLENGING {battleData.challengingCount}</span>
          </div>
        </div>
      </div>

      {/* Tension Meter Visualization (50/50 Standoff) */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-[11px] font-mono text-slate-400">
          <span className="text-emerald-400 flex items-center gap-1">
            <ShieldCheck className="h-3 w-3" /> Supporting by count ({supportPct}%)
          </span>
          <span className="text-amber-400 font-semibold uppercase">
            {balanceLabel}
          </span>
          <span className="text-red-400 flex items-center gap-1">
            Challenging by count ({challengePct}%) <ShieldAlert className="h-3 w-3" />
          </span>
        </div>
        <div className="h-3 w-full rounded-full bg-slate-950 border border-slate-800 flex overflow-hidden p-0.5">
          <div className="h-full bg-emerald-500 rounded-l-full transition-all shadow-[0_0_10px_rgba(16,185,129,0.3)]" style={{ width: `${supportPct}%` }} />
          <div className="h-full bg-red-500 rounded-r-full transition-all shadow-[0_0_10px_rgba(239,68,68,0.3)]" style={{ width: `${challengePct}%` }} />
        </div>
      </div>

      {/* Two Column Arena */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* LEFT COLUMN: SUPPORTING EVIDENCE */}
        <div className="rounded-xl border border-emerald-900/40 bg-gradient-to-b from-emerald-950/20 to-slate-950 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-emerald-900/30 pb-3">
            <div className="flex items-center gap-2 text-emerald-400 font-mono font-bold text-sm tracking-wide">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
              <span>SUPPORTING EVIDENCE</span>
            </div>
            <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/30">
              {battleData.supportingCount} Claims
            </span>
          </div>

          <div className="space-y-3">
            {battleData.supporting.length === 0 && (
              <p className="text-xs font-mono text-slate-500 border border-dashed border-slate-800 rounded-lg p-4">Insufficient evidence</p>
            )}
            {battleData.supporting.map((item) => (
              <div 
                key={item.id}
                className="rounded-lg border border-emerald-900/30 bg-slate-900/60 p-4 space-y-2 hover:border-emerald-500/40 transition-colors"
              >
                <div className="flex items-start gap-2.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 shrink-0 mt-1.5" />
                  <div>
                    <span className="text-xs font-mono font-bold text-emerald-300 block">
                      {item.source}
                    </span>
                    <p className="text-sm font-semibold text-slate-100 mt-0.5">
                      {item.claimPoint}
                    </p>
                  </div>
                </div>

                <p className="text-xs text-slate-400 pl-4 border-l border-emerald-900/50 ml-1">
                  {item.detail}
                </p>

                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pl-4 pt-1">
                  <span>Reliability: {item.reliability}</span>
                  <span className="text-emerald-400/80">Vector: Corroboration</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN: CHALLENGING EVIDENCE */}
        <div className="rounded-xl border border-red-900/40 bg-gradient-to-b from-red-950/20 to-slate-950 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-red-900/30 pb-3">
            <div className="flex items-center gap-2 text-red-400 font-mono font-bold text-sm tracking-wide">
              <span className="h-2.5 w-2.5 rounded-full bg-red-400 inline-block animate-pulse" />
              <span>CHALLENGING EVIDENCE</span>
            </div>
            <span className="text-xs font-mono font-bold text-red-400 bg-red-950/80 px-2 py-0.5 rounded border border-red-500/30">
              {battleData.challengingCount} Forensics
            </span>
          </div>

          <div className="space-y-3">
            {battleData.challenging.length === 0 && (
              <p className="text-xs font-mono text-slate-500 border border-dashed border-slate-800 rounded-lg p-4">Insufficient evidence</p>
            )}
            {battleData.challenging.map((item) => {
              const isAmber = item.variant === 'orange';
              const dotColor = isAmber ? 'bg-orange-400' : 'bg-red-400';
              const titleColor = isAmber ? 'text-orange-300' : 'text-red-300';
              const borderColor = isAmber ? 'border-orange-900/30 hover:border-orange-500/40' : 'border-red-900/30 hover:border-red-500/40';

              return (
                <div 
                  key={item.id}
                  className={`rounded-lg border bg-slate-900/60 p-4 space-y-2 transition-colors ${borderColor}`}
                >
                  <div className="flex items-start gap-2.5">
                    <span className={`h-2 w-2 rounded-full ${dotColor} shrink-0 mt-1.5`} />
                    <div>
                      <span className={`text-xs font-mono font-bold ${titleColor} block`}>
                        {item.source}
                      </span>
                      <p className="text-sm font-semibold text-slate-100 mt-0.5">
                        {item.claimPoint}
                      </p>
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 pl-4 border-l border-red-900/50 ml-1">
                    {item.detail}
                  </p>

                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pl-4 pt-1">
                    <span>Reliability: {item.reliability}</span>
                    <span className={isAmber ? 'text-orange-400/80' : 'text-red-400/80'}>
                      Vector: Conflict / Counter
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom Summary Bar */}
      <div className="rounded-xl border border-amber-500/40 bg-amber-950/30 p-5 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4 text-xs font-mono font-bold">
            <span className="text-emerald-400 bg-emerald-950/80 px-2.5 py-1 rounded border border-emerald-500/30">
              SUPPORTING &nbsp;{battleData.supportingCount}
            </span>
            <span className="text-red-400 bg-red-950/80 px-2.5 py-1 rounded border border-red-500/30">
              CHALLENGING &nbsp;{battleData.challengingCount}
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-amber-300 font-bold uppercase tracking-wider">
            <AlertCircle className="h-4 w-4 text-amber-400 shrink-0" />
            <span>{conflictLabel}</span>
          </div>
        </div>

        <div className="text-sm font-medium text-amber-200 text-center md:text-right font-sans max-w-xl">
          “{battleData.summary}”
        </div>
      </div>
    </div>
  );
};
