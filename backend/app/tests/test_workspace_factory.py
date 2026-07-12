from __future__ import annotations

import json

from app.fixtures import canonical_demo as demo
from app.fixtures.workspace_factory import build_user_workspace

# Every workspace-scoped ID that appears in the canonical demo. If the clone
# leaves any of these behind, isolation is broken.
_CANONICAL_WORKSPACE_IDS = {
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

OWNER_A = "user_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OWNER_B = "user_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
GOAL_TEXT = "Learn watercolor painting for a small gallery show"


def test_workspace_ids_differ_from_canonical_demo() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.goal.goal_id != demo.GOAL_ID
    assert ws.run.run_id != demo.RUN_ID
    assert ws.knowledge_map.knowledge_map_id != demo.KNOWLEDGE_MAP_ID
    assert ws.curriculum.curriculum_id != demo.CURRICULUM_ID
    # New IDs keep their type prefix.
    assert ws.goal.goal_id.startswith("goal_")
    assert ws.run.run_id.startswith("run_")
    assert ws.knowledge_map.knowledge_map_id.startswith("kmap_")


def test_goal_text_is_the_callers_own_not_the_demos() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.goal.goal_text == GOAL_TEXT
    assert ws.goal.goal_text != demo.LEARNING_GOAL.goal_text
    assert GOAL_TEXT in ws.goal.normalized_goal_text


def test_owner_is_stamped_on_roots_only() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    assert ws.goal.owner_user_id == OWNER_A
    assert ws.run.owner_user_id == OWNER_A


def test_two_workspaces_never_share_workspace_ids() -> None:
    a = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)
    b = build_user_workspace(OWNER_B, goal_text=GOAL_TEXT)

    assert a.goal.goal_id != b.goal.goal_id
    assert a.run.run_id != b.run.run_id
    assert a.curriculum.curriculum_id != b.curriculum.curriculum_id
    assert a.quiz.quiz_id != b.quiz.quiz_id


def test_cross_references_stay_internally_consistent() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    # The whole graph must point at this workspace's own goal/run/curriculum.
    assert ws.run.goal_id == ws.goal.goal_id
    assert ws.curriculum.goal_id == ws.goal.goal_id
    assert ws.curriculum.run_id == ws.run.run_id
    assert ws.curriculum.knowledge_map_id == ws.knowledge_map.knowledge_map_id
    assert ws.knowledge_map.goal_id == ws.goal.goal_id
    assert ws.progress_state.goal_id == ws.goal.goal_id
    assert ws.progress_state.curriculum_id == ws.curriculum.curriculum_id
    assert ws.quiz.goal_id == ws.goal.goal_id
    assert ws.quiz.curriculum_id == ws.curriculum.curriculum_id
    assert ws.quiz_attempt.quiz_id == ws.quiz.quiz_id
    assert ws.critic_review.curriculum_id == ws.curriculum.curriculum_id
    assert ws.evaluation_report.goal_id == ws.goal.goal_id
    # The run's artifact_ids dict values are remapped to the new IDs too.
    assert ws.run.artifact_ids["curriculum_id"] == ws.curriculum.curriculum_id
    assert ws.run.artifact_ids["quiz_id"] == ws.quiz.quiz_id


def test_resource_attachments_point_at_this_curriculum_but_shared_corpus() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)
    canonical_resource_ids = {resource.resource_id for resource in demo.RESOURCE_CORPUS}

    for attachment in ws.resource_attachments:
        assert attachment.curriculum_id == ws.curriculum.curriculum_id
        assert attachment.goal_id == ws.goal.goal_id
        assert attachment.attachment_id.startswith("attach_")
        # resource_id references the SHARED corpus and must be unchanged.
        assert attachment.resource_id in canonical_resource_ids


def test_no_canonical_workspace_id_survives_anywhere_in_the_clone() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    blob = json.dumps(
        [
            ws.goal.model_dump(mode="json"),
            ws.run.model_dump(mode="json"),
            ws.knowledge_map.model_dump(mode="json"),
            ws.curriculum.model_dump(mode="json"),
            *[a.model_dump(mode="json") for a in ws.resource_attachments],
            ws.progress_state.model_dump(mode="json"),
            ws.quiz.model_dump(mode="json"),
            ws.quiz_attempt.model_dump(mode="json"),
            ws.adaptation_event.model_dump(mode="json"),
            ws.critic_review.model_dump(mode="json"),
            ws.evaluation_report.model_dump(mode="json"),
        ]
    )

    for canonical_id in _CANONICAL_WORKSPACE_IDS:
        assert canonical_id not in blob, f"stale canonical id leaked into clone: {canonical_id}"


def test_enum_values_and_node_names_are_not_rewritten() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)

    # A prior naive implementation rewrote strings that merely shared an ID
    # prefix. The adaptation trigger enum and the run's node names must be
    # preserved verbatim.
    assert ws.adaptation_event.trigger_type == demo.ADAPTATION_EVENT.trigger_type
    # "goal_loaded"/"curriculum_loaded" etc. share ID prefixes but are node
    # names, not IDs, and must be left intact.
    assert ws.run.completed_nodes == [
        "goal_loaded",
        "assessment_loaded",
        "knowledge_map_loaded",
        "curriculum_loaded",
        "dashboard_loaded",
    ]


def test_concept_ids_and_topic_links_survive_cloning() -> None:
    ws = build_user_workspace(OWNER_A, goal_text=GOAL_TEXT)
    canonical_concepts = {concept.concept_id for concept in demo.KNOWLEDGE_MAP.concepts}

    # Concept vocabulary is shared and must be preserved verbatim.
    assert {c.concept_id for c in ws.knowledge_map.concepts} == canonical_concepts
    # Topic IDs are workspace-scoped: re-IDed, but a topic referenced by the
    # progress state must still exist in the curriculum.
    curriculum_topic_ids = {
        topic.topic_id for week in ws.curriculum.weeks for topic in week.topics
    }
    for topic_progress in ws.progress_state.topic_progress:
        assert topic_progress.topic_id in curriculum_topic_ids
