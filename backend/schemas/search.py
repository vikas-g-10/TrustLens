"""
Search and Evidence Retrieval Schemas for TrustLens Phase 3.

All models inherit from CamelModel for seamless frontend camelCase serialization.
Search results represent CANDIDATE EVIDENCE only and maintain explicit provenance.
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import Field
from backend.schemas.investigation import CamelModel


EvidenceRole = Literal['SUPPORTING', 'CONTRADICTING', 'NEUTRAL', 'UNKNOWN']
RetrievalStatus = Literal['SUCCESS', 'PARTIAL', 'FAILED']
IndependenceLevel = Literal['INDEPENDENT', 'RELATED', 'SYNDICATED', 'DUPLICATE']
ContentStatus = Literal['AVAILABLE', 'UNAVAILABLE', 'NOT_FETCHED']
QueryType = Literal['support', 'counter', 'direct']


class SearchResultCandidate(CamelModel):
    """A single candidate evidence source retrieved from external search."""
    title: str
    url: str
    snippet: str
    domain: str
    root_domain: str
    canonical_url: Optional[str] = None
    published_date: Optional[str] = None
    provider: str = "duckduckgo"
    rank: int = 1
    retrieved_at: str
    search_query: str = ""
    query_type: QueryType = "support"

    # Explainable Reliability Assessment
    reliability_score: int = Field(ge=0, le=100, default=50)
    reliability_factors: Dict[str, str] = Field(default_factory=dict)
    reliability_explanation: List[str] = Field(default_factory=list)

    # Heuristic Source Independence
    cluster_id: Optional[str] = None
    independence_level: Optional[IndependenceLevel] = None

    # Evidence Classification
    evidence_role: EvidenceRole = "UNKNOWN"
    classification_reason: str = ""
    classification_confidence: float = Field(ge=0.0, le=1.0, default=0.0)

    # Content Retrieval Status
    content_status: ContentStatus = "NOT_FETCHED"
    extracted_text: Optional[str] = None


class SourceCluster(CamelModel):
    """A cluster of sources grouped by independence heuristics."""
    cluster_id: str
    representative_source: SearchResultCandidate
    member_sources: List[SearchResultCandidate] = Field(default_factory=list)
    independence_level: IndependenceLevel
    reason: str


class GeneratedQuery(CamelModel):
    """A deterministic query generated from a user claim."""
    query: str
    query_type: QueryType
    focus: str


class SearchEvidence(CamelModel):
    """Structured candidate evidence retrieved during an investigation."""
    queries: List[GeneratedQuery] = Field(default_factory=list)
    supporting: List[SearchResultCandidate] = Field(default_factory=list)
    contradicting: List[SearchResultCandidate] = Field(default_factory=list)
    neutral: List[SearchResultCandidate] = Field(default_factory=list)
    sources: List[SearchResultCandidate] = Field(default_factory=list)
    clusters: List[SourceCluster] = Field(default_factory=list)
    retrieval_status: RetrievalStatus = "SUCCESS"
    retrieval_note: Optional[str] = None
