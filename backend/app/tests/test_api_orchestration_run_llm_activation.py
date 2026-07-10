from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.llm.fake_client as fake_client_module
from app.agents.deterministic.critic import build_critic_output
from app.agents.deterministic.curriculum import build_curriculum_output
from app.agents.deterministic.knowledge_map import build_knowledge_map_output
from app.agents.services.activation import factory as factory_module
from app.api.v1.dependencies import reset_api_container_for_tests
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.llm.contracts import RawLLMResponse, StructuredOutputRequest
from app.llm.fake_client import FakeLLMClient
from app.llm.observability.budget import RunBudget, RunScopedBudgetObserver
from app.llm.observability.events import LLMReliabilityEvent, LLMReliabilityEventType
from app.llm.observability.sinks import LoggingObserver
from app.main import create_app
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput

# All tests in this file are offline and deterministic: LLM_PROVIDER=fake only,
# never a real provider, network, or credentials (RULES.md §17.4).


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    # get_settings() is @lru_cache'd; without clearing, monkeypatched env vars
    # either read stale cached settings or leak into later tests.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_route_activates_knowledge_map_llm_agent_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    km_payload = build_knowledge_map_output(_knowledge_map_input()).model_dump(mode="json")
    _augment_default_payloads(monkeypatch, {KnowledgeMapAgentOutput.__name__: km_payload})
    call_log = _spy_on_generate(monkeypatch)

    response = _client().post("/api/v1/orchestration/runs")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    # The real proof this went through the LLM path, not just that the run
    # completed (which fallback would also produce): the fake client's
    # generate() was actually invoked for the knowledge-map schema.
    assert KnowledgeMapAgentOutput.__name__ in call_log


def test_route_activates_validated_critic_curriculum_combination_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    curriculum_payload = build_curriculum_output(_curriculum_input()).model_dump(mode="json")
    critic_payload = build_critic_output(_critic_input()).model_dump(mode="json")
    _augment_default_payloads(
        monkeypatch,
        {
            CurriculumAgentOutput.__name__: curriculum_payload,
            CriticAgentOutput.__name__: critic_payload,
        },
    )
    call_log = _spy_on_generate(monkeypatch)

    response = _client().post("/api/v1/orchestration/runs")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert CurriculumAgentOutput.__name__ in call_log
    assert CriticAgentOutput.__name__ in call_log


def test_route_rejects_non_allowlisted_combination_as_server_error_not_silent_degrade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # assessment+critic is not in VALIDATED_COMBINATIONS (only critic+curriculum
    # is, per Rebuild-22C). ActivationConfigError is raised the moment the
    # pipeline resolves its agent bundle (inside OrchestrationContext.from_
    # container, called from run_demo_pipeline at request time) — there is no
    # eager switch resolution in ApiServiceContainer.__post_init__, so this
    # surfaces per-request, not at process startup. No handler is registered
    # for ActivationConfigError, so it becomes a genuine 500, matching decision
    # 4's "5xx reserved for genuinely unexpected/misconfigured errors" — it
    # never silently activates and never silently degrades to fewer agents.
    monkeypatch.setenv("PATHAI_ENABLE_LLM_ASSESSMENT_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    response = _client(raise_server_exceptions=False).post("/api/v1/orchestration/runs")

    assert response.status_code == 500
    assert "PATHAI_ENABLE" not in response.text
    assert "fake" not in response.text.lower()


def test_route_degrades_to_fallback_when_run_budget_already_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    exhausted_observer = RunScopedBudgetObserver(
        RunBudget(max_llm_calls=1),
        inner=LoggingObserver(),
    )
    exhausted_observer.record(
        LLMReliabilityEvent(
            event_type=LLMReliabilityEventType.ATTEMPT_STARTED,
            schema_name=KnowledgeMapAgentOutput.__name__,
            attempt=1,
            max_attempts=1,
        ),
    )
    assert exhausted_observer.exhausted() is True
    monkeypatch.setattr(factory_module, "build_run_scoped_observer", lambda: exhausted_observer)
    call_log = _spy_on_generate(monkeypatch)

    response = _client().post("/api/v1/orchestration/runs")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    # Fail-safe: the exhausted budget means the knowledge-map agent's LLM
    # call is skipped entirely (degrades straight to its deterministic
    # fallback) — the run still completes, it never hard-fails.
    assert KnowledgeMapAgentOutput.__name__ not in call_log


def _client(*, raise_server_exceptions: bool = True) -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app(), raise_server_exceptions=raise_server_exceptions)


def _spy_on_generate(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    call_log: list[str] = []
    original_generate = FakeLLMClient.generate

    async def _spy(self: FakeLLMClient, request: StructuredOutputRequest) -> RawLLMResponse:
        call_log.append(request.schema_name)
        return await original_generate(self, request)

    monkeypatch.setattr(FakeLLMClient, "generate", _spy)
    return call_log


def _augment_default_payloads(
    monkeypatch: pytest.MonkeyPatch,
    extra: dict[str, object],
) -> None:
    original_default_payloads = fake_client_module._default_payloads

    def _augmented() -> dict[str, object]:
        payloads = original_default_payloads()
        payloads.update(extra)
        return payloads

    monkeypatch.setattr(fake_client_module, "_default_payloads", _augmented)


def _knowledge_map_input() -> KnowledgeMapAgentInput:
    return KnowledgeMapAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        assessment_answers=demo.ASSESSMENT_ANSWERS,
        concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
    )


def _curriculum_input() -> CurriculumAgentInput:
    return CurriculumAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        learner_profile=demo.LEARNING_GOAL.learner_profile,
        knowledge_map=demo.KNOWLEDGE_MAP,
        duration_weeks=demo.CURRICULUM.duration_weeks,
        hours_per_week=demo.LEARNING_GOAL.hours_per_week,
        critic_recommendations=[],
    )


def _critic_input() -> CriticAgentInput:
    return CriticAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resource_attachments=demo.RESOURCE_ATTACHMENTS,
        rubric_weights={},
    )
