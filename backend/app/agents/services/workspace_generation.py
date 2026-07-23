from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.agents.contracts import RunBudgetSummaryProvider
from app.agents.deterministic.progress import PRIORITY_WEAK_CONCEPTS
from app.agents.services.critic import CriticAgentService
from app.agents.services.curriculum import CurriculumAgentService
from app.agents.services.evaluation import EvaluationAgentService
from app.agents.services.knowledge_map import KnowledgeMapAgentService
from app.agents.services.progress import ProgressAgentService
from app.agents.services.quiz import QuizAgentService
from app.agents.services.resource import ResourceAgentService
from app.fixtures import canonical_demo as demo
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.critic import CriticReviewDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import AssessmentStatus, GoalStatus, ProgressStatus, TopicProgressStatus
from app.schemas.evaluation import EvaluationReportDTO
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.progress import ProgressStateDTO, TopicProgressDTO
from app.schemas.quiz import QuizAttemptDTO, QuizDTO
from app.schemas.workspace import LLMRunBudgetSummary
from app.services import (
    AssessmentService,
    CriticService,
    CurriculumService,
    EvaluationService,
    GoalService,
    KnowledgeMapService,
    ProgressService,
    QuizService,
)


class AssessmentNotCompleteError(Exception):
    """Raised when regeneration is requested before the goal has a completed
    live assessment session."""

    def __init__(self, goal_id: str) -> None:
        self.goal_id = goal_id
        super().__init__(f"no completed assessment session for goal: {goal_id}")


@dataclass(slots=True)
class GeneratedWorkspaceArtifacts:
    knowledge_map: KnowledgeMapDTO
    curriculum: CurriculumDTO
    critic_review: CriticReviewDTO
    evaluation_report: EvaluationReportDTO
    quiz: QuizDTO
    quiz_attempt: QuizAttemptDTO | None
    progress: ProgressStateDTO
    llm_budget_summary: LLMRunBudgetSummary | None = None


@dataclass(slots=True)
class WorkspaceGenerationService:
    """Builds a single user's knowledge map, curriculum, critic review,
    evaluation report, quiz, and real persisted progress state from their own
    completed live assessment. A fresh workspace seeds none of them
    (`app/fixtures/workspace_factory.py`), so the first call here mints fresh
    IDs and creates them; repeat calls find the goal's existing artifacts and
    regenerate them in place. The quiz agent needs a `ProgressStateDTO`
    before its own quiz-generation logic runs (it only reads
    `weak_concepts`), so `generate()` computes a lightweight, real (not
    persisted) weak-concepts seed to feed it.

    Unlike Rebuild-37, `generate()` no longer fabricates a scored quiz
    attempt alongside the quiz (Big_Audit Step 10): only the quiz's questions
    are built here. A real attempt only ever comes from a genuine learner
    submission through `POST /quizzes/{quiz_id}/attempts`
    (`QuizAgentService.submit_attempt`), so `progress_agent.build()` and
    `evaluation_agent.evaluate()` are called with `quiz_attempt=None` here -
    both already tolerate that absence honestly (the same pattern already
    used for `adaptation_event=None`), until a real attempt exists.

    Resources are now generated too (Big_Audit Step 12): `ResourceAgentService
    .attach()` runs the real deterministic matching/ranking algorithm against
    the curated corpus right after the curriculum is built, and its real
    attachments (not `[]`) feed the critic and evaluation agents below.
    Adaptation is still deliberately NOT generated here - it depends on real
    user activity (quiz scores, stuck topics) this service doesn't fabricate;
    it stays honestly absent until a real trigger fires through its own route.
    This is the per-user
    counterpart to the orchestration graph's
    `load_knowledge_map`/`load_curriculum`/`load_resources`/
    `load_critic_review`/`load_evaluation`/`load_progress` nodes, which only
    ever run against the
    fixed canonical demo goal (`app/orchestration/runner.py`) and still use
    `QuizAgentService.build()`'s original fused quiz+fabricated-attempt
    behavior unchanged."""

    knowledge_map_agent: KnowledgeMapAgentService
    curriculum_agent: CurriculumAgentService
    resource_agent: ResourceAgentService
    critic_agent: CriticAgentService
    evaluation_agent: EvaluationAgentService
    quiz_agent: QuizAgentService
    progress_agent: ProgressAgentService
    assessments: AssessmentService
    knowledge_maps: KnowledgeMapService
    curricula: CurriculumService
    critics: CriticService
    evaluations: EvaluationService
    quizzes: QuizService
    progress: ProgressService
    goals: GoalService
    llm_observer: RunBudgetSummaryProvider | None = None

    def generate(self, goal: LearningGoalDTO) -> GeneratedWorkspaceArtifacts:
        session = self._latest_completed_session(goal)
        answers = self.assessments.list_answers_by_session_id(session.assessment_session_id)

        existing_maps = self.knowledge_maps.list_by_goal_id(goal.goal_id)
        existing_curricula = self.curricula.list_by_goal_id(goal.goal_id)
        existing_reviews = self.critics.list_by_goal_id(goal.goal_id)
        existing_evaluations = self.evaluations.list_by_goal_id(goal.goal_id)
        knowledge_map_id = (
            existing_maps[0].knowledge_map_id if existing_maps else _new_id("kmap")
        )
        curriculum_id = (
            existing_curricula[0].curriculum_id if existing_curricula else _new_id("curriculum")
        )
        critic_review_id = (
            existing_reviews[0].critic_review_id if existing_reviews else _new_id("critic")
        )
        evaluation_report_id = (
            existing_evaluations[0].evaluation_report_id
            if existing_evaluations
            else _new_id("eval")
        )

        knowledge_map = self.knowledge_map_agent.build(
            goal,
            session,
            answers,
            knowledge_map_id=knowledge_map_id,
        )
        curriculum = self.curriculum_agent.build(
            goal,
            knowledge_map,
            curriculum_id=curriculum_id,
        )
        # Real resource attachments (Big_Audit Step 12): the goal-scoped
        # attachment IDs (`_attachment_id`) make this idempotent per goal, so
        # a regeneration overwrites the same records in place rather than
        # duplicating or colliding with another goal's attachments.
        resource_attachments = self.resource_agent.attach(curriculum, knowledge_map)
        critic_review = self.critic_agent.review(
            goal,
            knowledge_map,
            curriculum,
            resource_attachments,
            critic_review_id=critic_review_id,
        )
        existing_quizzes = self.quizzes.list_quizzes_by_goal_id(goal.goal_id)
        quiz_id = existing_quizzes[0].quiz_id if existing_quizzes else _new_id("quiz")
        existing_progress = self.progress.list_by_goal_id(goal.goal_id)
        progress_state_id = (
            existing_progress[0].progress_state_id if existing_progress else _new_id("progress")
        )

        # The quiz agent only reads `weak_concepts` off the progress state
        # (`QuizAgentService.build_quiz`), so this transient seed is never
        # persisted - the real, persisted progress state is built below.
        progress_seed = _progress_seed_for_quiz(goal, curriculum)
        quiz = self.quiz_agent.build_quiz(
            goal,
            curriculum,
            progress_seed,
            quiz_id=quiz_id,
        )

        # No real quiz attempt exists yet (a fresh quiz has none until a
        # learner actually takes it via `POST /quizzes/{quiz_id}/attempts`) -
        # both agents below already score its absence honestly, the same
        # pattern already used for `adaptation_event=None`.
        progress = self.progress_agent.build(
            goal,
            curriculum,
            None,
            progress_state_id=progress_state_id,
        )

        evaluation_report = self.evaluation_agent.evaluate(
            goal,
            session,
            knowledge_map,
            curriculum,
            resource_attachments,
            critic_review,
            None,
            None,
            evaluation_report_id=evaluation_report_id,
        )
        self.goals.update_status(goal.goal_id, GoalStatus.CURRICULUM_GENERATED)
        return GeneratedWorkspaceArtifacts(
            knowledge_map=knowledge_map,
            curriculum=curriculum,
            critic_review=critic_review,
            evaluation_report=evaluation_report,
            quiz=quiz,
            quiz_attempt=None,
            progress=progress,
            llm_budget_summary=self._llm_budget_summary(),
        )

    def _llm_budget_summary(self) -> LLMRunBudgetSummary | None:
        if self.llm_observer is None:
            return None
        return LLMRunBudgetSummary(**self.llm_observer.safe_summary())

    def _latest_completed_session(self, goal: LearningGoalDTO) -> AssessmentSessionDTO:
        sessions = self.assessments.list_sessions_by_goal_id(goal.goal_id)
        completed = [s for s in sessions if s.status == AssessmentStatus.COMPLETED]
        if not completed:
            raise AssessmentNotCompleteError(goal.goal_id)
        return completed[-1]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _progress_seed_for_quiz(goal: LearningGoalDTO, curriculum: CurriculumDTO) -> ProgressStateDTO:
    """A transient, never-persisted `ProgressStateDTO` carrying real (not
    empty) `weak_concepts`, built purely to satisfy `QuizAgentService.build`'s
    signature - it only reads that one field. Mirrors
    `deterministic/progress.py`'s own weak-concepts derivation (learner
    profile + `PRIORITY_WEAK_CONCEPTS`, both filtered to concepts the
    curriculum actually has), gated on the curriculum's real concepts so it
    carries no RAG-shaped default for a non-RAG goal."""
    first_topic = curriculum.weeks[0].topics[0]
    return ProgressStateDTO(
        progress_state_id=_new_id("progress"),
        goal_id=goal.goal_id,
        curriculum_id=curriculum.curriculum_id,
        status=ProgressStatus.NOT_STARTED,
        overall_completion=0.0,
        topic_progress=[
            TopicProgressDTO(
                topic_id=first_topic.topic_id,
                status=TopicProgressStatus.NOT_STARTED,
                completion=0.0,
            ),
        ],
        weak_concepts=_weak_concepts_seed(goal, curriculum),
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _weak_concepts_seed(goal: LearningGoalDTO, curriculum: CurriculumDTO) -> list[str]:
    curriculum_concepts = {
        concept
        for week in curriculum.weeks
        for topic in week.topics
        for concept in topic.concept_ids
    }
    candidates = [*goal.learner_profile.weak_areas, *PRIORITY_WEAK_CONCEPTS]
    seed: list[str] = []
    for concept in candidates:
        if concept in curriculum_concepts and concept not in seed:
            seed.append(concept)
    return seed
