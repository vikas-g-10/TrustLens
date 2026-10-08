import type {
  AnalysisCardData,
  EvidenceBattleItem,
  GraphEdge,
  GraphNode,
  InvestigationData,
  TimelineStep,
  VerdictStatus,
} from '../types/investigation';
import type { InvestigationResponse } from '../types/analysis';

type Item = AnalysisCardData['summaryItems'][number];

const UNAVAILABLE = 'Unavailable';
const INSUFFICIENT = 'Insufficient evidence';
const trunc = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + '…' : s);
const fmt = (iso: string) => new Date(iso).toLocaleString();

function urlSecurityCard(r: InvestigationResponse): AnalysisCardData {
  const a = r.urlAnalysis;
  if (!a) {
    return {
      id: 'url_security',
      title: 'URL SECURITY',
      badge: { text: UNAVAILABLE.toUpperCase(), variant: 'slate' },
      summaryItems: [{ iconType: 'info', text: 'No URL was submitted', variant: 'slate' }],
      details: { overview: 'No URL was provided, so no URL security checks were performed.', forensicNotes: [UNAVAILABLE] },
    };
  }
  if (!a.ok) {
    return {
      id: 'url_security',
      title: 'URL SECURITY',
      badge: { text: UNAVAILABLE.toUpperCase(), variant: 'slate' },
      summaryItems: [
        { iconType: 'alert', text: 'URL could not be verified', variant: 'red' },
        { iconType: 'warning', text: a.error.message, variant: 'amber' },
      ],
      details: {
        overview: 'The URL could not be retrieved, so redirect, tracking and page checks could not be performed.',
        metrics: [
          { label: 'Retrieval status', value: `Failed (${a.error.code})` },
          { label: 'Protocol Security', value: UNAVAILABLE },
          { label: 'Redirect Hops', value: UNAVAILABLE },
          { label: 'Tracking Parameters', value: UNAVAILABLE },
        ],
        forensicNotes: [a.error.message, 'A failed retrieval is not evidence that the site is malicious or genuine.'],
        technicalDisclaimer: 'Static analysis only. No page content was available.',
      },
    };
  }

  const d = a.data;
  const items: Item[] = [];
  items.push(d.https
    ? { iconType: 'check', text: 'HTTPS', variant: 'green' }
    : { iconType: 'warning', text: 'Connection is not HTTPS (unencrypted)', variant: 'amber' });
  if (d.redirectCount > 0) items.push({ iconType: 'warning', text: `Redirect detected (${d.redirectCount} hop${d.redirectCount > 1 ? 's' : ''})`, variant: 'amber' });
  if (d.trackingParams.length > 0) {
    items.push({ iconType: 'warning', text: `Tracking parameters: ${d.trackingParams.join(', ')}`, variant: 'amber' });
    items.push({ iconType: 'warning', text: 'Potential tracking behavior detected.', variant: 'amber' });
  }
  if (d.domainMismatch) items.push({ iconType: 'alert', text: `Domain mismatch: ${d.originalDomain} → ${d.finalDomain}`, variant: 'red' });
  if (d.suspiciousStructure.length > 0) items.push({ iconType: 'warning', text: `Suspicious URL structure: ${d.suspiciousStructure.join('; ')}`, variant: 'amber' });
  if (items.length === 1 && d.https) items.push({ iconType: 'check', text: 'No redirects, tracking parameters or unusual URL structure found', variant: 'green' });

  const concerning = d.domainMismatch || d.suspiciousStructure.length > 0;
  const caution = d.redirectCount > 0 || d.trackingParams.length > 0 || !d.https;
  const badge: AnalysisCardData['badge'] = concerning
    ? { text: '⚠ CONCERNS FOUND', variant: 'red' }
    : caution
    ? { text: '⚠ CAUTION', variant: 'amber' }
    : { text: '✓ NO ISSUES FOUND', variant: 'green' };

  const notes: string[] = [];
  if (d.redirectCount > 0) notes.push(`Redirect chain: ${d.redirectChain.join(' → ')}`);
  if (d.canonicalUrl) notes.push(`Canonical URL declared by the page: ${d.canonicalUrl}`);
  else notes.push('The page does not declare a canonical URL.');
  if (d.trackingParams.length > 0) notes.push('Potential tracking behavior detected. Actual data collection could not be independently verified.');
  if (notes.length === 0) notes.push('No additional observations.');

  return {
    id: 'url_security',
    title: 'URL SECURITY',
    badge,
    summaryItems: items,
    details: {
      overview: `The URL was retrieved (HTTP ${d.statusCode}). Findings below come from the real HTTP response; scripts were not executed.`,
      metrics: [
        { label: 'Protocol Security', value: d.https ? 'HTTPS' : 'HTTP (not encrypted)' },
        { label: 'Redirect Hops', value: String(d.redirectCount) },
        { label: 'Tracking Parameters', value: d.trackingParams.length ? d.trackingParams.join(', ') : 'None found' },
        { label: 'Destination Match', value: d.domainMismatch ? 'MISMATCH' : 'Same site' },
        { label: 'Final URL', value: trunc(d.finalUrl, 60) },
        { label: 'Page Title', value: d.title ? trunc(d.title, 60) : UNAVAILABLE },
      ],
      forensicNotes: notes,
      technicalDisclaimer: 'Static analysis of the HTTP response only. Actual data collection by the site was not observed.',
    },
  };
}

function mediaForensicsCard(r: InvestigationResponse): AnalysisCardData {
  const m = r.mediaAnalysis;
  if (!m || !m.analyzed) {
    return {
      id: 'media_forensics',
      title: 'MEDIA FORENSICS',
      badge: { text: UNAVAILABLE.toUpperCase(), variant: 'slate' },
      summaryItems: [{ iconType: 'info', text: 'No media was analyzed in this investigation', variant: 'slate' }],
      details: {
        overview: 'Live investigations analyze the claim and the submitted URL only when no media file is provided.',
        metrics: [{ label: 'Status', value: UNAVAILABLE }],
        forensicNotes: ['Media forensics are executed when an image file is uploaded.'],
      },
    };
  }

  const h = m.health;
  const exif = m.exif;
  const p = m.perceptualHash;
  const imgAnalysis = m.imageAnalysis;

  const healthScore = imgAnalysis?.evidenceHealth?.score ?? 50;
  const healthStatus = imgAnalysis?.evidenceHealth?.status ?? (healthScore >= 70 ? 'GOOD' : 'FAIR');
  const badgeVariant: AnalysisCardData['badge']['variant'] =
    healthScore >= 80 ? 'green' : healthScore >= 65 ? 'cyan' : healthScore >= 50 ? 'amber' : 'red';

  const items: Item[] = [];

  if (h?.resolution) {
    const mpStr = imgAnalysis?.file?.megapixels ? ` (${imgAnalysis.file.megapixels} MP)` : '';
    items.push({
      iconType: 'check',
      text: `${h.mimeType || 'Image'} · ${h.resolution}${mpStr}`,
      variant: 'green',
    });
  }

  if (h?.sha256) {
    items.push({
      iconType: 'check',
      text: `SHA-256: ${h.sha256.slice(0, 16)}…`,
      variant: 'green',
    });
  }

  if (exif && !exif.isStripped && (exif.cameraMake || exif.cameraModel)) {
    const hw = `${exif.cameraMake || ''} ${exif.cameraModel || ''}`.trim();
    items.push({
      iconType: 'check',
      text: `EXIF hardware provenance: ${hw}`,
      variant: 'green',
    });
  } else {
    items.push({
      iconType: 'info',
      text: 'EXIF metadata unavailable (neutral: 0 evidence)',
      variant: 'slate',
    });
  }

  if (m.elaAvailable && m.elaMeanError !== null && m.elaMeanError !== undefined) {
    items.push({
      iconType: 'check',
      text: `ELA computed: mean error differential ${m.elaMeanError}`,
      variant: 'green',
    });
  } else if (imgAnalysis?.ela?.status === 'not_applicable_non_jpeg') {
    items.push({
      iconType: 'info',
      text: `ELA: Not applicable for lossless ${imgAnalysis.file?.format || 'format'}`,
      variant: 'slate',
    });
  }

  if (p?.dhash && p?.phash) {
    items.push({
      iconType: 'check',
      text: `Perceptual hashes: dHash ${p.dhash.slice(0, 8)}… · pHash ${p.phash.slice(0, 8)}…`,
      variant: 'green',
    });
  }

  if (m.ocrText) {
    items.push({
      iconType: 'info',
      text: `OCR extracted text: "${trunc(m.ocrText, 60)}"`,
      variant: 'slate',
    });
  }

  if (m.multimodalAi) {
    const aiConfPct = Math.round((m.multimodalAi.confidence ?? 0) * 100);
    const aiAssessment = m.multimodalAi.aiGenerationAssessment?.replace(/_/g, ' ').toUpperCase() || 'INCONCLUSIVE';
    const isAi = m.multimodalAi.aiGenerationAssessment === 'likely_ai_generated';
    const isAuth = m.multimodalAi.aiGenerationAssessment === 'likely_authentic';
    const isManip = m.multimodalAi.aiGenerationAssessment === 'possibly_manipulated';
    items.push({
      iconType: isAi ? 'alert' : isAuth ? 'check' : isManip ? 'warning' : 'info',
      text: `Multimodal AI: ${aiAssessment} (${aiConfPct}% confidence)`,
      variant: isAi ? 'red' : isAuth ? 'green' : isManip ? 'amber' : 'slate',
    });
  }

  const metrics: { label: string; value: string }[] = [
    { label: 'File Name', value: m.mediaName || 'upload' },
    { label: 'File Size', value: h?.sizeBytes ? `${(h.sizeBytes / 1024).toFixed(1)} KB` : UNAVAILABLE },
    { label: 'Resolution', value: h?.resolution || UNAVAILABLE },
    { label: 'SHA-256', value: h?.sha256 ? `${h.sha256.slice(0, 12)}…` : UNAVAILABLE },
    { label: 'Evidence Health', value: `${healthScore}/100 (${healthStatus})` },
    { label: 'EXIF Provenance', value: exif && !exif.isStripped ? (exif.cameraMake || 'Present') : 'Unavailable (Neutral)' },
    { label: 'GPS Location', value: imgAnalysis?.metadata?.gpsPresent ? 'Present (Coordinates shielded)' : 'Unavailable' },
    { label: 'dHash', value: p?.dhash || UNAVAILABLE },
    { label: 'pHash', value: p?.phash || UNAVAILABLE },
    { label: 'Hash Comparison', value: 'Unavailable (no reference image)' },
    { label: 'ELA Status', value: m.elaAvailable ? `Measured (mean: ${m.elaMeanError})` : (imgAnalysis?.ela?.status || UNAVAILABLE) },
    { label: 'OCR Status', value: imgAnalysis?.ocr?.status || (m.ocrText ? 'SUCCESS' : UNAVAILABLE) },
    { label: 'AI Deepfake Detector', value: m.multimodalAi ? `Evaluated (${m.multimodalAi.modelUsed || 'Multimodal AI'})` : UNAVAILABLE },
    { label: 'Multimodal Assessment', value: m.multimodalAi ? m.multimodalAi.aiGenerationAssessment.replace(/_/g, ' ').toUpperCase() : UNAVAILABLE },
    { label: 'Multimodal Confidence', value: m.multimodalAi ? `${((m.multimodalAi.confidence ?? 0) * 100).toFixed(1)}%` : UNAVAILABLE },
    { label: 'PRNU Sensor Profile', value: UNAVAILABLE },
    { label: 'Optical Flow', value: UNAVAILABLE },
  ];


  const forensicNotes: string[] = [];
  if (m.forensicNotes && m.forensicNotes.length > 0) {
    forensicNotes.push(...m.forensicNotes);
  }
  forensicNotes.push('Evidence Health measures technical suitability for digital analysis, NOT real-world authenticity.');
  forensicNotes.push('Unavailable tests (AI detector, PRNU, optical flow) contribute zero evidence rather than negative suspicion.');

  return {
    id: 'media_forensics',
    title: 'MEDIA FORENSICS',
    badge: { text: `HEALTH: ${healthStatus} (${healthScore}/100)`, variant: badgeVariant },
    summaryItems: items,
    details: {
      overview: `Real Phase 4 image investigation performed on ${m.mediaName}. File integrity, dimensions, compression, EXIF metadata, ELA, and perceptual hashes measured genuinely without synthetic values.`,
      metrics,
      forensicNotes,
      technicalDisclaimer: 'Forensic measurements reflect technical image properties. High file health does not prove authenticity; missing metadata is not proof of tampering.',
    },
  };
}

function multimodalAiCard(r: InvestigationResponse): AnalysisCardData {
  const mm = r.multimodalAnalysis || r.mediaAnalysis?.multimodalAi || r.mediaAnalysis?.imageAnalysis?.multimodalAi;
  if (!mm) {
    return {
      id: 'multimodal_ai',
      title: 'MULTIMODAL AI ANALYSIS',
      badge: { text: UNAVAILABLE.toUpperCase(), variant: 'slate' },
      summaryItems: [{ iconType: 'info', text: 'No media was submitted for Multimodal AI visual inspection', variant: 'slate' }],
      details: {
        overview: 'Multimodal AI visual inspection analyzes uploaded imagery across lighting, perspective, anatomy, and synthetic diffusion artifacts.',
        metrics: [{ label: 'Status', value: UNAVAILABLE }],
        forensicNotes: ['Multimodal AI analysis is executed when an image is submitted with the claim.'],
      },
    };
  }

  const assessment = mm.aiGenerationAssessment || 'inconclusive';
  const confPct = Math.round((mm.confidence ?? 0) * 100);
  const formattedAssessment = assessment.replace(/_/g, ' ').toUpperCase();

  const isAi = assessment === 'likely_ai_generated';
  const isAuth = assessment === 'likely_authentic';
  const isManip = assessment === 'possibly_manipulated';

  const badgeVariant: AnalysisCardData['badge']['variant'] =
    isAi ? 'red' : isAuth ? 'green' : isManip ? 'amber' : 'slate';

  const items: Item[] = [
    {
      iconType: isAi ? 'alert' : isAuth ? 'check' : isManip ? 'warning' : 'info',
      text: `AI Assessment: ${formattedAssessment} · ${confPct}% confidence`,
      variant: badgeVariant,
    },
  ];

  if (mm.visualFindings && mm.visualFindings.length > 0) {
    items.push({
      iconType: 'info',
      text: `Visual finding: ${trunc(mm.visualFindings[0], 120)}`,
      variant: 'slate',
    });
  }


  if (mm.supportingSignals && mm.supportingSignals.length > 0) {
    items.push({
      iconType: 'check',
      text: `Supporting: ${trunc(mm.supportingSignals[0], 110)}`,
      variant: 'green',
    });
  }

  if (mm.contradictingSignals && mm.contradictingSignals.length > 0) {
    items.push({
      iconType: 'alert',
      text: `Contradicting: ${trunc(mm.contradictingSignals[0], 110)}`,
      variant: 'red',
    });
  }

  const forensicNotes: string[] = [];
  if (mm.explanation) {
    forensicNotes.push(`AI Explanation: ${mm.explanation}`);
  }
  if (mm.visualFindings && mm.visualFindings.length > 0) {
    forensicNotes.push(...mm.visualFindings.map((f: string) => `Visual Observation: ${f}`));
  }
  if (mm.supportingSignals && mm.supportingSignals.length > 0) {
    forensicNotes.push(...mm.supportingSignals.map((s: string) => `Supporting Signal: ${s}`));
  }
  if (mm.contradictingSignals && mm.contradictingSignals.length > 0) {
    forensicNotes.push(...mm.contradictingSignals.map((c: string) => `Contradicting Signal: ${c}`));
  }
  if (mm.limitations && mm.limitations.length > 0) {
    forensicNotes.push(...mm.limitations.map((l: string) => `Forensic Limitation: ${l}`));
  }

  return {
    id: 'multimodal_ai',
    title: 'MULTIMODAL AI ANALYSIS',
    badge: { text: `${formattedAssessment} (${confPct}%)`, variant: badgeVariant },
    summaryItems: items,
    details: {
      overview: mm.explanation || 'Visual analysis across lighting, geometry, facial anatomy, and synthetic artifacts.',
      metrics: [
        { label: 'AI Assessment', value: formattedAssessment },
        { label: 'Assessed Confidence', value: `${confPct}% (${(mm.confidence ?? 0).toFixed(2)})` },
        { label: 'Provider', value: mm.providerUsed || 'Groq' },
        { label: 'Vision Model', value: mm.modelUsed || 'qwen/qwen3.8-27b' },
        { label: 'Visual Findings', value: String(mm.visualFindings?.length ?? 0) },
        { label: 'Supporting Signals', value: String(mm.supportingSignals?.length ?? 0) },
        { label: 'Contradicting Signals', value: String(mm.contradictingSignals?.length ?? 0) },
      ],
      forensicNotes,
      technicalDisclaimer: 'Multimodal AI visual inspection is candidate evidence, not definitive proof of synthetic origin. Missing EXIF and ELA anomalies are evaluated in context.',
    },
  };
}


function buildCards(r: InvestigationResponse): AnalysisCardData[] {
  const f = r.final;
  const s = f.supportingEvidence.length;
  const c = f.contradictingEvidence.length;
  const pageOk = !!r.urlAnalysis && r.urlAnalysis.ok;
  const hasSearch = !!r.searchEvidence && Array.isArray(r.searchEvidence.sources);
  const searchSourceCount = hasSearch ? r.searchEvidence.sources.length : 0;
  const sourceCount = hasSearch
    ? `${searchSourceCount} external candidate source${searchSourceCount === 1 ? '' : 's'}`
    : pageOk ? '1 (the submitted page)' : '0';

  const evidenceBadge: AnalysisCardData['badge'] = !r.aiAvailable || (!s && !c)
    ? { text: INSUFFICIENT.toUpperCase(), variant: 'slate' }
    : s && c ? { text: '⚠ MIXED', variant: 'amber' }
    : s ? { text: '✓ SUPPORTED', variant: 'green' }
    : { text: '⚠ CHALLENGED', variant: 'red' };

  const evidenceItems: Item[] = !r.aiAvailable
    ? [{ iconType: 'info', text: 'Candidate evidence evaluation unavailable', variant: 'slate' }]
    : [
        { iconType: s ? 'check' : 'info', text: `${s} supporting point${s === 1 ? '' : 's'} identified`, variant: s ? 'green' : 'slate' },
        { iconType: c ? 'alert' : 'info', text: `${c} contradicting point${c === 1 ? '' : 's'} flagged`, variant: c ? 'red' : 'slate' },
      ];

  const contradictionBadge: AnalysisCardData['badge'] = !r.aiAvailable
    ? { text: UNAVAILABLE.toUpperCase(), variant: 'slate' }
    : c ? { text: '🔴 CONFLICT FLAGGED', variant: 'red' } : { text: 'NONE IDENTIFIED', variant: 'cyan' };

  const contradictionItems: Item[] = !r.aiAvailable
    ? [{ iconType: 'info', text: 'Contradiction analysis unavailable', variant: 'slate' }]
    : c
    ? f.contradictingEvidence.slice(0, 3).map((t): Item => ({ iconType: 'alert', text: trunc(t, 160), variant: 'red' }))
    : [{ iconType: 'info', text: 'No contradictions identified in retrieved candidates', variant: 'slate' }];

  const clusterCount = hasSearch && r.searchEvidence.clusters ? r.searchEvidence.clusters.length : 0;
  const indBadge: AnalysisCardData['badge'] = hasSearch && clusterCount > 0
    ? { text: `${clusterCount} CLUSTERS`, variant: 'cyan' }
    : { text: UNAVAILABLE.toUpperCase(), variant: 'slate' };

  const indItems: Item[] = hasSearch && clusterCount > 0
    ? [
        { iconType: 'info', text: `${clusterCount} heuristic independence cluster(s) formed`, variant: 'slate' },
        { iconType: 'check', text: `${searchSourceCount} candidate sources analyzed for wire duplication`, variant: 'green' },
      ]
    : [{ iconType: 'info', text: 'Independence clustering requires multi-source retrieval', variant: 'slate' }];

  const indNotes = hasSearch && r.searchEvidence.clusters
    ? r.searchEvidence.clusters.slice(0, 4).map((cl: any) => `${cl.clusterId} (${cl.independenceLevel}): ${cl.reason}`)
    : ['A single submitted source is one source, not independent confirmation.'];

  const counterBadge: AnalysisCardData['badge'] = hasSearch
    ? (c > 0 ? { text: '⚠ FLAGGED', variant: 'amber' } : { text: 'NONE FOUND', variant: 'cyan' })
    : { text: UNAVAILABLE.toUpperCase(), variant: 'slate' };

  const counterItems: Item[] = hasSearch
    ? [
        { iconType: c > 0 ? 'warning' : 'info', text: c > 0 ? `${c} counter/contradiction source(s) identified` : 'No counter-evidence candidates identified in search', variant: c > 0 ? 'amber' : 'slate' },
      ]
    : [{ iconType: 'info', text: 'External counter-evidence search was not performed', variant: 'slate' }];

  return [
    mediaForensicsCard(r),
    multimodalAiCard(r),
    urlSecurityCard(r),
    {
      id: 'independent_evidence',
      title: 'INDEPENDENT EVIDENCE',
      badge: evidenceBadge,
      summaryItems: evidenceItems,
      details: {
        overview: hasSearch
          ? `Retrieved ${searchSourceCount} candidate source(s) across ${clusterCount} heuristic cluster(s). Search results are candidate evidence only.`
          : 'Only the submitted page was retrieved. No third-party sources were searched.',
        metrics: [
          { label: 'Sources retrieved', value: sourceCount },
          { label: 'Supporting points', value: r.aiAvailable ? String(s) : UNAVAILABLE },
          { label: 'Contradicting points', value: r.aiAvailable ? String(c) : UNAVAILABLE },
          { label: 'Independence clusters', value: hasSearch ? String(clusterCount) : UNAVAILABLE },
        ],
        forensicNotes: f.uncertainties.length ? f.uncertainties.map((u) => `Uncertainty: ${u}`) : ['No additional notes.'],
      },
    },
    {
      id: 'contradiction_detection',
      title: 'CONTRADICTION DETECTION',
      badge: contradictionBadge,
      summaryItems: contradictionItems,
      details: {
        overview: 'Checks whether retrieved external sources contain debunking, denial, or contradictory assertions.',
        forensicNotes: c ? f.contradictingEvidence : [INSUFFICIENT],
      },
    },
    {
      id: 'source_independence',
      title: 'SOURCE INDEPENDENCE',
      badge: indBadge,
      summaryItems: indItems,
      details: {
        overview: hasSearch
          ? `Clustered ${searchSourceCount} candidate source(s) into ${clusterCount} groups using domain, title, and syndication heuristics.`
          : 'Source independence requires multiple sources. A single submitted page cannot be compared against other sources.',
        metrics: [
          { label: 'Sources examined', value: sourceCount },
          { label: 'Heuristic clusters', value: hasSearch ? String(clusterCount) : '0' },
        ],
        forensicNotes: indNotes,
      },
    },
    {
      id: 'counter_evidence',
      title: 'COUNTER-EVIDENCE',
      badge: counterBadge,
      summaryItems: counterItems,
      details: {
        overview: hasSearch
          ? 'Counter queries specifically searched for debunking, fact-checks, corrections, and official denials.'
          : 'This version does not search archives, news or other websites for evidence challenging the claim.',
        metrics: [{ label: 'Counter search', value: hasSearch ? 'Executed' : UNAVAILABLE }],
        forensicNotes: c ? f.contradictingEvidence : ['No explicit contradiction or debunking candidate found.'],
      },
    },
  ];
}

function buildBattle(r: InvestigationResponse): InvestigationData['battle'] {
  const f = r.final;
  const hasSearch = !!r.searchEvidence;
  const mk = (type: 'supporting' | 'challenging', variant: EvidenceBattleItem['variant']) => (text: string, i: number): EvidenceBattleItem => {
    let source = hasSearch ? 'Retrieved search candidate' : 'Retrieved page';
    let claimPoint = text;
    let reliability = hasSearch ? 'Heuristic reliability scorer' : 'AI-assessed · single source';

    if (text.startsWith('[')) {
      const closeBracket = text.indexOf(']');
      if (closeBracket > 1) {
        source = text.slice(1, closeBracket);
        claimPoint = text.slice(closeBracket + 1).trim();
      }
    }

    return {
      id: `${type}-${i + 1}`,
      source,
      claimPoint,
      type,
      variant,
      detail: hasSearch
        ? 'Retrieved via multi-query candidate search and categorized by deterministic keyword and contradiction signals.'
        : 'Identified by reasoning over the information retrieved from the submitted URL.',
      reliability,
    };
  };

  const supporting = f.supportingEvidence.map(mk('supporting', 'green'));
  const challenging = f.contradictingEvidence.map(mk('challenging', 'red'));
  const summary = !r.aiAvailable
    ? 'Evidence retrieval was incomplete or unavailable. Insufficient evidence for a verdict.'
    : !supporting.length && !challenging.length
    ? 'Insufficient evidence was found either way across retrieved sources.'
    : supporting.length && challenging.length
    ? 'Evidence points in multiple directions across candidate sources, so TrustLens does not force a binary verdict.'
    : supporting.length
    ? 'Supporting evidence was retrieved from candidate sources, pending final evidence fusion.'
    : 'Only challenging or contradicting evidence was identified in retrieved candidates.';
  return { supportingCount: supporting.length, challengingCount: challenging.length, summary, supporting, challenging };
}


function buildGraph(r: InvestigationResponse, status: VerdictStatus): InvestigationData['graph'] {
  const f = r.final;
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const pageOk = !!r.urlAnalysis && r.urlAnalysis.ok;
  const verdictLabel = status.replace('_', ' ');

  nodes.push({ id: 'CLAIM', label: 'CLAIM', category: 'claim', x: 480, y: 55, description: r.claim, sublabel: trunc(r.claim, 26), status: 'neutral', significance: 'The assertion submitted by the user, exactly as entered.' });

  if (r.inputUrl) {
    const err = r.urlAnalysis && !r.urlAnalysis.ok ? r.urlAnalysis.error.message : null;
    nodes.push({
      id: 'URL', label: 'URL', category: 'url', x: 380, y: 180,
      description: pageOk ? `Submitted URL ${r.inputUrl} (retrieved)` : `Submitted URL ${r.inputUrl}: ${err ?? 'not retrieved'}`,
      sublabel: trunc(r.inputUrl.replace(/^https?:\/\//, ''), 26),
      status: pageOk ? 'neutral' : 'inconclusive',
      significance: pageOk ? 'The page behind this URL was retrieved and analyzed.' : 'The URL could not be retrieved, so no page evidence exists.',
    });
    edges.push({ from: 'CLAIM', to: 'URL', label: 'submitted with', type: 'neutral' });
  }

  const sup = f.supportingEvidence.slice(0, 2);
  const con = f.contradictingEvidence.slice(0, 2);
  const supX = [150, 330];
  const conX = [630, 810];
  sup.forEach((t, i) => {
    const id = `SUPPORT_${i + 1}`;
    nodes.push({ id, label: `SUPPORT ${i + 1}`, category: 'source', x: supX[i], y: 335, description: t, sublabel: trunc(t, 24), status: 'supporting', significance: 'Evidence from the retrieved page that supports the claim (AI-assessed).' });
    edges.push({ from: r.inputUrl ? 'URL' : 'CLAIM', to: id, label: 'supports', type: 'supporting' });
    edges.push({ from: id, to: 'VERDICT', label: 'informs verdict', type: 'supporting' });
  });
  con.forEach((t, i) => {
    const id = `CONTRA_${i + 1}`;
    nodes.push({ id, label: `CONTRADICTION ${i + 1}`, category: 'conflict', x: conX[i], y: 335, description: t, sublabel: trunc(t, 24), status: 'challenging', significance: 'Evidence from the retrieved page that challenges the claim (AI-assessed).' });
    edges.push({ from: r.inputUrl ? 'URL' : 'CLAIM', to: id, label: 'contradicts', type: 'contradicting' });
    edges.push({ from: id, to: 'VERDICT', label: 'informs verdict', type: 'contradicting' });
  });
  if (!sup.length && !con.length) {
    nodes.push({ id: 'NO_EVIDENCE', label: 'INSUFFICIENT EVIDENCE', category: 'source', x: 480, y: 335, description: 'No usable supporting or contradicting evidence was identified.', sublabel: 'Nothing to weigh', status: 'inconclusive', significance: 'No evidence could be established either way.' });
    edges.push({ from: r.inputUrl ? 'URL' : 'CLAIM', to: 'NO_EVIDENCE', label: 'yielded', type: 'neutral' });
    edges.push({ from: 'NO_EVIDENCE', to: 'VERDICT', label: 'informs verdict', type: 'final' });
  }

  nodes.push({
    id: 'VERDICT', label: 'FINAL ASSESSMENT', category: 'verdict', x: 480, y: 500,
    description: `${verdictLabel} (${f.confidence}% confidence): ${f.summary}`,
    sublabel: `${verdictLabel} (${f.confidence}%)`,
    status: (status === 'LIKELY_GENUINE' || status === 'LIKELY_AUTHENTIC') ? 'supporting' : (status === 'HIGH_RISK' || status === 'LIKELY_AI_GENERATED' || status === 'LIKELY_MANIPULATED') ? 'challenging' : 'inconclusive',
    significance: r.aiAvailable ? 'The verdict generated by AI reasoning over the retrieved evidence.' : 'AI reasoning was unavailable; this is a transparent INCONCLUSIVE fallback.',
  });
  return { nodes, edges };
}

function buildTimeline(r: InvestigationResponse, submittedAt: string): TimelineStep[] {
  const f = r.final;
  const t: TimelineStep[] = [];
  t.push({ id: 't1', title: 'Claim submitted', dateText: fmt(submittedAt), description: `Claim received: “${trunc(r.claim, 200)}”`, type: 'investigation', status: 'neutral' });

  if (!r.inputUrl || !r.urlAnalysis) {
    t.push({ id: 't2', title: 'No URL provided', dateText: fmt(r.generatedAt), description: 'No URL was submitted, so no page could be retrieved.', type: 'conflict', status: 'warning' });
  } else if (!r.urlAnalysis.ok) {
    t.push({ id: 't2', title: 'URL retrieval failed', dateText: fmt(r.generatedAt), description: r.urlAnalysis.error.message, type: 'conflict', status: 'alert' });
  } else {
    const d = r.urlAnalysis.data;
    t.push({ id: 't2', title: 'URL retrieved', dateText: fmt(d.fetchedAt), description: `HTTP ${d.statusCode} from ${d.finalUrl} after ${d.redirectCount} redirect${d.redirectCount === 1 ? '' : 's'}.`, type: 'investigation', status: 'neutral' });
    t.push({ id: 't3', title: 'Page information extracted', dateText: fmt(d.fetchedAt), description: `Title: ${d.title ?? UNAVAILABLE}. ${d.headings.length} heading${d.headings.length === 1 ? '' : 's'} and ${d.visibleText.length.toLocaleString()} characters of visible text read.`, type: 'investigation', status: 'neutral' });
  }

  if (r.aiAvailable) {
    t.push({ id: 't4', title: 'Evidence weighed', dateText: fmt(r.generatedAt), description: `Supporting: ${f.supportingEvidence.length}. Contradicting: ${f.contradictingEvidence.length}.`, type: f.contradictingEvidence.length ? 'counter' : 'conflict', status: f.contradictingEvidence.length ? 'alert' : 'neutral' });
  } else {
    t.push({ id: 't4', title: 'AI reasoning unavailable', dateText: fmt(r.generatedAt), description: r.aiNote ?? 'AI reasoning could not be completed.', type: 'conflict', status: 'warning' });
  }
  const isNegative = f.verdict === 'HIGH_RISK' || f.verdict === 'LIKELY_AI_GENERATED' || f.verdict === 'LIKELY_MANIPULATED';
  const isPositive = f.verdict === 'LIKELY_GENUINE' || f.verdict === 'LIKELY_AUTHENTIC';
  t.push({ id: 't5', title: f.verdict.replace(/_/g, ' '), dateText: `${fmt(r.generatedAt)} (Finalized)`, description: f.summary, type: 'verdict', status: isNegative ? 'alert' : isPositive ? 'success' : 'warning' });
  return t;
}

function buildReasoning(r: InvestigationResponse): InvestigationData['reasoningSteps'] {
  const f = r.final;
  const steps: InvestigationData['reasoningSteps'] = [];
  const push = (title: string, finding: string, status: 'neutral' | 'alert' | 'warning' | 'verified') =>
    steps.push({ number: steps.length + 1, title, finding, status });

  push('CLAIM RECEIVED', r.claim, 'neutral');
  if (!r.inputUrl) push('URL ANALYZED', 'No URL submitted. ' + UNAVAILABLE + '.', 'warning');
  else if (r.urlAnalysis && !r.urlAnalysis.ok) push('URL ANALYZED', `Could not be verified: ${r.urlAnalysis.error.message}`, 'alert');
  else if (r.urlAnalysis?.ok) {
    const d = r.urlAnalysis.data;
    const flags = [d.redirectCount ? `${d.redirectCount} redirect(s)` : '', d.trackingParams.length ? 'tracking parameters' : '', d.domainMismatch ? 'domain mismatch' : '', d.suspiciousStructure.length ? 'unusual URL structure' : ''].filter(Boolean);
    push('URL ANALYZED', `Retrieved ${d.finalUrl} (HTTP ${d.statusCode}, ${d.https ? 'HTTPS' : 'not HTTPS'}). ${flags.length ? 'Flags: ' + flags.join(', ') + '.' : 'No URL-level flags.'}`, flags.length ? 'warning' : 'verified');
  }
  if (r.aiAvailable) {
    f.reasoning.slice(0, 6).forEach((step) => push('AI REASONING', step, 'neutral'));
  } else {
    push('AI REASONING', r.aiNote ?? 'AI reasoning was unavailable.', 'warning');
  }
  return steps;
}

function whyBullets(r: InvestigationResponse): string[] {
  const f = r.final;
  const pick = (f.verdict === 'LIKELY_GENUINE' || f.verdict === 'LIKELY_AUTHENTIC')
    ? [...f.supportingEvidence.slice(0, 3), ...f.uncertainties.slice(0, 2)]
    : (f.verdict === 'HIGH_RISK' || f.verdict === 'LIKELY_AI_GENERATED' || f.verdict === 'LIKELY_MANIPULATED')
    ? [...f.contradictingEvidence.slice(0, 3), ...f.uncertainties.slice(0, 2)]
    : [...f.uncertainties.slice(0, 3), ...f.contradictingEvidence.slice(0, 2)];
  const bullets = pick.map((b) => trunc(b, 220));
  if (r.urlAnalysis?.ok && r.urlAnalysis.data.trackingParams.length) bullets.push('URL contains tracking parameters (potential tracking behavior detected)');
  return bullets.length ? bullets : [INSUFFICIENT];
}

export function buildLiveInvestigation(r: InvestigationResponse, submittedAt: string): InvestigationData {
  const f = r.final;
  const status: VerdictStatus = f.verdict;
  const hasC = f.contradictingEvidence.length > 0;
  const genuineText = status === 'LIKELY_GENUINE' || status === 'LIKELY_AUTHENTIC'
    ? 'Not applicable: the available evidence supports the claim or image authenticity.'
    : [...f.contradictingEvidence, ...f.uncertainties].slice(0, 3).join(' ') || INSUFFICIENT + ' to establish that the claim is genuine.';
  const highRiskText = status === 'HIGH_RISK' || status === 'LIKELY_AI_GENERATED' || status === 'LIKELY_MANIPULATED'
    ? 'Not applicable: the evidence contradicts the claim or detects synthetic/manipulated indicators.'
    : hasC
    ? 'Contradicting points were found but did not decisively show the claim to be false or deceptive.'
    : 'No contradicting evidence was identified in the retrieved information.';

  return {
    caseId: `TL-LIVE-${Date.now().toString(36).toUpperCase()}`,
    isDemo: false,
    createdAt: r.generatedAt,
    live: r,
    claim: r.claim,
    mediaName: r.mediaAnalysis?.mediaName || 'Not provided',
    url: r.inputUrl ?? 'Not provided',
    verdict: {
      status,
      confidence: Math.min(95, Math.max(0, Math.round(f.confidence))),
      headline: status.replace(/_/g, ' '),
      mainExplanation: f.summary,
      whyNotGenuine: genuineText,
      whyNotHighRisk: highRiskText,
      finalReasoning: f.summary,
      whyBullets: whyBullets(r),
    },
    cards: buildCards(r),
    battle: buildBattle(r),
    graph: buildGraph(r, status),
    timeline: buildTimeline(r, submittedAt),
    reasoningSteps: buildReasoning(r),
    trustTriangle: r.trustTriangle,
    evidenceSummary: r.evidenceSummary,
    conflict: r.conflict,
    normalizedEvidence: r.normalizedEvidence,
  };
}
