from __future__ import annotations

from app.agents.services.activation.errors import ActivationConfigError
from app.agents.services.bundle import (
    AgentIntegrationSwitches,
    AssessmentAgentMode,
    CriticAgentMode,
    CurriculumAgentMode,
    KnowledgeMapAgentMode,
)
from app.core.settings import Settings

_AGENT_FLAG_NAMES: tuple[str, ...] = (
    "assessment_agent_mode",
    "knowledge_map_agent_mode",
    "critic_agent_mode",
    "curriculum_agent_mode",
)


def resolve_agent_integration_switches(settings: Settings) -> AgentIntegrationSwitches:
    """Resolve per-agent LLM activation flags into `AgentIntegrationSwitches`.

    Enforces one-agent-at-a-time activation: enabling more than one
    `PATHAI_ENABLE_LLM_*_AGENT` flag at once raises `ActivationConfigError`
    instead of silently allowing simultaneous LLM-backed agents.
    """
    enabled_flags = _enabled_flags(settings)

    if len(enabled_flags) > 1:
        conflicting = ", ".join(sorted(enabled_flags))
        msg = (
            "Only one LLM agent may be enabled at a time. "
            f"Conflicting flags: {conflicting}."
        )
        raise ActivationConfigError(msg)

    if not enabled_flags:
        return AgentIntegrationSwitches()

    selected = enabled_flags[0]
    return AgentIntegrationSwitches(
        assessment_agent_mode=(
            AssessmentAgentMode.LLM
            if selected == "assessment_agent_mode"
            else AssessmentAgentMode.DETERMINISTIC
        ),
        knowledge_map_agent_mode=(
            KnowledgeMapAgentMode.LLM
            if selected == "knowledge_map_agent_mode"
            else KnowledgeMapAgentMode.DETERMINISTIC
        ),
        critic_agent_mode=(
            CriticAgentMode.LLM
            if selected == "critic_agent_mode"
            else CriticAgentMode.DETERMINISTIC
        ),
        curriculum_agent_mode=(
            CurriculumAgentMode.LLM
            if selected == "curriculum_agent_mode"
            else CurriculumAgentMode.DETERMINISTIC
        ),
    )


def _enabled_flags(settings: Settings) -> list[str]:
    flag_values = {
        "assessment_agent_mode": settings.enable_llm_assessment_agent,
        "knowledge_map_agent_mode": settings.enable_llm_knowledge_map_agent,
        "critic_agent_mode": settings.enable_llm_critic_agent,
        "curriculum_agent_mode": settings.enable_llm_curriculum_agent,
    }
    return [name for name in _AGENT_FLAG_NAMES if flag_values[name]]
