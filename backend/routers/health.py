from fastapi import APIRouter
from config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint reporting AIML subsystem status."""
    return {
        "ok": True,
        "groqConfigured": bool(settings.groq_api_key),
        "model": settings.groq_model,
        "engine": "TrustLens FastAPI AIML Architecture",
        "version": settings.app_version,
        "phase": "Phase 9 (AIML prototype)"
    }
