"""
Source Reliability Scorer for TrustLens Phase 3.

EPISTEMIC NOTICE:
- Search results are candidate evidence only.
- Source reliability is heuristic.
- Source independence is heuristic.
- No search result alone determines the final verdict.
- The final decision will be performed later by Evidence Fusion.

Transparent, deterministic, and explainable scoring of web candidate sources.
Every score has explicit factors (PASS, FAIL, UNKNOWN) and explanations.
Unknown factors are explicitly marked UNKNOWN, never assumed FALSE.
"""
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


# Official and High-Credibility Domain Sets
GOVERNMENT_DOMAINS_OR_TLDS = {
    ".gov", ".gov.in", ".nic.in", ".gov.uk", ".europa.eu",
    ".who.int", ".un.org", ".nasa.gov", ".nih.gov", ".cdc.gov",
    ".isro.gov.in", ".pib.gov.in", ".mil"
}

EDUCATIONAL_DOMAINS_OR_TLDS = {
    ".edu", ".ac.in", ".ac.uk", ".edu.au", ".edu.sg",
    "nature.com", "science.org", "thelancet.com", "arxiv.org", "biorxiv.org"
}

ESTABLISHED_NEWS_OR_FACTCHECK = {
    "reuters.com", "apnews.com", "afp.com", "bbc.com", "bbc.co.uk",
    "bloomberg.com", "thehindu.com", "indianexpress.com", "ndtv.com",
    "nytimes.com", "washingtonpost.com", "wsj.com", "theguardian.com",
    "aljazeera.com", "snopes.com", "politifact.com", "altnews.in",
    "boomlive.in", "factcheck.org", "fullfact.org", "poynter.org",
    "thewire.in", "scroll.in", "livemint.com", "economictimes.indiatimes.com"
}

SUSPICIOUS_TLDS = {
    ".top", ".click", ".buzz", ".gq", ".tk", ".ml", ".cf",
    ".country", ".stream", ".loan", ".work", ".rest", ".fit",
    ".tk", ".cc", ".icu", ".monster"
}

TRACKING_PARAM_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid"
}


def get_root_domain(domain: str) -> str:
    """
    Extract registered/root domain (e.g., news.bbc.co.uk -> bbc.co.uk, www.nytimes.com -> nytimes.com).
    """
    parts = domain.lower().strip().split(".")
    if len(parts) <= 2:
        return ".".join(parts)

    # Multi-part ccTLD handling
    two_part_tlds = {
        "co.uk", "gov.uk", "ac.uk", "gov.in", "nic.in", "ac.in", "co.in",
        "com.au", "gov.au", "edu.au", "co.nz", "com.br", "co.za", "co.jp"
    }
    last_two = ".".join(parts[-2:])
    if last_two in two_part_tlds and len(parts) >= 3:
        return ".".join(parts[-3:])

    return ".".join(parts[-2:])


def evaluate_source_reliability(
    url: str,
    title: str = "",
    snippet: str = "",
    content_accessible: Optional[bool] = None,
    published_date: Optional[str] = None,
) -> Tuple[int, Dict[str, str], List[str]]:
    """
    Deterministic, explainable source reliability scorer.
    
    Returns:
        (score, factors_dict, explanations_list)
        
    Score range: 5 to 95 (never 100% false certainty or 0% absolute nihilism).
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.lower()
    query = parsed.query.lower()

    root_domain = get_root_domain(netloc)
    factors: Dict[str, str] = {}
    explanations: List[str] = []

    # 1. HTTPS Protocol
    if scheme == "https":
        factors["HTTPS"] = "PASS"
        explanations.append("HTTPS: PASS (Encrypted transport).")
        https_delta = 10
    elif scheme == "http":
        factors["HTTPS"] = "FAIL"
        explanations.append("HTTPS: FAIL (Unencrypted connection).")
        https_delta = -20
    else:
        factors["HTTPS"] = "UNKNOWN"
        explanations.append(f"HTTPS: UNKNOWN (Non-standard scheme '{scheme}').")
        https_delta = -15

    # 2. Domain Authority / Type
    is_gov = any(netloc.endswith(tld) for tld in GOVERNMENT_DOMAINS_OR_TLDS)
    is_edu = any(netloc.endswith(tld) for tld in EDUCATIONAL_DOMAINS_OR_TLDS) or root_domain in EDUCATIONAL_DOMAINS_OR_TLDS
    is_news = root_domain in ESTABLISHED_NEWS_OR_FACTCHECK or any(netloc.endswith("." + n) for n in ESTABLISHED_NEWS_OR_FACTCHECK)

    if is_gov:
        factors["Domain type"] = "GOVERNMENT"
        explanations.append("Domain type: GOVERNMENT (Official public institution/government indicator).")
        domain_delta = 30
    elif is_edu:
        factors["Domain type"] = "EDUCATIONAL"
        explanations.append("Domain type: EDUCATIONAL (Academic or scientific institution indicator).")
        domain_delta = 25
    elif is_news:
        factors["Domain type"] = "ESTABLISHED_NEWS"
        explanations.append("Domain type: ESTABLISHED_NEWS (Recognized major press agency, newsroom, or fact-check organization).")
        domain_delta = 25
    else:
        factors["Domain type"] = "GENERAL"
        explanations.append(f"Domain type: GENERAL (Standard commercial or public domain: {root_domain}).")
        domain_delta = 0

    # 3. Suspicious Domain Characteristics & Structure
    is_suspicious_tld = any(netloc.endswith(tld) for tld in SUSPICIOUS_TLDS)
    is_punycode = "xn--" in netloc
    is_ip = bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", netloc))
    excessive_subdomains = netloc.count(".") >= 4

    suspicious_reasons = []
    if is_suspicious_tld:
        suspicious_reasons.append("high-risk TLD")
    if is_punycode:
        suspicious_reasons.append("punycode/IDN spoofing potential")
    if is_ip:
        suspicious_reasons.append("numeric IP address hostname")
    if excessive_subdomains:
        suspicious_reasons.append("excessive nested subdomains")

    if suspicious_reasons:
        factors["Suspicious URL structure"] = "FAIL"
        explanations.append(f"Suspicious URL structure: FAIL ({', '.join(suspicious_reasons)}).")
        struct_delta = -30
    else:
        factors["Suspicious URL structure"] = "PASS"
        explanations.append("Suspicious URL structure: PASS (Standard domain structure).")
        struct_delta = 5

    # 4. Excessive Tracking Parameters
    query_params = [q.split("=")[0] for q in query.split("&") if q]
    tracking_found = [p for p in query_params if p in TRACKING_PARAM_KEYS]
    if len(tracking_found) >= 3:
        factors["Tracking parameters"] = "FAIL"
        explanations.append(f"Tracking parameters: FAIL ({len(tracking_found)} tracking tokens detected).")
        track_delta = -10
    else:
        factors["Tracking parameters"] = "PASS"
        explanations.append("Tracking parameters: PASS (No excessive tracking parameters).")
        track_delta = 0

    # 5. Author / Byline Indicator
    # Look for "By <Name>" or "Author:" in title or snippet
    author_pattern = re.search(r"\b(?:by|author|reported by|written by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})", snippet + " " + title, re.IGNORECASE)
    if author_pattern:
        factors["Author"] = "PASS"
        explanations.append(f"Author: PASS (Byline pattern detected: '{author_pattern.group(1)}').")
        author_delta = 5
    else:
        # Crucial Requirement 5: UNKNOWN, NOT FALSE!
        factors["Author"] = "UNKNOWN"
        explanations.append("Author: UNKNOWN (No explicit byline identified in retrieved snippet).")
        author_delta = 0

    # 6. Publication Date
    # Check published_date arg or search snippet for dates (e.g. 2026, Oct 5, 2025, etc.)
    has_date = bool(published_date) or bool(re.search(r"\b(20\d\d[-/]\d\d[-/]\d\d|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+20\d\d)\b", snippet, re.IGNORECASE))
    if has_date:
        factors["Publication date"] = "PASS"
        date_str = published_date or "Detected in source snippet"
        explanations.append(f"Publication date: PASS ({date_str}).")
        date_delta = 5
    else:
        # Crucial Requirement 5: UNKNOWN, NOT FALSE!
        factors["Publication date"] = "UNKNOWN"
        explanations.append("Publication date: UNKNOWN (Publication timestamp not provided in search snippet).")
        date_delta = 0

    # 7. Content Accessibility
    if content_accessible is True:
        factors["Content accessible"] = "PASS"
        explanations.append("Content accessible: PASS (Page content was verified via HTTP).")
        content_delta = 5
    elif content_accessible is False:
        factors["Content accessible"] = "FAIL"
        explanations.append("Content accessible: FAIL (Page was unreachable or returned error).")
        content_delta = -15
    else:
        factors["Content accessible"] = "UNKNOWN"
        explanations.append("Content accessible: UNKNOWN (Page body was not fetched; snippet evaluation only).")
        content_delta = 0

    # Calculate Total Score from Base 50
    raw_score = 50 + https_delta + domain_delta + struct_delta + track_delta + author_delta + date_delta + content_delta
    # Clamp to [5, 95] to prevent 100% false certainty or 0% absolute nihilism
    final_score = max(5, min(95, raw_score))

    return final_score, factors, explanations
