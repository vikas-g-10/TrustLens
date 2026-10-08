"""
Multimodal LLM Provider Abstraction for TrustLens Phase 5.

Supports:
- Groq Vision (e.g. qwen/qwen3.8-27b)
- OpenAI Vision (e.g. gpt-4o, gpt-4o-mini)
- Custom OpenAI-compatible endpoints
- Graceful Unavailable provider fallback

All providers return parsed structured JSON or raise MultimodalProviderError.
No credentials or API keys are exposed to the frontend.
"""
from abc import ABC, abstractmethod
import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional
import httpx

from backend.config import settings
from backend.services.multimodal.prompt import SYSTEM_PROMPT

logger = logging.getLogger("trustlens.multimodal")


class MultimodalProviderError(Exception):
    """Raised when multimodal vision inference fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, raw_response: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_response = raw_response


class MultimodalProvider(ABC):
    """Abstract base class for Multimodal Vision AI providers."""

    @abstractmethod
    async def analyze_image(
        self,
        image_data_url: str,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        Submits image and prompt to the multimodal AI provider.

        Returns:
            Dict[str, Any] parsed from structured JSON response.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass


class OpenAiCompatibleProvider(MultimodalProvider):
    """
    Standard OpenAI-compatible vision provider.
    Works seamlessly with Groq, OpenAI, and compatible endpoints.
    """

    def __init__(
        self,
        provider_name: str,
        api_key: str,
        base_url: str,
        model_name: str,
        timeout_seconds: float = 35.0,
    ):
        self._provider_name = provider_name
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def analyze_image(
        self,
        image_data_url: str,
        prompt: str,
    ) -> Dict[str, Any]:
        endpoint = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                },
            ],
            "temperature": 0.1,
            "max_tokens": 750,
            "response_format": {"type": "json_object"},
        }

        try:
            res = None
            for attempt in range(2):
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    res = await client.post(endpoint, headers=headers, json=payload)

                if res.status_code == 429 and attempt == 0:
                    retry_wait = 6.0
                    try:
                        err_data = res.json()
                        err_msg = err_data.get("error", {}).get("message", "")
                        if "try again in " in err_msg:
                            part = err_msg.split("try again in ")[1].split("s")[0]
                            retry_wait = min(12.0, max(2.0, float(part) + 1.0))
                    except Exception:
                        pass
                    logger.info(f"{self._provider_name} rate limit hit; waiting {retry_wait:.1f}s before retry...")
                    await asyncio.sleep(retry_wait)
                    continue
                break


            if res is None or res.status_code != 200:
                err_text = res.text if res is not None else "No response"
                code = res.status_code if res is not None else 500
                logger.warning(
                    f"Multimodal API error from {self._provider_name} ({code}): {err_text[:300]}"
                )
                raise MultimodalProviderError(
                    f"{self._provider_name} API returned HTTP {code}",
                    status_code=code,
                    raw_response=err_text,
                )


            data = res.json()
            choices = data.get("choices", [])
            if not choices:
                raise MultimodalProviderError(f"Empty choices returned from {self._provider_name}")

            content_str = choices[0].get("message", {}).get("content", "")
            if not content_str:
                raise MultimodalProviderError("Empty content received from multimodal model.")

            # Parse JSON safely
            # Handle potential markdown code fencing if model wraps despite json_object
            cleaned = content_str.strip()
            if cleaned.startswith("```"):
                first_nl = cleaned.find("\n")
                last_ticks = cleaned.rfind("```")
                if first_nl != -1 and last_ticks > first_nl:
                    cleaned = cleaned[first_nl + 1 : last_ticks].strip()

            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise MultimodalProviderError("Multimodal model output was not a JSON dictionary.")

            return parsed

        except httpx.TimeoutException as exc:
            raise MultimodalProviderError(
                f"{self._provider_name} request timed out after {self._timeout_seconds}s"
            ) from exc
        except httpx.RequestError as exc:
            raise MultimodalProviderError(
                f"Network connection to {self._provider_name} failed: {str(exc)}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise MultimodalProviderError(
                f"Failed to decode JSON from {self._provider_name} output: {str(exc)}"
            ) from exc


class UnavailableMultimodalProvider(MultimodalProvider):
    """Fallback provider when no multimodal API key is configured."""

    def __init__(self, reason: str = "No API key configured for multimodal model."):
        self._reason = reason

    @property
    def provider_name(self) -> str:
        return "unavailable"

    @property
    def model_name(self) -> str:
        return "none"

    async def analyze_image(
        self,
        image_data_url: str,
        prompt: str,
    ) -> Dict[str, Any]:
        raise MultimodalProviderError(self._reason)


def get_multimodal_provider() -> MultimodalProvider:
    """
    Factory function resolving the active MultimodalProvider based on application settings.
    Prioritizes:
    1. LLM_PROVIDER / LLM_API_KEY from settings
    2. GROQ_API_KEY fallback with multimodal_model
    3. UnavailableMultimodalProvider if no key exists
    """
    provider_name = (settings.llm_provider or "groq").lower().strip()
    timeout = getattr(settings, "multimodal_timeout_seconds", 35.0)

    # 1. Groq Provider
    if provider_name == "groq":
        api_key = settings.llm_api_key or settings.groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            return UnavailableMultimodalProvider("Groq API key not configured (GROQ_API_KEY).")
        model = (
            settings.llm_model
            or getattr(settings, "multimodal_model", None)
            or "qwen/qwen3.8-27b"
        )
        base_url = settings.llm_base_url or "https://api.groq.com/openai/v1"
        return OpenAiCompatibleProvider(
            provider_name="groq",
            api_key=api_key,
            base_url=base_url,
            model_name=model,
            timeout_seconds=timeout,
        )

    # 2. OpenAI Provider
    elif provider_name == "openai":
        api_key = settings.llm_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return UnavailableMultimodalProvider("OpenAI API key not configured (OPENAI_API_KEY).")
        model = settings.llm_model or "gpt-4o"
        base_url = settings.llm_base_url or "https://api.openai.com/v1"
        return OpenAiCompatibleProvider(
            provider_name="openai",
            api_key=api_key,
            base_url=base_url,
            model_name=model,
            timeout_seconds=timeout,
        )

    # 3. Custom / Generic OpenAI-compatible
    elif provider_name in ("custom", "openai_compatible", "gemini"):
        api_key = settings.llm_api_key or os.getenv("LLM_API_KEY") or ""
        base_url = settings.llm_base_url or "https://api.groq.com/openai/v1"
        model = settings.llm_model or "qwen/qwen3.8-27b"
        if not api_key:
            return UnavailableMultimodalProvider("LLM_API_KEY not configured.")
        return OpenAiCompatibleProvider(
            provider_name=provider_name,
            api_key=api_key,
            base_url=base_url,
            model_name=model,
            timeout_seconds=timeout,
        )

    # Fallback to Groq if key exists
    if settings.groq_api_key:
        return OpenAiCompatibleProvider(
            provider_name="groq",
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            model_name="qwen/qwen3.8-27b",
            timeout_seconds=timeout,
        )

    return UnavailableMultimodalProvider(f"Unsupported or unconfigured LLM provider: {provider_name}")
