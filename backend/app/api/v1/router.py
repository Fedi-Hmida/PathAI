from fastapi import APIRouter

from app.api.v1 import (
    adaptation,
    assessment,
    auth,
    critic,
    curriculum,
    dashboard,
    demo,
    evaluation,
    goal,
    health,
    knowledge_map,
    orchestration,
    progress,
    quiz,
    resource,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(goal.router)
api_router.include_router(assessment.router)
api_router.include_router(knowledge_map.router)
api_router.include_router(curriculum.router)
api_router.include_router(resource.router)
api_router.include_router(progress.router)
api_router.include_router(quiz.router)
api_router.include_router(adaptation.router)
api_router.include_router(critic.router)
api_router.include_router(evaluation.router)
api_router.include_router(orchestration.router)
api_router.include_router(dashboard.router)
api_router.include_router(demo.router)
