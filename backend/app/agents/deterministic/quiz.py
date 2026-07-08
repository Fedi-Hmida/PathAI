from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.schemas.enums import (
    DifficultyLevel,
    QuestionType,
    ScoringPolicyType,
)
from app.schemas.quiz import (
    ConceptQuizScore,
    QuizAgentInput,
    QuizAgentOutput,
    QuizAnswerSubmission,
    QuizAttemptDTO,
    QuizQuestionDTO,
    QuizScoreOutput,
    QuizScoringPolicy,
)

LOW_SCORE_THRESHOLD = 0.65


@dataclass(frozen=True, slots=True)
class QuestionBlueprint:
    question_id: str
    question_type: QuestionType
    prompt: str
    concept_ids: tuple[str, ...]
    correct_answer: str
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    points: float = 1.0
    options: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    explanation: str | None = None


QUESTION_BANK: dict[str, QuestionBlueprint] = {
    "retrieval_evaluation": QuestionBlueprint(
        question_id="question_quiz_recall_k",
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt="What does recall at k measure?",
        concept_ids=("retrieval_evaluation",),
        options=(
            "Relevant items appearing in the top k retrieved results",
            "Final answer fluency",
            "Number of generated tokens",
            "Client response speed",
        ),
        correct_answer="Relevant items appearing in the top k retrieved results",
        keywords=("relevant", "top", "retrieved"),
        explanation="Recall at k measures whether relevant items are retrieved within top k.",
    ),
    "vector_search": QuestionBlueprint(
        question_id="question_quiz_vector_search",
        question_type=QuestionType.SHORT_ANSWER,
        prompt="Why do embeddings matter for vector search?",
        concept_ids=("embeddings", "vector_search"),
        correct_answer="They place similar meanings near each other for retrieval.",
        keywords=("similar", "meaning", "retrieval"),
    ),
    "chunking": QuestionBlueprint(
        question_id="question_quiz_chunking",
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt="What is a common chunking tradeoff?",
        concept_ids=("chunking",),
        options=(
            "Granularity versus context completeness",
            "Authentication versus authorization",
            "Color palette versus layout",
            "Deployment versus billing",
        ),
        correct_answer="Granularity versus context completeness",
        keywords=("granularity", "context"),
    ),
    "embeddings": QuestionBlueprint(
        question_id="question_quiz_embeddings",
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt="What is the main role of embeddings in a RAG system?",
        concept_ids=("embeddings", "vector_search"),
        options=(
            "Represent text so semantic similarity can be compared",
            "Replace retrieval evaluation",
            "Render the user interface",
            "Store billing state",
        ),
        correct_answer="Represent text so semantic similarity can be compared",
        keywords=("semantic", "similarity"),
    ),
    "reranking": QuestionBlueprint(
        question_id="question_quiz_reranking",
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt="Why add a reranking step after first-stage retrieval?",
        concept_ids=("reranking", "retrieval_evaluation"),
        options=(
            "To reorder retrieved passages by relevance before generation",
            "To skip chunking entirely",
            "To hide low-confidence answers",
            "To replace vector indexing",
        ),
        correct_answer="To reorder retrieved passages by relevance before generation",
        keywords=("reorder", "relevance"),
    ),
    "production_rag_failures": QuestionBlueprint(
        question_id="question_quiz_production_failures",
        question_type=QuestionType.SHORT_ANSWER,
        prompt="Name one production failure mode that can make a RAG answer unreliable.",
        concept_ids=("production_rag_failures", "hallucination_reduction"),
        correct_answer="Stale or irrelevant retrieved context can cause unsupported answers.",
        difficulty=DifficultyLevel.ADVANCED,
        keywords=("stale", "irrelevant", "unsupported"),
    ),
}


def build_quiz_output(payload: QuizAgentInput) -> QuizAgentOutput:
    concepts = _prioritized_concepts(payload)
    questions = [_question_for_concept(concept) for concept in concepts]
    return QuizAgentOutput(
        quiz_title=_quiz_title(payload),
        questions=questions[: payload.question_count],
        scoring_policy=QuizScoringPolicy(
            type=ScoringPolicyType.EXACT_MATCH,
            partial_credit=False,
        ),
    )


def seeded_answers_for_questions(
    questions: list[QuizQuestionDTO],
) -> list[QuizAnswerSubmission]:
    answers: list[QuizAnswerSubmission] = []
    for question in questions:
        if question.question_id == "question_quiz_chunking":
            answers.append(
                QuizAnswerSubmission(
                    question_id=question.question_id,
                    selected_options=["Granularity versus context completeness"],
                ),
            )
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            answers.append(
                QuizAnswerSubmission(
                    question_id=question.question_id,
                    selected_options=[_first_wrong_option(question)],
                ),
            )
        else:
            answers.append(
                QuizAnswerSubmission(
                    question_id=question.question_id,
                    answer_text=_seeded_short_answer(question),
                ),
            )
    return answers


def score_quiz_attempt(attempt: QuizAttemptDTO) -> QuizScoreOutput:
    correct_count = 0
    concept_totals: dict[str, int] = {}
    concept_correct: dict[str, int] = {}
    for answer in attempt.answers:
        blueprint = _blueprint_for_question(answer.question_id)
        if blueprint is None:
            continue
        is_correct = _is_correct(answer, blueprint)
        correct_count += int(is_correct)
        for concept_id in blueprint.concept_ids:
            concept_totals[concept_id] = concept_totals.get(concept_id, 0) + 1
            concept_correct[concept_id] = concept_correct.get(concept_id, 0) + int(
                is_correct,
            )

    total_questions = max(1, len(attempt.answers))
    concept_scores = [
        ConceptQuizScore(
            concept_id=concept_id,
            score=round(concept_correct.get(concept_id, 0) / total, 2),
            correct_count=concept_correct.get(concept_id, 0),
            total_questions=total,
        )
        for concept_id, total in concept_totals.items()
    ]
    weak_concepts = [
        concept_score.concept_id
        for concept_score in concept_scores
        if concept_score.score < LOW_SCORE_THRESHOLD
    ]
    total_score = round(correct_count / total_questions, 2)
    return QuizScoreOutput(
        total_score=total_score,
        correct_count=correct_count,
        total_questions=total_questions,
        concept_scores=concept_scores or [_fallback_concept_score()],
        weak_concepts=weak_concepts,
        feedback=_feedback(total_score, weak_concepts),
    )


def _question_for_concept(concept: str) -> QuizQuestionDTO:
    blueprint = QUESTION_BANK.get(concept) or QUESTION_BANK["retrieval_evaluation"]
    return QuizQuestionDTO(
        question_id=blueprint.question_id,
        question_type=blueprint.question_type,
        prompt=blueprint.prompt,
        options=list(blueprint.options),
        concept_ids=list(blueprint.concept_ids),
        difficulty=blueprint.difficulty,
        correct_answer=blueprint.correct_answer,
        points=blueprint.points,
        explanation=blueprint.explanation,
    )


def _prioritized_concepts(payload: QuizAgentInput) -> list[str]:
    values: list[str] = []
    values.extend(payload.target_concepts)
    for topic in payload.curriculum_topics:
        values.extend(topic.concept_ids)
    concepts = [concept for concept in _unique(values) if concept in QUESTION_BANK]
    return concepts or ["retrieval_evaluation"]


def _quiz_title(payload: QuizAgentInput) -> str:
    if "rag" in payload.goal_text.lower():
        return "RAG Feedback Checkpoint"
    return "Deterministic Feedback Checkpoint"


def _first_wrong_option(question: QuizQuestionDTO) -> str:
    for option in question.options:
        if option != question.correct_answer:
            return option
    return "Needs review"


def _seeded_short_answer(question: QuizQuestionDTO) -> str:
    if "vector" in question.question_id:
        return "They make storage faster."
    if "production" in question.question_id:
        return "The app might be slow."
    return "I am not sure yet."


def _blueprint_for_question(question_id: str) -> QuestionBlueprint | None:
    return next(
        (
            blueprint
            for blueprint in QUESTION_BANK.values()
            if blueprint.question_id == question_id
        ),
        None,
    )


def _is_correct(answer: QuizAnswerSubmission, blueprint: QuestionBlueprint) -> bool:
    if blueprint.question_type == QuestionType.MULTIPLE_CHOICE:
        return answer.selected_options == [blueprint.correct_answer]
    text = (answer.answer_text or "").strip().lower()
    return sum(keyword in text for keyword in blueprint.keywords) >= 2


def _feedback(total_score: float, weak_concepts: list[str]) -> str:
    if total_score >= LOW_SCORE_THRESHOLD:
        return "Checkpoint passed. Continue with the next planned topic."
    if weak_concepts:
        concepts = ", ".join(concept.replace("_", " ") for concept in weak_concepts)
        return f"Review these concepts before continuing: {concepts}."
    return "Review the checkpoint concepts before continuing."


def _fallback_concept_score() -> ConceptQuizScore:
    return ConceptQuizScore(
        concept_id="retrieval_evaluation",
        score=0.0,
        correct_count=0,
        total_questions=1,
    )


def _unique(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized and normalized not in unique_values:
            unique_values.append(normalized)
    return unique_values
