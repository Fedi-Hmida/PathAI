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
from app.llm.observability.budget import RunBudget
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.enums import CriticPassStatus, OrchestrationRunStatus


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _forced_rejection_context(monkeypatch: pytest.MonkeyPatch) -> OrchestrationContext:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    context = OrchestrationContext.from_container(ApiServiceContainer())

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
    critic_agent.client.payloads[CriticAgentOutput.__name__] = (
        build_critic_output(critic_input)
        .model_copy(update={"pass_status": CriticPassStatus.REVISE})
        .model_dump(mode="json")
    )
    return context


def test_looping_run_stays_under_the_unchanged_run_budget_and_terminates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _forced_rejection_context(monkeypatch)
    curriculum_agent = context.agent_services.curriculum.agent
    critic_agent = context.agent_services.critic.agent
    assert isinstance(curriculum_agent, LLMCurriculumAgent)
    assert isinstance(critic_agent, LLMCriticAgent)
    curriculum_client = curriculum_agent.client
    critic_client = critic_agent.client
    assert isinstance(curriculum_client, FakeLLMClient)
    assert isinstance(critic_client, FakeLLMClient)

    result = run_straight_line_demo(context)

    # The run terminates (completing at all is the proof it does not spin).
    assert result.run.status == OrchestrationRunStatus.COMPLETED_WITH_WARNINGS

    total_llm_calls = curriculum_client.call_count + critic_client.call_count
    # One capped revision = 2 curriculum + 2 critic calls.
    assert total_llm_calls == 4
    # The Rebuild-40-calibrated run budget still comfortably covers the loop —
    # the hard revision cap, not a re-sized or separate budget, is the bound.
    assert RunBudget().max_llm_calls == 16
    assert total_llm_calls < RunBudget().max_llm_calls
    # The bound is the reused revision counter, capped at 1 — no new accounting.
    assert result.state.critic_revision_attempts == 1
