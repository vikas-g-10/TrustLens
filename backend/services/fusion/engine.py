"""
Deterministic Evidence Fusion Engine for TrustLens Phase 6.

Synthesizes normalized evidence vectors, source independence clusters, and conflict
assessments into an explainable, deterministic final verdict and Trust Triangle.

EPISTEMIC GUARANTEES:
1. The LLM does NOT decide the verdict; verdict derivation is 100% deterministic code.
2. Missing EXIF metadata contributes ZERO negative evidence (never penalizes image).
3. Wire syndication and duplicates are discounted to avoid double-counting.
4. Confidence reflects evidence quality, coverage, independence, and conflict, never exceeding 95%.
5. When evidence is sparse or contradictory, verdict transparently remains INCONCLUSIVE.
"""
from typing import List, Optional, Tuple
from schemas.fusion import (
    NormalizedEvidenceItem,
    EvidenceSummary,
    ConflictReport,
    TrustTriangle,
    FusionResult,
    FinalVerdictType,
)
from schemas.investigation import UrlAnalysisOutcome
from services.fusion.config import FusionConfig, DEFAULT_FUSION_CONFIG


class FusionEngine:
    """Deterministic, explainable Evidence Fusion Engine."""

    def __init__(self, config: FusionConfig = DEFAULT_FUSION_CONFIG):
        self.config = config

    def fuse(
        self,
        items: List[NormalizedEvidenceItem],
        summary: EvidenceSummary,
        conflict: ConflictReport,
        url_outcome: Optional[UrlAnalysisOutcome] = None,
    ) -> FusionResult:
        """
        Executes deterministic evidence fusion.
        """
        # 1. Aggregate directed strength by target hypothesis
        strength_auth = sum(it.weight for it in items if it.target_hypothesis == "AUTHENTIC")
        strength_ai = sum(it.weight for it in items if it.target_hypothesis == "AI_GENERATED")
        strength_manip = sum(it.weight for it in items if it.target_hypothesis == "MANIPULATED")
        strength_claim_true = sum(it.weight for it in items if it.target_hypothesis == "CLAIM_TRUE")
        strength_claim_false = sum(it.weight for it in items if it.target_hypothesis == "CLAIM_FALSE")

        total_active_strength = summary.supporting_strength + summary.contradicting_strength

        # Authenticity needs *independent physical provenance* (camera EXIF). A vision model's
        # opinion or web articles about the user's claim cannot establish that an image is real.
        has_media = any(it.evidence_type in ("FILE_INTEGRITY", "MULTIMODAL_VISION", "VIDEO_METADATA", "VIDEO_FRAME") for it in items)
        strength_auth_physical = sum(
            it.weight for it in items
            if it.target_hypothesis == "AUTHENTIC" and it.independence_group == "exif_metadata"
        )

        # 2. Compute Trust Triangle Scores (0.0 to 100.0)
        # A. Evidence Strength: normalized against expected comprehensive baseline (2.0)
        norm_evidence_strength = min(100.0, (total_active_strength / 2.0) * 100.0)
        evidence_strength_score = round(norm_evidence_strength, 1)

        # B. Evidence Conflict: directly reflects conflict_score
        evidence_conflict_score = round(conflict.conflict_score * 100.0, 1)

        # C. Manipulation Likelihood: fraction of directed signals indicating synthetic or edited content
        adverse_weight = strength_ai + strength_manip + strength_claim_false
        favorable_weight = strength_auth + strength_claim_true
        directed_total = adverse_weight + favorable_weight

        if directed_total <= 0.05:
            manipulation_likelihood_score = 0.0
        else:
            manipulation_likelihood_score = round((adverse_weight / directed_total) * 100.0, 1)

        trust_triangle = TrustTriangle(
            manipulation_likelihood=manipulation_likelihood_score,
            evidence_strength=evidence_strength_score,
            evidence_conflict=evidence_conflict_score,
        )

        # Identify key supporting and contradicting evidence IDs for provenance
        supporting_ids = [it.evidence_id for it in items if it.direction == "SUPPORTS" and it.weight > 0.04]
        contradicting_ids = [it.evidence_id for it in items if it.direction == "CONTRADICTS" and it.weight > 0.04]

        # 3. Decision Logic: Deriving Final Verdict
        verdict: FinalVerdictType = "INCONCLUSIVE"
        confidence: int = 0
        reason: str = ""

        media_directed = strength_ai + strength_manip + strength_auth
        web_directed = strength_claim_true + strength_claim_false

        # Condition 1: Security Safeguard — Target URL blocked or failed inspection
        if url_outcome and not url_outcome.ok:
            verdict = "INCONCLUSIVE"
            reason = (
                f"Target URL inspection failed ({url_outcome.error.code}): {url_outcome.error.message}. "
                "Without access to the target host, claim remains inconclusive."
            )
            confidence = 0

        # Condition 2: Epistemic Safeguard — URL investigated without media forensics (Phase 2 Rule: page existence != proof of claim)
        elif url_outcome and media_directed < 0.20:
            verdict = "INCONCLUSIVE"
            reason = (
                "Target URL was inspected, but page retrieval alone does not constitute decisive proof of the claim. "
                "Factual verification requires independent multi-source corroboration."
            )
            confidence = min(self.config.inconclusive_confidence_cap, int(evidence_strength_score * 0.25))

        # Condition 3: Sparse Evidence or Insufficient Coverage
        elif (
            summary.evidence_coverage < self.config.min_evidence_coverage
            or total_active_strength < self.config.min_effective_strength
        ):
            verdict = "INCONCLUSIVE"
            reason = (
                "Insufficient diagnostic evidence available across analyzed vectors. "
                "TrustLens does not force a premature verdict on sparse telemetry."
            )
            confidence = min(
                self.config.inconclusive_confidence_cap,
                max(0, int(evidence_strength_score * 0.3)),
            )

        # Condition 4: High Conflict / Severe Contradiction
        elif conflict.severity == "HIGH":
            verdict = "INCONCLUSIVE"
            reason = (
                f"Conflicting evidence detected across independent modalities ({int(conflict.conflict_score * 100)}% collision). "
                "Material contradiction between opposing sources prevents conclusive determination."
            )
            confidence = min(
                self.config.inconclusive_confidence_cap,
                max(5, int(evidence_strength_score * (1.0 - conflict.conflict_score))),
            )

        # Condition 3: Sufficient Evidence with Tolerable Conflict
        else:
            media_directed = strength_ai + strength_manip + strength_auth
            web_directed = strength_claim_true + strength_claim_false

            if media_directed >= 0.20:
                # Media analysis is primary
                total_media = media_directed + 1e-6
                ai_share = strength_ai / total_media
                manip_share = strength_manip / total_media
                auth_share = strength_auth / total_media

                if strength_ai >= 0.30 and ai_share >= self.config.decision_dominance_ratio:
                    verdict = "LIKELY_AI_GENERATED"
                    reason = (
                        "Evidence predominantly demonstrates synthetic generative AI visual markers "
                        "and lacks authentic physical camera provenance."
                    )
                    confidence = self._compute_confidence(
                        lead_strength=strength_ai,
                        total_strength=total_active_strength,
                        summary=summary,
                        conflict=conflict,
                    )

                elif strength_manip >= 0.30 and manip_share >= self.config.decision_dominance_ratio:
                    verdict = "LIKELY_MANIPULATED"
                    reason = (
                        "Forensic telemetry and metadata indicators point to localized editing, "
                        "compositing, or software manipulation."
                    )
                    confidence = self._compute_confidence(
                        lead_strength=strength_manip,
                        total_strength=total_active_strength,
                        summary=summary,
                        conflict=conflict,
                    )

                elif strength_auth >= 0.30 and auth_share >= self.config.decision_dominance_ratio \
                        and strength_auth_physical <= 0.0:
                    verdict = "INCONCLUSIVE"
                    reason = (
                        "No AI-generation markers were found, but nothing independently confirms camera capture "
                        "(no hardware EXIF/provenance). Visual impressions alone cannot prove an image is real, "
                        "as modern AI images are often photorealistic."
                    )
                    confidence = min(self.config.inconclusive_confidence_cap, int(evidence_strength_score * 0.25))

                elif strength_auth >= 0.30 and auth_share >= self.config.decision_dominance_ratio:
                    verdict = "LIKELY_AUTHENTIC"
                    reason = (
                        "Evidence consistently aligns with authentic camera capture, "
                        "natural optical characteristics, and verifiable metadata integrity."
                    )
                    confidence = self._compute_confidence(
                        lead_strength=strength_auth,
                        total_strength=total_active_strength,
                        summary=summary,
                        conflict=conflict,
                    )

                else:
                    verdict = "INCONCLUSIVE"
                    reason = "Available forensic and multimodal evidence does not decisively establish a single dominant hypothesis."
                    confidence = min(self.config.inconclusive_confidence_cap, int(evidence_strength_score * 0.25))

            elif web_directed >= 0.20 and has_media:
                verdict = "INCONCLUSIVE"
                reason = (
                    "Web results about the claim cannot establish whether the uploaded image itself is genuine "
                    "or AI-generated; the media forensics were not decisive."
                )
                confidence = min(self.config.inconclusive_confidence_cap, int(evidence_strength_score * 0.25))

            elif web_directed >= 0.20:
                # Web search claim verification is primary
                total_web = web_directed + 1e-6
                true_share = strength_claim_true / total_web
                false_share = strength_claim_false / total_web

                if strength_claim_true >= 0.25 and true_share >= self.config.decision_dominance_ratio:
                    verdict = "LIKELY_AUTHENTIC"
                    reason = "Independent external reporting and verified sources predominantly corroborate the factual claim."
                    confidence = self._compute_confidence(
                        lead_strength=strength_claim_true,
                        total_strength=total_active_strength,
                        summary=summary,
                        conflict=conflict,
                    )

                elif strength_claim_false >= 0.25 and false_share >= self.config.decision_dominance_ratio:
                    verdict = "HIGH_RISK"
                    reason = "Credible fact-checking and official sources contradict or debunk the claimed assertion."
                    confidence = self._compute_confidence(
                        lead_strength=strength_claim_false,
                        total_strength=total_active_strength,
                        summary=summary,
                        conflict=conflict,
                    )

                else:
                    verdict = "INCONCLUSIVE"
                    reason = "External candidate search yielded ambiguous or mixed sources insufficient for confirmation."
                    confidence = min(self.config.inconclusive_confidence_cap, int(evidence_strength_score * 0.25))

            else:
                verdict = "INCONCLUSIVE"
                reason = "Diagnostic evidence across media and web sources is insufficient for confirmation."
                confidence = 0

        # Provenance attribution tailored to the derived verdict
        if verdict == "LIKELY_AI_GENERATED":
            supporting_ids = [it.evidence_id for it in items if it.target_hypothesis == "AI_GENERATED" and it.weight > 0.02]
            contradicting_ids = [it.evidence_id for it in items if it.target_hypothesis in ("AUTHENTIC", "CLAIM_TRUE") and it.weight > 0.02]
        elif verdict == "LIKELY_MANIPULATED":
            supporting_ids = [it.evidence_id for it in items if it.target_hypothesis == "MANIPULATED" and it.weight > 0.02]
            contradicting_ids = [it.evidence_id for it in items if it.target_hypothesis in ("AUTHENTIC", "CLAIM_TRUE") and it.weight > 0.02]
        elif verdict in ("LIKELY_AUTHENTIC", "LIKELY_GENUINE"):
            supporting_ids = [it.evidence_id for it in items if it.target_hypothesis in ("AUTHENTIC", "CLAIM_TRUE") and it.weight > 0.02]
            contradicting_ids = [it.evidence_id for it in items if it.target_hypothesis in ("AI_GENERATED", "MANIPULATED", "CLAIM_FALSE") and it.weight > 0.02]
        elif verdict == "HIGH_RISK":
            supporting_ids = [it.evidence_id for it in items if it.target_hypothesis in ("AI_GENERATED", "MANIPULATED", "CLAIM_FALSE") and it.weight > 0.02]
            contradicting_ids = [it.evidence_id for it in items if it.target_hypothesis in ("AUTHENTIC", "CLAIM_TRUE") and it.weight > 0.02]
        else:
            supporting_ids = [it.evidence_id for it in items if it.direction == "SUPPORTS" and it.weight > 0.04]
            contradicting_ids = [it.evidence_id for it in items if it.direction == "CONTRADICTS" and it.weight > 0.04]

        return FusionResult(
            verdict=verdict,
            confidence=confidence,
            reason=reason,
            trust_triangle=trust_triangle,
            evidence_summary=summary,
            conflict=conflict,
            supporting_evidence_ids=supporting_ids,
            contradicting_evidence_ids=contradicting_ids,
            normalized_evidence=items,
        )

    def _compute_confidence(
        self,
        lead_strength: float,
        total_strength: float,
        summary: EvidenceSummary,
        conflict: ConflictReport,
    ) -> int:
        """
        Computes calibrated confidence score (0-95).
        Enforces epistemic safeguards against false certainty.
        """
        dominance_ratio = lead_strength / (total_strength + 1e-6)
        expected_baseline = 0.70 if summary.independent_evidence_count <= 2 else 1.10
        strength_factor = min(1.0, total_strength / expected_baseline)
        independence_factor = min(1.0, summary.independent_evidence_count / 2.0) if summary.independent_evidence_count >= 1 else 0.5
        conflict_retention = max(0.2, 1.0 - (self.config.conflict_penalty_weight * conflict.conflict_score))

        # Baseline calculation
        score = self.config.confidence_scale_factor * dominance_ratio * strength_factor * (0.75 + 0.25 * independence_factor) * conflict_retention
        rounded = int(round(score))

        # Clamp between 25 and max_confidence_cap (95)
        return max(25, min(self.config.max_confidence_cap, rounded))
