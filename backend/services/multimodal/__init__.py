"""
TrustLens Phase 5 Multimodal AI Package.
"""
from services.multimodal.analyzer import analyze_multimodal_image
from services.multimodal.provider import (
    MultimodalProvider,
    MultimodalProviderError,
    get_multimodal_provider,
)
from schemas.multimodal import MultimodalAiResult, AiGenerationAssessment

__all__ = [
    "analyze_multimodal_image",
    "get_multimodal_provider",
    "MultimodalProvider",
    "MultimodalProviderError",
    "MultimodalAiResult",
    "AiGenerationAssessment",
]
