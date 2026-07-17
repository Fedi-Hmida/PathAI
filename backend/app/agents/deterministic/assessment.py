from __future__ import annotations

import re
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
from app.schemas.enums import AssessmentStatus, DifficultyLevel, QuestionType
from app.schemas.goal import LearnerProfile, LearningGoalDTO

CANONICAL_DIAGNOSTIC_CONCEPTS: tuple[str, ...] = (
    "rag_fundamentals",
    "retrieval_evaluation",
    "vector_search",
    "chunking",
    "embeddings",
    "production_rag_failures",
)

_RAG_WORD_PATTERN = re.compile(r"\b(rag|retrieval)\b")

_GOAL_TEXT_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "to", "for", "of", "in", "on", "and", "or", "with",
        "my", "i", "learn", "learning", "want", "well", "enough", "so", "that",
        "at", "as", "be", "is", "are", "will", "can", "into", "about", "how",
        "this", "it", "its", "me", "months", "month", "weeks", "week", "years",
        "year", "build", "get", "good", "new", "playing", "play",
    }
)

_QUESTION_GAIN: dict[DifficultyLevel, float] = {
    DifficultyLevel.BEGINNER: 0.62,
    DifficultyLevel.INTERMEDIATE: 0.74,
    DifficultyLevel.ADVANCED: 0.82,
}

_QUESTION_DIFFICULTY_BY_POSITION: tuple[DifficultyLevel, ...] = (
    DifficultyLevel.BEGINNER,
    DifficultyLevel.INTERMEDIATE,
    DifficultyLevel.INTERMEDIATE,
    DifficultyLevel.ADVANCED,
    DifficultyLevel.ADVANCED,
)


def diagnostic_focus_for_goal(goal_text: str, learner_profile: LearnerProfile) -> list[str]:
    """Concepts to target for this goal's diagnostic.

    RAG-specific concepts are only used when the goal or profile is actually
    about RAG/retrieval (word-boundary matched, not a raw substring check -
    "mortgage" must not match "rag"). Anything else falls back to keywords
    derived from the goal text itself, never to the RAG concept set - a goal
    about an unrelated topic must never silently default to RAG.
    """
    normalized = f"{goal_text} {' '.join(learner_profile.weak_areas)}".lower()
    concepts: list[str] = []
    if _RAG_WORD_PATTERN.search(normalized):
        concepts.extend(CANONICAL_DIAGNOSTIC_CONCEPTS)
    concepts.extend(_safe_concepts(learner_profile.weak_areas))
    concepts.extend(_safe_concepts(learner_profile.strengths))
    return _unique(concepts) or _keywords_from_goal_text(goal_text)


def _keywords_from_goal_text(goal_text: str) -> list[str]:
    """A lightweight, deterministic stand-in for real concept extraction.

    Only used as a topic-neutral seed for target_concepts - the real
    per-goal concept understanding comes from the LLM agent when enabled;
    this just keeps the deterministic path (and any un-configured LLM
    prompt) from defaulting to RAG vocabulary for an unrelated goal.
    """
    tokens = re.findall(r"[a-z0-9]+", goal_text.lower())
    keywords = [token for token in tokens if len(token) > 2 and token not in _GOAL_TEXT_STOPWORDS]
    return _unique(keywords)[:6] or ["general_concepts"]


def build_question_output(payload: AssessmentAgentInput) -> AssessmentAgentOutput:
    answered_concepts = [
        concept_id
        for answer in payload.prior_answers
        for concept_id in answer.question.target_concepts
    ]
    concept_id = _next_concept(payload.target_concepts, answered_concepts)
    question = _question_for_concept(concept_id, index=len(payload.prior_answers))
    return AssessmentAgentOutput(
        question=question,
        rationale=_question_rationale(question),
        estimated_information_gain=_QUESTION_GAIN[question.difficulty],
    )


def _next_concept(target_concepts: list[str], answered_concepts: list[str]) -> str:
    for concept_id in target_concepts:
        if concept_id not in answered_concepts:
            return concept_id
    # Every target concept has already been asked at least once - cycle back
    # for a second reading rather than crashing when there are fewer target
    # concepts than the diagnostic's question limit.
    return target_concepts[len(answered_concepts) % len(target_concepts)]


def _question_for_concept(concept_id: str, *, index: int) -> AssessmentQuestionDTO:
    label = concept_id.replace("_", " ")
    difficulty = _QUESTION_DIFFICULTY_BY_POSITION[
        min(index, len(_QUESTION_DIFFICULTY_BY_POSITION) - 1)
    ]
    return AssessmentQuestionDTO(
        question_id=f"question_self_rating_{index}_{concept_id}",
        question_type=QuestionType.SELF_RATING,
        prompt=f"How confident are you in {label}? (1 = not at all, 5 = very confident)",
        target_concepts=[concept_id],
        difficulty=difficulty,
    )


def seeded_answer_for_question(
    *,
    goal: LearningGoalDTO,
    question: AssessmentQuestionDTO,
) -> AssessmentAnswerDTO:
    concept_id = question.target_concepts[0]
    self_rating = _seeded_self_rating(concept_id, goal.learner_profile)
    return AssessmentAnswerDTO(
        answer_id=f"answer_demo_{question.question_id.removeprefix('question_')}",
        assessment_session_id=demo.ASSESSMENT_ID,
        goal_id=goal.goal_id,
        question=question,
        answer_text=None,
        selected_options=[],
        self_rating=self_rating,
        score=0.0,
        concept_scores=[],
        feedback=None,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _seeded_self_rating(concept_id: str, learner_profile: LearnerProfile) -> int:
    """A plausible simulated self-rating for the no-real-learner auto-run path.

    Biased off the learner profile's own weak_areas/strengths - never
    topic-specific - so a profile with no signal (the default for a real,
    non-demo workspace) degrades to a neutral rating for every concept.
    """
    if concept_id in _safe_concepts(learner_profile.weak_areas):
        return 2
    if concept_id in _safe_concepts(learner_profile.strengths):
        return 4
    return 3


def score_answer(answer: AssessmentAnswerDTO) -> AssessmentScoreOutput:
    score = _score_for_self_rating(answer.self_rating)
    concept_scores = [
        ConceptEvidenceUpdate(
            concept_id=concept_id,
            score_delta=round((score - 0.5) * 2, 2),
            evidence=_evidence_text(concept_id, answer.self_rating),
        )
        for concept_id in answer.question.target_concepts
    ]
    return AssessmentScoreOutput(
        answer_id=answer.answer_id,
        score=score,
        concept_scores=concept_scores,
        feedback=_feedback_for_score(score),
        confidence_after_answer=_confidence_after_answer(score),
    )


def _score_for_self_rating(self_rating: int | None) -> float:
    if self_rating is None:
        return 0.5
    return round((self_rating - 1) / 4, 2)


def _evidence_text(concept_id: str, self_rating: int | None) -> str:
    label = concept_id.replace("_", " ")
    if self_rating is None:
        return f"No self-rating provided for {label}."
    return f"Learner self-rated {self_rating}/5 confidence in {label}."


def _feedback_for_score(score: float) -> str:
    if score < 0.35:
        return "Add targeted practice before moving deeper."
    if score < 0.65:
        return "Developing understanding - keep reinforcing with practice."
    return "Strong self-reported understanding."


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


def _question_rationale(question: AssessmentQuestionDTO) -> str:
    concepts = ", ".join(question.target_concepts)
    return f"Checks deterministic diagnostic evidence for: {concepts}."


def _confidence_after_answer(score: float) -> float:
    decisiveness = abs(score - 0.5) * 2
    return round(min(0.86, 0.5 + 0.3 * decisiveness), 2)


def _ordered_evidence_concepts(concept_scores: dict[str, list[float]]) -> list[str]:
    return list(concept_scores)


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
