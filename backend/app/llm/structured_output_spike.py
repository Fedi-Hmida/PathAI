from pathlib import Path
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.settings import Settings
from app.llm.client import StructuredModel, StructuredOutputRequest
from app.llm.mock_client import MockLLMClient


class LiveLLMNotConfiguredError(RuntimeError):
    pass


async def run_mock_structured_output_spike(output_schema: type[StructuredModel]) -> StructuredModel:
    client = MockLLMClient()
    request = StructuredOutputRequest(
        prompt="Return a tiny valid JSON object for the requested schema.",
        schema_name=output_schema.__name__,
    )
    return await client.generate_structured(request, output_schema)


async def run_optional_live_structured_output_spike(
    settings: Settings,
    output_schema: type[StructuredModel],
) -> StructuredModel:
    if not settings.enable_live_llm_tests:
        raise LiveLLMNotConfiguredError("Live LLM spike is disabled.")
    if not settings.live_llm_configured or settings.llm_provider.lower() == "mock":
        raise LiveLLMNotConfiguredError("Live LLM provider is not configured.")

    api_key = settings.effective_llm_api_key
    if api_key is None:
        raise LiveLLMNotConfiguredError("Live LLM API key is not configured.")

    endpoint = _chat_completions_endpoint(settings.effective_llm_base_url)
    prompt = (
        "Return only valid JSON for this schema name: "
        f"{output_schema.__name__}. Keep the response tiny and deterministic."
    )
    payload = {
        "model": settings.effective_llm_model,
        "messages": [
            {"role": "system", "content": "You return strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key.get_secret_value()}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        response = await client.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()

    content = _extract_chat_content(body)
    return output_schema.model_validate_json(content)


def load_live_settings_from_env_file(env_path: Path) -> Settings:
    values = _read_env_file(env_path)
    return Settings(
        llm_provider=values.get("LLM_PROVIDER", "openai_compatible"),
        llm_base_url=values.get("LLM_BASE_URL", ""),
        llm_model=values.get("LLM_MODEL", ""),
        llm_api_key=values.get("LLM_API_KEY") or None,
        openai_base_url=values.get("OPENAI_BASE_URL", ""),
        openai_api_key=values.get("OPENAI_API_KEY") or None,
        university_llm_api_url=values.get("UNIVERSITY_LLM_API_URL", ""),
        university_llm_api_key=values.get("UNIVERSITY_LLM_API_KEY") or None,
        university_llm_model=values.get("UNIVERSITY_LLM_MODEL", ""),
        llm_timeout_seconds=int(values.get("LLM_TIMEOUT_SECONDS", "45") or "45"),
        llm_mock_mode=False,
        enable_live_llm_tests=True,
    )


def parse_structured_payload(
    payload: object,
    output_schema: type[StructuredModel],
) -> StructuredModel:
    try:
        return output_schema.model_validate(payload)
    except ValidationError:
        raise


def _chat_completions_endpoint(base_url: str) -> str:
    cleaned = base_url.rstrip("/")
    if cleaned.endswith("/chat/completions"):
        return cleaned
    return f"{cleaned}/chat/completions"


def _extract_chat_content(body: dict[str, Any]) -> str:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("LLM response did not include choices.")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("LLM response did not include a message.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM response content was empty.")
    return content


def _read_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
