from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.llm.fake_client as fake_client_module
from app.agents.deterministic.critic import build_critic_output
from app.agents.deterministic.curriculum import build_curriculum_output
from app.api.v1.dependencies import reset_api_container_for_tests
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.llm.contracts import RawLLMResponse, StructuredOutputRequest
from app.llm.fake_client import FakeLLMClient
from app.main import create_app
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.enums import CriticPassStatus

# Offline and deterministic: LLM_PROVIDER=fake only, never a real provider.


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_route_returns_completed_with_warnings_when_revision_cap_is_hit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    curriculum_payload = build_curriculum_output(_curriculum_input()).model_dump(mode="json")
    critic_payload = (
        build_critic_output(_critic_input())
        .model_copy(update={"pass_status": CriticPassStatus.REVISE})
        .model_dump(mode="json")
    )
    _augment_default_payloads(
        monkeypatch,
        {
            CurriculumAgentOutput.__name__: curriculum_payload,
            CriticAgentOutput.__name__: critic_payload,
        },
    )
    call_log = _spy_on_generate(monkeypatch)

    client = _client()
    response = client.post("/api/v1/orchestration/runs")

    # A looping run over the synchronous route still returns promptly with the
    # distinguishable terminal status — the loop is bounded, so the request
    # cannot hang.
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed_with_warnings"
    assert len(body["warnings"]) == 1
    assert body["warnings"][0]["warning_code"] == "curriculum_revision_limit_reached"

    # The loop genuinely executed through the HTTP path: two curriculum
    # generations and two critic reviews.
    assert call_log.count(CurriculumAgentOutput.__name__) == 2
    assert call_log.count(CriticAgentOutput.__name__) == 2

    # Read-back over the pre-existing GET reflects the same terminal status.
    run_id = body["run_id"]
    get_body = client.get(f"/api/v1/orchestration/runs/{run_id}").json()
    assert get_body["status"] == "completed_with_warnings"
    assert len(get_body["warnings"]) == 1


def test_default_deterministic_route_is_unchanged_plain_completed() -> None:
    # No LLM flags: the route is a no-op wrapper over the graph — the default
    # deterministic run still completes plainly, exactly as before Rebuild-23.
    client = _client()
    response = client.post("/api/v1/orchestration/runs")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["warnings"] == []


def _client() -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app())


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
