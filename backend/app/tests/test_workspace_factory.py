from __future__ import annotations

import json

from app.fixtures import canonical_demo as demo
from app.fixtures.workspace_factory import build_user_workspace
from app.schemas.enums import GoalStatus, OrchestrationRunStatus

OWNER_A = "user_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OWNER_B = "user_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
GOAL_TEXT = "Learn watercolor painting for a small gallery show"


def test_workspace_ids_are_fresh_not_the_canonical_demos() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.goal.goal_id != demo.GOAL_ID
    assert ws.run.run_id != demo.RUN_ID
    # New IDs keep their type prefix.
    assert ws.goal.goal_id.startswith("goal_")
    assert ws.run.run_id.startswith("run_")


def test_goal_text_is_the_callers_own_not_the_demos() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.goal.goal_text == GOAL_TEXT
    assert ws.goal.goal_text != demo.LEARNING_GOAL.goal_text
    assert GOAL_TEXT in ws.goal.normalized_goal_text


def test_learner_profile_defaults_to_neutral_not_the_demos_rag_specific_one() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.goal.learner_profile.weak_areas == []
    assert ws.goal.learner_profile.strengths == []
    assert ws.goal.learner_profile.weak_areas != demo.LEARNING_GOAL.learner_profile.weak_areas


def test_owner_is_stamped_on_roots_only() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.goal.owner_user_id == OWNER_A
    assert ws.run.owner_user_id == OWNER_A


def test_two_workspaces_never_share_ids() -> None:
    a = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)
    b = build_user_workspace(OWNER_B, goal_text=GOAL_TEXT)

    assert a.goal.goal_id != b.goal.goal_id
    assert a.run.run_id != b.run.run_id


def test_run_points_at_this_workspaces_own_goal() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.run.goal_id == ws.goal.goal_id
    assert ws.run_id == ws.run.run_id
    assert ws.goal_id == ws.goal.goal_id


def test_seeded_run_is_honest_not_a_fabricated_completed_pipeline() -> None:
    """A freshly seeded workspace must not claim a finished pipeline: no
    completed nodes, no artifact IDs, not COMPLETED status - see provenance
    audit finding B5."""
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.run.status == OrchestrationRunStatus.CREATED
    assert ws.run.completed_nodes == []
    assert ws.run.artifact_ids == {}
    assert ws.run.completed_at is None


def test_seeded_goal_is_honest_not_active_or_demo_tagged() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.goal.status == GoalStatus.CREATED
    assert ws.goal.demo_seed_id is None


def test_no_canonical_demo_id_survives_anywhere_in_the_seed() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    blob = json.dumps([ws.goal.model_dump(mode="json"), ws.run.model_dump(mode="json")])

    canonical_ids = {
        demo.GOAL_ID,
        demo.RUN_ID,
        demo.ASSESSMENT_ID,
        demo.KNOWLEDGE_MAP_ID,
        demo.CURRICULUM_ID,
        demo.PROGRESS_ID,
        demo.QUIZ_ID,
        demo.QUIZ_ATTEMPT_ID,
        demo.ADAPTATION_ID,
        demo.CRITIC_REVIEW_ID,
        demo.EVALUATION_REPORT_ID,
    }
    for canonical_id in canonical_ids:
        assert canonical_id not in blob, f"stale canonical id leaked into seed: {canonical_id}"

    # No RAG-flavored vocabulary from the demo goal/learner profile either.
    assert "RAG" not in blob
    assert "rag_systems" not in blob
    assert "vector_search" not in blob
