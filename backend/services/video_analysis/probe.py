"""
Video probing & decode validation for TrustLens Phase 8.

Reports only what is actually measured. ffprobe (if installed) supplies container/stream
facts; OpenCV is used to prove the video is really decodable. Anything that cannot be
measured stays None, it is never guessed.
"""
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

import cv2

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi"}
# Tokens that ffprobe may report in format_name for the supported containers.
ALLOWED_CONTAINER_TOKENS = {"mov", "mp4", "matroska", "webm", "avi"}
FFPROBE_TIMEOUT_SECONDS = 20


def is_video_upload(filename: str, content_type: str = "") -> bool:
    """Route an upload to the video pipeline by extension or declared MIME type (else: image pipeline)."""
    name = (filename or "").lower()
    return any(name.endswith(ext) for ext in ALLOWED_EXTENSIONS) or (content_type or "").lower().startswith("video/")


class VideoProbeError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ProbeResult:
    container: Optional[str] = None
    codec: Optional[str] = None
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_rate: Optional[float] = None
    frame_count: Optional[int] = None
    frame_count_source: Optional[str] = None
    decodable: bool = False
    probe_tool: str = "none"
    notes: List[str] = field(default_factory=list)


def _to_float(v) -> Optional[float]:
    try:
        f = float(v)
        return f if f == f and f > 0 else None  # drop NaN / non-positive
    except (TypeError, ValueError):
        return None


def _to_int(v) -> Optional[int]:
    """Positive integer from an int, an integer-valued string ("30") or an integral float (30.0).

    OpenCV's VideoCapture.get() always returns floats, so int(str(v)) used to raise on "30.0" and
    silently discard real measurements (frame count, width, height). Non-integral floats are rejected
    rather than truncated, and NaN/inf/non-positive values are dropped.
    """
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")) or f <= 0 or f != int(f):
        return None
    return int(f)


def _parse_rate(rate: Optional[str]) -> Optional[float]:
    if not rate or "/" not in rate:
        return _to_float(rate)
    num, _, den = rate.partition("/")
    n, d = _to_float(num), _to_float(den)
    return (n / d) if n and d else None


def _run_ffprobe(path: str) -> Optional[dict]:
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [exe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
            capture_output=True, text=True, timeout=FFPROBE_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise VideoProbeError("PROBE_FAILED", f"ffprobe could not inspect the file: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip().splitlines()[:1]
        raise VideoProbeError(
            "INVALID_VIDEO",
            "The file is not a readable video container" + (f" ({detail[0]})" if detail else "."),
        )
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise VideoProbeError("PROBE_FAILED", "ffprobe returned unreadable output.") from exc


def probe_video(path: str) -> ProbeResult:
    """Probe + decode-check a video on disk. Raises VideoProbeError if it is not a usable video."""
    res = ProbeResult()
    info = _run_ffprobe(path)
    container_validated = info is not None  # ffprobe parsed a real container with a video stream

    if info is not None:
        res.probe_tool = "ffprobe+opencv"
        fmt = info.get("format", {}) or {}
        res.container = fmt.get("format_name")
        tokens = set((res.container or "").lower().split(","))
        if not tokens & ALLOWED_CONTAINER_TOKENS:
            raise VideoProbeError(
                "UNSUPPORTED_CONTAINER",
                f"Container '{res.container}' is not supported (supported: MP4, MOV, WebM, AVI).",
            )
        vstreams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
        if not vstreams:
            raise VideoProbeError("NO_VIDEO_STREAM", "The file contains no video stream.")
        v = vstreams[0]
        res.codec = v.get("codec_name")
        res.width, res.height = _to_int(v.get("width")), _to_int(v.get("height"))
        res.frame_rate = _parse_rate(v.get("avg_frame_rate")) or _parse_rate(v.get("r_frame_rate"))
        res.duration_seconds = _to_float(v.get("duration")) or _to_float(fmt.get("duration"))
        nb = _to_int(v.get("nb_frames"))
        if nb:
            res.frame_count, res.frame_count_source = nb, "container"
    else:
        res.probe_tool = "opencv"
        res.notes.append("ffprobe is not installed; container and codec could not be determined.")

    # Decode proof via OpenCV (also fills gaps left by the container probe)
    cap = cv2.VideoCapture(path)
    try:
        opened = cap.isOpened()
        ok, frame = cap.read() if opened else (False, None)
        if not opened or not ok or frame is None:
            reason = ("could not be opened by the decoder" if not opened
                      else "opened but no frame could be decoded")
            if container_validated:
                # ffprobe proved a well-formed container + video stream, so this is a decoder
                # limitation (e.g. codec unsupported by this OpenCV build), not a corrupt file.
                raise VideoProbeError(
                    "UNDECODABLE_VIDEO",
                    f"The video container is valid but its video stream {reason} (codec may be unsupported here).")
            # Without ffprobe nothing vouches for the file, so a decode failure means it is malformed,
            # truncated or not a video. (Cannot be distinguished from an unsupported codec in this mode.)
            raise VideoProbeError("INVALID_VIDEO", f"The file is not a readable video: it {reason}.")
        res.decodable = True
        res.width = res.width or _to_int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or int(frame.shape[1])
        res.height = res.height or _to_int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or int(frame.shape[0])
        res.frame_rate = res.frame_rate or _to_float(cap.get(cv2.CAP_PROP_FPS))
        if not res.frame_count:
            cv_count = _to_int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if cv_count:
                res.frame_count, res.frame_count_source = cv_count, "container"
    finally:
        cap.release()

    if not res.duration_seconds and res.frame_count and res.frame_rate:
        res.duration_seconds = round(res.frame_count / res.frame_rate, 3)
        res.notes.append("Duration was derived from frame count / frame rate.")
    if not res.frame_count and res.duration_seconds and res.frame_rate:
        res.frame_count = max(1, int(round(res.duration_seconds * res.frame_rate)))
        res.frame_count_source = "estimated_from_duration"
        res.notes.append("Frame count is an estimate (duration x frame rate); the container did not report it.")
    if not res.frame_count:
        res.notes.append("Frame count unavailable; only the first frame can be sampled deterministically.")
    return res
