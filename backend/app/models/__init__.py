"""Beanie document models for PathAI."""

from beanie import Document

from app.assessment.models import AssessmentSessionDocument
from app.curriculum.models import CurriculumDocument
from app.models.adaptation_log import AdaptationLogDocument
from app.models.generation_job import GenerationJobDocument
from app.models.progress_log import ProgressLogDocument
from app.models.quiz import QuizDocument
from app.models.resource import ResourceDocument
from app.models.user import UserProfileDocument

DOCUMENT_MODELS: list[type[Document]] = [
    UserProfileDocument,
    AssessmentSessionDocument,
    CurriculumDocument,
    ResourceDocument,
    QuizDocument,
    ProgressLogDocument,
    AdaptationLogDocument,
    GenerationJobDocument,
]


def get_registered_model_names() -> list[str]:
    return [model.__name__ for model in DOCUMENT_MODELS]


__all__ = [
    "AdaptationLogDocument",
    "AssessmentSessionDocument",
    "CurriculumDocument",
    "DOCUMENT_MODELS",
    "GenerationJobDocument",
    "ProgressLogDocument",
    "QuizDocument",
    "ResourceDocument",
    "UserProfileDocument",
    "get_registered_model_names",
]
