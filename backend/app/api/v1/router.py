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
    me_assessment,
    orchestration,
    progress,
    quiz,
    resource,
    workspace,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.public_router)
api_router.include_router(auth.router)
api_router.include_router(workspace.router)
api_router.include_router(me_assessment.router)
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
