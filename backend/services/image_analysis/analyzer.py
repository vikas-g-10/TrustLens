"""
Primary Image Analysis Orchestrator for TrustLens Phase 4.

Orchestrates safe decoding, SHA-256 calculation, EXIF metadata extraction,
compression analysis, CV signals, perceptual hashing, ELA, OCR, Evidence Health,
and structured evidence assembly.
"""
from datetime import datetime, timezone
from typing import List

from backend.schemas.image_analysis import (
    ImageAnalysisResponse,
    ImageEvidenceItem,
)
from backend.services.image_analysis.decoder import validate_and_decode_image
from backend.services.image_analysis.metadata import extract_exif_metadata
from backend.services.image_analysis.compression import analyze_compression
from backend.services.image_analysis.ela import compute_error_level_analysis
from backend.services.image_analysis.computer_vision import extract_computer_vision_signals
from backend.services.image_analysis.ocr import extract_ocr_text
from backend.services.image_analysis.evidence_health import calculate_evidence_health
from backend.services.image_analysis.provenance import scan_ai_provenance


def analyze_image_file(
    file_bytes: bytes,
    filename: str,
    content_type: str = "",
) -> ImageAnalysisResponse:
    """
    Execute complete Phase 4 image investigation pipeline on uploaded bytes.
    
    Returns:
        ImageAnalysisResponse
        
    Raises:
        ImageValidationError: If file fails size, format, or decode validation.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Safe Image Decode, SHA-256 Calculation, and File Metadata
    img, file_meta = validate_and_decode_image(file_bytes, filename, content_type)

    # 2. EXIF and Hardware Metadata Extraction (Privacy-Safe & Neutral)
    exif_meta = extract_exif_metadata(img)

    # 3. Compression and Quantization Analysis
    compression = analyze_compression(img, file_meta.format)

    # 4. Error Level Analysis (ELA)
    ela_result = compute_error_level_analysis(img, file_meta.format)

    # 5. Computer Vision Signals and Perceptual Hashing (dHash & pHash)
    cv_signals = extract_computer_vision_signals(img)

    # 6. OCR Text Extraction and Transparent Quality Assessment
    ocr_result = extract_ocr_text(img)

    # 6b. Explicit AI-generation provenance markers (C2PA / IPTC / PNG params)
    provenance = scan_ai_provenance(img, file_bytes)

    # 7. Evidence Health Evaluation (File Health & Forensic Reliability)
    evidence_health = calculate_evidence_health(
        file_meta,
        exif_meta,
        compression,
        cv_signals,
        ela_result,
        ocr_result,
    )

    # 8. Assemble Discrete Evidence Items
    evidence_items: List[ImageEvidenceItem] = []

    # File integrity evidence
    evidence_items.append(
        ImageEvidenceItem(
            evidence_type="file_integrity",
            observation=f"SHA-256 fingerprint: {file_meta.sha256} ({file_meta.size_bytes} bytes).",
            reliability_tier="TECHNICAL_OBSERVATION",
        )
    )

    # Resolution evidence
    evidence_items.append(
        ImageEvidenceItem(
            evidence_type="resolution",
            observation=f"Image dimensions: {file_meta.width}x{file_meta.height} ({file_meta.megapixels} MP, aspect ratio {file_meta.aspect_ratio}).",
            reliability_tier="TECHNICAL_OBSERVATION",
        )
    )

    # Metadata evidence
    if exif_meta.metadata_status == "present" and (exif_meta.camera_make or exif_meta.camera_model):
        hw = f"{exif_meta.camera_make or ''} {exif_meta.camera_model or ''}".strip()
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="metadata",
                observation=f"Hardware tag identified: {hw} (status: {exif_meta.metadata_status}).",
                reliability_tier="SUPPORTING_METADATA",
            )
        )
    elif exif_meta.metadata_status == "partial":
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="metadata",
                observation=f"Partial EXIF tags detected ({exif_meta.raw_tags_count} tags); no hardware make recorded.",
                reliability_tier="SUPPORTING_METADATA",
            )
        )
    else:
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="metadata",
                observation="EXIF hardware tags absent (neutral); contributes zero positive or negative manipulation evidence.",
                reliability_tier="NEUTRAL",
            )
        )

    # Editing software detection
    if exif_meta.editing_software:
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="metadata_software",
                observation=f"Editing software signature identified in EXIF: '{exif_meta.editing_software}'.",
                reliability_tier="TECHNICAL_OBSERVATION",
            )
        )

    # Compression evidence
    if compression.has_quantization_tables and compression.estimated_jpeg_quality is not None:
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="compression",
                observation=f"Measured JPEG quantization indicates encoding quality factor ~{compression.estimated_jpeg_quality}/100.",
                reliability_tier="TECHNICAL_OBSERVATION",
            )
        )

    # ELA evidence
    if ela_result.available and ela_result.mean_error is not None:
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="ela",
                observation=f"Error Level Analysis against baseline Q{ela_result.quality_factor_tested}: mean error {ela_result.mean_error}, max error {ela_result.max_error}.",
                reliability_tier="TECHNICAL_OBSERVATION",
            )
        )
    elif "non_jpeg" in ela_result.status:
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="ela",
                observation=f"Error Level Analysis is not applicable for {file_meta.format} (lossless container).",
                reliability_tier="NEUTRAL",
            )
        )

    if provenance.ai_marker_detected:
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="ai_provenance",
                observation="AI-generation provenance marker(s): " + " ".join(provenance.signals),
                reliability_tier="TECHNICAL_OBSERVATION",
            )
        )

    # Computer Vision evidence
    evidence_items.append(
        ImageEvidenceItem(
            evidence_type="cv_sharpness",
            observation=f"Focus/sharpness indicator: {cv_signals.sharpness_assessment} (Laplacian variance: {cv_signals.sharpness_score}).",
            reliability_tier="QUALITY_INDICATOR",
        )
    )
    evidence_items.append(
        ImageEvidenceItem(
            evidence_type="perceptual_hash",
            observation=f"Perceptual fingerprint: dHash={cv_signals.perceptual_hash_dhash}, pHash={cv_signals.perceptual_hash_phash}.",
            reliability_tier="TECHNICAL_OBSERVATION",
        )
    )

    # OCR evidence
    if ocr_result.available and ocr_result.status == "SUCCESS":
        snippet = (ocr_result.text[:120] + "…") if len(ocr_result.text) > 120 else ocr_result.text
        conf_str = f" ({ocr_result.confidence}% confidence, {ocr_result.ocr_quality} quality)" if ocr_result.confidence else f" ({ocr_result.ocr_quality} quality)"
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="ocr",
                observation=f"Embedded text detected{conf_str}: \"{snippet}\"",
                reliability_tier="DESCRIPTIVE",
            )
        )
    elif ocr_result.available and ocr_result.status == "NO_TEXT_DETECTED":
        evidence_items.append(
            ImageEvidenceItem(
                evidence_type="ocr",
                observation="OCR scanned image; no readable text regions detected.",
                reliability_tier="NEUTRAL",
            )
        )

    # 9. Epistemic Limitations (Mandatory Requirement 12 & 13)
    limitations = [
        "No authenticity conclusion is made from image quality, resolution, or compression alone.",
        "File Health measures technical suitability for digital analysis, NOT real-world authenticity.",
        "Missing EXIF metadata does not indicate manipulation; social platforms routinely strip metadata.",
        "Perceptual hashes aid comparison against archival images, but cannot establish authenticity independently.",
        "Error Level Analysis (ELA) is an indicator of compression differentials, not a manipulation probability.",
        "Unavailable forensic modules (PRNU, optical flow, deepfake detector) contribute zero evidence rather than suspicion.",
        "Final epistemic weighing and dialectical reasoning occur in subsequent Evidence Fusion phases.",
    ]

    return ImageAnalysisResponse(
        ok=True,
        file=file_meta,
        evidence_health=evidence_health,
        metadata=exif_meta,
        ela=ela_result,
        ocr=ocr_result,
        computer_vision=cv_signals,
        evidence=evidence_items,
        provenance=provenance,
        limitations=limitations,
        analyzed_at=now_iso,
    )
