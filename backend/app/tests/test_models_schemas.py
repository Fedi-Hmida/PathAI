from app.models import get_registered_model_names
from app.models.common import LearningGoal, ResourceReference, Topic
from app.models.progress_log import ProgressLogDocument
from app.models.resource import ResourceDocument
from app.models.user import UserProfileDocument
from app.schemas.learning import KnowledgeMapSchema, LearningGoalCreate
from app.schemas.progress import ProgressUpdateRequest


def test_model_registry_contains_phase1_documents() -> None:
    model_names = get_registered_model_names()

    assert model_names == [
        "UserProfileDocument",
        "AssessmentSessionDocument",
        "CurriculumDocument",
        "ResourceDocument",
        "QuizDocument",
        "ProgressLogDocument",
        "AdaptationLogDocument",
        "GenerationJobDocument",
    ]


def test_user_profile_placeholder_has_no_auth_fields() -> None:
    model_fields = UserProfileDocument.model_fields

    assert "email" in model_fields
    assert "name" in model_fields
    assert "goals" in model_fields
    assert "password" not in model_fields
    assert "password_hash" not in model_fields
    assert "jwt" not in model_fields


def test_learning_goal_and_nested_topic_validation() -> None:
    resource = ResourceReference(
        title="FastAPI Tutorial",
        url="https://fastapi.tiangolo.com/tutorial/",
        type="documentation",
        source_name="FastAPI",
        difficulty="beginner",
        estimated_minutes=45,
        quality_score=0.95,
    )
    topic = Topic(
        title="API fundamentals",
        difficulty="beginner",
        estimated_hours=3,
        resources=[resource],
    )
    goal = LearningGoal(
        title="Learn backend foundations",
        target_level="intermediate",
        timeline_weeks=8,
        hours_per_week=10,
    )

    assert topic.resources[0].quality_score == 0.95
    assert goal.status == "draft"


def test_resource_document_model_shape() -> None:
    model_fields = ResourceDocument.model_fields

    assert "title" in model_fields
    assert "url" in model_fields
    assert "topics" in model_fields
    assert "embedding" in model_fields
    assert ResourceDocument.Settings.name == "resources"


def test_resource_reference_validation() -> None:
    resource = ResourceReference(
        title="MongoDB Indexes",
        url="https://www.mongodb.com/docs/manual/indexes/",
        type="documentation",
        difficulty="intermediate",
        estimated_minutes=35,
        source_name="MongoDB Docs",
        quality_score=0.9,
    )

    assert resource.source_name == "MongoDB Docs"
    assert resource.quality_score == 0.9


def test_schema_validation_for_goal_knowledge_and_progress() -> None:
    goal = LearningGoalCreate(
        title="  Learn LangGraph orchestration ",
        target_level="intermediate",
        timeline_weeks=6,
        hours_per_week=8,
    )
    knowledge_map = KnowledgeMapSchema(
        strong=["Python basics"],
        weak=["evaluation"],
        missing=["reranking"],
        recommended_level="beginner",
        confidence_score=0.82,
    )
    progress = ProgressUpdateRequest(
        goal_id="goal-1",
        week_number=1,
        topic="RAG foundations",
        event="marked_in_progress",
        value={"source": "manual"},
    )

    assert goal.title == "Learn LangGraph orchestration"
    assert knowledge_map.confidence_score == 0.82
    assert progress.event == "marked_in_progress"
    assert ProgressLogDocument.Settings.name == "progress_logs"
