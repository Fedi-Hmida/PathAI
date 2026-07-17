from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema, Score, TimestampedDTO, VersionedDTO
from app.schemas.curriculum import CurriculumTopicDTO
from app.schemas.enums import (
    DifficultyLevel,
    QuestionType,
    QuizAttemptStatus,
    QuizStatus,
    ScoringPolicyType,
)
from app.schemas.ids import AttemptId, ConceptId, CurriculumId, GoalId, QuestionId, QuizId, TopicId


class QuizQuestionDTO(BaseSchema):
    question_id: QuestionId
    question_type: QuestionType
    prompt: str = Field(min_length=1, max_length=800)
    concept_ids: list[ConceptId] = Field(min_length=1, max_length=8)
    difficulty: DifficultyLevel
    correct_answer: str = Field(min_length=1, max_length=500)
    points: float = Field(gt=0.0, le=20.0)
    options: list[str] = Field(default_factory=list, max_length=8)
    rubric: str | None = Field(default=None, max_length=1000)
    explanation: str | None = Field(default=None, max_length=1000)


class LearnerQuizQuestionDTO(BaseSchema):
    question_id: QuestionId
    question_type: QuestionType
    prompt: str = Field(min_length=1, max_length=800)
    concept_ids: list[ConceptId] = Field(min_length=1, max_length=8)
    difficulty: DifficultyLevel
    points: float = Field(gt=0.0, le=20.0)
    options: list[str] = Field(default_factory=list, max_length=8)


class QuizScoringPolicy(BaseSchema):
    type: ScoringPolicyType
    partial_credit: bool = False


class QuizDTO(TimestampedDTO, VersionedDTO):
    quiz_id: QuizId
    goal_id: GoalId
    curriculum_id: CurriculumId
    target_topic_ids: list[TopicId] = Field(min_length=1, max_length=20)
    target_concept_ids: list[ConceptId] = Field(min_length=1, max_length=20)
    status: QuizStatus
    title: str = Field(min_length=1, max_length=220)
    questions: list[QuizQuestionDTO] = Field(min_length=1, max_length=20)
    scoring_policy: QuizScoringPolicy
    difficulty: DifficultyLevel | None = None


class LearnerQuizDTO(BaseSchema):
    quiz_id: QuizId
    title: str = Field(min_length=1, max_length=220)
    questions: list[LearnerQuizQuestionDTO] = Field(min_length=1, max_length=20)
    scoring_policy: QuizScoringPolicy


class QuizAnswerSubmission(BaseSchema):
    question_id: QuestionId
    answer_text: str | None = Field(default=None, max_length=1200)
    selected_options: list[str] = Field(default_factory=list, max_length=8)


class ConceptQuizScore(BaseSchema):
    concept_id: ConceptId
    score: Score
    correct_count: int = Field(ge=0, le=100)
    total_questions: int = Field(ge=1, le=100)


class QuizAttemptDTO(TimestampedDTO, VersionedDTO):
    quiz_attempt_id: AttemptId
    quiz_id: QuizId
    goal_id: GoalId
    curriculum_id: CurriculumId
    answers: list[QuizAnswerSubmission] = Field(min_length=1, max_length=50)
    total_score: Score
    correct_count: int = Field(ge=0, le=100)
    total_questions: int = Field(ge=1, le=100)
    concept_scores: list[ConceptQuizScore] = Field(min_length=1)
    weak_concepts: list[ConceptId] = Field(default_factory=list, max_length=20)
    submitted_at: datetime
    status: QuizAttemptStatus = QuizAttemptStatus.SCORED
    feedback: str | None = Field(default=None, max_length=1000)
    adaptation_triggered: bool = False


class QuizAgentInput(BaseSchema):
    goal_text: str = Field(min_length=5, max_length=500)
    curriculum_topics: list[CurriculumTopicDTO] = Field(min_length=1)
    # No min_length: a learner with no known weak concepts yet (fresh
    # workspace, no progress history) legitimately has none to target - the
    # deterministic agent's own concept-prioritization already falls back to
    # the curriculum's own topic concepts when this is empty.
    target_concepts: list[ConceptId] = Field(default_factory=list, max_length=20)
    difficulty: DifficultyLevel
    question_count: int = Field(ge=1, le=20)


class QuizAgentOutput(BaseSchema):
    quiz_title: str = Field(min_length=1, max_length=220)
    questions: list[QuizQuestionDTO] = Field(min_length=1, max_length=20)
    scoring_policy: QuizScoringPolicy


class QuizScoreOutput(BaseSchema):
    total_score: Score
    correct_count: int = Field(ge=0, le=100)
    total_questions: int = Field(ge=1, le=100)
    concept_scores: list[ConceptQuizScore] = Field(min_length=1)
    weak_concepts: list[ConceptId] = Field(default_factory=list, max_length=20)
    feedback: str = Field(min_length=1, max_length=1000)
