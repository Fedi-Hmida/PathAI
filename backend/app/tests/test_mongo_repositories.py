from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

import pytest

from app.models import get_registered_model_names
from app.repositories import (
    REPOSITORY_BACKEND_ENV,
    FakeAssessmentRepository,
    MongoAdapterRepository,
    MongoAssessmentRepository,
    MongoCriticRepository,
    MongoCurriculumRepository,
    MongoEvaluationRepository,
    MongoProgressRepository,
    MongoQuizRepository,
    MongoResourceRepository,
    build_repository_bundle,
    configured_repository_backend,
    mongo,
)


class StoredDocument:
    def __init__(self, **fields: Any) -> None:
        self.id = None
        for key, value in fields.items():
            setattr(self, key, deepcopy(value))

    def model_dump(
        self,
        *,
        mode: str = "python",
        exclude: set[str] | None = None,
    ) -> dict[str, Any]:
        del mode
        excluded = exclude or set()
        return {
            key: deepcopy(value)
            for key, value in self.__dict__.items()
            if key not in excluded
        }


class MongoRepositoryHarness:
    def __init__(self) -> None:
        self.collections: dict[type[Any], list[StoredDocument]] = {}
        self.upserts: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    async def upsert_document(
        self,
        document_cls: type[Any],
        query: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> StoredDocument:
        stored_query = dict(query)
        stored_payload = deepcopy(dict(payload))
        self.upserts.append((document_cls.__name__, stored_query, stored_payload))
        existing = await self.find_one(document_cls, stored_query)
        if existing is None:
            document = StoredDocument(**stored_payload)
            self.collections.setdefault(document_cls, []).append(document)
            return document
        for key, value in stored_payload.items():
            setattr(existing, key, deepcopy(value))
        return existing

    async def find_one(
        self,
        document_cls: type[Any],
        query: Mapping[str, Any],
    ) -> StoredDocument | None:
        for document in self.collections.get(document_cls, []):
            if self._matches(document, query):
                return document
        return None

    async def find_many(
        self,
        document_cls: type[Any],
        query: Mapping[str, Any],
        *,
        sort_field: str | None = None,
        descending: bool = False,
        limit: int | None = None,
    ) -> list[StoredDocument]:
        documents = [
            document
            for document in self.collections.get(document_cls, [])
            if self._matches(document, query)
        ]
        if sort_field is not None:
            documents.sort(
                key=lambda document: getattr(document, sort_field, ""),
                reverse=descending,
            )
        if limit is not None:
            return documents[:limit]
        return documents

    async def replace_document(self, document: StoredDocument) -> StoredDocument:
        return document

    @staticmethod
    def _matches(document: StoredDocument, query: Mapping[str, Any]) -> bool:
        return all(getattr(document, key, None) == value for key, value in query.items())


@pytest.fixture()
def mongo_harness(monkeypatch: pytest.MonkeyPatch) -> MongoRepositoryHarness:
    harness = MongoRepositoryHarness()
    monkeypatch.setattr(mongo, "_upsert_document", harness.upsert_document)
    monkeypatch.setattr(mongo, "_find_one", harness.find_one)
    monkeypatch.setattr(mongo, "_find_many", harness.find_many)
    monkeypatch.setattr(mongo, "_replace_document", harness.replace_document)
    return harness


def test_persistence_document_models_are_registered() -> None:
    registered = set(get_registered_model_names())

    assert {
        "ProgressSummaryDocument",
        "QuizSnapshotDocument",
        "QuizAttemptDocument",
        "AdaptationResultDocument",
        "CriticReviewDocument",
        "ResourceAttachmentDocument",
        "EvaluationReportDocument",
    }.issubset(registered)


def test_repository_factory_defaults_to_fake_and_can_build_mongo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(REPOSITORY_BACKEND_ENV, raising=False)

    fake_bundle = build_repository_bundle()
    assert configured_repository_backend() == "fake"
    assert isinstance(fake_bundle.assessment, FakeAssessmentRepository)

    monkeypatch.setenv(REPOSITORY_BACKEND_ENV, "mongo")
    mongo_bundle = build_repository_bundle()

    assert configured_repository_backend() == "mongo"
    assert isinstance(mongo_bundle.assessment, MongoAssessmentRepository)
    assert isinstance(mongo_bundle.curriculum, MongoCurriculumRepository)
    assert isinstance(mongo_bundle.progress, MongoProgressRepository)
    assert isinstance(mongo_bundle.quiz, MongoQuizRepository)
    assert isinstance(mongo_bundle.adapter, MongoAdapterRepository)
    assert isinstance(mongo_bundle.critic, MongoCriticRepository)
    assert isinstance(mongo_bundle.resource, MongoResourceRepository)
    assert isinstance(mongo_bundle.evaluation, MongoEvaluationRepository)


def test_mongo_assessment_and_curriculum_repositories_round_trip(
    mongo_harness: MongoRepositoryHarness,
) -> None:
    assessment_repository = MongoAssessmentRepository()
    curriculum_repository = MongoCurriculumRepository()

    created = assessment_repository.create_session(
        {
            "session_id": "session-1",
            "goal": "Learn RAG systems",
            "timeline_weeks": 4,
            "hours_per_week": 6,
            "target_level": "intermediate",
            "question_index": 1,
            "max_questions": 3,
            "confidence_score": 0.0,
            "status": "in_progress",
            "current_difficulty": "beginner",
        }
    )
    updated = assessment_repository.update_session("session-1", {"confidence_score": 0.7})
    finalized = assessment_repository.finalize_session(
        "session-1",
        {"recommended_level": "intermediate"},
    )
    curriculum_repository.save_curriculum(
        {
            "curriculum_id": "curriculum-1",
            "assessment_session_id": "session-1",
            "goal": "Learn RAG systems",
            "timeline_weeks": 4,
            "hours_per_week": 6,
            "weeks": [],
        }
    )

    assert created["session_id"] == "session-1"
    assert updated is not None
    assert updated["confidence_score"] == 0.7
    assert finalized is not None
    assert finalized["status"] == "completed"
    assert finalized["result"] == {"recommended_level": "intermediate"}
    assert assessment_repository.get_session("session-1") is not None
    assert len(assessment_repository.list_recent_sessions()) == 1
    assert curriculum_repository.get_curriculum("curriculum-1") is not None
    assert curriculum_repository.list_by_session("session-1")[0]["curriculum_id"] == (
        "curriculum-1"
    )
    assert mongo_harness.upserts[0][0] == "AssessmentSessionDocument"


def test_mongo_progress_quiz_and_adapter_repositories_round_trip(
    mongo_harness: MongoRepositoryHarness,
) -> None:
    del mongo_harness
    progress_repository = MongoProgressRepository()
    quiz_repository = MongoQuizRepository()
    adapter_repository = MongoAdapterRepository()

    progress_repository.initialize_progress(
        {
            "curriculum_id": "curriculum-1",
            "weeks": [
                {
                    "week_number": 1,
                    "topics": [{"topic_id": "topic-1", "topic_name": "Embeddings"}],
                }
            ],
            "events": [{"event": "initialized"}],
        }
    )
    progress_repository.update_topic_status("curriculum-1", 1, "topic-1", None, "done")
    progress_repository.append_event("curriculum-1", {"event": "marked_done"})
    quiz_repository.save_quiz(
        {
            "quiz_id": "quiz-1",
            "curriculum_id": "curriculum-1",
            "questions": [{"question_id": "question-1"}],
        }
    )
    quiz_repository.save_attempt(
        {
            "quiz_id": "quiz-1",
            "curriculum_id": "curriculum-1",
            "attempt": {"attempt_id": "attempt-1"},
            "score": 0.8,
        }
    )
    adapter_repository.save_adaptation_result(
        {
            "adaptation_id": "adaptation-1",
            "curriculum_id": "curriculum-1",
            "decision": "replanned",
        }
    )

    progress = progress_repository.get_progress("curriculum-1")
    assert progress is not None
    assert progress["weeks"][0]["topics"][0]["status"] == "done"
    assert len(progress_repository.list_events("curriculum-1")) == 2
    assert quiz_repository.get_quiz("quiz-1") is not None
    assert quiz_repository.get_history("curriculum-1")[0]["score"] == 0.8
    assert quiz_repository.list_by_curriculum("curriculum-1")[0]["quiz_id"] == "quiz-1"
    assert adapter_repository.get_adaptation_result("adaptation-1") is not None
    assert adapter_repository.get_history("curriculum-1")[0]["decision"] == "replanned"


def test_mongo_critic_resource_and_evaluation_repositories_round_trip(
    mongo_harness: MongoRepositoryHarness,
) -> None:
    del mongo_harness
    critic_repository = MongoCriticRepository()
    resource_repository = MongoResourceRepository()
    evaluation_repository = MongoEvaluationRepository()

    assert critic_repository.get_latest_review("curriculum-1") is None
    assert resource_repository.get_attachment_for_curriculum("curriculum-1") is None
    assert evaluation_repository.get_report("evaluation-1") is None

    critic_repository.save_review(
        {"review_id": "review-1", "curriculum_id": "curriculum-1", "score": 0.7}
    )
    critic_repository.save_review(
        {"review_id": "review-2", "curriculum_id": "curriculum-1", "score": 0.9}
    )
    resource_repository.upsert_resource(
        {
            "resource_id": "resource-1",
            "title": "Sentence-BERT",
            "url": "https://example.invalid/sentence-bert",
            "type": "paper",
            "topics": ["Embeddings"],
            "subtopics": [],
            "difficulty": "intermediate",
            "estimated_minutes": 45,
            "source_name": "arXiv",
            "source_domain": "example.invalid",
            "quality_score": 0.9,
            "active": True,
        }
    )
    resource_repository.save_attachment(
        {
            "curriculum_id": "curriculum-1",
            "attachments": [{"topic": "Embeddings", "resource_id": "resource-1"}],
        }
    )
    evaluation_repository.save_report(
        {
            "evaluation_id": "evaluation-1",
            "dataset_name": "pathai_synthetic",
            "metric_count": 86,
        }
    )

    latest = critic_repository.get_latest_review("curriculum-1")
    assert latest is not None
    assert latest["review_id"] == "review-2"
    assert len(critic_repository.list_reviews_for_curriculum("curriculum-1")) == 2
    assert resource_repository.list_catalog()[0]["resource_id"] == "resource-1"
    assert resource_repository.get_attachment_for_curriculum("curriculum-1") is not None
    assert evaluation_repository.get_report("evaluation-1") is not None
    assert len(evaluation_repository.list_reports("pathai_synthetic")) == 1
    assert len(evaluation_repository.list_reports()) == 1
