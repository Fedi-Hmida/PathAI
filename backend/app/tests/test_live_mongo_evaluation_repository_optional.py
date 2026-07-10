from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError
from app.repositories.mongo import MongoEvaluationRepository
from app.schemas.enums import EvaluationPassStatus
from app.schemas.evaluation import EvaluationMetricScores, EvaluationReportDTO

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def evaluation_repository() -> Iterator[MongoEvaluationRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    collection = client[settings.mongodb_database_name]["test_17k_evaluation_reports"]
    repository = MongoEvaluationRepository(collection)
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_evaluation_report(
    evaluation_report_id: str,
    goal_id: str,
    run_id: str,
) -> EvaluationReportDTO:
    now = datetime.now(tz=UTC)
    return EvaluationReportDTO(
        evaluation_report_id=evaluation_report_id,
        goal_id=goal_id,
        run_id=run_id,
        metric_scores=EvaluationMetricScores(
            curriculum_coverage=0.8,
            difficulty_alignment=0.75,
            pacing_balance=0.7,
            resource_relevance=0.8,
            resource_diversity=0.6,
            quiz_alignment=0.75,
            critic_coherence=0.8,
            workflow_completeness=0.9,
        ),
        overall_score=0.77,
        pass_status=EvaluationPassStatus.PASS_WITH_WARNINGS,
        warnings=["Resource diversity is on the low side."],
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_evaluation_report_create_get_and_duplicate(
    evaluation_repository: MongoEvaluationRepository,
) -> None:
    report = _sample_evaluation_report(
        "eval_live17k_a",
        "goal_live17k_a",
        "run_live17k_a",
    )

    created = evaluation_repository.create(report)
    assert created.evaluation_report_id == report.evaluation_report_id
    assert created.metric_scores.curriculum_coverage == 0.8

    fetched = evaluation_repository.get_by_id(report.evaluation_report_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        evaluation_repository.create(report)


@pytest.mark.live_mongo
def test_evaluation_report_list_by_goal_and_run_and_save(
    evaluation_repository: MongoEvaluationRepository,
) -> None:
    report = _sample_evaluation_report(
        "eval_live17k_b",
        "goal_live17k_b",
        "run_live17k_b",
    )
    evaluation_repository.create(report)

    assert len(evaluation_repository.list_by_goal_id(report.goal_id)) == 1
    assert len(evaluation_repository.list_by_run_id(report.run_id)) == 1

    revised = report.model_copy(update={"pass_status": EvaluationPassStatus.PASS})
    saved = evaluation_repository.save(revised)
    assert saved.pass_status == EvaluationPassStatus.PASS
