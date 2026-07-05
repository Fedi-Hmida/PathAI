from typing import Literal

from pydantic import BaseModel, Field


class MiniConceptMastery(BaseModel):
    concept_id: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=160)
    mastery_score: float = Field(ge=0.0, le=1.0)
    classification: Literal["strong", "developing", "weak", "missing"]


class MiniKnowledgeMapOutput(BaseModel):
    concepts: list[MiniConceptMastery] = Field(min_length=1)
    summary: str = Field(min_length=1, max_length=500)


class MiniCurriculumWeek(BaseModel):
    week_number: int = Field(ge=1, le=12)
    theme: str = Field(min_length=1, max_length=160)
    topics: list[str] = Field(min_length=1, max_length=8)


class MiniCurriculumOutput(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    weeks: list[MiniCurriculumWeek] = Field(min_length=1, max_length=8)


class MiniQuizQuestion(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_answer: str = Field(min_length=1, max_length=300)
    concept_ids: list[str] = Field(min_length=1, max_length=5)


class MiniQuizOutput(BaseModel):
    questions: list[MiniQuizQuestion] = Field(min_length=1, max_length=10)

