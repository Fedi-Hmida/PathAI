from __future__ import annotations

from app.repositories.mongo.adaptation import MongoAdaptationRepository
from app.repositories.mongo.assessment import MongoAssessmentRepository
from app.repositories.mongo.critic import MongoCriticReviewRepository
from app.repositories.mongo.curriculum import MongoCurriculumRepository
from app.repositories.mongo.evaluation import MongoEvaluationRepository
from app.repositories.mongo.goal import MongoGoalRepository
from app.repositories.mongo.knowledge_map import MongoKnowledgeMapRepository
from app.repositories.mongo.orchestration import MongoOrchestrationRunRepository
from app.repositories.mongo.progress import MongoProgressRepository
from app.repositories.mongo.quiz import MongoQuizRepository
from app.repositories.mongo.resource import MongoResourceRepository

__all__ = [
    "MongoAdaptationRepository",
    "MongoAssessmentRepository",
    "MongoCriticReviewRepository",
    "MongoCurriculumRepository",
    "MongoEvaluationRepository",
    "MongoGoalRepository",
    "MongoKnowledgeMapRepository",
    "MongoOrchestrationRunRepository",
    "MongoProgressRepository",
    "MongoQuizRepository",
    "MongoResourceRepository",
]
