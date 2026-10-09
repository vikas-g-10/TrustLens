/**
 * Controlled demo dataset for the /shorts-demo page.
 * All verdicts here are SCRIPTED demo data, not live analysis output.
 * Video paths are local placeholders; no real-world provenance is claimed.
 */

export type GroundTruth = 'LEGITIMATE' | 'AI_GENERATED' | 'FALSE_EVENT';
export type DemoVerdict =
  | 'LIKELY_AUTHENTIC'
  | 'LIKELY_AI_GENERATED'
  | 'NOT_TRUSTWORTHY'
  | 'INCONCLUSIVE';
export type EvidenceStrength = 'Strong' | 'Moderate' | 'Limited';
export type EvidenceConflict = 'None' | 'Low' | 'High';

export interface ShortDemoEntry {
  id: string;
  title: string;
  /** Local placeholder path. Files are not bundled; the UI falls back to a placeholder. */
  video: string;
  claim: string;
  groundTruth: GroundTruth;
  demoVerdict: DemoVerdict;
  description: string;
  evidenceSummary: string;
  evidenceStrength: EvidenceStrength;
  evidenceConflict: EvidenceConflict;
  limitations: string;
}

const LIMIT_GENERIC =
  'Placeholder demo entry. No real footage was analyzed and results are scripted for UI demonstration only.';

export const SHORTS_DEMO: ShortDemoEntry[] = [
  {
    id: 'legit-1',
    title: 'Street market ambience',
    video: '/demo-videos/legit-1.mp4',
    claim: 'This clip shows an ordinary street market scene.',
    groundTruth: 'LEGITIMATE',
    demoVerdict: 'LIKELY_AUTHENTIC',
    description: 'Placeholder for a legitimate everyday-scene clip.',
    evidenceSummary: 'Scripted: claim and visual content are consistent; no manipulation signals in this demo scenario.',
    evidenceStrength: 'Moderate',
    evidenceConflict: 'None',
    limitations: LIMIT_GENERIC,
  },
  {
    id: 'legit-2',
    title: 'Local cricket match',
    video: '/demo-videos/legit-2.mp4',
    claim: 'This clip shows a local amateur cricket match.',
    groundTruth: 'LEGITIMATE',
    demoVerdict: 'LIKELY_AUTHENTIC',
    description: 'Placeholder for a legitimate sports clip.',
    evidenceSummary: 'Scripted: sources and visuals agree in this demo scenario.',
    evidenceStrength: 'Moderate',
    evidenceConflict: 'None',
    limitations: LIMIT_GENERIC,
  },
  {
    id: 'legit-3',
    title: 'Rain on a city road',
    video: '/demo-videos/legit-3.mp4',
    claim: 'This clip shows heavy rain on a city road.',
    groundTruth: 'LEGITIMATE',
    demoVerdict: 'LIKELY_AUTHENTIC',
    description: 'Placeholder for a legitimate weather clip.',
    evidenceSummary: 'Scripted: reported conditions are consistent with the clip in this demo scenario.',
    evidenceStrength: 'Strong',
    evidenceConflict: 'Low',
    limitations: LIMIT_GENERIC,
  },
  {
    id: 'legit-4',
    title: 'Campus cultural event',
    video: '/demo-videos/legit-4.mp4',
    claim: 'This clip shows a college cultural event.',
    groundTruth: 'LEGITIMATE',
    demoVerdict: 'LIKELY_AUTHENTIC',
    description: 'Placeholder for a legitimate event clip.',
    evidenceSummary: 'Scripted: event description matches visible content in this demo scenario.',
    evidenceStrength: 'Moderate',
    evidenceConflict: 'None',
    limitations: LIMIT_GENERIC,
  },
  {
    id: 'legit-5',
    title: 'Traffic jam timelapse',
    video: '/demo-videos/legit-5.mp4',
    claim: 'This clip shows a rush-hour traffic jam.',
    groundTruth: 'LEGITIMATE',
    demoVerdict: 'LIKELY_AUTHENTIC',
    description: 'Placeholder for a legitimate traffic clip.',
    evidenceSummary: 'Scripted: no contradicting evidence in this demo scenario.',
    evidenceStrength: 'Limited',
    evidenceConflict: 'Low',
    limitations: LIMIT_GENERIC + ' Limited evidence means this stays a likelihood, not a certainty.',
  },
  {
    id: 'ai-1',
    title: 'Synthetic city flood',
    video: '/demo-videos/ai-1.mp4',
    claim: 'This video shows a flood in a major city today.',
    groundTruth: 'AI_GENERATED',
    demoVerdict: 'LIKELY_AI_GENERATED',
    description: 'Placeholder for an AI-generated disaster clip.',
    evidenceSummary: 'Scripted: synthetic-generation indicators outweigh supporting evidence in this demo scenario.',
    evidenceStrength: 'Moderate',
    evidenceConflict: 'Low',
    limitations: LIMIT_GENERIC,
  },
  {
    id: 'ai-2',
    title: 'Synthetic celebrity speech',
    video: '/demo-videos/ai-2.mp4',
    claim: 'This video shows a public figure making a statement.',
    groundTruth: 'AI_GENERATED',
    demoVerdict: 'LIKELY_AI_GENERATED',
    description: 'Placeholder for an AI-generated speech clip. No real person is depicted.',
    evidenceSummary: 'Scripted: generation indicators and missing corroboration in this demo scenario.',
    evidenceStrength: 'Moderate',
    evidenceConflict: 'Low',
    limitations: LIMIT_GENERIC,
  },
  {
    id: 'ai-3',
    title: 'Synthetic wildlife encounter',
    video: '/demo-videos/ai-3.mp4',
    claim: 'This video shows a rare animal in a residential street.',
    groundTruth: 'AI_GENERATED',
    demoVerdict: 'LIKELY_AI_GENERATED',
    description: 'Placeholder for an AI-generated animal clip.',
    evidenceSummary: 'Scripted: synthetic indicators present; no corroborating reports in this demo scenario.',
    evidenceStrength: 'Limited',
    evidenceConflict: 'Low',
    limitations: LIMIT_GENERIC,
  },
  {
    id: 'false-1',
    title: 'Old clip, new claim',
    video: '/demo-videos/false-1.mp4',
    claim: 'This video shows an event that happened this week.',
    groundTruth: 'FALSE_EVENT',
    demoVerdict: 'NOT_TRUSTWORTHY',
    description: 'Placeholder for a real-looking clip paired with a false or misleading claim.',
    evidenceSummary: 'Scripted: claim conflicts with available context in this demo scenario.',
    evidenceStrength: 'Moderate',
    evidenceConflict: 'High',
    limitations: LIMIT_GENERIC,
  },
  {
    id: 'false-2',
    title: 'Misattributed location',
    video: '/demo-videos/false-2.mp4',
    claim: 'This video shows an incident in a specific city.',
    groundTruth: 'FALSE_EVENT',
    demoVerdict: 'NOT_TRUSTWORTHY',
    description: 'Placeholder for a clip with a misattributed location claim.',
    evidenceSummary: 'Scripted: location claim is not supported by the evidence in this demo scenario.',
    evidenceStrength: 'Limited',
    evidenceConflict: 'High',
    limitations: LIMIT_GENERIC,
  },
];
