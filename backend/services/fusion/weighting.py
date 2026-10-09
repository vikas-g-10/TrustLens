"""
Reliability Weighting & Source Independence Engine for TrustLens Phase 6.

Calculates deterministic, transparent evidentiary weights for normalized evidence items.
Enforces strict source clustering discounts to eliminate wire syndication and duplicate skew.

Weighting Formulation:
  item.weight = base_weight(modality)
                * item.reliability
                * item.quality
                * independence_discount(cluster)
                * confidence_factor(origin)
"""
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from schemas.fusion import NormalizedEvidenceItem, EvidenceSummary
from services.fusion.config import FusionConfig, DEFAULT_FUSION_CONFIG


def apply_reliability_weighting(
    items: List[NormalizedEvidenceItem],
    config: FusionConfig = DEFAULT_FUSION_CONFIG,
) -> Tuple[List[NormalizedEvidenceItem], EvidenceSummary]:
    """
    Applies deterministic reliability weighting and source independence de-duplication.

    Returns:
        (updated_items_with_computed_weights, evidence_summary)
    """
    if not items:
        return [], EvidenceSummary()

    # 1. Group items by independence_group to prevent double-counting
    cluster_groups: Dict[str, List[NormalizedEvidenceItem]] = defaultdict(list)
    for it in items:
        cluster_groups[it.independence_group].append(it)

    weighted_items: List[NormalizedEvidenceItem] = []
    active_clusters_with_signal: Set[str] = set()

    for group_id, group_items in cluster_groups.items():
        # Sort by reliability descending so primary witness gets full weight
        sorted_group = sorted(group_items, key=lambda x: (x.reliability, x.quality), reverse=True)

        for index, item in enumerate(sorted_group):
            # Missing EXIF, failed tests, or neutral context strictly get 0.0 weight
            if (item.direction in ("NEUTRAL", "UNRELATED", "INSUFFICIENT_TEXT")
                    or item.reliability <= 0.0 or item.quality <= 0.0):
                item.weight = 0.0
                weighted_items.append(item)
                continue

            # Determine base modality weight
            if item.evidence_type == "FILE_INTEGRITY":
                base_w = config.weight_file_integrity
            elif item.evidence_type == "METADATA_EXIF":
                if item.target_hypothesis == "MANIPULATED":
                    base_w = config.weight_exif_editing_software
                elif item.target_hypothesis == "AUTHENTIC":
                    base_w = config.weight_exif_camera_hardware
                else:
                    base_w = 0.30
            elif item.evidence_type == "IMAGE_ELA":
                base_w = config.weight_ela
            elif item.evidence_type == "PERCEPTUAL_HASH":
                base_w = config.weight_cv_metrics
            elif item.evidence_type == "MULTIMODAL_VISION":
                base_w = config.weight_multimodal_vision
            elif item.evidence_type == "WEB_SOURCE":
                if item.reliability >= 0.75:
                    base_w = config.weight_web_high_tier
                elif item.reliability >= 0.50:
                    base_w = config.weight_web_medium_tier
                else:
                    base_w = config.weight_web_unverified_tier
            elif item.evidence_type == "URL_SECURITY":
                base_w = config.weight_url_security
            elif item.evidence_type == "IMAGE_TEXT":
                base_w = config.weight_image_text
            else:
                base_w = 0.30

            # Calculate independence discount
            if index == 0:
                # Primary item in cluster
                ind_discount = config.discount_cluster_primary
            else:
                # De-duplicate subsequent items from same cluster / wire service
                ind_level = item.provenance.get("independence_level", "")
                if ind_level == "DUPLICATE":
                    ind_discount = config.discount_cluster_duplicate
                elif ind_level == "SYNDICATED":
                    ind_discount = config.discount_cluster_syndicated
                elif ind_level == "RELATED":
                    ind_discount = config.discount_cluster_related
                else:
                    ind_discount = config.discount_cluster_syndicated

            # Confidence factor (from originating detector, if provided)
            conf_factor = item.confidence if (item.confidence is not None and item.confidence > 0.0) else 1.0

            # Deterministic multiplicative weight
            calculated_weight = base_w * item.reliability * item.quality * ind_discount * conf_factor
            if item.direction == "PARTIALLY_SUPPORTS":
                calculated_weight *= 0.5  # partial agreement counts for half
            item.weight = round(max(0.0, calculated_weight), 4)

            if item.weight > 0.04:
                active_clusters_with_signal.add(group_id)

            weighted_items.append(item)

    # 2. Formulate EvidenceSummary
    # IMAGE_TEXT is kept out of verdict-driving strengths unless explicitly enabled in config.
    counted = [it for it in weighted_items if config.image_text_affects_verdict or it.evidence_type != "IMAGE_TEXT"]
    sup_strength = sum(it.weight for it in counted if it.direction in ("SUPPORTS", "PARTIALLY_SUPPORTS"))
    contra_strength = sum(it.weight for it in counted if it.direction == "CONTRADICTS")

    sup_count = sum(1 for it in weighted_items if it.direction == "SUPPORTS")
    contra_count = sum(1 for it in weighted_items if it.direction == "CONTRADICTS")
    neutral_count = sum(1 for it in weighted_items if it.direction in ("NEUTRAL", "UNRELATED", "INSUFFICIENT_TEXT"))

    # Diagnostic coverage: check active presence across 4 core modalities
    active_modalities: Set[str] = set()
    for it in weighted_items:
        if it.weight > 0.02:
            if it.evidence_type in ("FILE_INTEGRITY", "METADATA_EXIF", "IMAGE_ELA", "PERCEPTUAL_HASH"):
                active_modalities.add("media_forensics")
            elif it.evidence_type == "MULTIMODAL_VISION":
                active_modalities.add("multimodal_ai")
            elif it.evidence_type == "WEB_SOURCE":
                active_modalities.add("web_search")
            elif it.evidence_type == "URL_SECURITY":
                active_modalities.add("url_security")

    coverage = len(active_modalities) / float(config.modality_diagnostic_slots)

    summary = EvidenceSummary(
        supporting_strength=round(sup_strength, 4),
        contradicting_strength=round(contra_strength, 4),
        independent_evidence_count=len(active_clusters_with_signal),
        evidence_coverage=round(coverage, 2),
        total_evidence_count=len(weighted_items),
        supporting_count=sup_count,
        contradicting_count=contra_count,
        neutral_count=neutral_count,
    )

    return weighted_items, summary
