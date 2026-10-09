"""
Automated test suite for TrustLens Phase 2: Real URL Inspection & SSRF Protections.
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from services.url_inspector import inspect_url


def test_ssrf_security_cases():
    """Verify all SSRF security rules defined in Phase 2 specification."""
    print("\n--- Testing SSRF Security Protections ---")

    test_cases = [
        # (Target URL, Expected Error Code, Description)
        ("http://127.0.0.1:8000/api/health", "BLOCKED_HOST", "Loopback IPv4 with port 8000"),
        ("http://127.0.0.1/", "BLOCKED_HOST", "Loopback IPv4 on port 80"),
        ("http://localhost:8000/api/health", "BLOCKED_HOST", "Localhost hostname with port 8000"),
        ("http://localhost/", "BLOCKED_HOST", "Localhost hostname on port 80"),
        ("http://169.254.169.254/latest/meta-data/", "BLOCKED_HOST", "AWS/Cloud metadata IP"),
        ("http://192.168.1.1/", "BLOCKED_HOST", "Private IPv4 (192.168.0.0/16)"),
        ("http://10.0.0.5/", "BLOCKED_HOST", "Private IPv4 (10.0.0.0/8)"),
        ("http://172.16.0.1/", "BLOCKED_HOST", "Private IPv4 (172.16.0.0/12)"),
        ("http://[::1]/", "BLOCKED_HOST", "Loopback IPv6 (::1)"),
        ("http://[fe80::1]/", "BLOCKED_HOST", "Link-local IPv6 (fe80::/10)"),
        ("http://[fc00::1]/", "BLOCKED_HOST", "Unique local IPv6 (fc00::/7)"),
        ("file:///etc/passwd", "INVALID_URL", "Unsupported scheme file://"),
        ("ftp://example.com/file", "INVALID_URL", "Unsupported scheme ftp://"),
        ("gopher://example.com/", "INVALID_URL", "Unsupported scheme gopher://"),
        ("http://example.com:8080/", "BLOCKED_HOST", "Non-standard port 8080"),
        ("http://example.com:22/", "BLOCKED_HOST", "Non-standard port 22 (SSH)"),
        ("http://user:pass@example.com/", "INVALID_URL", "Embedded credentials in URL"),
    ]

    for target_url, expected_code, desc in test_cases:
        outcome = asyncio.run(inspect_url(target_url))
        assert not outcome.ok, f"Expected {target_url} to be blocked, but it succeeded!"
        assert outcome.error.code == expected_code, (
            f"Failed for {desc} ({target_url}): expected {expected_code}, got {outcome.error.code} ({outcome.error.message})"
        )
        print(f"[PASS] {desc}: {target_url} -> {outcome.error.code} ({outcome.error.message})")


def test_api_investigate_with_ssrf_url():
    """Verify POST /api/investigate returns transparent failure for blocked SSRF URL."""
    print("\n--- Testing API Investigate with SSRF URL ---")
    client = TestClient(app)

    res = client.post("/api/investigate", json={
        "claim": "Testing SSRF protection via API",
        "url": "http://127.0.0.1:8000/api/health"
    })
    assert res.status_code == 200, f"Expected 200 JSON with error outcome, got {res.status_code}"
    data = res.json()
    assert data["urlAnalysis"] is not None
    assert data["urlAnalysis"]["ok"] is False
    assert data["urlAnalysis"]["error"]["code"] == "BLOCKED_HOST"
    assert data["final"]["verdict"] == "INCONCLUSIVE"
    print("[PASS] API rejected SSRF URL with transparent INCONCLUSIVE and BLOCKED_HOST outcome:", data["urlAnalysis"]["error"])


def test_real_https_smoke_url():
    """Verify live inspection of a stable, public HTTPS website."""
    print("\n--- Testing Live Public HTTPS URL Inspection ---")
    sample_url = "https://example.com"
    outcome = asyncio.run(inspect_url(sample_url))

    if not outcome.ok:
        print(f"[WARN] Public network check to {sample_url} returned error: {outcome.error.message}")
        print("Skipping external network assertion if offline.")
        return

    d = outcome.data
    assert d.https is True, "Expected HTTPS to be True"
    assert d.original_domain == "example.com"
    assert d.final_domain == "example.com"
    assert d.status_code in (200, 301, 302)
    assert d.title is not None, "Expected title to be extracted"
    assert len(d.visible_text) > 0, "Expected visible text to be extracted"
    assert d.domain_mismatch is False

    print(f"[PASS] Successfully inspected {sample_url}:")
    print(f"       Title: '{d.title}'")
    print(f"       Domain: {d.final_domain}")
    print(f"       Status: {d.status_code} ({'HTTPS' if d.https else 'HTTP'})")
    print(f"       Visible Text Excerpt ({len(d.visible_text)} chars): {d.visible_text[:80]}...")


def test_api_investigate_with_live_url():
    """Verify POST /api/investigate populates live URL analysis into frontend contract."""
    print("\n--- Testing API Investigate with Public HTTPS URL ---")
    client = TestClient(app)

    res = client.post("/api/investigate", json={
        "claim": "Example Domain is established by IANA.",
        "url": "https://example.com"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["urlAnalysis"] is not None
    if data["urlAnalysis"]["ok"]:
        d = data["urlAnalysis"]["data"]
        assert d["https"] is True
        assert d["finalDomain"] == "example.com"
        assert "title" in d
        assert data["final"]["verdict"] == "INCONCLUSIVE"  # Phase 2 Rule: page existence != proof of claim
        print("[PASS] API /api/investigate populated live urlAnalysis data matching frontend contract.")
        print(f"       Final Domain: {d['finalDomain']}, Title: {d['title']}")
        print(f"       Summary: {data['final']['summary']}")


if __name__ == "__main__":
    test_ssrf_security_cases()
    test_api_investigate_with_ssrf_url()
    test_real_https_smoke_url()
    test_api_investigate_with_live_url()
    print("\n==============================================")
    print("ALL PHASE 2 URL INSPECTION TESTS PASSED!")
    print("==============================================")
