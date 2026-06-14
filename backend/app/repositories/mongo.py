import asyncio
from collections.abc import Coroutine, Mapping
from copy import deepcopy
from threading import Thread
from typing import Any, TypeVar, cast

from beanie import Document

from app.assessment.models import AssessmentSessionDocument
from app.curriculum.models import CurriculumDocument
from app.models.persistence import (
    AdaptationResultDocument,
    CriticReviewDocument,
    EvaluationReportDocument,
    ProgressSummaryDocument,
    QuizAttemptDocument,
    QuizSnapshotDocument,
    ResourceAttachmentDocument,
)
from app.models.resource import ResourceDocument
from app.repositories.protocols import RepositoryPayload

DocumentT = TypeVar("DocumentT", bound=Document)
AsyncResultT = TypeVar("AsyncResultT")


def _copy_payload(payload: Mapping[str, Any]) -> RepositoryPayload:
    return deepcopy(dict(payload))


def _payload_id(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    raise ValueError(f"Payload requires one of these id fields: {', '.join(keys)}.")


def _document_payload(document: Document, *, exclude: set[str] | None = None) -> RepositoryPayload:
    excluded = {"id"}
    if exclude is not None:
        excluded.update(exclude)
    return cast(RepositoryPayload, document.model_dump(mode="json", exclude=excluded))


def _stored_payload(document: Document) -> RepositoryPayload:
    payload = getattr(document, "payload", None)
    if isinstance(payload, Mapping):
        return _copy_payload(payload)
    return _document_payload(document)


def _run_async(coro: Coroutine[Any, Any, AsyncResultT]) -> AsyncResultT:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, object] = {}

    def runner() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except BaseException as exc:  # pragma: no cover - defensive thread bridge
            result["error"] = exc

    thread = Thread(target=runner)
    thread.start()
    thread.join()
    if "error" in result:
        raise cast(BaseException, result["error"])
    return cast(AsyncResultT, result.get("value"))


async def _find_one(document_cls: type[DocumentT], query: Mapping[str, Any]) -> DocumentT | None:
    return await document_cls.find_one(dict(query))


async def _find_many(
    document_cls: type[DocumentT],
    query: Mapping[str, Any],
    *,
    sort_field: str | None = None,
    descending: bool = False,
    limit: int | None = None,
) -> list[DocumentT]:
    finder = document_cls.find(dict(query))
    if sort_field is not None:
        finder = finder.sort(f"-{sort_field}" if descending else sort_field)
    if limit is not None:
        finder = finder.limit(limit)
    return await finder.to_list()


async def _insert_document(document: DocumentT) -> DocumentT:
    return await document.insert()


async def _replace_document(document: DocumentT) -> DocumentT:
    return await document.replace()


def _set_document_fields(document: Document, payload: Mapping[str, Any]) -> None:
    for key, value in payload.items():
        setattr(document, key, deepcopy(value))


async def _upsert_document(
    document_cls: type[DocumentT],
    query: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> DocumentT:
    existing = await _find_one(document_cls, query)
    if existing is None:
        return await _insert_document(document_cls(**dict(payload)))
    _set_document_fields(existing, payload)
    return await _replace_document(existing)


class MongoAssessmentRepository:
    def create_session(self, session: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._save_session(session))

    def get_session(self, session_id: str) -> RepositoryPayload | None:
        return _run_async(self._get_session(session_id))

    def update_session(
        self,
        session_id: str,
        updates: Mapping[str, Any],
    ) -> RepositoryPayload | None:
        return _run_async(self._update_session(session_id, updates))

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
        return _run_async(self._list_recent_sessions(limit))

    async def _save_session(self, session: Mapping[str, Any]) -> RepositoryPayload:
        session_id = _payload_id(session, "session_id")
        document = await _upsert_document(
            AssessmentSessionDocument,
            {"session_id": session_id},
            session,
        )
        return _document_payload(document)

    async def _get_session(self, session_id: str) -> RepositoryPayload | None:
        document = await _find_one(AssessmentSessionDocument, {"session_id": session_id})
        return _document_payload(document) if document is not None else None

    async def _update_session(
        self,
        session_id: str,
        updates: Mapping[str, Any],
    ) -> RepositoryPayload | None:
        document = await _find_one(AssessmentSessionDocument, {"session_id": session_id})
        if document is None:
            return None
        _set_document_fields(document, updates)
        updated = await _replace_document(document)
        return _document_payload(updated)

    async def _list_recent_sessions(self, limit: int) -> list[RepositoryPayload]:
        documents = await _find_many(
            AssessmentSessionDocument,
            {},
            sort_field="created_at",
            descending=True,
            limit=max(limit, 0),
        )
        return [_document_payload(document) for document in documents]


class MongoCurriculumRepository:
    def save_curriculum(self, curriculum: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._save_curriculum(curriculum))

    def get_curriculum(self, curriculum_id: str) -> RepositoryPayload | None:
        return _run_async(self._get_curriculum(curriculum_id))

    def list_by_session(self, session_id: str) -> list[RepositoryPayload]:
        return _run_async(self._list_by_session(session_id))

    def list_recent_curricula(self, limit: int = 20) -> list[RepositoryPayload]:
        return _run_async(self._list_recent_curricula(limit))

    async def _save_curriculum(self, curriculum: Mapping[str, Any]) -> RepositoryPayload:
        curriculum_id = _payload_id(curriculum, "curriculum_id")
        document = await _upsert_document(
            CurriculumDocument,
            {"curriculum_id": curriculum_id},
            curriculum,
        )
        return _document_payload(document)

    async def _get_curriculum(self, curriculum_id: str) -> RepositoryPayload | None:
        document = await _find_one(CurriculumDocument, {"curriculum_id": curriculum_id})
        return _document_payload(document) if document is not None else None

    async def _list_by_session(self, session_id: str) -> list[RepositoryPayload]:
        documents = await _find_many(
            CurriculumDocument,
            {"assessment_session_id": session_id},
            sort_field="created_at",
            descending=True,
        )
        return [_document_payload(document) for document in documents]

    async def _list_recent_curricula(self, limit: int) -> list[RepositoryPayload]:
        documents = await _find_many(
            CurriculumDocument,
            {},
            sort_field="created_at",
            descending=True,
            limit=max(limit, 0),
        )
        return [_document_payload(document) for document in documents]


class MongoProgressRepository:
    def initialize_progress(self, summary: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._save_summary(summary))

    def get_progress(self, curriculum_id: str) -> RepositoryPayload | None:
        return _run_async(self._get_progress(curriculum_id))

    def update_topic_status(
        self,
        curriculum_id: str,
        week_number: int,
        topic_id: str | None,
        topic_name: str | None,
        status: str,
    ) -> RepositoryPayload | None:
        return _run_async(
            self._update_topic_status(
                curriculum_id,
                week_number,
                topic_id,
                topic_name,
                status,
            )
        )

    def append_event(
        self,
        curriculum_id: str,
        event: Mapping[str, Any],
    ) -> RepositoryPayload | None:
        return _run_async(self._append_event(curriculum_id, event))

    def list_events(self, curriculum_id: str) -> list[RepositoryPayload]:
        progress = self.get_progress(curriculum_id)
        if progress is None:
            return []
        events = progress.get("events", [])
        return [_copy_payload(event) for event in events if isinstance(event, Mapping)]

    async def _save_summary(self, summary: Mapping[str, Any]) -> RepositoryPayload:
        curriculum_id = _payload_id(summary, "curriculum_id")
        payload = _copy_payload(summary)
        document = await _upsert_document(
            ProgressSummaryDocument,
            {"curriculum_id": curriculum_id},
            {"curriculum_id": curriculum_id, "payload": payload},
        )
        return _stored_payload(document)

    async def _get_progress(self, curriculum_id: str) -> RepositoryPayload | None:
        document = await _find_one(ProgressSummaryDocument, {"curriculum_id": curriculum_id})
        return _stored_payload(document) if document is not None else None

    async def _update_topic_status(
        self,
        curriculum_id: str,
        week_number: int,
        topic_id: str | None,
        topic_name: str | None,
        status: str,
    ) -> RepositoryPayload | None:
        document = await _find_one(ProgressSummaryDocument, {"curriculum_id": curriculum_id})
        if document is None:
            return None
        payload = _stored_payload(document)
        for week in _mapping_list(payload.get("weeks")):
            if week.get("week_number") != week_number:
                continue
            for topic in _mapping_list(week.get("topics")):
                matches_id = topic_id is not None and topic.get("topic_id") == topic_id
                matches_name = topic_name is not None and topic.get("topic_name") == topic_name
                if matches_id or matches_name:
                    topic["status"] = status
                    document.payload = payload
                    await _replace_document(document)
                    return _copy_payload(payload)
        return None

    async def _append_event(
        self,
        curriculum_id: str,
        event: Mapping[str, Any],
    ) -> RepositoryPayload | None:
        document = await _find_one(ProgressSummaryDocument, {"curriculum_id": curriculum_id})
        if document is None:
            return None
        payload = _stored_payload(document)
        events = payload.setdefault("events", [])
        if isinstance(events, list):
            events.append(_copy_payload(event))
        document.payload = payload
        await _replace_document(document)
        return _copy_payload(payload)


class MongoQuizRepository:
    def save_quiz(self, quiz: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._save_quiz(quiz))

    def get_quiz(self, quiz_id: str) -> RepositoryPayload | None:
        return _run_async(self._get_quiz(quiz_id))

    def save_attempt(self, attempt: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._save_attempt(attempt))

    def get_history(self, curriculum_id: str) -> list[RepositoryPayload]:
        return _run_async(self._get_history(curriculum_id))

    def list_by_curriculum(self, curriculum_id: str) -> list[RepositoryPayload]:
        return _run_async(self._list_by_curriculum(curriculum_id))

    async def _save_quiz(self, quiz: Mapping[str, Any]) -> RepositoryPayload:
        quiz_id = _payload_id(quiz, "quiz_id")
        curriculum_id = _payload_id(quiz, "curriculum_id")
        payload = _copy_payload(quiz)
        document = await _upsert_document(
            QuizSnapshotDocument,
            {"quiz_id": quiz_id},
            {"quiz_id": quiz_id, "curriculum_id": curriculum_id, "payload": payload},
        )
        return _stored_payload(document)

    async def _get_quiz(self, quiz_id: str) -> RepositoryPayload | None:
        document = await _find_one(QuizSnapshotDocument, {"quiz_id": quiz_id})
        return _stored_payload(document) if document is not None else None

    async def _save_attempt(self, attempt: Mapping[str, Any]) -> RepositoryPayload:
        attempt_payload = _copy_payload(attempt)
        attempt_data = attempt_payload.get("attempt")
        attempt_id = _payload_id(
            attempt_data if isinstance(attempt_data, Mapping) else attempt_payload,
            "attempt_id",
        )
        quiz_id = _payload_id(attempt_payload, "quiz_id")
        curriculum_id = _payload_id(attempt_payload, "curriculum_id")
        document = await _upsert_document(
            QuizAttemptDocument,
            {"attempt_id": attempt_id},
            {
                "attempt_id": attempt_id,
                "quiz_id": quiz_id,
                "curriculum_id": curriculum_id,
                "payload": attempt_payload,
            },
        )
        return _stored_payload(document)

    async def _get_history(self, curriculum_id: str) -> list[RepositoryPayload]:
        documents = await _find_many(
            QuizAttemptDocument,
            {"curriculum_id": curriculum_id},
            sort_field="submitted_at",
            descending=False,
        )
        return [_stored_payload(document) for document in documents]

    async def _list_by_curriculum(self, curriculum_id: str) -> list[RepositoryPayload]:
        documents = await _find_many(
            QuizSnapshotDocument,
            {"curriculum_id": curriculum_id},
            sort_field="created_at",
            descending=False,
        )
        return [_stored_payload(document) for document in documents]


class MongoAdapterRepository:
    def save_adaptation_result(self, result: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._save_result(result))

    def get_adaptation_result(self, adaptation_id: str) -> RepositoryPayload | None:
        return _run_async(self._get_result(adaptation_id))

    def get_history(self, curriculum_id: str) -> list[RepositoryPayload]:
        return _run_async(self._get_history(curriculum_id))

    async def _save_result(self, result: Mapping[str, Any]) -> RepositoryPayload:
        adaptation_id = _payload_id(result, "adaptation_id")
        curriculum_id = _payload_id(result, "curriculum_id")
        payload = _copy_payload(result)
        document = await _upsert_document(
            AdaptationResultDocument,
            {"adaptation_id": adaptation_id},
            {
                "adaptation_id": adaptation_id,
                "curriculum_id": curriculum_id,
                "payload": payload,
            },
        )
        return _stored_payload(document)

    async def _get_result(self, adaptation_id: str) -> RepositoryPayload | None:
        document = await _find_one(
            AdaptationResultDocument,
            {"adaptation_id": adaptation_id},
        )
        return _stored_payload(document) if document is not None else None

    async def _get_history(self, curriculum_id: str) -> list[RepositoryPayload]:
        documents = await _find_many(
            AdaptationResultDocument,
            {"curriculum_id": curriculum_id},
            sort_field="created_at",
            descending=False,
        )
        return [_stored_payload(document) for document in documents]


class MongoCriticRepository:
    def save_review(self, review: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._save_review(review))

    def get_latest_review(self, curriculum_id: str) -> RepositoryPayload | None:
        reviews = self.list_reviews_for_curriculum(curriculum_id)
        return reviews[-1] if reviews else None

    def list_reviews_for_curriculum(self, curriculum_id: str) -> list[RepositoryPayload]:
        return _run_async(self._list_reviews(curriculum_id))

    async def _save_review(self, review: Mapping[str, Any]) -> RepositoryPayload:
        review_id = _payload_id(review, "review_id")
        curriculum_id = _payload_id(review, "curriculum_id")
        payload = _copy_payload(review)
        document = await _upsert_document(
            CriticReviewDocument,
            {"review_id": review_id},
            {"review_id": review_id, "curriculum_id": curriculum_id, "payload": payload},
        )
        return _stored_payload(document)

    async def _list_reviews(self, curriculum_id: str) -> list[RepositoryPayload]:
        documents = await _find_many(
            CriticReviewDocument,
            {"curriculum_id": curriculum_id},
            sort_field="created_at",
            descending=False,
        )
        return [_stored_payload(document) for document in documents]


class MongoResourceRepository:
    def upsert_resource(self, resource: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._upsert_resource(resource))

    def list_catalog(self) -> list[RepositoryPayload]:
        return _run_async(self._list_catalog())

    def save_attachment(self, attachment: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._save_attachment(attachment))

    def get_attachment_for_curriculum(self, curriculum_id: str) -> RepositoryPayload | None:
        return _run_async(self._get_attachment(curriculum_id))

    async def _upsert_resource(self, resource: Mapping[str, Any]) -> RepositoryPayload:
        resource_id = _payload_id(resource, "resource_id")
        document = await _upsert_document(
            ResourceDocument,
            {"resource_id": resource_id},
            resource,
        )
        return _document_payload(document)

    async def _list_catalog(self) -> list[RepositoryPayload]:
        documents = await _find_many(
            ResourceDocument,
            {"active": True},
            sort_field="quality_score",
            descending=True,
        )
        return [_document_payload(document) for document in documents]

    async def _save_attachment(self, attachment: Mapping[str, Any]) -> RepositoryPayload:
        curriculum_id = _payload_id(attachment, "curriculum_id")
        payload = _copy_payload(attachment)
        document = await _upsert_document(
            ResourceAttachmentDocument,
            {"curriculum_id": curriculum_id},
            {"curriculum_id": curriculum_id, "payload": payload},
        )
        return _stored_payload(document)

    async def _get_attachment(self, curriculum_id: str) -> RepositoryPayload | None:
        document = await _find_one(
            ResourceAttachmentDocument,
            {"curriculum_id": curriculum_id},
        )
        return _stored_payload(document) if document is not None else None


class MongoEvaluationRepository:
    def save_report(self, report: Mapping[str, Any]) -> RepositoryPayload:
        return _run_async(self._save_report(report))

    def list_reports(self, dataset_name: str | None = None) -> list[RepositoryPayload]:
        return _run_async(self._list_reports(dataset_name))

    def get_report(self, evaluation_id: str) -> RepositoryPayload | None:
        return _run_async(self._get_report(evaluation_id))

    async def _save_report(self, report: Mapping[str, Any]) -> RepositoryPayload:
        evaluation_id = _payload_id(report, "evaluation_id", "report_id")
        dataset_name = _payload_id(report, "dataset_name")
        payload = _copy_payload(report)
        document = await _upsert_document(
            EvaluationReportDocument,
            {"evaluation_id": evaluation_id},
            {
                "evaluation_id": evaluation_id,
                "dataset_name": dataset_name,
                "payload": payload,
            },
        )
        return _stored_payload(document)

    async def _list_reports(self, dataset_name: str | None) -> list[RepositoryPayload]:
        query = {"dataset_name": dataset_name} if dataset_name is not None else {}
        documents = await _find_many(
            EvaluationReportDocument,
            query,
            sort_field="created_at",
            descending=True,
        )
        return [_stored_payload(document) for document in documents]

    async def _get_report(self, evaluation_id: str) -> RepositoryPayload | None:
        document = await _find_one(EvaluationReportDocument, {"evaluation_id": evaluation_id})
        return _stored_payload(document) if document is not None else None


def _mapping_list(value: object) -> list[RepositoryPayload]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
