"""
Conflict Detection Engine for TrustLens Phase 6.

Identifies explicit dialectical contradictions and cross-modality collisions between
supporting and contradicting evidence vectors. Prevents silent averaging of opposing signals.
Produces structured ConflictReport consumed by the decision layer to adjust final confidence.
"""
from typing import List, Set, Tuple
from schemas.fusion import (
    NormalizedEvidenceItem,
    EvidenceSummary,
    ConflictReport,
    ConflictDetail,
    ConflictSeverity,
)
from services.fusion.config import FusionConfig, DEFAULT_FUSION_CONFIG


def detect_evidence_conflicts(
    items: List[NormalizedEvidenceItem],
    summary: EvidenceSummary,
    config: FusionConfig = DEFAULT_FUSION_CONFIG,
) -> ConflictReport:
    """
    Detects directional and cross-modality contradictions across weighted evidence items.
    """
    scored = [it for it in items if config.image_text_affects_verdict or it.evidence_type != "IMAGE_TEXT"]
    sup_items = [it for it in scored if it.direction == "SUPPORTS" and it.weight > 0.04]
    contra_items = [it for it in scored if it.direction == "CONTRADICTS" and it.weight > 0.04]

    sup_strength = summary.supporting_strength
    contra_strength = summary.contradicting_strength

    # 1. Compute quantitative collision ratio (0.0 to 1.0)
    total_directed = sup_strength + contra_strength
    if total_directed <= 0.08 or not sup_items or not contra_items:
        collision_ratio = 0.0
    else:
        # Harmonic collision metric: 2 * min / (sup + contra)
        collision_ratio = (2.0 * min(sup_strength, contra_strength)) / total_directed

    details: List[ConflictDetail] = []
    conflicting_ids: Set[str] = set()

    # 2. Identify specific hypothesis collision dimensions
    # A. Authentic vs AI-Generated
    auth_items = [it for it in items if it.target_hypothesis == "AUTHENTIC" and it.weight > 0.04]
    ai_items = [it for it in items if it.target_hypothesis == "AI_GENERATED" and it.weight > 0.04]
    if auth_items and ai_items:
        involved = [it.evidence_id for it in auth_items] + [it.evidence_id for it in ai_items]
        conflicting_ids.update(involved)
        auth_desc = ", ".join(it.source for it in auth_items[:2])
        ai_desc = ", ".join(it.source for it in ai_items[:2])
        details.append(
            ConflictDetail(
                conflict_id="conf_auth_vs_ai",
                description=f"Evidence supporting authentic capture ({auth_desc}) conflicts with synthetic AI indicators ({ai_desc}).",
                conflicting_evidence_ids=involved,
                severity="HIGH" if collision_ratio >= 0.5 else "MEDIUM",
                dimension="AUTHENTIC_VS_SYNTHETIC",
            )
        )

    # B. Authentic vs Manipulated
    manip_items = [it for it in items if it.target_hypothesis == "MANIPULATED" and it.weight > 0.04]
    if auth_items and manip_items:
        involved = [it.evidence_id for it in auth_items] + [it.evidence_id for it in manip_items]
        conflicting_ids.update(involved)
        details.append(
            ConflictDetail(
                conflict_id="conf_auth_vs_manip",
                description="Evidence supporting media authenticity conflicts with forensic editing/manipulation signals.",
                conflicting_evidence_ids=involved,
                severity="HIGH" if collision_ratio >= 0.5 else "MEDIUM",
                dimension="AUTHENTIC_VS_MANIPULATED",
            )
        )

    # C. External Search Contradiction (Supporting Web vs Contradicting Web)
    web_sup = [it for it in sup_items if it.evidence_type == "WEB_SOURCE"]
    web_contra = [it for it in contra_items if it.evidence_type == "WEB_SOURCE"]
    if web_sup and web_contra:
        involved = [it.evidence_id for it in web_sup] + [it.evidence_id for it in web_contra]
        conflicting_ids.update(involved)
        details.append(
            ConflictDetail(
                conflict_id="conf_web_factual_collision",
                description=(
                    f"External candidate sources disagree: {len(web_sup)} source(s) corroborate the claim, "
                    f"while {len(web_contra)} source(s) challenge or contradict it."
                ),
                conflicting_evidence_ids=involved,
                severity="HIGH" if collision_ratio >= 0.5 else "MEDIUM",
                dimension="FACTUAL_CLAIM_COLLISION",
            )
        )

    # 3. Determine overall conflict severity
    if collision_ratio >= config.high_conflict_ratio:
        severity: ConflictSeverity = "HIGH"
    elif collision_ratio >= 0.35:
        severity = "MEDIUM"
    elif collision_ratio >= 0.10:
        severity = "LOW"
    else:
        severity = "NONE"

    conflict_detected = bool(severity != "NONE" or len(details) > 0)

    # 4. Formulate overall descriptive summary
    if severity == "HIGH":
        desc = (
            f"High evidence conflict detected ({int(collision_ratio * 100)}% collision ratio). "
            "Substantive evidence simultaneously supports and contradicts the hypothesis. Verdict confidence reduced."
        )
    elif severity == "MEDIUM":
        desc = (
            f"Moderate evidence tension observed ({int(collision_ratio * 100)}% collision ratio) across opposing sources. "
            "Evidence must be weighed with caution."
        )
    elif severity == "LOW":
        desc = "Minor localized discrepancy noted, but dominant evidentiary consensus remains intact."
    else:
        desc = "No conflicting or contradictory evidence detected across analyzed vectors."

    # If items are conflicting, record all opposing IDs
    if conflict_detected and not conflicting_ids:
        conflicting_ids.update([it.evidence_id for it in sup_items + contra_items])

    return ConflictReport(
        detected=conflict_detected,
        count=len(details),
        severity=severity,
        conflict_score=round(collision_ratio, 4),
        conflicting_evidence_ids=sorted(list(conflicting_ids)),
        description=desc,
        details=details,
    )
