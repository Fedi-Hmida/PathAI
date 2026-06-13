import asyncio
from typing import Protocol, cast

import httpx

from app.core.config import Settings, get_settings
from app.llm.config import assert_real_llm_configured
from app.llm.errors import LLMRequestError, LLMResponseError, LLMTimeoutError
from app.llm.types import LLMMessage, LLMRequestOptions, LLMResponse


class LLMClientProtocol(Protocol):
    async def complete(
        self,
        messages: list[LLMMessage],
        options: LLMRequestOptions | None = None,
    ) -> LLMResponse:
        ...


class UniversityLLMClient:
    def __init__(
        self,
        settings: Settings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.transport = transport

    async def complete(
        self,
        messages: list[LLMMessage],
        options: LLMRequestOptions | None = None,
    ) -> LLMResponse:
        assert_real_llm_configured(self.settings)
        request_options = options or LLMRequestOptions()
        payload = self._build_payload(messages=messages, options=request_options)
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.settings.llm_timeout_seconds,
                    transport=self.transport,
                    trust_env=False,
                ) as client:
                    response = await client.post(
                        self.settings.llm_api_url,
                        json=payload,
                        headers=headers,
                    )
                if response.status_code in {429} or response.status_code >= 500:
                    raise LLMRequestError(
                        f"LLM provider returned retryable status {response.status_code}."
                    )
                if response.status_code >= 400:
                    raise LLMRequestError(f"LLM provider returned status {response.status_code}.")

                try:
                    data = response.json()
                except ValueError as exc:
                    raise LLMResponseError("LLM provider returned invalid JSON.") from exc
                if not isinstance(data, dict):
                    raise LLMResponseError("LLM provider returned a non-object response.")
                return self._parse_response(data)
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt >= self.settings.llm_max_retries:
                    raise LLMTimeoutError("LLM request timed out.") from exc
            except (httpx.HTTPError, LLMRequestError) as exc:
                last_error = exc
                if attempt >= self.settings.llm_max_retries:
                    raise LLMRequestError("LLM request failed after retries.") from exc

            await asyncio.sleep(self.settings.llm_retry_backoff_seconds * (2**attempt))

        raise LLMRequestError("LLM request failed.") from last_error

    def _build_payload(
        self,
        messages: list[LLMMessage],
        options: LLMRequestOptions,
    ) -> dict[str, object]:
        model = options.model or self.settings.university_llm_model
        payload: dict[str, object] = {
            "model": model,
            "messages": [message.model_dump() for message in messages],
            "temperature": options.temperature,
            "max_tokens": options.max_tokens,
        }
        if options.response_format is not None:
            payload["response_format"] = options.response_format
        return payload

    def _parse_response(self, data: dict[str, object]) -> LLMResponse:
        content = self._extract_content(data)
        if not content:
            raise LLMResponseError("LLM response did not contain text content.")

        finish_reason = None
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                finish_reason = first_choice.get("finish_reason")

        model_value = data.get("model")
        usage_value = data.get("usage")
        usage = cast(dict[str, object], usage_value) if isinstance(usage_value, dict) else {}

        return LLMResponse(
            content=content,
            model=model_value if isinstance(model_value, str) else None,
            finish_reason=finish_reason if isinstance(finish_reason, str) else None,
            usage=usage,
            raw=data,
        )

    def _extract_content(self, data: dict[str, object]) -> str | None:
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
                text = first_choice.get("text")
                if isinstance(text, str):
                    return text

        for key in ("output_text", "content", "text"):
            value = data.get(key)
            if isinstance(value, str):
                return value
        return None
