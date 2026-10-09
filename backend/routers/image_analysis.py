"""
Image Analysis Router for TrustLens Phase 4.

Exposes POST /api/analyze-image endpoint accepting multipart/form-data.
Performs safe decoding, Evidence Health evaluation, EXIF extraction,
deterministic computer vision measurements, and OCR text extraction.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from dependencies import check_rate_limit
from schemas.image_analysis import ImageAnalysisResponse
from services.image_analysis.analyzer import analyze_image_file
from services.image_analysis.decoder import ImageValidationError

from services.multimodal import analyze_multimodal_image

router = APIRouter(tags=["Image Analysis"])


@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    include_ai: bool = False,
    _rate_limit: None = Depends(check_rate_limit),
):
    """
    Phase 4/5 Image Analysis Endpoint.
    
    Accepts image file (JPEG, PNG, WEBP, max 10MB) via multipart/form-data.
    Computes real Evidence Health, EXIF metadata (with GPS privacy),
    deterministic Computer Vision metrics, perceptual hashes, and OCR text.
    Optionally executes Phase 5 Multimodal AI analysis if include_ai=True.
    """
    if not file or not file.filename:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "NO_FILE_UPLOADED", "message": "An image file is required.", "detail": "No file uploaded."},
        )

    try:
        # Read uploaded bytes
        file_bytes = await file.read()
        filename = file.filename
        content_type = file.content_type or ""

        analysis = analyze_image_file(file_bytes, filename, content_type)

        # Phase 5 Multimodal AI analysis if requested
        if include_ai:
            try:
                analysis.multimodal_ai = await analyze_multimodal_image(
                    image_bytes=file_bytes,
                    filename=filename,
                    mime_type=content_type,
                    image_analysis=analysis,
                )
            except Exception:
                pass

        return JSONResponse(content=analysis.model_dump(by_alias=True))

    except ImageValidationError as ive:
        return JSONResponse(
            status_code=ive.status_code,
            content={
                "error": ive.code,
                "message": ive.message,
                "detail": ive.message,
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "PROCESSING_ERROR",
                "message": f"An error occurred while analyzing the image: {str(exc)}",
                "detail": str(exc),
            },
        )
