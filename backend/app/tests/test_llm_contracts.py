from __future__ import annotations

from app.llm import (
    LLM_ENV_VAR_NAMES,
    LLMAdapterConfig,
    LLMClient,
    LLMModelMetadata,
    LLMRetryPolicy,
    LLMTimeoutPolicy,
    RawLLMResponse,
    StructuredOutputRequest,
)
from app.llm.fake_client import FakeLLMClient


def test_llm_contract_models_are_provider_neutral_and_secret_free() -> None:
    request = StructuredOutputRequest(
        prompt="Return JSON for a tiny schema.",
        schema_name="MiniKnowledgeMapOutput",
        request_id="req_demo",
        metadata=LLMModelMetadata(),
        timeout=LLMTimeoutPolicy(timeout_seconds=30),
        max_output_tokens=512,
    )
    response = RawLLMResponse(
        provider="fake",
        model="deterministic-fake",
        text='{"summary":"ok"}',
        request_id=request.request_id,
    )

    assert request.metadata.provider == "fake"
    assert request.metadata.model == "deterministic-fake"
    assert response.provider == "fake"
    assert isinstance(FakeLLMClient(), LLMClient)


def test_llm_config_uses_names_only_and_defaults_to_fake() -> None:
    config = LLMAdapterConfig.default_fake()
    summary = config.safe_summary()

    assert config.provider == "fake"
    assert config.live_enabled is False
    assert "LLM_API_KEY" in LLM_ENV_VAR_NAMES
    env_var_names = summary["env_var_names"]
    assert isinstance(env_var_names, list)
    assert "OPENAI_API_KEY" in env_var_names
    assert "api_key=" not in str(summary).lower()


def test_retry_policy_is_capped() -> None:
    policy = LLMRetryPolicy(max_attempts=2)

    assert policy.max_attempts == 2
    assert policy.retry_on_parse_error is True
