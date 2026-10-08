"""
Measurable Compression and Quantization Analysis for TrustLens Phase 4.

Inspects actual DCT quantization tables for JPEG images.
Never fabricates recompression scores or fake manipulation probabilities.
"""
from typing import Optional
from PIL import Image

from backend.schemas.image_analysis import CompressionIndicators


# Standard Independent JPEG Group (IJG) Reference Luminance Quantization Table
IJG_STANDARD_LUMINANCE = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99
]


def estimate_jpeg_quality_from_quantization(q_table: list) -> Optional[int]:
    """
    Estimate standard IJG quality factor (1-100) from measured luminance quantization table.
    Uses inverse IJG scaling calculation.
    """
    if not q_table or len(q_table) < 64:
        return None

    ref_table = IJG_STANDARD_LUMINANCE
    diffs = []
    for i in range(min(len(q_table), 64)):
        val = q_table[i]
        ref = ref_table[i]
        if ref > 0:
            diffs.append(val / ref)

    if not diffs:
        return None

    avg_scale = sum(diffs) / len(diffs)
    # IJG scaling formula inversion:
    # If S <= 1.0 (quality >= 50): quality = 100 - (S * 50)
    # If S > 1.0 (quality < 50): quality = 50 / S
    if avg_scale <= 1.0:
        quality = 100 - (avg_scale * 50)
    else:
        quality = 50.0 / avg_scale

    return max(1, min(100, int(round(quality))))


def analyze_compression(img: Image.Image, img_format: str) -> CompressionIndicators:
    """
    Analyze compression characteristics and quantization matrices.
    """
    notes = []
    img_fmt = (img_format or img.format or "").upper()

    if img_fmt != "JPEG":
        notes.append(f"Format is {img_fmt}; quantization table analysis applies only to DCT JPEG files.")
        notes.append("Lossless formats (PNG) preserve original pixel values without lossy DCT quantization.")
        return CompressionIndicators(
            has_quantization_tables=False,
            estimated_jpeg_quality=None,
            compression_status="not_applicable_non_jpeg",
            notes=notes,
        )

    # Check for JPEG quantization tables in Pillow
    q_dict = getattr(img, "quantization", None)
    if not q_dict:
        notes.append("JPEG quantization tables could not be extracted directly from stream.")
        notes.append("Compression characteristics remain unmeasured; this is not proof of tampering.")
        return CompressionIndicators(
            has_quantization_tables=False,
            estimated_jpeg_quality=None,
            compression_status="insufficient_evidence",
            notes=notes,
        )

    # Extract luminance table (index 0)
    luminance_table = q_dict.get(0)
    if not luminance_table:
        # Fallback to first available table
        luminance_table = next(iter(q_dict.values()), None)

    if not luminance_table:
        return CompressionIndicators(
            has_quantization_tables=False,
            estimated_jpeg_quality=None,
            compression_status="insufficient_evidence",
            notes=["No valid quantization matrix found in JPEG stream."],
        )

    # Table might be a list or array
    table_list = list(luminance_table)
    est_quality = estimate_jpeg_quality_from_quantization(table_list)

    notes.append(f"JPEG quantization matrix detected ({len(q_dict)} table(s)).")
    if est_quality is not None:
        notes.append(f"Estimated JPEG compression quality factor: ~{est_quality}/100.")
        if est_quality < 65:
            notes.append("Moderate to high lossy compression detected; fine textures may exhibit blocking artifacts.")
        else:
            notes.append("High JPEG encoding quality; fine detail and edges are well-preserved.")
    notes.append("JPEG compression is a technical transmission property; re-saving an image does NOT prove manipulation.")

    return CompressionIndicators(
        has_quantization_tables=True,
        estimated_jpeg_quality=est_quality,
        compression_status="measured",
        notes=notes,
    )


# Public helper alias
inspect_jpeg_compression = analyze_compression

