from __future__ import annotations

from collections.abc import Iterable

from app.schemas.curriculum import CurriculumTopicDTO
from app.schemas.enums import QuestionType, ScoringPolicyType
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


def build_quiz_output(payload: QuizAgentInput) -> QuizAgentOutput:
    topic_by_concept = _topic_by_concept(payload.curriculum_topics)
    concepts = _prioritized_concepts(payload, topic_by_concept)
    questions = [
        _question_for_concept(concept, topic_by_concept[concept], payload.curriculum_topics)
        for concept in concepts
    ]
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
    for index, question in enumerate(questions):
        selected = (
            [question.correct_answer] if index == 0 else [_first_wrong_option(question)]
        )
        answers.append(
            QuizAnswerSubmission(question_id=question.question_id, selected_options=selected),
        )
    return answers


def score_quiz_attempt(
    attempt: QuizAttemptDTO,
    questions: list[QuizQuestionDTO],
) -> QuizScoreOutput:
    questions_by_id = {question.question_id: question for question in questions}
    correct_count = 0
    concept_totals: dict[str, int] = {}
    concept_correct: dict[str, int] = {}
    for answer in attempt.answers:
        question = questions_by_id.get(answer.question_id)
        if question is None:
            continue
        is_correct = _is_correct(answer, question)
        correct_count += int(is_correct)
        for concept_id in question.concept_ids:
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
        concept_scores=concept_scores or [_fallback_concept_score(questions)],
        weak_concepts=weak_concepts,
        feedback=_feedback(total_score, weak_concepts),
    )


def _topic_by_concept(
    topics: Iterable[CurriculumTopicDTO],
) -> dict[str, CurriculumTopicDTO]:
    topic_by_concept: dict[str, CurriculumTopicDTO] = {}
    for topic in topics:
        for concept_id in topic.concept_ids:
            topic_by_concept.setdefault(concept_id, topic)
    return topic_by_concept


def _prioritized_concepts(
    payload: QuizAgentInput,
    topic_by_concept: dict[str, CurriculumTopicDTO],
) -> list[str]:
    values: list[str] = []
    values.extend(payload.target_concepts)
    for topic in payload.curriculum_topics:
        values.extend(topic.concept_ids)
    concepts = [concept for concept in _unique(values) if concept in topic_by_concept]
    if concepts:
        return concepts
    # Nothing requested resolved to a curriculum topic (shouldn't happen for a
    # well-formed curriculum) - fall back to the curriculum's own first concept
    # rather than a fixed domain default.
    first_topic = payload.curriculum_topics[0]
    return [first_topic.concept_ids[0]]


def _quiz_title(payload: QuizAgentInput) -> str:
    if "rag" in payload.goal_text.lower():
        return "RAG Feedback Checkpoint"
    return "Deterministic Feedback Checkpoint"


def _question_for_concept(
    concept_id: str,
    topic: CurriculumTopicDTO,
    all_topics: list[CurriculumTopicDTO],
) -> QuizQuestionDTO:
    label = concept_id.replace("_", " ")
    return QuizQuestionDTO(
        question_id=f"question_quiz_{concept_id}",
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt=f"Which topic in this curriculum covers '{label}'?",
        options=_topic_options(topic, all_topics),
        concept_ids=[concept_id],
        difficulty=topic.difficulty,
        correct_answer=topic.title,
        points=1.0,
        explanation=f"'{label}' is covered in the topic '{topic.title}'.",
    )


def _topic_options(
    topic: CurriculumTopicDTO,
    all_topics: list[CurriculumTopicDTO],
) -> list[str]:
    options = [topic.title]
    for other in all_topics:
        if other.title not in options:
            options.append(other.title)
        if len(options) == 4:
            break
    return options


def _first_wrong_option(question: QuizQuestionDTO) -> str:
    for option in question.options:
        if option != question.correct_answer:
            return option
    return "Needs review"


def _is_correct(answer: QuizAnswerSubmission, question: QuizQuestionDTO) -> bool:
    return answer.selected_options == [question.correct_answer]


def _feedback(total_score: float, weak_concepts: list[str]) -> str:
    if total_score >= LOW_SCORE_THRESHOLD:
        return "Checkpoint passed. Continue with the next planned topic."
    if weak_concepts:
        concepts = ", ".join(concept.replace("_", " ") for concept in weak_concepts)
        return f"Review these concepts before continuing: {concepts}."
    return "Review the checkpoint concepts before continuing."


def _fallback_concept_score(questions: list[QuizQuestionDTO]) -> ConceptQuizScore:
    concept_id = questions[0].concept_ids[0] if questions else "general_concepts"
    return ConceptQuizScore(
        concept_id=concept_id,
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
