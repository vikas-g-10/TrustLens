"""
Tavily Search Provider Implementation (Optional) for TrustLens Phase 3.

Only activated if TAVILY_API_KEY is configured in the environment.
"""
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse
import httpx

from services.search.base import SearchProvider, SearchProviderError, RawSearchResult


class TavilySearchProvider(SearchProvider):
    """
    SearchProvider implementation using Tavily Search API.
    Activated only if API key is provided; fails transparently otherwise.
    """

    def __init__(self, api_key: str, timeout_seconds: float = 8.0):
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "tavily"

    async def search(self, query: str, max_results: int = 5) -> List[RawSearchResult]:
        if not self.api_key:
            raise SearchProviderError("Tavily API key is not configured.", provider=self.provider_name)

        query_clean = query.strip()
        if not query_clean:
            return []

        payload = {
            "api_key": self.api_key,
            "query": query_clean,
            "max_results": max_results,
            "search_depth": "basic",
            "include_domains": [],
            "exclude_domains": [],
        }

        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post("https://api.tavily.com/search", json=payload)
                if res.status_code != 200:
                    raise SearchProviderError(
                        f"Tavily returned HTTP {res.status_code}: {res.text[:200]}",
                        provider=self.provider_name,
                    )
                data = res.json()
        except Exception as exc:
            raise SearchProviderError(
                f"Tavily request failed: {str(exc)}",
                provider=self.provider_name,
                original_error=exc,
            ) from exc

        results: List[RawSearchResult] = []
        raw_items = data.get("results", [])
        for idx, item in enumerate(raw_items, start=1):
            url = str(item.get("url", "")).strip()
            title = str(item.get("title", "")).strip()
            snippet = str(item.get("content", "")).strip()
            pub_date = item.get("published_date")

            if not url:
                continue

            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            results.append(
                RawSearchResult(
                    title=title or "Untitled",
                    url=url,
                    snippet=snippet,
                    domain=domain,
                    published_date=pub_date,
                    provider=self.provider_name,
                    rank=idx,
                    retrieved_at=now_iso,
                )
            )

        return results
