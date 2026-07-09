from __future__ import annotations

from app.agents.services.activation.allowlist import VALIDATED_COMBINATIONS
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

    Zero or one enabled flag always resolves, unconditionally — this is the
    safe default and has been unchanged since Rebuild-14B. Two or more flags
    resolve together only if that exact combination appears in
    `VALIDATED_COMBINATIONS` (Rebuild-22C); any other combination of 2+ raises
    `ActivationConfigError` naming the rejected combination, rather than
    silently activating an unvalidated pairing of real LLM agents.
    """
    enabled_flags = frozenset(_enabled_flags(settings))

    if len(enabled_flags) > 1 and enabled_flags not in VALIDATED_COMBINATIONS:
        conflicting = ", ".join(sorted(enabled_flags))
        msg = (
            "This combination of LLM agents is not on the validated-combination "
            f"allowlist: {conflicting}. See VALIDATED_COMBINATIONS in "
            "app/agents/services/activation/allowlist.py for currently allowed "
            "combinations."
        )
        raise ActivationConfigError(msg)

    return AgentIntegrationSwitches(
        assessment_agent_mode=(
            AssessmentAgentMode.LLM
            if "assessment_agent_mode" in enabled_flags
            else AssessmentAgentMode.DETERMINISTIC
        ),
        knowledge_map_agent_mode=(
            KnowledgeMapAgentMode.LLM
            if "knowledge_map_agent_mode" in enabled_flags
            else KnowledgeMapAgentMode.DETERMINISTIC
        ),
        critic_agent_mode=(
            CriticAgentMode.LLM
            if "critic_agent_mode" in enabled_flags
            else CriticAgentMode.DETERMINISTIC
        ),
        curriculum_agent_mode=(
            CurriculumAgentMode.LLM
            if "curriculum_agent_mode" in enabled_flags
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
