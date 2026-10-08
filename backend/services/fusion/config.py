"""
Configurable Weights and Thresholds for TrustLens Phase 6 Evidence Fusion.

All weights and thresholds are centralized here to avoid scattered magic numbers.
Values are deterministic and documented based on empirical evidentiary reliability.
"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class FusionConfig:
    """Configurable weights and operational thresholds for Evidence Fusion."""

    # Base modality weights (reflecting intrinsic diagnostic reliability)
    weight_file_integrity: float = 0.40
    weight_exif_camera_hardware: float = 0.75
    weight_exif_editing_software: float = 0.80
    weight_ela: float = 0.60
    weight_cv_metrics: float = 0.35
    weight_multimodal_vision: float = 0.85
    weight_url_security: float = 0.40
    weight_image_text: float = 0.30  # text inside an image: evidence about what it states, never proof
    # IMAGE_TEXT is recorded as a weighted evidence item, but does not yet drive the verdict or conflict score.
    image_text_affects_verdict: bool = False

    # Web source reliability scaling (multiplied by source reliability score 0.0-1.0)
    weight_web_high_tier: float = 0.85       # score >= 75 (Official / Established news)
    weight_web_medium_tier: float = 0.55     # 50 <= score < 75
    weight_web_unverified_tier: float = 0.25 # score < 50

    # Independence discount factors for repeated/syndicated sources in the same cluster
    discount_cluster_primary: float = 1.00     # First source in cluster
    discount_cluster_syndicated: float = 0.25  # Subsequent wire/syndicated sources
    discount_cluster_related: float = 0.40     # Subsequent same-domain sources
    discount_cluster_duplicate: float = 0.10   # Subsequent near-identical sources

    # Decision thresholds
    min_evidence_coverage: float = 0.20        # Coverage below this is INCONCLUSIVE
    min_effective_strength: float = 0.30       # Total active strength below this is INCONCLUSIVE
    high_conflict_ratio: float = 0.60          # Conflict above 60% forces INCONCLUSIVE
    decision_dominance_ratio: float = 0.65     # Leading hypothesis must represent >=65% of directed strength

    # Confidence scaling
    confidence_scale_factor: float = 90.0      # Scales normalized score to 0-90 baseline
    conflict_penalty_weight: float = 0.70      # Multiplier for reducing confidence on conflict
    max_confidence_cap: int = 95               # Epistemic ceiling: certainty is never 100%
    inconclusive_confidence_cap: int = 25      # Cap for inconclusive outcomes

    # Modality diagnostic weights for coverage calculation
    modality_diagnostic_slots: int = 4         # Media Forensics, Vision AI, Search Retrieval, URL Security


# Global singleton configuration instance
DEFAULT_FUSION_CONFIG = FusionConfig()
