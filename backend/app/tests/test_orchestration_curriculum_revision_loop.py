from __future__ import annotations

import pytest

from app.agents.deterministic.critic import build_critic_output
from app.agents.deterministic.curriculum import build_curriculum_output
from app.agents.llm.critic import LLMCriticAgent
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.llm.contracts import RawLLMResponse, StructuredOutputRequest
from app.llm.fake_client import FakeLLMClient
from app.orchestration.graph import MAX_CRITIC_REVISION_ATTEMPTS
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.enums import CriticPassStatus, OrchestrationStatus

_RECOMMENDATION_SENTINEL = "REBUILD_23C_REVISION_RECOMMENDATION_SENTINEL"


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    # get_settings() is @lru_cache'd; clear around each test so monkeypatched env
    # vars neither read stale settings nor leak into later tests.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _enable_critic_and_curriculum(monkeypatch: pytest.MonkeyPatch) -> OrchestrationContext:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    container = ApiServiceContainer()
    return OrchestrationContext.from_container(container)


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


def _curriculum_payload() -> dict[str, object]:
    return build_curriculum_output(_curriculum_input()).model_dump(mode="json")


def _critic_payload(pass_status: CriticPassStatus, recommendations: list[str]) -> dict[str, object]:
    base = build_critic_output(_critic_input())
    revised = base.model_copy(
        update={"pass_status": pass_status, "revision_recommendations": recommendations},
    )
    return revised.model_dump(mode="json")


def test_forced_rejection_loop_terminates_at_cap_and_feeds_recommendations_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _enable_critic_and_curriculum(monkeypatch)
    curriculum_agent = context.agent_services.curriculum.agent
    critic_agent = context.agent_services.critic.agent
    assert isinstance(curriculum_agent, LLMCurriculumAgent)
    assert isinstance(critic_agent, LLMCriticAgent)
    curriculum_client = curriculum_agent.client
    critic_client = critic_agent.client
    assert isinstance(curriculum_client, FakeLLMClient)
    assert isinstance(critic_client, FakeLLMClient)

    curriculum_client.payloads[CurriculumAgentOutput.__name__] = _curriculum_payload()
    # The critic never approves — it always asks to revise, with a distinctive
    # recommendation the regenerated curriculum prompt must carry.
    critic_client.payloads[CriticAgentOutput.__name__] = _critic_payload(
        CriticPassStatus.REVISE,
        [_RECOMMENDATION_SENTINEL],
    )

    curriculum_prompts: list[str] = []
    original_generate = curriculum_client.generate

    async def _spy_generate(request: StructuredOutputRequest) -> RawLLMResponse:
        curriculum_prompts.append(request.prompt)
        return await original_generate(request)

    monkeypatch.setattr(curriculum_client, "generate", _spy_generate)

    result = run_straight_line_demo(context)

    # The loop is hard-capped, so it terminates rather than spinning.
    assert result.state.status == OrchestrationStatus.COMPLETED
    assert MAX_CRITIC_REVISION_ATTEMPTS == 1
    # load_curriculum ran once for the initial draft + once for the single revision.
    assert result.state.node_attempts["load_curriculum"] == 2
    assert result.state.critic_revision_attempts == 1
    # 2 curriculum calls + 2 critic calls = 4 LLM calls, well under the run budget.
    assert curriculum_client.call_count == 2
    assert critic_client.call_count == 2

    # Reverse-direction handoff (the point of the phase): the critic's real
    # recommendation reached the *regenerated* curriculum prompt, and was absent
    # from the first draft's prompt (which had no critic output yet).
    assert len(curriculum_prompts) == 2
    assert _RECOMMENDATION_SENTINEL not in curriculum_prompts[0]
    assert _RECOMMENDATION_SENTINEL in curriculum_prompts[1]


def test_critic_approval_on_first_pass_does_not_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _enable_critic_and_curriculum(monkeypatch)
    curriculum_agent = context.agent_services.curriculum.agent
    critic_agent = context.agent_services.critic.agent
    assert isinstance(curriculum_agent, LLMCurriculumAgent)
    assert isinstance(critic_agent, LLMCriticAgent)
    curriculum_client = curriculum_agent.client
    critic_client = critic_agent.client
    assert isinstance(curriculum_client, FakeLLMClient)
    assert isinstance(critic_client, FakeLLMClient)

    curriculum_client.payloads[CurriculumAgentOutput.__name__] = _curriculum_payload()
    critic_client.payloads[CriticAgentOutput.__name__] = _critic_payload(
        CriticPassStatus.PASS,
        [],
    )

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert result.state.node_attempts["load_curriculum"] == 1
    assert result.state.critic_revision_attempts == 0
    assert curriculum_client.call_count == 1
    assert critic_client.call_count == 1
