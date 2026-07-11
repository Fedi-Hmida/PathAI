from __future__ import annotations

from app.repositories.fakes.adaptation import FakeAdaptationRepository
from app.repositories.fakes.assessment import FakeAssessmentRepository
from app.repositories.fakes.critic import FakeCriticReviewRepository
from app.repositories.fakes.curriculum import FakeCurriculumRepository
from app.repositories.fakes.evaluation import FakeEvaluationRepository
from app.repositories.fakes.goal import FakeGoalRepository
from app.repositories.fakes.knowledge_map import FakeKnowledgeMapRepository
from app.repositories.fakes.orchestration import FakeOrchestrationRunRepository
from app.repositories.fakes.progress import FakeProgressRepository
from app.repositories.fakes.quiz import FakeQuizRepository
from app.repositories.fakes.refresh_token import FakeRefreshTokenRepository
from app.repositories.fakes.resource import FakeResourceRepository
from app.repositories.fakes.user import FakeUserRepository

__all__ = [
    "FakeAdaptationRepository",
    "FakeAssessmentRepository",
    "FakeCriticReviewRepository",
    "FakeCurriculumRepository",
    "FakeEvaluationRepository",
    "FakeGoalRepository",
    "FakeKnowledgeMapRepository",
    "FakeOrchestrationRunRepository",
    "FakeProgressRepository",
    "FakeQuizRepository",
    "FakeRefreshTokenRepository",
    "FakeResourceRepository",
    "FakeUserRepository",
]
