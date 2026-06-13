from fastapi import APIRouter

from app.core.errors import PathAIError
from app.evaluation.errors import EvaluationError
from app.evaluation.schemas import (
    EvaluationDatasetsResponse,
    EvaluationReport,
    EvaluationRubricsResponse,
    EvaluationRunRequest,
    LearningGainRequest,
    LearningGainResult,
)
from app.evaluation.service import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["evaluation"])
evaluation_service = EvaluationService()


@router.get(
    "/datasets",
    response_model=EvaluationDatasetsResponse,
    summary="List local synthetic evaluation datasets.",
)
async def list_evaluation_datasets() -> EvaluationDatasetsResponse:
    try:
        return EvaluationDatasetsResponse(datasets=evaluation_service.list_datasets())
    except EvaluationError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/run-sample",
    response_model=EvaluationReport,
    summary="Run a deterministic synthetic PathAI evaluation report.",
)
async def run_sample_evaluation(request: EvaluationRunRequest) -> EvaluationReport:
    try:
        return evaluation_service.run_sample_evaluation(request)
    except EvaluationError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/learning-gain",
    response_model=LearningGainResult,
    summary="Calculate normalized learning gain from pre/post scores.",
)
async def calculate_learning_gain(request: LearningGainRequest) -> LearningGainResult:
    return evaluation_service.calculate_learning_gain(request)


@router.get(
    "/rubrics",
    response_model=EvaluationRubricsResponse,
    summary="Return human-review rubrics for academic evaluation.",
)
async def get_evaluation_rubrics() -> EvaluationRubricsResponse:
    return EvaluationRubricsResponse(rubrics=evaluation_service.get_rubrics())


def _to_pathai_error(exc: EvaluationError) -> PathAIError:
    return PathAIError(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
