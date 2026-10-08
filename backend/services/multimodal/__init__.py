"""
TrustLens Phase 5 Multimodal AI Package.
"""
from backend.services.multimodal.analyzer import analyze_multimodal_image
from backend.services.multimodal.provider import (
    MultimodalProvider,
    MultimodalProviderError,
    get_multimodal_provider,
)
from backend.schemas.multimodal import MultimodalAiResult, AiGenerationAssessment

__all__ = [
    "analyze_multimodal_image",
    "get_multimodal_provider",
    "MultimodalProvider",
    "MultimodalProviderError",
    "MultimodalAiResult",
    "AiGenerationAssessment",
]
