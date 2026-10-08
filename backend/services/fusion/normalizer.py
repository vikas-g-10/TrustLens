"""
Evidence Normalizer for TrustLens Phase 6.

Translates disparate signals across Phase 4 Image Forensics, Phase 5 Multimodal AI,
Phase 3 Search Retrieval, and Phase 2 URL Security into a unified, common internal
representation of structured NormalizedEvidenceItem vectors.

Guarantees:
1. Missing EXIF metadata contributes ZERO evidence (NEUTRAL, weight 0.0, no negative penalty).
2. Unavailable forensic detectors remain unavailable with zero fabricated values.
3. Model confidence is preserved as reported by originating components, never treated as absolute truth.
4. Source clustering IDs are preserved for independence de-duplication.
"""
from typing import Any, Dict, List, Optional
from backend.schemas.fusion import (
    NormalizedEvidenceItem,
    EvidenceDirection,
    EvidenceType,
    TargetHypothesis,
)
from backend.schemas.image_analysis import ImageAnalysisResponse
from backend.schemas.investigation import (
    MultimodalAiResult,
    ImageTextEvidence,
    UrlAnalysisOutcome,
    UrlAnalysisOutcomeSuccess,
    UrlAnalysisOutcomeFailure,
)
from backend.schemas.search import SearchEvidence


def normalize_all_evidence(
    claim_text: str = "",
    url_text: str = "",
    url_outcome: Optional[UrlAnalysisOutcome] = None,
    image_analysis: Optional[ImageAnalysisResponse] = None,
    search_evidence: Optional[SearchEvidence] = None,
    multimodal_result: Optional[MultimodalAiResult] = None,
    image_text_evidence: Optional[ImageTextEvidence] = None,
    video_analysis: Optional[Any] = None,
) -> List[NormalizedEvidenceItem]:
    """
    Normalizes all ingested telemetry into discrete NormalizedEvidenceItem objects.
    """
    items: List[NormalizedEvidenceItem] = []

    # =========================================================================
    # 1. Media File Integrity & Evidence Health (Phase 4)
    # =========================================================================
    if image_analysis:
        f = image_analysis.file
        eh = image_analysis.evidence_health

        if not f.is_valid or f.corruption_detected:
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_file_corruption",
                    evidence_type="FILE_INTEGRITY",
                    description=f"File validation failed or corruption detected for {f.filename}.",
                    direction="CONTRADICTS",
                    target_hypothesis="MANIPULATED",
                    reliability=0.90,
                    quality=1.00,
                    independence_group="file_decoder",
                    source="Pillow Image Decoder",
                    provenance={"filename": f.filename, "sha256": f.sha256},
                    confidence=1.00,
                    limitations=["Pixel-level analysis aborted due to container decode corruption."],
                )
            )
        else:
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_file_valid",
                    evidence_type="FILE_INTEGRITY",
                    description=(
                        f"Image container verified: {f.format} ({f.width}x{f.height}, "
                        f"{f.megapixels} MP, mode {f.image_mode}, SHA-256: {f.sha256[:12]}…)."
                    ),
                    direction="NEUTRAL",
                    target_hypothesis="CONTEXTUAL",
                    reliability=0.60,
                    quality=min(1.0, max(0.2, f.megapixels / 2.0)),
                    independence_group="file_decoder",
                    source="Pillow Image Decoder",
                    provenance={"filename": f.filename, "sha256": f.sha256, "format": f.format},
                    confidence=1.00,
                )
            )

        # Evidence Health (Measures forensic utility, NEVER authenticity directly)
        items.append(
            NormalizedEvidenceItem(
                evidence_id="ev_evidence_health",
                evidence_type="FILE_INTEGRITY",
                description=(
                    f"Evidence Health scored {eh.score}/100 ({eh.status}). "
                    f"Technical suitability for digital analysis verified."
                ),
                direction="NEUTRAL",
                target_hypothesis="CONTEXTUAL",
                reliability=0.50,
                quality=eh.score / 100.0,
                independence_group="evidence_health",
                source="Evidence Health Evaluator",
                provenance={"score": eh.score, "status": eh.status},
                limitations=["Evidence Health measures technical suitability for analysis, not real-world truth."],
            )
        )

        # =====================================================================
        # 2. EXIF Metadata (Phase 4)
        # =====================================================================
        meta = image_analysis.metadata
        if not meta.available:
            # Epistemic Rule: Missing EXIF is NOT suspicious
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_exif_metadata_missing",
                    evidence_type="METADATA_EXIF",
                    description=(
                        "EXIF metadata unavailable (neutral); social platforms and messaging apps routinely strip metadata. "
                        "Contributes zero negative evidence."
                    ),
                    direction="NEUTRAL",
                    target_hypothesis="CONTEXTUAL",
                    reliability=0.0,
                    quality=0.0,
                    weight=0.0,
                    independence_group="exif_metadata",
                    source="EXIF Extraction Module",
                    provenance={"metadata_status": "unavailable"},
                    limitations=["Missing metadata does not indicate tampering; social platforms routinely strip metadata."],
                )
            )
        else:
            if meta.editing_software:
                items.append(
                    NormalizedEvidenceItem(
                        evidence_id="ev_exif_editing_software",
                        evidence_type="METADATA_EXIF",
                        description=f"EXIF header records software post-processing or image manipulation tool: {meta.editing_software}.",
                        direction="CONTRADICTS",
                        target_hypothesis="MANIPULATED",
                        reliability=0.85,
                        quality=meta.completeness_score or 0.8,
                        independence_group="exif_metadata",
                        source="EXIF Extraction Module",
                        provenance={"software": meta.software, "editing_software": meta.editing_software},
                    )
                )
            elif meta.camera_make or meta.camera_model:
                items.append(
                    NormalizedEvidenceItem(
                        evidence_id="ev_exif_camera_hardware",
                        evidence_type="METADATA_EXIF",
                        description=f"EXIF metadata contains authentic physical camera signature: {meta.camera_make or ''} {meta.camera_model or ''}.".strip(),
                        direction="SUPPORTS",
                        target_hypothesis="AUTHENTIC",
                        reliability=0.80,
                        quality=meta.completeness_score or 0.8,
                        independence_group="exif_metadata",
                        source="EXIF Extraction Module",
                        provenance={"camera_make": meta.camera_make, "camera_model": meta.camera_model, "timestamp": meta.timestamp},
                    )
                )
            else:
                items.append(
                    NormalizedEvidenceItem(
                        evidence_id="ev_exif_generic_present",
                        evidence_type="METADATA_EXIF",
                        description=f"EXIF metadata present ({meta.raw_tags_count} tags) with neutral headers.",
                        direction="NEUTRAL",
                        target_hypothesis="CONTEXTUAL",
                        reliability=0.30,
                        quality=meta.completeness_score or 0.5,
                        independence_group="exif_metadata",
                        source="EXIF Extraction Module",
                        provenance={"raw_tags_count": meta.raw_tags_count},
                    )
                )

        # =====================================================================
        # 3. Error Level Analysis (Phase 4)
        # =====================================================================
        ela = image_analysis.ela
        if not ela.available:
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_ela_unavailable",
                    evidence_type="IMAGE_ELA",
                    description=f"Error Level Analysis unavailable ({ela.notes[0] if ela.notes else 'non-JPEG format'}).",
                    direction="NEUTRAL",
                    target_hypothesis="CONTEXTUAL",
                    reliability=0.0,
                    quality=0.0,
                    weight=0.0,
                    independence_group="ela_module",
                    source="Error Level Analysis Engine",
                    limitations=["ELA is applicable exclusively to lossy baseline JPEG compression."],
                )
            )
        else:
            mean_err = ela.mean_error or 0.0
            if mean_err > 12.0:
                items.append(
                    NormalizedEvidenceItem(
                        evidence_id="ev_ela_differential",
                        evidence_type="IMAGE_ELA",
                        description=(
                            f"Error Level Analysis against Q{ela.quality_factor_tested} detected localized high error "
                            f"differentials (mean error: {mean_err:.2f}, max error: {ela.max_error}). Potential composite."
                        ),
                        direction="CONTRADICTS",
                        target_hypothesis="MANIPULATED",
                        reliability=0.65,
                        quality=0.80,
                        independence_group="ela_module",
                        source="Error Level Analysis Engine",
                        provenance={"mean_error": mean_err, "max_error": ela.max_error, "q_tested": ela.quality_factor_tested},
                        limitations=["ELA error spikes can occasionally result from multiple legitimate re-saves."],
                    )
                )
            else:
                items.append(
                    NormalizedEvidenceItem(
                        evidence_id="ev_ela_uniform",
                        evidence_type="IMAGE_ELA",
                        description=(
                            f"Error Level Analysis against Q{ela.quality_factor_tested} demonstrates uniform pixel error "
                            f"rate (mean error: {mean_err:.2f}). No differential compression seams."
                        ),
                        direction="NEUTRAL",
                        target_hypothesis="CONTEXTUAL",
                        reliability=0.50,
                        quality=0.75,
                        weight=0.0,
                        independence_group="ela_module",
                        source="Error Level Analysis Engine",
                        provenance={"mean_error": mean_err, "q_tested": ela.quality_factor_tested},
                    )
                )

        # =====================================================================
        # 4. Computer Vision Metrics (Phase 4)
        # =====================================================================
        cv = image_analysis.computer_vision
        items.append(
            NormalizedEvidenceItem(
                evidence_id="ev_cv_metrics",
                evidence_type="PERCEPTUAL_HASH",
                description=(
                    f"Perceptual hashes computed: dHash={cv.perceptual_hash_dhash}, pHash={cv.perceptual_hash_phash}. "
                    f"Sharpness: {cv.sharpness_score:.1f} ({cv.sharpness_assessment}), contrast RMS: {cv.contrast_rms:.1f}."
                ),
                direction="NEUTRAL",
                target_hypothesis="CONTEXTUAL",
                reliability=0.30,
                quality=0.60,
                independence_group="computer_vision",
                source="Computer Vision Signal Engine",
                provenance={"dhash": cv.perceptual_hash_dhash, "phash": cv.perceptual_hash_phash},
                limitations=["Archival perceptual match database currently unavailable; serves as fingerprint only."],
            )
        )

        # AI provenance markers (C2PA / IPTC DigitalSourceType / SD params / tool names)
        prov = getattr(image_analysis, "provenance", None)
        if prov and prov.ai_marker_detected:
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_ai_provenance",
                    evidence_type="METADATA_EXIF",
                    description="Embedded provenance declares AI generation: " + " ".join(prov.signals),
                    direction="CONTRADICTS",
                    target_hypothesis="AI_GENERATED",
                    reliability=0.95 if prov.strong else 0.70,
                    quality=1.0,
                    independence_group="ai_provenance",
                    source="AI Provenance Scanner",
                    provenance={"generator": prov.generator, "c2pa": prov.c2pa_present},
                    limitations=["Markers can be stripped; absence proves nothing."],
                )
            )

        # OCR Text (if present)
        ocr = image_analysis.ocr
        if ocr.available and ocr.text:
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_ocr_text",
                    evidence_type="OCR_TEXT",
                    description=f"OCR extracted embedded text in media: \"{ocr.text[:100]}\".",
                    direction="NEUTRAL",
                    target_hypothesis="CONTEXTUAL",
                    reliability=min(1.0, (ocr.confidence or 60.0) / 100.0),
                    quality=0.70,
                    independence_group="ocr_module",
                    source="Tesseract OCR",
                    provenance={"regions_count": ocr.regions_count, "confidence": ocr.confidence},
                )
            )

    # =========================================================================
    # 4b. Image Text -> Claim Evidence
    # =========================================================================
    if image_text_evidence:
        ite = image_text_evidence
        q = max(0.0, min(1.0, ite.ocr_quality))
        hit = ite.relationship in ("SUPPORTS", "PARTIALLY_SUPPORTS", "CONTRADICTS")
        items.append(
            NormalizedEvidenceItem(
                evidence_id="ev_image_text",
                evidence_type="IMAGE_TEXT",
                description=f"Text inside the uploaded image vs the claim ({ite.relationship}): {ite.explanation}",
                direction=ite.relationship,
                # About what the image *states* relative to the claim; not an authenticity hypothesis.
                target_hypothesis="CONTEXTUAL",
                # OCR quality scales how far this evidence can be trusted (capped: image text is never proof).
                reliability=min(0.60, q) if hit else 0.0,
                quality=q if hit else 0.0,
                independence_group="image_text",
                source=ite.source,
                provenance={
                    "source": ite.source,
                    "relationship": ite.relationship,
                    "ocr_quality": q,
                    "matched_claim_points": ite.matched_claim_points,
                    "contradicted_claim_points": ite.contradicted_claim_points,
                    "missing_claim_points": ite.missing_claim_points,
                    "relevant_text": ite.relevant_text[:300],
                },
                limitations=[
                    "Text appearing in an image is not proof that the statement is true; "
                    "it only shows what the image states.",
                ],
            )
        )

    # =========================================================================
    # 5. Multimodal AI Visual Analysis (Phase 5)
    # =========================================================================
    if multimodal_result:
        assessment = multimodal_result.ai_generation_assessment
        conf = multimodal_result.confidence
        model_name = multimodal_result.model_used or "Vision AI"

        if assessment == "likely_ai_generated":
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_mm_ai_assessment",
                    evidence_type="MULTIMODAL_VISION",
                    description=(
                        f"Multimodal Vision AI ({model_name}) evaluated media as synthetic/AI-generated "
                        f"(model assessed confidence: {conf:.2f}): {multimodal_result.explanation}"
                    ),
                    direction="CONTRADICTS",
                    target_hypothesis="AI_GENERATED",
                    reliability=0.85,
                    quality=max(0.40, 1.0 - 0.08 * min(3, len(multimodal_result.limitations))),
                    confidence=conf,
                    independence_group="multimodal_vision",
                    source=f"Multimodal AI ({model_name})",
                    provenance={"assessment": assessment, "model": model_name, "findings": multimodal_result.visual_findings[:3]},
                    limitations=multimodal_result.limitations,
                )
            )
            # Add discrete visual signals as supportive micro-evidence
            for idx, sig in enumerate(multimodal_result.supporting_signals[:2]):
                items.append(
                    NormalizedEvidenceItem(
                        evidence_id=f"ev_mm_signal_ai_{idx+1}",
                        evidence_type="MULTIMODAL_VISION",
                        description=f"Visual synthetic finding: {sig}",
                        direction="CONTRADICTS",
                        target_hypothesis="AI_GENERATED",
                        reliability=0.75,
                        quality=0.80,
                        confidence=conf,
                        independence_group="multimodal_vision",
                        source=f"Multimodal AI ({model_name})",
                    )
                )

        elif assessment == "likely_authentic":
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_mm_ai_assessment",
                    evidence_type="MULTIMODAL_VISION",
                    description=(
                        f"Multimodal Vision AI ({model_name}) evaluated media as photographic content (note: vision models cannot reliably distinguish modern AI images from photos) "
                        f"(model assessed confidence: {conf:.2f}): {multimodal_result.explanation}"
                    ),
                    direction="SUPPORTS",
                    target_hypothesis="AUTHENTIC",
                    reliability=0.35,
                    quality=max(0.40, 1.0 - 0.08 * min(3, len(multimodal_result.limitations))),
                    confidence=conf,
                    independence_group="multimodal_vision",
                    source=f"Multimodal AI ({model_name})",
                    provenance={"assessment": assessment, "model": model_name, "findings": multimodal_result.visual_findings[:3]},
                    limitations=multimodal_result.limitations,
                )
            )
            for idx, sig in enumerate(multimodal_result.supporting_signals[:2]):
                items.append(
                    NormalizedEvidenceItem(
                        evidence_id=f"ev_mm_signal_auth_{idx+1}",
                        evidence_type="MULTIMODAL_VISION",
                        description=f"Visual authentic finding: {sig}",
                        direction="SUPPORTS",
                        target_hypothesis="AUTHENTIC",
                        reliability=0.30,
                        quality=0.80,
                        confidence=conf,
                        independence_group="multimodal_vision",
                        source=f"Multimodal AI ({model_name})",
                    )
                )

        elif assessment == "possibly_manipulated":
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_mm_ai_assessment",
                    evidence_type="MULTIMODAL_VISION",
                    description=(
                        f"Multimodal Vision AI ({model_name}) observed digital editing or manipulation artifacts "
                        f"(confidence: {conf:.2f}): {multimodal_result.explanation}"
                    ),
                    direction="CONTRADICTS",
                    target_hypothesis="MANIPULATED",
                    reliability=0.80,
                    quality=max(0.40, 1.0 - 0.08 * min(3, len(multimodal_result.limitations))),
                    confidence=conf,
                    independence_group="multimodal_vision",
                    source=f"Multimodal AI ({model_name})",
                    provenance={"assessment": assessment, "model": model_name, "findings": multimodal_result.visual_findings[:3]},
                    limitations=multimodal_result.limitations,
                )
            )

        else:
            # Inconclusive
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_mm_ai_inconclusive",
                    evidence_type="MULTIMODAL_VISION",
                    description=f"Multimodal Vision AI ({model_name}) was inconclusive: {multimodal_result.explanation or 'Insufficient distinct visual markers.'}",
                    direction="NEUTRAL",
                    target_hypothesis="CONTEXTUAL",
                    reliability=0.0,
                    quality=0.0,
                    weight=0.0,
                    independence_group="multimodal_vision",
                    source=f"Multimodal AI ({model_name})",
                    limitations=multimodal_result.limitations or ["Visual ambiguity prevents definitive assessment."],
                )
            )

    # =========================================================================
    # 6. Web Search External Evidence (Phase 3)
    # =========================================================================
    if search_evidence and search_evidence.sources:
        for idx, src in enumerate(search_evidence.sources):
            # Determine direction based on classifier partition
            if any(s.url == src.url for s in search_evidence.supporting):
                dir_val: EvidenceDirection = "SUPPORTS"
                hypo: TargetHypothesis = "CLAIM_TRUE"
            elif any(c.url == src.url for c in search_evidence.contradicting):
                dir_val: EvidenceDirection = "CONTRADICTS"
                hypo: TargetHypothesis = "CLAIM_FALSE"
            else:
                dir_val: EvidenceDirection = "NEUTRAL"
                hypo: TargetHypothesis = "CONTEXTUAL"

            rel_score = float(src.reliability_score or 50) / 100.0
            cluster_key = src.cluster_id or f"cluster_domain_{src.root_domain}"
            is_text_avail = (getattr(src, "content_status", "NOT_FETCHED") == "AVAILABLE")

            items.append(
                NormalizedEvidenceItem(
                    evidence_id=f"ev_web_source_{idx+1}",
                    evidence_type="WEB_SOURCE",
                    description=f"[{src.domain} · {src.reliability_score}/100] {src.title}: {src.snippet[:120]}…",
                    direction=dir_val,
                    target_hypothesis=hypo,
                    reliability=rel_score,
                    quality=0.85 if is_text_avail else 0.70,
                    independence_group=cluster_key,
                    source=src.domain,
                    provenance={
                        "url": src.url,
                        "title": src.title,
                        "domain": src.domain,
                        "reliability_score": src.reliability_score,
                        "factors": getattr(src, "reliability_factors", {}),
                        "independence_level": getattr(src, "independence_level", None),
                    },
                    limitations=[] if is_text_avail else ["Full article text was not accessible; snippet analyzed."],
                )
            )

    # =========================================================================
    # 7. URL Security Inspection (Phase 2)
    # =========================================================================
    if url_outcome:
        if isinstance(url_outcome, UrlAnalysisOutcomeSuccess) and url_outcome.ok:
            d = url_outcome.data
            has_security_red_flags = d.domain_mismatch or len(d.suspicious_structure) > 0

            if has_security_red_flags:
                items.append(
                    NormalizedEvidenceItem(
                        evidence_id="ev_url_security_flag",
                        evidence_type="URL_SECURITY",
                        description=(
                            f"URL inspection flagged security anomalies: "
                            f"{'Domain mismatch (' + d.original_domain + ' -> ' + d.final_domain + '); ' if d.domain_mismatch else ''}"
                            f"{'; '.join(d.suspicious_structure)}"
                        ),
                        direction="CONTRADICTS",
                        target_hypothesis="CLAIM_FALSE",
                        reliability=0.65,
                        quality=0.80,
                        independence_group="url_inspector",
                        source="URL Security Module",
                        provenance={"original_url": d.original_url, "final_url": d.final_url, "status_code": d.status_code},
                    )
                )
            else:
                items.append(
                    NormalizedEvidenceItem(
                        evidence_id="ev_url_security_clean",
                        evidence_type="URL_SECURITY",
                        description=f"Target URL verified ({d.final_domain}, HTTP {d.status_code}, {'HTTPS' if d.https else 'HTTP'}).",
                        direction="SUPPORTS",
                        target_hypothesis="AUTHENTIC",
                        reliability=0.45,
                        quality=0.75,
                        independence_group="url_inspector",
                        source="URL Security Module",
                        provenance={"final_url": d.final_url, "https": d.https},
                    )
                )
        elif isinstance(url_outcome, UrlAnalysisOutcomeFailure) or not url_outcome.ok:
            err = url_outcome.error
            items.append(
                NormalizedEvidenceItem(
                    evidence_id="ev_url_security_failure",
                    evidence_type="URL_SECURITY",
                    description=f"Target URL could not be retrieved ({err.code}): {err.message}.",
                    direction="NEUTRAL",
                    target_hypothesis="CONTEXTUAL",
                    reliability=0.0,
                    quality=0.0,
                    weight=0.0,
                    independence_group="url_inspector",
                    source="URL Security Module",
                    limitations=["A failed URL retrieval is not evidence that the site is fraudulent or genuine."],
                )
            )

    # =========================================================================
    # 6. Video evidence (Phase 8): representative-frame evidence, normalized separately
    # =========================================================================
    if video_analysis is not None:
        from backend.services.fusion.video_normalizer import normalize_video_evidence
        items.extend(normalize_video_evidence(video_analysis))

    return items
