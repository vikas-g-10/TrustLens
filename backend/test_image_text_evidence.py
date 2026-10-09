"""
TrustLens - Image Text -> Claim Evidence tests
==============================================
1. Image text directly supports the claim            -> SUPPORTS
2. Image text contradicts the claim                  -> CONTRADICTS (location / number)
3. Image text partially supports the claim           -> PARTIALLY_SUPPORTS
4. Image text unrelated to the claim                 -> UNRELATED
5. Poor OCR                                          -> INSUFFICIENT_TEXT
6. Real Phase 4 OCR on a rendered image (skipped if Tesseract is not installed)
7. Fusion: IMAGE_TEXT evidence item, OCR quality scales trust, verdict unchanged
8. POST /api/investigate returns imageTextEvidence (Phase 4 OCR output injected)
"""
import io
import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from dependencies import rate_limiter
from main import app
from schemas.image_analysis import OcrResult
from services.fusion import fuse_investigation_evidence
from services.image_analysis.image_text_evidence import compare_image_text_to_claim
from services.image_analysis.ocr import extract_ocr_text, _resolve_tesseract_binary

client = TestClient(app)
CLAIM = "Government X announced a new ₹5000 subsidy."


def ocr(text: str, conf: float = 92.0, **kw) -> OcrResult:
    """Build an OcrResult exactly as the Phase 4 OCR returns it."""
    quality = "high" if conf >= 80 else "moderate" if conf >= 50 else "low"
    return OcrResult(status="SUCCESS", available=True, ocr_quality=quality, text=text,
                     confidence=conf, regions_count=1, **kw)


def test_1_supports():
    r = compare_image_text_to_claim(
        ocr("Government X announces ₹5000 subsidy for farmers from January 2027."), CLAIM)
    assert r.relationship == "SUPPORTS"
    assert any("₹5000" in p for p in r.matched_claim_points)
    assert not r.contradicted_claim_points and not r.missing_claim_points
    assert "not whether it is true" in r.explanation      # text is evidence, not proof
    assert r.source == "uploaded_image" and r.ocr_quality == 0.92


def test_2_contradicts_location_and_number():
    claim = "Event X happened in Delhi on 10 March."
    r = compare_image_text_to_claim(ocr("Event X happened in Mumbai on 10 March."), claim)
    assert r.relationship == "CONTRADICTS"
    assert any("Delhi" in p and "Mumbai" in p for p in r.contradicted_claim_points)
    assert any("10 March" in p for p in r.matched_claim_points)       # date still matches

    r2 = compare_image_text_to_claim(ocr("Government X announces ₹7,500 subsidy for farmers"), CLAIM)
    assert r2.relationship == "CONTRADICTS"
    assert any("5000" in p and "7,500" in p for p in r2.contradicted_claim_points)


def test_3_partially_supports():
    r = compare_image_text_to_claim(ocr("Event X happened"), "Event X happened in Delhi on 10 March.")
    assert r.relationship == "PARTIALLY_SUPPORTS"
    assert any("Event X" in p for p in r.matched_claim_points)
    assert any("Delhi" in p for p in r.missing_claim_points)
    assert any("10 March" in p for p in r.missing_claim_points)


def test_4_unrelated():
    r = compare_image_text_to_claim(
        ocr("Petrol prices rose sharply in Mumbai this week as crude oil hit new highs."), CLAIM)
    assert r.relationship == "UNRELATED"
    assert not r.matched_claim_points


def test_5_poor_ocr_is_insufficient():
    low = compare_image_text_to_claim(ocr("Gvt Xx anno ,, subs 5o0 ~~ l", conf=31.0), CLAIM)
    assert low.relationship == "INSUFFICIENT_TEXT" and low.ocr_quality == 0.31
    unavailable = compare_image_text_to_claim(
        OcrResult(status="UNAVAILABLE", available=False, ocr_quality="unavailable", text=""), CLAIM)
    assert unavailable.relationship == "INSUFFICIENT_TEXT"
    empty = compare_image_text_to_claim(
        OcrResult(status="NO_TEXT_DETECTED", available=True, ocr_quality="not_applicable", text=""), CLAIM)
    assert empty.relationship == "INSUFFICIENT_TEXT"


def test_debunk_cue_is_contradiction_not_truth():
    r = compare_image_text_to_claim(
        ocr("FAKE NEWS: Government X announces ₹5000 subsidy. Fact check: no such scheme."), CLAIM)
    assert r.relationship == "CONTRADICTS"
    assert any(p.startswith("denial") for p in r.contradicted_claim_points)


@pytest.mark.skipif(_resolve_tesseract_binary() is None, reason="Tesseract OCR not installed")
def test_6_real_phase4_ocr():
    img = Image.new("RGB", (1400, 220), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=52)
    except TypeError:                       # very old Pillow
        font = ImageFont.load_default()
    d.text((30, 70), "Government X announces Rs 5000 subsidy for farmers", fill="black", font=font)
    res = extract_ocr_text(img)             # the EXISTING Phase 4 OCR
    assert res.status == "SUCCESS"
    r = compare_image_text_to_claim(res, "Government X announced a new Rs 5000 subsidy.")
    assert r.relationship in ("SUPPORTS", "PARTIALLY_SUPPORTS"), (r.relationship, res.text)
    assert r.ocr_quality > 0.5


def test_7_fusion_evidence_item_and_quality_effect():
    from schemas.investigation import ImageTextEvidence
    import asyncio

    def run(ite):
        return asyncio.run(fuse_investigation_evidence(claim_text=CLAIM, image_text_evidence=ite))

    good = compare_image_text_to_claim(
        ocr("Government X announces ₹5000 subsidy for farmers", conf=95.0), CLAIM)
    ok = compare_image_text_to_claim(
        ocr("Government X announces ₹5000 subsidy for farmers", conf=60.0), CLAIM)
    base = run(None)
    hi, mid = run(good), run(ok)

    item = next(i for i in hi.normalized_evidence if i.evidence_type == "IMAGE_TEXT")
    assert item.direction == "SUPPORTS" and item.source == "uploaded_image"
    assert item.provenance["relationship"] == "SUPPORTS"
    w_hi = item.weight
    w_mid = next(i for i in mid.normalized_evidence if i.evidence_type == "IMAGE_TEXT").weight
    assert w_hi > w_mid > 0, "higher OCR quality must give the evidence more weight"

    # Neutral relationships carry no weight
    unrelated = compare_image_text_to_claim(ocr("Petrol prices rose sharply in Mumbai this week."), CLAIM)
    n = next(i for i in run(unrelated).normalized_evidence if i.evidence_type == "IMAGE_TEXT")
    assert n.direction == "UNRELATED" and n.weight == 0.0

    # Does not change the existing verdict / trust triangle
    assert hi.verdict == base.verdict
    assert hi.trust_triangle == base.trust_triangle
    assert hi.conflict.severity == base.conflict.severity


def test_8_api_returns_image_text_evidence(monkeypatch):
    import services.image_analysis.analyzer as analyzer
    monkeypatch.setattr(
        analyzer, "extract_ocr_text",
        lambda img: ocr("Government X announces ₹5000 subsidy for farmers from January 2027."))
    rate_limiter.hits.clear()
    buf = io.BytesIO()
    Image.new("RGB", (400, 300), (200, 180, 160)).save(buf, "JPEG")
    resp = client.post("/api/investigate", data={"claim": CLAIM},
                       files={"file": ("poster.jpg", buf.getvalue(), "image/jpeg")})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    ite = body["imageTextEvidence"]
    assert ite["relationship"] == "SUPPORTS" and ite["source"] == "uploaded_image"
    assert "matchedClaimPoints" in ite and "ocrQuality" in ite
    assert any(e["evidenceType"] == "IMAGE_TEXT" for e in body["normalizedEvidence"])

    # No user claim -> no comparison (the placeholder claim must not be compared)
    rate_limiter.hits.clear()
    resp2 = client.post("/api/investigate", files={"file": ("poster.jpg", buf.getvalue(), "image/jpeg")})
    assert resp2.status_code == 200
    assert resp2.json().get("imageTextEvidence") is None
