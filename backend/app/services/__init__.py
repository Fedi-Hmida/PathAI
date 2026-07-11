from __future__ import annotations

from app.services.adaptation import AdaptationService
from app.services.assessment import AssessmentService
from app.services.auth import AuthService, AuthTokenConfig
from app.services.critic import CriticService
from app.services.curriculum import CurriculumService
from app.services.dashboard import DashboardService
from app.services.evaluation import EvaluationService
from app.services.goal import GoalService
from app.services.knowledge_map import KnowledgeMapService
from app.services.orchestration_run import OrchestrationRunService
from app.services.progress import ProgressService
from app.services.quiz import QuizService
from app.services.reporting import ReportingService
from app.services.resource import ResourceService

__all__ = [
    "AdaptationService",
    "AssessmentService",
    "AuthService",
    "AuthTokenConfig",
    "CriticService",
    "CurriculumService",
    "DashboardService",
    "EvaluationService",
    "GoalService",
    "KnowledgeMapService",
    "OrchestrationRunService",
    "ProgressService",
    "QuizService",
    "ReportingService",
    "ResourceService",
]
