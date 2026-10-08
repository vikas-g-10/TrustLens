"""
Image Analysis Schemas for TrustLens Phase 4.

Defines structured contracts for File Integrity, Evidence Health, EXIF metadata,
ELA, OCR, Computer Vision metrics, and evidence provenance. All models inherit
from CamelModel for frontend camelCase JSON serialization.
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import Field
from backend.schemas.investigation import CamelModel, MultimodalAiResult


HealthStatus = Literal["EXCELLENT", "GOOD", "FAIR", "POOR", "UNUSABLE"]
MetadataStatus = Literal["present", "partial", "unavailable"]
OcrStatus = Literal["SUCCESS", "NO_TEXT_DETECTED", "UNAVAILABLE"]
OcrQuality = Literal["high", "moderate", "low", "not_applicable", "unavailable"]
SharpnessLevel = Literal["high", "moderate", "low", "blur_detected"]
BrightnessLevel = Literal["normal", "underexposed", "overexposed"]
ReliabilityTier = Literal[
    "SUPPORTING_METADATA",
    "TECHNICAL_OBSERVATION",
    "QUALITY_INDICATOR",
    "DESCRIPTIVE",
    "NEUTRAL",
    "UNVERIFIED"
]


class FileMetadata(CamelModel):
    """Basic file metadata extracted after safe decode and hashing."""
    filename: str
    format: str
    size_bytes: int
    sha256: str
    width: int
    height: int
    aspect_ratio: str
    megapixels: float
    image_mode: str
    mime_type: str
    is_valid: bool = True
    corruption_detected: bool = False


class CompressionIndicators(CamelModel):
    """Measurable compression characteristics and quantization table indicators."""
    has_quantization_tables: bool = False
    estimated_jpeg_quality: Optional[int] = None
    compression_status: str = "not_applicable"
    notes: List[str] = Field(default_factory=list)


class ElaResult(CamelModel):
    """Error Level Analysis (ELA) measurements on recompressed pixel differentials."""
    status: str = "unavailable"
    available: bool = False
    quality_factor_tested: Optional[int] = None
    mean_error: Optional[float] = None
    max_error: Optional[float] = None
    error_variance: Optional[float] = None
    high_error_ratio: Optional[float] = None
    notes: List[str] = Field(default_factory=list)


class ForensicTestAvailability(CamelModel):
    """
    Explicit availability ledger for forensic modules.
    Guarantees transparent reporting: unperformed/unimplemented tests
    are marked 'unavailable' and contribute 0 evidence (zero negative bias).
    """
    file_integrity: str = "available"
    resolution_check: str = "available"
    exif_metadata: str = "unavailable"
    compression_analysis: str = "unavailable"
    ela_analysis: str = "unavailable"
    perceptual_hashing: str = "available"
    reference_comparison: str = "unavailable"
    ocr_extraction: str = "unavailable"
    ai_deepfake_detector: str = "unavailable"
    prnu_sensor_analysis: str = "unavailable"
    optical_flow_analysis: str = "unavailable"


class EvidenceHealth(CamelModel):
    """
    Evidence Health evaluation: measures forensic utility, resolution adequacy,
    and decode integrity. Evidence Health is NOT proof of authenticity.
    """
    score: int = Field(ge=0, le=100, default=50)
    status: HealthStatus = "GOOD"
    decode_successful: bool = True
    metadata_available: bool = False
    metadata_status: MetadataStatus = "unavailable"
    resolution_adequate: bool = True
    compression_indicators: CompressionIndicators
    test_availability: ForensicTestAvailability = Field(default_factory=ForensicTestAvailability)
    signals: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class ExifMetadata(CamelModel):
    """
    EXIF and camera hardware metadata.
    PRIVACY GUARANTEE: Raw GPS latitude/longitude coordinates are strictly withheld.
    EPISTEMIC GUARANTEE: Missing EXIF metadata contributes zero evidence, not negative evidence.
    """
    available: bool = False
    metadata_status: MetadataStatus = "unavailable"
    completeness_score: float = 0.0
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    software: Optional[str] = None
    editing_software: Optional[str] = None
    timestamp: Optional[str] = None
    orientation: Optional[int] = None
    gps_present: bool = False
    color_space: Optional[str] = None
    raw_tags_count: int = 0
    notes: List[str] = Field(default_factory=list)


class OcrResult(CamelModel):
    """Text extraction from image via OCR."""
    status: OcrStatus = "UNAVAILABLE"
    available: bool = False
    ocr_quality: OcrQuality = "unavailable"
    text: str = ""
    confidence: Optional[float] = None
    regions_count: int = 0
    notes: List[str] = Field(default_factory=list)


class ComputerVisionSignals(CamelModel):
    """Explainable, deterministic CV measurements computed over pixel values."""
    sharpness_score: float = 0.0
    sharpness_assessment: SharpnessLevel = "moderate"
    brightness_mean: float = 0.0
    brightness_assessment: BrightnessLevel = "normal"
    contrast_rms: float = 0.0
    edge_density: float = 0.0
    perceptual_hash_dhash: str = ""
    perceptual_hash_phash: str = ""
    comparison_status: str = "unavailable"
    noise_variance: float = 0.0


class ImageEvidenceItem(CamelModel):
    """Discrete evidence vector extracted from the image."""
    evidence_type: str
    observation: str
    reliability_tier: ReliabilityTier = "TECHNICAL_OBSERVATION"


class ProvenanceSignals(CamelModel):
    """Explicit AI-generation provenance markers (C2PA, IPTC, PNG params, tool names)."""
    ai_marker_detected: bool = False
    strong: bool = False
    generator: Optional[str] = None
    c2pa_present: bool = False
    signals: List[str] = Field(default_factory=list)


class ImageAnalysisResponse(CamelModel):
    """Primary response contract for POST /api/analyze-image."""
    ok: bool = True
    file: FileMetadata
    evidence_health: EvidenceHealth
    metadata: ExifMetadata
    ela: ElaResult
    ocr: OcrResult
    computer_vision: ComputerVisionSignals
    evidence: List[ImageEvidenceItem] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    multimodal_ai: Optional[MultimodalAiResult] = None
    provenance: Optional[ProvenanceSignals] = None
    analyzed_at: str
