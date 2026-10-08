import React, { useState } from 'react';
import { 
  Search, 
  Sparkles, 
  Film, 
  Link2, 
  FileText, 
  ImageIcon, 
  AlertTriangle, 
  ArrowRight, 
  Layers, 
  Fingerprint, 
  GitFork, 
  CheckCircle2,
  Upload,
  RefreshCw,
  Eye,
  Trash2,
  Activity,
  FileImage
} from 'lucide-react';
import { InputTab } from '../types/investigation';
import { analyzeImage } from '../services/investigationApi';
import type { ImageAnalysisResponse } from '../types/imageAnalysis';
import { ImageEvidenceModal } from './ImageEvidenceModal';

interface LandingHeroProps {
  onInvestigate: (claim: string, mediaName?: string, url?: string, isDemo?: boolean, file?: File | null) => void;
  onPopulateDemo: () => void;
  claim: string;
  setClaim: (val: string) => void;
  mediaName: string;
  setMediaName: (val: string) => void;
  url: string;
  setUrl: (val: string) => void;
  isDemoPopulated: boolean;
}

export const LandingHero: React.FC<LandingHeroProps> = ({
  onInvestigate,
  onPopulateDemo,
  claim,
  setClaim,
  mediaName,
  setUrl,
  url,
  isDemoPopulated
}) => {
  const [activeTab, setActiveTab] = useState<InputTab>('CLAIM');
  const [error, setError] = useState<string>('');

  // Phase 4 Real Image Analysis State
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [isAnalyzingImage, setIsAnalyzingImage] = useState<boolean>(false);
  const [imageAnalysisResult, setImageAnalysisResult] = useState<ImageAnalysisResponse | null>(null);
  const [imageError, setImageError] = useState<string>('');
  const [isImageModalOpen, setIsImageModalOpen] = useState<boolean>(false);

  // Phase 8: video files go through INVESTIGATE (backend video pipeline), not the image-only analyzer.
  const isVideoFile = (f: File | null) => !!f && (f.type.startsWith('video/') || /\.(mp4|mov|webm|avi)$/i.test(f.name));

  const handleImageFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageError('');
    setSelectedImageFile(file);
    setImageAnalysisResult(null);
    const objectUrl = URL.createObjectURL(file);
    setImagePreviewUrl(objectUrl);
    if (!claim.trim()) {
      setClaim(`Forensic ${isVideoFile(file) ? 'video' : 'image'} verification for ${file.name}`);
    }
  };

  const handleRunImageAnalysis = async () => {
    if (!selectedImageFile) return;
    setIsAnalyzingImage(true);
    setImageError('');
    try {
      const result = await analyzeImage(selectedImageFile);
      setImageAnalysisResult(result);
      setIsImageModalOpen(true);
    } catch (err: any) {
      setImageError(err.message || 'Image analysis failed.');
    } finally {
      setIsAnalyzingImage(false);
    }
  };

  const handleClearImage = () => {
    setSelectedImageFile(null);
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
      setImagePreviewUrl(null);
    }
    setImageAnalysisResult(null);
    setImageError('');
  };

  const handleStartInvestigate = () => {
    const finalClaim = claim.trim();
    if (!finalClaim && !selectedImageFile) {
      setError('Enter a claim, URL, or upload an image to investigate, or click TRY DEMO CASE.');
      return;
    }
    setError('');
    const effectiveClaim = finalClaim || (selectedImageFile ? `Forensic analysis of ${selectedImageFile.name}` : '');
    // The demo runs ONLY when the user explicitly clicked TRY DEMO CASE.
    onInvestigate(
      effectiveClaim,
      isDemoPopulated ? mediaName : selectedImageFile?.name,
      url.trim(),
      isDemoPopulated,
      isDemoPopulated ? null : selectedImageFile
    );
  };

  return (
    <div className="relative overflow-hidden border-b border-slate-800/80 bg-[#070B12] forensic-grid py-14 lg:py-20">
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 forensic-radial opacity-60" />

      <div className="relative mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center">
        {/* Core Differentiation Callout Banner */}
        <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/40 px-4 py-1.5 text-xs text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.15)] mb-6">
          <span className="font-semibold text-cyan-200">The Epistemic Shift:</span>
          <span className="text-slate-300">Most systems ask “Is this fake?”</span>
          <span className="text-cyan-400 font-semibold">TrustLens asks “Can I trust the evidence?”</span>
        </div>

        {/* Title & Subtitle */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white font-display">
          TRUST<span className="text-cyan-400">LENS</span>
        </h1>
        <p className="mt-3 text-lg sm:text-xl font-medium text-cyan-300/90 font-display">
          AI-Powered Digital Evidence Investigator
        </p>
        <p className="mx-auto mt-3 max-w-2xl text-sm sm:text-base text-slate-400 leading-relaxed">
          Analyze claims, media, URLs and sources. Detect contradictions. Find counter-evidence.
        </p>

        {/* Input Interface Box */}
        <div className="mt-10 mx-auto max-w-3xl rounded-xl border border-slate-800 bg-slate-900/90 shadow-2xl backdrop-blur-xl p-2 sm:p-4 text-left">
          {/* Input Tabs: CLAIM | URL | IMAGE | VIDEO */}
          <div className="flex items-center gap-1.5 border-b border-slate-800 pb-3 mb-4 overflow-x-auto">
            <button
              onClick={() => setActiveTab('CLAIM')}
              className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer whitespace-nowrap ${
                activeTab === 'CLAIM'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>CLAIM</span>
            </button>
            <button
              onClick={() => setActiveTab('URL')}
              className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer whitespace-nowrap ${
                activeTab === 'URL'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Link2 className="h-3.5 w-3.5" />
              <span>URL</span>
            </button>
            <button
              onClick={() => setActiveTab('IMAGE')}
              className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer whitespace-nowrap ${
                activeTab === 'IMAGE'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <ImageIcon className="h-3.5 w-3.5" />
              <span>IMAGE</span>
            </button>
            <button
              onClick={() => setActiveTab('VIDEO')}
              className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer whitespace-nowrap ${
                activeTab === 'VIDEO'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Film className="h-3.5 w-3.5" />
              <span>VIDEO</span>
            </button>
          </div>

          {/* Tab Specific Content / Main Input Area */}
          <div className="space-y-3">
            <div>
              <label htmlFor="claim-input" className="block text-xs font-mono text-cyan-300 font-bold mb-1.5 uppercase tracking-wider">
                CLAIM
              </label>
              <div className="relative">
                <textarea
                  id="claim-input"
                  value={claim}
                  onChange={(e) => { setClaim(e.target.value); if (error) setError(''); }}
                  placeholder="Enter a claim to investigate… (e.g. “This is the official website of Example University.”)"
                  rows={2}
                  className="w-full resize-none rounded-lg border border-slate-700 bg-slate-950/80 px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 font-sans"
                />
              </div>
              {error && <p className="mt-1.5 text-xs text-red-400 font-mono">{error}</p>}
            </div>

            {/* Submitted URL Field */}
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-3">
              <label className="block text-xs font-mono text-rose-300 font-bold mb-1 uppercase tracking-wider">
                SUBMITTED URL
              </label>
              <div className="flex items-center gap-2">
                <Link2 className="h-4 w-4 text-cyan-400 shrink-0" />
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/page"
                  className="w-full bg-transparent text-xs text-cyan-200 focus:outline-none font-mono"
                />
              </div>
            </div>

            {/* Video Tab Notice */}
            {activeTab === 'VIDEO' && !isDemoPopulated && (
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2.5 text-[11px] font-mono text-slate-400">
                Video upload (MP4 · MOV · WebM · AVI) is supported: TrustLens checks file health and analyzes up to 3 representative frames (beginning, middle, end), including on-screen text compared with your claim. It does not detect deepfakes or AI-generated video, and a decodable video is not proof of authenticity. Choose your video in the IMAGE tab's upload area (it accepts video files), then click INVESTIGATE.
              </div>
            )}

            {/* Image Tab: Phase 4 Real Forensic Upload Pipeline */}
            {activeTab === 'IMAGE' && !isDemoPopulated && (
              <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-mono text-cyan-300 font-bold uppercase tracking-wider">
                    IMAGE FORENSIC UPLOAD (PHASE 4 REAL ENGINE)
                  </label>
                  <span className="text-[10px] font-mono text-slate-400">
                    Images: JPEG · PNG · WEBP (10 MB) · Video: MP4 · MOV · WebM · AVI (30 MB)
                  </span>
                </div>

                <input
                  id="image-file-input"
                  type="file"
                  accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm,video/x-msvideo,.jpg,.jpeg,.png,.webp,.mp4,.mov,.webm,.avi"
                  onChange={handleImageFileChange}
                  className="hidden"
                />

                {!selectedImageFile ? (
                  <label
                    htmlFor="image-file-input"
                    className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-slate-700 hover:border-cyan-500/60 rounded-xl bg-slate-900/40 hover:bg-slate-900/70 transition-all cursor-pointer text-center group"
                  >
                    <Upload className="h-8 w-8 text-slate-400 group-hover:text-cyan-400 transition-colors mb-2" />
                    <span className="text-xs font-semibold text-slate-200 font-mono">
                      Click to select image or drag & drop file
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono mt-1">
                      Pillow Safe Decode · Evidence Health · EXIF · Privacy-Safe GPS · OCR · Computer Vision Signals
                    </span>
                  </label>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between bg-slate-900/80 p-3 rounded-lg border border-slate-700">
                      <div className="flex items-center gap-3">
                        {imagePreviewUrl && !isVideoFile(selectedImageFile) ? (
                          <img
                            src={imagePreviewUrl}
                            alt="Upload preview"
                            className="h-12 w-12 rounded object-cover border border-slate-600 shrink-0"
                          />
                        ) : (
                          <FileImage className="h-8 w-8 text-cyan-400 shrink-0" />
                        )}
                        <div>
                          <div className="text-xs font-bold text-white font-mono truncate max-w-xs sm:max-w-md">
                            {selectedImageFile.name}
                          </div>
                          <div className="text-[10px] font-mono text-slate-400">
                            {(selectedImageFile.size / 1024).toFixed(1)} KB · {selectedImageFile.type || 'image'}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {isVideoFile(selectedImageFile) && (
                          <span className="text-[10px] font-mono text-slate-400">Video is analyzed when you start the investigation</span>
                        )}

                        {!isVideoFile(selectedImageFile) && !imageAnalysisResult && !isAnalyzingImage && (
                          <button
                            type="button"
                            onClick={handleRunImageAnalysis}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-bold font-mono transition-colors cursor-pointer"
                          >
                            <Activity className="h-3.5 w-3.5" />
                            <span>ANALYZE IMAGE</span>
                          </button>
                        )}

                        {isAnalyzingImage && (
                          <div className="flex items-center gap-2 text-xs font-mono text-cyan-300">
                            <RefreshCw className="h-4 w-4 animate-spin text-cyan-400" />
                            <span>Analyzing...</span>
                          </div>
                        )}

                        {imageAnalysisResult && (
                          <button
                            type="button"
                            onClick={() => setIsImageModalOpen(true)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold font-mono transition-colors cursor-pointer"
                          >
                            <Eye className="h-3.5 w-3.5" />
                            <span>VIEW EVIDENCE</span>
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={handleClearImage}
                          title="Remove image"
                          className="p-1.5 rounded text-slate-400 hover:text-rose-300 hover:bg-slate-800 transition-colors cursor-pointer"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>

                    {imageError && (
                      <div className="p-2.5 rounded bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-mono">
                        {imageError}
                      </div>
                    )}

                    {imageAnalysisResult && (
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-cyan-500/30 text-xs font-mono space-y-2">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <span className="text-cyan-300 font-bold flex items-center gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                            Image Evidence Extracted Successfully
                          </span>
                          <div className="flex items-center gap-2">
                            {imageAnalysisResult.multimodalAi && (
                              <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-cyan-950 border border-cyan-500/40 text-cyan-300">
                                AI: {imageAnalysisResult.multimodalAi.aiGenerationAssessment.replace(/_/g, ' ').toUpperCase()} ({(imageAnalysisResult.multimodalAi.confidence * 100).toFixed(0)}%)
                              </span>
                            )}
                            <span className="text-slate-400">
                              Health: <strong className="text-white">{imageAnalysisResult.evidenceHealth.score}/100 ({imageAnalysisResult.evidenceHealth.status})</strong>
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] text-slate-300">
                          <div>
                            <span className="text-slate-500 block">Resolution</span>
                            {imageAnalysisResult.file.width} × {imageAnalysisResult.file.height} ({imageAnalysisResult.file.megapixels} MP)
                          </div>
                          <div>
                            <span className="text-slate-500 block">EXIF Metadata</span>
                            {imageAnalysisResult.metadata.available ? 'Present' : 'Stripped (Neutral)'}
                          </div>
                          <div>
                            <span className="text-slate-500 block">OCR Extraction</span>
                            {imageAnalysisResult.ocr.status}
                          </div>
                          <div>
                            <span className="text-slate-500 block">Sharpness / dHash</span>
                            {imageAnalysisResult.computerVision.sharpnessAssessment} · {imageAnalysisResult.computerVision.perceptualHashDhash.substring(0, 8)}...
                          </div>
                        </div>
                        <div className="pt-1 flex justify-end">
                          <button
                            type="button"
                            onClick={() => setIsImageModalOpen(true)}
                            className="text-[11px] text-cyan-400 hover:text-cyan-300 font-semibold underline flex items-center gap-1 cursor-pointer"
                          >
                            Inspect Full Evidence Ledger & Limitations →
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}


            {isDemoPopulated && (
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2.5 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Film className="h-4 w-4 text-cyan-400" />
                  <div>
                    <span className="text-xs text-slate-200 font-mono font-medium block">
                      {mediaName}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      Demo Media (SIMULATED) · no real file is analyzed
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-mono">
                  <span className="inline-block h-2 w-2 rounded-full bg-emerald-400" />
                  <span>Payload Ingested</span>
                </div>
              </div>
            )}

            {/* Demo Investigation Notice */}
            {isDemoPopulated && (
              <div className="rounded-lg border border-amber-500/40 bg-amber-950/30 p-3.5 text-xs text-amber-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold tracking-wider text-amber-300 flex items-center gap-1.5">
                    <AlertTriangle className="h-4 w-4" />
                    DEMO INVESTIGATION READY · SIMULATED ANALYSIS
                  </span>
                  <span className="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded font-mono border border-amber-500/30">
                    CLICK [INVESTIGATE] BELOW
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-300 pt-1 border-t border-amber-500/20 font-mono">
                  <div>
                    <span className="text-slate-400">CLAIM: </span>
                    <span className="text-white font-sans font-medium">“This video shows today’s flood in Bengaluru.”</span>
                  </div>
                  <div>
                    <span className="text-slate-400">SUBMITTED URL: </span>
                    <span className="text-cyan-300">youtube.com/shorts/demo-flood-video</span>
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 leading-tight pt-0.5">
                  * Note: Potential tracking behavior detected in URL routing. Actual data collection could not be independently verified.
                </p>
              </div>
            )}
          </div>

          {/* Action Buttons: [ INVESTIGATE ] & [ TRY DEMO CASE ] */}
          <div className="mt-5 flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate-800">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <button
                onClick={onPopulateDemo}
                className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 hover:text-white transition-all cursor-pointer whitespace-nowrap"
              >
                <Sparkles className="h-4 w-4 text-cyan-400" />
                <span>TRY DEMO CASE</span>
              </button>
            </div>

            <button
              onClick={handleStartInvestigate}
              className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-2.5 text-xs font-bold uppercase tracking-wider text-black hover:from-cyan-400 hover:to-blue-500 shadow-[0_0_20px_rgba(6,182,212,0.4)] transition-all cursor-pointer whitespace-nowrap"
            >
              <Search className="h-4 w-4" />
              <span>INVESTIGATE</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* 3 Pillar Value Propositions */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto text-left">
          <div className="p-4 rounded-lg border border-slate-800/80 bg-slate-900/40">
            <div className="flex items-center gap-2 text-cyan-400 mb-1.5">
              <Layers className="h-4 w-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider font-mono">1. Beyond Pixel Manipulation</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Real videos can be recycled to manufacture false narratives. We verify real-world calendar and geographical anchors.
            </p>
          </div>

          <div className="p-4 rounded-lg border border-slate-800/80 bg-slate-900/40">
            <div className="flex items-center gap-2 text-cyan-400 mb-1.5">
              <GitFork className="h-4 w-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider font-mono">2. Source Independence</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              3 retweets do not equal 3 independent witnesses. We trace viral syndication lineage back to single origin nodes.
            </p>
          </div>

          <div className="p-4 rounded-lg border border-slate-800/80 bg-slate-900/40">
            <div className="flex items-center gap-2 text-cyan-400 mb-1.5">
              <Fingerprint className="h-4 w-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider font-mono">3. Perceptual Counter-Evidence</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Autonomous archival comparison detects earlier publications, revealing when past catastrophes are repurposed as breaking news.
            </p>
          </div>
        </div>
      </div>

      {/* Phase 4 Real Forensic Inspection Modal */}
      <ImageEvidenceModal
        isOpen={isImageModalOpen}
        onClose={() => setIsImageModalOpen(false)}
        data={imageAnalysisResult}
        imagePreviewUrl={imagePreviewUrl}
      />
    </div>
  );
};

