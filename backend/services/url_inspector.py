import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin, parse_qs
from typing import Dict, List, Optional, Set, Tuple

import httpx
from bs4 import BeautifulSoup

from backend.utils.ssrf_validator import (
    SSRFValidationError,
    validate_url_scheme_and_port,
    assert_safe_hostname,
    resolve_and_verify_destination,
)
from backend.schemas.investigation import (
    UrlAnalysisOutcome,
    UrlAnalysisOutcomeSuccess,
    UrlAnalysisOutcomeFailure,
    UrlAnalysisData,
    UrlAnalysisError,
)

# Operational limits (matching server/urlAnalysis.ts)
MAX_REDIRECTS = 5
TOTAL_TIMEOUT_SECONDS = 12.0
MAX_BODY_BYTES = 1_500_000      # 1.5 MB body limit
MAX_TEXT_CHARS = 6_000          # 6,000 chars visible text excerpt
USER_AGENT = "Mozilla/5.0 (compatible; TrustLensBot/1.0; evidence-investigation)"

TRACKING_EXACT = {
    'fbclid', 'gclid', 'dclid', 'gbraid', 'wbraid', 'msclkid', 'yclid', 'ttclid',
    'twclid', 'igshid', 'mc_cid', 'mc_eid', '_hsenc', '_hsmi', 'li_fat_id', 'srsltid', 'si'
}

SHORTENERS = {
    'bit.ly', 't.co', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd',
    'buff.ly', 'rebrand.ly', 'cutt.ly', 'shorturl.at', 'tiny.cc', 'rb.gy'
}

MULTI_SUFFIX_REGEX = re.compile(r'\.(co|com|org|net|gov|ac|edu|nic|res)\.[a-z]{2}$', re.IGNORECASE)


def normalize_input_url(raw: str) -> str:
    """Normalize input string into a standard HTTP/HTTPS URL."""
    trimmed = raw.strip()
    if not trimmed or len(trimmed) > 2048:
        raise SSRFValidationError("INVALID_URL", "The URL is empty or too long.")
    
    # Prepend https:// if no scheme is provided
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', trimmed):
        trimmed = f"https://{trimmed}"
        
    return trimmed


def registrable_domain(host: str) -> str:
    """Extract the effective second-level/registrable domain."""
    h = host.lower().removeprefix("www.")
    labels = h.split('.')
    if len(labels) <= 2:
        return h
    if MULTI_SUFFIX_REGEX.search(h):
        return '.'.join(labels[-3:])
    return '.'.join(labels[-2:])


def detect_tracking_parameters(urls: List[str]) -> List[str]:
    """Identify telemetry and tracking tokens across all URLs in the redirect chain."""
    found = set()
    for u in urls:
        try:
            parsed = urlparse(u)
            params = parse_qs(parsed.query)
            for k in params.keys():
                k_lower = k.lower()
                if k_lower.startswith('utm_') or k_lower in TRACKING_EXACT:
                    found.add(k_lower)
        except Exception:
            pass
    return sorted(list(found))


def detect_suspicious_structure(original_url: str, final_url: str) -> List[str]:
    """Apply structural heuristics to flag potential obfuscation or risk."""
    out: List[str] = []

    for u_str in (original_url, final_url):
        try:
            parsed = urlparse(u_str)
            host = (parsed.hostname or "").lower()
            clean_host = host.strip("[]")

            # Check if host is direct raw IP
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', clean_host) or ':' in clean_host:
                if "Host is a raw IP address" not in out:
                    out.append("Host is a raw IP address")

            # Punycode
            if any(part.startswith('xn--') for part in host.split('.')):
                if "Hostname uses punycode (possible look-alike characters)" not in out:
                    out.append("Hostname uses punycode (possible look-alike characters)")

            # Excessive subdomains
            if len(host.split('.')) > 5:
                if "Unusually many subdomain levels" not in out:
                    out.append("Unusually many subdomain levels")

            # High hyphen count
            if host.count('-') >= 3:
                if "Hostname contains many hyphens" not in out:
                    out.append("Hostname contains many hyphens")

            # Shortener domain
            bare_host = clean_host.removeprefix("www.")
            if bare_host in SHORTENERS:
                if "URL shortener domain" not in out:
                    out.append("URL shortener domain")

            # Long URL
            if len(u_str) > 250:
                if "Very long URL" not in out:
                    out.append("Very long URL")
        except Exception:
            pass

    return out


def extract_html_page_data(html_content: str, base_url: str) -> Dict[str, any]:
    """
    Parse HTML content and extract metadata safely using BeautifulSoup.
    
    TRUST BOUNDARY:
    All extracted text is strictly marked as UNTRUSTED WEB EVIDENCE.
    No script or active content is executed.
    """
    soup = BeautifulSoup(html_content[:MAX_BODY_BYTES], "html.parser")

    # Title extraction
    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()[:300]

    # Meta tags extraction
    meta_desc = None
    og_title = None
    site_name = None

    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        content = meta.get("content") or ""
        if not content:
            continue
        content_clean = content.strip()
        if name in ("description", "og:description") and not meta_desc:
            meta_desc = content_clean[:500]
        elif name == "og:title" and not og_title:
            og_title = content_clean[:200]
        elif name == "og:site_name" and not site_name:
            site_name = content_clean[:120]

    if not title and og_title:
        title = og_title

    # Canonical link
    canonical_url = None
    for link in soup.find_all("link"):
        rel = link.get("rel") or []
        if isinstance(rel, list):
            rel_str = " ".join(rel).lower()
        else:
            rel_str = str(rel).lower()
        if "canonical" in rel_str and link.get("href"):
            try:
                canonical_url = urljoin(base_url, link.get("href").strip())
            except Exception:
                pass
            break

    # Headings extraction (h1, h2, h3 up to 20 unique items)
    headings: List[str] = []
    for tag in soup.find_all(['h1', 'h2', 'h3']):
        h_text = ' '.join(tag.get_text().split()).strip()[:160]
        if h_text and h_text not in headings and len(headings) < 20:
            headings.append(h_text)

    # Visible text extraction (strip script, style, svg, iframe, noscript)
    for tag in soup(['script', 'style', 'noscript', 'template', 'svg', 'iframe', 'head']):
        tag.decompose()

    raw_text = soup.get_text(separator=' ')
    clean_text = ' '.join(raw_text.split()).strip()

    text_truncated = len(clean_text) > MAX_TEXT_CHARS
    visible_excerpt = clean_text[:MAX_TEXT_CHARS]

    return {
        "title": title,
        "metaDescription": meta_desc,
        "siteName": site_name,
        "canonicalUrl": canonical_url,
        "headings": headings,
        "visibleText": visible_excerpt,
        "textTruncated": text_truncated,
        "trustBoundary": "UNTRUSTED WEB EVIDENCE"
    }


async def inspect_url(raw_url: str) -> UrlAnalysisOutcome:
    """
    Perform a complete, safe, SSRF-protected URL inspection.
    
    1. Validates scheme and port.
    2. Resolves DNS and blocks internal/private/loopback/cloud metadata IPs.
    3. Traverses redirects manually, re-validating EVERY hop against SSRF rules.
    4. Enforces strict timeouts and body limits.
    5. Extracts structured metadata and returns UrlAnalysisOutcome.
    """
    try:
        normalized = normalize_input_url(raw_url)
        parsed = urlparse(normalized)
        
        # Security validation on initial target: validate scheme & port first
        port = validate_url_scheme_and_port(parsed)
        assert_safe_hostname(parsed.hostname or "")
        resolve_and_verify_destination(parsed.hostname or "", port)

        start_time = time.time()
        deadline = start_time + TOTAL_TIMEOUT_SECONDS
        chain: List[str] = [normalized]
        current_url = normalized
        current_parsed = parsed

        final_response: Optional[httpx.Response] = None
        final_body = b""

        # Manual redirect traversal loop
        async with httpx.AsyncClient(
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.5",
                "Accept-Language": "en",
            },
            verify=True,
        ) as client:
            for redirect_count in range(MAX_REDIRECTS + 1):
                remaining_time = max(0.5, deadline - time.time())
                if remaining_time <= 0:
                    raise SSRFValidationError("TIMEOUT", "The request timed out.")

                try:
                    res = await client.get(
                        current_url,
                        follow_redirects=False,
                        timeout=remaining_time,
                    )
                except httpx.TimeoutException:
                    raise SSRFValidationError("TIMEOUT", "The request timed out.")
                except httpx.ConnectError as e:
                    raise SSRFValidationError("NETWORK_ERROR", f"Could not connect to server ({str(e)}).")
                except Exception as e:
                    raise SSRFValidationError("NETWORK_ERROR", f"Network error during retrieval: {str(e)}.")

                # Handle HTTP redirect (3xx)
                if res.status_code in (301, 302, 303, 307, 308) and "location" in res.headers:
                    if redirect_count >= MAX_REDIRECTS:
                        raise SSRFValidationError("TOO_MANY_REDIRECTS", f"More than {MAX_REDIRECTS} redirects.")

                    location = res.headers["location"]
                    try:
                        next_url = urljoin(current_url, location)
                        next_parsed = urlparse(next_url)
                    except Exception:
                        raise SSRFValidationError("INVALID_URL", "A redirect pointed to an invalid URL.")

                    # Re-validate EVERY redirect destination before following
                    next_port = validate_url_scheme_and_port(next_parsed)
                    assert_safe_hostname(next_parsed.hostname or "")
                    resolve_and_verify_destination(next_parsed.hostname or "", next_port)

                    chain.append(next_url)
                    current_url = next_url
                    current_parsed = next_parsed
                    continue

                # Final response reached
                final_response = res
                final_body = res.content[:MAX_BODY_BYTES]
                break

        if not final_response:
            raise SSRFValidationError("NETWORK_ERROR", "No response received.")

        if final_response.status_code >= 400:
            raise SSRFValidationError(
                "HTTP_ERROR",
                f"The server responded with HTTP {final_response.status_code}.",
                status_code=final_response.status_code
            )

        content_type_raw = final_response.headers.get("content-type", "")
        content_type_clean = content_type_raw.split(";")[0].strip().lower()
        if content_type_clean and not any(ct in content_type_clean for ct in ("text/html", "application/xhtml+xml", "text/plain")):
            raise SSRFValidationError("UNSUPPORTED_CONTENT", f"The URL returned non-page content ({content_type_clean}).")

        # Decode HTML body safely
        encoding = final_response.encoding or "utf-8"
        try:
            html_text = final_body.decode(encoding, errors="replace")
        except Exception:
            html_text = final_body.decode("utf-8", errors="replace")

        page_data = extract_html_page_data(html_text, current_url)

        orig_host = parsed.hostname or ""
        final_host = current_parsed.hostname or ""
        domain_mismatch = registrable_domain(orig_host) != registrable_domain(final_host)

        analysis_data = UrlAnalysisData(
            original_url=normalized,
            final_url=current_url,
            original_domain=orig_host,
            final_domain=final_host,
            https=current_parsed.scheme == "https",
            redirect_count=len(chain) - 1,
            redirect_chain=chain,
            domain_mismatch=domain_mismatch,
            status_code=final_response.status_code,
            content_type=content_type_clean or "unknown",
            title=page_data.get("title"),
            meta_description=page_data.get("metaDescription"),
            site_name=page_data.get("siteName"),
            headings=page_data.get("headings", []),
            canonical_url=page_data.get("canonicalUrl"),
            visible_text=page_data.get("visibleText", ""),
            text_truncated=page_data.get("textTruncated", False),
            tracking_params=detect_tracking_parameters(chain),
            suspicious_structure=detect_suspicious_structure(normalized, current_url),
            fetched_at=datetime.now(timezone.utc).isoformat()
        )

        return UrlAnalysisOutcomeSuccess(ok=True, data=analysis_data)

    except SSRFValidationError as e:
        return UrlAnalysisOutcomeFailure(
            ok=False,
            error=UrlAnalysisError(code=e.code, message=e.message, status_code=e.status_code)
        )
    except Exception as e:
        return UrlAnalysisOutcomeFailure(
            ok=False,
            error=UrlAnalysisError(code="NETWORK_ERROR", message=f"Unexpected error while retrieving the URL: {str(e)}")
        )
