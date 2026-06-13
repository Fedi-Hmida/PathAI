from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from app.repositories.protocols import RepositoryPayload


def _copy_payload(payload: Mapping[str, Any]) -> RepositoryPayload:
    return deepcopy(dict(payload))


def _copy_optional(payload: RepositoryPayload | None) -> RepositoryPayload | None:
    if payload is None:
        return None
    return _copy_payload(payload)


def _payload_id(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    raise ValueError(f"Payload requires one of these id fields: {', '.join(keys)}.")


def _matches_limit(items: list[RepositoryPayload], limit: int) -> list[RepositoryPayload]:
    if limit <= 0:
        return []
    return [_copy_payload(item) for item in items[-limit:]]


class FakeAssessmentRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, RepositoryPayload] = {}
        self._order: list[str] = []

    def create_session(self, session: Mapping[str, Any]) -> RepositoryPayload:
        session_id = _payload_id(session, "session_id")
        payload = _copy_payload(session)
        if session_id not in self._sessions:
            self._order.append(session_id)
        self._sessions[session_id] = payload
        return _copy_payload(payload)

    def get_session(self, session_id: str) -> RepositoryPayload | None:
        return _copy_optional(self._sessions.get(session_id))

    def update_session(
        self,
        session_id: str,
        updates: Mapping[str, Any],
    ) -> RepositoryPayload | None:
        current = self._sessions.get(session_id)
        if current is None:
            return None
        current.update(_copy_payload(updates))
        return _copy_payload(current)

    def finalize_session(
        self,
        session_id: str,
        result: Mapping[str, Any] | None = None,
    ) -> RepositoryPayload | None:
        updates: RepositoryPayload = {"status": "completed"}
        if result is not None:
            updates["result"] = _copy_payload(result)
        return self.update_session(session_id, updates)

    def list_recent_sessions(self, limit: int = 20) -> list[RepositoryPayload]:
        return _matches_limit([self._sessions[key] for key in self._order], limit)

    def clear(self) -> None:
        self._sessions.clear()
        self._order.clear()


class FakeCurriculumRepository:
    def __init__(self) -> None:
        self._curricula: dict[str, RepositoryPayload] = {}
        self._order: list[str] = []

    def save_curriculum(self, curriculum: Mapping[str, Any]) -> RepositoryPayload:
        curriculum_id = _payload_id(curriculum, "curriculum_id")
        payload = _copy_payload(curriculum)
        if curriculum_id not in self._curricula:
            self._order.append(curriculum_id)
        self._curricula[curriculum_id] = payload
        return _copy_payload(payload)

    def get_curriculum(self, curriculum_id: str) -> RepositoryPayload | None:
        return _copy_optional(self._curricula.get(curriculum_id))

    def list_by_session(self, session_id: str) -> list[RepositoryPayload]:
        return [
            _copy_payload(curriculum)
            for curriculum in self._curricula.values()
            if curriculum.get("session_id") == session_id
            or curriculum.get("assessment_session_id") == session_id
        ]

    def list_recent_curricula(self, limit: int = 20) -> list[RepositoryPayload]:
        return _matches_limit([self._curricula[key] for key in self._order], limit)

    def clear(self) -> None:
        self._curricula.clear()
        self._order.clear()


class FakeProgressRepository:
    def __init__(self) -> None:
        self._summaries: dict[str, RepositoryPayload] = {}
        self._events: dict[str, list[RepositoryPayload]] = {}

    def initialize_progress(self, summary: Mapping[str, Any]) -> RepositoryPayload:
        curriculum_id = _payload_id(summary, "curriculum_id")
        payload = _copy_payload(summary)
        self._summaries[curriculum_id] = payload
        self._events[curriculum_id] = []
        for event in payload.get("events", []):
            if isinstance(event, Mapping):
                self._events[curriculum_id].append(_copy_payload(event))
        return _copy_payload(payload)

    def get_progress(self, curriculum_id: str) -> RepositoryPayload | None:
        return _copy_optional(self._summaries.get(curriculum_id))

    def update_topic_status(
        self,
        curriculum_id: str,
        week_number: int,
        topic_id: str | None,
        topic_name: str | None,
        status: str,
    ) -> RepositoryPayload | None:
        summary = self._summaries.get(curriculum_id)
        if summary is None:
            return None
        for week in _mapping_list(summary.get("weeks")):
            if week.get("week_number") != week_number:
                continue
            for topic in _mapping_list(week.get("topics")):
                topic_matches = (
                    topic_id is not None and topic.get("topic_id") == topic_id
                ) or (
                    topic_name is not None and topic.get("topic_name") == topic_name
                )
                if topic_matches:
                    topic["status"] = status
                    return _copy_payload(summary)
        return None

    def append_event(
        self,
        curriculum_id: str,
        event: Mapping[str, Any],
    ) -> RepositoryPayload | None:
        summary = self._summaries.get(curriculum_id)
        if summary is None:
            return None
        event_payload = _copy_payload(event)
        self._events.setdefault(curriculum_id, []).append(event_payload)
        events = summary.setdefault("events", [])
        if isinstance(events, list):
            events.append(_copy_payload(event_payload))
        return _copy_payload(summary)

    def list_events(self, curriculum_id: str) -> list[RepositoryPayload]:
        return [_copy_payload(event) for event in self._events.get(curriculum_id, [])]

    def clear(self) -> None:
        self._summaries.clear()
        self._events.clear()


class FakeQuizRepository:
    def __init__(self) -> None:
        self._quizzes: dict[str, RepositoryPayload] = {}
        self._attempts: dict[str, list[RepositoryPayload]] = {}

    def save_quiz(self, quiz: Mapping[str, Any]) -> RepositoryPayload:
        quiz_id = _payload_id(quiz, "quiz_id")
        payload = _copy_payload(quiz)
        self._quizzes[quiz_id] = payload
        return _copy_payload(payload)

    def get_quiz(self, quiz_id: str) -> RepositoryPayload | None:
        return _copy_optional(self._quizzes.get(quiz_id))

    def save_attempt(self, attempt: Mapping[str, Any]) -> RepositoryPayload:
        curriculum_id = _payload_id(attempt, "curriculum_id")
        payload = _copy_payload(attempt)
        self._attempts.setdefault(curriculum_id, []).append(payload)
        return _copy_payload(payload)

    def get_history(self, curriculum_id: str) -> list[RepositoryPayload]:
        return [_copy_payload(attempt) for attempt in self._attempts.get(curriculum_id, [])]

    def list_by_curriculum(self, curriculum_id: str) -> list[RepositoryPayload]:
        return [
            _copy_payload(quiz)
            for quiz in self._quizzes.values()
            if quiz.get("curriculum_id") == curriculum_id
        ]

    def clear(self) -> None:
        self._quizzes.clear()
        self._attempts.clear()


class FakeAdapterRepository:
    def __init__(self) -> None:
        self._results: dict[str, RepositoryPayload] = {}

    def save_adaptation_result(self, result: Mapping[str, Any]) -> RepositoryPayload:
        adaptation_id = _payload_id(result, "adaptation_id")
        payload = _copy_payload(result)
        self._results[adaptation_id] = payload
        return _copy_payload(payload)

    def get_adaptation_result(self, adaptation_id: str) -> RepositoryPayload | None:
        return _copy_optional(self._results.get(adaptation_id))

    def get_history(self, curriculum_id: str) -> list[RepositoryPayload]:
        return [
            _copy_payload(result)
            for result in self._results.values()
            if result.get("curriculum_id") == curriculum_id
        ]

    def clear(self) -> None:
        self._results.clear()


class FakeCriticRepository:
    def __init__(self) -> None:
        self._reviews: dict[str, list[RepositoryPayload]] = {}

    def save_review(self, review: Mapping[str, Any]) -> RepositoryPayload:
        curriculum_id = _payload_id(review, "curriculum_id")
        payload = _copy_payload(review)
        self._reviews.setdefault(curriculum_id, []).append(payload)
        return _copy_payload(payload)

    def get_latest_review(self, curriculum_id: str) -> RepositoryPayload | None:
        reviews = self._reviews.get(curriculum_id, [])
        if not reviews:
            return None
        return _copy_payload(reviews[-1])

    def list_reviews_for_curriculum(self, curriculum_id: str) -> list[RepositoryPayload]:
        return [_copy_payload(review) for review in self._reviews.get(curriculum_id, [])]

    def clear(self) -> None:
        self._reviews.clear()


class FakeResourceRepository:
    def __init__(self) -> None:
        self._resources: dict[str, RepositoryPayload] = {}
        self._attachments: dict[str, RepositoryPayload] = {}

    def upsert_resource(self, resource: Mapping[str, Any]) -> RepositoryPayload:
        resource_id = _payload_id(resource, "resource_id")
        payload = _copy_payload(resource)
        self._resources[resource_id] = payload
        return _copy_payload(payload)

    def list_catalog(self) -> list[RepositoryPayload]:
        return [_copy_payload(resource) for resource in self._resources.values()]

    def save_attachment(self, attachment: Mapping[str, Any]) -> RepositoryPayload:
        curriculum_id = _payload_id(attachment, "curriculum_id")
        payload = _copy_payload(attachment)
        self._attachments[curriculum_id] = payload
        return _copy_payload(payload)

    def get_attachment_for_curriculum(self, curriculum_id: str) -> RepositoryPayload | None:
        return _copy_optional(self._attachments.get(curriculum_id))

    def clear(self) -> None:
        self._resources.clear()
        self._attachments.clear()


class FakeEvaluationRepository:
    def __init__(self) -> None:
        self._reports: dict[str, RepositoryPayload] = {}
        self._order: list[str] = []

    def save_report(self, report: Mapping[str, Any]) -> RepositoryPayload:
        evaluation_id = _payload_id(report, "evaluation_id", "report_id")
        payload = _copy_payload(report)
        if evaluation_id not in self._reports:
            self._order.append(evaluation_id)
        self._reports[evaluation_id] = payload
        return _copy_payload(payload)

    def list_reports(self, dataset_name: str | None = None) -> list[RepositoryPayload]:
        reports = [self._reports[key] for key in self._order]
        if dataset_name is not None:
            reports = [report for report in reports if report.get("dataset_name") == dataset_name]
        return [_copy_payload(report) for report in reports]

    def get_report(self, evaluation_id: str) -> RepositoryPayload | None:
        return _copy_optional(self._reports.get(evaluation_id))

    def clear(self) -> None:
        self._reports.clear()
        self._order.clear()


class FakeOrchestrationRepository:
    def __init__(self) -> None:
        self._snapshots: dict[str, RepositoryPayload] = {}
        self._order: list[str] = []

    def save_run_snapshot(self, snapshot: Mapping[str, Any]) -> RepositoryPayload:
        run_id = _payload_id(snapshot, "run_id", "orchestration_id", "generation_job_id")
        payload = _copy_payload(snapshot)
        if run_id not in self._snapshots:
            self._order.append(run_id)
        self._snapshots[run_id] = payload
        return _copy_payload(payload)

    def get_run_snapshot(self, run_id: str) -> RepositoryPayload | None:
        return _copy_optional(self._snapshots.get(run_id))

    def list_runs_for_curriculum(self, curriculum_id: str) -> list[RepositoryPayload]:
        return [
            _copy_payload(snapshot)
            for snapshot in (self._snapshots[key] for key in self._order)
            if snapshot.get("curriculum_id") == curriculum_id
        ]

    def clear(self) -> None:
        self._snapshots.clear()
        self._order.clear()


def _mapping_list(value: object) -> list[RepositoryPayload]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
