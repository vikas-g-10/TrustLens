"""
Post-Fusion LLM Explanation Layer for TrustLens Phase 6.

Generates transparent, human-readable explanations strictly grounded in the
deterministically fused verdict, Trust Triangle metrics, and evidence provenance.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. The LLM must NOT decide or override the verdict, confidence, weights, or conflict metrics.
2. The LLM receives the deterministically computed verdict and evidence points as fixed truth.
3. If the LLM provider fails, times out, or has no API key, the deterministic explanation
   is returned immediately with zero error.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional
import httpx

from backend.config import settings
from backend.schemas.fusion import FusionResult, NormalizedEvidenceItem

logger = logging.getLogger("trustlens.fusion.explanation")


def generate_deterministic_explanation(
    fusion_result: FusionResult,
    claim_text: str = "",
) -> str:
    """
    Builds a robust, factual, deterministic explanation from fused evidence.
    Always available offline without requiring any external LLM APIs.
    """
    verdict = fusion_result.verdict
    conf = fusion_result.confidence
    tt = fusion_result.trust_triangle
    conflict = fusion_result.conflict
    summary = fusion_result.evidence_summary

    verdict_label = verdict.replace("_", " ")

    if verdict == "LIKELY_AI_GENERATED":
        headline = (
            f"TrustLens evaluated this media as {verdict_label} ({conf}% confidence). "
            f"Manipulation likelihood is assessed at {tt.manipulation_likelihood:.1f}% based on synthetic generation markers."
        )
    elif verdict == "LIKELY_AUTHENTIC":
        headline = (
            f"TrustLens evaluated this media as {verdict_label} ({conf}% confidence). "
            f"Evidence demonstrates consistent camera hardware provenance and natural optical continuity."
        )
    elif verdict == "LIKELY_MANIPULATED":
        headline = (
            f"TrustLens evaluated this media as {verdict_label} ({conf}% confidence). "
            f"Forensic differential artifacts and editing indicators suggest post-capture alteration."
        )
    elif verdict == "HIGH_RISK":
        headline = (
            f"TrustLens evaluated this assertion as HIGH RISK ({conf}% confidence). "
            "Corroborating fact-checks and independent reporting contradict the claimed event."
        )
    else:
        # INCONCLUSIVE
        if conflict.severity == "HIGH":
            headline = (
                f"Investigation is INCONCLUSIVE ({conf}% confidence) due to significant evidence collision "
                f"({int(conflict.conflict_score * 100)}% conflict ratio). Opposing sources prevent a reliable verdict."
            )
        else:
            headline = (
                f"Investigation is INCONCLUSIVE ({conf}% confidence). "
                f"Evidence coverage ({int(summary.evidence_coverage * 100)}%) is insufficient to establish a definitive determination."
            )

    return headline


async def generate_verdict_explanation(
    fusion_result: FusionResult,
    claim_text: str = "",
) -> str:
    """
    Produces an explainable summary. Attempts LLM formatting when configured,
    with instant deterministic fallback.
    """
    base_explanation = generate_deterministic_explanation(fusion_result, claim_text)

    # Check if LLM API is configured for post-hoc explanation
    api_key = settings.llm_api_key or settings.groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        return base_explanation

    base_url = settings.llm_base_url or "https://api.groq.com/openai/v1"
    model_name = settings.llm_model or "qwen/qwen3.8-27b"
    timeout = getattr(settings, "multimodal_timeout_seconds", 12.0)

    # Gather grounded context for the LLM
    top_sup = [
        f"[{it.evidence_id}] {it.description}"
        for it in fusion_result.normalized_evidence
        if it.direction == "SUPPORTS" and it.weight > 0.04
    ][:3]
    top_contra = [
        f"[{it.evidence_id}] {it.description}"
        for it in fusion_result.normalized_evidence
        if it.direction == "CONTRADICTS" and it.weight > 0.04
    ][:3]

    system_prompt = (
        "You are the explainability engine of TrustLens, a digital evidence investigation platform. "
        "The deterministic Evidence Fusion Engine has ALREADY computed the final verdict, confidence, and metrics. "
        "Your task is solely to write a concise, professional 2-3 sentence explanation explaining to the user "
        "WHY TrustLens reached this conclusion based on the provided evidence points. "
        "CRITICAL: You MUST NOT change the verdict, confidence, or evidence weights. "
        "Do not invent facts or cite evidence not present in the prompt."
    )

    user_prompt = (
        f"Computed Verdict: {fusion_result.verdict}\n"
        f"Confidence: {fusion_result.confidence}%\n"
        f"Trust Triangle Metrics:\n"
        f"  - Manipulation Likelihood: {fusion_result.trust_triangle.manipulation_likelihood}%\n"
        f"  - Evidence Strength: {fusion_result.trust_triangle.evidence_strength}%\n"
        f"  - Evidence Conflict: {fusion_result.trust_triangle.evidence_conflict}%\n"
        f"Conflict Severity: {fusion_result.conflict.severity}\n"
        f"Key Supporting Evidence:\n" + ("\n".join(top_sup) if top_sup else "None") + "\n"
        f"Key Contradicting Evidence:\n" + ("\n".join(top_contra) if top_contra else "None") + "\n"
        f"Deterministic Reason: {fusion_result.reason}\n\n"
        f"Provide a clear, 2-3 sentence explanation summarizing this decision."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 250,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            if res.status_code == 200:
                data = res.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    if content and len(content) > 20:
                        return content
    except Exception as exc:
        logger.info(f"LLM explanation generation skipped/failed ({str(exc)}); using deterministic baseline.")

    return base_explanation
