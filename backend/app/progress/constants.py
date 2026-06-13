from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

TopicStatus = Literal["pending", "in_progress", "done", "stuck"]
WeekStatus = Literal["pending", "in_progress", "done", "stuck"]
ProgressEventType = Literal[
    "initialized",
    "marked_done",
    "marked_stuck",
    "marked_in_progress",
    "quiz_completed",
    "resource_viewed",
]
AdapterSignalType = Literal[
    "on_track",
    "behind_schedule_candidate",
    "repeated_stuck_topics",
    "low_quiz_score",
    "completed_week",
]

DEFAULT_USER_ID = "demo-user"
LOW_QUIZ_SCORE_THRESHOLD = 0.6
REPEATED_STUCK_THRESHOLD = 2


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_event_id() -> str:
    return f"progress_evt_{uuid4().hex}"
