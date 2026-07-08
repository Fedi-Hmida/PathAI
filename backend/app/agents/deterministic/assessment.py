from __future__ import annotations

from collections.abc import Iterable

from app.fixtures import canonical_demo as demo
from app.schemas.assessment import (
    AssessmentAgentInput,
    AssessmentAgentOutput,
    AssessmentAnswerDTO,
    AssessmentQuestionDTO,
    AssessmentScoreOutput,
    AssessmentSessionDTO,
    ConceptEvidence,
    ConceptEvidenceUpdate,
)
from app.schemas.enums import AssessmentStatus, DifficultyLevel
from app.schemas.goal import LearnerProfile, LearningGoalDTO

CANONICAL_DIAGNOSTIC_CONCEPTS: tuple[str, ...] = (
    "rag_fundamentals",
    "retrieval_evaluation",
    "vector_search",
    "chunking",
    "embeddings",
    "production_rag_failures",
)

_QUESTION_GAIN: dict[DifficultyLevel, float] = {
    DifficultyLevel.BEGINNER: 0.62,
    DifficultyLevel.INTERMEDIATE: 0.74,
    DifficultyLevel.ADVANCED: 0.82,
}

_SEEDED_ANSWERS: dict[str, dict[str, object]] = {
    "question_assess_retriever_role": {
        "answer_id": "answer_demo_retriever_role",
        "selected_options": ["Retriever"],
    },
    "question_assess_recall_at_k": {
        "answer_id": "answer_demo_recall_at_k",
        "answer_text": "It checks if answers are good.",
    },
    "question_assess_chunking": {
        "answer_id": "answer_demo_chunking",
        "selected_options": ["It changes context granularity"],
    },
    "question_assess_embeddings": {
        "answer_id": "answer_demo_embeddings",
        "answer_text": "2",
    },
    "question_assess_failures": {
        "answer_id": "answer_demo_production_failures",
        "answer_text": "I am not sure yet.",
    },
}

_SCORE_BLUEPRINTS: dict[str, tuple[float, tuple[ConceptEvidenceUpdate, ...], str]] = {
    "question_assess_retriever_role": (
        1.0,
        (
            ConceptEvidenceUpdate(
                concept_id="rag_fundamentals",
                score_delta=0.32,
                evidence="Correctly identified retrieval responsibility.",
            ),
            ConceptEvidenceUpdate(
                concept_id="retrieval",
                score_delta=0.22,
                evidence="Recognized the retrieval component in a RAG pipeline.",
            ),
        ),
        "Strong understanding of the retriever role.",
    ),
    "question_assess_recall_at_k": (
        0.25,
        (
            ConceptEvidenceUpdate(
                concept_id="retrieval_evaluation",
                score_delta=-0.30,
                evidence="Confused retrieval quality with final answer quality.",
            ),
        ),
        "Needs targeted practice with retrieval metrics.",
    ),
    "question_assess_chunking": (
        0.62,
        (
            ConceptEvidenceUpdate(
                concept_id="chunking",
                score_delta=0.08,
                evidence="Recognized that chunk size changes retrieval granularity.",
            ),
            ConceptEvidenceUpdate(
                concept_id="retrieval",
                score_delta=0.05,
                evidence="Connected chunking choices to retrieval quality.",
            ),
        ),
        "Developing understanding of chunking tradeoffs.",
    ),
    "question_assess_embeddings": (
        0.35,
        (
            ConceptEvidenceUpdate(
                concept_id="embeddings",
                score_delta=-0.12,
                evidence="Self-rated low confidence explaining semantic embeddings.",
            ),
            ConceptEvidenceUpdate(
                concept_id="vector_search",
                score_delta=-0.18,
                evidence="Needs support connecting embeddings to vector search behavior.",
            ),
        ),
        "Review embeddings and vector similarity before project integration.",
    ),
    "question_assess_failures": (
        0.18,
        (
            ConceptEvidenceUpdate(
                concept_id="production_rag_failures",
                score_delta=-0.35,
                evidence="Could not name a concrete production RAG failure mode.",
            ),
            ConceptEvidenceUpdate(
                concept_id="hallucination_reduction",
                score_delta=-0.15,
                evidence="Needs clearer grounding and failure-mode vocabulary.",
            ),
        ),
        "Add focused practice on production RAG failure modes.",
    ),
}


def diagnostic_focus_for_goal(goal_text: str, learner_profile: LearnerProfile) -> list[str]:
    normalized = f"{goal_text} {' '.join(learner_profile.weak_areas)}".lower()
    concepts: list[str] = []
    if "rag" in normalized or "retrieval" in normalized:
        concepts.extend(CANONICAL_DIAGNOSTIC_CONCEPTS)
    concepts.extend(_safe_concepts(learner_profile.weak_areas))
    concepts.extend(_safe_concepts(learner_profile.strengths))
    return _unique(concepts) or list(CANONICAL_DIAGNOSTIC_CONCEPTS)


def build_question_output(payload: AssessmentAgentInput) -> AssessmentAgentOutput:
    answered_question_ids = {
        answer.question.question_id
        for answer in payload.prior_answers
    }
    question = _select_question(payload.target_concepts, answered_question_ids)
    return AssessmentAgentOutput(
        question=question,
        rationale=_question_rationale(question),
        estimated_information_gain=_QUESTION_GAIN[question.difficulty],
    )


def seeded_answer_for_question(
    *,
    goal: LearningGoalDTO,
    question: AssessmentQuestionDTO,
) -> AssessmentAnswerDTO:
    seed = _SEEDED_ANSWERS.get(question.question_id, {})
    answer_id = str(
        seed.get(
            "answer_id",
            f"answer_demo_{question.question_id.removeprefix('question_')}",
        ),
    )
    return AssessmentAnswerDTO(
        answer_id=answer_id,
        assessment_session_id=demo.ASSESSMENT_ID,
        goal_id=goal.goal_id,
        question=question,
        answer_text=_optional_str(seed.get("answer_text")),
        selected_options=_optional_str_list(seed.get("selected_options")),
        score=0.0,
        concept_scores=[],
        feedback=None,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def score_answer(answer: AssessmentAnswerDTO) -> AssessmentScoreOutput:
    score, concept_scores, feedback = _SCORE_BLUEPRINTS.get(
        answer.question.question_id,
        _fallback_score(answer),
    )
    return AssessmentScoreOutput(
        answer_id=answer.answer_id,
        score=score,
        concept_scores=list(concept_scores),
        feedback=feedback,
        confidence_after_answer=_confidence_after_answer(answer.question.question_id),
    )


def build_scored_answer(
    answer: AssessmentAnswerDTO,
    score_output: AssessmentScoreOutput,
) -> AssessmentAnswerDTO:
    return answer.model_copy(
        update={
            "score": score_output.score,
            "concept_scores": score_output.concept_scores,
            "feedback": score_output.feedback,
        },
        deep=True,
    )


def build_completed_session(
    *,
    goal: LearningGoalDTO,
    answers: list[AssessmentAnswerDTO],
) -> AssessmentSessionDTO:
    evidence = concept_evidence_from_answers(answers, goal.learner_profile)
    confidence = assessment_confidence(answer_count=len(answers), evidence_count=len(evidence))
    return AssessmentSessionDTO(
        assessment_session_id=demo.ASSESSMENT_ID,
        goal_id=goal.goal_id,
        run_id=goal.run_id,
        status=AssessmentStatus.COMPLETED,
        question_count=len(answers),
        confidence=confidence,
        concept_evidence=evidence,
        started_at=demo.NOW,
        completed_at=demo.NOW,
        termination_reason=(
            "confidence_target_met"
            if confidence >= 0.75
            else "deterministic_question_limit_reached"
        ),
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def concept_evidence_from_answers(
    answers: list[AssessmentAnswerDTO],
    learner_profile: LearnerProfile,
) -> list[ConceptEvidence]:
    concept_scores: dict[str, list[float]] = {}
    concept_evidence: dict[str, list[str]] = {}
    for answer in answers:
        for update in answer.concept_scores:
            concept_scores.setdefault(update.concept_id, []).append(answer.score)
            concept_evidence.setdefault(update.concept_id, []).append(update.evidence)

    for strength in _safe_concepts(learner_profile.strengths):
        concept_scores.setdefault(strength, []).append(0.78)
        concept_evidence.setdefault(strength, []).append(
            "Learner profile lists this as a prior strength.",
        )

    ordered_concepts = _ordered_evidence_concepts(concept_scores)
    return [
        ConceptEvidence(
            concept_id=concept_id,
            score=round(sum(scores) / len(scores), 2),
            evidence=concept_evidence.get(concept_id, []),
        )
        for concept_id in ordered_concepts
        if (scores := concept_scores[concept_id])
    ]


def assessment_confidence(*, answer_count: int, evidence_count: int) -> float:
    confidence = 0.38 + (0.06 * answer_count) + (0.02 * evidence_count)
    return round(min(0.88, confidence), 2)


def _select_question(
    target_concepts: list[str],
    answered_question_ids: set[str],
) -> AssessmentQuestionDTO:
    target_set = set(target_concepts)
    for question in demo.ASSESSMENT_QUESTIONS:
        if question.question_id in answered_question_ids:
            continue
        if target_set.intersection(question.target_concepts):
            return question.model_copy(deep=True)
    for question in demo.ASSESSMENT_QUESTIONS:
        if question.question_id not in answered_question_ids:
            return question.model_copy(deep=True)
    return demo.ASSESSMENT_QUESTIONS[-1].model_copy(deep=True)


def _question_rationale(question: AssessmentQuestionDTO) -> str:
    concepts = ", ".join(question.target_concepts)
    return f"Checks deterministic diagnostic evidence for: {concepts}."


def _fallback_score(
    answer: AssessmentAnswerDTO,
) -> tuple[float, tuple[ConceptEvidenceUpdate, ...], str]:
    concept_scores = tuple(
        ConceptEvidenceUpdate(
            concept_id=concept_id,
            score_delta=0.0,
            evidence="Deterministic fallback evidence for an unrecognized question.",
        )
        for concept_id in answer.question.target_concepts
    )
    return 0.5, concept_scores, "Fallback deterministic assessment score."


def _confidence_after_answer(question_id: str) -> float:
    order = [question.question_id for question in demo.ASSESSMENT_QUESTIONS]
    try:
        index = order.index(question_id) + 1
    except ValueError:
        index = 1
    return assessment_confidence(answer_count=index, evidence_count=min(index + 2, 8))


def _ordered_evidence_concepts(concept_scores: dict[str, list[float]]) -> list[str]:
    preferred = [
        "rag_fundamentals",
        "retrieval",
        "retrieval_evaluation",
        "chunking",
        "embeddings",
        "vector_search",
        "production_rag_failures",
        "hallucination_reduction",
        "api_basics",
        "python_basics",
        "machine_learning_basics",
    ]
    return [
        *[concept for concept in preferred if concept in concept_scores],
        *sorted(concept for concept in concept_scores if concept not in preferred),
    ]


def _safe_concepts(values: Iterable[str]) -> list[str]:
    concepts = []
    for value in values:
        concept = value.strip().lower().replace("-", "_").replace(" ", "_")
        if concept and concept[0].isalpha():
            concepts.append(concept)
    return concepts


def _unique(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return unique_values


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
