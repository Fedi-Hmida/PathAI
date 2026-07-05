from __future__ import annotations

from typing import Annotated, Final, TypeAlias

from pydantic import Field

ID_BODY_PATTERN: Final[str] = r"[A-Za-z0-9][A-Za-z0-9_-]{2,119}"

GOAL_PREFIX: Final[str] = "goal_"
RUN_PREFIX: Final[str] = "run_"
ASSESSMENT_PREFIX: Final[str] = "assessment_"
ANSWER_PREFIX: Final[str] = "answer_"
KNOWLEDGE_MAP_PREFIX: Final[str] = "kmap_"
CURRICULUM_PREFIX: Final[str] = "curriculum_"
WEEK_PREFIX: Final[str] = "week_"
TOPIC_PREFIX: Final[str] = "topic_"
RESOURCE_PREFIX: Final[str] = "resource_"
ATTACHMENT_PREFIX: Final[str] = "attach_"
PROGRESS_PREFIX: Final[str] = "progress_"
QUIZ_PREFIX: Final[str] = "quiz_"
QUESTION_PREFIX: Final[str] = "question_"
ATTEMPT_PREFIX: Final[str] = "attempt_"
ADAPTATION_PREFIX: Final[str] = "adapt_"
CRITIC_PREFIX: Final[str] = "critic_"
EVALUATION_PREFIX: Final[str] = "eval_"

GoalId: TypeAlias = Annotated[str, Field(pattern=rf"^{GOAL_PREFIX}{ID_BODY_PATTERN}$")]
RunId: TypeAlias = Annotated[str, Field(pattern=rf"^{RUN_PREFIX}{ID_BODY_PATTERN}$")]
AssessmentId: TypeAlias = Annotated[
    str,
    Field(pattern=rf"^{ASSESSMENT_PREFIX}{ID_BODY_PATTERN}$"),
]
AnswerId: TypeAlias = Annotated[str, Field(pattern=rf"^{ANSWER_PREFIX}{ID_BODY_PATTERN}$")]
KnowledgeMapId: TypeAlias = Annotated[
    str,
    Field(pattern=rf"^{KNOWLEDGE_MAP_PREFIX}{ID_BODY_PATTERN}$"),
]
CurriculumId: TypeAlias = Annotated[
    str,
    Field(pattern=rf"^{CURRICULUM_PREFIX}{ID_BODY_PATTERN}$"),
]
WeekId: TypeAlias = Annotated[str, Field(pattern=rf"^{WEEK_PREFIX}{ID_BODY_PATTERN}$")]
TopicId: TypeAlias = Annotated[str, Field(pattern=rf"^{TOPIC_PREFIX}{ID_BODY_PATTERN}$")]
ResourceId: TypeAlias = Annotated[str, Field(pattern=rf"^{RESOURCE_PREFIX}{ID_BODY_PATTERN}$")]
AttachmentId: TypeAlias = Annotated[
    str,
    Field(pattern=rf"^{ATTACHMENT_PREFIX}{ID_BODY_PATTERN}$"),
]
ProgressId: TypeAlias = Annotated[str, Field(pattern=rf"^{PROGRESS_PREFIX}{ID_BODY_PATTERN}$")]
QuizId: TypeAlias = Annotated[str, Field(pattern=rf"^{QUIZ_PREFIX}{ID_BODY_PATTERN}$")]
QuestionId: TypeAlias = Annotated[str, Field(pattern=rf"^{QUESTION_PREFIX}{ID_BODY_PATTERN}$")]
AttemptId: TypeAlias = Annotated[str, Field(pattern=rf"^{ATTEMPT_PREFIX}{ID_BODY_PATTERN}$")]
AdaptationId: TypeAlias = Annotated[
    str,
    Field(pattern=rf"^{ADAPTATION_PREFIX}{ID_BODY_PATTERN}$"),
]
CriticReviewId: TypeAlias = Annotated[str, Field(pattern=rf"^{CRITIC_PREFIX}{ID_BODY_PATTERN}$")]
EvaluationReportId: TypeAlias = Annotated[
    str,
    Field(pattern=rf"^{EVALUATION_PREFIX}{ID_BODY_PATTERN}$"),
]
ConceptId: TypeAlias = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{1,80}$")]
