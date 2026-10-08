// Phase 8: mirrors backend/schemas/video_analysis.py (camelCase). Only real, measured fields.
export type VideoClaimRelationship =
  | 'SUPPORTS' | 'CONTRADICTS' | 'PARTIALLY_SUPPORTS' | 'UNRELATED' | 'INSUFFICIENT_EVIDENCE';
export type CapabilityStatus = 'IMPLEMENTED' | 'PARTIAL' | 'UNAVAILABLE';

export interface VideoMetadata {
  filename: string;
  sizeBytes: number;
  sha256: string;
  container?: string | null;
  codec?: string | null;
  durationSeconds?: number | null;
  width?: number | null;
  height?: number | null;
  frameRate?: number | null;
  frameCount?: number | null;
  frameCountSource?: string | null;
  decodable: boolean;
  probeTool: string;
  notes: string[];
}

export interface VideoFrameEvidence {
  frameRef: string;
  position: 'beginning' | 'middle' | 'end';
  frameIndex: number;
  timestampSeconds?: number | null;
  sourceType: string;
  source: string;
  decoded: boolean;
  error?: string | null;
  qualityScore?: number | null;
  qualityStatus?: string | null;
  ocrAvailable: boolean;
  ocrText: string;
  claimRelationship?: VideoClaimRelationship | null;
  thumbnailDataUrl?: string | null;
  multimodal?: { aiGenerationAssessment?: string; confidence?: number; modelUsed?: string | null } | null;
}

export interface VideoCapability {
  name: string;
  status: CapabilityStatus;
  note: string;
}

export interface VideoAnalysisResult {
  ok: boolean;
  status: 'ANALYZED' | 'PARTIAL' | 'FAILED';
  errorCode?: string | null;
  error?: string | null;
  metadata?: VideoMetadata | null;
  frames: VideoFrameEvidence[];
  claimComparison?: {
    relationship: VideoClaimRelationship;
    explanation: string;
    supportingFrames: string[];
    contradictingFrames: string[];
  } | null;
  capabilities: VideoCapability[];
  limitations: string[];
  analyzedAt: string;
}
