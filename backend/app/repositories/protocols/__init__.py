from __future__ import annotations

from app.repositories.protocols.adaptation import AdaptationRepository
from app.repositories.protocols.assessment import AssessmentRepository
from app.repositories.protocols.critic import CriticReviewRepository
from app.repositories.protocols.curriculum import CurriculumRepository
from app.repositories.protocols.evaluation import EvaluationRepository
from app.repositories.protocols.goal import GoalRepository
from app.repositories.protocols.knowledge_map import KnowledgeMapRepository
from app.repositories.protocols.orchestration import OrchestrationRunRepository
from app.repositories.protocols.progress import ProgressRepository
from app.repositories.protocols.quiz import QuizRepository
from app.repositories.protocols.resource import ResourceRepository

__all__ = [
    "AdaptationRepository",
    "AssessmentRepository",
    "CriticReviewRepository",
    "CurriculumRepository",
    "EvaluationRepository",
    "GoalRepository",
    "KnowledgeMapRepository",
    "OrchestrationRunRepository",
    "ProgressRepository",
    "QuizRepository",
    "ResourceRepository",
]
