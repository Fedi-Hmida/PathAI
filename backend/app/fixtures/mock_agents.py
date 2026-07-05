from __future__ import annotations

from app.fixtures.canonical_demo import (
    ADAPTATION_CHANGE,
    ADAPTATION_EVENT,
    ASSESSMENT_ANSWERS,
    ASSESSMENT_QUESTIONS,
    CANONICAL_GOAL_TEXT,
    CRITIC_REVIEW,
    CURRICULUM,
    EVALUATION_REPORT,
    KNOWLEDGE_MAP,
    QUIZ,
    QUIZ_ATTEMPT,
    RESOURCE_ATTACHMENTS,
)
from app.schemas.adaptation import AdaptationAgentOutput
from app.schemas.assessment import (
    AssessmentAgentOutput,
    AssessmentScoreOutput,
    ConceptEvidenceUpdate,
)
from app.schemas.base import BaseSchema
from app.schemas.critic import CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentOutput, CurriculumTopicDTO
from app.schemas.enums import DifficultyLevel
from app.schemas.evaluation import EvaluationAgentOutput
from app.schemas.knowledge_map import KnowledgeMapAgentOutput
from app.schemas.quiz import QuizAgentOutput, QuizScoreOutput
from app.schemas.resource import ResourceAgentOutput, ResourceCoverageSummary

ASSESSMENT_AGENT_OUTPUT = AssessmentAgentOutput(
    question=ASSESSMENT_QUESTIONS[0],
    rationale="The question checks whether the learner understands retrieval in RAG.",
    estimated_information_gain=0.72,
)

ASSESSMENT_SCORE_OUTPUT = AssessmentScoreOutput(
    answer_id=ASSESSMENT_ANSWERS[1].answer_id,
    score=0.25,
    concept_scores=[
        ConceptEvidenceUpdate(
            concept_id="retrieval_evaluation",
            score_delta=-0.3,
            evidence="The answer confused retrieval quality with final answer quality.",
        )
    ],
    feedback="Review recall and precision before continuing.",
    confidence_after_answer=0.78,
)

KNOWLEDGE_MAP_AGENT_OUTPUT = KnowledgeMapAgentOutput(
    concepts=KNOWLEDGE_MAP.concepts,
    strong_concepts=KNOWLEDGE_MAP.strong_concepts,
    developing_concepts=KNOWLEDGE_MAP.developing_concepts,
    weak_concepts=KNOWLEDGE_MAP.weak_concepts,
    missing_concepts=KNOWLEDGE_MAP.missing_concepts,
    confidence=KNOWLEDGE_MAP.confidence,
    summary=KNOWLEDGE_MAP.summary,
)

CURRICULUM_AGENT_OUTPUT = CurriculumAgentOutput(
    title=CURRICULUM.title,
    duration_weeks=CURRICULUM.duration_weeks,
    weeks=CURRICULUM.weeks,
    assumptions=CURRICULUM.assumptions,
    target_outcomes=CURRICULUM.target_outcomes,
)

RESOURCE_AGENT_OUTPUT = ResourceAgentOutput(
    attachments=RESOURCE_ATTACHMENTS,
    coverage_summary=ResourceCoverageSummary(
        topics_with_resources=2,
        topics_without_resources=4,
        average_relevance=0.93,
        resource_type_diversity=0.67,
    ),
    warnings=["Fixture corpus is intentionally small for schema validation."],
)

CRITIC_AGENT_OUTPUT = CriticAgentOutput(
    overall_score=CRITIC_REVIEW.overall_score,
    pass_status=CRITIC_REVIEW.pass_status,
    dimension_scores=CRITIC_REVIEW.dimension_scores,
    strengths=CRITIC_REVIEW.strengths,
    issues=CRITIC_REVIEW.issues,
    revision_recommendations=CRITIC_REVIEW.revision_recommendations,
)

QUIZ_AGENT_OUTPUT = QuizAgentOutput(
    quiz_title=QUIZ.title,
    questions=QUIZ.questions,
    scoring_policy=QUIZ.scoring_policy,
)

QUIZ_SCORE_OUTPUT = QuizScoreOutput(
    total_score=QUIZ_ATTEMPT.total_score,
    correct_count=QUIZ_ATTEMPT.correct_count,
    total_questions=QUIZ_ATTEMPT.total_questions,
    concept_scores=QUIZ_ATTEMPT.concept_scores,
    weak_concepts=QUIZ_ATTEMPT.weak_concepts,
    feedback=QUIZ_ATTEMPT.feedback or "Review weak concepts.",
)

ADDED_PRACTICE_TOPIC = CurriculumTopicDTO(
    topic_id="topic_retrieval_metrics_practice",
    title="Extra retrieval metrics practice",
    description="Work through recall and precision examples before returning to integration.",
    concept_ids=["retrieval_evaluation"],
    difficulty=DifficultyLevel.INTERMEDIATE,
    estimated_hours=1.5,
    learning_outcomes=["Calculate recall at k and precision at k for toy examples."],
    sequence_order=5,
    adaptation_origin=ADAPTATION_EVENT.adaptation_event_id,
)

ADAPTATION_AGENT_OUTPUT = AdaptationAgentOutput(
    trigger_reason=ADAPTATION_EVENT.trigger_type.value,
    before_summary=ADAPTATION_EVENT.before_summary,
    after_summary=ADAPTATION_EVENT.after_summary,
    changes=[ADAPTATION_CHANGE],
    added_practice_topics=[ADDED_PRACTICE_TOPIC],
    removed_or_deferred_topics=[],
    expected_benefit="The learner should understand retrieval metrics before project integration.",
)

EVALUATION_AGENT_OUTPUT = EvaluationAgentOutput(
    metric_scores=EVALUATION_REPORT.metric_scores,
    weighted_score=EVALUATION_REPORT.overall_score,
    pass_status=EVALUATION_REPORT.pass_status,
    warnings=EVALUATION_REPORT.warnings,
    recommendations=EVALUATION_REPORT.recommendations,
)

MOCK_AGENT_OUTPUTS: dict[str, BaseSchema] = {
    "assessment": ASSESSMENT_AGENT_OUTPUT,
    "assessment_score": ASSESSMENT_SCORE_OUTPUT,
    "knowledge_map": KNOWLEDGE_MAP_AGENT_OUTPUT,
    "curriculum": CURRICULUM_AGENT_OUTPUT,
    "resource": RESOURCE_AGENT_OUTPUT,
    "critic": CRITIC_AGENT_OUTPUT,
    "quiz": QUIZ_AGENT_OUTPUT,
    "quiz_score": QUIZ_SCORE_OUTPUT,
    "adaptation": ADAPTATION_AGENT_OUTPUT,
    "evaluation": EVALUATION_AGENT_OUTPUT,
}

MOCK_AGENT_GOAL_TEXT = CANONICAL_GOAL_TEXT
