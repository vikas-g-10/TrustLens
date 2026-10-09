"""
TrustLens Phase 8 Verification Test Suite: Video Investigation
==============================================================
1. Valid video metadata extraction (MP4 / MOV / AVI / WebM, real files generated at runtime)
2. Invalid / corrupt / unsupported video -> clear error + INCONCLUSIVE (no fabricated evidence)
3. Deterministic representative-frame extraction (<= 3 frames, content verified)
4. OCR on a video frame (skipped if Tesseract is not installed)
5. Provenance on frame evidence (source_type VIDEO, source uploaded_video, frame_index/timestamp)
6. Video evidence entering Phase 6 fusion (verdict stays with the fusion engine)
7. Unsupported/unavailable advanced detection is reported UNAVAILABLE, never fabricated
8. Existing image pipeline regression (no VIDEO_* evidence, routing unchanged)
9. POST /api/investigate video integration
"""
import asyncio
import os
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas.fusion import NormalizedEvidenceItem
from services.fusion import fuse_investigation_evidence
from services.fusion.conflict import detect_evidence_conflicts
from services.fusion.engine import FusionEngine
from services.fusion.weighting import apply_reliability_weighting
from services.image_analysis.analyzer import analyze_image_file
from services.image_analysis.ocr import _resolve_tesseract_binary
from services.video_analysis.analyzer import analyze_video_file
from services.video_analysis.frames import extract_frames, sample_targets
from services.video_analysis.probe import VideoProbeError, is_video_upload, probe_video

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))
TEXT = "SALE 50 PERCENT OFF TODAY"
N_FRAMES, FPS, SIZE = 30, 10, (640, 360)
# (extension, OpenCV fourcc) combos; each is skipped if this OpenCV build cannot write it.
CONTAINERS = [("mp4", "mp4v"), ("mov", "mp4v"), ("avi", "MJPG"), ("webm", "VP80")]


def _write_video(path: str, fourcc: str) -> bool:
    w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*fourcc), FPS, SIZE)
    if not w.isOpened():
        return False
    for i in range(N_FRAMES):
        img = np.full((SIZE[1], SIZE[0], 3), 255, np.uint8)
        color = [(0, 0, 255), (0, 255, 0), (255, 0, 0)][i * 3 // N_FRAMES]  # BGR: red, green, blue thirds
        cv2.rectangle(img, (0, 0), (SIZE[0] - 1, 40), color, -1)
        cv2.putText(img, TEXT, (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 0), 3, cv2.LINE_AA)
        w.write(img)
    w.release()
    return os.path.exists(path) and os.path.getsize(path) > 0


@pytest.fixture(scope="module")
def videos(tmp_path_factory):
    d = tmp_path_factory.mktemp("videos")
    out = {}
    for ext, fourcc in CONTAINERS:
        p = str(d / f"clip.{ext}")
        if _write_video(p, fourcc):
            out[ext] = p
    if "mp4" not in out:
        pytest.skip("OpenCV in this environment cannot write MP4 test videos")
    return out


def _bytes(path):
    with open(path, "rb") as f:
        return f.read()


def _run(coro):
    return asyncio.run(coro)


# 1 ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("ext", [e for e, _ in CONTAINERS])
def test_valid_video_metadata(videos, ext):
    if ext not in videos:
        pytest.skip(f"cannot write .{ext} here")
    r = probe_video(videos[ext])
    assert r.decodable is True
    assert (r.width, r.height) == SIZE
    assert r.frame_rate == pytest.approx(FPS, rel=0.01)
    assert r.duration_seconds == pytest.approx(N_FRAMES / FPS, rel=0.05)
    assert r.frame_count == N_FRAMES
    assert r.frame_count_source in ("container", "estimated_from_duration")


# 2 ---------------------------------------------------------------------------------------------
def test_corrupt_and_unsupported_video(videos):
    with pytest.raises(VideoProbeError):
        p = os.path.join(os.path.dirname(videos["mp4"]), "junk.mp4")
        with open(p, "wb") as f:
            f.write(b"this is not a video" * 50)
        probe_video(p)

    good = _bytes(videos["mp4"])
    cases = [
        ("junk.mp4", b"not a video" * 50, "video/mp4", "INVALID_VIDEO"),
        ("truncated.mp4", good[:2000], "video/mp4", "INVALID_VIDEO"),
        ("empty.mp4", b"", "video/mp4", "EMPTY_FILE"),
        ("clip.mkv", good, "video/x-matroska", "UNSUPPORTED_EXTENSION"),
        ("clip.mp4", good, "text/plain", "UNSUPPORTED_MIME_TYPE"),
    ]
    for name, blob, ctype, code in cases:
        res = _run(analyze_video_file(blob, name, ctype, "claim")).result
        assert res.ok is False and res.status == "FAILED", name
        assert res.error_code == code, (name, res.error_code)
        assert res.frames == [] and res.error

        fused = _run(fuse_investigation_evidence(claim_text="claim", video_analysis=res))
        assert fused.verdict == "INCONCLUSIVE", name
        # a failed decode contributes nothing; it is not treated as manipulation evidence
        assert all(it.weight == 0.0 and it.direction == "NEUTRAL" for it in fused.normalized_evidence)


# 3 ---------------------------------------------------------------------------------------------
def test_sample_targets_are_deterministic_and_small():
    assert sample_targets(30) == [("beginning", 0), ("middle", 15), ("end", 29)]
    assert sample_targets(30) == sample_targets(30)
    assert sample_targets(2) == [("beginning", 0), ("middle", 1)]
    assert sample_targets(1) == [("beginning", 0)]
    assert sample_targets(None) == [("beginning", 0)]
    assert len(sample_targets(10_000_000)) == 3


@pytest.mark.parametrize("ext", [e for e, _ in CONTAINERS])
def test_representative_frame_extraction(videos, ext):
    if ext not in videos:
        pytest.skip(f"cannot write .{ext} here")
    r = probe_video(videos[ext])
    frames = extract_frames(videos[ext], r.frame_count, r.frame_rate)
    assert [f.position for f in frames] == ["beginning", "middle", "end"]
    assert [f.frame_index for f in frames] == [0, 15, 29]
    assert frames[1].timestamp_seconds == pytest.approx(1.5, abs=0.01)
    # content check: the frame at each position really comes from that part of the video
    top_bar = [tuple(int(v) for v in f.image[10, 300]) for f in frames]
    assert top_bar[0][2] > 200 and top_bar[0][0] < 60      # red
    assert top_bar[1][1] > 200 and top_bar[1][0] < 60      # green
    assert top_bar[2][0] > 200 and top_bar[2][2] < 60      # blue


# 4 ---------------------------------------------------------------------------------------------
@pytest.mark.skipif(not _resolve_tesseract_binary(), reason="Tesseract OCR not installed")
def test_ocr_on_video_frame(videos):
    res = _run(analyze_video_file(_bytes(videos["mp4"]), "clip.mp4", "video/mp4", "")).result
    assert res.ok
    mid = next(f for f in res.frames if f.position == "middle")
    assert mid.ocr_available and "PERCENT" in mid.ocr_text.upper()
    # claim comparison reuses the existing image-text comparator
    res2 = _run(analyze_video_file(_bytes(videos["mp4"]), "clip.mp4", "video/mp4",
                                   "The video says the sale is 80 percent off")).result
    assert res2.claim_comparison.relationship == "CONTRADICTS"
    res3 = _run(analyze_video_file(_bytes(videos["mp4"]), "clip.mp4", "video/mp4",
                                   "The store is running a sale with 50 percent off")).result
    assert res3.claim_comparison.relationship in ("SUPPORTS", "PARTIALLY_SUPPORTS")


def test_claim_comparison_without_claim_is_insufficient(videos):
    res = _run(analyze_video_file(_bytes(videos["mp4"]), "clip.mp4", "video/mp4", "")).result
    assert res.claim_comparison.relationship == "INSUFFICIENT_EVIDENCE"


# 5 ---------------------------------------------------------------------------------------------
def test_frame_provenance(videos):
    claim = "The store is running a sale with 50 percent off"
    res = _run(analyze_video_file(_bytes(videos["mp4"]), "clip.mp4", "video/mp4", claim)).result
    assert len(res.frames) == 3
    for f in res.frames:
        assert (f.source_type, f.source) == ("VIDEO", "uploaded_video")
        assert f.frame_ref.startswith("frame_") and f.timestamp_seconds is not None
    fused = _run(fuse_investigation_evidence(claim_text=claim, video_analysis=res))
    video_items = [it for it in fused.normalized_evidence if it.provenance.get("source_type") == "VIDEO"]
    assert video_items
    for it in video_items:
        assert it.provenance["source"] == "uploaded_video"
        if it.evidence_id.startswith("ev_video_frame_"):
            assert "frame_index" in it.provenance and "timestamp_seconds" in it.provenance


# 6 ---------------------------------------------------------------------------------------------
def test_video_evidence_enters_phase6_fusion(videos):
    res = _run(analyze_video_file(_bytes(videos["mp4"]), "clip.mp4", "video/mp4",
                                  "The video says the sale is 80 percent off")).result
    fused = _run(fuse_investigation_evidence(claim_text="The video says the sale is 80 percent off", video_analysis=res))
    ids = {it.evidence_id for it in fused.normalized_evidence}
    assert "ev_video_metadata" in ids and "ev_video_claim_text" in ids
    # decodable video + readable text is NOT authenticity evidence: fusion stays INCONCLUSIVE
    assert fused.verdict == "INCONCLUSIVE"
    assert fused.verdict not in ("LIKELY_AUTHENTIC", "LIKELY_GENUINE")
    # nothing video-derived drives hypothesis strength
    assert all(it.weight == 0.0 or it.evidence_type == "IMAGE_TEXT"
               for it in fused.normalized_evidence if it.provenance.get("source_type") == "VIDEO")


def _web_item(i):
    return NormalizedEvidenceItem(
        evidence_id=f"web_{i}", evidence_type="WEB_SOURCE", description="independent source corroborates claim",
        direction="SUPPORTS", target_hypothesis="CLAIM_TRUE", reliability=0.9, quality=1.0,
        independence_group=f"web_cluster_{i}", source="example.org")


def _fuse_items(items):
    weighted, summary = apply_reliability_weighting(items)
    return FusionEngine().fuse(weighted, summary, detect_evidence_conflicts(weighted, summary))


def test_web_corroboration_cannot_certify_an_uploaded_video(videos):
    """Existing guard (web results can't prove the *media* is genuine) now also covers video."""
    web = [_web_item(1), _web_item(2)]
    assert _fuse_items(list(web)).verdict == "LIKELY_AUTHENTIC"  # baseline: text-only claim, unchanged
    res = _run(analyze_video_file(_bytes(videos["mp4"]), "clip.mp4", "video/mp4", "")).result
    from services.fusion.video_normalizer import normalize_video_evidence
    with_video = _fuse_items(list(web) + normalize_video_evidence(res))
    assert with_video.verdict == "INCONCLUSIVE"


# 7 ---------------------------------------------------------------------------------------------
def test_advanced_video_detection_is_unavailable(videos):
    res = _run(analyze_video_file(_bytes(videos["mp4"]), "clip.mp4", "video/mp4", "")).result
    caps = {c.name: c.status for c in res.capabilities}
    for name in ("PRNU sensor-noise fingerprinting", "Deepfake / face-swap detection",
                 "Facial manipulation probability", "Optical-flow / temporal manipulation detection",
                 "AI-generated video probability", "Audio track analysis", "Full frame-by-frame analysis"):
        assert caps[name] == "UNAVAILABLE", name
    assert caps["Container & stream metadata"] == "IMPLEMENTED"
    assert caps["Per-frame image health & forensics (existing image pipeline)"] == "PARTIAL"  # not oversold
    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield str(k).lower()
                yield from keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v)

    # No video-level detector output fields may exist (frame-level image analysis may *mention* PRNU as unavailable).
    video_keys = set(keys(res.model_dump(by_alias=True)))
    for forbidden in ("deepfakeprobability", "aigeneratedprobability", "opticalflowscore", "authenticityscore",
                      "tamperingscore", "manipulationprobability"):
        assert forbidden not in video_keys, forbidden
    assert any("does NOT mean the video is authentic" in l for l in res.limitations)


# 8 ---------------------------------------------------------------------------------------------
def test_image_pipeline_regression():
    assert not is_video_upload("photo.jpg", "image/jpeg")
    assert not is_video_upload("graphic.png", "image/png")
    assert not is_video_upload("pic.webp", "image/webp")
    assert is_video_upload("clip.mp4", "video/mp4")
    assert is_video_upload("clip.webm", "")

    path = os.path.join(FIXTURES_DIR, "real_test_photo.jpg")
    ia = analyze_image_file(_bytes(path), "real_test_photo.jpg", "image/jpeg")
    fused = _run(fuse_investigation_evidence(claim_text="A photo", image_analysis=ia))
    assert not any(it.evidence_type in ("VIDEO_METADATA", "VIDEO_FRAME") for it in fused.normalized_evidence)
    assert ia.file.format == "JPEG"


# 9 ---------------------------------------------------------------------------------------------
def test_investigate_endpoint_video(videos):
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    r = client.post("/api/investigate", data={"claim": "The video says the sale is 80 percent off"},
                    files={"file": ("clip.mp4", _bytes(videos["mp4"]), "video/mp4")})
    assert r.status_code == 200, r.text
    data = r.json()
    va = data["mediaAnalysis"]["videoAnalysis"]
    assert data["mediaAnalysis"]["mediaType"] == "video" and va["ok"] is True
    assert len(va["frames"]) == 3 and va["metadata"]["width"] == SIZE[0]
    assert data["final"]["verdict"] == "INCONCLUSIVE"
    assert any(e["provenance"].get("source_type") == "VIDEO" for e in data["normalizedEvidence"])

    bad = client.post("/api/investigate", data={"claim": "anything"},
                      files={"file": ("junk.mp4", b"not a video" * 50, "video/mp4")})
    assert bad.status_code == 200
    b = bad.json()
    assert b["mediaAnalysis"]["analyzed"] is False and b["final"]["verdict"] == "INCONCLUSIVE"
    assert b["mediaAnalysis"]["videoAnalysis"]["errorCode"] == "INVALID_VIDEO"

    only = client.post("/api/investigate", files={"file": ("junk.mp4", b"not a video" * 50, "video/mp4")})
    assert only.status_code == 400  # no claim, no url, unusable video
