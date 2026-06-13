from typing import Protocol

from app.curriculum.errors import CurriculumInputError, CurriculumNotFoundError
from app.curriculum.llm import generate_curriculum_with_llm
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.rules import validate_curriculum_plan
from app.curriculum.schemas import (
    CurriculumGenerateResponse,
    CurriculumGenerationRequest,
    CurriculumGenerationResult,
    CurriculumPlan,
    CurriculumResponse,
    CurriculumValidationIssue,
    CurriculumValidationResponse,
)
from app.repositories import CurriculumRepository, FakeCurriculumRepository


class CurriculumStore(Protocol):
    def save(self, curriculum: CurriculumPlan) -> None:
        ...

    def load(self, curriculum_id: str) -> CurriculumPlan | None:
        ...

    def clear(self) -> None:
        ...


class RepositoryBackedCurriculumStore:
    def __init__(self, repository: CurriculumRepository | None = None) -> None:
        self.repository = repository or FakeCurriculumRepository()

    def save(self, curriculum: CurriculumPlan) -> None:
        self.repository.save_curriculum(curriculum.model_dump(mode="json"))

    def load(self, curriculum_id: str) -> CurriculumPlan | None:
        payload = self.repository.get_curriculum(curriculum_id)
        if payload is None:
            return None
        return CurriculumPlan.model_validate(payload)

    def clear(self) -> None:
        clear = getattr(self.repository, "clear", None)
        if callable(clear):
            clear()


class InMemoryCurriculumStore(RepositoryBackedCurriculumStore):
    """Backward-compatible fake repository store for tests and local demo routes."""

    def __init__(self) -> None:
        super().__init__(FakeCurriculumRepository())


class CurriculumService:
    def __init__(
        self,
        store: CurriculumStore | None = None,
        repository: CurriculumRepository | None = None,
    ) -> None:
        self.store = store or RepositoryBackedCurriculumStore(repository)

    async def generate_curriculum(
        self,
        request: CurriculumGenerationRequest,
    ) -> CurriculumGenerateResponse:
        self._ensure_explicit_generation_input(request)
        deterministic = build_deterministic_curriculum(request)
        curriculum = await generate_curriculum_with_llm(request, deterministic)
        validation_issues = validate_curriculum_plan(curriculum)
        curriculum = curriculum.model_copy(
            update={
                "validation_issues": validation_issues,
                "status": "invalid" if _has_errors(validation_issues) else "generated",
            }
        )
        self.store.save(curriculum)
        return CurriculumGenerateResponse(
            result=CurriculumGenerationResult(
                curriculum=curriculum,
                validation_issues=validation_issues,
            )
        )

    def get_curriculum(self, curriculum_id: str) -> CurriculumResponse:
        curriculum = self.store.load(curriculum_id)
        if curriculum is None:
            raise CurriculumNotFoundError(curriculum_id)
        return CurriculumResponse(curriculum=curriculum)

    def validate_request(
        self,
        request: CurriculumGenerationRequest,
    ) -> CurriculumValidationResponse:
        self._ensure_explicit_generation_input(request)
        plan = build_deterministic_curriculum(request)
        issues = validate_curriculum_plan(plan)
        return CurriculumValidationResponse(
            valid=not _has_errors(issues),
            validation_issues=issues,
            message="Curriculum request can generate a structurally valid draft."
            if not _has_errors(issues)
            else "Curriculum request generated structural validation issues.",
        )

    def _ensure_explicit_generation_input(self, request: CurriculumGenerationRequest) -> None:
        missing = [
            name
            for name, value in {
                "goal": request.goal,
                "timeline_weeks": request.timeline_weeks,
                "hours_per_week": request.hours_per_week,
                "knowledge_map": request.knowledge_map,
            }.items()
            if value is None
        ]
        if missing:
            raise CurriculumInputError(
                code="curriculum_input_incomplete",
                message=f"Curriculum input is incomplete. Missing: {', '.join(missing)}.",
                status_code=422,
            )


def _has_errors(issues: list[CurriculumValidationIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)
