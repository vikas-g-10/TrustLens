export interface FileMetadata {
  filename: string;
  format: string;
  sizeBytes: number;
  sha256: string;
  width: number;
  height: number;
  aspectRatio: string;
  megapixels: number;
  imageMode: string;
  mimeType: string;
  isValid?: boolean;
  corruptionDetected?: boolean;
}

export interface CompressionIndicators {
  hasQuantizationTables: boolean;
  estimatedJpegQuality?: number | null;
  compressionStatus: string;
  notes: string[];
}

export interface ElaResult {
  status: string;
  available: boolean;
  qualityFactorTested?: number | null;
  meanError?: number | null;
  maxError?: number | null;
  errorVariance?: number | null;
  highErrorRatio?: number | null;
  notes: string[];
}

export interface ForensicTestAvailability {
  fileIntegrity: string;
  resolutionCheck: string;
  exifMetadata: string;
  compressionAnalysis: string;
  elaAnalysis: string;
  perceptualHashing: string;
  referenceComparison: string;
  ocrExtraction: string;
  aiDeepfakeDetector: string;
  prnuSensorAnalysis: string;
  opticalFlowAnalysis: string;
}

export interface EvidenceHealth {
  score: number;
  status: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'UNUSABLE';
  decodeSuccessful: boolean;
  metadataAvailable: boolean;
  metadataStatus?: 'present' | 'partial' | 'unavailable';
  resolutionAdequate: boolean;
  compressionIndicators: CompressionIndicators;
  testAvailability?: ForensicTestAvailability;
  signals: string[];
  notes: string[];
}

export interface ExifMetadata {
  available: boolean;
  metadataStatus?: 'present' | 'partial' | 'unavailable';
  completenessScore?: number;
  cameraMake?: string | null;
  cameraModel?: string | null;
  software?: string | null;
  editingSoftware?: string | null;
  timestamp?: string | null;
  orientation?: number | string | null;
  gpsPresent: boolean;
  colorSpace?: string | null;
  rawTagsCount: number;
  notes: string[];
}

export interface OcrResult {
  status: 'SUCCESS' | 'NO_TEXT_DETECTED' | 'NO_TEXT_FOUND' | 'UNAVAILABLE' | 'ERROR';
  available: boolean;
  ocrQuality?: 'high' | 'moderate' | 'low' | 'not_applicable' | 'unavailable';
  text: string;
  confidence?: number | null;
  regionsCount: number;
  notes: string[];
}

export interface ComputerVisionSignals {
  sharpnessScore: number;
  sharpnessAssessment: string;
  brightnessMean: number;
  brightnessAssessment: string;
  contrastRms: number;
  edgeDensity: number;
  perceptualHashDhash: string;
  perceptualHashPhash: string;
  comparisonStatus?: string;
  noiseVariance: number;
}

export interface ImageEvidenceItem {
  evidenceType?: string;
  type?: string;
  category?: string;
  observation: string;
  reliabilityTier?: string;
  reliability?: string;
  technicalDetails?: Record<string, unknown>;
}

export type AiGenerationAssessment =
  | 'likely_ai_generated'
  | 'likely_authentic'
  | 'possibly_manipulated'
  | 'inconclusive';

export interface MultimodalAiResult {
  aiGenerationAssessment: AiGenerationAssessment;
  confidence: number;
  visualFindings: string[];
  supportingSignals: string[];
  contradictingSignals: string[];
  limitations: string[];
  explanation: string;
  modelUsed?: string | null;
  providerUsed?: string | null;
  analyzedAt?: string | null;
}

export interface ImageAnalysisResponse {
  ok?: boolean;
  file: FileMetadata;
  evidenceHealth: EvidenceHealth;
  metadata: ExifMetadata;
  ela: ElaResult;
  ocr: OcrResult;
  computerVision: ComputerVisionSignals;
  evidence: ImageEvidenceItem[];
  limitations: string[];
  multimodalAi?: MultimodalAiResult | null;
  analyzedAt?: string;
  generatedAt?: string;
}

