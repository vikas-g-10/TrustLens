import type { AnalysisCardData } from '../types/investigation';
import type { InvestigationResponse } from '../types/analysis';
import type { VideoAnalysisResult } from '../types/videoAnalysis';

type Item = AnalysisCardData['summaryItems'][number];
const UNAVAILABLE = 'Unavailable';
const trunc = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

/**
 * Phase 8 video card. Presents only measured facts and honest capability status.
 * A decoded/analyzed video is never presented as "authentic"; the verdict comes from Phase 6 fusion.
 */
export function videoForensicsCard(r: InvestigationResponse): AnalysisCardData {
  const m = r.mediaAnalysis;
  const v: VideoAnalysisResult | undefined = m?.videoAnalysis;

  if (!v || !v.ok || !v.metadata) {
    return {
      id: 'media_forensics',
      title: 'VIDEO FORENSICS',
      badge: { text: 'VIDEO NOT ANALYZED', variant: 'amber' },
      summaryItems: [
        { iconType: 'warning', text: v?.error || 'The uploaded video could not be analyzed.', variant: 'amber' },
        { iconType: 'info', text: 'No video evidence was produced; this is not a finding about the video.', variant: 'slate' },
      ],
      details: {
        overview: 'The uploaded video failed validation or decoding, so it contributes no evidence to the investigation.',
        metrics: [
          { label: 'Status', value: v?.status || 'FAILED' },
          { label: 'Error Code', value: v?.errorCode || UNAVAILABLE },
        ],
        forensicNotes: v?.limitations ?? ['The video could not be analyzed.'],
        technicalDisclaimer: 'An unreadable or unsupported file is not evidence of manipulation.',
      },
    };
  }

  const md = v.metadata;
  const decoded = v.frames.filter((f) => f.decoded);
  const items: Item[] = [
    {
      iconType: 'check',
      text: `${md.container || 'Container unknown'} · ${md.width ?? '?'}x${md.height ?? '?'} · ${md.frameRate?.toFixed(2) ?? '?'} fps · ${md.durationSeconds ?? '?'}s`,
      variant: 'green',
    },
    {
      iconType: decoded.length === v.frames.length ? 'check' : 'warning',
      text: `${decoded.length}/${v.frames.length} representative frames decoded and analyzed (not the full video)`,
      variant: decoded.length === v.frames.length ? 'green' : 'amber',
    },
  ];
  for (const f of decoded) {
    const ocr = f.ocrText?.trim() ? `OCR "${trunc(f.ocrText.trim(), 40)}"` : f.ocrAvailable ? 'no text' : 'OCR unavailable';
    items.push({
      iconType: 'info',
      text: `Frame ${f.frameIndex} (t=${f.timestampSeconds ?? '?'}s, ${f.position}): health ${f.qualityScore ?? '?'}/100 · ${ocr}`,
      variant: 'slate',
    });
  }
  if (v.claimComparison) {
    const rel = v.claimComparison.relationship;
    items.push({
      iconType: rel === 'CONTRADICTS' ? 'alert' : rel === 'SUPPORTS' || rel === 'PARTIALLY_SUPPORTS' ? 'check' : 'info',
      text: `Video text vs claim: ${rel.replace(/_/g, ' ')}`,
      variant: rel === 'CONTRADICTS' ? 'red' : rel === 'SUPPORTS' ? 'green' : rel === 'PARTIALLY_SUPPORTS' ? 'amber' : 'slate',
    });
  }
  const unavailable = v.capabilities.filter((c) => c.status === 'UNAVAILABLE').length;
  items.push({
    iconType: 'info',
    text: `${unavailable} capabilities UNAVAILABLE (incl. PRNU, deepfake, optical flow, AI-video probability): zero evidence, not suspicion`,
    variant: 'slate',
  });

  const metrics = [
    { label: 'File Name', value: md.filename },
    { label: 'File Size', value: `${(md.sizeBytes / 1024).toFixed(1)} KB` },
    { label: 'SHA-256', value: `${md.sha256.slice(0, 12)}…` },
    { label: 'Container', value: md.container || UNAVAILABLE },
    { label: 'Codec', value: md.codec || UNAVAILABLE },
    { label: 'Resolution', value: md.width && md.height ? `${md.width}x${md.height}` : UNAVAILABLE },
    { label: 'Frame Rate', value: md.frameRate ? `${md.frameRate.toFixed(2)} fps` : UNAVAILABLE },
    { label: 'Duration', value: md.durationSeconds != null ? `${md.durationSeconds}s` : UNAVAILABLE },
    { label: 'Frame Count', value: md.frameCount ? `${md.frameCount} (${md.frameCountSource || 'unknown'})` : UNAVAILABLE },
    { label: 'Processing Status', value: v.status },
    ...v.capabilities.map((c) => ({ label: c.name, value: c.status })),
  ];

  return {
    id: 'media_forensics',
    title: 'VIDEO FORENSICS',
    badge: { text: `FRAMES: ${decoded.length}/${v.frames.length} · ${v.status}`, variant: v.status === 'ANALYZED' ? 'cyan' : 'amber' },
    summaryItems: items,
    details: {
      overview: `Phase 8 video investigation of ${md.filename}: container/stream facts were measured and ${v.frames.length} representative frame(s) were run through the existing image pipeline (health, CV, OCR).`,
      metrics,
      forensicNotes: [...(v.claimComparison ? [v.claimComparison.explanation] : []), ...v.limitations],
      technicalDisclaimer: 'Successful decoding and frame analysis does not mean the video is authentic. The final verdict comes only from the Phase 6 evidence-fusion engine.',
    },
  };
}
