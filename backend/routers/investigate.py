from datetime import datetime, timezone
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from backend.dependencies import check_rate_limit
from backend.services.url_inspector import inspect_url
from backend.services.search.search_service import SearchService, ClaimQueryGenerator
from backend.services.source_reliability import get_root_domain
from backend.schemas.search import SearchEvidence
from backend.schemas.investigation import (
    InvestigationResponse,
    AiReasoning,
    Claim,
    MediaAnalysis,
    FileHealth,
    EXIFMetadata,
    PerceptualHash,
    UrlAnalysisOutcome,
    UrlAnalysisOutcomeSuccess,
    UrlAnalysisOutcomeFailure,
    MultimodalAiResult,
    Contradiction,
)
from backend.services.image_analysis.analyzer import analyze_image_file
from backend.services.image_analysis.decoder import ImageValidationError
from backend.services.image_analysis.image_text_evidence import compare_image_text_to_claim
from backend.schemas.image_analysis import ImageAnalysisResponse
from backend.services.multimodal import analyze_multimodal_image
from backend.services.fusion import fuse_investigation_evidence
from backend.config import settings
from backend.services.video_analysis.analyzer import (
    VideoAnalysisBundle,
    add_multimodal_frame,
    analyze_video_file,
)
from backend.services.video_analysis.probe import is_video_upload

router = APIRouter(tags=["Investigation"])


def _is_video_upload(upload) -> bool:
    """Phase 8: route by extension / declared MIME type. Anything else keeps the image pipeline."""
    return is_video_upload(getattr(upload, "filename", "") or "", getattr(upload, "content_type", "") or "")


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate_claim(
    request: Request,
    _rate_limit: None = Depends(check_rate_limit),
):
    """
    Digital Investigation Endpoint (AIML prototype).

    Accepts claims, URLs, and optional image or video files (multipart/form-data or JSON).
    Executes:
    1. Image forensics & Evidence Health (if an image is provided), or video probing and
       beginning/middle/end representative-frame analysis (if a video is provided).
    2. Real SSRF-protected URL inspection (if URL provided).
    3. Deterministic multi-query search retrieval with supporting & counter evidence (if claim provided).
    4. Source reliability scoring & heuristic independence clustering.
    5. Optional multimodal AI visual inspection, recorded as one weighted evidence input.
    6. Phase 6 deterministic evidence fusion: FusionEngine is the sole author of the final verdict,
       confidence, and reason. No LLM output can override them.
    """
    content_type = request.headers.get("content-type", "")
    claim_text = ""
    url_text = ""
    file_upload = None
    image_analysis_result: Optional[ImageAnalysisResponse] = None
    image_error_msg: Optional[str] = None
    file_bytes: Optional[bytes] = None
    video_bundle: Optional[VideoAnalysisBundle] = None
    video_error_msg: Optional[str] = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            claim_text = str(body.get("claim", "")).strip()
            url_text = str(body.get("url", "")).strip()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        claim_text = str(form.get("claim", "")).strip()
        url_text = str(form.get("url", "")).strip()
        file_item = form.get("file") or form.get("image")
        if file_item and hasattr(file_item, "read") and hasattr(file_item, "filename") and file_item.filename:
            file_upload = file_item
    else:
        # Default try parsing JSON
        try:
            body = await request.json()
            claim_text = str(body.get("claim", "")).strip()
            url_text = str(body.get("url", "")).strip()
        except Exception:
            pass

    # Phase 8: uploaded video (separate branch; the image branch below is unchanged)
    if file_upload and _is_video_upload(file_upload):
        file_bytes = await file_upload.read()
        video_bundle = await analyze_video_file(
            file_bytes,
            file_upload.filename,
            getattr(file_upload, "content_type", "") or "",
            claim_text,
        )
        if not video_bundle.result.ok:
            video_error_msg = video_bundle.result.error
    # Process uploaded image if present
    elif file_upload:
        try:
            file_bytes = await file_upload.read()
            if len(file_bytes) > 0:
                image_analysis_result = analyze_image_file(
                    file_bytes,
                    file_upload.filename,
                    getattr(file_upload, "content_type", "") or "",
                )
        except ImageValidationError as ive:
            image_error_msg = ive.message
        except Exception as exc:
            image_error_msg = f"Failed to analyze image: {str(exc)}"

    video_result = video_bundle.result if video_bundle else None
    video_ok = bool(video_result and video_result.ok)
    user_claim_text = claim_text  # the claim as typed by the user (before any placeholder is applied)
    if not claim_text and image_analysis_result:
        claim_text = f"Forensic analysis of {image_analysis_result.file.filename}"
    elif not claim_text and video_ok:
        claim_text = f"Forensic analysis of {video_result.metadata.filename}"

    if not claim_text and not url_text and not image_analysis_result and not video_ok:
        err_msg = image_error_msg or video_error_msg or "A claim, URL, or image/video file is required."
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": err_msg, "detail": err_msg}
        )

    if len(claim_text) > 1000:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "The claim is too long (max 1000 characters).", "detail": "Claim exceeds 1000 characters."}
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    url_outcome: Optional[UrlAnalysisOutcome] = None
    search_evidence: Optional[SearchEvidence] = None

    # Step 1: Execute Real URL Inspection if URL is supplied
    if url_text:
        url_outcome = await inspect_url(url_text)

    # Step 2: Execute Claim-Based Search Retrieval if Claim is supplied
    if claim_text:
        search_svc = SearchService()
        search_evidence = await search_svc.investigate_claim(claim_text)

        # Do not allow a URL's own page to count as independent confirmation of itself
        if url_outcome and url_outcome.ok:
            sub_domain = url_outcome.data.final_domain.lower()
            sub_root = get_root_domain(sub_domain)
            for src in search_evidence.sources:
                if src.root_domain == sub_root or src.domain == sub_domain:
                    src.independence_level = "DUPLICATE"
                    src.classification_reason = (
                        f"{src.classification_reason} (Note: Matches submitted URL domain; cannot self-corroborate)."
                    )
            for cl in search_evidence.clusters:
                if any(m.root_domain == sub_root for m in cl.member_sources):
                    cl.reason = f"{cl.reason} (Includes submitted URL domain - not independent confirmation)."

    # Step 2.5: Execute Phase 5 Multimodal AI Visual Analysis (if image provided)
    multimodal_result: Optional[MultimodalAiResult] = None
    if image_analysis_result and file_bytes:
        try:
            multimodal_result = await analyze_multimodal_image(
                image_bytes=file_bytes,
                filename=image_analysis_result.file.filename,
                mime_type=image_analysis_result.file.mime_type,
                claim_text=claim_text,
                image_analysis=image_analysis_result,
                search_evidence=search_evidence,
            )
        except Exception as exc:
            multimodal_result = MultimodalAiResult(
                ai_generation_assessment="inconclusive",
                confidence=0.0,
                limitations=[f"Multimodal AI execution exception: {str(exc)}"],
                explanation="Multimodal AI analysis encountered an error. Investigation continues with deterministic Phase 4 forensics.",
                analyzed_at=now_iso,
            )

    # Step 2.55: Phase 8 optional multimodal inspection of ONE representative video frame
    if video_bundle and video_ok:
        await add_multimodal_frame(video_bundle, claim_text, search_evidence)

    # Step 2.6: Image text -> claim evidence (reuses the Phase 4 OCR result; no second OCR)
    image_text_evidence = None
    if image_analysis_result and user_claim_text:
        image_text_evidence = compare_image_text_to_claim(image_analysis_result.ocr, user_claim_text)

    # Step 3: Formulate Transparent Reasoning & Candidate Evidence Breakdown
    reasoning_steps: List[str] = []
    uncertainties: List[str] = []
    supporting_evidence: List[str] = []
    contradicting_evidence: List[str] = []

    if claim_text:
        reasoning_steps.append(f"Claim received: '{claim_text}'.")

    # Image telemetry integration
    if image_analysis_result:
        f = image_analysis_result.file
        eh = image_analysis_result.evidence_health
        reasoning_steps.append(
            f"Image analyzed: {f.filename} ({f.width}x{f.height}, {f.format}, {f.megapixels} MP, SHA-256: {f.sha256[:12]}…). "
            f"Evidence Health: {eh.score}/100 ({eh.status})."
        )
        if image_analysis_result.metadata.available:
            hw_str = f" ({image_analysis_result.metadata.camera_make or 'Device unspecified'})" if image_analysis_result.metadata.camera_make else ""
            reasoning_steps.append(f"EXIF metadata: {image_analysis_result.metadata.metadata_status}{hw_str}.")
        else:
            reasoning_steps.append("EXIF metadata unavailable (neutral); contributes 0 manipulation evidence.")
        if image_analysis_result.ela.available:
            reasoning_steps.append(
                f"Error Level Analysis against Q{image_analysis_result.ela.quality_factor_tested}: mean error {image_analysis_result.ela.mean_error}."
            )
        if image_analysis_result.ocr.available and image_analysis_result.ocr.text:
            reasoning_steps.append(f"OCR detected embedded text: \"{image_analysis_result.ocr.text[:100]}\".")
        if image_text_evidence:
            reasoning_steps.append(
                f"Image text vs claim: {image_text_evidence.relationship} "
                f"(OCR quality {int(image_text_evidence.ocr_quality * 100)}%). {image_text_evidence.explanation}"
            )
        if multimodal_result:
            model_tag = f" ({multimodal_result.model_used})" if multimodal_result.model_used else ""
            reasoning_steps.append(
                f"Phase 5 Multimodal AI visual inspection{model_tag}: "
                f"{multimodal_result.ai_generation_assessment.upper()} (assessed confidence: {multimodal_result.confidence:.2f}). "
                f"{multimodal_result.explanation}"
            )
            for vf in multimodal_result.visual_findings[:3]:
                reasoning_steps.append(f"Visual observation: {vf}")
            for sup in multimodal_result.supporting_signals[:2]:
                supporting_evidence.append(f"[Visual AI · {int(multimodal_result.confidence * 100)}/100] {sup}")
            for con in multimodal_result.contradicting_signals[:2]:
                contradicting_evidence.append(f"[Visual AI · {int(multimodal_result.confidence * 100)}/100] {con}")
            for lim in multimodal_result.limitations:
                if lim not in uncertainties:
                    uncertainties.append(lim)
    elif image_error_msg:
        uncertainties.append(f"Uploaded media could not be analyzed: {image_error_msg}")
        reasoning_steps.append(f"Image analysis error: {image_error_msg}")

    # Phase 8 video telemetry (evidence only; the verdict comes from Phase 6 fusion)
    if video_result:
        if video_ok:
            vm = video_result.metadata
            reasoning_steps.append(
                f"Video analyzed: {vm.filename} ({vm.container or 'container unknown'}, "
                f"{vm.width}x{vm.height}, {vm.duration_seconds}s, {vm.frame_rate} fps, {vm.frame_count} frames "
                f"[{vm.frame_count_source or 'unknown'}]). {sum(1 for f in video_result.frames if f.decoded)}/"
                f"{len(video_result.frames)} representative frame(s) decoded and analyzed."
            )
            for vf in video_result.frames:
                if vf.decoded:
                    reasoning_steps.append(
                        f"Frame {vf.frame_index} (t={vf.timestamp_seconds}s, {vf.position}): Evidence Health "
                        f"{vf.quality_score}/100; OCR {'text found' if vf.ocr_text.strip() else 'no text'}."
                    )
            if video_result.claim_comparison:
                reasoning_steps.append(
                    f"Video text vs claim: {video_result.claim_comparison.relationship}. "
                    f"{video_result.claim_comparison.explanation}"
                )
        else:
            uncertainties.append(f"Uploaded video could not be analyzed: {video_error_msg}")
            reasoning_steps.append(f"Video analysis error: {video_error_msg}")
        for lim in video_result.limitations:
            if lim not in uncertainties:
                uncertainties.append(lim)

    # URL Telemetry integration
    if url_text:
        if isinstance(url_outcome, UrlAnalysisOutcomeFailure) or (url_outcome and not url_outcome.ok):
            err = url_outcome.error
            uncertainties.append(f"Target URL failed verification: {err.message}.")
            reasoning_steps.append(f"URL inspection failed ({err.code}): {err.message}.")
        elif url_outcome and url_outcome.ok:
            d = url_outcome.data
            flags = []
            if d.domain_mismatch:
                flags.append(f"domain mismatch ({d.original_domain} → {d.final_domain})")
            if d.tracking_params:
                flags.append(f"tracking tokens ({', '.join(d.tracking_params[:2])})")
            if d.suspicious_structure:
                flags.append(f"suspicious structure ({'; '.join(d.suspicious_structure[:1])})")
            if not d.https:
                flags.append("unencrypted connection (HTTP)")
            reasoning_steps.append(
                f"Target URL inspected: {d.final_url} (HTTP {d.status_code}, {'HTTPS' if d.https else 'HTTP'}). "
                f"Title: '{d.title or 'Unavailable'}'. "
                f"Flags: {'; '.join(flags) if flags else 'None'}."
            )

    # Search Retrieval Telemetry integration
    if search_evidence:
        retrieval_status = search_evidence.retrieval_status
        queries_run = len(search_evidence.queries)
        support_queries = [q.query for q in search_evidence.queries if q.query_type == "support"]
        counter_queries = [q.query for q in search_evidence.queries if q.query_type == "counter"]

        reasoning_steps.append(
            f"Deterministic query generation produced {queries_run} queries: "
            f"{len(support_queries)} supporting query variations and {len(counter_queries)} contradiction/counter queries."
        )

        if retrieval_status == "FAILED":
            uncertainties.append(
                f"Search provider was unreachable: {search_evidence.retrieval_note or 'Network error'}."
            )
            reasoning_steps.append("Search candidate retrieval failed; transparent error recorded.")
        elif not search_evidence.sources:
            uncertainties.append("No public web sources were indexed for this specific claim wording.")
            reasoning_steps.append("Candidate search returned 0 external sources.")
        else:
            reasoning_steps.append(
                f"Retrieved {len(search_evidence.sources)} unique candidate sources across "
                f"{len(search_evidence.clusters)} independence cluster(s)."
            )

            for cand in search_evidence.supporting:
                clean_title = (cand.title[:60] + "…") if len(cand.title) > 60 else cand.title
                supporting_evidence.append(
                    f"[{cand.domain} · {cand.reliability_score}/100] {clean_title}: {cand.snippet[:120]}…"
                )

            for cand in search_evidence.contradicting:
                clean_title = (cand.title[:60] + "…") if len(cand.title) > 60 else cand.title
                contradicting_evidence.append(
                    f"[{cand.domain} · {cand.reliability_score}/100] {clean_title}: {cand.snippet[:120]}…"
                )

            syndicated_clusters = [cl for cl in search_evidence.clusters if cl.independence_level in ("SYNDICATED", "DUPLICATE")]
            if syndicated_clusters:
                reasoning_steps.append(
                    f"Heuristic clustering flagged {len(syndicated_clusters)} cluster(s) with duplicated or wire-syndicated articles."
                )

    # Mandatory Epistemic Uncertainties
    if image_analysis_result:
        uncertainties.append("Evidence Health measures technical suitability for digital analysis, not real-world authenticity.")
        uncertainties.append("Missing EXIF metadata does not indicate tampering; social platforms routinely strip metadata.")
    uncertainties.append("Search results are candidate evidence only; source ranking is not proof of authenticity.")
    uncertainties.append("Source reliability and independence are evaluated heuristically.")

    # Step 3.5: Execute Phase 6 Deterministic Evidence Fusion
    fusion_result = await fuse_investigation_evidence(
        claim_text=claim_text,
        url_text=url_text,
        url_outcome=url_outcome,
        image_analysis=image_analysis_result,
        search_evidence=search_evidence,
        multimodal_result=multimodal_result,
        image_text_evidence=image_text_evidence,
        video_analysis=video_result,
    )

    # Collect additional normalized limitations
    for it in fusion_result.normalized_evidence:
        for lim in it.limitations:
            if lim not in uncertainties:
                uncertainties.append(lim)

    # Synthesize telemetry logs for reasoning steps
    tt = fusion_result.trust_triangle
    reasoning_steps.append(
        f"Phase 6 Evidence Fusion synthesized {len(fusion_result.normalized_evidence)} normalized evidence vector(s) "
        f"across {fusion_result.evidence_summary.independent_evidence_count} independent cluster(s). "
        f"Trust Triangle: Likelihood {tt.manipulation_likelihood:.1f}%, Strength {tt.evidence_strength:.1f}%, Conflict {tt.evidence_conflict:.1f}%."
    )
    if fusion_result.conflict.detected:
        reasoning_steps.append(
            f"Conflict Detection ({fusion_result.conflict.severity} severity): {fusion_result.conflict.description}"
        )
    reasoning_steps.append(
        f"Final Deterministic Verdict: {fusion_result.verdict.replace('_', ' ')} ({fusion_result.confidence}% confidence). "
        f"{fusion_result.reason}"
    )

    # Populate supporting and contradicting evidence strings with traceable IDs
    for it in fusion_result.normalized_evidence:
        if it.direction == "SUPPORTS" and it.weight > 0.04:
            s_str = f"[{it.source} · {it.evidence_id}] {it.description}"
            if s_str not in supporting_evidence and len(supporting_evidence) < 8:
                supporting_evidence.append(s_str)
        elif it.direction == "CONTRADICTS" and it.weight > 0.04:
            c_str = f"[{it.source} · {it.evidence_id}] {it.description}"
            if c_str not in contradicting_evidence and len(contradicting_evidence) < 8:
                contradicting_evidence.append(c_str)

    ai_reasoning = AiReasoning(
        claim=claim_text or (url_text if url_text else "Investigation"),
        verdict=fusion_result.verdict,
        confidence=fusion_result.confidence,
        summary=fusion_result.reason or "Candidate evidence evaluated via deterministic evidence fusion.",
        supporting_evidence=supporting_evidence,
        contradicting_evidence=contradicting_evidence,
        uncertainties=uncertainties,
        reasoning=reasoning_steps,
        reason=fusion_result.reason,
        supporting_evidence_ids=fusion_result.supporting_evidence_ids,
        contradicting_evidence_ids=fusion_result.contradicting_evidence_ids,
    )

    claim_decomp = ClaimQueryGenerator.decompose_claim(claim_text) if claim_text else None

    # Construct MediaAnalysis with genuine Phase 4 evidence
    if image_analysis_result:
        media_analysis = MediaAnalysis(
            analyzed=True,
            media_name=image_analysis_result.file.filename,
            media_type="image",
            health=FileHealth(
                filename=image_analysis_result.file.filename,
                size_bytes=image_analysis_result.file.size_bytes,
                mime_type=image_analysis_result.file.mime_type,
                sha256=image_analysis_result.file.sha256,
                is_supported=image_analysis_result.file.is_valid,
                resolution=f"{image_analysis_result.file.width}x{image_analysis_result.file.height}",
                compression_ratio=None,
                metadata_available=image_analysis_result.metadata.available,
                metadata_completeness_score=image_analysis_result.metadata.completeness_score,
                ocr_quality_score=image_analysis_result.ocr.confidence,
                metadata_note=(
                    "Metadata present; provides provenance context."
                    if image_analysis_result.metadata.available
                    else "Missing metadata reduces test contribution to zero; it is not evidence of manipulation."
                ),
            ),
            exif=EXIFMetadata(
                camera_make=image_analysis_result.metadata.camera_make,
                camera_model=image_analysis_result.metadata.camera_model,
                capture_timestamp=image_analysis_result.metadata.timestamp,
                gps_latitude=None,
                gps_longitude=None,
                is_stripped=not image_analysis_result.metadata.available,
                software=image_analysis_result.metadata.software,
            ),
            perceptual_hash=PerceptualHash(
                dhash=image_analysis_result.computer_vision.perceptual_hash_dhash,
                phash=image_analysis_result.computer_vision.perceptual_hash_phash,
                archival_match_found=False,
                match_similarity_pct=0.0,
                earliest_archival_timestamp=None,
            ),
            prnu_sensor_available=False,
            optical_flow_available=False,
            ai_generated_probability=(
                multimodal_result.confidence
                if (multimodal_result and multimodal_result.ai_generation_assessment == "likely_ai_generated")
                else None
            ),
            tampering_score=(
                multimodal_result.confidence
                if (multimodal_result and multimodal_result.ai_generation_assessment == "possibly_manipulated")
                else None
            ),
            ela_available=image_analysis_result.ela.available,
            ela_mean_error=image_analysis_result.ela.mean_error,
            ocr_text=image_analysis_result.ocr.text if image_analysis_result.ocr.available else None,
            forensic_notes=image_analysis_result.evidence_health.signals + image_analysis_result.evidence_health.notes[:1],
            image_analysis=image_analysis_result.model_dump(by_alias=True),
            multimodal_ai=multimodal_result,
        )
    elif video_result:
        vm = video_result.metadata
        ocr_qs = [f.ocr_quality for f in video_result.frames if f.decoded and f.ocr_available]
        media_analysis = MediaAnalysis(
            analyzed=video_ok,
            media_name=vm.filename if vm else getattr(file_upload, "filename", "upload"),
            media_type="video",
            health=FileHealth(
                filename=vm.filename,
                size_bytes=vm.size_bytes,
                mime_type=getattr(file_upload, "content_type", "") or "application/octet-stream",
                sha256=vm.sha256,
                is_supported=video_ok,
                resolution=f"{vm.width}x{vm.height}" if vm.width and vm.height else None,
                metadata_available=False,
                ocr_quality_score=max(ocr_qs) if ocr_qs else None,
                video_frame_count=vm.frame_count,
                metadata_note="Container/stream facts were measured; EXIF does not apply to video frames.",
            ) if vm else None,
            forensic_notes=(
                [f"Video status: {video_result.status}."] if video_ok
                else [f"Failed video validation: {video_error_msg}"]
            ) + [f"{c.name}: {c.status}" for c in video_result.capabilities if c.status == "UNAVAILABLE"][:4],
            video_analysis=video_result.model_dump(by_alias=True),
        )
    elif image_error_msg:
        media_analysis = MediaAnalysis(
            analyzed=False,
            media_name=getattr(file_upload, "filename", "upload"),
            media_type="image",
            forensic_notes=[f"Failed image validation: {image_error_msg}"],
        )
    else:
        media_analysis = MediaAnalysis(
            analyzed=False,
            media_name="Not provided",
            media_type="none",
            forensic_notes=["No media was analyzed in this investigation."],
        )

    response = InvestigationResponse(
        claim=claim_text or (url_text if url_text else "Investigation"),
        input_url=url_text if url_text else None,
        url_analysis=url_outcome,
        final=ai_reasoning,
        ai_available=bool((search_evidence and search_evidence.sources) or multimodal_result),
        ai_note=(
            f"Phase 6 Deterministic Evidence Fusion active. Trust Triangle: "
            f"Likelihood {fusion_result.trust_triangle.manipulation_likelihood:.1f}%, "
            f"Strength {fusion_result.trust_triangle.evidence_strength:.1f}%, "
            f"Conflict {fusion_result.trust_triangle.evidence_conflict:.1f}%."
        ),
        model=multimodal_result.model_used if multimodal_result else None,
        generated_at=now_iso,
        claim_analysis=Claim(
            raw_text=claim_text,
            normalized_proposition=claim_text,
            event_type=claim_decomp.get("event") if claim_decomp else None,
            temporal_anchor=claim_decomp.get("date") if claim_decomp else None,
            location_anchor=claim_decomp.get("location") if claim_decomp else None,
            entities=claim_decomp.get("entities", []) if claim_decomp else [],
        ) if claim_text else None,
        media_analysis=media_analysis,
        contradiction=Contradiction(
            detected=fusion_result.conflict.detected,
            conflict_type="factual" if fusion_result.conflict.detected else None,
            description=fusion_result.conflict.description if fusion_result.conflict.detected else None,
        ),
        search_evidence=search_evidence,
        multimodal_analysis=multimodal_result,
        image_text_evidence=image_text_evidence,
        trust_triangle=fusion_result.trust_triangle,
        evidence_summary=fusion_result.evidence_summary,
        conflict=fusion_result.conflict,
        normalized_evidence=fusion_result.normalized_evidence,
    )

    return JSONResponse(content=response.model_dump(by_alias=True))
