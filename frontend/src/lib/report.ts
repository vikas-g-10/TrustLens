import type { InvestigationData } from '../types/investigation';

const list = (items: string[]) => (items.length ? items.map((i) => `- ${i}`).join('\n') : '- Insufficient evidence');

export function buildReportMarkdown(data: InvestigationData, generatedAt: string): string {
  const card = (id: string) => data.cards.find((c) => c.id === id);
  const items = (id: string) => list(card(id)?.summaryItems.map((i) => i.text) ?? ['Unavailable']);
  const status = data.verdict.status.replace('_', ' ');
  const classification = data.isDemo ? 'DEMO INVESTIGATION · SIMULATED ANALYSIS' : 'LIVE URL INVESTIGATION';

  const lines: string[] = [
    '# EVIDENCE INVESTIGATION REPORT',
    `Case ID: ${data.caseId}`,
    `Verdict: ${status} (Confidence: ${data.verdict.confidence}%)`,
    `Generated: ${generatedAt}`,
    `Classification: ${classification}`,
    '',
    '## 1. INVESTIGATED CLAIM',
    `"${data.claim}"`,
    `Submitted URL: ${data.url}`,
    `Media: ${data.mediaName}`,
    '',
    '## 2. FINAL ASSESSMENT',
    `Verdict: ${status}`,
    `Summary: ${data.verdict.mainExplanation}`,
    '',
    data.isDemo ? '## 3. MEDIA FORENSICS FINDINGS (SIMULATED)' : '## 3. MEDIA FORENSICS FINDINGS',
    items('media_forensics'),
    '',
    '## 4. URL SECURITY FINDINGS',
    items('url_security'),
  ];

  const live = data.live;
  if (live?.urlAnalysis?.ok) {
    const d = live.urlAnalysis.data;
    lines.push(
      '',
      'Retrieved page information:',
      `- Final URL: ${d.finalUrl} (HTTP ${d.statusCode})`,
      `- Redirects: ${d.redirectCount}`,
      `- Title: ${d.title ?? 'Unavailable'}`,
      `- Meta description: ${d.metaDescription ?? 'Unavailable'}`,
      `- Canonical URL: ${d.canonicalUrl ?? 'Unavailable'}`,
      `- Headings: ${d.headings.length ? d.headings.slice(0, 8).join(' | ') : 'Unavailable'}`,
      `- Retrieved at: ${d.fetchedAt}`
    );
  } else if (live?.urlAnalysis && !live.urlAnalysis.ok) {
    lines.push('', `Retrieval failed: ${live.urlAnalysis.error.message}`);
  }
  lines.push(
    '* Potential tracking behavior is inferred from URL parameters only. Actual data collection could not be independently verified.',
    '',
    '## 5. SUPPORTING EVIDENCE',
    list(data.battle.supporting.map((s) => (data.isDemo ? `[${s.source}] ${s.claimPoint}: ${s.detail}` : s.claimPoint))),
    '',
    '## 6. CONTRADICTING EVIDENCE',
    list(data.battle.challenging.map((c) => (data.isDemo ? `[${c.source}] ${c.claimPoint}: ${c.detail}` : c.claimPoint))),
    '',
    '## 7. SOURCE INDEPENDENCE',
    data.isDemo
      ? '- (Simulated) Lineage analysis indicates multi-post syndication traces back to a single unverified post.'
      : '- Unavailable: only the submitted page was examined; no independent sources were searched.',
    '',
    '## 8. REASONING',
    ...(data.isDemo
      ? [`- Why Not Genuine: ${data.verdict.whyNotGenuine}`, `- Why Not High Risk: ${data.verdict.whyNotHighRisk}`, `- Core Conclusion: ${data.verdict.finalReasoning}`]
      : [
          ...data.reasoningSteps.map((s) => `${s.number}. ${s.title}: ${s.finding}`),
          `- Why not genuine: ${data.verdict.whyNotGenuine}`,
          `- Why not high risk: ${data.verdict.whyNotHighRisk}`,
        ])
  );

  if (live) {
    lines.push('', '## 9. ANALYSIS METHOD', `- AI reasoning: ${live.aiAvailable ? `Groq (${live.model})` : 'Unavailable'}`);
    if (live.aiNote) lines.push(`- Note: ${live.aiNote}`);
    if (live.final.uncertainties.length) lines.push('- Uncertainties:', ...live.final.uncertainties.map((u) => `  - ${u}`));
  } else {
    lines.push('', '## 9. NOTICE', '- This is a DEMO INVESTIGATION. All findings are SIMULATED and do not describe real events or media.');
  }
  return lines.join('\n');
}

export async function sha256Hex(text: string): Promise<string | null> {
  try {
    if (!globalThis.crypto?.subtle) return null;
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
    return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
  } catch {
    return null;
  }
}
