import { InvestigationData, PipelineStage } from '../types/investigation';

export const INITIAL_PIPELINE_STAGES: PipelineStage[] = [
  {
    id: 'claim_extraction',
    label: 'CLAIM EXTRACTION',
    subtext: 'Isolating factual assertions, date markers, and location coordinates',
    status: 'pending',
    telemetryLog: 'Extracted: [Event: Urban Flood] [Location: Bengaluru, IN] [Temporal Anchor: Today]'
  },
  {
    id: 'media_forensics',
    label: 'MEDIA FORENSICS',
    subtext: 'Scanning pixel continuity, compression artifacts, and generative deepfake markers',
    status: 'pending',
    telemetryLog: 'Sensor PRNU: Native CMOS camera optics. EXIF creation date: STRIPPED. No generative AI seams.'
  },
  {
    id: 'url_security',
    label: 'URL SECURITY',
    subtext: 'Auditing redirect hops, parameter tracking payload, and destination mismatch',
    status: 'pending',
    telemetryLog: 'HTTPS verified. Redirect hops detected. Tracking tokens identified. Destination mismatch flagged.'
  },
  {
    id: 'evidence_retrieval',
    label: 'EVIDENCE RETRIEVAL',
    subtext: 'Querying news wires, regional rainfall Doppler radars, and social feeds',
    status: 'pending',
    telemetryLog: 'Ingested 5 candidate sources: Doppler confirms precipitation; traffic alerts note waterlogging.'
  },
  {
    id: 'contradiction_check',
    label: 'CONTRADICTION CHECK',
    subtext: 'Cross-referencing reverse perceptual image hashes against historical video archives',
    status: 'pending',
    telemetryLog: 'Visual dHash match: 94.2% structural alignment against historical archival repository.'
  },
  {
    id: 'source_independence',
    label: 'SOURCE INDEPENDENCE',
    subtext: 'Testing whether multiple accounts constitute independent witnesses or circular syndication',
    status: 'pending',
    telemetryLog: 'Lineage trace: 3 sources share identical phrasing tracing to a single unverified channel.'
  },
  {
    id: 'counter_evidence',
    label: 'COUNTER-EVIDENCE',
    subtext: 'Evaluating archival timestamps that conflict with the claimed current date',
    status: 'pending',
    telemetryLog: 'Counter-evidence established: Identical sequence published previously in August 2022.'
  },
  {
    id: 'evidence_fusion',
    label: 'EVIDENCE FUSION',
    subtext: 'Synthesizing dialectical evidence vectors into an epistemic matrix',
    status: 'pending',
    telemetryLog: 'Evidence collision: Supporting 3 vs Challenging 3. Material conflict prevents binary confirmation.'
  },
  {
    id: 'final_reasoning',
    label: 'FINAL REASONING',
    subtext: 'Calibrating explainable decision logic and confidence boundary',
    status: 'pending',
    telemetryLog: 'Verdict derived: INCONCLUSIVE (78% confidence). Authentic footage reused out of temporal context.'
  }
];

export const DEMO_CASE: InvestigationData = {
  caseId: 'TL-2026-BLR-0941',
  isDemo: true,
  createdAt: '2026-01-01T08:32:00.000Z',
  claim: "This video shows today’s flood in Bengaluru.",
  mediaName: "FLOOD_VIDEO_DEMO.mp4",
  url: "youtube.com/shorts/demo-flood-video",
  verdict: {
    status: "INCONCLUSIVE",
    confidence: 78,
    headline: "Temporal Provenance Conflict: Authentic Media Reused Out of Context",
    mainExplanation: "The submitted media may depict a genuine flood event, but the available evidence cannot establish that this footage represents today’s Bengaluru flood.",
    whyNotGenuine: "The claim depends on establishing the video's date and context. Available evidence does not independently establish those attributes, and counter-evidence creates a material conflict.",
    whyNotHighRisk: "The media itself has not been conclusively shown to be fabricated or manipulated. The primary uncertainty concerns provenance and context rather than proven fabrication.",
    finalReasoning: "Evidence is conflicting and provenance remains unresolved.",
    whyBullets: [
      "No reliable original timestamp",
      "Location cannot be independently verified",
      "Similar footage was published previously",
      "Supporting sources are not fully independent",
      "URL shows suspicious redirect/tracking indicators"
    ]
  },
  cards: [
    {
      id: "media_forensics",
      title: "MEDIA FORENSICS",
      badge: {
        text: "⚠ CONTEXT UNCERTAIN",
        variant: "amber"
      },
      summaryItems: [
        {
          iconType: "check",
          text: "No obvious visual manipulation detected",
          variant: "green"
        },
        {
          iconType: "warning",
          text: "Original capture date unavailable",
          variant: "amber"
        },
        {
          iconType: "warning",
          text: "Location cannot be independently verified",
          variant: "amber"
        }
      ],
      details: {
        overview: "Frame-by-frame analysis reveals no deepfake generation or generative splice boundaries. However, crucial metadata containers were purged upon re-encoding.",
        metrics: [
          { label: "Generative AI Likelihood", value: "< 4.1%" },
          { label: "Compression Generation", value: "3rd generation re-encode" },
          { label: "EXIF Timestamp", value: "Null / Stripped" },
          { label: "Color Grading Consistency", value: "98.7% (Natural daylight)" }
        ],
        forensicNotes: [
          "No boundary discontinuity or warping detected around moving vehicles and reflections.",
          "Audio track lacks ambient stereo phase cues, indicating non-original or re-dubbed soundtrack.",
          "Visual topography matches Bellandur / Outer Ring Road sector, but landmarks lack temporal markers."
        ],
        technicalDisclaimer: "Optical forensics verify visual continuity but cannot establish the real-world calendar date of optical exposure."
      }
    },
    {
      id: "url_security",
      title: "URL SECURITY",
      badge: {
        text: "🔴 SUSPICIOUS",
        variant: "red"
      },
      summaryItems: [
        {
          iconType: "check",
          text: "HTTPS",
          variant: "green"
        },
        {
          iconType: "warning",
          text: "Redirect behavior",
          variant: "amber"
        },
        {
          iconType: "warning",
          text: "Tracking parameters",
          variant: "amber"
        },
        {
          iconType: "alert",
          text: "Destination mismatch",
          variant: "red"
        },
        {
          iconType: "warning",
          text: "Potential tracking/fingerprinting behavior",
          variant: "amber"
        }
      ],
      details: {
        overview: "The submitted URL uses intermediary redirect behaviors and tracking query parameters that route users through an analytics tracker wrapper.",
        metrics: [
          { label: "Protocol Security", value: "TLS 1.3 / HTTPS" },
          { label: "Redirect Hops", value: "2 intermediary hops" },
          { label: "Tracking Parameters", value: "7 telemetry tokens" },
          { label: "Destination Match", value: "MISMATCH FLAGGED" }
        ],
        forensicNotes: [
          "Potential tracking behavior detected.",
          "Actual data collection could not be independently verified.",
          "Submitted URL resolves to a different canonical resource than the initial presentation suggests."
        ],
        technicalDisclaimer: "DEMO ANALYSIS: Potential tracking behavior detected. Actual data collection could not be independently verified."
      }
    },
    {
      id: "independent_evidence",
      title: "INDEPENDENT EVIDENCE",
      badge: {
        text: "⚠ MIXED",
        variant: "amber"
      },
      summaryItems: [
        {
          iconType: "check",
          text: "3 supporting sources",
          variant: "green"
        },
        {
          iconType: "alert",
          text: "2 contradicting sources",
          variant: "red"
        }
      ],
      details: {
        overview: "Cross-platform interrogation retrieved 5 primary corroboration candidates. While regional rain conditions are authentic, video-level corroboration is polarized.",
        metrics: [
          { label: "Total Ingested Sources", value: "5 validated feeds" },
          { label: "Supporting Weight", value: "50%" },
          { label: "Contradicting Weight", value: "50%" },
          { label: "Source Independence Index", value: "Low (Cluster effect)" }
        ],
        forensicNotes: [
          "Sources report that Bengaluru experienced downpours in the region.",
          "Challenging sources identify that this exact video was circulated in earlier monsoon seasons.",
          "High volume of retweets does not constitute independent institutional verification."
        ]
      }
    },
    {
      id: "contradiction_detection",
      title: "CONTRADICTION DETECTION",
      badge: {
        text: "🔴 CONFLICT DETECTED",
        variant: "red"
      },
      summaryItems: [
        {
          iconType: "alert",
          text: "Similar footage appears in an earlier publication.",
          variant: "red"
        }
      ],
      details: {
        overview: "Automated perceptual hashing matched keyframe indices against historical fact-checking and public media archives with high confidence.",
        metrics: [
          { label: "Keyframe Hash Distance", value: "0.058 (94.2% match)" },
          { label: "Earlier Publication Found", value: "August 2022 Archive" },
          { label: "Archival Identifier", value: "ARCHIVE-ID-220829" },
          { label: "Watermark Variance", value: "Crop applied on top-left" }
        ],
        forensicNotes: [
          "Identical white vehicle submerged to wheel arch visible in both sequences.",
          "Identical yellow pedestrian overpass structure in background frame 04:12.",
          "The chronological delta between the earliest known upload and today's claim is > 4 years."
        ]
      }
    },
    {
      id: "source_independence",
      title: "SOURCE INDEPENDENCE",
      badge: {
        text: "⚠ PARTIALLY DUPLICATED",
        variant: "amber"
      },
      summaryItems: [
        {
          iconType: "warning",
          text: "3 sources ≠ 3 independent confirmations",
          variant: "amber"
        }
      ],
      details: {
        overview: "Textual and temporal lineage mapping reveals that multiple social media accounts claiming to 'confirm' the footage are merely quoting the same initial viral tweet.",
        metrics: [
          { label: "Common Origin Node", value: "Telegram Aggregator 'BLR_LIVE'" },
          { label: "Syntactic Repetition", value: "91% identical caption phrasing" },
          { label: "Independent Eyes-On-Ground", value: "0 verified journalists" },
          { label: "Echo Multiplier", value: "3.4x syndication ratio" }
        ],
        forensicNotes: [
          "3 sources ≠ 3 independent confirmations.",
          "TrustLens analyzes evidence independence before increasing confidence.",
          "Information cascades frequently masquerade as multiple distinct confirmations."
        ]
      }
    },
    {
      id: "counter_evidence",
      title: "COUNTER-EVIDENCE",
      badge: {
        text: "🟠 FOUND",
        variant: "orange"
      },
      summaryItems: [
        {
          iconType: "warning",
          text: "Earlier publication of visually similar footage challenges the claimed date.",
          variant: "amber"
        }
      ],
      details: {
        overview: "Definitive archival counter-evidence invalidates the temporal claim that this specific visual recording occurred during today's meteorological event.",
        metrics: [
          { label: "Earliest Archival Timestamp", value: "2022-08-29 17:42 IST" },
          { label: "Archival Platform", value: "Regional News YouTube Channel" },
          { label: "Claim Discrepancy", value: "Temporal Displacement" },
          { label: "Verification Strength", value: "High (Cryptographic archive match)" }
        ],
        forensicNotes: [
          "Archived video title: 'Severe waterlogging at Rainbow Drive layout Bellandur 2022'.",
          "Geo-features and signboard markings completely align with historical 2022 record.",
          "Demonstrates that real footage of an actual past disaster is being weaponized out of time."
        ]
      }
    }
  ],
  battle: {
    supportingCount: 3,
    challengingCount: 3,
    summary: "Because material evidence points in both directions, TrustLens does not force a binary verdict.",
    supporting: [
      {
        id: "sup-1",
        source: "Bengaluru rainfall/flood reports",
        claimPoint: "Independent reporting confirms flooding conditions in the region.",
        type: "supporting",
        variant: "green",
        detail: "State disaster monitoring recorded high precipitation across urban zones with localized waterlogging.",
        reliability: "High (Official Reporting)"
      },
      {
        id: "sup-2",
        source: "Visual consistency",
        claimPoint: "The submitted footage is visually consistent with flood conditions.",
        type: "supporting",
        variant: "green",
        detail: "Water levels, road conditions, and urban infrastructure visible in video are physically consistent with severe flooding.",
        reliability: "High (Visual Analysis)"
      },
      {
        id: "sup-3",
        source: "Weather evidence",
        claimPoint: "Rainfall conditions are consistent with the claimed event.",
        type: "supporting",
        variant: "green",
        detail: "Radar data and meteorological bulletins indicate active convective precipitation over Bengaluru.",
        reliability: "High (Doppler Radar & Satellite)"
      }
    ],
    challenging: [
      {
        id: "chal-1",
        source: "Earlier publication",
        claimPoint: "Similar footage appears in an earlier publication.",
        type: "challenging",
        variant: "red",
        detail: "Reverse visual search discovered identical footage published previously in August 2022.",
        reliability: "High (Archive Match)"
      },
      {
        id: "chal-2",
        source: "Missing provenance",
        claimPoint: "Original capture time and location cannot be independently established.",
        type: "challenging",
        variant: "red",
        detail: "Original file creation timestamps and camera metadata are missing or stripped.",
        reliability: "High (Container Audit)"
      },
      {
        id: "chal-3",
        source: "Source duplication",
        claimPoint: "Multiple supporting reports may originate from the same underlying source.",
        type: "challenging",
        variant: "orange",
        detail: "Lineage tracing reveals circulating posts quote the same unverified post rather than independent verification.",
        reliability: "High (Lineage Mapping)"
      }
    ]
  },
  graph: {
    nodes: [
      { 
        id: "CLAIM", 
        label: "CLAIM", 
        category: "claim", 
        x: 480, 
        y: 60, 
        description: "“This video shows today’s flood in Bengaluru.”", 
        sublabel: "Factual Assertion",
        status: "neutral" 
      },
      { 
        id: "MEDIA", 
        label: "MEDIA", 
        category: "media", 
        x: 180, 
        y: 190, 
        description: "Flood Video (FLOOD_VIDEO_DEMO.mp4 - Authentic pixels, unverified date)", 
        sublabel: "Flood Video",
        status: "neutral" 
      },
      { 
        id: "URL", 
        label: "URL", 
        category: "url", 
        x: 370, 
        y: 190, 
        description: "Submitted URL (youtube.com/shorts/demo-flood-video - Suspicious redirects/tracking)", 
        sublabel: "Submitted URL",
        status: "challenging" 
      },
      { 
        id: "SUPPORTING_SOURCE_A", 
        label: "SUPPORTING SOURCE A", 
        category: "source", 
        x: 590, 
        y: 190, 
        description: "Reports flooding conditions in Bengaluru region today", 
        sublabel: "Rainfall Reports",
        status: "supporting" 
      },
      { 
        id: "SUPPORTING_SOURCE_B", 
        label: "SUPPORTING SOURCE B", 
        category: "source", 
        x: 800, 
        y: 190, 
        description: "Weather information confirms heavy rainfall conditions", 
        sublabel: "Weather Data",
        status: "supporting" 
      },
      { 
        id: "EARLIER_PUBLICATION", 
        label: "EARLIER PUBLICATION", 
        category: "counter", 
        x: 180, 
        y: 330, 
        description: "Archival record shows visually identical sequence existed in August 2022", 
        sublabel: "Aug 2022 Archive",
        status: "challenging" 
      },
      { 
        id: "CONTRADICTION", 
        label: "CONTRADICTION", 
        category: "conflict", 
        x: 390, 
        y: 360, 
        description: "Material conflict: Claim asserts 'today', but footage existed years earlier", 
        sublabel: "Temporal Conflict",
        status: "challenging" 
      },
      { 
        id: "COUNTER_EVIDENCE", 
        label: "COUNTER-EVIDENCE", 
        category: "counter", 
        x: 650, 
        y: 360, 
        description: "Earlier publication challenges the claimed date of the event", 
        sublabel: "Refutes Claimed Date",
        status: "challenging" 
      },
      { 
        id: "FINAL_ASSESSMENT", 
        label: "FINAL ASSESSMENT", 
        category: "verdict", 
        x: 480, 
        y: 490, 
        description: "INCONCLUSIVE (78% confidence): Authentic media reused out of date", 
        sublabel: "INCONCLUSIVE (78%)",
        status: "inconclusive" 
      }
    ],
    edges: [
      { from: "CLAIM", to: "MEDIA", label: "refers to", type: "neutral" },
      { from: "CLAIM", to: "URL", label: "distributed via", type: "neutral" },
      { from: "CLAIM", to: "SUPPORTING_SOURCE_A", label: "supported by", type: "supporting" },
      { from: "CLAIM", to: "SUPPORTING_SOURCE_B", label: "supported by", type: "supporting" },
      { from: "MEDIA", to: "EARLIER_PUBLICATION", label: "matches archived footage", type: "contradicting" },
      { from: "EARLIER_PUBLICATION", to: "CONTRADICTION", label: "creates contradiction", type: "contradicting" },
      { from: "CONTRADICTION", to: "COUNTER_EVIDENCE", label: "establishes counter-evidence", type: "contradicting" },
      { from: "CONTRADICTION", to: "FINAL_ASSESSMENT", label: "informs verdict", type: "final" }
    ]
  },
  timeline: [
    {
      id: "time-1",
      title: "Earlier publication",
      dateText: "August 29, 2022 · 17:42 IST",
      description: "Original raw footage recorded during Rainbow Drive Bellandur flooding and published on local community YouTube archive.",
      type: "past_archive",
      status: "warning"
    },
    {
      id: "time-2",
      title: "Claimed current event",
      dateText: "Today · 08:15 AM",
      description: "Social media post surfaces claiming: “This video shows today’s flood in Bengaluru.”",
      type: "viral_post",
      status: "neutral"
    },
    {
      id: "time-3",
      title: "TrustLens investigation",
      dateText: "Today · 08:32 AM",
      description: "Automated forensic pipeline ingests video hashes, checks URL security, and cross-references live meteorological data.",
      type: "investigation",
      status: "neutral"
    },
    {
      id: "time-4",
      title: "Supporting + conflicting evidence",
      dateText: "Today · 08:32 AM (+15s)",
      description: "Supporting: Real rainfall in region. Conflicting: Missing original provenance and syndication duplication.",
      type: "conflict",
      status: "alert"
    },
    {
      id: "time-5",
      title: "Counter-evidence",
      dateText: "Today · 08:33 AM",
      description: "Archival match confirms identical visual sequence appeared previously, directly refuting the claimed date.",
      type: "counter",
      status: "alert"
    },
    {
      id: "time-6",
      title: "INCONCLUSIVE",
      dateText: "Today · 08:33 AM (Finalized)",
      description: "Verdict rendered: Footage may be authentic, but cannot establish today’s Bengaluru flood.",
      type: "verdict",
      status: "warning"
    }
  ],
  reasoningSteps: [
    {
      number: 1,
      title: "CLAIM EXTRACTED",
      finding: "The claim concerns the date and location of the flood footage.",
      status: "neutral"
    },
    {
      number: 2,
      title: "MEDIA ANALYZED",
      finding: "No obvious manipulation detected, but provenance is incomplete.",
      status: "verified"
    },
    {
      number: 3,
      title: "URL ANALYZED",
      finding: "Suspicious redirect/tracking indicators detected in the demo analysis.",
      status: "alert"
    },
    {
      number: 4,
      title: "SUPPORTING EVIDENCE FOUND",
      finding: "Multiple sources support flooding conditions.",
      status: "verified"
    },
    {
      number: 5,
      title: "CONTRADICTION FOUND",
      finding: "Similar footage appears to have existed previously.",
      status: "alert"
    },
    {
      number: 6,
      title: "COUNTER-EVIDENCE FOUND",
      finding: "Earlier publication challenges the claimed date.",
      status: "alert"
    },
    {
      number: 7,
      title: "FINAL REASONING",
      finding: "Evidence is conflicting and provenance remains unresolved.",
      status: "warning"
    }
  ],
  trustTriangle: {
    manipulationLikelihood: 65.0,
    evidenceStrength: 82.0,
    evidenceConflict: 74.0,
  },
  evidenceSummary: {
    supportingStrength: 1.15,
    contradictingStrength: 1.30,
    independentEvidenceCount: 3,
    evidenceCoverage: 0.75,
    totalEvidenceCount: 6,
    supportingCount: 3,
    contradictingCount: 3,
    neutralCount: 0,
  },
  conflict: {
    detected: true,
    count: 1,
    severity: "HIGH",
    conflictScore: 0.74,
    conflictingEvidenceIds: ["ev_weather_radar", "ev_historical_archive"],
    description: "Archival footage from August 2022 contradicts current precipitation timeline.",
    details: [
      {
        conflictId: "conf_temporal_collision",
        description: "Sequence published in August 2022 conflicts with claimed current flood event.",
        conflictingEvidenceIds: ["ev_weather_radar", "ev_historical_archive"],
        severity: "HIGH",
        dimension: "TEMPORAL_ARCHIVE",
      }
    ],
  },
};

/** Pipeline stages shown while a LIVE investigation runs. No simulated telemetry. */
export const LIVE_PIPELINE_STAGES: PipelineStage[] = [
  { id: 'claim_extraction', label: 'CLAIM RECEIVED', subtext: 'Registering the claim exactly as submitted', status: 'pending' },
  { id: 'media_forensics', label: 'MEDIA FORENSICS', subtext: 'Not applicable to URL investigations (no media analyzed)', status: 'pending' },
  { id: 'url_security', label: 'URL SECURITY', subtext: 'Validating the URL, following redirects safely, checking HTTPS and tracking parameters', status: 'pending' },
  { id: 'evidence_retrieval', label: 'PAGE RETRIEVAL', subtext: 'Reading the public page: title, description, headings, visible text, canonical URL', status: 'pending' },
  { id: 'contradiction_check', label: 'CONTRADICTION CHECK', subtext: 'Comparing page information against the claim', status: 'pending' },
  { id: 'source_independence', label: 'SOURCE INDEPENDENCE', subtext: 'Checking how many independent sources are available', status: 'pending' },
  { id: 'counter_evidence', label: 'COUNTER-EVIDENCE', subtext: 'Looking for evidence that challenges the claim', status: 'pending' },
  { id: 'evidence_fusion', label: 'EVIDENCE FUSION', subtext: 'Weighing supporting against contradicting evidence', status: 'pending' },
  { id: 'final_reasoning', label: 'FINAL REASONING', subtext: 'AI reasoning over the retrieved evidence (this step can take several seconds)', status: 'pending' },
];
