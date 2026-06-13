from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

CurriculumStatus = Literal["generated", "invalid"]
CurriculumSource = Literal["deterministic", "mock_llm", "real_llm"]
TopicPriority = Literal["high", "medium", "low"]
ValidationSeverity = Literal["error", "warning"]
DifficultyLevel = Literal["beginner", "intermediate", "advanced"]

DEFAULT_USER_ID = "demo-user"


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_uuid() -> str:
    return str(uuid4())
