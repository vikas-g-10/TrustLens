"""
Safe Image Decoder and File Validator for TrustLens Phase 4.

Enforces:
1. File size limits (default 10 MB) prior to processing.
2. Supported MIME and extension validation (JPEG, PNG, WEBP).
3. Decompression-bomb protection (MAX_IMAGE_PIXELS).
4. Safe two-stage PIL validation (verify headers + load pixels).
5. Untrusted input isolation: image content is data, never executable.
"""
import hashlib
import io
import os
from typing import Tuple
from PIL import Image, UnidentifiedImageError

from config import settings
from schemas.image_analysis import FileMetadata


# Supported format mappings
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/pjpeg",
    "image/png",
    "image/x-png",
    "image/webp",
}
SUPPORTED_PIL_FORMATS = {"JPEG", "PNG", "WEBP"}

# Safe decompression limit: 89,478,485 pixels (~89 Megapixels)
Image.MAX_IMAGE_PIXELS = 89_478_485


class ImageValidationError(Exception):
    """Raised when an uploaded file fails validation or safe decoding."""
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def validate_and_decode_image(
    file_bytes: bytes,
    filename: str,
    content_type: str = "",
) -> Tuple[Image.Image, FileMetadata]:
    """
    Safely validate and decode an uploaded image.
    
    Returns:
        (PIL.Image.Image, FileMetadata)
        
    Raises:
        ImageValidationError: On empty, oversized, unsupported, or corrupt files.
    """
    # 1. Check file size
    size_bytes = len(file_bytes)
    if size_bytes == 0:
        raise ImageValidationError("EMPTY_FILE", "The uploaded file is empty (0 bytes).", status_code=400)

    max_size = getattr(settings, "max_image_upload_size_bytes", 10 * 1024 * 1024)
    if size_bytes > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ImageValidationError(
            "FILE_TOO_LARGE",
            f"File size ({size_bytes / (1024 * 1024):.1f} MB) exceeds maximum allowed limit ({max_mb:.0f} MB).",
            status_code=413,
        )

    # 2. Check filename and extension
    clean_filename = os.path.basename(filename.strip()) if filename else "upload"
    _, ext = os.path.splitext(clean_filename.lower())
    if ext not in SUPPORTED_EXTENSIONS:
        raise ImageValidationError(
            "UNSUPPORTED_EXTENSION",
            f"File extension '{ext}' is not supported. Allowed formats: JPEG (.jpg, .jpeg), PNG (.png), WEBP (.webp).",
            status_code=415,
        )

    # 3. Check client MIME type if supplied
    clean_mime = content_type.lower().split(";")[0].strip() if content_type else ""
    if clean_mime and clean_mime not in SUPPORTED_MIME_TYPES and clean_mime != "application/octet-stream":
        raise ImageValidationError(
            "UNSUPPORTED_MIME_TYPE",
            f"MIME type '{clean_mime}' is not supported. Allowed types: image/jpeg, image/png, image/webp.",
            status_code=415,
        )

    # 4. Safe decode verification with Pillow
    try:
        # First pass: verify headers and integrity without loading full pixel array
        verify_stream = io.BytesIO(file_bytes)
        img_verify = Image.open(verify_stream)
        pil_format = (img_verify.format or "").upper()

        if pil_format not in SUPPORTED_PIL_FORMATS:
            raise ImageValidationError(
                "UNSUPPORTED_FORMAT",
                f"Decoded image format '{pil_format}' is not supported. Only JPEG, PNG, and WEBP are accepted.",
                status_code=415,
            )

        img_verify.verify()

    except ImageValidationError:
        raise
    except UnidentifiedImageError as uie:
        raise ImageValidationError(
            "INVALID_IMAGE_DATA",
            "The file could not be identified as a valid image. It may be corrupt or not an image.",
            status_code=400,
        ) from uie
    except Exception as exc:
        raise ImageValidationError(
            "CORRUPT_IMAGE",
            f"Failed to verify image headers: {str(exc)}",
            status_code=400,
        ) from exc

    # Second pass: fully load and render pixel data into memory
    try:
        decode_stream = io.BytesIO(file_bytes)
        img = Image.open(decode_stream)
        img.load()  # Force decode to detect truncated streams
    except Exception as exc:
        raise ImageValidationError(
            "CORRUPT_IMAGE_PAYLOAD",
            f"The image contains truncated or malformed pixel data: {str(exc)}",
            status_code=400,
        ) from exc

    width, height = img.size
    if width <= 0 or height <= 0:
        raise ImageValidationError(
            "INVALID_DIMENSIONS",
            "Image has invalid zero or negative dimensions.",
            status_code=400,
        )

    # Calculate Aspect Ratio and Megapixels
    from math import gcd
    div = gcd(width, height)
    aspect_ratio = f"{width // div}:{height // div}" if div > 0 else f"{width}:{height}"
    # Standard common ratio naming if applicable
    ratio_float = width / height
    if abs(ratio_float - 16 / 9) < 0.05:
        aspect_ratio = "16:9"
    elif abs(ratio_float - 4 / 3) < 0.05:
        aspect_ratio = "4:3"
    elif abs(ratio_float - 1.0) < 0.01:
        aspect_ratio = "1:1"
    elif abs(ratio_float - 3 / 2) < 0.05:
        aspect_ratio = "3:2"

    megapixels = round((width * height) / 1_000_000, 2)

    actual_mime = "image/jpeg" if pil_format == "JPEG" else ("image/png" if pil_format == "PNG" else "image/webp")

    # Calculate real cryptographic hash of uploaded bytes
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    file_metadata = FileMetadata(
        filename=clean_filename,
        format=pil_format,
        size_bytes=size_bytes,
        sha256=sha256_hash,
        width=width,
        height=height,
        aspect_ratio=aspect_ratio,
        megapixels=megapixels,
        image_mode=img.mode,
        mime_type=actual_mime,
        is_valid=True,
        corruption_detected=False,
    )

    return img, file_metadata
