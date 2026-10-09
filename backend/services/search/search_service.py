"""
Search Orchestration & Evidence Retrieval Service for TrustLens Phase 3.

EPISTEMIC NOTICE:
- Search results are candidate evidence only.
- Source reliability is heuristic.
- Source independence is heuristic.
- No search result alone determines the final verdict.
- The final decision will be performed later by Evidence Fusion.

Handles:
1. Deterministic claim decomposition and multi-query generation (support & counter).
2. Parallel provider retrieval with SSRF safety.
3. URL normalization and provenance preservation.
4. Source reliability scoring and heuristic independence clustering.
5. Evidence classification (SUPPORTING / CONTRADICTING / NEUTRAL / UNKNOWN).
6. Transparent failure reporting without fabricating evidence or jumping to verdicts.
"""
import asyncio
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import httpx
from bs4 import BeautifulSoup

from config import settings
from schemas.search import (
    SearchResultCandidate,
    SourceCluster,
    GeneratedQuery,
    SearchEvidence,
    EvidenceRole,
    QueryType,
    ContentStatus,
    RetrievalStatus,
)
from services.search.base import SearchProvider, SearchProviderError, RawSearchResult
from services.search.duckduckgo_provider import DuckDuckGoSearchProvider
from services.search.tavily_provider import TavilySearchProvider
from services.source_reliability import evaluate_source_reliability, get_root_domain
from services.source_independence import cluster_sources_by_independence
from utils.ssrf_validator import validate_url_ssrf_safety, is_blocked_ip


# Contradiction / Debunking lexical markers
CONTRADICTION_MARKERS = [
    r"\bfalse\b", r"\bfake\b", r"\bhoax\b", r"\bdebunked?\b",
    r"\bdenied\b", r"\bdenies\b", r"\bmisleading\b", r"\buntrue\b",
    r"\bfact[- ]check\b", r"\bno evidence\b", r"\bdid not (?:happen|occur)\b",
    r"\bfabricated\b", r"\brefuted\b", r"\bdisproven\b", r"\bdoctored\b",
    r"\bout of context\b", r"\bdeepfake\b"
]

COMMON_STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "by", "with", "is", "are", "was", "were", "been", "has", "have", "had",
    "that", "this", "these", "those", "it", "its", "from", "as", "about"
}

KNOWN_EVENT_KEYWORDS = [
    "rainfall", "flooding", "flood", "rain", "earthquake", "landslide",
    "resigned", "arrested", "elected", "died", "killed", "passed away",
    "accident", "crash", "explosion", "fire", "scam", "protest", "strike",
    "announced", "launched", "signed", "warns", "banned"
]


def normalize_source_url(raw_url: str) -> Tuple[str, str, str]:
    """
    Normalize URL: lowercase scheme & host, strip fragments and tracking parameters.
    Returns:
        (canonical_url, domain, root_domain)
    """
    parsed = urlparse(raw_url.strip())
    scheme = parsed.scheme.lower() or "https"
    domain = (parsed.hostname or parsed.netloc).lower()
    root_domain = get_root_domain(domain)

    # Standard port clean-up for canonical URL netloc
    port = parsed.port
    if port and ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        netloc = domain
    elif port:
        netloc = f"{domain}:{port}"
    else:
        netloc = domain

    # Strip standard tracking query params
    clean_params = []
    if parsed.query:
        tracking_keys = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "fbclid", "gclid", "dclid", "msclkid", "ref", "source"
        }
        for k, v in parse_qs(parsed.query, keep_blank_values=False).items():
            if k.lower() not in tracking_keys:
                for val in v:
                    clean_params.append((k, val))

    clean_query = urlencode(clean_params)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    canonical = urlunparse((scheme, netloc, path, "", clean_query, ""))
    return canonical, domain, root_domain



class ClaimQueryGenerator:
    """
    Deterministic claim query generator.
    Extracts entities, location, dates, events, and produces focused support and counter queries.
    """

    @classmethod
    def decompose_claim(cls, claim: str) -> Dict[str, any]:
        """Extract entities, location, date, event, and keywords using deterministic regex."""
        text = claim.strip()

        # 1. Date extraction (e.g. October 5 2026, Oct 2026, 2026, 05/10/2026)
        date_match = re.search(
            r"\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*,?\s+\d{4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}|20\d\d[-/]\d\d[-/]\d\d|\b20\d\d\b)",
            text,
            re.IGNORECASE,
        )
        date_str = date_match.group(1).strip() if date_match else None

        # 2. Location extraction (phrases after 'in', 'at', 'near', or capitalized geographic tokens)
        loc_match = re.search(r"\b(?:in|at|near|across)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        location_str = loc_match.group(1).strip() if loc_match else None

        # 3. Event extraction
        detected_events = [ev for ev in KNOWN_EVENT_KEYWORDS if re.search(r"\b" + re.escape(ev) + r"\b", text, re.IGNORECASE)]
        event_str = " ".join(detected_events) if detected_events else None

        # 4. Entities (Capitalized tokens or quoted phrases not at start of sentence)
        quoted = re.findall(r'"([^"]+)"', text)
        cap_words = re.findall(r'(?<=\s)[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text)
        entities = list(dict.fromkeys(quoted + cap_words))
        if location_str and location_str in entities:
            entities.remove(location_str)

        # 5. Core keywords (alphanumeric, not stop words)
        words = [re.sub(r"[^\w]", "", w) for w in text.split()]
        keywords = [w for w in words if w.lower() not in COMMON_STOPWORDS and len(w) > 2]

        return {
            "date": date_str,
            "location": location_str,
            "event": event_str,
            "entities": entities,
            "keywords": keywords,
        }

    @classmethod
    def generate_queries(cls, claim: str) -> List[GeneratedQuery]:
        """
        Generate multiple distinct focused queries:
        1. Exact/Core phrase query
        2. Entity + Event query
        3. Entity + Date query
        4. Event + Location query
        5. Contradiction / Counter queries (false, fact check, denied, debunked)
        """
        parsed = cls.decompose_claim(claim)
        queries: List[GeneratedQuery] = []
        seen_query_texts: Set[str] = set()

        def add_query(q_text: str, q_type: QueryType, focus: str):
            clean = " ".join(q_text.strip().split())
            if clean and clean.lower() not in seen_query_texts:
                seen_query_texts.add(clean.lower())
                queries.append(GeneratedQuery(query=clean, query_type=q_type, focus=focus))

        entities = parsed["entities"]
        location = parsed["location"]
        event = parsed["event"]
        date = parsed["date"]
        keywords = parsed["keywords"]

        # 1. Exact key phrase query (quoted core assertion or top 4 keywords)
        if len(keywords) >= 3:
            exact_core = " ".join(keywords[:4])
            add_query(f'"{exact_core}"', "support", "exact_phrase")
        else:
            add_query(f'"{claim.strip()}"', "support", "exact_phrase")

        # 2. Entity + Event query
        subject = entities[0] if entities else (location or "")
        if subject and event:
            add_query(f"{subject} {event}", "support", "entity_event")
        elif subject and len(keywords) >= 2:
            add_query(f"{subject} {' '.join(keywords[:3])}", "support", "entity_keywords")

        # 3. Entity + Date query
        if (subject or location) and date:
            target_loc = location or subject
            add_query(f"{target_loc} {date} {event or ''}".strip(), "support", "entity_date")

        # 4. Event + Location query
        if event and location:
            add_query(f"{event} in {location} {date or ''}".strip(), "support", "event_location")

        # 5. Fallback top keywords query if needed
        if len(queries) < 3 and keywords:
            add_query(" ".join(keywords[:5]), "support", "keyword_fallback")

        # 6. Contradiction / Counter queries (MANDATORY REQUIREMENT 3)
        counter_anchor = f"{location or (entities[0] if entities else '')} {event or (' '.join(keywords[:2]))}".strip()
        if not counter_anchor:
            counter_anchor = " ".join(keywords[:3])

        add_query(f"{counter_anchor} false", "counter", "counter_false")
        add_query(f"{counter_anchor} fact check", "counter", "counter_factcheck")
        add_query(f"{counter_anchor} denied", "counter", "counter_denied")
        add_query(f"{counter_anchor} debunked", "counter", "counter_debunked")

        return queries


class EvidenceClassifier:
    """
    Conservative deterministic evidence classifier.
    Categorizes candidate sources into SUPPORTING, CONTRADICTING, NEUTRAL, UNKNOWN.
    """

    @classmethod
    def classify(
        cls,
        claim: str,
        title: str,
        snippet: str,
        extracted_text: Optional[str] = None,
        query_type: QueryType = "support",
    ) -> Tuple[EvidenceRole, str, float]:
        """
        Classify candidate evidence against user claim.
        Returns:
            (evidence_role, classification_reason, classification_confidence)
        """
        text_corpus = f"{title} {snippet} {extracted_text or ''}".lower()
        claim_lower = claim.lower()
        decomp = ClaimQueryGenerator.decompose_claim(claim)

        # Check for contradiction / debunking markers
        contradiction_hits = [
            m for m in CONTRADICTION_MARKERS
            if re.search(m, text_corpus)
        ]

        # Calculate overlap with claim keywords
        claim_kw = [k.lower() for k in decomp["keywords"] if len(k) > 3]
        matched_kw = [k for k in claim_kw if k in text_corpus]
        overlap_ratio = len(matched_kw) / len(claim_kw) if claim_kw else 0.0

        # Location and event match
        loc = decomp["location"]
        event = decomp["event"]
        loc_matched = bool(loc and loc.lower() in text_corpus)
        event_matched = bool(event and any(e in text_corpus for e in event.split()))

        # Rule 1: Clear contradiction / fact-check debunk
        if contradiction_hits and (loc_matched or event_matched or overlap_ratio >= 0.4):
            clean_hits = [h.replace(r"\b", "") for h in contradiction_hits[:2]]
            reason = (
                f"Source explicitly contains debunking or contradiction signals ({', '.join(clean_hits)}) "
                f"addressing the claimed topic."
            )
            return "CONTRADICTING", reason, 0.85

        # Rule 2: Strong corroboration / supporting report
        if (loc_matched or not loc) and (event_matched or overlap_ratio >= 0.6) and not contradiction_hits:
            reason = (
                "Source directly reports and corroborates the claimed event and context without negation."
            )
            confidence = min(0.90, 0.50 + overlap_ratio * 0.4)
            return "SUPPORTING", reason, round(confidence, 2)

        # Rule 3: Moderate overlap without assertion
        if overlap_ratio >= 0.35 or loc_matched:
            reason = (
                "Source mentions related entities or location but provides background context without "
                "definitively verifying or refuting the claim."
            )
            return "NEUTRAL", reason, 0.60

        # Rule 4: Ambiguous or weak overlap
        return (
            "UNKNOWN",
            "Insufficient topical overlap in retrieved snippet to establish supporting or contradicting evidence.",
            0.20,
        )


class SearchService:
    """
    Primary Search & Evidence Retrieval Service.
    Orchestrates query generation, provider execution, SSRF-safe page fetching,
    source reliability, and independence clustering.
    """

    def __init__(self, provider: Optional[SearchProvider] = None):
        if provider:
            self.provider = provider
        elif settings.search_provider == "tavily" and settings.tavily_api_key:
            self.provider = TavilySearchProvider(api_key=settings.tavily_api_key)
        else:
            self.provider = DuckDuckGoSearchProvider()

    async def _fetch_limited_content(self, url: str) -> Tuple[ContentStatus, Optional[str]]:
        """
        Fetch a limited excerpt of untrusted web content with Phase 2 SSRF protections.
        Limits: 150KB max, 3.5s timeout, public IPs only, no JS.
        """
        # Validate SSRF safety before initiating HTTP call
        is_safe, error_code, error_msg = validate_url_ssrf_safety(url)
        if not is_safe:
            return "UNAVAILABLE", None

        try:
            async with httpx.AsyncClient(
                follow_redirects=False,  # Re-validate every redirect manually
                timeout=3.5,
                headers={"User-Agent": "TrustLens-AIML-EvidenceBot/1.0"},
            ) as client:
                current_url = url
                response = None
                for _ in range(3):  # Max 3 hops
                    safe, _, _ = validate_url_ssrf_safety(current_url)
                    if not safe:
                        return "UNAVAILABLE", None

                    resp = await client.get(current_url)
                    if resp.is_redirect:
                        loc = resp.headers.get("location")
                        if not loc:
                            break
                        parsed_curr = urlparse(current_url)
                        current_url = str(httpx.URL(current_url).join(loc))
                        continue
                    response = resp
                    break

                if not response or response.status_code != 200:
                    return "UNAVAILABLE", None

                # Extract first 150KB
                content_bytes = response.content[: 150 * 1024]
                html_text = content_bytes.decode("utf-8", errors="replace")

                soup = BeautifulSoup(html_text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    tag.decompose()

                extracted_text = " ".join(soup.get_text().split())[:2000]
                return "AVAILABLE", extracted_text

        except Exception:
            return "UNAVAILABLE", None

    async def investigate_claim(
        self,
        claim: str,
        max_queries: int = 6,
        results_per_query: int = 4,
        fetch_top_n: int = 2,
    ) -> SearchEvidence:
        """
        Execute full Phase 3 evidence retrieval for a user claim.
        """
        claim_clean = claim.strip()
        if not claim_clean:
            return SearchEvidence(
                queries=[],
                supporting=[],
                contradicting=[],
                neutral=[],
                sources=[],
                clusters=[],
                retrieval_status="SUCCESS",
                retrieval_note="No claim text provided for retrieval.",
            )

        # 1. Deterministic Query Generation
        generated_queries = ClaimQueryGenerator.generate_queries(claim_clean)[:max_queries]
        all_raw_results: List[Tuple[RawSearchResult, GeneratedQuery]] = []
        retrieval_errors: List[str] = []

        # 2. Execute searches across providers concurrently
        async def run_single_query(gen_q: GeneratedQuery):
            try:
                results = await self.provider.search(gen_q.query, max_results=results_per_query)
                return gen_q, results, None
            except SearchProviderError as spe:
                return gen_q, [], str(spe)
            except Exception as exc:
                return gen_q, [], str(exc)

        query_tasks = [run_single_query(q) for q in generated_queries]
        query_outcomes = await asyncio.gather(*query_tasks)

        for gen_q, results, err in query_outcomes:
            if err:
                retrieval_errors.append(f"Query '{gen_q.query}': {err}")
            for r in results:
                all_raw_results.append((r, gen_q))

        # 3. Determine Overall Retrieval Status
        if not all_raw_results and retrieval_errors:
            # Full provider failure
            return SearchEvidence(
                queries=generated_queries,
                supporting=[],
                contradicting=[],
                neutral=[],
                sources=[],
                clusters=[],
                retrieval_status="FAILED",
                retrieval_note=f"Search provider ({self.provider.provider_name}) was unreachable: {retrieval_errors[0]}",
            )

        retrieval_status: RetrievalStatus = "PARTIAL" if retrieval_errors else "SUCCESS"
        retrieval_note = None
        if retrieval_errors:
            retrieval_note = f"{len(retrieval_errors)} queries failed during retrieval."

        if not all_raw_results:
            # Succeeded without finding results (e.g. obscure or zero-hit search)
            return SearchEvidence(
                queries=generated_queries,
                supporting=[],
                contradicting=[],
                neutral=[],
                sources=[],
                clusters=[],
                retrieval_status="SUCCESS",
                retrieval_note="No candidate search sources found for this claim.",
            )

        # 4. Deduplicate Candidates while preserving Provenance
        unique_candidates: Dict[str, SearchResultCandidate] = {}

        for raw_r, gen_q in all_raw_results:
            canonical_url, domain, root_domain = normalize_source_url(raw_r.url)
            if canonical_url in unique_candidates:
                continue

            # Evaluate Source Reliability
            score, factors, explanations = evaluate_source_reliability(
                url=canonical_url,
                title=raw_r.title,
                snippet=raw_r.snippet,
                content_accessible=None,  # Evaluated if fetched
                published_date=raw_r.published_date,
            )

            candidate = SearchResultCandidate(
                title=raw_r.title,
                url=canonical_url,
                snippet=raw_r.snippet,
                domain=domain,
                root_domain=root_domain,
                canonical_url=canonical_url,
                published_date=raw_r.published_date,
                provider=raw_r.provider,
                rank=raw_r.rank,
                retrieved_at=raw_r.retrieved_at,
                search_query=gen_q.query,
                query_type=gen_q.query_type,
                reliability_score=score,
                reliability_factors=factors,
                reliability_explanation=explanations,
                content_status="NOT_FETCHED",
            )
            unique_candidates[canonical_url] = candidate

        candidate_list = list(unique_candidates.values())

        # 5. Optional Safe Content Fetching for Top Candidates
        # Fetch top N to supplement snippets
        fetch_tasks = []
        for i, cand in enumerate(candidate_list[:fetch_top_n]):
            fetch_tasks.append(self._fetch_limited_content(cand.url))

        if fetch_tasks:
            fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
            for i, res in enumerate(fetch_results):
                cand = candidate_list[i]
                if isinstance(res, tuple):
                    c_status, ext_text = res
                    cand.content_status = c_status
                    cand.extracted_text = ext_text
                    # Re-score with content accessibility factor
                    score, factors, explanations = evaluate_source_reliability(
                        url=cand.url,
                        title=cand.title,
                        snippet=cand.snippet,
                        content_accessible=(c_status == "AVAILABLE"),
                        published_date=cand.published_date,
                    )
                    cand.reliability_score = score
                    cand.reliability_factors = factors
                    cand.reliability_explanation = explanations

        # 6. Source Independence Clustering
        clusters, clustered_candidates = cluster_sources_by_independence(candidate_list)

        # 7. Evidence Classification
        supporting: List[SearchResultCandidate] = []
        contradicting: List[SearchResultCandidate] = []
        neutral: List[SearchResultCandidate] = []

        for cand in clustered_candidates:
            role, reason, conf = EvidenceClassifier.classify(
                claim=claim_clean,
                title=cand.title,
                snippet=cand.snippet,
                extracted_text=cand.extracted_text,
                query_type=cand.query_type,
            )
            cand.evidence_role = role
            cand.classification_reason = reason
            cand.classification_confidence = conf

            if role == "SUPPORTING":
                supporting.append(cand)
            elif role == "CONTRADICTING":
                contradicting.append(cand)
            elif role == "NEUTRAL":
                neutral.append(cand)

        # Re-sort clusters and candidates by reliability and rank
        supporting.sort(key=lambda s: s.reliability_score, reverse=True)
        contradicting.sort(key=lambda s: s.reliability_score, reverse=True)
        neutral.sort(key=lambda s: s.reliability_score, reverse=True)
        clustered_candidates.sort(key=lambda s: s.reliability_score, reverse=True)

        return SearchEvidence(
            queries=generated_queries,
            supporting=supporting,
            contradicting=contradicting,
            neutral=neutral,
            sources=clustered_candidates,
            clusters=clusters,
            retrieval_status=retrieval_status,
            retrieval_note=retrieval_note,
        )
