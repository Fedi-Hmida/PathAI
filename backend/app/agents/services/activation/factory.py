from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import AssessorAgent, CriticAgent, CurriculumAgent, KnowledgeMapAgent
from app.agents.llm.assessment import LLMAssessmentAgent
from app.agents.llm.client_selection import build_llm_client_for_agent
from app.agents.llm.critic import LLMCriticAgent
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.agents.llm.observer_selection import build_default_observer
from app.agents.llm.retry_policy_selection import resolve_retry_policy
from app.agents.mock import (
    MockAssessorAgent,
    MockCriticAgent,
    MockCurriculumAgent,
    MockKnowledgeMapAgent,
)
from app.agents.services.bundle import (
    AgentIntegrationSwitches,
    AssessmentAgentMode,
    CriticAgentMode,
    CurriculumAgentMode,
    KnowledgeMapAgentMode,
)
from app.core.settings import Settings


@dataclass(slots=True, frozen=True)
class InjectedAgents:
    """LLM-backed agents to inject into `build_mock_agent_service_bundle`.

    A `None` field means "no override" — the bundle keeps using its own
    default deterministic mock agent for that role.
    """

    assessment: AssessorAgent | None = None
    knowledge_map: KnowledgeMapAgent | None = None
    critic: CriticAgent | None = None
    curriculum: CurriculumAgent | None = None


def build_injected_agents(
    switches: AgentIntegrationSwitches,
    settings: Settings,
) -> InjectedAgents:
    """Build LLM-backed agent instances for every switch resolved to `LLM`.

    Every constructed agent always carries its matching deterministic mock
    agent as `fallback_agent` with `fallback_on_error=True` — a live/fake
    provider failure degrades to deterministic output, it never hard-fails
    the caller.
    """
    return InjectedAgents(
        assessment=_build_assessment_agent(switches, settings),
        knowledge_map=_build_knowledge_map_agent(switches, settings),
        critic=_build_critic_agent(switches, settings),
        curriculum=_build_curriculum_agent(switches, settings),
    )


def _build_assessment_agent(
    switches: AgentIntegrationSwitches,
    settings: Settings,
) -> AssessorAgent | None:
    if switches.assessment_agent_mode != AssessmentAgentMode.LLM:
        return None
    client = build_llm_client_for_agent(settings)
    retry_policy = resolve_retry_policy(settings)
    return LLMAssessmentAgent(
        client=client,
        fallback_agent=MockAssessorAgent(),
        fallback_on_error=True,
        retry_policy=retry_policy,
        observer=build_default_observer(),
    )


def _build_knowledge_map_agent(
    switches: AgentIntegrationSwitches,
    settings: Settings,
) -> KnowledgeMapAgent | None:
    if switches.knowledge_map_agent_mode != KnowledgeMapAgentMode.LLM:
        return None
    client = build_llm_client_for_agent(settings)
    retry_policy = resolve_retry_policy(settings)
    return LLMKnowledgeMapAgent(
        client=client,
        fallback_agent=MockKnowledgeMapAgent(),
        fallback_on_error=True,
        retry_policy=retry_policy,
        observer=build_default_observer(),
    )


def _build_critic_agent(
    switches: AgentIntegrationSwitches,
    settings: Settings,
) -> CriticAgent | None:
    if switches.critic_agent_mode != CriticAgentMode.LLM:
        return None
    client = build_llm_client_for_agent(settings)
    retry_policy = resolve_retry_policy(settings)
    return LLMCriticAgent(
        client=client,
        fallback_agent=MockCriticAgent(),
        fallback_on_error=True,
        retry_policy=retry_policy,
        observer=build_default_observer(),
    )


def _build_curriculum_agent(
    switches: AgentIntegrationSwitches,
    settings: Settings,
) -> CurriculumAgent | None:
    if switches.curriculum_agent_mode != CurriculumAgentMode.LLM:
        return None
    client = build_llm_client_for_agent(settings)
    retry_policy = resolve_retry_policy(settings)
    return LLMCurriculumAgent(
        client=client,
        fallback_agent=MockCurriculumAgent(),
        fallback_on_error=True,
        retry_policy=retry_policy,
        observer=build_default_observer(),
    )
