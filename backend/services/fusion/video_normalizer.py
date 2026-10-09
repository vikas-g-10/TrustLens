"""
Video evidence normalizer for TrustLens Phase 8.

Converts VideoAnalysisResult into the SAME NormalizedEvidenceItem objects the Phase 6 engine
already consumes. It makes no verdict. Guarantees:
- Metadata, frame health, OCR and multimodal findings are NEUTRAL (weight 0): a decodable, sharp
  video is not evidence of authenticity, and a failed decode is not evidence of manipulation.
- The only directional item is the on-screen-text vs claim relationship (IMAGE_TEXT), which the
  existing config already keeps out of the verdict (image_text_affects_verdict=False).
- Every item carries provenance: source_type=VIDEO, source=uploaded_video, frame_index/timestamp.
"""
from typing import Any, Dict, List
from schemas.fusion import NormalizedEvidenceItem
from schemas.video_analysis import VideoAnalysisResult, VideoFrameEvidence

_SRC = {"source_type": "VIDEO", "source": "uploaded_video"}
_NOT_PROOF = "A video that decodes and analyzes successfully is not thereby shown to be authentic."


def _frame_prov(f: VideoFrameEvidence, **extra: Any) -> Dict[str, Any]:
    return {**_SRC, "frame_ref": f.frame_ref, "position": f.position, "frame_index": f.frame_index,
            "timestamp_seconds": f.timestamp_seconds, **extra}


def normalize_video_evidence(video: VideoAnalysisResult) -> List[NormalizedEvidenceItem]:
    items: List[NormalizedEvidenceItem] = []

    if not video.ok or not video.metadata:
        items.append(NormalizedEvidenceItem(
            evidence_id="ev_video_unanalyzable", evidence_type="VIDEO_METADATA",
            description=f"Video could not be analyzed ({video.error_code}): {video.error}",
            direction="NEUTRAL", target_hypothesis="CONTEXTUAL", reliability=0.0, quality=0.0,
            independence_group="video_container", source="Video Probe (ffprobe/OpenCV)",
            provenance={**_SRC, "error_code": video.error_code},
            limitations=["An unreadable or unsupported file is not evidence of manipulation; it contributes nothing."]))
        return items

    m = video.metadata
    bits = [m.container or "container unknown", m.codec or "codec unknown",
            f"{m.width}x{m.height}" if m.width and m.height else "resolution unknown",
            f"{m.frame_rate:.2f} fps" if m.frame_rate else "fps unknown",
            f"{m.duration_seconds:.2f}s" if m.duration_seconds else "duration unknown",
            f"{m.frame_count} frames ({m.frame_count_source})" if m.frame_count else "frame count unknown"]
    items.append(NormalizedEvidenceItem(
        evidence_id="ev_video_metadata", evidence_type="VIDEO_METADATA",
        description="Video decoded and measured: " + ", ".join(bits) + f", SHA-256 {m.sha256[:12]}….",
        direction="NEUTRAL", target_hypothesis="CONTEXTUAL", reliability=0.60, quality=1.0 if m.decodable else 0.0,
        independence_group="video_container", source="Video Probe (ffprobe/OpenCV)", confidence=1.0,
        provenance={**_SRC, "sha256": m.sha256, "container": m.container, "probe_tool": m.probe_tool},
        limitations=[_NOT_PROOF]))

    for f in video.frames:
        if not f.decoded:
            items.append(NormalizedEvidenceItem(
                evidence_id=f"ev_video_{f.frame_ref}_undecoded", evidence_type="VIDEO_FRAME",
                description=f"{f.frame_ref} (frame {f.frame_index}) could not be decoded: {f.error}",
                direction="NEUTRAL", target_hypothesis="CONTEXTUAL", reliability=0.0, quality=0.0,
                independence_group="video_frame_quality", source="Frame Extractor", provenance=_frame_prov(f),
                limitations=["A frame that cannot be decoded is not evidence of manipulation."]))
            continue
        items.append(NormalizedEvidenceItem(
            evidence_id=f"ev_video_{f.frame_ref}_quality", evidence_type="VIDEO_FRAME",
            description=(f"{f.frame_ref} (frame {f.frame_index}, t={f.timestamp_seconds}s): "
                         f"Evidence Health {f.quality_score}/100 ({f.quality_status}); technical suitability only."),
            direction="NEUTRAL", target_hypothesis="CONTEXTUAL", reliability=0.50,
            quality=(f.quality_score or 0) / 100.0, independence_group="video_frame_quality",
            source="Evidence Health Evaluator (frame)",
            provenance=_frame_prov(f, score=f.quality_score, status=f.quality_status),
            limitations=["Frame health measures technical suitability, not authenticity."]))
        if f.ocr_available and f.ocr_text.strip():
            items.append(NormalizedEvidenceItem(
                evidence_id=f"ev_video_{f.frame_ref}_ocr", evidence_type="OCR_TEXT",
                description=f"OCR text in {f.frame_ref}: \"{f.ocr_text[:100]}\".",
                direction="NEUTRAL", target_hypothesis="CONTEXTUAL",
                reliability=min(1.0, (f.ocr_confidence or 60.0) / 100.0), quality=0.70,
                independence_group="video_frame_ocr", source="Tesseract OCR (frame)",
                provenance=_frame_prov(f, confidence=f.ocr_confidence)))
        mm = f.multimodal
        if mm is not None and getattr(mm, "model_used", None):
            items.append(NormalizedEvidenceItem(
                evidence_id=f"ev_video_{f.frame_ref}_multimodal", evidence_type="MULTIMODAL_VISION",
                description=(f"Multimodal AI ({mm.model_used}) on {f.frame_ref} only: "
                             f"{mm.ai_generation_assessment} (model-assessed confidence {mm.confidence:.2f}). Advisory."),
                direction="NEUTRAL", target_hypothesis="CONTEXTUAL", reliability=0.0, quality=0.0,
                confidence=mm.confidence, independence_group="video_multimodal",
                source=f"Multimodal AI ({mm.model_used})",
                provenance=_frame_prov(f, assessment=mm.ai_generation_assessment, model=mm.model_used),
                limitations=["One extracted frame cannot support a video-level authenticity or AI-generation judgement; "
                             "recorded for transparency and given no verdict weight."] + list(mm.limitations)))

    cc = video.claim_comparison
    if cc is not None:
        direction = "INSUFFICIENT_TEXT" if cc.relationship == "INSUFFICIENT_EVIDENCE" else cc.relationship
        hit = cc.relationship in ("SUPPORTS", "PARTIALLY_SUPPORTS", "CONTRADICTS")
        q = max(0.0, min(1.0, cc.ocr_quality))
        frames = cc.supporting_frames + cc.contradicting_frames
        by_ref = {f.frame_ref: f for f in video.frames}
        items.append(NormalizedEvidenceItem(
            evidence_id="ev_video_claim_text", evidence_type="IMAGE_TEXT",
            description=f"Text in sampled video frames vs the claim ({cc.relationship}): {cc.explanation}",
            direction=direction, target_hypothesis="CONTEXTUAL",
            reliability=min(0.60, q) if hit else 0.0, quality=q if hit else 0.0,
            independence_group="video_frame_text", source=cc.source,
            provenance={**_SRC, "relationship": cc.relationship, "ocr_quality": q, "frames": [
                {"frame_ref": r, "frame_index": by_ref[r].frame_index, "timestamp_seconds": by_ref[r].timestamp_seconds}
                for r in frames if r in by_ref]},
            limitations=["On-screen text is not proof a statement is true; only 3 sampled frames were read."]))
    return items
