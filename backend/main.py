from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import settings
from backend.routers import health, investigate, image_analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup diagnostics
    print(f"[trustlens-backend] Starting {settings.app_name} ({settings.app_version})")
    print(f"[trustlens-backend] Groq Configured: {bool(settings.groq_api_key)}")
    print(f"[trustlens-backend] Model: {settings.groq_model}")
    print(f"[trustlens-backend] Listening on http://{settings.host}:{settings.port}")
    yield
    print(f"[trustlens-backend] Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="TrustLens Evidence-Driven Digital Investigation Engine REST API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(investigate.router, prefix=settings.api_prefix)
app.include_router(image_analysis.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "documentation": "/docs",
        "health": f"{settings.api_prefix}/health",
        "investigate": f"{settings.api_prefix}/investigate",
        "analyze_image": f"{settings.api_prefix}/analyze-image",
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.host, port=settings.port, reload=True)
