from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import (
    AssessmentAgentServiceDependency,
    AssessmentServiceDependency,
    AuthorizationDependency,
    CurrentUserDependency,
    GoalServiceDependency,
    WorkspaceServiceDependency,
    require_auth_enabled,
)
from app.schemas.assessment import (
    AssessmentAnswerCreate,
    AssessmentAnswerResponse,
    AssessmentSessionDTO,
)
from app.schemas.ids import AssessmentId

# The whole router requires auth; it is invisible (404) when auth is disabled,
# mirroring app/api/v1/workspace.py.
router = APIRouter(
    prefix="/me/assessment",
    tags=["assessment"],
    dependencies=[Depends(require_auth_enabled)],
)


@router.get("", response_model=AssessmentSessionDTO)
def get_my_assessment(
    user: CurrentUserDependency,
    workspace: WorkspaceServiceDependency,
    agents: AssessmentAgentServiceDependency,
) -> AssessmentSessionDTO:
    goal = workspace.get_owned_goal(user)
    if goal is None:
        raise HTTPException(status_code=404, detail="no workspace")
    session = agents.get_current_session(goal)
    if session is None:
        raise HTTPException(status_code=404, detail="no assessment session")
    return session


@router.post("/start", response_model=AssessmentSessionDTO, status_code=201)
def start_my_assessment(
    user: CurrentUserDependency,
    workspace: WorkspaceServiceDependency,
    agents: AssessmentAgentServiceDependency,
) -> AssessmentSessionDTO:
    goal = workspace.get_owned_goal(user)
    if goal is None:
        raise HTTPException(status_code=404, detail="no workspace")
    return agents.start(goal)


@router.post("/{assessment_id}/answer", response_model=AssessmentAnswerResponse)
def answer_my_assessment(
    assessment_id: AssessmentId,
    answer_create: AssessmentAnswerCreate,
    user: CurrentUserDependency,
    assessments: AssessmentServiceDependency,
    goals: GoalServiceDependency,
    authz: AuthorizationDependency,
    agents: AssessmentAgentServiceDependency,
) -> AssessmentAnswerResponse:
    session = assessments.get_session_by_id(assessment_id)
    authz.assert_goal_access(user, session.goal_id)
    goal = goals.get_by_id(session.goal_id)
    updated_session, answer = agents.submit_answer(
        goal=goal,
        session=session,
        answer_create=answer_create,
    )
    return AssessmentAnswerResponse(session=updated_session, answer=answer)
