from __future__ import annotations

import pytest

from app.agents.deterministic.knowledge_map import build_knowledge_map_output
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.agents.llm.observer_selection import build_run_scoped_observer
from app.agents.mock import MockKnowledgeMapAgent
from app.agents.services.activation import factory as factory_module
from app.agents.services.activation.factory import build_injected_agents
from app.agents.services.bundle import AgentIntegrationSwitches, CurriculumAgentMode
from app.core.settings import Settings
from app.fixtures import canonical_demo as demo
from app.llm import FakeLLMClient, FakeLLMScenario, LLMRetryPolicy
from app.llm.observability.budget import RunBudget, RunScopedBudgetObserver
from app.llm.observability.events import LLMReliabilityEvent, LLMReliabilityEventType
from app.llm.observability.observer import LLMReliabilityObserver, NullObserver
from app.llm.observability.sinks import CountingObserver
from app.schemas.knowledge_map import KnowledgeMapAgentInput

_NO_DELAY_SINGLE_ATTEMPT = LLMRetryPolicy(max_attempts=1, backoff_seconds=0)


def _exhausted_observer(
    inner: LLMReliabilityObserver | None = None,
) -> RunScopedBudgetObserver:
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=1), inner=inner)
    observer.record(
        LLMReliabilityEvent(
            event_type=LLMReliabilityEventType.ATTEMPT_STARTED,
            schema_name="KnowledgeMapAgentOutput",
            attempt=1,
            max_attempts=1,
        ),
    )
    assert observer.exhausted() is True
    return observer


def test_exhausted_budget_skips_the_llm_call_and_falls_back() -> None:
    fake_client = FakeLLMClient(scenario=FakeLLMScenario.VALID_JSON)
    agent = LLMKnowledgeMapAgent(
        client=fake_client,
        fallback_agent=MockKnowledgeMapAgent(),
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
        observer=_exhausted_observer(),
    )
    payload = _knowledge_map_input()

    output = agent.build_knowledge_map(payload)

    assert output == build_knowledge_map_output(payload)
    assert fake_client.call_count == 0


def test_exhaustion_fallback_event_carries_the_run_budget_error_code() -> None:
    inner = CountingObserver()
    agent = LLMKnowledgeMapAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.VALID_JSON),
        fallback_agent=MockKnowledgeMapAgent(),
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
        observer=_exhausted_observer(inner=inner),
    )

    agent.build_knowledge_map(_knowledge_map_input())

    summary = inner.safe_summary()
    counts_by_error_code = summary["counts_by_error_code"]
    assert isinstance(counts_by_error_code, dict)
    assert counts_by_error_code.get("llm_run_budget_exhausted") == 1


def test_non_exhausted_budget_does_not_interfere_with_a_normal_call() -> None:
    fake_client = FakeLLMClient(scenario=FakeLLMScenario.VALID_JSON)
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=100))
    agent = LLMKnowledgeMapAgent(
        client=fake_client,
        fallback_agent=MockKnowledgeMapAgent(),
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
        observer=observer,
    )

    output = agent.build_knowledge_map(_knowledge_map_input())

    assert output == build_knowledge_map_output(_knowledge_map_input())
    assert fake_client.call_count == 1
    assert observer.exhausted() is False


def test_plain_observers_are_never_treated_as_exhausted() -> None:
    for plain_observer in (CountingObserver(), NullObserver()):
        fake_client = FakeLLMClient(scenario=FakeLLMScenario.VALID_JSON)
        agent = LLMKnowledgeMapAgent(
            client=fake_client,
            fallback_agent=MockKnowledgeMapAgent(),
            fallback_on_error=True,
            retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
            observer=plain_observer,
        )

        output = agent.build_knowledge_map(_knowledge_map_input())

        assert output == build_knowledge_map_output(_knowledge_map_input())
        assert fake_client.call_count == 1


def test_build_injected_agents_constructs_the_observer_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count = 0
    real_builder = factory_module.build_run_scoped_observer

    def _counting_builder(budget: RunBudget | None = None) -> LLMReliabilityObserver:
        nonlocal call_count
        call_count += 1
        return real_builder(budget)

    monkeypatch.setattr(factory_module, "build_run_scoped_observer", _counting_builder)

    switches = AgentIntegrationSwitches(curriculum_agent_mode=CurriculumAgentMode.LLM)
    settings = Settings(llm_provider="fake")

    build_injected_agents(switches, settings)

    assert call_count == 1


def test_build_injected_agents_shares_one_observer_instance_across_agent_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = build_run_scoped_observer()
    monkeypatch.setattr(
        factory_module,
        "build_run_scoped_observer",
        lambda budget=None: sentinel,
    )

    switches = AgentIntegrationSwitches(curriculum_agent_mode=CurriculumAgentMode.LLM)
    settings = Settings(llm_provider="fake")

    injected = build_injected_agents(switches, settings)

    assert isinstance(injected.curriculum, LLMCurriculumAgent)
    assert injected.curriculum.observer is sentinel
    # Fail-loud is the default: no silent deterministic fallback is wired in.
    assert injected.curriculum.fallback_agent is None


def _knowledge_map_input() -> KnowledgeMapAgentInput:
    return KnowledgeMapAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        assessment_answers=demo.ASSESSMENT_ANSWERS,
        concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
    )
