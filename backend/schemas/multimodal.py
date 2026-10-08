"""
Multimodal AI Schemas for TrustLens Phase 5.

Re-exports structured Pydantic models from backend.schemas.investigation.
Guarantees transparent epistemic assessment without hardcoded confidence or fake detectors.
"""
from backend.schemas.investigation import (
    AiGenerationAssessment,
    MultimodalAiResult,
)

__all__ = ["AiGenerationAssessment", "MultimodalAiResult"]
