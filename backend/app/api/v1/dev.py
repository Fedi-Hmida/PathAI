from fastapi import APIRouter

from app.adapter.schemas import AdaptationExampleResponse, AdaptationReplanRequest
from app.adapter.service import AdapterService
from app.agents.demo_orchestration import (
    ServiceBackedDemoOrchestrator,
    ServiceBackedDemoRequest,
    ServiceBackedDemoResult,
)
from app.agents.service import PathAIGraphService, run_demo_graph_from_payload
from app.assessment.schemas import KnowledgeMap
from app.core.config import get_settings
from app.core.errors import PathAIError
from app.critic.schemas import CriticExampleResponse, CriticReviewRequest
from app.critic.service import CriticService
from app.curriculum.schemas import CurriculumExampleResponse, CurriculumGenerationRequest
from app.curriculum.service import CurriculumService
from app.evaluation.schemas import EvaluationReport, EvaluationRunRequest
from app.evaluation.service import EvaluationService
from app.llm.client import UniversityLLMClient
from app.llm.config import assert_real_llm_configured, get_safe_llm_config
from app.llm.errors import LLMConfigurationError, LLMError
from app.llm.mock import MockLLMClient
from app.llm.redaction import redact_for_llm
from app.llm.structured import generate_structured
from app.llm.types import LLMHealthCheckOutput, LLMMessage, SafeLLMConfig
from app.models import get_registered_model_names
from app.progress.schemas import (
    ProgressExampleResponse,
    ProgressInitializeRequest,
    ProgressUpdateRequest,
)
from app.progress.service import ProgressService
from app.prompts import PromptNotFoundError, PromptRenderError, get_prompt_registry
from app.quiz.schemas import (
    QuizAnswer,
    QuizExampleResponse,
    QuizGenerationRequest,
    QuizSubmissionRequest,
)
from app.quiz.service import QuizService
from app.rag.schemas import (
    CurriculumResourceAttachmentRequest,
    ResourceExampleResponse,
    ResourceRetrievalRequest,
)
from app.rag.service import ResourceService
from app.schemas.dev import (
    GoalValidationResponse,
    GraphDefinitionResponse,
    GraphDemoRunRequest,
    GraphDemoRunResponse,
    MockStructuredLLMRequest,
    RegisteredModelsResponse,
)
from app.schemas.learning import LearningGoalCreate

router = APIRouter(prefix="/dev", tags=["development"])
graph_service = PathAIGraphService()
curriculum_dev_service = CurriculumService()
resource_dev_service = ResourceService()
critic_dev_service = CriticService()
progress_dev_service = ProgressService()
quiz_dev_service = QuizService()
adapter_dev_service = AdapterService()
evaluation_dev_service = EvaluationService()
service_backed_demo_orchestrator = ServiceBackedDemoOrchestrator()


@router.get(
    "/models",
    response_model=RegisteredModelsResponse,
    summary="List registered Beanie models for development diagnostics.",
)
async def list_registered_models() -> RegisteredModelsResponse:
    return RegisteredModelsResponse(models=get_registered_model_names())


@router.post(
    "/goals/validate",
    response_model=GoalValidationResponse,
    summary="Validate a learning goal payload without persistence.",
)
async def validate_learning_goal(goal: LearningGoalCreate) -> GoalValidationResponse:
    return GoalValidationResponse(
        valid=True,
        goal=goal,
        message="Learning goal payload is structurally valid. No data was persisted.",
    )


@router.get(
    "/llm/config",
    response_model=SafeLLMConfig,
    summary="Show safe LLM runtime configuration for development diagnostics.",
)
async def get_llm_config() -> SafeLLMConfig:
    return get_safe_llm_config()


@router.post(
    "/llm/mock-structured",
    response_model=LLMHealthCheckOutput,
    summary="Validate structured output behavior with the mock LLM client.",
)
async def mock_structured_llm(request: MockStructuredLLMRequest) -> LLMHealthCheckOutput:
    try:
        prompt = get_prompt_registry().render(
            request.prompt_name,
            {"context": request.context},
        )
    except PromptNotFoundError as exc:
        raise PathAIError(
            code="prompt_not_found",
            message=str(exc),
            status_code=404,
        ) from exc
    except PromptRenderError as exc:
        raise PathAIError(
            code="prompt_render_failed",
            message=str(exc),
            status_code=422,
        ) from exc

    messages = [LLMMessage(role="user", content=redact_for_llm(prompt.content))]
    return await generate_structured(
        client=MockLLMClient(),
        messages=messages,
        output_model=LLMHealthCheckOutput,
    )


@router.post(
    "/llm/health-check",
    response_model=LLMHealthCheckOutput,
    summary="Call the configured real LLM only when mock mode is disabled.",
)
async def real_llm_health_check() -> LLMHealthCheckOutput:
    settings = get_settings()
    try:
        assert_real_llm_configured(settings)
    except LLMConfigurationError as exc:
        raise PathAIError(
            code="llm_not_configured",
            message=str(exc),
            status_code=409,
        ) from exc

    prompt = get_prompt_registry(settings).render(
        "llm_health_check",
        {"context": "Return a minimal operational health check for PathAI."},
    )
    messages = [LLMMessage(role="user", content=redact_for_llm(prompt.content))]

    try:
        return await generate_structured(
            client=UniversityLLMClient(settings=settings),
            messages=messages,
            output_model=LLMHealthCheckOutput,
        )
    except LLMError as exc:
        raise PathAIError(
            code="llm_health_check_failed",
            message=str(exc),
            status_code=502,
        ) from exc


@router.get(
    "/graph/definition",
    response_model=GraphDefinitionResponse,
    summary="Show the Phase 3 graph definition for development diagnostics.",
)
async def get_graph_definition() -> GraphDefinitionResponse:
    return GraphDefinitionResponse.model_validate(graph_service.get_graph_definition_summary())


@router.post(
    "/graph/demo-run",
    response_model=GraphDemoRunResponse,
    summary="Run the deterministic Phase 3 graph skeleton without real agents.",
)
async def run_graph_demo(request: GraphDemoRunRequest) -> GraphDemoRunResponse:
    final_state = run_demo_graph_from_payload(
        user_id=request.user_id,
        goal_id=request.goal_id,
        goal=request.goal,
        timeline_weeks=request.timeline_weeks,
        hours_per_week=request.hours_per_week,
        max_revisions=request.max_revisions,
        critic_reject_until_revision=request.critic_reject_until_revision,
        simulate_failure_node=request.simulate_failure_node,
    )
    return GraphDemoRunResponse(
        final_state=final_state.public_summary(),
        trace=[event.model_dump(mode="json") for event in final_state.trace],
        warnings=[warning.model_dump(mode="json") for warning in final_state.warnings],
        errors=[error.model_dump(mode="json") for error in final_state.errors],
    )


@router.post(
    "/graph/service-backed-demo-run",
    response_model=ServiceBackedDemoResult,
    summary="Run a local no-auth service-backed demo flow using real PathAI modules.",
)
async def run_service_backed_demo(
    request: ServiceBackedDemoRequest,
) -> ServiceBackedDemoResult:
    return await service_backed_demo_orchestrator.run(request)


@router.get(
    "/curriculum/example",
    response_model=CurriculumExampleResponse,
    summary="Return a deterministic example curriculum for development diagnostics.",
)
async def get_curriculum_example() -> CurriculumExampleResponse:
    request = CurriculumGenerationRequest(
        goal="Learn RAG systems for a graduation project",
        timeline_weeks=6,
        hours_per_week=8,
        knowledge_map=KnowledgeMap(
            strong=["Python basics"],
            weak=["Embeddings", "Evaluation"],
            missing=["Chunking", "Reranking", "Prompt Injection"],
            recommended_level="beginner",
            confidence_score=0.82,
            assessment_notes=["Demo knowledge map for curriculum diagnostics."],
        ),
    )
    result = await curriculum_dev_service.generate_curriculum(request)
    return CurriculumExampleResponse(request=request, result=result.result)


@router.get(
    "/resources/example",
    response_model=ResourceExampleResponse,
    summary="Return a deterministic resource retrieval example for diagnostics.",
)
async def get_resource_example() -> ResourceExampleResponse:
    summary = resource_dev_service.get_resource_catalog_summary()
    retrieval = resource_dev_service.retrieve_for_topic(
        ResourceRetrievalRequest(
            topic="retrieval augmented generation",
            goal="Learn RAG systems for a graduation project",
            difficulty="intermediate",
            subtopics=["retrieval", "generation"],
            top_k=2,
        )
    )
    return ResourceExampleResponse(summary=summary, retrieval=retrieval)


@router.get(
    "/critic/example",
    response_model=CriticExampleResponse,
    summary="Return a deterministic Critic review example for diagnostics.",
)
async def get_critic_example() -> CriticExampleResponse:
    request = CurriculumGenerationRequest(
        goal="Learn RAG systems for a graduation project",
        timeline_weeks=4,
        hours_per_week=8,
        knowledge_map=KnowledgeMap(
            strong=["Python basics"],
            weak=["Embeddings"],
            missing=["Chunking", "Reranking"],
            recommended_level="beginner",
            confidence_score=0.84,
            assessment_notes=["Demo knowledge map for critic diagnostics."],
        ),
    )
    curriculum_response = await curriculum_dev_service.generate_curriculum(request)
    resource_attachment = resource_dev_service.retrieve_for_curriculum(
        request=CurriculumResourceAttachmentRequest(
            curriculum=curriculum_response.result.curriculum,
            top_k=2,
        )
    )
    review = await critic_dev_service.review_curriculum_with_resources(
        CriticReviewRequest(
            curriculum=curriculum_response.result.curriculum,
            resource_attachment=resource_attachment,
        )
    )
    return CriticExampleResponse(review=review)


@router.get(
    "/progress/example",
    response_model=ProgressExampleResponse,
    summary="Return a deterministic progress tracking example for diagnostics.",
)
async def get_progress_example() -> ProgressExampleResponse:
    curriculum_response = await _build_demo_curriculum()
    progress_response = progress_dev_service.initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum_response.result.curriculum)
    )
    first_week = progress_response.summary.weeks[0]
    first_topic = first_week.topics[0]
    updated = progress_dev_service.update_progress(
        ProgressUpdateRequest(
            curriculum_id=progress_response.summary.curriculum_id,
            week_number=first_week.week_number,
            topic_id=first_topic.topic_id,
            status="done",
        )
    )
    return ProgressExampleResponse(summary=updated.summary)


@router.get(
    "/quiz/example",
    response_model=QuizExampleResponse,
    summary="Return a deterministic quiz generation and scoring example for diagnostics.",
)
async def get_quiz_example() -> QuizExampleResponse:
    curriculum_response = await _build_demo_curriculum()
    quiz_response = await quiz_dev_service.generate_quiz(
        QuizGenerationRequest(
            curriculum=curriculum_response.result.curriculum,
            week_number=1,
            question_count=5,
        )
    )
    result = quiz_dev_service.submit_quiz(
        quiz_response.quiz.quiz_id,
        QuizSubmissionRequest(
            answers=[
                QuizAnswer(
                    question_id=question.question_id,
                    answer=question.correct_answer,
                )
                for question in quiz_response.quiz.questions
            ]
        ),
    )
    return QuizExampleResponse(quiz=quiz_response.quiz, result=result)


@router.get(
    "/adapt/example",
    response_model=AdaptationExampleResponse,
    summary="Return a deterministic adaptation/replanning example for diagnostics.",
)
async def get_adaptation_example() -> AdaptationExampleResponse:
    curriculum_response = await _build_demo_curriculum()
    curriculum = curriculum_response.result.curriculum
    resource_attachment = resource_dev_service.retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=2)
    )
    progress_response = progress_dev_service.initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    )
    first_week = progress_response.summary.weeks[0]
    first_topic = first_week.topics[0]
    progress_summary = progress_dev_service.update_progress(
        ProgressUpdateRequest(
            curriculum_id=progress_response.summary.curriculum_id,
            week_number=first_week.week_number,
            topic_id=first_topic.topic_id,
            status="stuck",
        )
    ).summary
    quiz_response = await quiz_dev_service.generate_quiz(
        QuizGenerationRequest(curriculum=curriculum, week_number=1, question_count=5)
    )
    quiz_dev_service.submit_quiz(
        quiz_response.quiz.quiz_id,
        QuizSubmissionRequest(
            answers=[
                QuizAnswer(question_id=question.question_id, answer="not sure")
                for question in quiz_response.quiz.questions
            ]
        ),
    )
    quiz_history = quiz_dev_service.get_history(curriculum.curriculum_id)
    result = await adapter_dev_service.run_replan(
        AdaptationReplanRequest(
            curriculum=curriculum,
            progress_summary=progress_summary,
            quiz_history=quiz_history,
            expected_week_number=1,
            existing_resource_attachment=resource_attachment,
        )
    )
    return AdaptationExampleResponse(result=result)


@router.get(
    "/evaluation/example",
    response_model=EvaluationReport,
    summary="Return a deterministic synthetic evaluation report example.",
)
async def get_evaluation_example() -> EvaluationReport:
    return evaluation_dev_service.run_sample_evaluation(EvaluationRunRequest())


async def _build_demo_curriculum() -> CurriculumExampleResponse:
    request = CurriculumGenerationRequest(
        goal="Learn RAG systems for a graduation project",
        timeline_weeks=4,
        hours_per_week=8,
        knowledge_map=KnowledgeMap(
            strong=["Python basics"],
            weak=["Embeddings"],
            missing=["Chunking", "Reranking"],
            recommended_level="beginner",
            confidence_score=0.84,
            assessment_notes=["Demo knowledge map for progress and quiz diagnostics."],
        ),
    )
    result = await curriculum_dev_service.generate_curriculum(request)
    return CurriculumExampleResponse(request=request, result=result.result)
