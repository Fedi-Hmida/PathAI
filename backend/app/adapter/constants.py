from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

AdaptationTriggerReason = Literal[
    "behind_schedule",
    "repeated_stuck_topics",
    "low_quiz_score",
    "completed_week",
    "ahead_of_schedule",
    "manual_request",
    "none",
]
AdaptationSignalSeverity = Literal["info", "warning", "critical"]
AdaptationDecisionStatus = Literal["no_replan", "replan_recommended", "replanned"]
ReplanFlowStep = Literal["adapter", "curriculum", "resource", "critic", "persist", "notify"]

LOW_QUIZ_SCORE_THRESHOLD = 0.6
REPEATED_STUCK_TOPIC_THRESHOLD = 2
BEHIND_SCHEDULE_COMPLETION_THRESHOLD = 50.0
AHEAD_OF_SCHEDULE_WEEK_DELTA = 1


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_adaptation_id() -> str:
    return f"adapt_{uuid4().hex}"
