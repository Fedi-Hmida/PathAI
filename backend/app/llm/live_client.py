from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field, SecretStr

from app.core.settings import Settings
from app.llm.contracts import (
    RawLLMResponse,
    StructuredModel,
    StructuredOutputRequest,
)
from app.llm.errors import LLMProviderError, LLMTimeoutError
from app.llm.structured_output import parse_structured_output

LIVE_LLM_OPT_IN_ENV_VAR = "PATHAI_RUN_LIVE_LLM_TESTS"


class LiveLLMNotConfiguredError(RuntimeError):
    pass


class LiveLLMSmokeResponse(BaseModel):
    status: Literal["ok"]
    message: str = Field(min_length=1, max_length=200)


@dataclass(slots=True, repr=False)
class OpenAICompatibleLiveLLMClient:
    provider: str
    model: str
    base_url: str
    api_key: SecretStr
    timeout_seconds: int = 45

    def __repr__(self) -> str:
        return (
            "OpenAICompatibleLiveLLMClient("
            f"provider={self.provider!r}, model={self.model!r}, "
            f"timeout_seconds={self.timeout_seconds!r})"
        )

    async def generate(self, request: StructuredOutputRequest) -> RawLLMResponse:
        endpoint = _chat_completions_endpoint(self.base_url)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return strict JSON only."},
                {"role": "user", "content": request.prompt},
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                timeout=min(request.timeout.timeout_seconds, self.timeout_seconds),
            ) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                body = response.json()
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                "Live LLM request timed out.",
                provider=self.provider,
            ) from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            raise LLMProviderError(
                f"Live LLM provider returned HTTP {status_code}.",
                provider=self.provider,
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMProviderError(
                "Live LLM provider request failed.",
                provider=self.provider,
            ) from exc

        return RawLLMResponse(
            provider=self.provider,
            model=self.model,
            text=_extract_chat_content(body),
            request_id=request.request_id,
            finish_reason=_extract_finish_reason(body),
        )

    async def generate_structured(
        self,
        request: StructuredOutputRequest,
        output_schema: type[StructuredModel],
    ) -> StructuredModel:
        response = await self.generate(request)
        return parse_structured_output(response.text, output_schema)


def live_llm_smoke_enabled() -> bool:
    value = os.getenv(LIVE_LLM_OPT_IN_ENV_VAR, "")
    return value.lower() in {"1", "true", "yes"}


def build_live_client_from_settings(settings: Settings) -> OpenAICompatibleLiveLLMClient:
    if settings.llm_provider.lower() == "mock":
        raise LiveLLMNotConfiguredError("Live LLM provider is not configured.")
    if not settings.effective_llm_base_url:
        raise LiveLLMNotConfiguredError("Live LLM base URL is not configured.")
    if not settings.effective_llm_model:
        raise LiveLLMNotConfiguredError("Live LLM model is not configured.")
    if settings.effective_llm_api_key is None:
        raise LiveLLMNotConfiguredError("Live LLM API key is not configured.")
    return OpenAICompatibleLiveLLMClient(
        provider=settings.llm_provider,
        model=settings.effective_llm_model,
        base_url=settings.effective_llm_base_url,
        api_key=settings.effective_llm_api_key,
        timeout_seconds=settings.llm_timeout_seconds,
    )


async def run_live_structured_output_smoke(
    settings: Settings,
    output_schema: type[StructuredModel],
) -> StructuredModel:
    if not live_llm_smoke_enabled():
        raise LiveLLMNotConfiguredError("Live LLM smoke check is disabled.")
    client = build_live_client_from_settings(settings)
    request = StructuredOutputRequest(
        prompt=(
            "Return only JSON matching this shape: "
            '{"status":"ok","message":"short smoke check message"}.'
        ),
        schema_name=output_schema.__name__,
        request_id="live_llm_smoke",
        max_output_tokens=128,
    )
    return await client.generate_structured(request, output_schema)


def _chat_completions_endpoint(base_url: str) -> str:
    cleaned = base_url.rstrip("/")
    if cleaned.endswith("/chat/completions"):
        return cleaned
    return f"{cleaned}/chat/completions"


def _extract_chat_content(body: dict[str, Any]) -> str:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMProviderError("Live LLM response did not include choices.")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise LLMProviderError("Live LLM response did not include a message.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMProviderError("Live LLM response content was empty.")
    return content


def _extract_finish_reason(body: dict[str, Any]) -> str | None:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    finish_reason = choices[0].get("finish_reason")
    return finish_reason if isinstance(finish_reason, str) else None
