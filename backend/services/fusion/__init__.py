"""
TrustLens Phase 6 Evidence Fusion Service.

Exposes the unified entrypoint for fusing evidence from Phase 4 Image Forensics,
Phase 5 Multimodal AI, Phase 3 Search Retrieval, and Phase 2 URL Security.
"""
from typing import Any, Optional
from backend.schemas.fusion import (
    FusionResult,
    NormalizedEvidenceItem,
    EvidenceSummary,
    ConflictReport,
    TrustTriangle,
)
from backend.schemas.image_analysis import ImageAnalysisResponse
from backend.schemas.investigation import (
    MultimodalAiResult,
    UrlAnalysisOutcome,
)
from backend.schemas.search import SearchEvidence

from backend.services.fusion.config import FusionConfig, DEFAULT_FUSION_CONFIG
from backend.services.fusion.normalizer import normalize_all_evidence
from backend.services.fusion.weighting import apply_reliability_weighting
from backend.services.fusion.conflict import detect_evidence_conflicts
from backend.services.fusion.engine import FusionEngine
from backend.services.fusion.explanation import (
    generate_deterministic_explanation,
    generate_verdict_explanation,
)


async def fuse_investigation_evidence(
    claim_text: str = "",
    url_text: str = "",
    url_outcome: Optional[UrlAnalysisOutcome] = None,
    image_analysis: Optional[ImageAnalysisResponse] = None,
    search_evidence: Optional[SearchEvidence] = None,
    multimodal_result: Optional[MultimodalAiResult] = None,
    image_text_evidence: Optional[Any] = None,
    config: FusionConfig = DEFAULT_FUSION_CONFIG,
) -> FusionResult:
    """
    Executes the complete deterministic Phase 6 Evidence Fusion Pipeline:
    1. Normalizes all inputs into common NormalizedEvidenceItem representation.
    2. Applies deterministic reliability weighting and source clustering de-duplication.
    3. Detects directional collisions and cross-modality contradictions.
    4. Computes deterministic verdict, confidence, and Trust Triangle scores.
    5. Optionally formats post-verdict explainable summary without changing computed decision.
    """
    # 1. Normalize
    normalized_items = normalize_all_evidence(
        claim_text=claim_text,
        url_text=url_text,
        url_outcome=url_outcome,
        image_analysis=image_analysis,
        search_evidence=search_evidence,
        multimodal_result=multimodal_result,
        image_text_evidence=image_text_evidence,
    )

    # 2. Weight and de-duplicate
    weighted_items, summary = apply_reliability_weighting(normalized_items, config=config)

    # 3. Detect conflicts
    conflict_report = detect_evidence_conflicts(weighted_items, summary, config=config)

    # 4. Deterministic fusion engine
    engine = FusionEngine(config=config)
    result = engine.fuse(weighted_items, summary, conflict_report, url_outcome=url_outcome)

    # 5. Explainable synthesis (LLM formatting grounded strictly on computed result, or fallback)
    explanation_text = await generate_verdict_explanation(result, claim_text=claim_text)
    if explanation_text:
        result.reason = explanation_text

    return result


__all__ = [
    "fuse_investigation_evidence",
    "FusionEngine",
    "FusionConfig",
    "DEFAULT_FUSION_CONFIG",
    "normalize_all_evidence",
    "apply_reliability_weighting",
    "detect_evidence_conflicts",
    "generate_deterministic_explanation",
    "generate_verdict_explanation",
]
