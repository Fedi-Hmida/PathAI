from __future__ import annotations

from enum import StrEnum


class DifficultyLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExecutionMode(StrEnum):
    INTERACTIVE = "interactive"
    DEMO = "demo"


class GoalStatus(StrEnum):
    CREATED = "created"
    ASSESSMENT_STARTED = "assessment_started"
    CURRICULUM_GENERATED = "curriculum_generated"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class AssessmentStatus(StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeMapStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    FAILED = "failed"


class CurriculumStatus(StrEnum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    ACTIVE = "active"
    ADAPTED = "adapted"
    SUPERSEDED = "superseded"
    FAILED = "failed"


class ResourceStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    NEEDS_REVIEW = "needs_review"


class ResourceAttachmentStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REMOVED = "removed"


class ProgressStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ADAPTATION_NEEDED = "adaptation_needed"
    COMPLETED = "completed"


class TopicProgressStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STUCK = "stuck"
    NEEDS_REVIEW = "needs_review"


class QuizStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class QuizAttemptStatus(StrEnum):
    SUBMITTED = "submitted"
    SCORED = "scored"
    FAILED = "failed"


class AdaptationStatus(StrEnum):
    PROPOSED = "proposed"
    APPLIED = "applied"
    FAILED = "failed"


class CriticPassStatus(StrEnum):
    PASS = "pass"
    REVISE = "revise"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    FAILED = "failed"


class EvaluationPassStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    PASS_WITH_WARNINGS = "pass_with_warnings"


class OrchestrationStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_USER = "waiting_for_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestrationRunStatus(StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    REQUIRES_INPUT = "requires_input"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class NodeResultStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    REQUIRES_INPUT = "requires_input"


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    SELF_RATING = "self_rating"


class ConceptClassification(StrEnum):
    STRONG = "strong"
    DEVELOPING = "developing"
    WEAK = "weak"
    MISSING = "missing"


class ResourceType(StrEnum):
    DOCUMENTATION = "documentation"
    TUTORIAL = "tutorial"
    PAPER = "paper"
    ARTICLE = "article"
    VIDEO = "video"
    CODE_EXAMPLE = "code_example"
    EXERCISE = "exercise"
    CHECKLIST = "checklist"


class ScoringPolicyType(StrEnum):
    EXACT_MATCH = "exact_match"
    RUBRIC = "rubric"
    SELF_RATING = "self_rating"


class AdaptationTriggerType(StrEnum):
    QUIZ_SCORE_BELOW_THRESHOLD = "quiz_score_below_threshold"
    STUCK_EVENT_THRESHOLD = "stuck_event_threshold"
    CRITIC_SCORE_BELOW_THRESHOLD = "critic_score_below_threshold"


class CurriculumChangeType(StrEnum):
    INSERT_TOPIC = "insert_topic"
    ADD_PRACTICE_EXERCISE = "add_practice_exercise"
    REORDER_TOPIC = "reorder_topic"
    REDUCE_DIFFICULTY = "reduce_difficulty"
    ADD_RESOURCE = "add_resource"
    ADD_REVIEW_QUIZ = "add_review_quiz"
    SPLIT_TOPIC = "split_topic"
    DEFER_TOPIC = "defer_topic"
