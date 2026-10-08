"""
Source Independence Clustering for TrustLens Phase 3.

EPISTEMIC NOTICE:
- Search results are candidate evidence only.
- Source reliability is heuristic.
- Source independence is heuristic.
- No search result alone determines the final verdict.
- The final decision will be performed later by Evidence Fusion.

Evaluates whether multiple retrieved candidate sources represent truly independent
reporting or mere duplication/wire syndication.
Heuristic assessment: Does not claim absolute verification of editorial independence.
"""
import re
from typing import List, Set, Tuple
from urllib.parse import urlparse

from backend.schemas.search import (
    SearchResultCandidate,
    SourceCluster,
    IndependenceLevel,
)
from backend.services.source_reliability import get_root_domain


# Known wire services that syndicate across thousands of outlets
WIRE_SERVICES = {
    "reuters", "associated press", "ap news", "afp", "agence france-presse",
    "ani", "pti", "press trust of india", "bloomberg", "pr newswire", "business wire"
}

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were",
    "will", "with", "this", "after", "says", "said", "over"
}


def _tokenize(text: str) -> Set[str]:
    """Extract lowercased alphanumeric word tokens minus stop words."""
    words = re.findall(r"\b[a-z0-9]{3,}\b", text.lower())
    return {w for w in words if w not in STOP_WORDS}


def _jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard token overlap between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _detect_wire_attribution(text: str) -> Set[str]:
    """Detect mentioned wire agencies in text/snippet."""
    text_lower = text.lower()
    return {wire for wire in WIRE_SERVICES if wire in text_lower}


def cluster_sources_by_independence(
    candidates: List[SearchResultCandidate],
) -> Tuple[List[SourceCluster], List[SearchResultCandidate]]:
    """
    Cluster search result candidates using deterministic independence heuristics:
    1. Same root domain / canonical URL -> RELATED or DUPLICATE
    2. Near-identical headline/title -> SYNDICATED
    3. High snippet token overlap (>60%) -> SYNDICATED
    4. Shared wire attribution (e.g., both citing Reuters) -> SYNDICATED
    5. Distinct domains with independent text -> INDEPENDENT
    
    Returns:
        (clusters, updated_candidates_with_cluster_metadata)
    """
    if not candidates:
        return [], []

    # Working copy to annotate
    annotated: List[SearchResultCandidate] = [c.model_copy() for c in candidates]

    # Pre-tokenize titles and snippets
    tokenized_titles = [_tokenize(c.title) for c in annotated]
    tokenized_snippets = [_tokenize(c.snippet) for c in annotated]
    wire_tags = [_detect_wire_attribution(c.title + " " + c.snippet) for c in annotated]

    n = len(annotated)
    # cluster_assignment: index -> cluster_index
    cluster_map: List[int] = list(range(n))

    # Union-find or pairwise grouping
    def find_root(i: int) -> int:
        while cluster_map[i] != i:
            cluster_map[i] = cluster_map[cluster_map[i]]
            i = cluster_map[i]
        return i

    def union(i: int, j: int) -> None:
        root_i = find_root(i)
        root_j = find_root(j)
        if root_i != root_j:
            cluster_map[root_j] = root_i

    # Pairwise comparison
    pairwise_reasons: dict[Tuple[int, int], Tuple[IndependenceLevel, str]] = {}

    for i in range(n):
        for j in range(i + 1, n):
            c_i = annotated[i]
            c_j = annotated[j]

            # Heuristic 1: Exact or same root domain
            same_root = (c_i.root_domain and c_i.root_domain == c_j.root_domain)
            same_url = (c_i.url == c_j.url) or (c_i.canonical_url and c_i.canonical_url == c_j.canonical_url)

            # Heuristic 2: Title similarity
            title_sim = _jaccard_similarity(tokenized_titles[i], tokenized_titles[j])

            # Heuristic 3: Snippet similarity
            snippet_sim = _jaccard_similarity(tokenized_snippets[i], tokenized_snippets[j])

            # Heuristic 4: Wire service cross-attribution
            common_wires = wire_tags[i] & wire_tags[j]

            if same_url:
                union(i, j)
                pairwise_reasons[(i, j)] = ("DUPLICATE", f"Identical URL / canonical target: {c_i.url}")
            elif same_root:
                level = "DUPLICATE" if title_sim > 0.70 else "RELATED"
                union(i, j)
                pairwise_reasons[(i, j)] = (level, f"Shared root domain: {c_i.root_domain}")
            elif title_sim >= 0.70:
                union(i, j)
                pairwise_reasons[(i, j)] = ("SYNDICATED", f"Near-identical headlines (Jaccard similarity {title_sim:.2f})")
            elif snippet_sim >= 0.60:
                union(i, j)
                pairwise_reasons[(i, j)] = ("SYNDICATED", f"High text snippet similarity (Jaccard similarity {snippet_sim:.2f})")
            elif common_wires and (title_sim >= 0.40 or snippet_sim >= 0.35):
                union(i, j)
                wire_names = ", ".join(common_wires).upper()
                pairwise_reasons[(i, j)] = ("SYNDICATED", f"Shared wire service attribution ({wire_names})")

    # Group members into clusters
    groups: dict[int, List[int]] = {}
    for idx in range(n):
        root = find_root(idx)
        groups.setdefault(root, []).append(idx)

    clusters: List[SourceCluster] = []
    cluster_counter = 1

    for root, member_indices in groups.items():
        cluster_id = f"cluster-{cluster_counter}"
        cluster_counter += 1

        members = [annotated[idx] for idx in member_indices]

        # Select representative source: highest reliability score, then lowest rank
        representative = max(members, key=lambda m: (m.reliability_score, -m.rank))

        # Determine overall cluster independence level and explanation
        if len(members) == 1:
            ind_level: IndependenceLevel = "INDEPENDENT"
            reason = f"Unique reporting from {representative.domain} without detected syndication or domain duplication."
        else:
            # Check reasons among pairs
            found_levels = [
                pairwise_reasons.get((min(a, b), max(a, b)), ("RELATED", "Shared context"))[0]
                for a in member_indices for b in member_indices if a < b and (min(a, b), max(a, b)) in pairwise_reasons
            ]
            if "DUPLICATE" in found_levels:
                ind_level = "DUPLICATE"
                reason = f"Duplicate coverage on the same domain ({representative.root_domain}) or identical URL."
            elif "SYNDICATED" in found_levels:
                ind_level = "SYNDICATED"
                reason = "Syndicated content: outlets republishing the same press release or wire article."
            else:
                ind_level = "RELATED"
                reason = f"Multiple articles from related domain or organization ({representative.root_domain})."

        # Update candidate annotations
        for m in members:
            m.cluster_id = cluster_id
            m.independence_level = ind_level

        clusters.append(
            SourceCluster(
                cluster_id=cluster_id,
                representative_source=representative,
                member_sources=members,
                independence_level=ind_level,
                reason=reason,
            )
        )

    return clusters, annotated
