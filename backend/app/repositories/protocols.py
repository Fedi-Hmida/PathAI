from collections.abc import Mapping
from typing import Any, Protocol, TypeAlias

RepositoryPayload: TypeAlias = dict[str, Any]


class AssessmentRepository(Protocol):
    def create_session(self, session: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def get_session(self, session_id: str) -> RepositoryPayload | None:
        ...

    def update_session(
        self,
        session_id: str,
        updates: Mapping[str, Any],
    ) -> RepositoryPayload | None:
        ...

    def finalize_session(
        self,
        session_id: str,
        result: Mapping[str, Any] | None = None,
    ) -> RepositoryPayload | None:
        ...

    def list_recent_sessions(self, limit: int = 20) -> list[RepositoryPayload]:
        ...


class CurriculumRepository(Protocol):
    def save_curriculum(self, curriculum: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def get_curriculum(self, curriculum_id: str) -> RepositoryPayload | None:
        ...

    def list_by_session(self, session_id: str) -> list[RepositoryPayload]:
        ...

    def list_recent_curricula(self, limit: int = 20) -> list[RepositoryPayload]:
        ...


class ProgressRepository(Protocol):
    def initialize_progress(self, summary: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def get_progress(self, curriculum_id: str) -> RepositoryPayload | None:
        ...

    def update_topic_status(
        self,
        curriculum_id: str,
        week_number: int,
        topic_id: str | None,
        topic_name: str | None,
        status: str,
    ) -> RepositoryPayload | None:
        ...

    def append_event(
        self,
        curriculum_id: str,
        event: Mapping[str, Any],
    ) -> RepositoryPayload | None:
        ...

    def list_events(self, curriculum_id: str) -> list[RepositoryPayload]:
        ...


class QuizRepository(Protocol):
    def save_quiz(self, quiz: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def get_quiz(self, quiz_id: str) -> RepositoryPayload | None:
        ...

    def save_attempt(self, attempt: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def get_history(self, curriculum_id: str) -> list[RepositoryPayload]:
        ...

    def list_by_curriculum(self, curriculum_id: str) -> list[RepositoryPayload]:
        ...


class AdapterRepository(Protocol):
    def save_adaptation_result(self, result: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def get_adaptation_result(self, adaptation_id: str) -> RepositoryPayload | None:
        ...

    def get_history(self, curriculum_id: str) -> list[RepositoryPayload]:
        ...


class CriticRepository(Protocol):
    def save_review(self, review: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def get_latest_review(self, curriculum_id: str) -> RepositoryPayload | None:
        ...

    def list_reviews_for_curriculum(self, curriculum_id: str) -> list[RepositoryPayload]:
        ...


class ResourceRepository(Protocol):
    def upsert_resource(self, resource: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def list_catalog(self) -> list[RepositoryPayload]:
        ...

    def save_attachment(self, attachment: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def get_attachment_for_curriculum(self, curriculum_id: str) -> RepositoryPayload | None:
        ...


class EvaluationRepository(Protocol):
    def save_report(self, report: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def list_reports(self, dataset_name: str | None = None) -> list[RepositoryPayload]:
        ...

    def get_report(self, evaluation_id: str) -> RepositoryPayload | None:
        ...


class OrchestrationRepository(Protocol):
    def save_run_snapshot(self, snapshot: Mapping[str, Any]) -> RepositoryPayload:
        ...

    def get_run_snapshot(self, run_id: str) -> RepositoryPayload | None:
        ...

    def list_runs_for_curriculum(self, curriculum_id: str) -> list[RepositoryPayload]:
        ...
