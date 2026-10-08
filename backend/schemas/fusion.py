"""
Evidence Fusion Schemas for TrustLens Phase 6.

Defines common normalized evidence structures, conflict detection models,
Trust Triangle metrics, evidence summary ledgers, and deterministic fusion outcomes.
All models inherit from CamelModel for frontend camelCase JSON serialization.
"""
from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from backend.schemas.base import CamelModel


EvidenceDirection = Literal[
    "SUPPORTS", "CONTRADICTS", "NEUTRAL",
    # Image-text vs claim relationships (IMAGE_TEXT evidence)
    "PARTIALLY_SUPPORTS", "UNRELATED", "INSUFFICIENT_TEXT",
]

TargetHypothesis = Literal[
    "AUTHENTIC",
    "AI_GENERATED",
    "MANIPULATED",
    "CLAIM_TRUE",
    "CLAIM_FALSE",
    "CONTEXTUAL"
]

EvidenceType = Literal[
    "FILE_INTEGRITY",
    "METADATA_EXIF",
    "IMAGE_COMPRESSION",
    "IMAGE_ELA",
    "PERCEPTUAL_HASH",
    "OCR_TEXT",
    "IMAGE_TEXT",
    "MULTIMODAL_VISION",
    "WEB_SOURCE",
    "URL_SECURITY",
    "CORROBORATING_REPORT"
]

ConflictSeverity = Literal["NONE", "LOW", "MEDIUM", "HIGH"]

FinalVerdictType = Literal[
    "LIKELY_AUTHENTIC",
    "LIKELY_AI_GENERATED",
    "LIKELY_MANIPULATED",
    "INCONCLUSIVE",
    "LIKELY_GENUINE",
    "HIGH_RISK"
]


class NormalizedEvidenceItem(CamelModel):
    """
    Common normalized internal representation for discrete evidence points.
    Applies to media files, forensic checks, multimodal AI visual signals,
    web news sources, and URL security indicators.
    """
    evidence_id: str
    evidence_type: EvidenceType
    description: str
    direction: EvidenceDirection
    target_hypothesis: TargetHypothesis = "CONTEXTUAL"
    reliability: float = Field(ge=0.0, le=1.0, default=0.5)
    quality: float = Field(ge=0.0, le=1.0, default=0.5)
    independence_group: str = "unassigned"
    source: str = "internal"
    provenance: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, default=0.0)
    limitations: List[str] = Field(default_factory=list)


class ConflictDetail(CamelModel):
    """Specific collision instance between opposing evidence items."""
    conflict_id: str
    description: str
    conflicting_evidence_ids: List[str] = Field(default_factory=list)
    severity: ConflictSeverity = "LOW"
    dimension: str = "GENERAL"


class ConflictReport(CamelModel):
    """Structured report on detected contradictions and collisions."""
    detected: bool = False
    count: int = 0
    severity: ConflictSeverity = "NONE"
    conflict_score: float = Field(ge=0.0, le=1.0, default=0.0)
    conflicting_evidence_ids: List[str] = Field(default_factory=list)
    description: str = "No conflicting evidence detected."
    details: List[ConflictDetail] = Field(default_factory=list)


class TrustTriangle(CamelModel):
    """
    The TrustLens Trust Triangle:
    1. Manipulation / AI-generation Likelihood (0.0 - 100.0)
    2. Evidence Strength (0.0 - 100.0)
    3. Evidence Conflict (0.0 - 100.0)
    """
    manipulation_likelihood: float = Field(ge=0.0, le=100.0, default=0.0)
    evidence_strength: float = Field(ge=0.0, le=100.0, default=0.0)
    evidence_conflict: float = Field(ge=0.0, le=100.0, default=0.0)


class EvidenceSummary(CamelModel):
    """Quantitative summary of ingested evidence vectors."""
    supporting_strength: float = 0.0
    contradicting_strength: float = 0.0
    independent_evidence_count: int = 0
    evidence_coverage: float = Field(ge=0.0, le=1.0, default=0.0)
    total_evidence_count: int = 0
    supporting_count: int = 0
    contradicting_count: int = 0
    neutral_count: int = 0


class FusionResult(CamelModel):
    """
    Complete outcome of the deterministic Evidence Fusion engine.
    Traceable to individual evidence points and transparently explainable.
    """
    verdict: FinalVerdictType = "INCONCLUSIVE"
    confidence: int = Field(ge=0, le=95, default=0)
    reason: str = ""
    trust_triangle: TrustTriangle = Field(default_factory=TrustTriangle)
    evidence_summary: EvidenceSummary = Field(default_factory=EvidenceSummary)
    conflict: ConflictReport = Field(default_factory=ConflictReport)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    normalized_evidence: List[NormalizedEvidenceItem] = Field(default_factory=list)
