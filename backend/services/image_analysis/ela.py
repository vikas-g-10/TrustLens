"""
Error Level Analysis (ELA) Service for TrustLens Phase 4.

Implements genuine, explainable Error Level Analysis:
1. Resaves the decoded image at a controlled JPEG quality factor (default 90).
2. Computes per-pixel absolute difference between original and resaved images.
3. Derives measurable statistics: mean error, max error, error variance, and high-error ratio.
4. Identifies format applicability: ELA is specific to lossy DCT compression (JPEG).
   Non-JPEG formats (PNG, WEBP) are reported transparently as not applicable.

EPISTEMIC GUARANTEE:
ELA is an explainable compression-differential indicator, NOT proof of manipulation.
Never converts ELA into a fabricated "manipulation probability".
"""
import io
from typing import Optional, List
import numpy as np
from PIL import Image

from schemas.image_analysis import ElaResult


def compute_error_level_analysis(
    img: Image.Image,
    img_format: str,
    jpeg_quality: int = 90,
) -> ElaResult:
    """
    Perform genuine Error Level Analysis on an image.

    Args:
        img: Decoded PIL Image.
        img_format: Detected format string (e.g. 'JPEG', 'PNG', 'WEBP').
        jpeg_quality: Resave quality factor for DCT difference baseline (default 90).

    Returns:
        ElaResult containing measurable statistics and structured notes.
    """
    clean_fmt = (img_format or img.format or "").upper()
    notes: List[str] = []

    # Format applicability check: ELA evaluates JPEG quantization grid behavior
    if clean_fmt != "JPEG":
        notes.append(
            f"Image format is {clean_fmt}. Error Level Analysis applies specifically to lossy JPEG DCT quantization."
        )
        notes.append(
            "Lossless containers (e.g. PNG) do not possess native JPEG 8x8 block quantization grids."
        )
        return ElaResult(
            status="not_applicable_non_jpeg",
            available=False,
            quality_factor_tested=None,
            mean_error=None,
            max_error=None,
            error_variance=None,
            high_error_ratio=None,
            notes=notes,
        )

    try:
        # 1. Normalize image to RGB for uniform channel differencing
        rgb_orig = img.convert("RGB")
        orig_arr = np.array(rgb_orig, dtype=np.float64)

        # 2. Resave to in-memory buffer at controlled JPEG quality factor
        buffer = io.BytesIO()
        rgb_orig.save(buffer, format="JPEG", quality=jpeg_quality)
        buffer.seek(0)

        # 3. Re-open resaved JPEG and extract pixel array
        resaved_img = Image.open(buffer)
        resaved_arr = np.array(resaved_img.convert("RGB"), dtype=np.float64)

        # 4. Compute absolute channel-wise pixel differences
        diff = np.abs(orig_arr - resaved_arr)

        # 5. Calculate genuine, explainable statistical indicators
        mean_err = round(float(np.mean(diff)), 2)
        max_err = round(float(np.max(diff)), 2)
        var_err = round(float(np.var(diff)), 2)

        # Ratio of pixels with noticeable error difference (> 15.0 on 0-255 scale)
        high_error_count = int(np.sum(diff > 15.0))
        high_error_ratio = round(float(high_error_count / diff.size), 4)

        notes.append(
            f"Measured error level differential against baseline JPEG quality {jpeg_quality}: "
            f"mean error = {mean_err}, max error = {max_err}, variance = {var_err}."
        )

        if high_error_ratio < 0.05:
            notes.append(
                f"Low error dispersion ({high_error_ratio * 100:.1f}% high-error pixels); uniform compression levels observed."
            )
        elif high_error_ratio < 0.20:
            notes.append(
                f"Moderate error dispersion ({high_error_ratio * 100:.1f}% high-error pixels); typical for complex scenes or high edge density."
            )
        else:
            notes.append(
                f"Elevated error dispersion ({high_error_ratio * 100:.1f}% high-error pixels); presents high-frequency contrast differentials."
            )

        notes.append(
            "ELA indicates pixel response to recompression. It is NOT proof of manipulation; edges naturally yield higher error levels."
        )

        return ElaResult(
            status="available",
            available=True,
            quality_factor_tested=jpeg_quality,
            mean_error=mean_err,
            max_error=max_err,
            error_variance=var_err,
            high_error_ratio=high_error_ratio,
            notes=notes,
        )

    except Exception as exc:
        return ElaResult(
            status="unavailable",
            available=False,
            quality_factor_tested=None,
            mean_error=None,
            max_error=None,
            error_variance=None,
            high_error_ratio=None,
            notes=[f"ELA calculation encountered an error: {str(exc)}"],
        )
