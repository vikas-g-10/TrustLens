import type {
  InvestigationResponse,
  TrustTriangle,
  EvidenceSummary,
  ConflictReport,
  NormalizedEvidenceItem,
} from './analysis';

export type InputTab = 'CLAIM' | 'URL' | 'IMAGE' | 'VIDEO';

export type PipelineStageId = 
  | 'claim_extraction'
  | 'media_forensics'
  | 'url_security'
  | 'evidence_retrieval'
  | 'contradiction_check'
  | 'source_independence'
  | 'counter_evidence'
  | 'evidence_fusion'
  | 'final_reasoning';

export type StageStatus = 'pending' | 'analyzing' | 'complete';

export interface PipelineStage {
  id: PipelineStageId;
  label: string;
  subtext: string;
  status: StageStatus;
  telemetryLog?: string;
}

export type VerdictStatus =
  | 'INCONCLUSIVE'
  | 'LIKELY_GENUINE'
  | 'HIGH_RISK'
  | 'LIKELY_AUTHENTIC'
  | 'LIKELY_AI_GENERATED'
  | 'LIKELY_MANIPULATED';

export interface AnalysisCardData {
  id: string;
  title: string;
  badge: {
    text: string;
    variant: 'amber' | 'red' | 'green' | 'orange' | 'cyan' | 'slate';
  };
  summaryItems: {
    iconType: 'check' | 'warning' | 'alert' | 'info';
    text: string;
    variant: 'green' | 'amber' | 'red' | 'slate';
  }[];
  details: {
    overview: string;
    metrics?: { label: string; value: string }[];
    forensicNotes: string[];
    technicalDisclaimer?: string;
  };
}

export interface EvidenceBattleItem {
  id: string;
  source: string;
  claimPoint: string;
  type: 'supporting' | 'challenging';
  variant: 'green' | 'red' | 'orange';
  detail: string;
  timestamp?: string;
  reliability: string;
}

export interface GraphNode {
  id: string;
  label: string;
  category: 'claim' | 'media' | 'url' | 'source' | 'conflict' | 'counter' | 'verdict';
  x: number;
  y: number;
  description: string;
  significance?: string;
  sublabel?: string;
  status: 'supporting' | 'challenging' | 'neutral' | 'inconclusive';
}

export interface GraphEdge {
  from: string;
  to: string;
  label?: string;
  type: 'supporting' | 'contradicting' | 'final' | 'neutral';
}

export interface TimelineStep {
  id: string;
  title: string;
  dateText: string;
  description: string;
  type: 'past_archive' | 'viral_post' | 'investigation' | 'conflict' | 'counter' | 'verdict';
  status: 'warning' | 'neutral' | 'alert' | 'success';
}

export interface InvestigationData {
  caseId: string;
  isDemo: boolean;
  createdAt: string;
  /** Raw live result (URL analysis + AI reasoning). Absent for the demo case. */
  live?: InvestigationResponse;
  claim: string;
  mediaName: string;
  url: string;
  verdict: {
    status: VerdictStatus;
    confidence: number;
    headline: string;
    mainExplanation: string;
    whyNotGenuine: string;
    whyNotHighRisk: string;
    finalReasoning: string;
    /** Short bullet reasons shown under WHY? */
    whyBullets: string[];
  };
  cards: AnalysisCardData[];
  battle: {
    supportingCount: number;
    challengingCount: number;
    summary: string;
    supporting: EvidenceBattleItem[];
    challenging: EvidenceBattleItem[];
  };
  graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  timeline: TimelineStep[];
  reasoningSteps: {
    number: number;
    title: string;
    finding: string;
    status: 'neutral' | 'alert' | 'warning' | 'verified';
  }[];
  trustTriangle?: TrustTriangle;
  evidenceSummary?: EvidenceSummary;
  conflict?: ConflictReport;
  normalizedEvidence?: NormalizedEvidenceItem[];
}
