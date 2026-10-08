import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  FileVideo,
  Info,
  Loader2,
  Pause,
  Play,
  RotateCcw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Upload,
  Volume2,
  VolumeX,
  X,
  Zap,
} from 'lucide-react';
import { DemoVerdict, ShortDemoEntry, SHORTS_DEMO } from '../data/shortsDemo';
import { PRECOMPUTED_SHORTS_RESULTS } from '../data/precomputedShortsResults';
import { runInvestigation } from '../services/investigationApi';
import type { AiVerdict, InvestigationResponse } from '../types/analysis';

const VERDICT_UI: Record<
  string,
  { icon: string; label: string; sub: string; ring: string; text: string; bg: string; badgeBg: string }
> = {
  LIKELY_AUTHENTIC: {
    icon: '🟢',
    label: 'LIKELY AUTHENTIC',
    sub: 'Consistent with authentic capture',
    ring: 'border-emerald-500/70',
    text: 'text-emerald-300',
    bg: 'bg-emerald-950/85',
    badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  },
  LIKELY_GENUINE: {
    icon: '🟢',
    label: 'LIKELY AUTHENTIC',
    sub: 'Consistent with authentic capture',
    ring: 'border-emerald-500/70',
    text: 'text-emerald-300',
    bg: 'bg-emerald-950/85',
    badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  },
  LIKELY_AI_GENERATED: {
    icon: '🔴',
    label: 'LIKELY AI-GENERATED',
    sub: 'Synthetic generation indicators detected',
    ring: 'border-red-500/70',
    text: 'text-red-300',
    bg: 'bg-red-950/85',
    badgeBg: 'bg-red-500/20 text-red-300 border-red-500/40',
  },
  HIGH_RISK: {
    icon: '🔴',
    label: 'HIGH RISK / DECEPTIVE',
    sub: 'Critical conflict or misattribution',
    ring: 'border-red-500/70',
    text: 'text-red-300',
    bg: 'bg-red-950/85',
    badgeBg: 'bg-red-500/20 text-red-300 border-red-500/40',
  },
  LIKELY_MANIPULATED: {
    icon: '🔴',
    label: 'LIKELY MANIPULATED',
    sub: 'Digital tampering detected',
    ring: 'border-rose-500/70',
    text: 'text-rose-300',
    bg: 'bg-rose-950/85',
    badgeBg: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
  },
  NOT_TRUSTWORTHY: {
    icon: '🔴',
    label: 'NOT TRUSTWORTHY',
    sub: 'Significant evidence conflict',
    ring: 'border-red-500/70',
    text: 'text-red-300',
    bg: 'bg-red-950/85',
    badgeBg: 'bg-red-500/20 text-red-300 border-red-500/40',
  },
  INCONCLUSIVE: {
    icon: '⚪',
    label: 'INCONCLUSIVE',
    sub: 'More forensic evidence needed',
    ring: 'border-slate-500/70',
    text: 'text-slate-200',
    bg: 'bg-slate-900/85',
    badgeBg: 'bg-slate-500/20 text-slate-300 border-slate-500/40',
  },
};

const PENDING_UI = {
  icon: '⚡',
  label: 'ANALYZING',
  sub: 'Auditing video evidence…',
  ring: 'border-cyan-400/70 shadow-[0_0_15px_rgba(6,182,212,0.4)]',
  text: 'text-cyan-300',
  bg: 'bg-slate-950/90',
  badgeBg: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
};

const FAILED_UI = {
  icon: '⚠️',
  label: 'ANALYSIS FAILED',
  sub: 'No verdict available',
  ring: 'border-amber-400/60',
  text: 'text-amber-300',
  bg: 'bg-slate-900/90',
  badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
};

const MAX_UPLOAD_BYTES = 30 * 1024 * 1024; // 30 MB

const FAST_ANIMATION_STEPS = [
  { label: 'Preparing video & validating stream', duration: 550, progress: 25 },
  { label: 'Scanning visual evidence & keyframes', duration: 650, progress: 55 },
  { label: 'Evaluating risk indicators & conflict', duration: 650, progress: 85 },
  { label: 'Preparing forensic investigation report', duration: 550, progress: 100 },
];

function presentationForVerdict(verdict: AiVerdict | string) {
  return VERDICT_UI[verdict] || VERDICT_UI.INCONCLUSIVE;
}

const DEMO_VIDEOS_BASE = (import.meta.env.VITE_DEMO_VIDEOS_BASE_URL || '').replace(/\/+$/, '');

function resolveVideoSrc(path: string): string {
  if (!path || path.startsWith('blob:') || path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  if (DEMO_VIDEOS_BASE) {
    return `${DEMO_VIDEOS_BASE}${path.startsWith('/') ? path : '/' + path}`;
  }
  return path;
}

function fmt(t: number) {
  if (!Number.isFinite(t) || t < 0) return '0:00';
  const m = Math.floor(t / 60);
  const sec = Math.floor(t % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

export interface ShortsCardItem extends ShortDemoEntry {
  isUploaded?: boolean;
  uploadedFile?: File;
}

function ShortCard({
  entry,
  index,
  total,
}: {
  entry: ShortsCardItem;
  index: number;
  total: number;
}) {
  const [open, setOpen] = useState(false);
  const [videoFailed, setVideoFailed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(true);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [retryKey, setRetryKey] = useState(0);

  // Analysis state
  const [analysisState, setAnalysisState] = useState<'idle' | 'loading' | 'complete' | 'error'>(
    entry.isUploaded ? 'idle' : 'complete'
  );
  const [resultSource, setResultSource] = useState<'PRECOMPUTED' | 'LIVE'>(
    entry.isUploaded ? 'LIVE' : 'PRECOMPUTED'
  );
  const [result, setResult] = useState<InvestigationResponse | null>(() => {
    return PRECOMPUTED_SHORTS_RESULTS[entry.id] || null;
  });
  const [analysisError, setAnalysisError] = useState('');
  const [animationStep, setAnimationStep] = useState(0);
  const [animationProgress, setAnimationProgress] = useState(0);

  const sectionRef = useRef<HTMLElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const userPaused = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const timerRef = useRef<NodeJS.Timeout[]>([]);

  const isComplete = analysisState === 'complete' && result !== null;
  const currentVerdict = result ? result.final.verdict : entry.demoVerdict;
  const ui =
    analysisState === 'loading'
      ? PENDING_UI
      : analysisState === 'error'
      ? FAILED_UI
      : presentationForVerdict(currentVerdict);

  const confidenceScore = result ? result.final.confidence : 85;

  // Cleanup timers & requests on unmount
  useEffect(() => {
    return () => {
      timerRef.current.forEach(clearTimeout);
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, []);

  // Keyboard shortcut: Escape closes panel
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  // Autoplay/pause when scrolling through feed
  useEffect(() => {
    const section = sectionRef.current;
    if (!section || typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver(
      ([e]) => {
        const v = videoRef.current;
        if (!v) return;
        if (e.isIntersecting && e.intersectionRatio >= 0.6) {
          if (!userPaused.current) v.play().catch(() => {});
        } else {
          v.pause();
          setOpen(false);
        }
      },
      { threshold: [0, 0.6, 1] }
    );
    io.observe(section);
    return () => io.disconnect();
  }, [retryKey, videoFailed]);

  const togglePlay = () => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) {
      userPaused.current = false;
      v.play().catch(() => {});
    } else {
      userPaused.current = true;
      v.pause();
    }
  };

  const onPlay = () => {
    setPlaying(true);
    document.querySelectorAll('video').forEach((other) => {
      if (other !== videoRef.current) other.pause();
    });
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = Number(e.target.value);
    setTime(v.currentTime);
  };

  const retry = () => {
    setVideoFailed(false);
    setLoading(true);
    setPlaying(false);
    setTime(0);
    setDuration(0);
    setRetryKey((k) => k + 1);
  };

  // Run the 2-3s fast analysis animation for precomputed demo videos
  const runFastDemoAnalysis = () => {
    if (analysisState === 'loading') return;
    timerRef.current.forEach(clearTimeout);
    timerRef.current = [];

    setAnalysisState('loading');
    setAnalysisError('');
    setAnimationStep(0);
    setAnimationProgress(15);
    setOpen(true);

    let cumulative = 0;
    FAST_ANIMATION_STEPS.forEach((step, idx) => {
      cumulative += step.duration;
      const t = setTimeout(() => {
        setAnimationStep(idx);
        setAnimationProgress(step.progress);
      }, cumulative - step.duration);
      timerRef.current.push(t);
    });

    const finalTimer = setTimeout(() => {
      const demoResult = PRECOMPUTED_SHORTS_RESULTS[entry.id];
      if (demoResult) {
        setResult(demoResult);
        setResultSource('PRECOMPUTED');
        setAnalysisState('complete');
      } else {
        setAnalysisState('error');
        setAnalysisError('No precomputed result found for this demo video.');
      }
    }, cumulative);

    timerRef.current.push(finalTimer);
  };

  // Run live backend analysis (for uploaded video or on-demand live check)
  const runLiveBackendAnalysis = async () => {
    if (analysisState === 'loading') return;
    if (abortControllerRef.current) abortControllerRef.current.abort();
    abortControllerRef.current = new AbortController();

    setAnalysisState('loading');
    setAnalysisError('');
    setAnimationStep(0);
    setAnimationProgress(20);
    setOpen(true);

    try {
      let fileToUpload: File;
      if (entry.uploadedFile) {
        fileToUpload = entry.uploadedFile;
      } else {
        // Fetch demo video file
        setAnimationStep(0);
        const resolvedPath = resolveVideoSrc(entry.video);
        const resp = await fetch(resolvedPath, { cache: 'no-store' });
        if (!resp.ok) throw new Error(`Could not load video file (HTTP ${resp.status}).`);
        const blob = await resp.blob();
        if (!blob.size) throw new Error('Video file is empty.');
        const ext = entry.video.split('.').pop()?.toLowerCase() || 'mp4';
        const mime = blob.type || (ext === 'webm' ? 'video/webm' : ext === 'mov' ? 'video/quicktime' : 'video/mp4');
        fileToUpload = new File([blob], `${entry.id}.${ext}`, { type: mime });
      }

      setAnimationStep(1);
      setAnimationProgress(50);

      const liveResponse = await runInvestigation(entry.claim, '', fileToUpload);
      if (liveResponse.serviceError) {
        throw new Error(`TrustLens backend service error: ${liveResponse.serviceError}`);
      }

      const va = liveResponse.mediaAnalysis?.videoAnalysis;
      if (va && !va.ok) {
        throw new Error(va.error || 'Video analysis pipeline encountered an error.');
      }

      setAnimationStep(3);
      setAnimationProgress(100);
      setResult(liveResponse);
      setResultSource('LIVE');
      setAnalysisState('complete');
    } catch (err: any) {
      setAnalysisState('error');
      setAnalysisError(err instanceof Error ? err.message : 'Video analysis failed.');
    }
  };

  const handleStartAnalysis = () => {
    if (entry.isUploaded) {
      runLiveBackendAnalysis();
    } else {
      runFastDemoAnalysis();
    }
  };

  const panelId = `panel-${entry.id}`;

  return (
    <section
      ref={sectionRef}
      data-short-card
      aria-label={`Short ${index + 1} of ${total}: ${entry.title}`}
      className="h-full snap-start snap-always flex items-center justify-center p-2 sm:p-4"
    >
      <div className="relative h-full aspect-[9/16] max-w-full overflow-hidden rounded-2xl border border-slate-700/70 bg-[#0B1220] shadow-2xl">
        {/* Video Player */}
        {!videoFailed && (
          <video
            key={retryKey}
            ref={videoRef}
            className="absolute inset-0 h-full w-full cursor-pointer object-cover"
            src={resolveVideoSrc(entry.video)}
            muted={muted}
            loop
            playsInline
            preload="metadata"
            aria-label={entry.title}
            onClick={togglePlay}
            onError={() => {
              setVideoFailed(true);
              setLoading(false);
              setPlaying(false);
            }}
            onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
            onLoadedData={() => setLoading(false)}
            onCanPlay={() => setLoading(false)}
            onWaiting={() => setLoading(true)}
            onPlaying={() => setLoading(false)}
            onPlay={onPlay}
            onPause={() => setPlaying(false)}
            onTimeUpdate={(e) => setTime(e.currentTarget.currentTime)}
          />
        )}

        {/* Video Failed Placeholder */}
        {videoFailed && (
          <div
            role="alert"
            className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-gradient-to-b from-slate-900 via-[#0B1220] to-slate-950 px-6 text-center"
          >
            <AlertTriangle size={32} className="text-amber-400" aria-hidden="true" />
            <p className="text-sm font-semibold text-slate-200">Video preview unavailable</p>
            <p className="text-[11px] text-slate-500 break-all">{entry.video}</p>
            <button
              type="button"
              onClick={retry}
              className="mt-1 rounded-md border border-slate-600 px-3 py-1 text-xs text-slate-200 hover:text-white"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading spinner */}
        {loading && !videoFailed && (
          <div
            className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center"
            role="status"
            aria-label="Loading video"
          >
            <Loader2 size={32} className="animate-spin text-slate-300" />
          </div>
        )}

        {/* Top-left: Category Badge */}
        <div className="absolute left-3 top-3 z-20 flex flex-col gap-1.5">
          <span
            className={`rounded-md border px-2 py-0.5 text-[10px] font-bold tracking-wider backdrop-blur-md ${
              entry.isUploaded
                ? 'border-cyan-400/60 bg-cyan-950/80 text-cyan-300'
                : 'border-amber-400/50 bg-black/70 text-amber-300'
            }`}
          >
            {entry.isUploaded ? 'UPLOADED SHORT' : 'VERIFIED DEMO'}
          </span>
          {isComplete && (
            <span
              className={`flex items-center gap-1 rounded-md border px-2 py-0.5 text-[9px] font-semibold backdrop-blur-md ${
                resultSource === 'PRECOMPUTED'
                  ? 'border-amber-500/40 bg-amber-950/80 text-amber-200'
                  : 'border-cyan-500/40 bg-cyan-950/80 text-cyan-200'
              }`}
            >
              {resultSource === 'PRECOMPUTED' ? (
                <>
                  <Zap size={10} className="text-amber-400" /> Fast Demo Result (~2s)
                </>
              ) : (
                <>
                  <Cpu size={10} className="text-cyan-400" /> Live Backend Result
                </>
              )}
            </span>
          )}
        </div>

        {/* Top-right: Verdict Overlay Button */}
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-controls={panelId}
          aria-label={`TrustLens Verdict: ${ui.label}. Click to ${open ? 'hide' : 'view'} evidence`}
          className={`absolute right-3 top-3 z-20 flex items-center gap-2 rounded-xl border px-3 py-1.5 text-right backdrop-blur-md shadow-lg transition-all ${ui.ring} ${ui.bg} hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-white`}
        >
          <div className="text-right">
            <span className={`block text-[11px] font-bold leading-tight ${ui.text}`}>
              <span aria-hidden="true">{ui.icon} </span>
              {ui.label}
            </span>
            <span className="block text-[9px] font-mono text-slate-400">
              {analysisState === 'loading'
                ? 'Auditing…'
                : isComplete
                ? `${confidenceScore}% confidence`
                : 'Tap for details'}
            </span>
          </div>
          <Shield size={16} className={ui.text} />
        </button>

        {/* Multi-stage 2-3s Analysis Progress Banner (visible over video while analyzing) */}
        {analysisState === 'loading' && (
          <div className="absolute inset-x-3 top-16 z-30 rounded-xl border border-cyan-500/50 bg-[#070B12]/95 p-3 shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center justify-between text-xs font-semibold text-cyan-300">
              <span className="flex items-center gap-2">
                <Loader2 size={14} className="animate-spin text-cyan-400" />
                {FAST_ANIMATION_STEPS[animationStep]?.label || 'Auditing video…'}
              </span>
              <span className="font-mono text-[10px] text-cyan-400">{animationProgress}%</span>
            </div>
            {/* Animated progress bar */}
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full bg-gradient-to-r from-cyan-400 via-blue-500 to-emerald-400 transition-all duration-300 ease-out"
                style={{ width: `${animationProgress}%` }}
              />
            </div>
            <div className="mt-1.5 flex justify-between text-[9px] text-slate-400 font-mono">
              <span>Step {animationStep + 1} of 4</span>
              <span>Target: ~2.4s</span>
            </div>
          </div>
        )}

        {/* Interactive Forensic Details Panel */}
        {open && (
          <div
            id={panelId}
            role="dialog"
            aria-label="TrustLens Forensic Evidence Panel"
            className="absolute inset-x-2 sm:inset-x-3 top-14 bottom-16 z-30 flex flex-col rounded-xl border border-slate-700/80 bg-[#0B1220]/95 p-3.5 shadow-2xl backdrop-blur-md overflow-hidden animate-in fade-in zoom-in-95 duration-200"
          >
            {/* Panel Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <div className="flex items-center gap-1.5">
                <ShieldCheck size={16} className="text-cyan-400" />
                <span className="text-xs font-bold font-display text-white">TrustLens Forensic Audit</span>
                <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${ui.badgeBg}`}>
                  {resultSource === 'PRECOMPUTED' ? 'PRECOMPUTED DEMO' : 'LIVE ANALYSIS'}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close details"
                className="rounded-lg p-1 text-slate-400 hover:text-white hover:bg-slate-800/60 focus:outline-none"
              >
                <X size={15} />
              </button>
            </div>

            {/* Scrollable Panel Body */}
            <div className="flex-1 overflow-y-auto space-y-3 py-2.5 pr-1 text-xs">
              {/* Verdict Banner Card */}
              <div className={`rounded-xl border p-3 ${ui.badgeBg}`}>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400">
                      Primary Risk Verdict
                    </span>
                    <h4 className={`text-sm font-bold mt-0.5 ${ui.text}`}>
                      {ui.icon} {ui.label}
                    </h4>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 font-mono block">Confidence</span>
                    <span className="text-sm font-bold font-mono text-white">{confidenceScore}%</span>
                  </div>
                </div>
                {/* Confidence Bar */}
                <div className="mt-2 h-1.5 w-full rounded-full bg-slate-900/60 overflow-hidden">
                  <div
                    className={`h-full ${
                      ui.label.includes('AUTHENTIC')
                        ? 'bg-emerald-400'
                        : ui.label.includes('INCONCLUSIVE')
                        ? 'bg-slate-400'
                        : 'bg-red-400'
                    }`}
                    style={{ width: `${confidenceScore}%` }}
                  />
                </div>
              </div>

              {/* Claim Description */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                  Verified Claim
                </span>
                <p className="text-xs text-slate-200 leading-relaxed font-sans">{entry.claim}</p>
              </div>

              {/* Trust Triangle Metrics */}
              {result?.trustTriangle && (
                <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 block mb-1.5">
                    Trust Triangle Synthesis
                  </span>
                  <div className="grid grid-cols-3 gap-2 text-center font-mono text-[10px]">
                    <div className="rounded bg-black/40 p-1.5 border border-slate-800">
                      <span className="text-slate-400 block text-[9px]">Likelihood</span>
                      <span
                        className={`font-bold ${
                          result.trustTriangle.manipulationLikelihood > 50 ? 'text-red-400' : 'text-emerald-400'
                        }`}
                      >
                        {Math.round(result.trustTriangle.manipulationLikelihood)}%
                      </span>
                    </div>
                    <div className="rounded bg-black/40 p-1.5 border border-slate-800">
                      <span className="text-slate-400 block text-[9px]">Strength</span>
                      <span className="font-bold text-cyan-300">
                        {Math.round(result.trustTriangle.evidenceStrength)}%
                      </span>
                    </div>
                    <div className="rounded bg-black/40 p-1.5 border border-slate-800">
                      <span className="text-slate-400 block text-[9px]">Conflict</span>
                      <span
                        className={`font-bold ${
                          result.trustTriangle.evidenceConflict > 40 ? 'text-amber-400' : 'text-slate-300'
                        }`}
                      >
                        {Math.round(result.trustTriangle.evidenceConflict)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Verdict Explanation */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                  Reasoning Summary
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {result?.final.summary || result?.final.reason || entry.evidenceSummary}
                </p>
              </div>

              {/* Key Indicators / Evidence */}
              {result?.final.supportingEvidence && result.final.supportingEvidence.length > 0 && (
                <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block mb-1.5">
                    Key Supporting Indicators
                  </span>
                  <ul className="space-y-1 text-[11px] text-slate-300">
                    {result.final.supportingEvidence.slice(0, 3).map((item, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <CheckCircle2 size={12} className="text-emerald-400 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Contradicting Evidence / Conflict */}
              {result?.final.contradictingEvidence && result.final.contradictingEvidence.length > 0 && (
                <div className="rounded-lg border border-amber-900/30 bg-amber-950/20 p-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block mb-1.5">
                    Contradicting Indicators & Conflict
                  </span>
                  <ul className="space-y-1 text-[11px] text-amber-200/90">
                    {result.final.contradictingEvidence.slice(0, 3).map((item, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <AlertTriangle size={12} className="text-amber-400 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Epistemic Limitations */}
              <div className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-2.5 text-[10px] text-slate-400">
                <span className="font-semibold text-slate-300 block mb-0.5 flex items-center gap-1">
                  <Info size={11} className="text-slate-400" /> Epistemic Guardrails
                </span>
                <p>
                  {result?.final.uncertainties?.[0] || entry.limitations}
                </p>
              </div>

              {/* Failure Error Display */}
              {analysisState === 'error' && (
                <div className="rounded-lg border border-red-500/50 bg-red-950/40 p-2.5 text-xs text-red-200">
                  <p className="font-semibold flex items-center gap-1.5">
                    <AlertTriangle size={14} className="text-red-400" />
                    Analysis Failed
                  </p>
                  <p className="mt-1 text-[11px] text-red-300">{analysisError}</p>
                </div>
              )}
            </div>

            {/* Panel Footer Actions */}
            <div className="border-t border-slate-800 pt-2.5 flex items-center gap-2">
              <button
                type="button"
                onClick={handleStartAnalysis}
                disabled={analysisState === 'loading' || videoFailed}
                className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-cyan-500/20 border border-cyan-400/40 px-3 py-2 text-xs font-semibold text-cyan-200 hover:bg-cyan-500/30 disabled:opacity-50 transition-colors"
              >
                {analysisState === 'loading' ? (
                  <>
                    <Loader2 size={13} className="animate-spin text-cyan-400" />
                    Auditing…
                  </>
                ) : (
                  <>
                    <Zap size={13} className="text-cyan-400" />
                    {entry.isUploaded ? 'Re-analyze Video' : 'Re-run Fast Audit (~2s)'}
                  </>
                )}
              </button>

              {!entry.isUploaded && (
                <button
                  type="button"
                  onClick={runLiveBackendAnalysis}
                  disabled={analysisState === 'loading' || videoFailed}
                  title="Run real live backend inference via /api/investigate"
                  className="rounded-lg border border-slate-700 bg-slate-800/80 p-2 text-slate-300 hover:text-white hover:bg-slate-700 disabled:opacity-50"
                >
                  <Cpu size={14} />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Bottom Bar: Video Title, Description, and Scrubber Controls */}
        <div className="absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black/95 via-black/70 to-transparent p-3 pt-10">
          <div className="pointer-events-none mb-2">
            <p className="text-sm font-semibold text-white truncate">{entry.title}</p>
            <p className="text-[11px] text-slate-300 line-clamp-1">{entry.description}</p>
          </div>

          {!videoFailed && (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={togglePlay}
                aria-label={playing ? 'Pause' : 'Play'}
                className="rounded-full bg-white/15 p-1.5 text-white hover:bg-white/25 focus:outline-none"
              >
                {playing ? <Pause size={14} /> : <Play size={14} />}
              </button>

              <input
                type="range"
                min={0}
                max={duration || 0}
                step={0.1}
                value={Math.min(time, duration || 0)}
                onChange={seek}
                disabled={!duration}
                aria-label="Seek time"
                className="h-1 min-w-0 flex-1 accent-cyan-400 cursor-pointer"
              />

              <span className="w-[5.2rem] shrink-0 text-right text-[10px] tabular-nums text-slate-300 font-mono">
                {fmt(time)} / {fmt(duration)}
              </span>

              <button
                type="button"
                onClick={() => setMuted((m) => !m)}
                aria-label={muted ? 'Unmute' : 'Mute'}
                aria-pressed={!muted}
                className="rounded-full bg-white/15 p-1.5 text-white hover:bg-white/25 focus:outline-none"
              >
                {muted ? <VolumeX size={14} /> : <Volume2 size={14} />}
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default function ShortsAnalyzer() {
  const [feedEntries, setFeedEntries] = useState<ShortsCardItem[]>(SHORTS_DEMO);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [customClaim, setCustomClaim] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const feedRef = useRef<HTMLDivElement>(null);

  const scrollByCard = useCallback((dir: 1 | -1) => {
    const el = feedRef.current;
    if (el) el.scrollBy({ top: dir * el.clientHeight, behavior: 'smooth' });
  }, []);

  const onKeyDown = (e: React.KeyboardEvent) => {
    const t = e.target as HTMLElement;
    if (t.tagName === 'VIDEO' || t.tagName === 'INPUT') return;
    if (e.key === 'ArrowDown' || e.key === 'PageDown') {
      e.preventDefault();
      scrollByCard(1);
    }
    if (e.key === 'ArrowUp' || e.key === 'PageUp') {
      e.preventDefault();
      scrollByCard(-1);
    }
  };

  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > MAX_UPLOAD_BYTES) {
      setUploadError(`Video size (${(file.size / 1048576).toFixed(1)} MB) exceeds 30 MB limit.`);
      return;
    }

    const validExtensions = ['.mp4', '.webm', '.mov', '.avi'];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));
    if (!hasValidExt && !file.type.startsWith('video/')) {
      setUploadError('Unsupported format. Please upload MP4, WebM, MOV, or AVI video.');
      return;
    }

    setUploadError(null);
    const objectUrl = URL.createObjectURL(file);
    const claim = customClaim.trim() || `Forensic investigation of uploaded video: ${file.name}`;

    const newEntry: ShortsCardItem = {
      id: `upload-${Date.now()}`,
      title: file.name.replace(/\.[^/.]+$/, ''),
      video: objectUrl,
      claim: claim,
      groundTruth: 'LEGITIMATE',
      demoVerdict: 'INCONCLUSIVE',
      description: `Uploaded user clip (${(file.size / 1048576).toFixed(1)} MB)`,
      evidenceSummary: 'Live backend investigation pending.',
      evidenceStrength: 'Moderate',
      evidenceConflict: 'None',
      limitations: 'Live forensic analysis executed against user-supplied video bytes.',
      isUploaded: true,
      uploadedFile: file,
    };

    setFeedEntries((prev) => [newEntry, ...prev]);
    setIsModalOpen(false);
    setCustomClaim('');
    if (fileInputRef.current) fileInputRef.current.value = '';

    // Scroll back to top to view new upload
    setTimeout(() => {
      if (feedRef.current) feedRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }, 100);
  };

  return (
    <section id="shorts-analyzer" aria-label="Shorts Analyzer" className="flex h-[calc(100dvh-4rem)] flex-col">
      {/* Top Header Controls Bar */}
      <div className="mx-auto w-full max-w-7xl shrink-0 px-4 py-2 sm:px-6 lg:px-8 border-b border-slate-900/60 bg-[#070B12]/80 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold text-white font-display flex items-center gap-1.5">
                <Sparkles size={14} className="text-cyan-400" />
                Shorts Analyzer
              </h1>
              <span className="rounded-full bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.2 text-[10px] font-mono text-cyan-300">
                Fast Audit (~2–3s)
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Swipe or use arrow keys to audit short-form video evidence. Predefined clips return verified forensic verdicts in ~2s.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-3 py-1.5 text-xs font-semibold text-black hover:from-cyan-400 hover:to-blue-500 shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all cursor-pointer"
            >
              <Upload size={13} className="text-black" />
              <span>Upload Your Short</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Snap Feed View */}
      <div className="relative min-h-0 flex-1">
        <div
          ref={feedRef}
          tabIndex={0}
          role="feed"
          aria-label="TrustLens Shorts Analyzer feed"
          onKeyDown={onKeyDown}
          className="h-full snap-y snap-mandatory overflow-y-scroll focus:outline-none"
        >
          {feedEntries.map((entry, i) => (
            <ShortCard key={entry.id} entry={entry} index={i} total={feedEntries.length} />
          ))}
        </div>

        {/* Up / Down Navigation Controls */}
        <div className="absolute bottom-4 right-3 z-40 hidden flex-col gap-2 sm:flex">
          <button
            type="button"
            onClick={() => scrollByCard(-1)}
            aria-label="Previous short"
            className="rounded-full border border-slate-700 bg-black/70 p-2 text-slate-300 hover:text-white hover:bg-black/90 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
          >
            <ChevronUp size={18} />
          </button>
          <button
            type="button"
            onClick={() => scrollByCard(1)}
            aria-label="Next short"
            className="rounded-full border border-slate-700 bg-black/70 p-2 text-slate-300 hover:text-white hover:bg-black/90 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
          >
            <ChevronDown size={18} />
          </button>
        </div>
      </div>

      {/* Upload Video Modal */}
      {isModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200"
        >
          <div className="w-full max-w-md rounded-2xl border border-cyan-500/30 bg-[#0B1220] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FileVideo size={20} className="text-cyan-400" />
                <h3 className="text-base font-bold text-white font-display">Upload Video for Live Audit</h3>
              </div>
              <button
                type="button"
                onClick={() => {
                  setIsModalOpen(false);
                  setUploadError(null);
                }}
                className="rounded-lg p-1 text-slate-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Claim to verify (optional)
              </label>
              <input
                type="text"
                value={customClaim}
                onChange={(e) => setCustomClaim(e.target.value)}
                placeholder="e.g. This video shows an authentic event in..."
                className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-400 focus:outline-none"
              />
            </div>

            <div className="rounded-xl border-2 border-dashed border-slate-700 p-6 text-center hover:border-cyan-400/50 transition-colors">
              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/webm,video/quicktime,video/x-msvideo,.mp4,.webm,.mov,.avi"
                onChange={handleFileSelected}
                className="hidden"
                id="shorts-video-file-input"
              />
              <label htmlFor="shorts-video-file-input" className="cursor-pointer block space-y-2">
                <Upload size={28} className="mx-auto text-cyan-400" />
                <p className="text-xs font-semibold text-slate-200">
                  Click to select video (MP4, WebM, MOV)
                </p>
                <p className="text-[11px] text-slate-500">
                  Maximum file size: 30 MB · Up to 3 representative frames sampled
                </p>
              </label>
            </div>

            {uploadError && (
              <div className="rounded-xl border border-red-500/40 bg-red-950/40 p-3 text-xs text-red-300 flex items-start gap-2">
                <AlertTriangle size={15} className="text-red-400 shrink-0 mt-0.5" />
                <span>{uploadError}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
