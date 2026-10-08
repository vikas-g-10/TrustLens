from fastapi import APIRouter
from backend.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint matching Express contract and reporting AIML subsystem status."""
    return {
        "ok": True,
        "groqConfigured": bool(settings.groq_api_key),
        "model": settings.groq_model,
        "engine": "TrustLens FastAPI AIML Architecture",
        "version": settings.app_version,
        "phase": "Phase 1 Foundation"
    }
