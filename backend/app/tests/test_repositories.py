from app.repositories import (
    FakeAdapterRepository,
    FakeAssessmentRepository,
    FakeCriticRepository,
    FakeCurriculumRepository,
    FakeEvaluationRepository,
    FakeOrchestrationRepository,
    FakeProgressRepository,
    FakeQuizRepository,
    FakeResourceRepository,
)


def test_fake_assessment_repository_create_update_finalize_and_reset() -> None:
    repository = FakeAssessmentRepository()

    created = repository.create_session(
        {"session_id": "session-1", "goal": "Learn RAG", "status": "in_progress"}
    )
    created["goal"] = "mutated outside repository"
    updated = repository.update_session("session-1", {"confidence_score": 0.8})
    finalized = repository.finalize_session("session-1", {"recommended_level": "intermediate"})

    stored = repository.get_session("session-1")
    assert stored is not None
    assert stored["goal"] == "Learn RAG"
    assert updated is not None
    assert updated["confidence_score"] == 0.8
    assert finalized is not None
    assert finalized["status"] == "completed"
    assert finalized["result"] == {"recommended_level": "intermediate"}
    assert len(repository.list_recent_sessions()) == 1

    repository.clear()
    assert repository.get_session("session-1") is None


def test_fake_curriculum_repository_lists_by_session_and_recent_order() -> None:
    repository = FakeCurriculumRepository()

    repository.save_curriculum(
        {"curriculum_id": "curriculum-1", "session_id": "session-1", "goal": "RAG"}
    )
    repository.save_curriculum(
        {"curriculum_id": "curriculum-2", "session_id": "session-2", "goal": "CV"}
    )

    assert repository.get_curriculum("curriculum-1") is not None
    assert [item["curriculum_id"] for item in repository.list_by_session("session-1")] == [
        "curriculum-1"
    ]
    assert [item["curriculum_id"] for item in repository.list_recent_curricula(limit=1)] == [
        "curriculum-2"
    ]


def test_fake_progress_repository_updates_topics_and_appends_events() -> None:
    repository = FakeProgressRepository()

    repository.initialize_progress(
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
    updated = repository.update_topic_status("curriculum-1", 1, "topic-1", None, "done")
    with_event = repository.append_event(
        "curriculum-1",
        {"event": "marked_done", "topic_id": "topic-1"},
    )

    assert updated is not None
    assert updated["weeks"][0]["topics"][0]["status"] == "done"
    assert with_event is not None
    assert len(repository.list_events("curriculum-1")) == 2


def test_fake_quiz_repository_tracks_quizzes_and_attempt_history() -> None:
    repository = FakeQuizRepository()

    repository.save_quiz({"quiz_id": "quiz-1", "curriculum_id": "curriculum-1"})
    repository.save_attempt(
        {
            "quiz_id": "quiz-1",
            "curriculum_id": "curriculum-1",
            "score": 0.75,
        }
    )

    assert repository.get_quiz("quiz-1") is not None
    assert len(repository.list_by_curriculum("curriculum-1")) == 1
    assert repository.get_history("curriculum-1")[0]["score"] == 0.75


def test_fake_adapter_repository_tracks_adaptation_history() -> None:
    repository = FakeAdapterRepository()

    repository.save_adaptation_result(
        {
            "adaptation_id": "adaptation-1",
            "curriculum_id": "curriculum-1",
            "decision": "replanned",
        }
    )

    assert repository.get_adaptation_result("adaptation-1") is not None
    assert len(repository.get_history("curriculum-1")) == 1


def test_fake_critic_repository_returns_latest_review() -> None:
    repository = FakeCriticRepository()

    repository.save_review(
        {"review_id": "review-1", "curriculum_id": "curriculum-1", "score": 0.62}
    )
    repository.save_review(
        {"review_id": "review-2", "curriculum_id": "curriculum-1", "score": 0.88}
    )

    latest = repository.get_latest_review("curriculum-1")
    assert latest is not None
    assert latest["review_id"] == "review-2"
    assert len(repository.list_reviews_for_curriculum("curriculum-1")) == 2


def test_fake_resource_repository_tracks_catalog_and_attachments() -> None:
    repository = FakeResourceRepository()

    repository.upsert_resource({"resource_id": "resource-1", "title": "Sentence-BERT"})
    repository.save_attachment(
        {
            "curriculum_id": "curriculum-1",
            "attachments": [{"topic": "Embeddings", "resource_id": "resource-1"}],
        }
    )

    assert repository.list_catalog()[0]["title"] == "Sentence-BERT"
    assert repository.get_attachment_for_curriculum("curriculum-1") is not None


def test_fake_evaluation_repository_lists_reports_by_dataset() -> None:
    repository = FakeEvaluationRepository()

    repository.save_report(
        {"evaluation_id": "evaluation-1", "dataset_name": "pathai_synthetic"}
    )
    repository.save_report({"evaluation_id": "evaluation-2", "dataset_name": "other"})

    assert repository.get_report("evaluation-1") is not None
    assert len(repository.list_reports("pathai_synthetic")) == 1
    assert len(repository.list_reports()) == 2


def test_fake_orchestration_repository_lists_runs_by_curriculum() -> None:
    repository = FakeOrchestrationRepository()

    repository.save_run_snapshot(
        {
            "run_id": "run-1",
            "curriculum_id": "curriculum-1",
            "steps_completed": 10,
        }
    )

    assert repository.get_run_snapshot("run-1") is not None
    assert len(repository.list_runs_for_curriculum("curriculum-1")) == 1
