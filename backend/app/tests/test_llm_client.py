import httpx
import pytest

from app.core.config import Settings
from app.llm.client import UniversityLLMClient
from app.llm.mock import MockLLMClient
from app.llm.types import LLMMessage, LLMRequestOptions


@pytest.mark.asyncio
async def test_mock_llm_client_returns_deterministic_response() -> None:
    client = MockLLMClient()

    response = await client.complete([LLMMessage(role="user", content="health check")])

    assert response.model == "mock-pathai-llm"
    assert "Mock LLM structured output validated" in response.content
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_university_llm_client_retries_retryable_status() -> None:
    call_count = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(500, json={"error": "temporary"})
        return httpx.Response(
            200,
            json={
                "model": "demo-model",
                "choices": [
                    {
                        "message": {"content": '{"status":"ok","message":"ready"}'},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 10},
            },
        )

    settings = Settings(
        university_llm_api_url="https://llm.example.edu/chat",
        university_llm_api_key="secret-key",
        university_llm_model="demo-model",
        llm_mock_mode=False,
        llm_max_retries=1,
        llm_retry_backoff_seconds=0,
    )
    client = UniversityLLMClient(settings=settings, transport=httpx.MockTransport(handler))

    response = await client.complete(
        messages=[LLMMessage(role="user", content="hello")],
        options=LLMRequestOptions(max_tokens=20),
    )

    assert call_count == 2
    assert response.model == "demo-model"
    assert response.finish_reason == "stop"
