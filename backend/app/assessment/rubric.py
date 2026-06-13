from collections import defaultdict

from app.assessment.constants import IDK_ANSWERS, AssessmentSignal, DifficultyLevel, utc_now
from app.assessment.schemas import (
    AnswerEvaluation,
    AssessmentQuestion,
    KnowledgeMap,
)


def is_idk_answer(answer: str) -> bool:
    return answer.strip().lower() in IDK_ANSWERS


def evaluate_answer(question: AssessmentQuestion, answer: str) -> AnswerEvaluation:
    normalized_answer = answer.strip().lower()
    if is_idk_answer(normalized_answer):
        return AnswerEvaluation(
            question_id=question.question_id,
            topic=question.topic,
            difficulty=question.difficulty,
            answer=answer,
            score=0.0,
            signal="missing",
            matched_concepts=[],
            missing_concepts=question.expected_concepts,
            is_idk=True,
            feedback="Marked as a knowledge gap because the learner did not know the answer.",
            created_at=utc_now(),
        )

    matched: list[str] = []
    missing: list[str] = []
    for concept in question.expected_concepts:
        if _concept_matches(concept, normalized_answer):
            matched.append(concept)
        else:
            missing.append(concept)

    raw_score = len(matched) / max(len(question.expected_concepts), 1)
    if raw_score == 0.0 and normalized_answer:
        raw_score = 0.15
    score = min(1.0, raw_score)
    signal = score_to_signal(score)

    return AnswerEvaluation(
        question_id=question.question_id,
        topic=question.topic,
        difficulty=question.difficulty,
        answer=answer,
        score=score,
        signal=signal,
        matched_concepts=matched,
        missing_concepts=missing,
        is_idk=False,
        feedback=_build_feedback(signal, matched, missing),
        created_at=utc_now(),
    )


def score_to_signal(score: float) -> AssessmentSignal:
    if score >= 0.75:
        return "strong"
    if score >= 0.35:
        return "weak"
    return "missing"


def next_difficulty(current: DifficultyLevel, evaluation: AnswerEvaluation) -> DifficultyLevel:
    order: list[DifficultyLevel] = ["beginner", "intermediate", "advanced"]
    index = order.index(current)
    if evaluation.score >= 0.75 and index < len(order) - 1:
        return order[index + 1]
    if evaluation.score < 0.35 and index > 0:
        return order[index - 1]
    return current


def compute_confidence(answer_count: int, max_questions: int, topic_count: int) -> float:
    answer_factor = min(answer_count / max(max_questions, 1), 1.0)
    coverage_factor = min(topic_count / 6, 1.0)
    confidence = 0.2 + (answer_factor * 0.6) + (coverage_factor * 0.2)
    return round(min(confidence, 0.95), 2)


def build_knowledge_map(
    answers: list[AnswerEvaluation],
    goal: str,
    fallback_level: DifficultyLevel,
    confidence_score: float,
) -> KnowledgeMap:
    scores_by_topic: dict[str, list[float]] = defaultdict(list)
    for answer in answers:
        scores_by_topic[answer.topic].append(answer.score)

    strong: list[str] = []
    weak: list[str] = []
    missing: list[str] = []

    for topic, scores in sorted(scores_by_topic.items()):
        average = sum(scores) / len(scores)
        if average >= 0.75:
            strong.append(topic)
        elif average >= 0.35:
            weak.append(topic)
        else:
            missing.append(topic)

    if not answers:
        missing.append("Initial assessment evidence")

    recommended_level = _recommended_level(answers, fallback_level)
    notes = [
        f"Assessment generated from {len(answers)} answer(s) for goal: {goal}.",
        "Topics are classified using deterministic concept matching for Phase 4.",
    ]
    if any(answer.is_idk for answer in answers):
        notes.append("'I do not know' answers were treated as gap evidence.")

    return KnowledgeMap(
        strong=strong,
        weak=weak,
        missing=missing,
        recommended_level=recommended_level,
        confidence_score=confidence_score,
        assessment_notes=notes,
    )


def _concept_matches(concept: str, answer: str) -> bool:
    tokens = [token for token in concept.lower().replace("-", " ").split() if len(token) >= 3]
    if not tokens:
        return False
    return any(token in answer for token in tokens)


def _build_feedback(signal: AssessmentSignal, matched: list[str], missing: list[str]) -> str:
    if signal == "strong":
        return "Strong answer with the expected concepts present."
    if signal == "weak":
        return "Partial answer; matched some concepts but still has gaps."
    if matched:
        return "Answer includes a small amount of relevant evidence but misses the core concepts."
    if missing:
        return "Answer did not show evidence for the expected concepts."
    return "Answer could not be evaluated confidently."


def _recommended_level(
    answers: list[AnswerEvaluation],
    fallback_level: DifficultyLevel,
) -> DifficultyLevel:
    if not answers:
        return fallback_level
    average = sum(answer.score for answer in answers) / len(answers)
    if average >= 0.76:
        return "advanced"
    if average >= 0.45:
        return "intermediate"
    return "beginner"
