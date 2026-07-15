from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import AssessorAgent, CriticAgent, CurriculumAgent, KnowledgeMapAgent
from app.agents.llm.assessment import LLMAssessmentAgent
from app.agents.llm.client_selection import build_llm_client_for_agent
from app.agents.llm.critic import LLMCriticAgent
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.agents.llm.observer_selection import build_run_scoped_observer
from app.agents.llm.retry_policy_selection import resolve_retry_policy
from app.agents.llm.timeout_policy_selection import resolve_timeout_policy
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

    Fallback policy is governed by `PATHAI_LLM_FALLBACK_MODE`
    (`Settings.llm_deterministic_fallback_enabled`):

    - fail-loud (default): agents carry no fallback (`fallback_on_error=False`),
      so a live/fake provider failure raises `LLMGenerationUnavailableError`
      rather than silently degrading to another topic's canned deterministic
      output.
    - deterministic (opt-in, for offline tests / an intentional offline demo):
      each agent carries its matching deterministic mock agent as
      `fallback_agent` with `fallback_on_error=True`, restoring the legacy
      degrade-on-failure behavior.

    All agents built from this one call share a single run-scoped observer
    (Rebuild-22B), so a run-level call/wall-clock ceiling applies across every
    agent in the run rather than independently per agent.
    """
    observer = build_run_scoped_observer()
    return InjectedAgents(
        assessment=_build_assessment_agent(switches, settings, observer),
        knowledge_map=_build_knowledge_map_agent(switches, settings, observer),
        critic=_build_critic_agent(switches, settings, observer),
        curriculum=_build_curriculum_agent(switches, settings, observer),
    )


def _build_assessment_agent(
    switches: AgentIntegrationSwitches,
    settings: Settings,
    observer,
) -> AssessorAgent | None:
    if switches.assessment_agent_mode != AssessmentAgentMode.LLM:
        return None
    client = build_llm_client_for_agent(settings)
    retry_policy = resolve_retry_policy(settings)
    timeout_policy = resolve_timeout_policy(settings)
    degrade = settings.llm_deterministic_fallback_enabled
    return LLMAssessmentAgent(
        client=client,
        fallback_agent=MockAssessorAgent() if degrade else None,
        fallback_on_error=degrade,
        retry_policy=retry_policy,
        timeout_policy=timeout_policy,
        observer=observer,
    )


def _build_knowledge_map_agent(
    switches: AgentIntegrationSwitches,
    settings: Settings,
    observer,
) -> KnowledgeMapAgent | None:
    if switches.knowledge_map_agent_mode != KnowledgeMapAgentMode.LLM:
        return None
    client = build_llm_client_for_agent(settings)
    retry_policy = resolve_retry_policy(settings)
    timeout_policy = resolve_timeout_policy(settings)
    degrade = settings.llm_deterministic_fallback_enabled
    return LLMKnowledgeMapAgent(
        client=client,
        fallback_agent=MockKnowledgeMapAgent() if degrade else None,
        fallback_on_error=degrade,
        retry_policy=retry_policy,
        timeout_policy=timeout_policy,
        observer=observer,
    )


def _build_critic_agent(
    switches: AgentIntegrationSwitches,
    settings: Settings,
    observer,
) -> CriticAgent | None:
    if switches.critic_agent_mode != CriticAgentMode.LLM:
        return None
    client = build_llm_client_for_agent(settings)
    retry_policy = resolve_retry_policy(settings)
    timeout_policy = resolve_timeout_policy(settings)
    degrade = settings.llm_deterministic_fallback_enabled
    return LLMCriticAgent(
        client=client,
        fallback_agent=MockCriticAgent() if degrade else None,
        fallback_on_error=degrade,
        retry_policy=retry_policy,
        timeout_policy=timeout_policy,
        observer=observer,
    )


def _build_curriculum_agent(
    switches: AgentIntegrationSwitches,
    settings: Settings,
    observer,
) -> CurriculumAgent | None:
    if switches.curriculum_agent_mode != CurriculumAgentMode.LLM:
        return None
    client = build_llm_client_for_agent(settings)
    retry_policy = resolve_retry_policy(settings)
    timeout_policy = resolve_timeout_policy(settings)
    degrade = settings.llm_deterministic_fallback_enabled
    return LLMCurriculumAgent(
        client=client,
        fallback_agent=MockCurriculumAgent() if degrade else None,
        fallback_on_error=degrade,
        retry_policy=retry_policy,
        timeout_policy=timeout_policy,
        observer=observer,
    )
