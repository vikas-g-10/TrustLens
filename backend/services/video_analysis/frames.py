"""
Deterministic representative-frame extraction for TrustLens Phase 8.

Samples at most three frames (beginning / middle / end). It never processes every frame.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2

BACKOFF_FRAMES = 10  # if the exact end frame cannot be decoded, step back at most this far
MAX_FRAME_SIDE_ON_RETRY = 1280
THUMB_WIDTH = 320


@dataclass
class ExtractedFrame:
    position: str                 # beginning | middle | end
    requested_index: int
    frame_index: int              # index actually decoded (may differ from requested at the very end)
    timestamp_seconds: Optional[float]
    image: Optional[object] = None  # BGR ndarray, or None when decoding failed
    error: Optional[str] = None


def sample_targets(frame_count: Optional[int]) -> List[Tuple[str, int]]:
    """Deterministic (position, index) targets; duplicates collapse (first label wins)."""
    if not frame_count or frame_count < 1:
        return [("beginning", 0)]
    wanted = [("beginning", 0), ("middle", frame_count // 2), ("end", frame_count - 1)]
    seen, out = set(), []
    for pos, idx in wanted:
        if idx not in seen:
            seen.add(idx)
            out.append((pos, idx))
    return out


MAX_SEQUENTIAL_GRABS = 20000  # upper bound on frames skipped (not analyzed) by the sequential fallback


def _read_by_seek(cap, idx: int):
    """Seek to idx and decode. Returns the frame only if the decoder confirms it landed on idx.

    CAP_PROP_POS_FRAMES seeking is codec/backend dependent: a failed or imprecise seek can silently
    return a different frame, so the landing position is verified instead of trusted.
    """
    if not cap.set(cv2.CAP_PROP_POS_FRAMES, idx):
        return None
    ok, img = cap.read()
    if not ok or img is None:
        return None
    pos = cap.get(cv2.CAP_PROP_POS_FRAMES)  # index of the NEXT frame to be decoded
    if pos and int(round(pos)) != idx + 1:
        return None  # seek landed elsewhere; do not claim this is frame idx
    return img


def _read_sequential(path: str, idx: int):
    """Decode from the start and return exactly frame idx (slow but exact; works on unseekable streams)."""
    if idx > MAX_SEQUENTIAL_GRABS:
        return None
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            return None
        for _ in range(idx):
            if not cap.grab():
                return None  # video is shorter than the requested index
        ok, img = cap.read()
        return img if ok and img is not None else None
    finally:
        cap.release()


def _read_frame(cap, path: str, idx: int):
    img = _read_by_seek(cap, idx)
    return img if img is not None else _read_sequential(path, idx)


def extract_frames(path: str, frame_count: Optional[int], fps: Optional[float]) -> List[ExtractedFrame]:
    """Decode the beginning/middle/end frames. Every returned image is a real decoded frame.

    frame_index is the index actually decoded (the end target may back off a few frames if the very
    last frame is undecodable); timestamp is frame_index / fps, or None when fps is unknown.
    """
    results: List[ExtractedFrame] = []
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            return [ExtractedFrame(p, i, i, None, None, "Video could not be reopened for frame extraction.")
                    for p, i in sample_targets(frame_count)]
        for pos, idx in sample_targets(frame_count):
            frame, used = None, idx
            for back in range(0, min(BACKOFF_FRAMES, idx) + 1):
                used = idx - back
                img = _read_frame(cap, path, used)
                if img is not None:
                    frame = img
                    break
            if frame is None:
                results.append(ExtractedFrame(pos, idx, idx, round(idx / fps, 3) if fps else None, None,
                                              f"Frame {idx} could not be decoded."))
            else:
                results.append(ExtractedFrame(pos, idx, used, round(used / fps, 3) if fps else None, frame, None))
    finally:
        cap.release()
    return results


def encode_frame_png(frame, max_bytes: int) -> Tuple[bytes, bool]:
    """Lossless PNG (no new compression artefacts). Downscales once only if over max_bytes."""
    ok, buf = cv2.imencode(".png", frame)
    if not ok:
        raise ValueError("PNG encoding failed")
    data, downscaled = buf.tobytes(), False
    if len(data) > max_bytes:
        h, w = frame.shape[:2]
        scale = MAX_FRAME_SIDE_ON_RETRY / max(h, w)
        if scale < 1.0:
            small = cv2.resize(frame, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".png", small)
            if not ok:
                raise ValueError("PNG encoding failed")
            data, downscaled = buf.tobytes(), True
    return data, downscaled


def thumbnail_data_url(frame) -> Optional[str]:
    import base64
    h, w = frame.shape[:2]
    scale = THUMB_WIDTH / float(w) if w > THUMB_WIDTH else 1.0
    small = cv2.resize(frame, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", small, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    if not ok:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")
