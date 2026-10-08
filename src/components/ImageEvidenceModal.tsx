import React from 'react';
import {
  X,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Camera,
  MapPin,
  Hash,
  Activity,
  Cpu,
  Layers,
  Info,
  CheckCircle2,
  FileImage,
  Sliders,
  Sparkles,
  Search,
} from 'lucide-react';
import type { ImageAnalysisResponse } from '../types/imageAnalysis';

interface ImageEvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: ImageAnalysisResponse | null;
  imagePreviewUrl?: string | null;
}

export const ImageEvidenceModal: React.FC<ImageEvidenceModalProps> = ({
  isOpen,
  onClose,
  data,
  imagePreviewUrl,
}) => {
  if (!isOpen || !data) return null;

  const { file, evidenceHealth, metadata, ela, ocr, computerVision, evidence, limitations } = data;

  const getHealthBadgeColor = (status: string) => {
    switch (status) {
      case 'EXCELLENT':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'GOOD':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
      case 'FAIR':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'POOR':
      case 'UNUSABLE':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/40';
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/85 backdrop-blur-md overflow-y-auto animate-in fade-in duration-200">
      <div className="relative w-full max-w-5xl rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden my-6 max-h-[90vh] flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-6 py-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-950 border border-cyan-500/40 text-cyan-400">
              <FileImage className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white font-mono">
                  IMAGE EVIDENCE INSPECTION: {file.filename}
                </h3>
                <span className="text-[10px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 px-2 py-0.5 rounded font-mono font-semibold">
                  REAL PHASE 4 MEASUREMENTS
                </span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                SHA-256 · File Health · EXIF · ELA · OCR · Perceptual Hashes (Zero Fabricated Metrics)
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1 font-sans">
          
          {/* Top Summary Banner: Image Preview + Primary File Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* Visual Thumbnail */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-3 flex flex-col items-center justify-center min-h-[160px]">
              {imagePreviewUrl ? (
                <div className="relative w-full h-40 rounded-lg overflow-hidden border border-slate-700/60 flex items-center justify-center bg-black/60">
                  <img
                    src={imagePreviewUrl}
                    alt={file.filename}
                    className="max-h-full max-w-full object-contain"
                  />
                  <div className="absolute bottom-1 right-1 bg-black/70 px-2 py-0.5 rounded text-[10px] font-mono text-cyan-300">
                    {file.width} × {file.height}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center text-slate-500 text-xs font-mono py-6">
                  <FileImage className="h-10 w-10 text-slate-600 mb-2" />
                  <span>{file.format} Payload</span>
                </div>
              )}
            </div>

            {/* Evidence Health Score Card */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                    <Activity className="h-3.5 w-3.5" /> File Health
                  </span>
                  <span className={`text-xs font-mono px-2 py-0.5 rounded font-bold border ${getHealthBadgeColor(evidenceHealth.status)}`}>
                    {evidenceHealth.status} ({evidenceHealth.score}/100)
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 mb-3 overflow-hidden">
                  <div
                    className={`h-2 rounded-full ${
                      evidenceHealth.score >= 70
                        ? 'bg-emerald-400'
                        : evidenceHealth.score >= 45
                        ? 'bg-cyan-400'
                        : 'bg-amber-400'
                    }`}
                    style={{ width: `${Math.max(5, evidenceHealth.score)}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed">
                  Measures the technical utility, decode integrity, and forensic test suitability of the file.
                </p>
              </div>

              <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[10px] font-mono text-slate-400 flex items-center gap-1.5">
                <Info className="h-3 w-3 text-cyan-400 shrink-0" />
                <span>Health ≠ Authenticity. A healthy image is not necessarily genuine.</span>
              </div>
            </div>

            {/* Technical File Specifications */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-1.5 text-xs font-mono">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 block mb-1">
                File Integrity & Specs
              </span>
              <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                <span className="text-slate-400">Format:</span>
                <span className="text-cyan-300 font-bold">{file.format} ({file.mimeType})</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                <span className="text-slate-400">Dimensions:</span>
                <span className="text-white font-semibold">{file.width} × {file.height} ({file.aspectRatio})</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                <span className="text-slate-400">Megapixels:</span>
                <span className="text-white">{file.megapixels} MP</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                <span className="text-slate-400">File Size:</span>
                <span className="text-white">{formatBytes(file.sizeBytes)}</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                <span className="text-slate-400">SHA-256:</span>
                <span className="text-cyan-300 font-mono text-[10px] truncate max-w-[140px]" title={file.sha256}>
                  {file.sha256 ? `${file.sha256.slice(0, 14)}…` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-slate-400">Color Mode:</span>
                <span className="text-cyan-300">{file.imageMode}</span>
              </div>
            </div>

          </div>

          {/* Section: Evidence Health Signals & Technical Notes */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-2.5">
            <h4 className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-cyan-400" /> Technical Health Signals
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
              {evidenceHealth.signals.map((sig, i) => (
                <div key={i} className="flex items-start gap-2 bg-slate-900/60 p-2 rounded border border-slate-800/80">
                  <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400 mt-0.5 shrink-0" />
                  <span className="text-slate-300 text-[11px] leading-tight">{sig}</span>
                </div>
              ))}
            </div>
            {evidenceHealth.compressionIndicators && (
              <div className="mt-2 pt-2 border-t border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
                <div className="text-slate-300 font-semibold">Compression & Quantization Analysis:</div>
                {evidenceHealth.compressionIndicators.notes.map((note, idx) => (
                  <p key={idx} className="text-slate-400 pl-2 border-l border-slate-700">
                    • {note}
                  </p>
                ))}
              </div>
            )}
          </div>

          {/* Three-Column Grid: EXIF, ELA, and OCR */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* EXIF / Metadata Card */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-3 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Camera className="h-3.5 w-3.5 text-cyan-400" /> EXIF Metadata
                  </h4>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
                    metadata.available
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      : 'bg-slate-700/30 text-slate-400 border-slate-700'
                  }`}>
                    {metadata.available ? `EXIF (${(metadata.metadataStatus || 'present').toUpperCase()})` : 'UNAVAILABLE (NEUTRAL)'}
                  </span>
                </div>

                <div className="space-y-1.5 text-xs font-mono bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
                  <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                    <span className="text-slate-400">Camera:</span>
                    <span className="text-white font-medium truncate max-w-[130px]">
                      {metadata.cameraMake || metadata.cameraModel
                        ? `${metadata.cameraMake || ''} ${metadata.cameraModel || ''}`.trim()
                        : 'Not recorded'}
                    </span>
                  </div>
                  <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                    <span className="text-slate-400">Software:</span>
                    <span className="text-white font-medium truncate max-w-[130px]">{metadata.software || 'Not recorded'}</span>
                  </div>
                  {metadata.editingSoftware && (
                    <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                      <span className="text-amber-400 font-semibold">Editor:</span>
                      <span className="text-amber-300 font-bold truncate max-w-[130px]">{metadata.editingSoftware}</span>
                    </div>
                  )}
                  <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                    <span className="text-slate-400">Timestamp:</span>
                    <span className="text-cyan-300 font-medium truncate max-w-[130px]">{metadata.timestamp || 'Not recorded'}</span>
                  </div>
                  <div className="flex justify-between py-0.5">
                    <span className="text-slate-400 flex items-center gap-1">
                      <MapPin className="h-3 w-3 text-cyan-400" /> GPS:
                    </span>
                    <span className={`font-semibold ${metadata.gpsPresent ? 'text-amber-300' : 'text-slate-400'}`}>
                      {metadata.gpsPresent ? 'Present (Shielded)' : 'None'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="text-[10px] font-mono text-slate-400 space-y-1 pt-2 border-t border-slate-800/60">
                <p className="text-slate-400 leading-tight">
                  • Missing metadata is NOT evidence of tampering (social apps strip EXIF).
                </p>
              </div>
            </div>

            {/* Error Level Analysis (ELA) Card */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-3 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="h-3.5 w-3.5 text-cyan-400" /> Error Level Analysis
                  </h4>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
                    ela?.available
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      : 'bg-slate-700/30 text-slate-400 border-slate-700'
                  }`}>
                    {ela?.available ? 'MEASURED (Q90)' : (ela?.status || 'UNAVAILABLE').toUpperCase()}
                  </span>
                </div>

                {ela?.available ? (
                  <div className="space-y-1.5 text-xs font-mono bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
                    <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                      <span className="text-slate-400">Baseline Quality:</span>
                      <span className="text-cyan-300 font-semibold">Q{ela.qualityFactorTested}</span>
                    </div>
                    <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                      <span className="text-slate-400">Mean Error Diff:</span>
                      <span className="text-white font-bold">{ela.meanError}</span>
                    </div>
                    <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                      <span className="text-slate-400">Max Error:</span>
                      <span className="text-white">{ela.maxError}</span>
                    </div>
                    <div className="flex justify-between py-0.5 border-b border-slate-800/60">
                      <span className="text-slate-400">Error Variance:</span>
                      <span className="text-white">{ela.errorVariance}</span>
                    </div>
                    <div className="flex justify-between py-0.5">
                      <span className="text-slate-400">High-Error Pixels:</span>
                      <span className="text-cyan-300">
                        {ela.highErrorRatio !== null && ela.highErrorRatio !== undefined
                          ? `${(ela.highErrorRatio * 100).toFixed(1)}%`
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800/80 text-center py-4">
                    <p className="text-xs font-mono text-slate-400">
                      {ela?.status === 'not_applicable_non_jpeg'
                        ? `Not applicable for ${file.format} (lossless container).`
                        : 'ELA unavailable for this file.'}
                    </p>
                  </div>
                )}
              </div>

              <div className="text-[10px] font-mono text-slate-400 space-y-1 pt-2 border-t border-slate-800/60">
                <p className="text-slate-400 leading-tight">
                  • ELA measures recompression differentials. Not a fake manipulation probability.
                </p>
              </div>
            </div>

            {/* OCR Text Extraction Card */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-3 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
                    <FileText className="h-3.5 w-3.5 text-cyan-400" /> Optical Character Recognition
                  </h4>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
                    ocr.status === 'SUCCESS'
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      : ocr.status === 'NO_TEXT_DETECTED' || ocr.status === 'NO_TEXT_FOUND'
                      ? 'bg-slate-700/30 text-slate-400 border-slate-700'
                      : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  }`}>
                    {ocr.status}
                  </span>
                </div>

                {ocr.available && ocr.text ? (
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-[11px] font-mono text-slate-400">
                      <span>Quality: {(ocr.ocrQuality || 'high').toUpperCase()}</span>
                      <span>Confidence: {ocr.confidence ? `${ocr.confidence}%` : 'N/A'}</span>
                    </div>
                    <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-700 font-mono text-xs text-cyan-200 max-h-24 overflow-y-auto whitespace-pre-wrap">
                      {ocr.text}
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800/80 text-center py-4">
                    <FileText className="h-6 w-6 text-slate-600 mx-auto mb-1" />
                    <p className="text-xs font-mono text-slate-400">
                      {ocr.status === 'NO_TEXT_DETECTED' || ocr.status === 'NO_TEXT_FOUND'
                        ? 'No readable text in image bounds.'
                        : 'Engine unavailable on host.'}
                    </p>
                  </div>
                )}
              </div>

              <div className="text-[10px] font-mono text-slate-400 space-y-1 pt-2 border-t border-slate-800/60">
                <p className="text-slate-400 leading-tight">
                  • OCR text represents visual evidence requiring independent verification.
                </p>
              </div>
            </div>

          </div>

          {/* Section: Computer Vision Measurements */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5 text-cyan-400" /> Computer Vision Measurements (Deterministic Signals)
              </h4>
              <span className="text-[10px] font-mono text-slate-400">
                100% Real Algorithms · Zero Simulated Values
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              
              <div className="bg-slate-900/70 p-3 rounded-lg border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 block mb-1">Sharpness (Laplacian)</span>
                <span className="text-base font-bold font-mono text-white block">
                  {computerVision.sharpnessScore}
                </span>
                <span className="text-[9px] font-mono text-cyan-400 uppercase">
                  {computerVision.sharpnessAssessment}
                </span>
              </div>

              <div className="bg-slate-900/70 p-3 rounded-lg border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 block mb-1">Mean Brightness</span>
                <span className="text-base font-bold font-mono text-white block">
                  {computerVision.brightnessMean}
                </span>
                <span className="text-[9px] font-mono text-cyan-400 uppercase">
                  {computerVision.brightnessAssessment}
                </span>
              </div>

              <div className="bg-slate-900/70 p-3 rounded-lg border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 block mb-1">RMS Contrast</span>
                <span className="text-base font-bold font-mono text-white block">
                  {computerVision.contrastRms}
                </span>
                <span className="text-[9px] font-mono text-slate-400 uppercase">
                  Pixel standard dev
                </span>
              </div>

              <div className="bg-slate-900/70 p-3 rounded-lg border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 block mb-1">Edge Density</span>
                <span className="text-base font-bold font-mono text-white block">
                  {computerVision.edgeDensity}%
                </span>
                <span className="text-[9px] font-mono text-slate-400 uppercase">
                  Spatial gradient
                </span>
              </div>

              <div className="bg-slate-900/70 p-3 rounded-lg border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 block mb-1">Noise Variance</span>
                <span className="text-base font-bold font-mono text-white block">
                  {computerVision.noiseVariance}
                </span>
                <span className="text-[9px] font-mono text-slate-400 uppercase">
                  High-freq residual
                </span>
              </div>

              <div className="bg-slate-900/70 p-3 rounded-lg border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 block mb-1">Perceptual Hash</span>
                <span className="text-xs font-bold font-mono text-cyan-300 block truncate" title={computerVision.perceptualHashPhash}>
                  pHash
                </span>
                <span className="text-[9px] font-mono text-slate-400 uppercase">
                  64-bit DCT
                </span>
              </div>

            </div>

            {/* Perceptual Hashes Box */}
            <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800/80 font-mono text-xs space-y-1.5">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-1">
                <span className="text-slate-400 flex items-center gap-1">
                  <Hash className="h-3.5 w-3.5 text-cyan-400" /> Difference Hash (dHash):
                </span>
                <span className="text-cyan-300 font-bold tracking-wider">{computerVision.perceptualHashDhash}</span>
              </div>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-1">
                <span className="text-slate-400 flex items-center gap-1">
                  <Hash className="h-3.5 w-3.5 text-cyan-400" /> Perceptual DCT Hash (pHash):
                </span>
                <span className="text-cyan-300 font-bold tracking-wider">{computerVision.perceptualHashPhash}</span>
              </div>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-1 pt-1 border-t border-slate-800">
                <span className="text-slate-400 flex items-center gap-1">
                  <Search className="h-3.5 w-3.5 text-slate-500" /> Archival Reference Comparison:
                </span>
                <span className="text-slate-400 italic">Unavailable (No reference image provided)</span>
              </div>
              <p className="text-[10px] text-slate-500 pt-1">
                * Perceptual hashes enable cross-dataset matching against reference archives; hashes do not assert authenticity independently.
              </p>
            </div>
          </div>

          {/* Section: Forensic Test Reliability & Availability Ledger */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-3">
            <h4 className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-cyan-400" /> Forensic Test Usability Ledger
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 text-xs font-mono">
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">File Integrity:</span>
                <span className="text-emerald-400 font-semibold">Available</span>
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">Dimensions/Resolution:</span>
                <span className="text-emerald-400 font-semibold">Available</span>
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">Perceptual Hashing:</span>
                <span className="text-emerald-400 font-semibold">Available</span>
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">EXIF Metadata:</span>
                <span className={metadata.available ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
                  {metadata.available ? 'Available' : 'Unavailable (0 pts)'}
                </span>
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">Error Level Analysis:</span>
                <span className={ela?.available ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
                  {ela?.available ? 'Available' : 'Not Applicable'}
                </span>
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">OCR Extraction:</span>
                <span className={ocr.available ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
                  {ocr.available ? 'Available' : 'Unavailable'}
                </span>
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">Multimodal AI Inspection:</span>
                <span className={data.multimodalAi ? 'text-emerald-400 font-semibold' : 'text-slate-500 italic'}>
                  {data.multimodalAi ? `Evaluated (${data.multimodalAi.aiGenerationAssessment.replace(/_/g, ' ')})` : 'Unavailable'}
                </span>
              </div>

              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">PRNU Sensor Profile:</span>
                <span className="text-slate-500 italic">Unavailable</span>
              </div>
            </div>
            <p className="text-[10.5px] font-mono text-slate-500 pt-1">
              * Epistemic Rule: Unavailable modules contribute zero evidence. An unavailable test is NEVER treated as negative or suspicious evidence.
            </p>
          </div>

          {/* Section: Structured Evidence Ledger */}
          {evidence && evidence.length > 0 && (
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-3">
              <h4 className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
                <Sliders className="h-3.5 w-3.5 text-cyan-400" /> Extracted Evidence Items
              </h4>
              <div className="space-y-2">
                {evidence.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-mono"
                  >
                    <div className="flex items-start gap-2">
                      <span className="text-cyan-400 font-bold uppercase text-[10px] bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                        {item.evidenceType || item.category || 'OBSERVATION'}
                      </span>
                      <span className="text-slate-200">{item.observation}</span>
                    </div>
                    <span className="text-[10px] font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded shrink-0 self-start sm:self-center">
                      Tier: {item.reliabilityTier || item.reliability || 'TECHNICAL'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section: Phase 5 Multimodal AI Visual Assessment */}
          {data.multimodalAi && (
            <div className="rounded-xl border border-cyan-500/30 bg-slate-950/70 p-4 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-cyan-400" />
                  <h4 className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider">
                    MULTIMODAL AI VISUAL ASSESSMENT (PHASE 5)
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-2.5 py-1 rounded font-mono font-bold border ${
                      data.multimodalAi.aiGenerationAssessment === 'likely_ai_generated'
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : data.multimodalAi.aiGenerationAssessment === 'likely_authentic'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : data.multimodalAi.aiGenerationAssessment === 'possibly_manipulated'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-slate-500/20 text-slate-300 border-slate-500/40'
                    }`}
                  >
                    {data.multimodalAi.aiGenerationAssessment.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <span className="text-xs font-mono text-cyan-200 bg-cyan-950/80 px-2.5 py-1 rounded border border-cyan-800">
                    Confidence: {(data.multimodalAi.confidence * 100).toFixed(1)}% ({data.multimodalAi.confidence.toFixed(2)})
                  </span>
                </div>
              </div>

              {data.multimodalAi.explanation && (
                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-sans text-slate-200 leading-relaxed">
                  <span className="text-cyan-400 font-bold block font-mono text-[11px] mb-1">
                    AI ASSESSMENT EXPLANATION
                  </span>
                  {data.multimodalAi.explanation}
                </div>
              )}

              {data.multimodalAi.visualFindings && data.multimodalAi.visualFindings.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-mono text-slate-400 font-semibold block">
                    KEY VISUAL FINDINGS ({data.multimodalAi.visualFindings.length})
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {data.multimodalAi.visualFindings.map((finding, idx) => (
                      <div
                        key={idx}
                        className="p-2 rounded bg-slate-900/50 border border-slate-800 text-xs font-mono text-slate-300 flex items-start gap-2"
                      >
                        <span className="text-cyan-400 font-bold shrink-0">[{idx + 1}]</span>
                        <span>{finding}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {data.multimodalAi.supportingSignals && data.multimodalAi.supportingSignals.length > 0 && (
                  <div className="space-y-1.5 p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30">
                    <span className="text-[11px] font-mono text-emerald-300 font-bold block flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      SUPPORTING SIGNALS
                    </span>
                    <div className="space-y-1 text-xs font-mono text-emerald-100">
                      {data.multimodalAi.supportingSignals.map((sig, idx) => (
                        <p key={idx} className="flex items-start gap-1.5 text-[11px]">
                          <span className="text-emerald-400">✓</span>
                          <span>{sig}</span>
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {data.multimodalAi.contradictingSignals && data.multimodalAi.contradictingSignals.length > 0 && (
                  <div className="space-y-1.5 p-3 rounded-lg bg-rose-950/20 border border-rose-500/30">
                    <span className="text-[11px] font-mono text-rose-300 font-bold block flex items-center gap-1.5">
                      <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
                      CONTRADICTING / COMPLICATING SIGNALS
                    </span>
                    <div className="space-y-1 text-xs font-mono text-rose-100">
                      {data.multimodalAi.contradictingSignals.map((sig, idx) => (
                        <p key={idx} className="flex items-start gap-1.5 text-[11px]">
                          <span className="text-rose-400">⚠</span>
                          <span>{sig}</span>
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1">
                <span>Model: {data.multimodalAi.modelUsed || 'Vision Model'} · Provider: {data.multimodalAi.providerUsed || 'Groq'}</span>
                <span>Visual inspection is candidate evidence, not ground truth</span>
              </div>
            </div>
          )}


          {/* Section: Forensic Limitations & Scientific Caveats */}
          <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 space-y-2">
            <h4 className="text-xs font-mono font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle className="h-4 w-4 text-amber-400" /> Epistemic Boundaries & Forensic Limitations
            </h4>
            <div className="space-y-1.5 text-xs text-slate-300 font-mono">
              {limitations.map((lim, idx) => (
                <p key={idx} className="flex items-start gap-2 text-[11px] leading-relaxed">
                  <span className="text-amber-400 shrink-0 font-bold">[{idx + 1}]</span>
                  <span>{lim}</span>
                </p>
              ))}
            </div>
          </div>

        </div>

        {/* Footer Actions */}
        <div className="border-t border-slate-800 bg-slate-950 px-6 py-3.5 flex justify-between items-center shrink-0">
          <span className="text-[11px] font-mono text-slate-500">
            Phase 4 Genuine Forensics · TrustLens Multi-Pillar Architecture
          </span>
          <button
            onClick={onClose}
            className="rounded-lg bg-slate-800 hover:bg-slate-700 px-4 py-2 text-xs font-mono text-white transition-colors cursor-pointer"
          >
            Close Inspector
          </button>
        </div>

      </div>
    </div>
  );
};
