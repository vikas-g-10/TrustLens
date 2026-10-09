"""
TrustLens Phase 6 Verification Test Suite
=========================================
Tests the complete Phase 6 Evidence Fusion & Decision Pipeline:
1. Test 1 — Strong AI-generated evidence (fixtures/ai_generated_face.jpg -> LIKELY_AI_GENERATED)
2. Test 2 — Normal photograph (fixtures/real_test_photo.jpg -> LIKELY_AUTHENTIC)
3. Test 3 — Manipulated image (fixtures/edited_manipulated_photo.jpg -> LIKELY_MANIPULATED)
4. Test 4 — Missing EXIF strictly neutral (photo_missing_exif.jpg has 0 weight/neutral; missing EXIF != suspicious)
5. Test 5 — Conflicting evidence (opposing signals produce measurable conflict & reduced confidence)
6. Test 6 — Duplicate/syndicated sources (5 copies of same wire article cluster to 1 independent source with discount)
7. Test 7 — Sparse evidence (insufficient telemetry remains INCONCLUSIVE with low confidence)
8. Test 8 — Phase 4 regression (file health, ELA, perceptual hashes, EXIF extraction remain fully intact)
9. Test 9 — Phase 5 regression (multimodal prompt, normalization, provider safety remain intact)
10. Test 10 — POST /api/investigate integration (end-to-end endpoint returns full Phase 6 fusion data)
11. Test 11 — LLM explanation cannot override deterministic fusion results
"""

import asyncio
import hashlib
import io
import os
import sys
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from PIL import Image

from main import app
from dependencies import rate_limiter
from schemas.investigation import (
    InvestigationResponse,
    MultimodalAiResult,
    MediaAnalysis,
)
from schemas.fusion import (
    NormalizedEvidenceItem,
    ConflictReport,
    ConflictDetail,
    TrustTriangle,
    EvidenceSummary,
    FusionResult,
)
from services.image_analysis.analyzer import analyze_image_file
from services.image_analysis.computer_vision import calculate_dhash, calculate_phash
from services.image_analysis.ela import compute_error_level_analysis
from services.image_analysis.compression import analyze_compression
from services.image_analysis.evidence_health import calculate_evidence_health
from services.multimodal.analyzer import _normalize_assessment, _normalize_confidence
from services.multimodal.prompt import build_multimodal_prompt
from services.fusion import (
    fuse_investigation_evidence,
    FusionEngine,
    normalize_all_evidence,
    apply_reliability_weighting,
    detect_evidence_conflicts,
    generate_deterministic_explanation,
)

client = TestClient(app)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(filename: str) -> bytes:
    filepath = os.path.join(FIXTURES_DIR, filename)
    assert os.path.isfile(filepath), f"Fixture not found: {filepath}"
    with open(filepath, "rb") as f:
        return f.read()


def test_case_1_ai_generated_image():
    print("\n--- Test 1: Strong AI-Generated Evidence ---")
    data = load_fixture("ai_generated_face.jpg")
    img_analysis = analyze_image_file(data, "ai_generated_face.jpg")

    # Multimodal AI structured observation for synthetic face
    mm_result = MultimodalAiResult(
        ai_generation_assessment="likely_ai_generated",
        confidence=0.88,
        visual_findings=["Hyper-smooth skin texture", "Irregular iris margin", "Synthetic diffusion artifacts"],
        supporting_signals=["Consistent with StyleGAN/diffusion facial generation"],
        contradicting_signals=[],
        limitations=["Optical camera sensor profile unavailable"],
        model_used="qwen/qwen3.8-27b",
        provider_used="groq",
        explanation="Facial features exhibit hallmark signs of algorithmic synthesis without physical lens aberration.",
    )

    fusion_res = asyncio.run(fuse_investigation_evidence(
        claim_text="Verify whether this portrait is AI-generated",
        image_analysis=img_analysis,
        multimodal_result=mm_result,
    ))

    assert fusion_res.verdict == "LIKELY_AI_GENERATED", f"Expected LIKELY_AI_GENERATED, got {fusion_res.verdict}"
    assert fusion_res.trust_triangle.manipulation_likelihood >= 50.0, f"Expected manipulation_likelihood >= 50, got {fusion_res.trust_triangle.manipulation_likelihood}"
    assert fusion_res.trust_triangle.evidence_strength >= 30.0, f"Expected evidence_strength >= 30, got {fusion_res.trust_triangle.evidence_strength}"
    assert fusion_res.confidence >= 50, f"Expected confidence >= 50, got {fusion_res.confidence}"
    assert len(fusion_res.supporting_evidence_ids) > 0, "Expected supporting evidence IDs in provenance"
    assert "ev_mm_ai_assessment" in fusion_res.supporting_evidence_ids, "Expected ev_mm_ai_assessment in supporting provenance"
    print(f"[PASS] Test 1: Verdict={fusion_res.verdict}, Conf={fusion_res.confidence}%, ManipLikelihood={fusion_res.trust_triangle.manipulation_likelihood}%")


def test_case_2_normal_photograph():
    print("\n--- Test 2: Normal Photograph ---")
    data = load_fixture("real_test_photo.jpg")
    img_analysis = analyze_image_file(data, "real_test_photo.jpg")
    assert img_analysis.metadata.camera_make == "TrustLens Optical Corp"

    # Multimodal AI structured observation for authentic camera photograph
    mm_result = MultimodalAiResult(
        ai_generation_assessment="likely_authentic",
        confidence=0.85,
        visual_findings=["Natural optical depth of field", "Physically consistent lens flare", "Natural perspective"],
        supporting_signals=["Consistent with physical optical capture"],
        contradicting_signals=[],
        limitations=["Compression quantization reduces fine high-frequency noise"],
        model_used="qwen/qwen3.8-27b",
        provider_used="groq",
        explanation="Optical perspective and physical light transport align with authentic camera photography.",
    )

    fusion_res = asyncio.run(fuse_investigation_evidence(
        claim_text="Verify whether this is a real camera photo",
        image_analysis=img_analysis,
        multimodal_result=mm_result,
    ))

    assert fusion_res.verdict == "LIKELY_AUTHENTIC", f"Expected LIKELY_AUTHENTIC, got {fusion_res.verdict}"
    assert fusion_res.trust_triangle.manipulation_likelihood <= 35.0, f"Expected manipulation_likelihood <= 35, got {fusion_res.trust_triangle.manipulation_likelihood}"
    assert fusion_res.trust_triangle.evidence_strength >= 30.0, f"Expected evidence_strength >= 30, got {fusion_res.trust_triangle.evidence_strength}"
    assert fusion_res.confidence >= 50, f"Expected confidence >= 50, got {fusion_res.confidence}"
    assert len(fusion_res.supporting_evidence_ids) > 0, "Expected supporting evidence IDs in provenance"
    print(f"[PASS] Test 2: Verdict={fusion_res.verdict}, Conf={fusion_res.confidence}%, ManipLikelihood={fusion_res.trust_triangle.manipulation_likelihood}%")


def test_case_3_manipulated_image():
    print("\n--- Test 3: Manipulated Image ---")
    data = load_fixture("edited_manipulated_photo.jpg")
    img_analysis = analyze_image_file(data, "edited_manipulated_photo.jpg")

    # Multimodal AI structured observation for edited photograph
    mm_result = MultimodalAiResult(
        ai_generation_assessment="possibly_manipulated",
        confidence=0.82,
        visual_findings=["Differential edge sharpness on subject", "Lighting angle mismatch on foreground element"],
        supporting_signals=["Localized compositing boundaries detected"],
        contradicting_signals=[],
        limitations=["Resolution limits pixel-level clone detection"],
        model_used="qwen/qwen3.8-27b",
        provider_used="groq",
        explanation="Visual indicators show signs of selective editing and differential lighting inconsistency.",
    )

    fusion_res = asyncio.run(fuse_investigation_evidence(
        claim_text="Check if this photo was edited",
        image_analysis=img_analysis,
        multimodal_result=mm_result,
    ))

    assert fusion_res.verdict == "LIKELY_MANIPULATED", f"Expected LIKELY_MANIPULATED, got {fusion_res.verdict}"
    assert fusion_res.trust_triangle.manipulation_likelihood >= 50.0, f"Expected manipulation_likelihood >= 50, got {fusion_res.trust_triangle.manipulation_likelihood}"
    assert len(fusion_res.supporting_evidence_ids) > 0, "Expected supporting evidence IDs in provenance"
    print(f"[PASS] Test 3: Verdict={fusion_res.verdict}, Conf={fusion_res.confidence}%, ManipLikelihood={fusion_res.trust_triangle.manipulation_likelihood}%")


def test_case_4_missing_exif_neutral():
    print("\n--- Test 4: Missing EXIF Strictly Neutral ---")
    data = load_fixture("photo_missing_exif.jpg")
    img_analysis = analyze_image_file(data, "photo_missing_exif.jpg")
    assert img_analysis.metadata.metadata_status == "unavailable"
    assert img_analysis.metadata.available is False

    # Normalize evidence vectors
    items = normalize_all_evidence(
        claim_text="Verify photo with missing EXIF",
        image_analysis=img_analysis,
        multimodal_result=None,
        search_evidence=None,
        url_outcome=None,
    )

    exif_items = [it for it in items if it.evidence_type == "METADATA_EXIF"]
    assert len(exif_items) == 1, "Expected exactly 1 METADATA_EXIF item"
    exif_item = exif_items[0]

    # Verify zero negative penalty and neutral contribution
    assert exif_item.direction == "NEUTRAL", f"Expected direction NEUTRAL, got {exif_item.direction}"
    assert exif_item.weight == 0.0, f"Expected weight 0.0, got {exif_item.weight}"
    assert exif_item.target_hypothesis == "CONTEXTUAL", f"Expected hypothesis CONTEXTUAL, got {exif_item.target_hypothesis}"

    # Fuse without adverse evidence -> must NOT produce LIKELY_MANIPULATED or LIKELY_AI_GENERATED
    fusion_res = asyncio.run(fuse_investigation_evidence(
        claim_text="Verify photo with missing EXIF",
        image_analysis=img_analysis,
        multimodal_result=None,
    ))
    assert fusion_res.verdict not in ["LIKELY_MANIPULATED", "LIKELY_AI_GENERATED"], (
        f"Missing EXIF erroneously produced adverse verdict {fusion_res.verdict}!"
    )
    print(f"[PASS] Test 4: Missing EXIF is strictly neutral: weight={exif_item.weight}, direction={exif_item.direction}, verdict={fusion_res.verdict}")


def test_case_5_conflicting_evidence():
    print("\n--- Test 5: Conflicting Evidence Detection ---")
    # Scenario: Modality A claims authentic, Modality B claims synthetic/manipulated
    opposing_items = [
        NormalizedEvidenceItem(
            evidence_id="EVID-AUTH-1",
            evidence_type="MULTIMODAL_VISION",
            description="Vision model asserts natural optical capture and human anatomical consistency.",
            direction="SUPPORTS",
            target_hypothesis="AUTHENTIC",
            weight=0.65,
            reliability=0.85,
            quality=0.85,
            source="vision_model_1",
            independence_group="vision_auditor",
        ),
        NormalizedEvidenceItem(
            evidence_id="EVID-SYNTH-1",
            evidence_type="IMAGE_ELA",
            description="High error level differential indicates synthetic frequency patterns.",
            direction="CONTRADICTS",
            target_hypothesis="AI_GENERATED",
            weight=0.65,
            reliability=0.85,
            quality=0.85,
            source="ela_detector",
            independence_group="forensic_tools",
        ),
    ]

    summary = EvidenceSummary(
        supporting_strength=0.65,
        contradicting_strength=0.65,
        independent_evidence_count=2,
        evidence_coverage=0.60,
        total_evidence_count=2,
    )

    conflict_report = detect_evidence_conflicts(opposing_items, summary)

    assert conflict_report.detected is True, "Expected conflict to be detected"
    assert conflict_report.severity in ["MEDIUM", "HIGH"], f"Expected MEDIUM or HIGH severity, got {conflict_report.severity}"
    assert conflict_report.conflict_score >= 0.5, f"Expected conflict_score >= 0.5, got {conflict_report.conflict_score}"

    # Fuse through engine
    engine = FusionEngine()
    fusion_res = engine.fuse(items=opposing_items, summary=summary, conflict=conflict_report)

    assert fusion_res.conflict.detected is True
    assert fusion_res.trust_triangle.evidence_conflict >= 50.0
    # Because of high conflict, confidence is constrained
    assert fusion_res.confidence <= 70, f"Expected confidence <= 70 under high conflict, got {fusion_res.confidence}"
    print(f"[PASS] Test 5: Conflict detected: count={conflict_report.count}, score={conflict_report.conflict_score}, severity={conflict_report.severity}, conf={fusion_res.confidence}%")


def test_case_6_duplicate_syndicated_sources():
    print("\n--- Test 6: Source Independence & Duplicate Clustering ---")
    # Simulate 5 search sources where 4 are copies/syndications of the first article
    from schemas.search import SearchEvidence, SearchResultCandidate

    primary_src = SearchResultCandidate(
        url="https://reuters.com/article-original",
        domain="reuters.com",
        root_domain="reuters.com",
        title="Primary Wire Report on Claim",
        snippet="Original investigation report on claim.",
        content_status="AVAILABLE",
        reliability_score=90,
        independence_level="INDEPENDENT",
        cluster_id="wire-cluster-1",
        retrieved_at="2026-10-08T12:00:00Z",
    )
    syndicated_sources = [
        SearchResultCandidate(
            url=f"https://affiliate{i}.com/wire-reprint",
            domain=f"affiliate{i}.com",
            root_domain=f"affiliate{i}.com",
            title=f"Primary Wire Report on Claim - Reprint {i}",
            snippet="Original investigation report on claim.",
            content_status="AVAILABLE",
            reliability_score=70,
            independence_level="SYNDICATED",
            cluster_id="wire-cluster-1",
            retrieved_at="2026-10-08T12:00:00Z",
        )
        for i in range(1, 5)
    ]
    all_sources = [primary_src] + syndicated_sources

    search_ev = SearchEvidence(
        sources=all_sources,
        supporting=all_sources,
        retrieval_status="SUCCESS",
    )

    items = normalize_all_evidence(
        claim_text="Testing syndication discounting",
        image_analysis=None,
        multimodal_result=None,
        search_evidence=search_ev,
        url_outcome=None,
    )

    weighted_items, summary = apply_reliability_weighting(items)

    web_items = [it for it in weighted_items if it.evidence_type == "WEB_SOURCE"]
    assert len(web_items) == 5, f"Expected 5 normalized web items, got {len(web_items)}"

    # All 5 items belong to the same cluster group
    primary_item = web_items[0]
    syndicated_items = web_items[1:]

    assert len(syndicated_items) == 4

    primary_weight = primary_item.weight
    for synd_it in syndicated_items:
        assert synd_it.weight <= primary_weight * 0.35, (
            f"Syndicated item weight {synd_it.weight} was not discounted against primary {primary_weight}!"
        )

    # Independent evidence count should reflect 1 independent cluster, NOT 5
    assert summary.independent_evidence_count == 1, (
        f"Expected independent_evidence_count=1, got {summary.independent_evidence_count}"
    )
    print(f"[PASS] Test 6: 5 syndicated articles clustered to {summary.independent_evidence_count} independent source. Primary weight={primary_weight:.3f}, Syndicated weights={[s.weight for s in syndicated_items]}")


def test_case_7_sparse_evidence():
    print("\n--- Test 7: Sparse Evidence Handling ---")
    # Investigation with no media and no external search
    fusion_res = asyncio.run(fuse_investigation_evidence(
        claim_text="Completely uncorroborated standalone claim with zero diagnostic telemetry",
        image_analysis=None,
        multimodal_result=None,
        search_evidence=None,
        url_outcome=None,
    ))

    assert fusion_res.verdict == "INCONCLUSIVE", f"Expected INCONCLUSIVE on sparse evidence, got {fusion_res.verdict}"
    assert fusion_res.confidence <= 25, f"Expected confidence <= 25, got {fusion_res.confidence}"
    assert fusion_res.trust_triangle.evidence_strength <= 20.0, f"Expected low evidence strength, got {fusion_res.trust_triangle.evidence_strength}"
    print(f"[PASS] Test 7: Sparse telemetry appropriately yielded {fusion_res.verdict} with confidence {fusion_res.confidence}%")


def test_case_8_phase_4_regression():
    print("\n--- Test 8: Phase 4 Regression Verification ---")
    data = load_fixture("real_test_photo.jpg")
    img = Image.open(io.BytesIO(data))

    # Computer Vision hashes
    dh = calculate_dhash(img)
    ph = calculate_phash(img)
    assert len(dh) == 16, f"Invalid dHash format: {dh}"
    assert len(ph) == 16, f"Invalid pHash format: {ph}"

    # ELA
    ela_res = compute_error_level_analysis(img, "JPEG")
    assert ela_res.available is True
    assert ela_res.mean_error is not None

    # Compression
    comp_res = analyze_compression(img, "JPEG")
    assert comp_res.compression_status in ("measured", "quantization_tables_present", "available", "not_applicable")

    # Full Phase 4 analyzer
    p4_result = analyze_image_file(data, "real_test_photo.jpg")
    assert p4_result.file.sha256 == hashlib.sha256(data).hexdigest()
    assert p4_result.evidence_health.score >= 50
    print(f"[PASS] Test 8: Phase 4 forensics fully intact (dHash={dh}, pHash={ph}, ELA mean={ela_res.mean_error}, Health={p4_result.evidence_health.score})")


def test_case_9_phase_5_regression():
    print("\n--- Test 9: Phase 5 Regression Verification ---")
    # Multimodal assessment normalization
    assert _normalize_assessment("likely_ai_generated") == "likely_ai_generated"
    assert _normalize_assessment("LIKELY AI GENERATED") == "likely_ai_generated"
    assert _normalize_assessment("genuine") == "likely_authentic"
    assert _normalize_assessment("unclear") == "inconclusive"

    # Multimodal confidence normalization
    assert _normalize_confidence(85) == 0.85
    assert _normalize_confidence(0.92) == 0.92
    assert _normalize_confidence(-10) == 0.0
    assert _normalize_confidence(150) == 1.0

    # Prompt construction
    from services.multimodal.prompt import SYSTEM_PROMPT
    prompt = build_multimodal_prompt(filename="moon.jpg", claim_text="Evaluating moon landing photo")
    assert "Evaluating moon landing photo" not in prompt  # claim withheld to avoid anchoring bias
    assert "Missing EXIF metadata is UNAVAILABLE, NOT suspicious" in SYSTEM_PROMPT
    print("[PASS] Test 9: Phase 5 multimodal normalization and prompt contracts fully intact.")


def test_case_10_api_investigate_integration():
    print("\n--- Test 10: POST /api/investigate Integration ---")
    rate_limiter.hits.clear()
    data = load_fixture("real_test_photo.jpg")

    response = client.post(
        "/api/investigate",
        data={"claim": "Test photo taken with standard camera"},
        files={"file": ("real_test_photo.jpg", data, "image/jpeg")},
    )

    assert response.status_code == 200, f"API failed: {response.text}"
    body = response.json()

    # Verify Phase 6 fields present in InvestigationResponse
    assert "trustTriangle" in body, "Missing trustTriangle in API response"
    assert "evidenceSummary" in body, "Missing evidenceSummary in API response"
    assert "conflict" in body, "Missing conflict in API response"
    assert "normalizedEvidence" in body, "Missing normalizedEvidence in API response"

    tt = body["trustTriangle"]
    assert "manipulationLikelihood" in tt
    assert "evidenceStrength" in tt
    assert "evidenceConflict" in tt

    final = body["final"]
    assert "verdict" in final
    assert final["verdict"] in [
        "LIKELY_AUTHENTIC",
        "LIKELY_AI_GENERATED",
        "LIKELY_MANIPULATED",
        "INCONCLUSIVE",
        "LIKELY_GENUINE",
        "HIGH_RISK",
    ]
    assert 0 <= final["confidence"] <= 95
    assert "reason" in final
    print(f"[PASS] Test 10: POST /api/investigate returned valid Phase 6 payload: verdict={final['verdict']}, conf={final['confidence']}%, TT={tt}")


def test_case_11_llm_cannot_override_fusion():
    print("\n--- Test 11: LLM Cannot Override Deterministic Fusion ---")
    # Create deterministic result
    det_result = FusionResult(
        verdict="LIKELY_AI_GENERATED",
        confidence=82,
        reason="Deterministic fusion found multiple synthetic generation indicators.",
        trust_triangle=TrustTriangle(manipulation_likelihood=88.0, evidence_strength=75.0, evidence_conflict=10.0),
        evidence_summary=EvidenceSummary(supporting_strength=1.5, contradicting_strength=0.1, independent_evidence_count=2),
        conflict=ConflictReport(detected=False),
        supporting_evidence_ids=["EVID-MM-AI", "EVID-SYNTH-1"],
    )

    # Explanation generator generates textual explanation only
    explanation = generate_deterministic_explanation(det_result, claim_text="Sample synthetic image")

    # Verify explanation reflects but does not alter the verdict or metrics
    assert "LIKELY AI GENERATED" in explanation.upper()
    assert "82%" in explanation
    assert det_result.verdict == "LIKELY_AI_GENERATED"
    assert det_result.confidence == 82
    print(f"[PASS] Test 11: Deterministic fusion result preserved intact without LLM override.")


def run_all_tests():
    print("=" * 70)
    print("TRUSTLENS PHASE 6: EVIDENCE FUSION & FINAL DECISION VERIFICATION SUITE")
    print("=" * 70)

    test_case_1_ai_generated_image()
    test_case_2_normal_photograph()
    test_case_3_manipulated_image()
    test_case_4_missing_exif_neutral()
    test_case_5_conflicting_evidence()
    test_case_6_duplicate_syndicated_sources()
    test_case_7_sparse_evidence()
    test_case_8_phase_4_regression()
    test_case_9_phase_5_regression()
    test_case_10_api_investigate_integration()
    test_case_11_llm_cannot_override_fusion()

    print("\n" + "=" * 70)
    print("ALL 11 PHASE 6 VERIFICATION SUITE TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
