"""
Video Analysis Schemas for TrustLens Phase 8.

Video evidence is derived ONLY from real processing: container/stream probing,
deterministic representative-frame extraction, and the existing Phase 4 image
pipeline (+ optional Phase 5 multimodal) run on those frames.

Nothing here represents authenticity, deepfake, PRNU, optical-flow or
AI-generated-video detection; those capabilities are reported as UNAVAILABLE.
"""
from typing import Any, List, Literal, Optional
from pydantic import Field
from backend.schemas.base import CamelModel
from backend.schemas.image_analysis import ImageAnalysisResponse

VideoClaimRelationship = Literal[
    "SUPPORTS", "CONTRADICTS", "PARTIALLY_SUPPORTS", "UNRELATED", "INSUFFICIENT_EVIDENCE"
]
CapabilityStatus = Literal["IMPLEMENTED", "PARTIAL", "UNAVAILABLE"]
VideoStatus = Literal["ANALYZED", "PARTIAL", "FAILED"]


class VideoMetadata(CamelModel):
    """Facts measured from the uploaded video. Fields are None when not measurable."""
    filename: str
    size_bytes: int
    sha256: str
    container: Optional[str] = None
    codec: Optional[str] = None
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_rate: Optional[float] = None
    frame_count: Optional[int] = None
    frame_count_source: Optional[str] = None  # "container" | "estimated_from_duration" | None
    decodable: bool = False
    probe_tool: str = "none"  # "ffprobe+opencv" | "opencv" | "none"
    notes: List[str] = Field(default_factory=list)


class VideoFrameEvidence(CamelModel):
    """Evidence from ONE representative frame; carries provenance back to the video."""
    frame_ref: str                      # e.g. "frame_2_middle"
    position: Literal["beginning", "middle", "end"]
    frame_index: int                    # requested index within the video
    timestamp_seconds: Optional[float] = None
    source_type: str = "VIDEO"
    source: str = "uploaded_video"
    decoded: bool = False
    error: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    downscaled: bool = False
    sha256: Optional[str] = None
    thumbnail_data_url: Optional[str] = None
    quality_score: Optional[int] = None      # existing Evidence Health score (technical suitability only)
    quality_status: Optional[str] = None
    ocr_available: bool = False
    ocr_text: str = ""
    ocr_confidence: Optional[float] = None
    ocr_quality: float = 0.0                 # 0-1, from the existing Phase 4 OCR-quality score
    claim_relationship: Optional[VideoClaimRelationship] = None
    claim_explanation: Optional[str] = None
    image_analysis: Optional[ImageAnalysisResponse] = None
    multimodal: Optional[Any] = None         # MultimodalAiResult for this frame, if it was run


class VideoCapability(CamelModel):
    name: str
    status: CapabilityStatus
    note: str = ""


class VideoClaimComparison(CamelModel):
    relationship: VideoClaimRelationship = "INSUFFICIENT_EVIDENCE"
    explanation: str = ""
    supporting_frames: List[str] = Field(default_factory=list)
    contradicting_frames: List[str] = Field(default_factory=list)
    ocr_quality: float = Field(ge=0.0, le=1.0, default=0.0)
    source_type: str = "VIDEO"
    source: str = "uploaded_video"


class VideoAnalysisResult(CamelModel):
    ok: bool = False
    status: VideoStatus = "FAILED"
    error_code: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[VideoMetadata] = None
    frames: List[VideoFrameEvidence] = Field(default_factory=list)
    claim_comparison: Optional[VideoClaimComparison] = None
    capabilities: List[VideoCapability] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    analyzed_at: str = ""
