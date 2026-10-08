"""
Multimodal AI Analyzer for TrustLens Phase 5.

Coordinates image preprocessing, prompt construction, LLM provider invocation,
strict Pydantic output validation, and epistemic error handling.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from backend.schemas.multimodal import AiGenerationAssessment, MultimodalAiResult
from backend.services.multimodal.image_utils import prepare_image_for_multimodal
from backend.services.multimodal.prompt import build_multimodal_prompt
from backend.services.multimodal.provider import (
    MultimodalProvider,
    MultimodalProviderError,
    get_multimodal_provider,
)

logger = logging.getLogger("trustlens.multimodal.analyzer")

VALID_ASSESSMENTS: set = {
    "likely_ai_generated",
    "likely_authentic",
    "possibly_manipulated",
    "inconclusive",
}


def _normalize_assessment(raw_value: Any) -> AiGenerationAssessment:
    """Normalizes raw string to a valid AiGenerationAssessment enum value."""
    if not raw_value or not isinstance(raw_value, str):
        return "inconclusive"

    cleaned = raw_value.strip().lower().replace("-", "_").replace(" ", "_")
    if cleaned in VALID_ASSESSMENTS:
        return cleaned  # type: ignore

    # Fallback keyword matching if model gave minor variance
    if "ai_gen" in cleaned or "synthetic" in cleaned or "deepfake" in cleaned:
        return "likely_ai_generated"
    if "authentic" in cleaned or "genuine" in cleaned or "real" in cleaned:
        return "likely_authentic"
    if "manipulat" in cleaned or "tamper" in cleaned or "edited" in cleaned:
        return "possibly_manipulated"

    return "inconclusive"


def _normalize_confidence(raw_conf: Any) -> float:
    """
    Normalizes confidence to a float between 0.0 and 1.0.
    Accepts floats in [0.0, 1.0] or percentages in [0, 100].
    Never invents or hardcodes a default confidence score.
    """
    if raw_conf is None:
        return 0.0
    try:
        val = float(raw_conf)
        if val > 1.0:
            val = val / 100.0
        return max(0.0, min(1.0, round(val, 4)))
    except (ValueError, TypeError):
        return 0.0


def _ensure_string_list(raw_list: Any) -> List[str]:
    """Ensures input is a clean list of non-empty strings."""
    if not raw_list:
        return []
    if isinstance(raw_list, str):
        return [raw_list.strip()] if raw_list.strip() else []
    if isinstance(raw_list, list):
        out = []
        for item in raw_list:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif isinstance(item, dict):
                # If model returned list of dicts with explanation/point
                desc = item.get("point") or item.get("description") or item.get("finding") or str(item)
                if desc.strip():
                    out.append(desc.strip())
        return out
    return []


async def analyze_multimodal_image(
    image_bytes: bytes,
    filename: str,
    mime_type: str = "image/jpeg",
    claim_text: Optional[str] = None,
    image_analysis: Optional[Any] = None,
    search_evidence: Optional[Any] = None,
    provider: Optional[MultimodalProvider] = None,
) -> MultimodalAiResult:
    """
    Executes Phase 5 Multimodal AI visual analysis over the uploaded image.

    Inputs:
    - image_bytes: Raw uploaded file bytes (JPEG, PNG, WEBP)
    - filename: Original upload filename
    - mime_type: Declared content type
    - claim_text: Associated user proposition
    - image_analysis: Phase 4 ImageAnalysisResponse with File Health, EXIF, ELA, CV, OCR
    - search_evidence: Phase 3 retrieved external candidates (supporting & counter)
    - provider: Optional injected MultimodalProvider instance (for testing or overrides)

    Returns:
        Structured Pydantic MultimodalAiResult guaranteed not to raise unhandled exceptions.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    active_provider = provider or get_multimodal_provider()

    # Step 1: Prepare and optimize image for multimodal model
    try:
        data_url, prepared_mime, (w, h) = prepare_image_for_multimodal(
            image_bytes=image_bytes,
            filename=filename,
            mime_type=mime_type,
        )
    except Exception as prep_exc:
        logger.warning(f"Failed to prepare image for multimodal model: {prep_exc}")
        return MultimodalAiResult(
            ai_generation_assessment="inconclusive",
            confidence=0.0,
            visual_findings=[],
            supporting_signals=[],
            contradicting_signals=[],
            limitations=[
                f"Image could not be prepared for multimodal inspection: {str(prep_exc)}"
            ],
            explanation=(
                "Visual inspection could not be performed due to image decoding or format limitations. "
                "Forensic evaluation relies on deterministic Phase 4 metrics."
            ),
            model_used=active_provider.model_name,
            provider_used=active_provider.provider_name,
            analyzed_at=now_iso,
        )

    # Step 2: Formulate evidence-aware prompt
    prompt = build_multimodal_prompt(
        filename=filename,
        claim_text=claim_text,
        image_analysis=image_analysis,
        search_evidence=search_evidence,
    )

    # Step 3: Invoke Multimodal Provider
    try:
        raw_output = await active_provider.analyze_image(
            image_data_url=data_url,
            prompt=prompt,
        )

        assessment = _normalize_assessment(raw_output.get("ai_generation_assessment"))
        confidence = _normalize_confidence(raw_output.get("confidence"))
        visual_findings = _ensure_string_list(raw_output.get("visual_findings"))
        supporting = _ensure_string_list(raw_output.get("supporting_signals"))
        contradicting = _ensure_string_list(raw_output.get("contradicting_signals"))
        limitations = _ensure_string_list(raw_output.get("limitations"))
        explanation = str(raw_output.get("explanation", "")).strip()

        # Epistemic safeguard: add standard boundaries if not already noted
        boundary_note = "Visual inspection alone cannot definitively prove synthetic generation; metadata and provenance remain critical."
        if not any("alone cannot" in lim.lower() for lim in limitations):
            limitations.append(boundary_note)

        return MultimodalAiResult(
            ai_generation_assessment=assessment,
            confidence=confidence,
            visual_findings=visual_findings,
            supporting_signals=supporting,
            contradicting_signals=contradicting,
            limitations=limitations,
            explanation=explanation,
            model_used=active_provider.model_name,
            provider_used=active_provider.provider_name,
            analyzed_at=now_iso,
        )

    except MultimodalProviderError as mpe:
        logger.warning(f"Multimodal inference error: {mpe.message}")
        return MultimodalAiResult(
            ai_generation_assessment="inconclusive",
            confidence=0.0,
            visual_findings=[],
            supporting_signals=[],
            contradicting_signals=[],
            limitations=[
                f"Multimodal AI inspection unavailable: {mpe.message}",
                "Absence of multimodal AI assessment does not indicate manipulation or authenticity.",
            ],
            explanation=(
                f"Multimodal visual inspection was not available ({mpe.message}). "
                "The investigation remains inconclusive regarding synthetic origin and relies on Phase 4 technical forensics."
            ),
            model_used=active_provider.model_name,
            provider_used=active_provider.provider_name,
            analyzed_at=now_iso,
        )
    except Exception as exc:
        logger.error(f"Unexpected error during multimodal analysis: {exc}", exc_info=True)
        return MultimodalAiResult(
            ai_generation_assessment="inconclusive",
            confidence=0.0,
            visual_findings=[],
            supporting_signals=[],
            contradicting_signals=[],
            limitations=[
                f"Unexpected multimodal processing error: {str(exc)}",
            ],
            explanation=(
                "An unexpected processing error prevented multimodal visual assessment. "
                "Investigation proceeds with Phase 4 file forensics."
            ),
            model_used=active_provider.model_name,
            provider_used=active_provider.provider_name,
            analyzed_at=now_iso,
        )
