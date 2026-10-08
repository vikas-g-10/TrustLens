import type { AiReasoning, InvestigationResponse } from '../types/analysis';
import type { ImageAnalysisResponse } from '../types/imageAnalysis';

const REQUEST_TIMEOUT_MS = 90_000;
const IMAGE_UPLOAD_TIMEOUT_MS = 60_000;

function unavailable(claim: string, url: string, reason: string): InvestigationResponse {
  const summary = `The investigation service could not be reached (${reason}). The claim could not be verified.`;
  const final: AiReasoning = {
    claim,
    verdict: 'INCONCLUSIVE',
    confidence: 0,
    summary,
    supportingEvidence: [],
    contradictingEvidence: [],
    uncertainties: ['Investigation service unavailable.'],
    reasoning: [summary],
  };
  return {
    claim,
    inputUrl: url || null,
    urlAnalysis: null,
    final,
    aiAvailable: false,
    aiNote: 'AI reasoning was unavailable because the investigation service could not be reached.',
    model: null,
    generatedAt: new Date().toISOString(),
    serviceError: reason,
  };
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export async function checkBackendHealth(): Promise<{ ok: boolean; version?: string; error?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    const data = await res.json();
    return { ok: true, version: data.version };
  } catch (err: any) {
    return { ok: false, error: err.message };
  }
}

/** Runs a live investigation. Never throws: failures become a transparent INCONCLUSIVE result. */
export async function runInvestigation(claim: string, url: string, file?: File | null): Promise<InvestigationResponse> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    let fetchOptions: RequestInit;

    if (file) {
      const formData = new FormData();
      if (claim) formData.append('claim', claim);
      if (url) formData.append('url', url);
      formData.append('file', file);
      fetchOptions = {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      };
    } else {
      fetchOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ claim, url }),
        signal: controller.signal,
      };
    }

    const res = await fetch(`${API_BASE_URL}/api/investigate`, fetchOptions);
    const body = await res.json().catch(() => null);
    if (!res.ok || !body || !body.final) {
      return unavailable(claim, url, body?.error || `HTTP ${res.status}`);
    }
    return body as InvestigationResponse;
  } catch (e) {
    return unavailable(claim, url, e instanceof Error && e.name === 'AbortError' ? 'request timed out' : 'network error');
  } finally {
    clearTimeout(timer);
  }
}

/** Uploads an image to the real backend image analysis pipeline. */
export async function analyzeImage(file: File): Promise<ImageAnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), IMAGE_UPLOAD_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE_URL}/api/analyze-image?include_ai=true`, {
      method: 'POST',
      // Notice: Do NOT set Content-Type header; browser must set multipart/form-data with its boundary
      body: formData,
      signal: controller.signal,
    });


    if (!res.ok) {
      const body = await res.json().catch(() => null);
      let errorMsg = `Upload failed with HTTP ${res.status}`;
      if (res.status === 413) {
        errorMsg = 'File too large. Maximum supported upload size is 10 MB.';
      } else if (res.status === 415) {
        errorMsg = body?.detail || 'Unsupported image format. Please upload JPEG, PNG, or WEBP.';
      } else if (res.status === 400 || res.status === 422) {
        errorMsg = body?.detail || 'Invalid or malformed image file.';
      } else if (res.status >= 500) {
        errorMsg = body?.detail || 'Image analysis service encountered an internal error.';
      } else if (body?.detail) {
        errorMsg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
      throw new Error(errorMsg);
    }

    const data = await res.json();
    return data as ImageAnalysisResponse;
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw new Error('Image analysis request timed out (60s). Please try again with a smaller file.');
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

