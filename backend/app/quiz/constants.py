from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

QuizQuestionType = Literal["multiple_choice", "true_false", "short_answer"]

DEFAULT_QUESTION_COUNT = 5
MAX_QUESTION_COUNT = 7
PASS_THRESHOLD = 0.7
LOW_SCORE_THRESHOLD = 0.6


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_quiz_id() -> str:
    return f"quiz_{uuid4().hex}"


def new_question_id() -> str:
    return f"question_{uuid4().hex}"


def new_attempt_id() -> str:
    return f"attempt_{uuid4().hex}"
