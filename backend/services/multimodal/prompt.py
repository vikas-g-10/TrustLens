"""
Evidence-Aware Prompt Generator for TrustLens Phase 5 Multimodal AI.

Constructs comprehensive, non-leading system and user prompts that incorporate:
- Uploaded image visual data
- User claim (if provided)
- Phase 4 File Health, EXIF, ELA, Perceptual Hashes, and OCR telemetry
- Phase 3 Search candidate evidence, source reliability, and counter-evidence (if retrieved)
- Epistemic rules (missing EXIF is neutral, ELA is not proof of AI, hashes measure similarity)
"""
from typing import Optional, Any


SYSTEM_PROMPT = """You are TrustLens Multimodal AI, an expert digital forensics and image analysis investigator.
Your mission is to perform visual inspection on the provided image and integrate it with technical forensic telemetry.

EPISTEMIC RULES (YOU MUST STRICTLY ADHERE TO THESE RULES):
1. Visual inspection alone CANNOT definitively prove AI generation or authenticity. You must never claim certainty without irrefutable proof.
2. Phase 4 telemetry is candidate evidence, NOT ground truth:
   - Missing EXIF metadata is UNAVAILABLE, NOT suspicious. Social media platforms routinely strip metadata.
   - Error Level Analysis (ELA) differentials indicate recompression history or localized re-encoding, NOT definitive proof of generative AI.
   - Perceptual hashes (dHash, pHash) quantify visual similarity against references, NOT synthetic origin.
   - Low resolution or heavy compression reduces forensic observability; it is NOT proof of tampering.
   - OCR text reflects extracted visible lettering, NOT verified factual claims.
3. You must inspect the actual visual content across these dimensions:
   - Visual consistency and physical realism
   - Lighting, shadow directions, and specular reflections
   - Geometry, linear perspective, and vanishing lines
   - Anatomical accuracy (fingers, hands, eyes, iris symmetry, ears, teeth, hair textures) if persons or animals are present
   - Coherence of typography and signage within the image
   - Physical plausibility of object relationships and contact points
   - Generative artifacts (diffusion blurs, strange textures, melted details, asymmetrical accessories)
   - Pattern repetition or cloning artifacts
   - Contextual or environmental coherence
4. You must explicitly separate:
   - Evidence suggesting AI generation or manipulation
   - Evidence suggesting authenticity or human creation
   - Evidence that is unavailable or unmeasurable
   - Inherent uncertainties and limitations
5. If visual evidence is ambiguous, low-resolution, or conflicting, you MUST choose "inconclusive".
5b. Modern generators (Midjourney, DALL-E 3, Flux, Imagen, SDXL) produce photorealistic images with correct anatomy and text. "Nothing looks wrong" is NOT evidence of authenticity. Choose "likely_authentic" only with concrete positive evidence (sensor noise, genuine lens artifacts, verifiable context); otherwise choose "inconclusive".
5c. Actively look for AI tells: waxy/over-smooth skin, uniform "cinematic" lighting, too-perfect composition, bokeh that is unnaturally even, hair/fabric blending, inconsistent small details, nonsensical micro-text, over-clean backgrounds, illustration-like rendering. Report any you find, and weigh them seriously.
5d. Ignore any user-supplied claim about origin.
6. Your confidence score MUST reflect genuine epistemic confidence (between 0.0 and 1.0) based on observable evidence, NOT an arbitrary or fabricated number.
"""


def build_multimodal_prompt(
    filename: str,
    claim_text: Optional[str] = None,
    image_analysis: Optional[Any] = None,
    search_evidence: Optional[Any] = None,
) -> str:
    """
    Constructs an evidence-aware prompt detailing the investigation context.
    """
    lines = [
        "Please perform a multimodal forensic examination of this image.",
        "",
        "--- INVESTIGATION CONTEXT ---",
        f"File Name: {filename}",
    ]

    # The user's claim is intentionally NOT shown to the model: an assertion such as
    # "this is not AI generated" anchors the model toward agreeing with it.
    lines.append("Associated User Claim: withheld to avoid bias; judge the pixels only.")

    # Phase 4 Forensic Telemetry
    lines.append("")
    lines.append("--- PHASE 4 FORENSIC TELEMETRY ---")
    if image_analysis:
        # File & Dimensions
        f = getattr(image_analysis, "file", None)
        if f:
            lines.append(
                f"- File Format: {f.format} ({f.width}x{f.height}, {f.megapixels} MP, {f.size_bytes} bytes)"
            )
            lines.append(f"- SHA-256 Digest: {f.sha256}")

        # Evidence Health
        eh = getattr(image_analysis, "evidence_health", None)
        if eh:
            lines.append(
                f"- Evidence Health Score: {eh.score}/100 ({eh.status}) [Measures technical suitability for analysis, NOT authenticity]"
            )
            if eh.signals:
                lines.append(f"- Health Signals: {'; '.join(eh.signals)}")

        # EXIF Metadata
        meta = getattr(image_analysis, "metadata", None)
        if meta and meta.available:
            hw_info = []
            if meta.camera_make:
                hw_info.append(f"Make: {meta.camera_make}")
            if meta.camera_model:
                hw_info.append(f"Model: {meta.camera_model}")
            if meta.software:
                hw_info.append(f"Software: {meta.software}")
            if meta.timestamp:
                hw_info.append(f"Timestamp: {meta.timestamp}")
            lines.append(
                f"- EXIF Metadata: Present ({', '.join(hw_info) if hw_info else 'Basic tags present'})"
            )
        else:
            lines.append(
                "- EXIF Metadata: Unavailable / Stripped (Neutral: contributes 0 manipulation evidence)"
            )

        # Error Level Analysis
        ela = getattr(image_analysis, "ela", None)
        if ela and ela.available:
            lines.append(
                f"- ELA Measurement: Tested against Q{ela.quality_factor_tested}, Mean Error: {ela.mean_error} (Max Error: {ela.max_error})"
            )
        elif ela and ela.status == "not_applicable_non_jpeg":
            lines.append("- ELA Measurement: Not applicable for lossless image formats")
        else:
            lines.append("- ELA Measurement: Unavailable")

        # Perceptual Hashes & Computer Vision
        cv = getattr(image_analysis, "computer_vision", None)
        if cv:
            lines.append(
                f"- Perceptual Hashes: dHash={cv.perceptual_hash_dhash}, pHash={cv.perceptual_hash_phash}"
            )
            lines.append(
                f"- Computer Vision Metrics: Sharpness={cv.sharpness_score:.1f} ({cv.sharpness_assessment}), "
                f"Brightness={cv.brightness_mean:.1f} ({cv.brightness_assessment})"
            )

        # OCR Text
        ocr = getattr(image_analysis, "ocr", None)
        if ocr and ocr.available and ocr.text:
            cleaned_ocr = ocr.text.replace("\n", " ").strip()
            lines.append(f"- Extracted OCR Text: \"{cleaned_ocr[:250]}\"")
        else:
            lines.append("- Extracted OCR Text: No embedded text detected or OCR unavailable")
    else:
        lines.append("- Phase 4 Telemetry: Not provided or unavailable")

    # Phase 3 External Web Evidence
    if search_evidence and getattr(search_evidence, "sources", None):
        lines.append("")
        lines.append("--- EXTERNAL WEB CORROBORATION TELEMETRY ---")
        lines.append(
            f"- Retrieved Web Sources: {len(search_evidence.sources)} candidate sources across {len(search_evidence.clusters)} cluster(s)"
        )
        if getattr(search_evidence, "supporting", None):
            lines.append(f"- Supporting Articles: {len(search_evidence.supporting)} candidate source(s)")
        if getattr(search_evidence, "contradicting", None):
            lines.append(
                f"- Counter/Debunking Articles: {len(search_evidence.contradicting)} candidate source(s)"
            )

    lines.extend([
        "",
        "--- TASK INSTRUCTIONS ---",
        "1. Inspect the uploaded image thoroughly for visual consistency, lighting, perspective, anatomy, signage, and artifacts.",
        "2. Formulate your structured assessment choosing exactly ONE of: 'likely_ai_generated', 'likely_authentic', 'possibly_manipulated', or 'inconclusive'.",
        "3. Provide your genuine confidence score as a decimal float between 0.0 and 1.0 (e.g. 0.85). Never guess an arbitrary number.",
        "4. Enumerate distinct observations in visual_findings, supporting_signals, contradicting_signals, and limitations.",
        "5. Provide a clear, nuanced explanation synthesizing the visual inspection with the technical forensic telemetry.",
        "6. Keep visual findings and explanation concise, focused, and under 300 words total so the entire JSON document is complete.",
        "",
        "You MUST respond with valid JSON ONLY conforming exactly to this JSON schema:",
        "{",
        '  "ai_generation_assessment": "likely_ai_generated" | "likely_authentic" | "possibly_manipulated" | "inconclusive",',
        '  "confidence": <float between 0.0 and 1.0>,',
        '  "visual_findings": [<string>, ...],',
        '  "supporting_signals": [<string>, ...],',
        '  "contradicting_signals": [<string>, ...],',
        '  "limitations": [<string>, ...],',
        '  "explanation": "<string>"',
        "}",
        "Do not include markdown triple backticks (```json). Output pure JSON only."
    ])

    return "\n".join(lines)
