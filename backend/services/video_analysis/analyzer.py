"""
Video investigation orchestrator for TrustLens Phase 8.

video -> validate/probe -> <=3 representative frames -> EXISTING image pipeline per frame
(file health, ELA n/a for PNG, CV, OCR) -> EXISTING image-text-vs-claim comparison.
No forensic code is duplicated. Phase 6 fusion remains the only verdict authority.
"""
import asyncio
import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from config import settings
from schemas.video_analysis import (
    VideoAnalysisResult, VideoCapability, VideoClaimComparison, VideoFrameEvidence, VideoMetadata,
)
from services.image_analysis.analyzer import analyze_image_file
from services.image_analysis.image_text_evidence import compare_image_text_to_claim
from services.video_analysis.frames import encode_frame_png, extract_frames, thumbnail_data_url
from services.video_analysis.probe import ALLOWED_EXTENSIONS, VideoProbeError, probe_video

SOURCE_TYPE, SOURCE = "VIDEO", "uploaded_video"

# Never implemented in TrustLens. Listed explicitly so the UI/report cannot imply them.
UNAVAILABLE_DETECTORS = [
    ("PRNU sensor-noise fingerprinting", "Not implemented."),
    ("Deepfake / face-swap detection", "Not implemented."),
    ("Facial manipulation probability", "Not implemented."),
    ("Optical-flow / temporal manipulation detection", "Not implemented; only 3 frames are sampled."),
    ("AI-generated video probability", "Not implemented; no video-level generative detector exists."),
    ("Audio track analysis", "Not implemented."),
    ("Full frame-by-frame analysis", "Not performed; only representative frames are analyzed."),
]


import copy
from collections import OrderedDict

# Content-based LRU cache keyed by sha256 + normalized claim + app_version
_VIDEO_CACHE: "OrderedDict[str, VideoAnalysisBundle]" = OrderedDict()
_MAX_CACHE_ITEMS = 64

@dataclass
class VideoAnalysisBundle:
    """Result plus the PNG bytes of decoded frames (kept server-side for the optional multimodal step)."""
    result: VideoAnalysisResult
    frame_png: Dict[str, bytes] = field(default_factory=dict)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _failed(code: str, msg: str, metadata: Optional[VideoMetadata] = None) -> VideoAnalysisBundle:
    return VideoAnalysisBundle(VideoAnalysisResult(
        ok=False, status="FAILED", error_code=code, error=msg, metadata=metadata,
        capabilities=_capabilities([], None),
        limitations=["The video could not be analyzed, so it contributes no evidence. This is not a finding about the video."],
        analyzed_at=_now(),
    ))


def _map_relationship(rel: str) -> str:
    return "INSUFFICIENT_EVIDENCE" if rel == "INSUFFICIENT_TEXT" else rel


def _capabilities(frames: List[VideoFrameEvidence], mm_frame: Optional[VideoFrameEvidence]) -> List[VideoCapability]:
    decoded = [f for f in frames if f.decoded]
    caps = [
        VideoCapability(name="Container & stream metadata", status="IMPLEMENTED",
                        note="Measured with ffprobe/OpenCV; unmeasurable fields are left empty."),
        VideoCapability(name="Decode validation", status="IMPLEMENTED"),
        VideoCapability(name="Representative frame extraction", status="IMPLEMENTED" if decoded else "UNAVAILABLE",
                        note="Beginning / middle / end only."),
        VideoCapability(name="Per-frame image health & forensics (existing image pipeline)",
                        status="PARTIAL" if decoded else "UNAVAILABLE",
                        note="Frames are re-encoded losslessly as PNG, so ELA and EXIF do not apply. "
                             "Measures technical suitability, not authenticity."),
    ]
    ocr_ok = any(f.ocr_available for f in decoded)
    caps.append(VideoCapability(name="OCR on frames", status="PARTIAL" if ocr_ok else "UNAVAILABLE",
                                note="Sampled frames only; text between samples is not seen." if ocr_ok
                                else "OCR engine unavailable or no frame decoded."))
    mm = getattr(mm_frame, "multimodal", None) if mm_frame else None
    if mm is not None and getattr(mm, "model_used", None):
        caps.append(VideoCapability(name="Multimodal AI inspection", status="PARTIAL",
                                    note=f"Single frame ({mm_frame.frame_ref}) only; advisory, not a video-level judgement."))
    else:
        caps.append(VideoCapability(name="Multimodal AI inspection", status="UNAVAILABLE",
                                    note="Provider not configured, not run, or it failed for the sampled frame."))
    caps += [VideoCapability(name=n, status="UNAVAILABLE", note=note) for n, note in UNAVAILABLE_DETECTORS]
    return caps


def _aggregate_claim(frames: List[VideoFrameEvidence], claim: str) -> VideoClaimComparison:
    if not claim.strip():
        return VideoClaimComparison(relationship="INSUFFICIENT_EVIDENCE",
                                    explanation="No user claim was provided to compare against the video.")
    by = lambda r: [f for f in frames if f.claim_relationship == r]
    sup, par, con, unr = by("SUPPORTS"), by("PARTIALLY_SUPPORTS"), by("CONTRADICTS"), by("UNRELATED")
    refs = lambda fs: [f.frame_ref for f in fs]
    q = lambda fs: max([f.ocr_quality for f in fs] or [0.0])

    if not (sup or par or con or unr):
        return VideoClaimComparison(
            relationship="INSUFFICIENT_EVIDENCE",
            explanation="No readable text was obtained from the sampled frames, so the claim could not be compared with the video.")
    if con and (sup or par):
        rel, hit = "PARTIALLY_SUPPORTS", sup + par + con
        why = (f"Sampled frames disagree: {', '.join(refs(sup + par))} agree(s) with the claim while "
               f"{', '.join(refs(con))} contradict(s) it.")
    elif con:
        rel, hit, why = "CONTRADICTS", con, f"Text in {', '.join(refs(con))} contradicts the claim."
    elif sup and not par:
        rel, hit, why = "SUPPORTS", sup, f"Text in {', '.join(refs(sup))} matches the claim."
    elif sup or par:
        rel, hit, why = "PARTIALLY_SUPPORTS", sup + par, f"Text in {', '.join(refs(sup + par))} matches only part of the claim."
    else:
        rel, hit, why = "UNRELATED", unr, "Text found in the sampled frames is unrelated to the claim."
    return VideoClaimComparison(
        relationship=rel, explanation=why + " Only 3 sampled frames were read; on-screen text is not proof the claim is true.",
        supporting_frames=refs(sup + par), contradicting_frames=refs(con), ocr_quality=round(q(hit), 3))


def _analyze_sync(file_bytes: bytes, filename: str, content_type: str, claim_text: str) -> VideoAnalysisBundle:
    clean = os.path.basename((filename or "upload").strip()) or "upload"
    stem, ext = os.path.splitext(clean.lower())
    sha = hashlib.sha256(file_bytes).hexdigest()
    base_meta = VideoMetadata(filename=clean, size_bytes=len(file_bytes), sha256=sha)

    if not file_bytes:
        return _failed("EMPTY_FILE", "The uploaded video is empty (0 bytes).")

    cache_key = f"{sha}:{claim_text.strip()}:{settings.app_version}"
    if cache_key in _VIDEO_CACHE:
        cached = _VIDEO_CACHE[cache_key]
        _VIDEO_CACHE.move_to_end(cache_key)
        return copy.deepcopy(cached)
    limit = settings.max_upload_size_bytes
    if len(file_bytes) > limit:
        return _failed("FILE_TOO_LARGE",
                       f"Video size ({len(file_bytes) / 1048576:.1f} MB) exceeds the {limit // 1048576} MB limit.", base_meta)
    if ext not in ALLOWED_EXTENSIONS:
        return _failed("UNSUPPORTED_EXTENSION",
                       f"File extension '{ext}' is not supported. Allowed video formats: MP4, MOV, WebM, AVI.", base_meta)
    mime = (content_type or "").lower().split(";")[0].strip()
    if mime and not mime.startswith("video/") and mime != "application/octet-stream":
        return _failed("UNSUPPORTED_MIME_TYPE", f"MIME type '{mime}' is not a supported video type.", base_meta)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        try:
            probe = probe_video(tmp_path)
        except VideoProbeError as exc:
            return _failed(exc.code, exc.message, base_meta)

        meta = VideoMetadata(
            filename=clean, size_bytes=len(file_bytes), sha256=sha, container=probe.container, codec=probe.codec,
            duration_seconds=probe.duration_seconds, width=probe.width, height=probe.height, frame_rate=probe.frame_rate,
            frame_count=probe.frame_count, frame_count_source=probe.frame_count_source, decodable=probe.decodable,
            probe_tool=probe.probe_tool, notes=probe.notes)

        frames: List[VideoFrameEvidence] = []
        pngs: Dict[str, bytes] = {}
        max_png = getattr(settings, "max_image_upload_size_bytes", 10 * 1024 * 1024)
        for i, ex in enumerate(extract_frames(tmp_path, probe.frame_count, probe.frame_rate), start=1):
            ref = f"frame_{i}_{ex.position}"
            fe = VideoFrameEvidence(frame_ref=ref, position=ex.position, frame_index=ex.frame_index,
                                    timestamp_seconds=ex.timestamp_seconds, source_type=SOURCE_TYPE, source=SOURCE)
            if ex.image is None:
                fe.error = ex.error
                frames.append(fe)
                continue
            try:
                png, downscaled = encode_frame_png(ex.image, max_png)
                ia = analyze_image_file(png, f"{stem}_{ref}.png", "image/png")
            except Exception as exc:  # frame-level failure must not sink the whole video
                fe.error = f"Frame could not be analyzed: {exc}"
                frames.append(fe)
                continue
            fe.decoded, fe.downscaled = True, downscaled
            fe.width, fe.height, fe.sha256 = ia.file.width, ia.file.height, ia.file.sha256
            fe.thumbnail_data_url = thumbnail_data_url(ex.image)
            fe.quality_score, fe.quality_status = ia.evidence_health.score, ia.evidence_health.status
            fe.ocr_available = ia.ocr.available
            fe.ocr_text = ia.ocr.text if ia.ocr.available else ""
            fe.ocr_confidence = ia.ocr.confidence
            fe.image_analysis = ia
            if claim_text.strip():
                ite = compare_image_text_to_claim(ia.ocr, claim_text)
                fe.claim_relationship = _map_relationship(ite.relationship)
                fe.claim_explanation = ite.explanation
                fe.ocr_quality = ite.ocr_quality
            pngs[ref] = png
            frames.append(fe)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    decoded = [f for f in frames if f.decoded]
    if not decoded:
        res = _failed("NO_FRAMES_DECODED", "No representative frame could be decoded from the video.", meta)
        res.result.frames = frames
        return res

    limitations = [
        "Only up to 3 representative frames (beginning/middle/end) were analyzed, not the full video.",
        "Frame health measures technical suitability for analysis, not whether the video is authentic.",
        "Successful decoding and analysis does NOT mean the video is authentic.",
        "Frames are re-encoded as lossless PNG: ELA and EXIF do not apply to extracted frames.",
        "Video-level PRNU, deepfake, facial-manipulation, optical-flow and AI-generated-video detection are unavailable.",
        "On-screen text is evidence of what the video shows, not proof that a claim is true.",
    ]
    if len(decoded) < len(frames):
        limitations.append(f"{len(frames) - len(decoded)} sampled frame(s) could not be decoded or analyzed.")
    if any(f.downscaled for f in decoded):
        limitations.append("At least one frame was downscaled to fit the image size limit.")
    limitations += meta.notes

    result = VideoAnalysisResult(
        ok=True, status="ANALYZED" if len(decoded) == len(frames) else "PARTIAL", metadata=meta, frames=frames,
        claim_comparison=_aggregate_claim(frames, claim_text), capabilities=_capabilities(frames, None),
        limitations=limitations, analyzed_at=_now())
    bundle = VideoAnalysisBundle(result, pngs)
    if len(_VIDEO_CACHE) >= _MAX_CACHE_ITEMS:
        _VIDEO_CACHE.popitem(last=False)
    _VIDEO_CACHE[cache_key] = copy.deepcopy(bundle)
    return bundle


async def analyze_video_file(file_bytes: bytes, filename: str, content_type: str = "",
                             claim_text: str = "") -> VideoAnalysisBundle:
    """Run the (blocking) video pipeline off the event loop. Never raises for bad input."""
    try:
        return await asyncio.to_thread(_analyze_sync, file_bytes, filename, content_type, claim_text)
    except Exception as exc:
        return _failed("VIDEO_ANALYSIS_ERROR", f"Video analysis failed unexpectedly: {exc}")


async def add_multimodal_frame(bundle: VideoAnalysisBundle, claim_text: str, search_evidence=None) -> None:
    """Optional Phase 5 step on ONE frame (middle, else first decoded). Failure is recorded, never raised."""
    res = bundle.result
    cands = [f for f in res.frames if f.decoded]
    if not res.ok or not cands:
        return
    frame = next((f for f in cands if f.position == "middle"), cands[0])
    try:
        from services.multimodal import analyze_multimodal_image
        frame.multimodal = await analyze_multimodal_image(
            image_bytes=bundle.frame_png[frame.frame_ref], filename=f"{frame.frame_ref}.png", mime_type="image/png",
            claim_text=claim_text, image_analysis=frame.image_analysis, search_evidence=search_evidence)
    except Exception as exc:
        res.limitations.append(f"Multimodal inspection of {frame.frame_ref} failed: {exc}")
    res.capabilities = _capabilities(res.frames, frame)
    res.limitations.append(
        f"Multimodal AI saw only {frame.frame_ref}; it is recorded as advisory and does not drive the video verdict.")
