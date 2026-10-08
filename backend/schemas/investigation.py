from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import Field

from backend.schemas.base import CamelModel
from backend.schemas.fusion import (
    TrustTriangle,
    EvidenceSummary,
    ConflictReport,
    NormalizedEvidenceItem,
)

# Re-export CamelModel for backward compatibility
__all__ = [
    "CamelModel",
    "AiVerdict",
    "AiGenerationAssessment",
    "MultimodalAiResult",
    "InvestigationResponse",
    "AiReasoning",
    "FileHealth",
    "EXIFMetadata",
    "PerceptualHash",
    "MediaAnalysis",
    "Claim",
    "Source",
    "Evidence",
    "Contradiction",
    "Provenance",
    "Verdict",
]

# --- Error & Status Enums ---
UrlErrorCode = Literal[
    'INVALID_URL',
    'BLOCKED_HOST',
    'DNS_FAILURE',
    'TIMEOUT',
    'TOO_MANY_REDIRECTS',
    'HTTP_ERROR',
    'UNSUPPORTED_CONTENT',
    'NETWORK_ERROR'
]

AiVerdict = Literal[
    'LIKELY_GENUINE',
    'HIGH_RISK',
    'INCONCLUSIVE',
    'LIKELY_AUTHENTIC',
    'LIKELY_AI_GENERATED',
    'LIKELY_MANIPULATED'
]

AiGenerationAssessment = Literal[
    'likely_ai_generated',
    'likely_authentic',
    'possibly_manipulated',
    'inconclusive'
]


# --- Phase 5 Multimodal AI Response Schema ---
class MultimodalAiResult(CamelModel):
    """
    Structured outcome of Phase 5 Multimodal AI visual analysis.

    Examines actual uploaded pixels alongside Phase 4 forensic telemetry.
    Confidence originates from the vision model's structured assessment,
    never hardcoded or fabricated.
    """
    ai_generation_assessment: AiGenerationAssessment = 'inconclusive'
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    visual_findings: List[str] = Field(default_factory=list)
    supporting_signals: List[str] = Field(default_factory=list)
    contradicting_signals: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    explanation: str = ''
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    analyzed_at: Optional[str] = None


# --- URL Analysis Sub-schemas ---
class UrlAnalysisError(CamelModel):
    code: UrlErrorCode
    message: str
    status_code: Optional[int] = None


class UrlAnalysisData(CamelModel):
    original_url: str
    final_url: str
    original_domain: str
    final_domain: str
    https: bool
    redirect_count: int
    redirect_chain: List[str]
    domain_mismatch: bool
    status_code: int
    content_type: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    site_name: Optional[str] = None
    headings: List[str] = Field(default_factory=list)
    canonical_url: Optional[str] = None
    visible_text: str = ""
    text_truncated: bool = False
    tracking_params: List[str] = Field(default_factory=list)
    suspicious_structure: List[str] = Field(default_factory=list)
    fetched_at: str


class UrlAnalysisOutcomeSuccess(CamelModel):
    ok: Literal[True] = True
    data: UrlAnalysisData


class UrlAnalysisOutcomeFailure(CamelModel):
    ok: Literal[False] = False
    error: UrlAnalysisError


UrlAnalysisOutcome = Union[UrlAnalysisOutcomeSuccess, UrlAnalysisOutcomeFailure]


# --- AI Reasoning / Verdict Schema ---
class AiReasoning(CamelModel):
    claim: str
    verdict: AiVerdict
    confidence: int = Field(ge=0, le=95)
    summary: str
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    # Phase 6 Provenance & Decision Extensions
    reason: Optional[str] = None
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)


# --- Section 10 Core Architectural Models ---

class FileHealth(CamelModel):
    """File Health layer: evaluates file integrity, format, resolution, and metadata completeness."""
    filename: str
    size_bytes: int
    mime_type: str
    sha256: str
    is_supported: bool
    resolution: Optional[str] = None
    compression_ratio: Optional[float] = None
    metadata_available: bool = False
    metadata_completeness_score: float = 0.0  # 0.0 - 1.0
    ocr_quality_score: Optional[float] = None  # None if no OCR performed
    video_frame_count: Optional[int] = None
    # Requirement 6: Missing metadata MUST NOT be treated as manipulation evidence.
    metadata_note: str = "Missing metadata reduces test contribution to zero; it is not evidence of manipulation."


class EXIFMetadata(CamelModel):
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    capture_timestamp: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    is_stripped: bool = False
    software: Optional[str] = None


class PerceptualHash(CamelModel):
    dhash: Optional[str] = None
    phash: Optional[str] = None
    archival_match_found: bool = False
    match_similarity_pct: float = 0.0
    earliest_archival_timestamp: Optional[str] = None


class MediaAnalysis(CamelModel):
    """Media forensics & analysis model."""
    analyzed: bool = False
    media_name: str = "Not provided"
    media_type: Literal['image', 'video', 'document', 'none'] = 'none'
    health: Optional[FileHealth] = None
    exif: Optional[EXIFMetadata] = None
    perceptual_hash: Optional[PerceptualHash] = None
    # Requirement 7 & 8: Do not invent forensic measurements.
    prnu_sensor_available: bool = False
    optical_flow_available: bool = False
    ai_generated_probability: Optional[float] = None  # Displayed ONLY when real detector runs
    tampering_score: Optional[float] = None
    ela_available: bool = False
    ela_mean_error: Optional[float] = None
    ocr_text: Optional[str] = None
    forensic_notes: List[str] = Field(default_factory=list)
    image_analysis: Optional[Any] = None
    multimodal_ai: Optional[MultimodalAiResult] = None


class Claim(CamelModel):
    """Claim representation extracted via NLP understanding."""
    raw_text: str
    normalized_proposition: str
    event_type: Optional[str] = None
    temporal_anchor: Optional[str] = None
    location_anchor: Optional[str] = None
    entities: List[str] = Field(default_factory=list)


class Source(CamelModel):
    """Source reliability and provenance model."""
    domain: str
    url: str
    title: Optional[str] = None
    reliability_tier: Literal['High (Official Reporting)', 'High (Visual Analysis)', 'Medium', 'Unverified'] = 'Unverified'
    is_independent: bool = True
    cluster_id: Optional[str] = None
    syndication_lineage: Optional[str] = None


class Evidence(CamelModel):
    """Discrete evidence vector ingested into dialectical weighing."""
    id: str
    source: Source
    claim_point: str
    evidence_type: Literal['supporting', 'challenging']
    variant: Literal['green', 'red', 'orange']
    detail: str
    timestamp: Optional[str] = None
    reliability: str


class Contradiction(CamelModel):
    """Contradiction detection entity."""
    detected: bool = False
    conflict_type: Optional[Literal['temporal', 'geographic', 'factual', 'provenance']] = None
    description: Optional[str] = None
    earlier_publication_url: Optional[str] = None
    earlier_publication_date: Optional[str] = None


class Provenance(CamelModel):
    """Provenance tracking for claims and assets."""
    origin_url: Optional[str] = None
    earliest_timestamp: Optional[str] = None
    chain_of_custody: List[str] = Field(default_factory=list)
    has_tamper_evidence: bool = False


class Verdict(CamelModel):
    """Epistemic verdict model."""
    status: AiVerdict
    confidence: int = Field(ge=0, le=95)
    headline: str
    main_explanation: str
    why_not_genuine: str
    why_not_high_risk: str
    final_reasoning: str
    why_bullets: List[str] = Field(default_factory=list)


# --- Image Text -> Claim Evidence ---
ImageTextRelationship = Literal[
    "SUPPORTS", "CONTRADICTS", "PARTIALLY_SUPPORTS", "UNRELATED", "INSUFFICIENT_TEXT"
]


class ImageTextEvidence(CamelModel):
    """
    How text visible inside an uploaded image relates to the user's claim.
    The text is evidence to evaluate, NOT proof that what it states is true.
    """
    extracted_text: str = ""
    relevant_text: str = ""
    relationship: ImageTextRelationship = "INSUFFICIENT_TEXT"
    matched_claim_points: List[str] = Field(default_factory=list)
    contradicted_claim_points: List[str] = Field(default_factory=list)
    missing_claim_points: List[str] = Field(default_factory=list)
    explanation: str = ""
    ocr_quality: float = 0.0  # 0.0-1.0, derived from the Phase 4 OCR confidence
    source: str = "uploaded_image"


# --- Primary Response Schema (Matches InvestigationResponse) ---
class InvestigationResponse(CamelModel):
    """Primary response contract consumed by the React/Vite presentation layer."""
    claim: str
    input_url: Optional[str] = None
    url_analysis: Optional[UrlAnalysisOutcome] = None
    final: AiReasoning
    ai_available: bool = False
    ai_note: Optional[str] = None
    model: Optional[str] = None
    generated_at: str

    # Extended models available for Phase 2+ deep consumers
    claim_analysis: Optional[Claim] = None
    media_analysis: Optional[MediaAnalysis] = None
    contradiction: Optional[Contradiction] = None
    provenance: Optional[Provenance] = None
    search_evidence: Optional[Any] = None
    multimodal_analysis: Optional[MultimodalAiResult] = None
    image_text_evidence: Optional[ImageTextEvidence] = None

    # Phase 6 Evidence Fusion models
    trust_triangle: Optional[TrustTriangle] = None
    evidence_summary: Optional[EvidenceSummary] = None
    conflict: Optional[ConflictReport] = None
    normalized_evidence: Optional[List[NormalizedEvidenceItem]] = None
