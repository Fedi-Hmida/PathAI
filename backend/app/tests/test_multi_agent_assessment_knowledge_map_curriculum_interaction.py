from __future__ import annotations

import pytest

from app.agents.llm.assessment import LLMAssessmentAgent
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.agents.services.activation.errors import ActivationConfigError
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
from app.llm.contracts import RawLLMResponse, StructuredOutputRequest
from app.llm.fake_client import FakeLLMClient
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.assessment import AssessmentAgentOutput, AssessmentScoreOutput
from app.schemas.enums import OrchestrationStatus
from app.schemas.knowledge_map import KnowledgeMapAgentOutput

_SENTINEL_EVIDENCE_CONCEPT = "sentinel_concept_from_assessment_rebuild29"
_SENTINEL_EVIDENCE_TEXT = "SENTINEL_EVIDENCE_TEXT_FROM_ASSESSMENT_REBUILD_29"
_SENTINEL_WEAK_CONCEPT = "sentinel_weak_concept_rebuild29"
_SENTINEL_KNOWLEDGE_MAP_LABEL = "SENTINEL_KNOWLEDGE_MAP_LABEL_REBUILD_29"


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _enable_all_three(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_ASSESSMENT_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")


def test_all_three_flags_resolve_to_llm_agents_with_distinct_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_all_three(monkeypatch)

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)
    bundle = context.agent_services

    assert isinstance(bundle.assessment.agent, LLMAssessmentAgent)
    assert isinstance(bundle.knowledge_map.agent, LLMKnowledgeMapAgent)
    assert isinstance(bundle.curriculum.agent, LLMCurriculumAgent)
    clients = {
        bundle.assessment.agent.client,
        bundle.knowledge_map.agent.client,
        bundle.curriculum.agent.client,
    }
    assert len(clients) == 3, "each agent must get its own client instance"


def test_knowledge_map_consumes_assessments_real_evidence_not_a_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_all_three(monkeypatch)

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)
    bundle = context.agent_services
    assessment_agent = bundle.assessment.agent
    knowledge_map_agent = bundle.knowledge_map.agent
    assert isinstance(assessment_agent, LLMAssessmentAgent)
    assert isinstance(knowledge_map_agent, LLMKnowledgeMapAgent)
    assessment_client = assessment_agent.client
    knowledge_map_client = knowledge_map_agent.client
    assert isinstance(assessment_client, FakeLLMClient)
    assert isinstance(knowledge_map_client, FakeLLMClient)

    assessment_client.payloads[AssessmentAgentOutput.__name__] = _sentinel_question_payload()
    assessment_client.payloads[AssessmentScoreOutput.__name__] = _sentinel_score_payload()
    knowledge_map_client.payloads[KnowledgeMapAgentOutput.__name__] = (
        _sentinel_knowledge_map_payload()
    )

    captured_prompts: list[str] = []
    original_generate = knowledge_map_client.generate

    async def _spy_generate(request: StructuredOutputRequest) -> RawLLMResponse:
        captured_prompts.append(request.prompt)
        return await original_generate(request)

    monkeypatch.setattr(knowledge_map_client, "generate", _spy_generate)

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert knowledge_map_client.call_count == 1
    # The real proof: the knowledge-map agent's own prompt embedded the
    # assessment agent's *real* scored evidence - not a fixture, not
    # demo.KNOWLEDGE_MAP - the sentinel concept/evidence this test seeded
    # into the assessment agent's fake client.
    assert any(_SENTINEL_EVIDENCE_CONCEPT in prompt for prompt in captured_prompts)
    assert any(_SENTINEL_EVIDENCE_TEXT in prompt for prompt in captured_prompts)


def test_curriculum_consumes_knowledge_maps_real_output_not_a_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_all_three(monkeypatch)

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)
    bundle = context.agent_services
    assessment_agent = bundle.assessment.agent
    knowledge_map_agent = bundle.knowledge_map.agent
    curriculum_agent = bundle.curriculum.agent
    assert isinstance(assessment_agent, LLMAssessmentAgent)
    assert isinstance(knowledge_map_agent, LLMKnowledgeMapAgent)
    assert isinstance(curriculum_agent, LLMCurriculumAgent)
    assessment_client = assessment_agent.client
    knowledge_map_client = knowledge_map_agent.client
    curriculum_client = curriculum_agent.client
    assert isinstance(assessment_client, FakeLLMClient)
    assert isinstance(knowledge_map_client, FakeLLMClient)
    assert isinstance(curriculum_client, FakeLLMClient)

    assessment_client.payloads[AssessmentAgentOutput.__name__] = _sentinel_question_payload()
    assessment_client.payloads[AssessmentScoreOutput.__name__] = _sentinel_score_payload()
    knowledge_map_client.payloads[KnowledgeMapAgentOutput.__name__] = (
        _sentinel_knowledge_map_payload()
    )

    captured_prompts: list[str] = []
    original_generate = curriculum_client.generate

    async def _spy_generate(request: StructuredOutputRequest) -> RawLLMResponse:
        captured_prompts.append(request.prompt)
        return await original_generate(request)

    monkeypatch.setattr(curriculum_client, "generate", _spy_generate)

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.COMPLETED
    # >=1, not ==1: the deterministic critic (unchanged here) may trigger the
    # bounded revision loop against the sentinel curriculum content, which
    # would call curriculum a second time - irrelevant to what this test
    # actually proves (the handoff), so it isn't asserted away.
    assert curriculum_client.call_count >= 1
    # The real proof: the curriculum agent's own prompt embedded the
    # knowledge-map agent's *real* concept label - the sentinel this test
    # seeded into the knowledge-map agent's fake client, not demo.CURRICULUM
    # and not a re-derived fixture.
    assert any(_SENTINEL_KNOWLEDGE_MAP_LABEL in prompt for prompt in captured_prompts)


def test_non_allowlisted_combination_including_a_third_flag_still_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_ASSESSMENT_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()

    with pytest.raises(ActivationConfigError) as exc_info:
        OrchestrationContext.from_container(container)

    message = str(exc_info.value)
    assert "assessment_agent_mode" in message
    assert "knowledge_map_agent_mode" in message
    assert "critic_agent_mode" in message


def _sentinel_question_payload() -> dict[str, object]:
    return {
        "question": {
            "question_id": "question_sentinel_rebuild29",
            "question_type": "self_rating",
            "prompt": "Sentinel diagnostic question for Rebuild-29 interaction test.",
            "options": [],
            "target_concepts": [_SENTINEL_EVIDENCE_CONCEPT],
            "difficulty": "beginner",
        },
        "rationale": "Sentinel rationale for Rebuild-29 interaction test.",
        "estimated_information_gain": 0.5,
    }


def _sentinel_score_payload() -> dict[str, object]:
    return {
        "answer_id": None,
        "score": 0.4,
        "concept_scores": [
            {
                "concept_id": _SENTINEL_EVIDENCE_CONCEPT,
                "score_delta": 0.4,
                "evidence": _SENTINEL_EVIDENCE_TEXT,
            }
        ],
        "feedback": "Sentinel feedback for Rebuild-29 interaction test.",
        "confidence_after_answer": 0.5,
    }


def _sentinel_knowledge_map_payload() -> dict[str, object]:
    return {
        "concepts": [
            {
                "concept_id": _SENTINEL_WEAK_CONCEPT,
                "label": _SENTINEL_KNOWLEDGE_MAP_LABEL,
                "mastery_score": 0.3,
                "classification": "weak",
            }
        ],
        "strong_concepts": [],
        "developing_concepts": [],
        "weak_concepts": [_SENTINEL_WEAK_CONCEPT],
        "missing_concepts": [],
        "confidence": 0.6,
        "summary": "Sentinel knowledge map summary for Rebuild-29 interaction test.",
    }
