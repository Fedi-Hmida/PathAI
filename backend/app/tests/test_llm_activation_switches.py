from __future__ import annotations

from itertools import combinations

import pytest

from app.agents.services.activation import ActivationConfigError, resolve_agent_integration_switches
from app.agents.services.activation.allowlist import VALIDATED_COMBINATIONS
from app.agents.services.bundle import (
    AgentIntegrationSwitches,
    AssessmentAgentMode,
    CriticAgentMode,
    CurriculumAgentMode,
    KnowledgeMapAgentMode,
)
from app.core.settings import Settings

_FLAG_FIELDS: tuple[str, ...] = (
    "enable_llm_assessment_agent",
    "enable_llm_knowledge_map_agent",
    "enable_llm_critic_agent",
    "enable_llm_curriculum_agent",
)

_FLAG_ENV_VARS: dict[str, str] = {
    "enable_llm_assessment_agent": "PATHAI_ENABLE_LLM_ASSESSMENT_AGENT",
    "enable_llm_knowledge_map_agent": "PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT",
    "enable_llm_critic_agent": "PATHAI_ENABLE_LLM_CRITIC_AGENT",
    "enable_llm_curriculum_agent": "PATHAI_ENABLE_LLM_CURRICULUM_AGENT",
}

_SWITCH_FIELD_FOR_FLAG: dict[str, str] = {
    "enable_llm_assessment_agent": "assessment_agent_mode",
    "enable_llm_knowledge_map_agent": "knowledge_map_agent_mode",
    "enable_llm_critic_agent": "critic_agent_mode",
    "enable_llm_curriculum_agent": "curriculum_agent_mode",
}

_LLM_MODE_FOR_FLAG: dict[str, object] = {
    "enable_llm_assessment_agent": AssessmentAgentMode.LLM,
    "enable_llm_knowledge_map_agent": KnowledgeMapAgentMode.LLM,
    "enable_llm_critic_agent": CriticAgentMode.LLM,
    "enable_llm_curriculum_agent": CurriculumAgentMode.LLM,
}


def test_no_flags_set_returns_default_deterministic_switches() -> None:
    settings = Settings()

    switches = resolve_agent_integration_switches(settings)

    assert switches == AgentIntegrationSwitches()


@pytest.mark.parametrize("flag_field", _FLAG_FIELDS)
def test_single_flag_enables_only_its_own_switch(flag_field: str) -> None:
    settings = Settings.model_validate({flag_field: True})

    switches = resolve_agent_integration_switches(settings)

    for other_flag, switch_field in _SWITCH_FIELD_FOR_FLAG.items():
        value = getattr(switches, switch_field)
        if other_flag == flag_field:
            assert value == _LLM_MODE_FOR_FLAG[flag_field]
        else:
            assert value.value == "deterministic"


# Excludes any pair already on the validated-combination allowlist (Rebuild-22C)
# so this list adapts automatically as the allowlist grows, without needing a
# hand-maintained exclusion here.
_NON_ALLOWLISTED_FLAG_PAIRS: list[tuple[str, str]] = [
    pair
    for pair in combinations(_FLAG_FIELDS, 2)
    if frozenset(_SWITCH_FIELD_FOR_FLAG[flag] for flag in pair) not in VALIDATED_COMBINATIONS
]


@pytest.mark.parametrize("flag_pair", _NON_ALLOWLISTED_FLAG_PAIRS)
def test_two_flags_enabled_raises_activation_config_error(
    flag_pair: tuple[str, str],
) -> None:
    settings = Settings.model_validate({flag_pair[0]: True, flag_pair[1]: True})

    with pytest.raises(ActivationConfigError) as exc_info:
        resolve_agent_integration_switches(settings)

    message = str(exc_info.value)
    assert _SWITCH_FIELD_FOR_FLAG[flag_pair[0]] in message
    assert _SWITCH_FIELD_FOR_FLAG[flag_pair[1]] in message


def test_allowlisted_critic_curriculum_combination_resolves_to_both_llm() -> None:
    settings = Settings(
        enable_llm_critic_agent=True,
        enable_llm_curriculum_agent=True,
    )

    switches = resolve_agent_integration_switches(settings)

    assert switches.critic_agent_mode == CriticAgentMode.LLM
    assert switches.curriculum_agent_mode == CurriculumAgentMode.LLM
    assert switches.assessment_agent_mode == AssessmentAgentMode.DETERMINISTIC
    assert switches.knowledge_map_agent_mode == KnowledgeMapAgentMode.DETERMINISTIC


def test_three_flags_enabled_raises_activation_config_error() -> None:
    settings = Settings(
        enable_llm_assessment_agent=True,
        enable_llm_knowledge_map_agent=True,
        enable_llm_critic_agent=True,
    )

    with pytest.raises(ActivationConfigError):
        resolve_agent_integration_switches(settings)


def test_all_four_flags_enabled_raises_activation_config_error() -> None:
    settings = Settings.model_validate({flag: True for flag in _FLAG_FIELDS})

    with pytest.raises(ActivationConfigError):
        resolve_agent_integration_switches(settings)


def test_conflict_error_message_contains_no_secret_shaped_values() -> None:
    settings = Settings(
        enable_llm_assessment_agent=True,
        enable_llm_critic_agent=True,
        llm_api_key="super-secret-api-key-value",
    )

    with pytest.raises(ActivationConfigError) as exc_info:
        resolve_agent_integration_switches(settings)

    assert "super-secret-api-key-value" not in str(exc_info.value)


@pytest.mark.parametrize("flag_field", _FLAG_FIELDS)
def test_env_var_alias_binds_to_settings_field(
    flag_field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_var in _FLAG_ENV_VARS.values():
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setenv(_FLAG_ENV_VARS[flag_field], "true")

    settings = Settings()

    assert getattr(settings, flag_field) is True
    for other_flag in _FLAG_ENV_VARS:
        if other_flag != flag_field:
            assert getattr(settings, other_flag) is False
