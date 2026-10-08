"""
Evidence Health Evaluation for TrustLens Phase 4.

EPISTEMIC RULE:
Evidence Health measures how suitable and complete a file is as forensic evidence.
"How much should TrustLens trust the forensic tests performed on this file?"

It is NOT merely "Is this file valid?", and it is NOT proof of authenticity:
- A high Evidence Health score does NOT mean the image is authentic.
- A low Evidence Health score does NOT mean the image is manipulated or fake.
- An unavailable test contributes ZERO evidence, NOT negative/suspicious evidence.

Conceptual Model:
File Health
├── integrity
├── resolution
├── compression
├── metadata
├── OCR
├── image quality
└── forensic reliability
"""
from typing import List
from backend.schemas.image_analysis import (
    FileMetadata,
    ExifMetadata,
    CompressionIndicators,
    ComputerVisionSignals,
    ElaResult,
    OcrResult,
    EvidenceHealth,
    ForensicTestAvailability,
    HealthStatus,
)


def calculate_evidence_health(
    file_meta: FileMetadata,
    exif_meta: ExifMetadata,
    compression: CompressionIndicators,
    cv_signals: ComputerVisionSignals,
    ela: ElaResult,
    ocr: OcrResult,
) -> EvidenceHealth:
    """
    Calculate explainable Evidence Health score, signals, and forensic test availability.
    """
    score = 0
    signals: List[str] = []
    notes: List[str] = []

    # 1. File Integrity & Decode Validity (Max 20 pts)
    if file_meta.is_valid and not file_meta.corruption_detected:
        score += 20
        signals.append(
            f"File integrity verified: Safe decode completed; SHA-256 computed ({file_meta.sha256[:12]}…)."
        )
    else:
        signals.append("File integrity warning: Decode encountered anomalies or truncation.")

    # 2. Resolution Adequacy (Max 25 pts)
    mp = file_meta.megapixels
    if mp >= 2.0:
        score += 25
        signals.append(f"High resolution ({mp} MP, {file_meta.width}x{file_meta.height}): Ample pixel density for forensic analysis.")
        res_adequate = True
    elif mp >= 0.9:
        score += 18
        signals.append(f"Standard HD resolution ({mp} MP, {file_meta.width}x{file_meta.height}): Adequate for visual inspection.")
        res_adequate = True
    elif mp >= 0.3:
        score += 10
        signals.append(f"Low resolution ({mp} MP): Fine pixel structures may be blurred by downsampling.")
        res_adequate = False
    else:
        score += 0
        signals.append(f"Very low resolution ({mp} MP): Substantial loss of forensic detail.")
        res_adequate = False

    # 3. Format & Compression Fidelity (Max 20 pts)
    fmt = file_meta.format.upper()
    if fmt == "PNG":
        score += 20
        signals.append("Lossless PNG container: Pixel values preserved without lossy DCT quantization artifacts.")
    elif fmt == "WEBP":
        score += 17
        signals.append("WEBP container: Modern compressed container with preserved luminance detail.")
    elif fmt == "JPEG":
        q = compression.estimated_jpeg_quality
        if q is not None and q >= 80:
            score += 20
            signals.append(f"High-quality JPEG (~{q}/100): Minimal lossy quantization noise.")
        elif q is not None and q >= 55:
            score += 14
            signals.append(f"Moderate JPEG (~{q}/100): Standard web compression with minor 8x8 block artifacts.")
        elif q is not None:
            score += 8
            signals.append(f"Low-quality JPEG (~{q}/100): Significant lossy quantization artifacts.")
        else:
            score += 14
            signals.append("Standard JPEG encoding.")
    else:
        score += 10
        signals.append(f"Standard {fmt} encoding.")

    # 4. Metadata Completeness (Max 15 pts)
    # Crucial Rule: Missing metadata contributes 0 evidence, never negative evidence.
    if exif_meta.metadata_status == "present":
        score += 15
        hw = f"{exif_meta.camera_make or ''} {exif_meta.camera_model or ''}".strip()
        signals.append(f"Hardware provenance present: {hw or 'Recorded in EXIF'}.")
    elif exif_meta.metadata_status == "partial":
        score += 8
        signals.append("Partial EXIF metadata present.")
    else:
        signals.append("EXIF metadata unavailable (neutral): Contributes zero forensic evidence (not suspicious).")

    # 5. Image Quality & Focus (Max 10 pts)
    if cv_signals.sharpness_assessment in ("high", "moderate"):
        score += 10
        signals.append(f"In-focus visual detail: {cv_signals.sharpness_assessment} (Laplacian variance {cv_signals.sharpness_score}).")
    else:
        score += 4
        signals.append(f"Low sharpness or optical motion blur observed ({cv_signals.sharpness_assessment}).")

    # 6. Forensic Test Usability (Max 10 pts)
    # Points awarded for successful execution of available forensic tests
    if ela.available and ela.status == "available":
        score += 5
        signals.append(f"Error Level Analysis computed: Baseline quality {ela.quality_factor_tested}, mean error {ela.mean_error}.")
    elif "non_jpeg" in ela.status:
        score += 5  # Lossless format doesn't need lossy ELA
        signals.append("Error Level Analysis: Not applicable for lossless non-JPEG format (neutral).")

    if ocr.available and ocr.status == "SUCCESS":
        score += 5
        signals.append(f"OCR executed: {ocr.regions_count} text region(s) identified with {ocr.ocr_quality.upper()} quality.")
    elif ocr.available and ocr.status == "NO_TEXT_DETECTED":
        score += 5
        signals.append("OCR executed: No text regions in image bounds.")
    else:
        signals.append("OCR engine unavailable on host (neutral): Text extraction skipped without penalty.")

    # Clamp score to [10, 95]
    final_score = max(10, min(95, score))

    # Health status tier
    if final_score >= 80:
        status: HealthStatus = "EXCELLENT"
    elif final_score >= 65:
        status: HealthStatus = "GOOD"
    elif final_score >= 50:
        status: HealthStatus = "FAIR"
    elif final_score >= 35:
        status: HealthStatus = "POOR"
    else:
        status: HealthStatus = "UNUSABLE"

    # Compile Forensic Test Availability Ledger
    test_availability = ForensicTestAvailability(
        file_integrity="available",
        resolution_check="available",
        exif_metadata="available" if exif_meta.available else "unavailable",
        compression_analysis="available" if compression.has_quantization_tables else ("not_applicable" if "non_jpeg" in compression.compression_status else "insufficient_evidence"),
        ela_analysis="available" if ela.available else ("not_applicable" if "non_jpeg" in ela.status else "unavailable"),
        perceptual_hashing="available" if (cv_signals.perceptual_hash_dhash and cv_signals.perceptual_hash_phash) else "unavailable",
        reference_comparison="unavailable",  # No comparison reference supplied
        ocr_extraction="available" if ocr.available else "unavailable",
        ai_deepfake_detector="unavailable",  # Honest: not implemented
        prnu_sensor_analysis="unavailable",  # Honest: not implemented
        optical_flow_analysis="unavailable",  # Honest: not implemented
    )

    notes.append(
        "File Health measures the technical suitability and reliability of the file for digital analysis. "
        "It answers: 'How much should TrustLens trust the forensic tests performed on this file?'"
    )
    notes.append(
        "File Health is NOT an authenticity verdict: a high-health image can still be fake, "
        "and an image with unavailable metadata is not inherently suspicious."
    )

    return EvidenceHealth(
        score=final_score,
        status=status,
        decode_successful=True,
        metadata_available=exif_meta.available,
        metadata_status=exif_meta.metadata_status,
        resolution_adequate=res_adequate,
        compression_indicators=compression,
        test_availability=test_availability,
        signals=signals,
        notes=notes,
    )
