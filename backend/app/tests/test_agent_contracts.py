from __future__ import annotations

from app.agents.contracts import (
    AdapterAgent,
    AssessorAgent,
    CriticAgent,
    CurriculumAgent,
    EvaluationAgent,
    KnowledgeMapAgent,
    ProgressAgent,
    QuizAgent,
    ResourceAgent,
)
from app.agents.mock import (
    MockAdapterAgent,
    MockAssessorAgent,
    MockCriticAgent,
    MockCurriculumAgent,
    MockEvaluationAgent,
    MockKnowledgeMapAgent,
    MockProgressAgent,
    MockQuizAgent,
    MockResourceAgent,
)


def test_agent_contract_modules_import_cleanly() -> None:
    assert AssessorAgent.__name__ == "AssessorAgent"
    assert KnowledgeMapAgent.__name__ == "KnowledgeMapAgent"
    assert CurriculumAgent.__name__ == "CurriculumAgent"
    assert ResourceAgent.__name__ == "ResourceAgent"
    assert CriticAgent.__name__ == "CriticAgent"
    assert ProgressAgent.__name__ == "ProgressAgent"
    assert QuizAgent.__name__ == "QuizAgent"
    assert AdapterAgent.__name__ == "AdapterAgent"
    assert EvaluationAgent.__name__ == "EvaluationAgent"


def test_mock_agents_expose_expected_contract_methods() -> None:
    assert callable(MockAssessorAgent().generate_question)
    assert callable(MockAssessorAgent().score_answer)
    assert callable(MockKnowledgeMapAgent().build_knowledge_map)
    assert callable(MockCurriculumAgent().build_curriculum)
    assert callable(MockResourceAgent().attach_resources)
    assert callable(MockCriticAgent().review_curriculum)
    assert callable(MockProgressAgent().build_progress_state)
    assert callable(MockQuizAgent().build_quiz)
    assert callable(MockQuizAgent().score_attempt)
    assert callable(MockAdapterAgent().plan_adaptation)
    assert callable(MockEvaluationAgent().evaluate_run)
