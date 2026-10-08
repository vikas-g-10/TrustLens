import React from 'react';
import { ShieldAlert, Compass, FileText, RefreshCw } from 'lucide-react';

interface HeaderProps {
  onReset: () => void;
  onOpenReport?: () => void;
  hasActiveCase: boolean;
  onNavigateSection?: (sectionId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  onReset,
  onOpenReport,
  hasActiveCase,
  onNavigateSection
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-[#070B12]/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Zone 1: Wordmark Brand */}
        <div className="flex items-center gap-3">
          <button 
            onClick={onReset} 
            className="flex items-center gap-2.5 text-left group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-950/80 border border-cyan-500/30 text-cyan-400 group-hover:border-cyan-400 group-hover:shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight text-white font-display">
                TRUST<span className="text-cyan-400">LENS</span>
              </span>
              <span className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">
                Evidence Forensics Platform
              </span>
            </div>
          </button>
        </div>

        {/* Zone 2: Navigation Links */}
        <nav className="hidden md:flex items-center gap-7 text-xs font-medium text-slate-300">
          <button
            onClick={() => onNavigateSection?.('investigation-overview')}
            className="hover:text-cyan-300 transition-colors whitespace-nowrap cursor-pointer"
          >
            Investigation
          </button>
          <button
            onClick={() => onNavigateSection?.('evidence-battle')}
            className="hover:text-cyan-300 transition-colors whitespace-nowrap cursor-pointer"
          >
            Evidence Battle
          </button>
          <button
            onClick={() => onNavigateSection?.('evidence-graph')}
            className="hover:text-cyan-300 transition-colors whitespace-nowrap cursor-pointer"
          >
            Evidence Graph
          </button>
          <button
            onClick={() => onNavigateSection?.('explainable-reasoning')}
            className="hover:text-cyan-300 transition-colors whitespace-nowrap cursor-pointer"
          >
            Why This Verdict
          </button>
          <button
            onClick={() => onNavigateSection?.('evidence-timeline')}
            className="hover:text-cyan-300 transition-colors whitespace-nowrap cursor-pointer"
          >
            Timeline
          </button>
        </nav>

        {/* Zone 3: Primary Actions */}
        <div className="flex items-center gap-3">
          {hasActiveCase && (
            <button
              onClick={onOpenReport}
              className="flex items-center gap-1.5 rounded-lg border border-cyan-500/30 bg-cyan-950/40 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-900/60 hover:border-cyan-400 transition-all cursor-pointer whitespace-nowrap"
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Report</span>
            </button>
          )}

          <button
            onClick={onReset}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-800 hover:text-white transition-all cursor-pointer whitespace-nowrap"
            title="Reset to New Investigation"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">New Case</span>
          </button>
        </div>
      </div>
    </header>
  );
};
