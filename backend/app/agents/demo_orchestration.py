from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.adapter.schemas import (
    AdaptationCheckRequest,
    AdaptationDecision,
    AdaptationReplanRequest,
    AdaptationResult,
)
from app.adapter.service import AdapterService
from app.assessment.constants import MIN_ASSESSMENT_QUESTIONS, DifficultyLevel
from app.assessment.schemas import (
    AnswerSubmissionRequest,
    AssessmentQuestion,
    FinalAssessmentResult,
    GoalIntakeRequest,
)
from app.assessment.service import AssessmentService
from app.critic.schemas import CriticReviewRequest, CriticReviewResult
from app.critic.service import CriticService
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.curriculum.service import CurriculumService
from app.evaluation.schemas import EvaluationReport, EvaluationRunRequest
from app.evaluation.service import EvaluationService
from app.progress.constants import TopicStatus
from app.progress.schemas import (
    CurriculumProgressSummary,
    ProgressInitializeRequest,
    ProgressUpdateRequest,
)
from app.progress.service import ProgressService
from app.quiz.schemas import (
    Quiz,
    QuizAnswer,
    QuizGenerationRequest,
    QuizHistorySummary,
    QuizResult,
    QuizSubmissionRequest,
)
from app.quiz.service import QuizService
from app.rag.schemas import (
    CurriculumResourceAttachmentRequest,
    CurriculumResourceAttachmentResponse,
)
from app.rag.service import ResourceService

StepStatus = Literal["completed"]
QuizAnswerMode = Literal["correct", "idk"]


class ServiceBackedDemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(
        default="Learn RAG systems for a graduation project",
        min_length=3,
        max_length=1000,
    )
    assessment_answer: str = Field(
        default="Embeddings represent text as vectors for semantic similarity search.",
        min_length=0,
        max_length=2000,
    )
    timeline_weeks: int = Field(default=4, ge=1, le=12)
    hours_per_week: int = Field(default=6, ge=1, le=40)
    target_level: DifficultyLevel = "beginner"
    max_questions: int = Field(default=3, ge=MIN_ASSESSMENT_QUESTIONS, le=12)
    resource_top_k: int = Field(default=2, ge=1, le=5)
    quiz_question_count: int = Field(default=3, ge=1, le=7)
    quiz_answer_mode: QuizAnswerMode = "correct"
    progress_status: TopicStatus = "stuck"
    expected_week_number: int = Field(default=1, ge=1, le=12)


class ServiceBackedDemoStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    status: StepStatus
    summary: str = Field(min_length=1, max_length=500)


class ServiceBackedDemoResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1, max_length=120)
    steps: list[ServiceBackedDemoStep] = Field(default_factory=list)
    initial_question: AssessmentQuestion
    assessment: FinalAssessmentResult
    curriculum: CurriculumPlan
    resource_attachment: CurriculumResourceAttachmentResponse
    critic_review: CriticReviewResult
    progress_summary: CurriculumProgressSummary
    quiz: Quiz
    quiz_result: QuizResult
    quiz_history: QuizHistorySummary
    adaptation_decision: AdaptationDecision
    adaptation_result: AdaptationResult
    evaluation_report: EvaluationReport
    notes: list[str] = Field(default_factory=list)


class ServiceBackedDemoOrchestrator:
    """Runs the implemented demo modules in one deterministic local-only flow."""

    def __init__(
        self,
        assessment_service: AssessmentService | None = None,
        curriculum_service: CurriculumService | None = None,
        resource_service: ResourceService | None = None,
        critic_service: CriticService | None = None,
        progress_service: ProgressService | None = None,
        quiz_service: QuizService | None = None,
        adapter_service: AdapterService | None = None,
        evaluation_service: EvaluationService | None = None,
    ) -> None:
        self.assessment_service = assessment_service or AssessmentService()
        self.curriculum_service = curriculum_service or CurriculumService()
        self.resource_service = resource_service or ResourceService()
        self.critic_service = critic_service or CriticService()
        self.progress_service = progress_service or ProgressService()
        self.quiz_service = quiz_service or QuizService()
        self.adapter_service = adapter_service or AdapterService(
            resource_service=self.resource_service,
            critic_service=self.critic_service,
        )
        self.evaluation_service = evaluation_service or EvaluationService()

    async def run(self, request: ServiceBackedDemoRequest) -> ServiceBackedDemoResult:
        steps: list[ServiceBackedDemoStep] = []
        run_id = f"demo_{uuid4().hex}"

        started = await self.assessment_service.start_assessment(
            GoalIntakeRequest(
                goal=request.goal,
                timeline_weeks=request.timeline_weeks,
                hours_per_week=request.hours_per_week,
                target_level=request.target_level,
                max_questions=request.max_questions,
            )
        )
        _add_step(steps, "Assessment started", started.next_question.topic)

        submitted = await self.assessment_service.submit_answer(
            started.session.session_id,
            AnswerSubmissionRequest(answer=request.assessment_answer),
        )
        signal = submitted.evaluation.signal if submitted.evaluation else "completed"
        _add_step(steps, "Assessment answer submitted", f"Answer signal: {signal}.")

        finalized = self.assessment_service.finalize_assessment(started.session.session_id)
        _add_step(
            steps,
            "Knowledge map finalized",
            f"Confidence: {finalized.result.knowledge_map.confidence_score:.2f}.",
        )

        curriculum_response = await self.curriculum_service.generate_curriculum(
            CurriculumGenerationRequest(
                goal=request.goal,
                timeline_weeks=request.timeline_weeks,
                hours_per_week=request.hours_per_week,
                knowledge_map=finalized.result.knowledge_map,
                assessment_session_id=started.session.session_id,
            )
        )
        curriculum = curriculum_response.result.curriculum
        _add_step(steps, "Curriculum generated", f"{len(curriculum.weeks)} weeks created.")

        resource_attachment = self.resource_service.retrieve_for_curriculum(
            CurriculumResourceAttachmentRequest(
                curriculum=curriculum,
                top_k=request.resource_top_k,
            )
        )
        _add_step(
            steps,
            "Resources attached",
            f"{len(resource_attachment.attachments)} topic attachments created.",
        )

        critic_review = await self.critic_service.review_curriculum_with_resources(
            CriticReviewRequest(
                curriculum=curriculum,
                resource_attachment=resource_attachment,
                required_resources_per_topic=1,
                max_revisions=2,
            )
        )
        _add_step(
            steps,
            "Critic review completed",
            f"Decision: {critic_review.decision}; score {critic_review.overall_quality_score:.2f}.",
        )

        progress_response = self.progress_service.initialize_progress(
            ProgressInitializeRequest(curriculum=curriculum)
        )
        first_topic = progress_response.summary.weeks[0].topics[0]
        progress_update = self.progress_service.update_progress(
            ProgressUpdateRequest(
                curriculum_id=curriculum.curriculum_id,
                week_number=first_topic.week_number,
                topic_id=first_topic.topic_id,
                status=request.progress_status,
            )
        )
        _add_step(
            steps,
            "Progress updated",
            f"Marked {first_topic.topic_name} as {request.progress_status}.",
        )

        quiz_response = await self.quiz_service.generate_quiz(
            QuizGenerationRequest(
                curriculum=curriculum,
                week_number=1,
                resource_attachment=resource_attachment,
                question_count=request.quiz_question_count,
            )
        )
        quiz_result = self.quiz_service.submit_quiz(
            quiz_response.quiz.quiz_id,
            QuizSubmissionRequest(
                answers=[
                    QuizAnswer(
                        question_id=question.question_id,
                        answer=_answer_for_mode(question.correct_answer, request.quiz_answer_mode),
                    )
                    for question in quiz_response.quiz.questions
                ]
            ),
        )
        quiz_history = self.quiz_service.get_history(curriculum.curriculum_id)
        _add_step(steps, "Quiz completed", f"Score: {quiz_result.score:.2f}.")

        adaptation_decision = self.adapter_service.check_adaptation(
            AdaptationCheckRequest(
                curriculum=curriculum,
                progress_summary=progress_update.summary,
                quiz_history=quiz_history,
                expected_week_number=request.expected_week_number,
            )
        )
        adaptation_result = await self.adapter_service.run_replan(
            AdaptationReplanRequest(
                curriculum=curriculum,
                progress_summary=progress_update.summary,
                quiz_history=quiz_history,
                expected_week_number=request.expected_week_number,
                existing_resource_attachment=resource_attachment,
                top_k=request.resource_top_k,
            )
        )
        _add_step(
            steps,
            "Adapter flow completed",
            f"Decision: {adaptation_result.decision.decision}.",
        )

        evaluation_report = self.evaluation_service.run_sample_evaluation(
            EvaluationRunRequest()
        )
        _add_step(
            steps,
            "Synthetic evaluation generated",
            f"{len(evaluation_report.metric_scores)} metric scores produced.",
        )

        return ServiceBackedDemoResult(
            run_id=run_id,
            steps=steps,
            initial_question=started.next_question,
            assessment=finalized.result,
            curriculum=curriculum,
            resource_attachment=resource_attachment,
            critic_review=critic_review,
            progress_summary=progress_update.summary,
            quiz=quiz_response.quiz,
            quiz_result=quiz_result,
            quiz_history=quiz_history,
            adaptation_decision=adaptation_decision,
            adaptation_result=adaptation_result,
            evaluation_report=evaluation_report,
            notes=[
                "This is a local no-auth service-backed demo path.",
                "It uses existing deterministic/mock-safe services and in-memory stores.",
                "It does not call the real LLM, MongoDB persistence, auth, Docker, or deployment.",
            ],
        )


def _add_step(
    steps: list[ServiceBackedDemoStep],
    name: str,
    summary: str,
) -> None:
    steps.append(
        ServiceBackedDemoStep(
            order=len(steps) + 1,
            name=name,
            status="completed",
            summary=summary,
        )
    )


def _answer_for_mode(correct_answer: str, mode: QuizAnswerMode) -> str:
    if mode == "idk":
        return "I do not know yet."
    return correct_answer
