import React, { useState } from 'react';
import { 
  X, 
  Play, 
  Pause, 
  Video, 
  Cpu, 
  Layers, 
  Eye, 
  Search, 
  ShieldCheck, 
  AlertTriangle,
  RotateCcw
} from 'lucide-react';

interface MediaInspectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  mediaName: string;
}

export const MediaInspectionModal: React.FC<MediaInspectionModalProps> = ({
  isOpen,
  onClose,
  mediaName
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [activeOverlay, setActiveOverlay] = useState<'optical_flow' | 'archive_match' | 'sensor_noise'>('archive_match');
  const [currentFrameTime, setCurrentFrameTime] = useState<number>(4.2);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/85 backdrop-blur-md overflow-y-auto animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden my-6">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-950 border border-cyan-500/40 text-cyan-400">
              <Video className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                FORENSIC MEDIA INSPECTOR: {mediaName}
              </h3>
              <span className="text-[10px] text-cyan-400 font-mono">
                SIMULATED ANALYSIS · Demo visualization only, no real media was processed
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

        {/* Body */}
        <div className="p-6 space-y-6">
          
          {/* Simulated Forensic Video Player HUD */}
          <div className="relative aspect-video rounded-xl border border-slate-700 bg-[#060A14] overflow-hidden flex flex-col justify-between">
            {/* Visual simulation of urban flood scene with forensic HUD overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-slate-900/60 via-slate-950/80 to-[#040711] flex items-center justify-center">
              
              {/* Synthetic forensic scene graphics */}
              <div className="relative w-full h-full flex flex-col items-center justify-center text-center p-6 select-none">
                
                {/* Background storm / flood water simulation grid */}
                <div className="absolute inset-0 forensic-grid opacity-30 pointer-events-none" />

                {/* Submerged Car & Waterline Vector Visualization */}
                <div className="relative z-10 space-y-3">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-black/70 border border-cyan-500/40 font-mono text-[11px] text-cyan-300">
                    <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                    <span>SCENE TARGET: Submerged Urban Vehicles (Bellandur Ring Road)</span>
                  </div>

                  {/* Comparison split screen if archive match is toggled */}
                  {activeOverlay === 'archive_match' && (
                    <div className="grid grid-cols-2 gap-4 max-w-lg mx-auto bg-slate-950/90 p-3 rounded-lg border border-amber-500/40 text-left">
                      <div className="space-y-1">
                        <span className="text-[10px] font-mono text-cyan-400 font-bold block">
                          CLAIMED VIRAL CLIP (TODAY)
                        </span>
                        <div className="h-24 rounded bg-slate-900 border border-slate-700 flex flex-col items-center justify-center text-[11px] text-slate-400 p-2 text-center">
                          <span className="text-white font-mono font-bold">Keyframe 04:12</span>
                          <span className="text-[10px] text-slate-500">Water depth ~0.8m · White SUV</span>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <span className="text-[10px] font-mono text-rose-400 font-bold block">
                          ARCHIVE: 2022-08-29
                        </span>
                        <div className="h-24 rounded bg-rose-950/30 border border-rose-500/40 flex flex-col items-center justify-center text-[11px] text-rose-300 p-2 text-center">
                          <span className="text-rose-200 font-mono font-bold">Keyframe Match (94.2%)</span>
                          <span className="text-[10px] text-rose-400">Identical shop banner in background</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeOverlay === 'optical_flow' && (
                    <div className="max-w-md mx-auto bg-slate-950/90 p-3 rounded-lg border border-cyan-500/40 text-xs font-mono text-cyan-300">
                      <div className="flex items-center justify-between pb-1 mb-1 border-b border-cyan-500/20 text-[10px]">
                        <span>OPTICAL FLOW VECTORS: NOMINAL</span>
                        <span>DIVERGENCE: 0.02</span>
                      </div>
                      <p className="text-[11px] text-slate-300 font-sans">
                        Fluid dynamics match natural laminar turbulent surface ripple. No generative diffusion seams or synthetic warping discovered.
                      </p>
                    </div>
                  )}

                  {activeOverlay === 'sensor_noise' && (
                    <div className="max-w-md mx-auto bg-slate-950/90 p-3 rounded-lg border border-emerald-500/40 text-xs font-mono text-emerald-300">
                      <div className="flex items-center justify-between pb-1 mb-1 border-b border-emerald-500/20 text-[10px]">
                        <span>PRNU SENSOR PROFILE: PHYSICAL CMOS</span>
                        <span>ISO: 400</span>
                      </div>
                      <p className="text-[11px] text-slate-300 font-sans">
                        Consistent Bayer filter pixel crosstalk confirms authentic camera optics capture.
                      </p>
                    </div>
                  )}
                </div>

                {/* Scanline line */}
                <div className="absolute inset-x-0 top-1/2 h-0.5 bg-cyan-500/40 pointer-events-none" />
              </div>
            </div>

            {/* Video HUD Top Overlay */}
            <div className="relative z-20 flex items-center justify-between p-3 bg-gradient-to-b from-black/80 to-transparent text-[11px] font-mono text-slate-300">
              <span className="text-cyan-400 font-bold">● REC LIVE ANALYSIS</span>
              <span>TIMECODE: 00:0{Math.floor(currentFrameTime)}.{Math.floor((currentFrameTime % 1) * 60)} / 00:15.00</span>
              <span className="text-amber-400">FPS: 24.0 (VFR)</span>
            </div>

            {/* Video HUD Bottom Controls */}
            <div className="relative z-20 p-3 bg-gradient-to-t from-black/90 to-transparent space-y-2">
              {/* Scrubber slider */}
              <input
                type="range"
                min="0"
                max="15"
                step="0.1"
                value={currentFrameTime}
                onChange={(e) => setCurrentFrameTime(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
              />

              <div className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="flex items-center gap-1.5 px-3 py-1 rounded bg-cyan-500 text-black font-bold hover:bg-cyan-400 transition-colors cursor-pointer"
                  >
                    {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                    <span>{isPlaying ? 'PAUSE' : 'PLAY'}</span>
                  </button>

                  <button
                    onClick={() => setCurrentFrameTime(0)}
                    className="p-1 rounded text-slate-400 hover:text-white transition-colors cursor-pointer"
                    title="Rewind to start"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* Overlay layer switches */}
                <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded border border-slate-800">
                  <button
                    onClick={() => setActiveOverlay('archive_match')}
                    className={`px-2 py-0.5 rounded text-[10px] transition-colors cursor-pointer ${
                      activeOverlay === 'archive_match' ? 'bg-amber-500/20 text-amber-300 font-bold' : 'text-slate-400'
                    }`}
                  >
                    Archive Diff
                  </button>
                  <button
                    onClick={() => setActiveOverlay('optical_flow')}
                    className={`px-2 py-0.5 rounded text-[10px] transition-colors cursor-pointer ${
                      activeOverlay === 'optical_flow' ? 'bg-cyan-500/20 text-cyan-300 font-bold' : 'text-slate-400'
                    }`}
                  >
                    Optical Flow
                  </button>
                  <button
                    onClick={() => setActiveOverlay('sensor_noise')}
                    className={`px-2 py-0.5 rounded text-[10px] transition-colors cursor-pointer ${
                      activeOverlay === 'sensor_noise' ? 'bg-emerald-500/20 text-emerald-300 font-bold' : 'text-slate-400'
                    }`}
                  >
                    Sensor Noise
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Forensic Metadata Breakdown Table */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
            <div className="rounded-lg border border-slate-800 bg-slate-950 p-3 space-y-1">
              <span className="text-[10px] text-slate-500 block">EXIF / QUICKTIME ATOMS</span>
              <span className="text-rose-400 font-bold block">STRIPPED / NULL</span>
              <p className="text-[11px] text-slate-400 font-sans">
                Original capture timestamp metadata removed during TikTok transcoding.
              </p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950 p-3 space-y-1">
              <span className="text-[10px] text-slate-500 block">PERCEPTUAL HASH (dHash)</span>
              <span className="text-amber-400 font-bold block">0x9a8f23e410bc</span>
              <p className="text-[11px] text-slate-400 font-sans">
                Matched August 29, 2022 YouTube archive record with 94.2% structural similarity.
              </p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950 p-3 space-y-1">
              <span className="text-[10px] text-slate-500 block">AI GENERATIVE ARTIFACTS</span>
              <span className="text-emerald-400 font-bold block">NEGATIVE (0.04)</span>
              <p className="text-[11px] text-slate-400 font-sans">
                Real camera sensor optics confirmed. The footage is genuine, but outdated.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 bg-slate-950 px-6 py-4 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors cursor-pointer"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
