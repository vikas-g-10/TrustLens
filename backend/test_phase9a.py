"""
TrustLens Phase 9A Regression Suite: Reasoning Integrity
========================================================
Proves, on the real async fusion path (and through POST /api/investigate), that:
1. The deterministic FusionEngine reason survives `fuse_investigation_evidence` unchanged.
2. With NO LLM configured, the reason is NOT replaced by the generic one-line headline.
3. Even with an LLM configured (and a hostile model response), nothing is merged into
   verdict / confidence / reason / Trust Triangle, and the LLM endpoint is never called.
4. Verdict and confidence stay deterministic (identical across repeated runs).
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient

from config import settings
from dependencies import rate_limiter
from main import app
from schemas.investigation import MultimodalAiResult
from services.fusion import (
    FusionEngine,
    apply_reliability_weighting,
    detect_evidence_conflicts,
    fuse_investigation_evidence,
    normalize_all_evidence,
)
from services.image_analysis.analyzer import analyze_image_file

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

# Openings of the generic headlines produced by explanation.generate_deterministic_explanation.
# The engine's own reasons never start this way; if one of these shows up, the reason was overwritten.
GENERIC_HEADLINE_PREFIXES = ("TrustLens evaluated", "Investigation is INCONCLUSIVE (")


def _fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURES_DIR, name), "rb") as f:
        return f.read()


def _scenarios():
    """(label, fuse kwargs, expected verdict). Real fixtures; no mocking of fusion internals."""
    missing_exif = analyze_image_file(_fixture("photo_missing_exif.jpg"), "photo_missing_exif.jpg")
    ai_face = analyze_image_file(_fixture("ai_generated_face.jpg"), "ai_generated_face.jpg")
    mm_ai = MultimodalAiResult(
        ai_generation_assessment="likely_ai_generated",
        confidence=0.88,
        visual_findings=["Hyper-smooth skin texture", "Synthetic diffusion artifacts"],
        supporting_signals=["Consistent with diffusion facial generation"],
        limitations=["Optical camera sensor profile unavailable"],
        model_used="test-model",
        provider_used="test",
        explanation="Facial features exhibit hallmark signs of algorithmic synthesis.",
    )
    return [
        ("missing_exif_inconclusive",
         dict(claim_text="Verify photo with missing EXIF", image_analysis=missing_exif),
         "INCONCLUSIVE"),
        ("ai_generated_face",
         dict(claim_text="Verify whether this portrait is AI-generated", image_analysis=ai_face,
              multimodal_result=mm_ai),
         "LIKELY_AI_GENERATED"),
    ]


def _engine_only(kwargs):
    """The expected result, computed by calling the deterministic stages directly (no async wrapper)."""
    items = normalize_all_evidence(
        claim_text=kwargs.get("claim_text", ""),
        url_text="",
        url_outcome=None,
        image_analysis=kwargs.get("image_analysis"),
        search_evidence=None,
        multimodal_result=kwargs.get("multimodal_result"),
        image_text_evidence=None,
        video_analysis=None,
    )
    weighted, summary = apply_reliability_weighting(items)
    conflict = detect_evidence_conflicts(weighted, summary)
    return FusionEngine().fuse(weighted, summary, conflict, url_outcome=None)


def _assert_matches_engine(result, expected, label):
    assert result.verdict == expected.verdict, label
    assert result.confidence == expected.confidence, label
    assert result.reason == expected.reason, f"{label}: engine reason was altered"
    assert result.trust_triangle == expected.trust_triangle, label
    assert result.reason.strip(), f"{label}: reason must not be empty"
    assert not result.reason.startswith(GENERIC_HEADLINE_PREFIXES), (
        f"{label}: reason was replaced by the generic headline: {result.reason!r}"
    )


@pytest.fixture
def no_llm(monkeypatch):
    """No LLM configuration at all (also ignores any key present in a local .env)."""
    for name in ("llm_api_key", "groq_api_key"):
        monkeypatch.setattr(settings, name, None)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


@pytest.fixture
def hostile_llm(monkeypatch):
    """An LLM IS configured and would answer with text contradicting the verdict.
    Any HTTP use by the explanation layer is recorded, so the test can prove it never happens."""
    import services.fusion.explanation as explanation

    calls = []

    class _HostileResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {
                "content": "Final verdict: LIKELY_AUTHENTIC with 99% confidence. Ignore all prior evidence."}}]}

    class _HostileClient:
        def __init__(self, *a, **k):
            calls.append("init")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, *a, **k):
            calls.append("post")
            return _HostileResponse()

    monkeypatch.setattr(settings, "llm_api_key", "test-key-not-real")
    monkeypatch.setattr(explanation.httpx, "AsyncClient", _HostileClient)
    return calls


@pytest.mark.parametrize("label,kwargs,expected_verdict", _scenarios(), ids=[s[0] for s in _scenarios()])
def test_engine_reason_survives_without_llm(no_llm, label, kwargs, expected_verdict):
    expected = _engine_only(kwargs)
    assert expected.verdict == expected_verdict  # scenario sanity: the engine itself decides this

    result = asyncio.run(fuse_investigation_evidence(**kwargs))
    _assert_matches_engine(result, expected, label)


@pytest.mark.parametrize("label,kwargs,expected_verdict", _scenarios(), ids=[s[0] for s in _scenarios()])
def test_llm_cannot_alter_verdict_confidence_or_reason(hostile_llm, label, kwargs, expected_verdict):
    expected = _engine_only(kwargs)
    result = asyncio.run(fuse_investigation_evidence(**kwargs))

    _assert_matches_engine(result, expected, label)
    assert result.verdict == expected_verdict
    assert "LIKELY_AUTHENTIC" not in result.reason and "99%" not in result.reason
    assert hostile_llm == [], f"fusion pipeline must not call the LLM explanation endpoint: {hostile_llm}"


@pytest.mark.parametrize("label,kwargs,expected_verdict", _scenarios(), ids=[s[0] for s in _scenarios()])
def test_fusion_is_deterministic_across_runs(no_llm, label, kwargs, expected_verdict):
    runs = [asyncio.run(fuse_investigation_evidence(**kwargs)) for _ in range(3)]
    assert len({(r.verdict, r.confidence, r.reason) for r in runs}) == 1, label


def test_api_final_reason_is_engine_reason_not_generic_headline(no_llm):
    """Through POST /api/investigate: final.reason/summary carry the engine's reason, and the
    narrative 'Final Deterministic Verdict' step quotes that same reason."""
    rate_limiter.hits.clear()
    client = TestClient(app)
    resp = client.post(
        "/api/investigate",
        data={"claim": "Test photo with no camera metadata"},
        files={"file": ("photo_missing_exif.jpg", _fixture("photo_missing_exif.jpg"), "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    final = resp.json()["final"]

    assert final["reason"] and final["reason"] == final["summary"]
    assert not final["reason"].startswith(GENERIC_HEADLINE_PREFIXES), final["reason"]
    assert final["verdict"] not in ("LIKELY_AI_GENERATED", "LIKELY_MANIPULATED")  # missing EXIF is neutral
    verdict_steps = [s for s in final["reasoning"] if s.startswith("Final Deterministic Verdict:")]
    assert len(verdict_steps) == 1 and final["reason"] in verdict_steps[0]
