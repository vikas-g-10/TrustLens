// Types shared between the server (URL analysis + Groq) and the client UI.

export type UrlErrorCode =
  | 'INVALID_URL'
  | 'BLOCKED_HOST'
  | 'DNS_FAILURE'
  | 'TIMEOUT'
  | 'TOO_MANY_REDIRECTS'
  | 'HTTP_ERROR'
  | 'UNSUPPORTED_CONTENT'
  | 'NETWORK_ERROR';

export interface UrlAnalysisError {
  code: UrlErrorCode;
  message: string;
  statusCode?: number;
}

export interface UrlAnalysis {
  originalUrl: string;
  finalUrl: string;
  originalDomain: string;
  finalDomain: string;
  https: boolean;
  redirectCount: number;
  redirectChain: string[];
  domainMismatch: boolean;
  statusCode: number;
  contentType: string;
  title: string | null;
  metaDescription: string | null;
  siteName: string | null;
  headings: string[];
  canonicalUrl: string | null;
  visibleText: string;
  textTruncated: boolean;
  trackingParams: string[];
  suspiciousStructure: string[];
  fetchedAt: string;
}

export type UrlAnalysisOutcome =
  | { ok: true; data: UrlAnalysis }
  | { ok: false; error: UrlAnalysisError };

export type AiVerdict =
  | 'LIKELY_GENUINE'
  | 'HIGH_RISK'
  | 'INCONCLUSIVE'
  | 'LIKELY_AUTHENTIC'
  | 'LIKELY_AI_GENERATED'
  | 'LIKELY_MANIPULATED';

export interface AiReasoning {
  claim: string;
  verdict: AiVerdict;
  confidence: number;
  summary: string;
  supportingEvidence: string[];
  contradictingEvidence: string[];
  uncertainties: string[];
  reasoning: string[];
  reason?: string;
  supportingEvidenceIds?: string[];
  contradictingEvidenceIds?: string[];
}

export interface TrustTriangle {
  manipulationLikelihood: number;
  evidenceStrength: number;
  evidenceConflict: number;
}

export interface EvidenceSummary {
  supportingStrength: number;
  contradictingStrength: number;
  independentEvidenceCount: number;
  evidenceCoverage: number;
  totalEvidenceCount: number;
  supportingCount: number;
  contradictingCount: number;
  neutralCount: number;
}

export interface ConflictDetail {
  conflictId: string;
  description: string;
  conflictingEvidenceIds: string[];
  severity: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
  dimension: string;
}

export interface ConflictReport {
  detected: boolean;
  count: number;
  severity: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
  conflictScore: number;
  conflictingEvidenceIds: string[];
  description: string;
  details: ConflictDetail[];
}

export interface NormalizedEvidenceItem {
  evidenceId: string;
  evidenceType: string;
  description: string;
  direction: 'SUPPORTS' | 'CONTRADICTS' | 'NEUTRAL';
  targetHypothesis: string;
  reliability: number;
  quality: number;
  independenceGroup: string;
  source: string;
  provenance: Record<string, any>;
  confidence?: number | null;
  weight: number;
  limitations: string[];
}

import type { MultimodalAiResult } from './imageAnalysis';

export interface InvestigationResponse {
  claim: string;
  inputUrl: string | null;
  urlAnalysis: UrlAnalysisOutcome | null;
  /** The reasoning actually shown to the user (Groq output, or a transparent INCONCLUSIVE fallback). */
  final: AiReasoning;
  /** True only when `final` came from a validated Groq response. */
  aiAvailable: boolean;
  aiNote: string | null;
  model: string | null;
  generatedAt: string;
  searchEvidence?: any;
  mediaAnalysis?: any;
  multimodalAnalysis?: MultimodalAiResult | null;
  trustTriangle?: TrustTriangle;
  evidenceSummary?: EvidenceSummary;
  conflict?: ConflictReport;
  normalizedEvidence?: NormalizedEvidenceItem[];
}


