from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError, NotFoundError
from app.repositories.mongo import MongoGoalRepository, MongoOrchestrationRunRepository
from app.schemas.enums import (
    DifficultyLevel,
    GoalStatus,
    NodeResultStatus,
    OrchestrationRunStatus,
)
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.orchestration import OrchestrationRunDTO, WorkflowNodeEvent

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def goal_repository() -> Iterator[MongoGoalRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    collection = client[settings.mongodb_database_name]["test_17b_learning_goals"]
    repository = MongoGoalRepository(collection)
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


@pytest.fixture
def orchestration_repository() -> Iterator[MongoOrchestrationRunRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    collection = client[settings.mongodb_database_name]["test_17b_orchestration_runs"]
    repository = MongoOrchestrationRunRepository(collection)
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_goal(goal_id: str, run_id: str) -> LearningGoalDTO:
    now = datetime.now(tz=UTC)
    return LearningGoalDTO(
        goal_id=goal_id,
        run_id=run_id,
        goal_text="Learn distributed systems fundamentals",
        normalized_goal_text="Learn distributed systems fundamentals",
        status=GoalStatus.CREATED,
        learner_profile=LearnerProfile(
            learner_type="live mongo test learner",
            time_availability_hours_per_week=6,
            desired_outcome="Prove the Mongo repository works end to end.",
            difficulty_target=DifficultyLevel.INTERMEDIATE,
        ),
        created_at=now,
        updated_at=now,
    )


def _sample_run(run_id: str, goal_id: str) -> OrchestrationRunDTO:
    now = datetime.now(tz=UTC)
    return OrchestrationRunDTO(
        run_id=run_id,
        goal_id=goal_id,
        workflow_version="live-mongo-test-v1",
        status=OrchestrationRunStatus.CREATED,
        started_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_goal_repository_create_get_and_duplicate(
    goal_repository: MongoGoalRepository,
) -> None:
    goal = _sample_goal("goal_live17b_a", "run_live17b_a")

    created = goal_repository.create(goal)
    assert created.goal_id == goal.goal_id

    fetched = goal_repository.get_by_id(goal.goal_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        goal_repository.create(goal)


@pytest.mark.live_mongo
def test_goal_repository_get_by_run_id_save_and_update_status(
    goal_repository: MongoGoalRepository,
) -> None:
    goal = _sample_goal("goal_live17b_b", "run_live17b_b")
    goal_repository.create(goal)

    by_run = goal_repository.get_by_run_id(goal.run_id)
    assert by_run.goal_id == goal.goal_id

    updated = goal_repository.update_status(goal.goal_id, GoalStatus.ACTIVE)
    assert updated.status == GoalStatus.ACTIVE

    with pytest.raises(NotFoundError):
        goal_repository.get_by_id("goal_live17b_missing")


@pytest.mark.live_mongo
def test_orchestration_run_repository_create_and_append_event(
    orchestration_repository: MongoOrchestrationRunRepository,
) -> None:
    goal_id = "goal_live17b_c"
    run = _sample_run("run_live17b_c", goal_id)
    orchestration_repository.create(run)

    event = WorkflowNodeEvent(
        run_id=run.run_id,
        node_name="load_curriculum",
        status=NodeResultStatus.SUCCESS,
        created_at=datetime.now(tz=UTC),
    )
    updated = orchestration_repository.append_event(run.run_id, event)
    assert len(updated.node_events) == 1
    assert updated.node_events[0].node_name == "load_curriculum"

    by_goal = orchestration_repository.list_by_goal_id(goal_id)
    assert len(by_goal) == 1
