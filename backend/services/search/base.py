"""
Search Provider Abstract Interface for TrustLens Phase 3.

EPISTEMIC NOTICE:
- Search results are candidate evidence only.
- Source reliability is heuristic.
- Source independence is heuristic.
- No search result alone determines the final verdict.
- The final decision will be performed later by Evidence Fusion.

Defines the contract for external search providers (DuckDuckGo, Tavily, etc.)
so that candidate evidence retrieval is provider-agnostic and maintains
strict provenance.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchProviderError(Exception):
    """Raised when an external search provider fails or is unreachable."""
    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error


class RawSearchResult(BaseModel):
    """
    Standardized result structure returned by any SearchProvider.
    Ensures provider-specific structures are never leaked into the application.
    """
    title: str
    url: str
    snippet: str
    domain: str
    published_date: Optional[str] = None
    provider: str
    rank: int = 1
    retrieved_at: str


class SearchProvider(ABC):
    """
    Abstract interface for evidence search providers.
    """
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the search provider."""
        pass

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[RawSearchResult]:
        """
        Execute an asynchronous search query and return standardized RawSearchResult items.
        
        Args:
            query: The search query string.
            max_results: Maximum number of search candidates to return.
            
        Returns:
            List of RawSearchResult objects.
            
        Raises:
            SearchProviderError: If the provider is unreachable or returns an error.
        """
        pass
