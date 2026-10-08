"""
Image utilities for Phase 5 Multimodal AI analysis.

Safely handles decoding, format normalization, size optimization,
and base64 data URL formatting for multimodal vision model APIs.
"""
import base64
import io
from typing import Tuple
from PIL import Image, ImageOps


MAX_VISION_DIMENSION = 768
MAX_PAYLOAD_BYTES = 2 * 1024 * 1024  # 2 MB threshold for base64 encoding


def prepare_image_for_multimodal(
    image_bytes: bytes,
    filename: str,
    mime_type: str = "image/jpeg",
) -> Tuple[str, str, Tuple[int, int]]:
    """
    Prepares uploaded image bytes for multimodal LLM vision consumption.

    - Validates image decodability.
    - Handles EXIF orientation so the vision model sees the canonical image.
    - Proportionally scales down dimensions exceeding MAX_VISION_DIMENSION (1536px)
      to avoid exceeding vision token/payload limits while preserving fine details.
    - Formats as a clean data URL string: data:{mime_type};base64,{b64}

    Returns:
        Tuple of (data_url, output_mime_type, (width, height))
    """
    if not image_bytes or len(image_bytes) == 0:
        raise ValueError("Empty image payload provided for multimodal analysis.")

    try:
        with Image.open(io.BytesIO(image_bytes)) as pil_img:
            # Handle orientation if present
            try:
                pil_img = ImageOps.exif_transpose(pil_img)
            except Exception:
                pass

            # Determine appropriate mode
            if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
                # Preserve PNG transparency
                target_format = "PNG"
                target_mime = "image/png"
            else:
                target_format = "JPEG"
                target_mime = "image/jpeg"
                if pil_img.mode != "RGB":
                    pil_img = pil_img.convert("RGB")

            orig_width, orig_height = pil_img.size
            cur_width, cur_height = orig_width, orig_height

            # Downsample if dimensions are excessively large
            needs_resize = max(cur_width, cur_height) > MAX_VISION_DIMENSION
            if needs_resize:
                pil_img.thumbnail((MAX_VISION_DIMENSION, MAX_VISION_DIMENSION), Image.Resampling.LANCZOS)
                cur_width, cur_height = pil_img.size

            # Encode to in-memory buffer
            out_buf = io.BytesIO()
            if target_format == "JPEG":
                pil_img.save(out_buf, format="JPEG", quality=90, optimize=True)
            else:
                pil_img.save(out_buf, format="PNG", optimize=True)

            out_bytes = out_buf.getvalue()

            # If still over threshold, compress to JPEG Q80
            if len(out_bytes) > MAX_PAYLOAD_BYTES:
                if pil_img.mode != "RGB":
                    pil_img = pil_img.convert("RGB")
                out_buf = io.BytesIO()
                pil_img.save(out_buf, format="JPEG", quality=80, optimize=True)
                out_bytes = out_buf.getvalue()
                target_mime = "image/jpeg"

            b64_str = base64.b64encode(out_bytes).decode("ascii")
            data_url = f"data:{target_mime};base64,{b64_str}"
            return data_url, target_mime, (cur_width, cur_height)

    except Exception as exc:
        raise ValueError(f"Failed to prepare image for multimodal model: {str(exc)}") from exc
