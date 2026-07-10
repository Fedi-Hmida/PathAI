from __future__ import annotations

import pytest

from app.agents.deterministic.critic import build_critic_output
from app.agents.deterministic.curriculum import build_curriculum_output
from app.agents.llm.critic import LLMCriticAgent
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.llm.fake_client import FakeLLMClient
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.enums import CriticPassStatus, OrchestrationRunStatus

_RECOMMENDATION_SENTINEL = "REBUILD_23D_LEAK_CANARY_RECOMMENDATION"


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _context(monkeypatch: pytest.MonkeyPatch) -> OrchestrationContext:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    return OrchestrationContext.from_container(ApiServiceContainer())


def _seed(
    context: OrchestrationContext,
    *,
    pass_status: CriticPassStatus,
    recommendations: list[str],
) -> None:
    curriculum_agent = context.agent_services.curriculum.agent
    critic_agent = context.agent_services.critic.agent
    assert isinstance(curriculum_agent, LLMCurriculumAgent)
    assert isinstance(critic_agent, LLMCriticAgent)
    assert isinstance(curriculum_agent.client, FakeLLMClient)
    assert isinstance(critic_agent.client, FakeLLMClient)

    curriculum_input = CurriculumAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        learner_profile=demo.LEARNING_GOAL.learner_profile,
        knowledge_map=demo.KNOWLEDGE_MAP,
        duration_weeks=demo.CURRICULUM.duration_weeks,
        hours_per_week=demo.LEARNING_GOAL.hours_per_week,
        critic_recommendations=[],
    )
    critic_input = CriticAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resource_attachments=demo.RESOURCE_ATTACHMENTS,
        rubric_weights={},
    )
    curriculum_agent.client.payloads[CurriculumAgentOutput.__name__] = build_curriculum_output(
        curriculum_input,
    ).model_dump(mode="json")
    critic_output = build_critic_output(critic_input).model_copy(
        update={"pass_status": pass_status, "revision_recommendations": recommendations},
    )
    critic_agent.client.payloads[CriticAgentOutput.__name__] = critic_output.model_dump(mode="json")


def test_cap_hit_without_approval_completes_with_a_single_sanitized_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(monkeypatch)
    _seed(context, pass_status=CriticPassStatus.REVISE, recommendations=[_RECOMMENDATION_SENTINEL])

    result = run_straight_line_demo(context)

    assert result.run.status == OrchestrationRunStatus.COMPLETED_WITH_WARNINGS
    assert len(result.run.warnings) == 1
    warning = result.run.warnings[0]
    assert warning.warning_code == "curriculum_revision_limit_reached"
    # The last (revised) curriculum was accepted, keeping the stable demo ID.
    assert result.run.artifact_ids.get("curriculum_id") == demo.CURRICULUM_ID

    # The warning must leak no critic recommendation / curriculum content.
    serialized = warning.model_dump_json()
    assert _RECOMMENDATION_SENTINEL not in serialized
    for shape in ("key", "token", "password", "secret", "prompt"):
        assert shape not in warning.message.lower()


def test_critic_approval_completes_plain_without_warnings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(monkeypatch)
    _seed(context, pass_status=CriticPassStatus.PASS, recommendations=[])

    result = run_straight_line_demo(context)

    assert result.run.status == OrchestrationRunStatus.COMPLETED
    assert result.run.warnings == []
