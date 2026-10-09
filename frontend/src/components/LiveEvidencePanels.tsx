import React from 'react';
import { AlertTriangle, Info, Link2, Layers } from 'lucide-react';
import type { InvestigationResponse, ImageTextRelationship } from '../types/analysis';

/**
 * Phase 7: renders REAL backend investigation data only (live runs, never the demo case).
 * Every value comes from the response; anything missing is shown as "Unavailable".
 */

const UNAVAILABLE = 'Unavailable';

const SECTION = 'rounded-2xl border border-slate-800 bg-slate-950/70 p-6 space-y-4';
const KICKER = 'text-xs font-mono font-bold tracking-widest text-cyan-400 uppercase';
const TITLE = 'text-xl font-bold text-white font-display mt-0.5';

const REL_STYLE: Record<ImageTextRelationship, string> = {
  SUPPORTS: 'border-emerald-500/50 bg-emerald-950/40 text-emerald-300',
  CONTRADICTS: 'border-rose-500/50 bg-rose-950/40 text-rose-300',
  PARTIALLY_SUPPORTS: 'border-amber-500/50 bg-amber-950/40 text-amber-300',
  UNRELATED: 'border-slate-600 bg-slate-900 text-slate-300',
  INSUFFICIENT_TEXT: 'border-slate-600 bg-slate-900 text-slate-300',
};

const DIR_STYLE: Record<string, string> = {
  SUPPORTS: 'text-emerald-300 border-emerald-800/60 bg-emerald-950/40',
  PARTIALLY_SUPPORTS: 'text-amber-300 border-amber-800/60 bg-amber-950/40',
  CONTRADICTS: 'text-rose-300 border-rose-800/60 bg-rose-950/40',
};

const pct = (v: number | null | undefined) =>
  v === null || v === undefined ? UNAVAILABLE : `${Math.round(v * 100)}%`;

// ---------------------------------------------------------------------------
// 1. Honest status notices (error / search / multimodal / no or thin evidence)
// ---------------------------------------------------------------------------
export function buildNotices(r: InvestigationResponse): { tone: 'red' | 'amber' | 'slate'; text: string }[] {
  const out: { tone: 'red' | 'amber' | 'slate'; text: string }[] = [];

  if (r.serviceError) {
    out.push({
      tone: 'red',
      text: `The investigation service could not be reached (${r.serviceError}). This INCONCLUSIVE result is a placeholder, not an analysis of your claim.`,
    });
    return out; // nothing else below is meaningful without a backend result
  }

  const se = r.searchEvidence;
  if (!se) {
    out.push({ tone: 'slate', text: 'Web search unavailable: no external search was performed for this investigation.' });
  } else if (se.retrievalStatus === 'FAILED') {
    out.push({ tone: 'amber', text: `Web search unavailable: ${(se.retrievalNote || 'the search provider could not be reached').replace(/\.+$/, '')}. No web evidence was retrieved.` });
  } else if (se.retrievalStatus === 'PARTIAL') {
    out.push({ tone: 'amber', text: `Web search returned partial results${se.retrievalNote ? `: ${se.retrievalNote}` : '.'}` });
  } else if (Array.isArray(se.sources) && se.sources.length === 0) {
    out.push({ tone: 'slate', text: 'Web search ran but found no usable sources for this claim.' });
  }

  const mm = r.multimodalAnalysis;
  if (r.mediaAnalysis?.analyzed) {
    if (!mm) {
      out.push({ tone: 'amber', text: 'Multimodal AI provider unavailable: no visual AI assessment was produced. Deterministic image forensics still apply.' });
    } else if (mm.aiGenerationAssessment === 'inconclusive' && mm.confidence === 0) {
      const why = mm.limitations?.[0] || mm.explanation || 'no reason given';
      out.push({ tone: 'amber', text: `Multimodal AI provider unavailable or failed: ${why}` });
    }
  }

  const total = r.evidenceSummary?.totalEvidenceCount;
  if ((r.normalizedEvidence && r.normalizedEvidence.length === 0) || total === 0) {
    out.push({ tone: 'slate', text: 'No evidence was collected. The verdict cannot be anything other than INCONCLUSIVE.' });
  } else if (r.final.verdict === 'INCONCLUSIVE') {
    out.push({ tone: 'slate', text: 'Insufficient evidence: the collected evidence does not decide the question either way.' });
  }
  return out;
}

export const StatusNotices: React.FC<{ live: InvestigationResponse }> = ({ live }) => {
  const notices = buildNotices(live);
  if (!notices.length) return null;
  const tone = {
    red: 'border-rose-500/50 bg-rose-950/30 text-rose-200',
    amber: 'border-amber-500/40 bg-amber-950/20 text-amber-200',
    slate: 'border-slate-700 bg-slate-900/60 text-slate-300',
  };
  return (
    <div className="space-y-2" role="status">
      {notices.map((n, i) => (
        <div key={i} className={`flex items-start gap-2 rounded-xl border p-3 text-xs ${tone[n.tone]}`}>
          {n.tone === 'slate' ? <Info className="h-4 w-4 shrink-0 mt-0.5" /> : <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />}
          <span>{n.text}</span>
        </div>
      ))}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 2. Image text (OCR) evidence
// ---------------------------------------------------------------------------
const PointList: React.FC<{ label: string; items: string[]; cls: string }> = ({ label, items, cls }) => (
  <div>
    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block mb-1">{label}</span>
    {items.length ? (
      <div className="flex flex-wrap gap-1.5">
        {items.map((p, i) => (
          <span key={i} className={`rounded border px-1.5 py-0.5 text-[11px] ${cls}`}>{p}</span>
        ))}
      </div>
    ) : (
      <span className="text-xs text-slate-500">None</span>
    )}
  </div>
);

export const ImageTextEvidencePanel: React.FC<{ live: InvestigationResponse }> = ({ live }) => {
  if (!live.mediaAnalysis?.analyzed) return null;
  const ite = live.imageTextEvidence;
  const ocr = live.mediaAnalysis?.imageAnalysis?.ocr;

  return (
    <section id="image-text-evidence" className={SECTION}>
      <div>
        <span className={KICKER}>Image Text Evidence</span>
        <h3 className={TITLE}>Text found inside the image</h3>
        <p className="text-xs text-slate-400 mt-1">
          Text in an image is evidence of what the image <em>states</em>. It is not proof that the statement is true.
        </p>
      </div>

      {!ite ? (
        <div className="space-y-2 text-xs text-slate-300">
          <p>
            No image-text comparison was produced
            {live.mediaAnalysis?.imageAnalysis ? ' (no claim text was submitted to compare against).' : '.'}
          </p>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block mb-1">
              OCR status: {ocr?.status ?? UNAVAILABLE}
            </span>
            <span className="font-mono text-slate-200 break-words">
              {ocr?.text ? ocr.text : 'No extracted text available.'}
            </span>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
            <span className={`rounded-lg border px-3 py-1 font-bold ${REL_STYLE[ite.relationship]}`}>
              {ite.relationship.replace(/_/g, ' ')}
            </span>
            <span className="text-slate-400">OCR quality: <span className="text-slate-100 font-bold">{pct(ite.ocrQuality)}</span></span>
            <span className="text-slate-400">Provenance: <span className="text-slate-100">{ite.source}</span></span>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block mb-1">Extracted text</span>
            <span className="font-mono text-xs text-slate-200 break-words whitespace-pre-wrap">
              {ite.extractedText || 'No text extracted.'}
            </span>
          </div>

          {ite.relevantText && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block mb-1">Relevant text</span>
              <span className="font-mono text-xs text-slate-200 break-words">{ite.relevantText}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <PointList label="Matched facts" items={ite.matchedClaimPoints} cls="border-emerald-800/60 bg-emerald-950/40 text-emerald-300" />
            <PointList label="Contradicted facts" items={ite.contradictedClaimPoints} cls="border-rose-800/60 bg-rose-950/40 text-rose-300" />
            <PointList label="Not found in image text" items={ite.missingClaimPoints} cls="border-slate-700 bg-slate-900 text-slate-300" />
          </div>

          <p className="text-xs text-slate-300">{ite.explanation || UNAVAILABLE}</p>
        </div>
      )}
    </section>
  );
};

// ---------------------------------------------------------------------------
// 3. Web sources: reliability + independence (backend heuristics, shown as-is)
// ---------------------------------------------------------------------------
const MAX_SOURCES = 8;

export const SourceReliabilityPanel: React.FC<{ live: InvestigationResponse }> = ({ live }) => {
  const se = live.searchEvidence;
  const sources: any[] = Array.isArray(se?.sources) ? se.sources : [];
  if (!sources.length) return null;

  return (
    <section id="source-reliability" className={SECTION}>
      <div>
        <span className={KICKER}>Web Evidence</span>
        <h3 className={TITLE}>Source reliability &amp; independence</h3>
        <p className="text-xs text-slate-400 mt-1">
          Candidate sources only. Reliability and independence are heuristic scores from the backend, not verification.
          {sources.length > MAX_SOURCES && ` Showing ${MAX_SOURCES} of ${sources.length}.`}
        </p>
      </div>
      <div className="space-y-2">
        {sources.slice(0, MAX_SOURCES).map((s, i) => (
          <div key={`${s.url}-${i}`} className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-xs space-y-1.5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-cyan-300 hover:text-cyan-200 font-semibold break-words min-w-0">
                {s.title || s.domain}
              </a>
              <span className="font-mono text-[10px] text-slate-400">{s.domain}</span>
            </div>
            <div className="flex flex-wrap gap-2 font-mono text-[10px]">
              <span className="rounded border border-slate-700 px-1.5 py-0.5 text-slate-200">Reliability {s.reliabilityScore ?? UNAVAILABLE}{typeof s.reliabilityScore === 'number' ? '/100' : ''}</span>
              <span className="rounded border border-slate-700 px-1.5 py-0.5 text-slate-200">Independence {s.independenceLevel ?? UNAVAILABLE}</span>
              {s.clusterId && <span className="rounded border border-slate-700 px-1.5 py-0.5 text-slate-400">{s.clusterId}</span>}
              <span className={`rounded border px-1.5 py-0.5 ${s.evidenceRole === 'SUPPORTING' ? DIR_STYLE.SUPPORTS : s.evidenceRole === 'CONTRADICTING' ? DIR_STYLE.CONTRADICTS : 'border-slate-700 text-slate-300'}`}>
                {s.evidenceRole ?? 'UNKNOWN'}
              </span>
            </div>
            {s.classificationReason && <p className="text-slate-400">{s.classificationReason}</p>}
            {Array.isArray(s.reliabilityExplanation) && s.reliabilityExplanation.length > 0 && (
              <p className="text-slate-500">{s.reliabilityExplanation.join(' · ')}</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
};

// ---------------------------------------------------------------------------
// 4. Evidence ledger: every normalized item the Phase 6 fusion actually used
// ---------------------------------------------------------------------------
export const EvidenceLedger: React.FC<{ live: InvestigationResponse }> = ({ live }) => {
  const items = live.normalizedEvidence;
  if (!items || items.length === 0) return null;
  const sup = new Set(live.final.supportingEvidenceIds ?? []);
  const con = new Set(live.final.contradictingEvidenceIds ?? []);

  return (
    <section id="evidence-ledger" className={SECTION}>
      <div className="flex items-start gap-2">
        <Layers className="h-5 w-5 text-cyan-400 mt-1 shrink-0" />
        <div>
          <span className={KICKER}>Evidence Provenance</span>
          <h3 className={TITLE}>Evidence ledger ({items.length})</h3>
          <p className="text-xs text-slate-400 mt-1">
            Every item the deterministic Phase 6 fusion weighed, with its reliability, independence group and origin.
          </p>
        </div>
      </div>
      <div className="space-y-2">
        {items.map((it) => (
          <div key={it.evidenceId} className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-xs space-y-1.5">
            <div className="flex flex-wrap items-center gap-2 font-mono text-[10px]">
              <span className="text-slate-200 font-bold">{it.evidenceId}</span>
              <span className="rounded border border-slate-700 px-1.5 py-0.5 text-slate-300">{it.evidenceType}</span>
              <span className={`rounded border px-1.5 py-0.5 ${DIR_STYLE[it.direction] ?? 'border-slate-700 text-slate-300'}`}>
                {it.direction.replace(/_/g, ' ')}
              </span>
              {sup.has(it.evidenceId) && <span className="text-emerald-400">counted: supports</span>}
              {con.has(it.evidenceId) && <span className="text-rose-400">counted: contradicts</span>}
            </div>
            <p className="text-slate-200">{it.description}</p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-[10px] text-slate-400">
              <span>Source: {it.source}</span>
              <span>Reliability: {pct(it.reliability)}</span>
              <span>Quality: {pct(it.quality)}</span>
              <span>Independence group: {it.independenceGroup}</span>
              <span>Weight: {it.weight.toFixed(2)}</span>
            </div>
            {it.limitations.length > 0 && <p className="text-amber-300/80">Limitations: {it.limitations.join(' · ')}</p>}
            {it.provenance && Object.keys(it.provenance).length > 0 && (
              <details className="text-[10px] font-mono text-slate-500">
                <summary className="cursor-pointer text-slate-400 flex items-center gap-1 w-fit">
                  <Link2 className="h-3 w-3" /> provenance
                </summary>
                <pre className="mt-1 overflow-x-auto whitespace-pre-wrap break-words text-slate-400">
                  {JSON.stringify(it.provenance, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
      </div>
    </section>
  );
};

// ---------------------------------------------------------------------------
// Convenience wrapper used by App
// ---------------------------------------------------------------------------
export const LiveEvidencePanels: React.FC<{ live: InvestigationResponse }> = ({ live }) => (
  <>
    <ImageTextEvidencePanel live={live} />
    <SourceReliabilityPanel live={live} />
    <EvidenceLedger live={live} />
  </>
);
