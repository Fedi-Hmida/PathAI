import json
from pathlib import Path

from app.evaluation.constants import (
    DEFAULT_EVALUATION_DATASET,
    SYNTHETIC_DATASET_DESCRIPTION,
)
from app.evaluation.errors import EvaluationError
from app.evaluation.schemas import EvaluationDatasetSummary, LearnerGoalFixture

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "goals.json"


def load_goal_fixtures(dataset_name: str = DEFAULT_EVALUATION_DATASET) -> list[LearnerGoalFixture]:
    if dataset_name != DEFAULT_EVALUATION_DATASET:
        raise EvaluationError(
            code="evaluation_dataset_not_found",
            message=f"Evaluation dataset '{dataset_name}' is not available locally.",
            status_code=404,
        )
    raw_items = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw_items, list):
        raise EvaluationError(
            code="evaluation_dataset_invalid",
            message="Evaluation fixture file must contain a list of goal fixtures.",
            status_code=500,
        )
    fixtures: list[LearnerGoalFixture] = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise EvaluationError(
                code="evaluation_dataset_invalid",
                message="Each evaluation fixture must be an object.",
                status_code=500,
            )
        fixtures.append(LearnerGoalFixture.model_validate(item))
    return [fixture.model_copy(deep=True) for fixture in fixtures]


def list_dataset_summaries() -> list[EvaluationDatasetSummary]:
    fixtures = load_goal_fixtures()
    return [
        EvaluationDatasetSummary(
            dataset_name=DEFAULT_EVALUATION_DATASET,
            description=SYNTHETIC_DATASET_DESCRIPTION,
            fixture_count=len(fixtures),
            goals=[fixture.goal for fixture in fixtures],
        )
    ]


def get_dataset_summary(dataset_name: str = DEFAULT_EVALUATION_DATASET) -> EvaluationDatasetSummary:
    for summary in list_dataset_summaries():
        if summary.dataset_name == dataset_name:
            return summary
    raise EvaluationError(
        code="evaluation_dataset_not_found",
        message=f"Evaluation dataset '{dataset_name}' is not available locally.",
        status_code=404,
    )
