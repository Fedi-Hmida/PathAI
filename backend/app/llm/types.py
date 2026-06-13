from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LLMRole = Literal["system", "user", "assistant"]


class LLMMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: LLMRole
    content: str = Field(min_length=1)


class LLMRequestOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=8000)
    response_format: dict[str, str] | None = None


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    content: str
    model: str | None = None
    finish_reason: str | None = None
    usage: dict[str, object] = Field(default_factory=dict)
    raw: dict[str, object] = Field(default_factory=dict)


class SafeLLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_url_configured: bool
    api_key_configured: bool
    model: str
    timeout_seconds: float
    max_retries: int
    retry_backoff_seconds: float
    mock_mode: bool
    prompt_version: str


class LLMHealthCheckOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "degraded"]
    message: str = Field(min_length=1, max_length=300)
    model: str | None = Field(default=None, max_length=120)


class AssessmentQuestionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=5, max_length=1200)
    question_type: Literal["short_answer", "mcq", "true_false"]
    options: list[str] = Field(default_factory=list, max_length=6)
    expected_concepts: list[str] = Field(default_factory=list)
    difficulty: Literal["beginner", "intermediate", "advanced"]


class KnowledgeMapDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strong: list[str] = Field(default_factory=list)
    weak: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    recommended_level: Literal["beginner", "intermediate", "advanced"]
    confidence_score: float = Field(ge=0.0, le=1.0)


class CurriculumDraftSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=180)
    overview: str = Field(min_length=10, max_length=1000)
    total_weeks: int = Field(ge=1, le=52)
    main_topics: list[str] = Field(default_factory=list)
