from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import app.llm.fake_client as fake_client_module
from app.api.v1.dependencies import reset_api_container_for_tests
from app.core.settings import get_settings
from app.main import create_app
from app.schemas.knowledge_map import KnowledgeMapAgentOutput


@pytest.fixture
def auth_enabled_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "workspace-generation-test-secret-0123456789")
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    yield
    get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correcthorsebattery"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]  # type: ignore[no-any-return]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_workspace(
    client: TestClient,
    token: str,
    goal_text: str = "Learn classical guitar for a wedding performance",
):
    return client.post(
        "/api/v1/me/workspace",
        headers=_auth_header(token),
        json={"goal_text": goal_text},
    )


def _complete_assessment(client: TestClient, token: str) -> None:
    start = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))
    assessment_id = start.json()["assessment_session_id"]
    question_id = start.json()["current_question"]["question_id"]
    for _ in range(5):
        response = client.post(
            f"/api/v1/me/assessment/{assessment_id}/answer",
            headers=_auth_header(token),
            json={"question_id": question_id, "selected_options": [], "self_rating": 3},
        )
        next_question = response.json()["session"]["current_question"]
        if next_question is not None:
            question_id = next_question["question_id"]


def _goal_id_for_run(client: TestClient, token: str, run_id: str) -> str:
    dashboard = client.get(f"/api/v1/dashboard/{run_id}", headers=_auth_header(token)).json()
    return dashboard["goal_summary"]["goal_id"]  # type: ignore[no-any-return]


def _goal_status(client: TestClient, token: str, goal_id: str) -> str:
    # The same route frontend/app/goal/[goalId]/page.tsx reads goal.status
    # from, so this proves the lifecycle transition is observable end-to-end
    # through the real API, not just at the service layer in isolation.
    response = client.get(f"/api/v1/goals/{goal_id}", headers=_auth_header(token))
    assert response.status_code == 200
    return response.json()["status"]  # type: ignore[no-any-return]


def test_goal_status_advances_through_its_real_lifecycle(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    goal_text = "Learn classical guitar for a wedding performance"
    run_id = _create_workspace(client, token, goal_text=goal_text).json()["run_id"]
    goal_id = _goal_id_for_run(client, token, run_id)

    assert _goal_status(client, token, goal_id) == "created"

    start_response = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))
    assert start_response.status_code == 201
    assert _goal_status(client, token, goal_id) == "assessment_started"

    _complete_assessment(client, token)
    assert _goal_status(client, token, goal_id) == "assessment_started"

    generate_response = client.post(
        "/api/v1/me/workspace/generate",
        headers=_auth_header(token),
    )
    assert generate_response.status_code == 200
    assert _goal_status(client, token, goal_id) == "curriculum_generated"

    # Regeneration fires the same transition again - a real, current fact
    # each time - and must not regress to an earlier status.
    second_generate_response = client.post(
        "/api/v1/me/workspace/generate",
        headers=_auth_header(token),
    )
    assert second_generate_response.status_code == 200
    assert _goal_status(client, token, goal_id) == "curriculum_generated"


def test_generate_without_a_workspace_is_not_found(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")

    response = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert response.status_code == 404


def test_generate_before_assessment_completes_is_a_conflict(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)

    response = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert response.status_code == 409


def test_generate_before_assessment_seeds_no_demo_clone_content(
    auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    goal_text = "Learn classical guitar for a wedding performance"
    run_id = _create_workspace(client, token, goal_text=goal_text).json()["run_id"]

    dashboard_before = client.get(
        f"/api/v1/dashboard/{run_id}",
        headers=_auth_header(token),
    ).json()

    assert dashboard_before["goal_summary"]["text"] == goal_text
    assert dashboard_before["run_summary"]["status"] == "queued"
    artifact_ids = dashboard_before["navigation_summary"]["artifact_ids"]
    assert "knowledge_map_id" not in artifact_ids
    assert "curriculum_id" not in artifact_ids
    assert dashboard_before["knowledge_map_summary"] is None
    assert dashboard_before["curriculum_summary"] is None
    assert dashboard_before["quiz_summary"] is None
    assert dashboard_before["critic_summary"] is None
    assert dashboard_before["evaluation_summary"] is None
    assert dashboard_before["progress_summary"] is None
    assert dashboard_before["resources_summary"]["total_attached"] == 0


def test_generate_after_completed_assessment_creates_fresh_real_content(
    auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    goal_text = "Learn classical guitar for a wedding performance"
    run_id = _create_workspace(client, token, goal_text=goal_text).json()["run_id"]

    _complete_assessment(client, token)

    response = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    # Fresh IDs, never the canonical demo's.
    assert body["knowledge_map_id"] != "kmap_demo_rag"
    assert body["curriculum_id"] != "curriculum_demo_rag_v1"
    assert body["critic_review_id"] != "critic_demo_rag"
    assert body["evaluation_report_id"] != "eval_demo_rag"
    assert body["quiz_id"] != "quiz_demo_rag"
    # Step 10: generate() no longer fabricates a scored attempt - a fresh
    # quiz has no attempt until a real learner takes it.
    assert body["quiz_attempt_id"] is None

    dashboard_after = client.get(
        f"/api/v1/dashboard/{run_id}",
        headers=_auth_header(token),
    ).json()
    assert dashboard_after["assessment_summary"] is not None
    assert dashboard_after["goal_summary"]["text"] == goal_text
    assert dashboard_after["knowledge_map_summary"] is not None
    assert dashboard_after["curriculum_summary"] is not None
    artifact_ids = dashboard_after["navigation_summary"]["artifact_ids"]
    assert artifact_ids["knowledge_map_id"] == body["knowledge_map_id"]
    assert artifact_ids["curriculum_id"] == body["curriculum_id"]
    assert artifact_ids["critic_review_id"] == body["critic_review_id"]
    assert artifact_ids["evaluation_report_id"] == body["evaluation_report_id"]
    # quiz_id resolves independently of any attempt (dashboard.py looks the
    # quiz up directly by goal), while quiz_attempt_id stays honestly absent.
    assert artifact_ids["quiz_id"] == body["quiz_id"]
    assert "quiz_attempt_id" not in artifact_ids
    # Step 2: critic + evaluation are now real, derived from this workspace's
    # own knowledge map/curriculum (see test_critic_behavior.py for the
    # RAG-vocabulary-free unit check on the critic's own logic).
    critic_summary = dashboard_after["critic_summary"]
    assert critic_summary is not None
    assert 0.0 <= critic_summary["overall_score"] <= 1.0
    evaluation_summary = dashboard_after["evaluation_summary"]
    assert evaluation_summary is not None
    assert 0.0 <= evaluation_summary["overall_score"] <= 1.0
    # The evaluation report honestly carries no quiz_attempt_id either - no
    # real attempt exists yet (Step 10; same honest-absence pattern already
    # used for adaptation_event_id).
    evaluation_report = client.get(
        f"/api/v1/evaluations/{body['evaluation_report_id']}",
        headers=_auth_header(token),
    ).json()
    assert "quiz_attempt_id" not in evaluation_report["artifact_ids"]
    # Rebuild-37/Step 10: the quiz itself is still real, derived from this
    # workspace's own curriculum (see test_quiz_behavior.py for the
    # RAG-vocabulary-free unit check on the quiz agent's own logic), but its
    # dashboard tile stays honestly empty until a real attempt exists.
    assert dashboard_after["quiz_summary"] is None
    # Step 9: progress is now real too, built honestly with no quiz attempt
    # yet (see test_progress_behavior.py for the RAG-vocabulary-free unit
    # check on the progress agent's own logic).
    progress_summary = dashboard_after["progress_summary"]
    assert progress_summary is not None
    assert 0 <= progress_summary["completion_percentage"] <= 100
    assert artifact_ids["progress_state_id"]
    # Step 12: resources are now real too - this goal's curriculum collapses
    # to the deterministic fallback topic, but the corpus carries curated
    # guitar entries for exactly this goal (see
    # test_workspace_generate_persists_real_resource_attachments below for
    # the full proof). Adaptation stays honestly empty - its own future step.
    assert dashboard_after["resources_summary"]["total_attached"] > 0
    assert dashboard_after["adaptation_summary"]["recent_events"] == []


def test_workspace_generate_persists_real_resource_attachments(auth_enabled_app: None) -> None:
    """Big_Audit Step 12: generate() now wires `ResourceAgentService.attach()`
    for real, and the persisted attachments are reachable end-to-end through
    the real API - GET /resources/by-curriculum/{id} and the dashboard's
    resources summary - for a real, non-RAG goal matched against the curated
    corpus additions."""
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    goal_text = "Learn classical guitar for a wedding performance"
    run_id = _create_workspace(client, token, goal_text=goal_text).json()["run_id"]
    _complete_assessment(client, token)

    generate_response = client.post(
        "/api/v1/me/workspace/generate",
        headers=_auth_header(token),
    )
    assert generate_response.status_code == 200
    curriculum_id = generate_response.json()["curriculum_id"]

    attachments_response = client.get(
        f"/api/v1/resources/by-curriculum/{curriculum_id}",
        headers=_auth_header(token),
    )
    assert attachments_response.status_code == 200
    attachments = attachments_response.json()
    assert len(attachments) > 0
    assert all(attachment["curriculum_id"] == curriculum_id for attachment in attachments)
    resource_ids = {attachment["resource_id"] for attachment in attachments}
    assert "resource_guitar_fundamentals" in resource_ids
    # No RAG-corpus content leaked into this non-RAG goal's real matches.
    assert resource_ids.isdisjoint({"resource_rag_intro", "resource_retrieval_metrics"})

    dashboard = client.get(f"/api/v1/dashboard/{run_id}", headers=_auth_header(token)).json()
    assert dashboard["resources_summary"]["total_attached"] == len(attachments)

    # Regeneration overwrites the same goal-scoped attachment records rather
    # than duplicating them (create_or_replace, mirroring the
    # Progress/Critic regeneration-freshness fix).
    second_generate_response = client.post(
        "/api/v1/me/workspace/generate",
        headers=_auth_header(token),
    )
    assert second_generate_response.status_code == 200
    second_attachments = client.get(
        f"/api/v1/resources/by-curriculum/{curriculum_id}",
        headers=_auth_header(token),
    ).json()
    assert {a["attachment_id"] for a in second_attachments} == {
        a["attachment_id"] for a in attachments
    }


def test_workspace_generate_leaves_a_non_matching_goal_honestly_empty(
    auth_enabled_app: None,
) -> None:
    """The corpus-diversity decision (Big_Audit Step 12) is honestly narrow,
    not comprehensive: a goal with nothing curated for it gets zero
    attachments, never a fabricated placeholder match."""
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    goal_text = "Learn Mandarin calligraphy for a museum exhibit"
    run_id = _create_workspace(client, token, goal_text=goal_text).json()["run_id"]
    _complete_assessment(client, token)

    generate_response = client.post(
        "/api/v1/me/workspace/generate",
        headers=_auth_header(token),
    )
    assert generate_response.status_code == 200
    curriculum_id = generate_response.json()["curriculum_id"]

    attachments_response = client.get(
        f"/api/v1/resources/by-curriculum/{curriculum_id}",
        headers=_auth_header(token),
    )
    assert attachments_response.status_code == 200
    assert attachments_response.json() == []

    dashboard = client.get(f"/api/v1/dashboard/{run_id}", headers=_auth_header(token)).json()
    assert dashboard["resources_summary"]["total_attached"] == 0


def test_generate_is_callable_again_and_still_succeeds(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)
    _complete_assessment(client, token)

    first = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))
    second = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_regenerating_reuses_the_same_quiz_id_instead_of_duplicating(
    auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)
    _complete_assessment(client, token)

    first = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token)).json()
    second = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token)).json()

    # create_or_replace semantics: the same goal's quiz ID is reused and
    # overwritten in place on regeneration, never duplicated. Neither call
    # produces an attempt (Step 10).
    assert first["quiz_id"] == second["quiz_id"]
    assert first["quiz_attempt_id"] is None
    assert second["quiz_attempt_id"] is None


def test_get_progress_returns_real_data_after_generate(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    run_id = _create_workspace(client, token).json()["run_id"]
    _complete_assessment(client, token)

    generate_response = client.post(
        "/api/v1/me/workspace/generate",
        headers=_auth_header(token),
    )
    assert generate_response.status_code == 200

    dashboard = client.get(f"/api/v1/dashboard/{run_id}", headers=_auth_header(token)).json()
    progress_state_id = dashboard["navigation_summary"]["artifact_ids"]["progress_state_id"]
    assert progress_state_id

    progress_response = client.get(
        f"/api/v1/progress/{progress_state_id}",
        headers=_auth_header(token),
    )
    assert progress_response.status_code == 200
    progress_body = progress_response.json()
    assert progress_body["progress_state_id"] == progress_state_id
    assert len(progress_body["topic_progress"]) >= 1
    assert progress_body["status"] in {
        "not_started",
        "in_progress",
        "adaptation_needed",
        "completed",
    }
    progress_summary = dashboard["progress_summary"]
    assert progress_summary is not None
    assert progress_summary["completion_percentage"] == round(
        progress_body["overall_completion"] * 100,
    )

    # Regenerating must update the same progress record through the real
    # API, not create a second one - mirroring the service-layer proof in
    # test_progress_behavior.py.
    second_generate_response = client.post(
        "/api/v1/me/workspace/generate",
        headers=_auth_header(token),
    )
    assert second_generate_response.status_code == 200
    dashboard_after_regen = client.get(
        f"/api/v1/dashboard/{run_id}",
        headers=_auth_header(token),
    ).json()
    assert (
        dashboard_after_regen["navigation_summary"]["artifact_ids"]["progress_state_id"]
        == progress_state_id
    )


def test_workspace_generate_route_is_hidden_when_auth_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    client = TestClient(create_app())

    response = client.post("/api/v1/me/workspace/generate")

    assert response.status_code == 404
    get_settings.cache_clear()


def test_generate_without_any_llm_agent_carries_no_budget_summary(
    auth_enabled_app: None,
) -> None:
    """§17.1.4 surface (Big_Audit Step 4): a fully deterministic run touches no
    observer, so the field must stay null, not a fabricated empty summary."""
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)
    _complete_assessment(client, token)

    response = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert response.status_code == 200
    assert response.json()["llm_budget_summary"] is None


def test_generate_with_an_llm_agent_carries_a_redacted_budget_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "workspace-generation-test-secret-0123456789")
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "false")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    _augment_default_payloads(
        monkeypatch,
        {KnowledgeMapAgentOutput.__name__: _valid_knowledge_map_payload()},
    )
    get_settings.cache_clear()
    reset_api_container_for_tests()
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)
    _complete_assessment(client, token)

    response = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert response.status_code == 200
    summary = response.json()["llm_budget_summary"]
    assert summary is not None
    assert summary["llm_call_count"] >= 1
    assert summary["max_llm_calls"] == 16
    assert summary["max_wall_clock_seconds"] == 120.0
    assert summary["exhausted"] is False
    assert summary["exhaustion_reason"] is None
    # Redaction (RULES.md §7/§9): a genuinely secret-shaped value must never
    # reach this HTTP response, however it got constructed.
    assert "sk-" not in response.text
    assert "Bearer" not in response.text
    get_settings.cache_clear()


def _augment_default_payloads(
    monkeypatch: pytest.MonkeyPatch,
    extra: dict[str, object],
) -> None:
    original_default_payloads = fake_client_module._default_payloads

    def _augmented() -> dict[str, object]:
        payloads = original_default_payloads()
        payloads.update(extra)
        return payloads

    monkeypatch.setattr(fake_client_module, "_default_payloads", _augmented)


def _valid_knowledge_map_payload() -> dict[str, object]:
    return {
        "concepts": [
            {
                "concept_id": "workspace_generation_test_concept",
                "label": "Workspace generation test concept",
                "mastery_score": 0.3,
                "classification": "weak",
            },
        ],
        "strong_concepts": [],
        "developing_concepts": [],
        "weak_concepts": ["workspace_generation_test_concept"],
        "missing_concepts": [],
        "confidence": 0.6,
        "summary": "Workspace generation route test knowledge map summary.",
    }
