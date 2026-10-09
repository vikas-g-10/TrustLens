import React, { useEffect, useState } from 'react';
import { 
  CheckCircle2, 
  Loader2, 
  ShieldAlert, 
  Terminal, 
  FastForward, 
  Database,
  Search,
  Key,
  GitBranch,
  Split,
  Cpu
} from 'lucide-react';
import { PipelineStage, PipelineStageId } from '../types/investigation';

interface PipelineAnimationProps {
  stages: PipelineStage[];
  onComplete: () => void;
  caseClaim: string;
  /** When false, the pipeline waits at the last stage until the real result arrives. */
  isReady?: boolean;
}

const clock = () => new Date().toISOString().slice(11, 23);

export const PipelineAnimation: React.FC<PipelineAnimationProps> = ({
  stages,
  onComplete,
  caseClaim,
  isReady = true
}) => {
  const [currentStageIndex, setCurrentStageIndex] = useState<number>(0);
  const [stageStatuses, setStageStatuses] = useState<Record<string, 'pending' | 'analyzing' | 'complete'>>({});
  const [activeLogs, setActiveLogs] = useState<string[]>([]);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(1);

  // Initialize stage statuses
  useEffect(() => {
    const initialStatuses: Record<string, 'pending' | 'analyzing' | 'complete'> = {};
    stages.forEach((s, idx) => {
      initialStatuses[s.id] = idx === 0 ? 'analyzing' : 'pending';
    });
    setStageStatuses(initialStatuses);
    setActiveLogs([`[${clock()}] INGESTION: Initializing TrustLens evidentiary pipeline for claim...`]);
  }, [stages]);

  // Stage progression loop
  useEffect(() => {
    if (currentStageIndex >= stages.length) {
      if (!isReady) return; // keep waiting for the real investigation result
      // Finished all stages, transition after a brief pause
      const finishTimer = setTimeout(() => {
        onComplete();
      }, 500 / speedMultiplier);
      return () => clearTimeout(finishTimer);
    }

    const currentStage = stages[currentStageIndex];
    
    // Set current to analyzing
    setStageStatuses(prev => ({
      ...prev,
      [currentStage.id]: 'analyzing'
    }));

    if (currentStage.telemetryLog) {
      setActiveLogs(prev => [
        `[${clock()}] ${currentStage.label}: ${currentStage.telemetryLog}`,
        ...prev.slice(0, 5)
      ]);
    }

    // Step duration: ~350ms to 450ms per step
    const stepDuration = (400) / speedMultiplier;
    const timer = setTimeout(() => {
      // Mark current complete
      setStageStatuses(prev => ({
        ...prev,
        [currentStage.id]: 'complete'
      }));
      // Move to next stage
      setCurrentStageIndex(prev => prev + 1);
    }, stepDuration);

    return () => clearTimeout(timer);
  }, [currentStageIndex, stages, speedMultiplier, onComplete, isReady]);

  const handleSkip = () => {
    // Jump to the end; the effect above completes once the result is ready
    const completed: Record<string, 'pending' | 'analyzing' | 'complete'> = {};
    stages.forEach(s => {
      completed[s.id] = isReady ? 'complete' : s.id === stages[stages.length - 1].id ? 'analyzing' : 'complete';
    });
    setStageStatuses(completed);
    setCurrentStageIndex(stages.length);
  };

  const getStageIcon = (id: PipelineStageId) => {
    switch (id) {
      case 'claim_extraction': return <Search className="h-4 w-4" />;
      case 'media_forensics': return <Database className="h-4 w-4" />;
      case 'url_security': return <Key className="h-4 w-4" />;
      case 'evidence_retrieval': return <Search className="h-4 w-4" />;
      case 'contradiction_check': return <Split className="h-4 w-4" />;
      case 'source_independence': return <GitBranch className="h-4 w-4" />;
      case 'counter_evidence': return <ShieldAlert className="h-4 w-4" />;
      case 'evidence_fusion': return <Cpu className="h-4 w-4" />;
      case 'final_reasoning': return <Terminal className="h-4 w-4" />;
      default: return <Database className="h-4 w-4" />;
    }
  };

  const waiting = currentStageIndex >= stages.length && !isReady;

  return (
    <div className="relative min-h-[80vh] flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8 forensic-grid">
      <div className="w-full max-w-4xl mx-auto space-y-6">
        
        {/* Header HUD */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
              </span>
              <span className="text-xs font-mono font-bold tracking-widest text-cyan-400 uppercase">
                Forensic Pipeline Execution
              </span>
            </div>
            <p className="text-sm text-slate-300 font-medium truncate mt-1 max-w-xl">
              Target: "{caseClaim}"
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setSpeedMultiplier(prev => prev === 1 ? 2.5 : 1)}
              className="text-xs font-mono px-2.5 py-1 rounded border border-slate-700 bg-slate-800/80 text-slate-300 hover:text-cyan-300 transition-colors cursor-pointer"
            >
              Speed: {speedMultiplier > 1 ? '2.5x Turbo' : '1.0x Normal'}
            </button>
            <button
              onClick={handleSkip}
              className="flex items-center gap-1.5 text-xs font-mono font-semibold px-3 py-1 rounded bg-slate-800 border border-slate-700 text-cyan-400 hover:bg-slate-700 hover:border-cyan-500 transition-all cursor-pointer"
            >
              <FastForward className="h-3.5 w-3.5" />
              <span>Skip Animation</span>
            </button>
          </div>
        </div>

        {/* 9-Stage Flow Visualizer */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 shadow-2xl backdrop-blur-xl p-5 sm:p-7">
          <div className="space-y-3">
            {stages.map((stage, index) => {
              const status = waiting && index === stages.length - 1 ? 'analyzing' : stageStatuses[stage.id] || 'pending';
              const isAnalyzing = status === 'analyzing';
              const isComplete = status === 'complete';
              const isPending = status === 'pending';

              return (
                <div
                  key={stage.id}
                  className={`relative flex items-center justify-between rounded-lg p-3 transition-all duration-300 ${
                    isAnalyzing
                      ? 'border border-cyan-500/50 bg-cyan-950/30 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                      : isComplete
                      ? 'border border-emerald-900/40 bg-emerald-950/10'
                      : 'border border-slate-800/60 bg-slate-950/40 opacity-40'
                  }`}
                >
                  {/* Step Left: Index + Icon + Label + Subtext */}
                  <div className="flex items-center gap-3.5">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-md font-mono text-xs font-bold transition-all ${
                        isAnalyzing
                          ? 'bg-cyan-500 text-black shadow-[0_0_10px_rgba(6,182,212,0.5)]'
                          : isComplete
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                          : 'bg-slate-800 text-slate-500'
                      }`}
                    >
                      {getStageIcon(stage.id)}
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold tracking-wider text-slate-200">
                          {stage.label}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500">
                          0{index + 1}/09
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 hidden sm:block">
                        {stage.subtext}
                      </p>
                    </div>
                  </div>

                  {/* Step Right: Status Badge (ANALYZING... vs ✓ COMPLETE) */}
                  <div className="flex items-center gap-2 font-mono text-xs font-semibold shrink-0">
                    {isAnalyzing && (
                      <div className="flex items-center gap-2 text-cyan-400">
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        <span className="animate-pulse">ANALYZING...</span>
                      </div>
                    )}
                    {isComplete && (
                      <div className="flex items-center gap-1.5 text-emerald-400">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>✓ COMPLETE</span>
                      </div>
                    )}
                    {isPending && (
                      <span className="text-slate-600">QUEUED</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Live Telemetry Log Terminal */}
          <div className="mt-5 rounded-lg border border-slate-800 bg-[#040711] p-3.5">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 mb-2 text-[10px] font-mono text-slate-400">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <Terminal className="h-3 w-3" />
                TELEMETRY FEED
              </span>
              <span>BUFFER: ACTIVE</span>
            </div>
            <div className="space-y-1 font-mono text-[11px] text-slate-300 min-h-[70px]">
              {activeLogs.map((log, i) => (
                <div key={i} className="flex items-start gap-2 truncate">
                  <span className="text-cyan-500 select-none">›</span>
                  <span className="truncate">{log}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
