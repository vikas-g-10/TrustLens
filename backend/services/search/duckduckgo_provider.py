"""
DuckDuckGo Search Provider Implementation for TrustLens Phase 3.

Provides free, keyless candidate evidence retrieval with strict error handling,
threadpool offloading, and structured provenance metadata.
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

from services.search.base import SearchProvider, SearchProviderError, RawSearchResult


class DuckDuckGoSearchProvider(SearchProvider):
    """
    SearchProvider implementation using DuckDuckGo (via `ddgs` or `duckduckgo_search`).
    Runs synchronously offloaded to asyncio.to_thread to maintain asynchronous performance.
    """

    def __init__(self, timeout_seconds: float = 8.0):
        self.timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "duckduckgo"

    def _sync_search(self, query: str, max_results: int) -> List[dict]:
        """Synchronous search worker."""
        try:
            # Prefer ddgs library, fallback to duckduckgo_search
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS  # type: ignore

            with DDGS(timeout=self.timeout_seconds) as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return results
        except Exception as exc:
            raise SearchProviderError(
                message=f"DuckDuckGo search failed for query '{query}': {str(exc)}",
                provider=self.provider_name,
                original_error=exc,
            ) from exc

    async def search(self, query: str, max_results: int = 5) -> List[RawSearchResult]:
        """
        Execute search on DuckDuckGo and return standardized RawSearchResult list.
        Never fabricates results.
        """
        query_clean = query.strip()
        if not query_clean:
            return []

        try:
            raw_items = await asyncio.wait_for(
                asyncio.to_thread(self._sync_search, query_clean, max_results),
                timeout=self.timeout_seconds + 2.0,
            )
        except asyncio.TimeoutError as te:
            raise SearchProviderError(
                message=f"DuckDuckGo search timed out after {self.timeout_seconds}s for query '{query_clean}'",
                provider=self.provider_name,
                original_error=te,
            ) from te
        except SearchProviderError:
            raise
        except Exception as exc:
            raise SearchProviderError(
                message=f"Unexpected error executing DuckDuckGo search: {str(exc)}",
                provider=self.provider_name,
                original_error=exc,
            ) from exc

        now_iso = datetime.now(timezone.utc).isoformat()
        results: List[RawSearchResult] = []

        for idx, item in enumerate(raw_items, start=1):
            url = str(item.get("href", "")).strip()
            title = str(item.get("title", "")).strip()
            snippet = str(item.get("body", "")).strip()

            if not url:
                continue

            # Extract domain cleanly
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            results.append(
                RawSearchResult(
                    title=title or "Untitled",
                    url=url,
                    snippet=snippet,
                    domain=domain,
                    published_date=None,  # DDG text search does not reliably include publication dates
                    provider=self.provider_name,
                    rank=idx,
                    retrieved_at=now_iso,
                )
            )

        return results
