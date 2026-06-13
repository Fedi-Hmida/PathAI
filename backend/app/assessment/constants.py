from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

AssessmentStatus = Literal["in_progress", "completed", "abandoned"]
AssessmentSignal = Literal["strong", "weak", "missing"]
AssessmentQuestionType = Literal["short_answer", "multiple_choice", "self_rating"]
AssessmentQuestionSource = Literal["question_bank", "mock_llm", "real_llm"]
DifficultyLevel = Literal["beginner", "intermediate", "advanced"]

DEFAULT_USER_ID = "demo-user"
DEFAULT_MAX_QUESTIONS = 8
MIN_QUESTIONS_FOR_CONFIDENCE = 4
MAX_ASSESSMENT_QUESTIONS = 12
MIN_ASSESSMENT_QUESTIONS = 3

IDK_ANSWERS = {
    "",
    "i don't know",
    "i dont know",
    "idk",
    "not sure",
    "no idea",
    "skip",
}


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_uuid() -> str:
    return str(uuid4())
