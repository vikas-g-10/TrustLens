"""
Multimodal AI Schemas for TrustLens Phase 5.

Re-exports structured Pydantic models from schemas.investigation.
Guarantees transparent epistemic assessment without hardcoded confidence or fake detectors.
"""
from schemas.investigation import (
    AiGenerationAssessment,
    MultimodalAiResult,
)

__all__ = ["AiGenerationAssessment", "MultimodalAiResult"]
