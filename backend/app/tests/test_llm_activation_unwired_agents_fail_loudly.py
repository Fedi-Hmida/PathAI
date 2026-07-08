from __future__ import annotations

import pytest

from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.agents.mock import (
    MockAssessorAgent,
    MockCriticAgent,
    MockCurriculumAgent,
    MockKnowledgeMapAgent,
)
from app.agents.services.activation import ActivationConfigError
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
from app.llm.fake_client import FakeLLMClient
from app.orchestration.nodes import OrchestrationContext


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    # get_settings() is @lru_cache'd; without clearing, monkeypatched env vars
    # in this file either read stale cached settings or leak into later tests.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_assessment_flag_alone_raises_activation_config_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_ASSESSMENT_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    with pytest.raises(ActivationConfigError) as exc_info:
        OrchestrationContext.from_container(container)

    assert "assessment_agent_mode" in str(exc_info.value)


def test_critic_flag_alone_raises_activation_config_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    with pytest.raises(ActivationConfigError) as exc_info:
        OrchestrationContext.from_container(container)

    assert "critic_agent_mode" in str(exc_info.value)


def test_curriculum_flag_alone_raises_activation_config_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    with pytest.raises(ActivationConfigError) as exc_info:
        OrchestrationContext.from_container(container)

    assert "curriculum_agent_mode" in str(exc_info.value)


@pytest.mark.parametrize(
    "flag_name",
    [
        "PATHAI_ENABLE_LLM_ASSESSMENT_AGENT",
        "PATHAI_ENABLE_LLM_CRITIC_AGENT",
        "PATHAI_ENABLE_LLM_CURRICULUM_AGENT",
    ],
)
def test_error_message_contains_no_secret_shaped_values(
    flag_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(flag_name, "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setenv("LLM_API_KEY", "super-secret-api-key-value")

    container = ApiServiceContainer()
    with pytest.raises(ActivationConfigError) as exc_info:
        OrchestrationContext.from_container(container)

    assert "super-secret-api-key-value" not in str(exc_info.value)


def test_knowledge_map_flag_still_resolves_to_llm_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    knowledge_map_agent = context.agent_services.knowledge_map.agent
    assert isinstance(knowledge_map_agent, LLMKnowledgeMapAgent)
    assert isinstance(knowledge_map_agent.client, FakeLLMClient)


def test_no_flags_set_still_resolves_to_all_deterministic() -> None:
    container = ApiServiceContainer()

    context = OrchestrationContext.from_container(container)

    bundle = context.agent_services
    assert isinstance(bundle.assessment.agent, MockAssessorAgent)
    assert isinstance(bundle.knowledge_map.agent, MockKnowledgeMapAgent)
    assert isinstance(bundle.critic.agent, MockCriticAgent)
    assert isinstance(bundle.curriculum.agent, MockCurriculumAgent)
