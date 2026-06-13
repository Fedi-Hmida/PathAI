from fastapi import APIRouter

from app.api.v1 import (
    adapt,
    assessment,
    critic,
    curriculum,
    dev,
    evaluation,
    health,
    progress,
    quiz,
    resources,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(assessment.router)
api_router.include_router(curriculum.router)
api_router.include_router(resources.router)
api_router.include_router(critic.router)
api_router.include_router(progress.router)
api_router.include_router(quiz.router)
api_router.include_router(adapt.router)
api_router.include_router(evaluation.router)
api_router.include_router(dev.router)
