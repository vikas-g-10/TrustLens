"""
AI-generation provenance scanner for TrustLens.

Looks for *explicit, machine-readable* declarations that an image was generated
by an AI tool. This is high-precision evidence (a positive hit is strong), but
low-recall: most AI images shared online have had these markers stripped, so
"no marker found" is NEUTRAL and must never be read as "authentic".

Checks:
  1. C2PA / JUMBF Content Credentials (and whether they mention an AI generator)
  2. IPTC/XMP DigitalSourceType = trainedAlgorithmicMedia / compositeSynthetic
  3. PNG text chunks written by Stable Diffusion / ComfyUI / A1111 / NovelAI
  4. Generator names in EXIF Software, XMP, or other embedded strings
"""
import re
from typing import List, Optional
from PIL import Image

from backend.schemas.image_analysis import ProvenanceSignals

AI_GENERATOR_MARKERS = [
    "midjourney", "dall-e", "dall·e", "dalle", "openai", "stable diffusion",
    "stablediffusion", "sdxl", "comfyui", "automatic1111", "invokeai",
    "novelai", "firefly", "adobe firefly", "imagen", "google ai", "synthid",
    "gemini", "leonardo.ai", "ideogram", "flux", "playground ai", "nightcafe",
    "dreamstudio", "bing image creator", "microsoft designer", "runway",
    "craiyon", "canva ai", "magic media", "grok", "aurora", "recraft",
]

PNG_AI_CHUNK_KEYS = {"parameters", "prompt", "workflow", "negative prompt",
                     "sd-metadata", "comment", "description", "software", "dream"}

_DST_PATTERN = re.compile(rb"(trainedAlgorithmicMedia|compositeSynthetic|algorithmicMedia)")
_MARKER_PATTERN = re.compile(
    "|".join(re.escape(m) for m in AI_GENERATOR_MARKERS).encode(), re.IGNORECASE
)


def scan_ai_provenance(img: Image.Image, file_bytes: bytes) -> ProvenanceSignals:
    signals: List[str] = []
    generator: Optional[str] = None

    # 1. C2PA / JUMBF manifest
    has_c2pa = b"c2pa" in file_bytes[:2_000_000] or b"jumb" in file_bytes[:2_000_000]
    if has_c2pa:
        signals.append("C2PA/JUMBF Content Credentials manifest present.")

    # 2. IPTC / XMP DigitalSourceType
    dst = _DST_PATTERN.search(file_bytes)
    if dst:
        signals.append(f"DigitalSourceType declares synthetic media: '{dst.group(1).decode()}'.")

    # 3. PNG text chunks (SD / ComfyUI / A1111 / NovelAI)
    info = getattr(img, "info", {}) or {}
    for key, val in info.items():
        k = str(key).lower()
        if k in PNG_AI_CHUNK_KEYS and isinstance(val, (str, bytes)):
            text = val.decode("latin-1", "ignore") if isinstance(val, bytes) else val
            low = text.lower()
            if k in ("parameters", "prompt", "workflow", "negative prompt", "sd-metadata", "dream") or \
               any(m in low for m in AI_GENERATOR_MARKERS) or "steps:" in low and "sampler" in low:
                signals.append(f"PNG text chunk '{key}' contains generation parameters/prompt data.")
                generator = generator or "Stable Diffusion-style pipeline"

    # 4. Generator names anywhere in headers (first 256 KB covers EXIF/XMP/PNG chunks)
    m = _MARKER_PATTERN.search(file_bytes[:262_144])
    if m:
        name = m.group(0).decode("latin-1", "ignore")
        generator = generator or name
        signals.append(f"Embedded metadata references AI tool: '{name}'.")

    # Require the weaker string-match to be corroborated or be a distinctive name,
    # but any DigitalSourceType / SD param chunk is decisive by itself.
    strong = bool(dst) or any("generation parameters" in s for s in signals) or \
             (has_c2pa and generator is not None)
    detected = strong or generator is not None

    return ProvenanceSignals(
        ai_marker_detected=detected,
        strong=strong,
        generator=generator,
        c2pa_present=has_c2pa,
        signals=signals,
    )
