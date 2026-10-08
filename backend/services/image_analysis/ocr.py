"""
Optical Character Recognition (OCR) Service for TrustLens Phase 4.

Uses pytesseract to extract textual content from uploaded images.
If Tesseract binary is not installed on the host environment, reports
transparent `status: 'UNAVAILABLE'` and `ocr_quality: 'unavailable'` without fabricating text.
"""
import os
import shutil
from typing import Optional
from PIL import Image

from backend.schemas.image_analysis import OcrResult, OcrStatus, OcrQuality


# Standard Windows installation candidates
TESSERACT_CANDIDATES = [
    os.environ.get("TESSERACT_CMD", ""),
    "tesseract",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]


def _resolve_tesseract_binary() -> Optional[str]:
    """Find executable tesseract binary on host or return None."""
    for path in TESSERACT_CANDIDATES:
        if not path:
            continue
        if os.path.isabs(path) and os.path.isfile(path):
            return path
        which_path = shutil.which(path)
        if which_path and os.path.isfile(which_path):
            return which_path
    return None


def extract_ocr_text(img: Image.Image) -> OcrResult:
    """
    Execute OCR text extraction.
    Returns structured OcrResult with text, confidence, quality rating, and region metrics.
    Never fabricates OCR text.
    """
    tesseract_binary = _resolve_tesseract_binary()
    if not tesseract_binary:
        return OcrResult(
            status="UNAVAILABLE",
            available=False,
            ocr_quality="unavailable",
            text="",
            confidence=None,
            regions_count=0,
            notes=[
                "Tesseract OCR engine is not installed on host PATH. Text extraction skipped.",
                "Install Tesseract OCR on the host system to enable automated visual text recognition.",
            ],
        )

    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = tesseract_binary

        # 1. Extract string text
        text_raw = pytesseract.image_to_string(img)
        clean_text = " ".join(text_raw.split()).strip()

        # 2. Extract detailed bounding data for confidence and region metrics
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        confidences = []
        regions = set()

        num_boxes = len(data.get("text", []))
        for i in range(num_boxes):
            word = str(data["text"][i]).strip()
            conf_str = data["conf"][i]
            try:
                conf_val = float(conf_str)
                if conf_val > 0 and word:
                    confidences.append(conf_val)
                    block_num = data.get("block_num", [0])[i]
                    par_num = data.get("par_num", [0])[i]
                    regions.add((block_num, par_num))
            except (ValueError, TypeError):
                continue

        avg_conf = round(sum(confidences) / len(confidences), 1) if confidences else None
        region_count = len(regions)

        if not clean_text:
            return OcrResult(
                status="NO_TEXT_DETECTED",
                available=True,
                ocr_quality="not_applicable",
                text="",
                confidence=None,
                regions_count=0,
                notes=["OCR executed successfully; no legible text regions were identified in the image."],
            )

        # Determine qualitative OCR quality based on measured character confidence
        if avg_conf is not None:
            if avg_conf >= 80.0:
                ocr_quality: OcrQuality = "high"
            elif avg_conf >= 50.0:
                ocr_quality = "moderate"
            else:
                ocr_quality = "low"
        else:
            ocr_quality = "moderate"

        notes = [
            f"Detected {len(confidences)} word token(s) across {region_count} region(s).",
            f"OCR quality rating: {ocr_quality.upper()}.",
            "OCR text represents visual evidence from the image and requires independent factual verification.",
        ]
        if avg_conf is not None:
            notes.append(f"Average optical character recognition confidence: {avg_conf}%.")

        return OcrResult(
            status="SUCCESS",
            available=True,
            ocr_quality=ocr_quality,
            text=clean_text,
            confidence=avg_conf,
            regions_count=region_count,
            notes=notes,
        )

    except Exception as exc:
        return OcrResult(
            status="UNAVAILABLE",
            available=False,
            ocr_quality="unavailable",
            text="",
            confidence=None,
            regions_count=0,
            notes=[f"OCR execution encountered an error: {str(exc)}"],
        )
