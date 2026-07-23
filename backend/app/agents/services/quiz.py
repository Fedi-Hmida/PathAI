from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.agents.contracts import QuizAgent
from app.agents.deterministic.quiz import (
    LOW_SCORE_THRESHOLD,
    seeded_answers_for_questions,
)
from app.agents.mock import MockQuizAgent
from app.agents.services.common import create_or_replace, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO
from app.schemas.enums import DifficultyLevel, QuizAttemptStatus, QuizStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import (
    ConceptQuizScore,
    QuizAgentInput,
    QuizAgentOutput,
    QuizAnswerSubmission,
    QuizAttemptDTO,
    QuizDTO,
    QuizQuestionDTO,
    QuizScoreOutput,
)
from app.services import QuizService


@dataclass(slots=True)
class QuizAgentService:
    agent: QuizAgent
    quizzes: QuizService

    def build_quiz(
        self,
        goal: LearningGoalDTO,
        curriculum: CurriculumDTO,
        progress_state: ProgressStateDTO,
        *,
        quiz_id: str | None = None,
    ) -> QuizDTO:
        """Build (or regenerate) the quiz's questions only - no attempt.

        This is what `WorkspaceGenerationService.generate()` calls (Big_Audit
        Step 10): a fresh quiz is never accompanied by a fabricated attempt
        any more. A real attempt only ever comes from `submit_attempt()`,
        driven by a genuine learner submission through
        `POST /quizzes/{quiz_id}/attempts`.
        """
        return self._build_quiz(goal, curriculum, progress_state, quiz_id=quiz_id)

    def submit_attempt(
        self,
        quiz: QuizDTO,
        answers: list[QuizAnswerSubmission],
        *,
        quiz_attempt_id: str | None = None,
    ) -> QuizAttemptDTO:
        """Score a real learner's submitted answers and persist a genuinely
        new attempt (never an overwrite of a prior one - see
        `dashboard.py`'s latest-attempt-by-`submitted_at` selection, which
        already assumes a goal can accumulate multiple real attempts over
        time as a learner retakes a quiz)."""
        now = datetime.now(UTC)
        attempt_template = QuizAttemptDTO(
            quiz_attempt_id=quiz_attempt_id or f"attempt_{uuid4().hex}",
            quiz_id=quiz.quiz_id,
            goal_id=quiz.goal_id,
            curriculum_id=quiz.curriculum_id,
            answers=answers,
            total_score=0.0,
            correct_count=0,
            total_questions=len(answers),
            concept_scores=[
                ConceptQuizScore(
                    concept_id=quiz.questions[0].concept_ids[0],
                    score=0.0,
                    correct_count=0,
                    total_questions=1,
                ),
            ],
            submitted_at=now,
            status=QuizAttemptStatus.SUBMITTED,
            feedback=None,
            adaptation_triggered=False,
            created_at=now,
            updated_at=now,
        )
        score_output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=QuizScoreOutput,
            payload=self.agent.score_attempt(attempt_template, quiz.questions),
        )
        attempt = attempt_template.model_copy(
            update={
                "total_score": score_output.total_score,
                "correct_count": score_output.correct_count,
                "total_questions": score_output.total_questions,
                "concept_scores": score_output.concept_scores,
                "weak_concepts": score_output.weak_concepts,
                "feedback": score_output.feedback,
                "status": QuizAttemptStatus.SCORED,
                "adaptation_triggered": score_output.total_score < LOW_SCORE_THRESHOLD,
            },
            deep=True,
        )
        return self.quizzes.create_attempt(attempt)

    def build(
        self,
        goal: LearningGoalDTO,
        curriculum: CurriculumDTO,
        progress_state: ProgressStateDTO,
        *,
        quiz_id: str | None = None,
        quiz_attempt_id: str | None = None,
    ) -> tuple[QuizDTO, QuizAttemptDTO]:
        """Build the quiz and an auto-scored, seeded-answer attempt in one
        call.

        Kept exactly as before: this is still what the orchestration graph's
        fixed canonical-demo pipeline (`load_quiz`) and this module's own
        pre-existing unit tests rely on. `WorkspaceGenerationService.generate()`
        no longer calls this - it calls `build_quiz()` instead (Big_Audit
        Step 10 reworks the real per-user path only, not the demo pipeline).
        """
        saved_quiz = self._build_quiz(goal, curriculum, progress_state, quiz_id=quiz_id)
        attempt_template = QuizAttemptDTO(
            quiz_attempt_id=quiz_attempt_id or demo.QUIZ_ATTEMPT_ID,
            quiz_id=saved_quiz.quiz_id,
            goal_id=goal.goal_id,
            curriculum_id=curriculum.curriculum_id,
            answers=seeded_answers_for_questions(saved_quiz.questions),
            total_score=0.0,
            correct_count=0,
            total_questions=len(saved_quiz.questions),
            concept_scores=[
                demo.QUIZ_ATTEMPT.concept_scores[0].model_copy(deep=True),
            ],
            weak_concepts=saved_quiz.target_concept_ids,
            submitted_at=demo.NOW,
            status=QuizAttemptStatus.SCORED,
            feedback="Deterministic attempt awaiting scoring.",
            adaptation_triggered=False,
            created_at=demo.NOW,
            updated_at=demo.NOW,
        )
        score_output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=QuizScoreOutput,
            payload=self.agent.score_attempt(attempt_template, saved_quiz.questions),
        )
        attempt = attempt_template.model_copy(
            update={
                "total_score": score_output.total_score,
                "correct_count": score_output.correct_count,
                "total_questions": score_output.total_questions,
                "concept_scores": score_output.concept_scores,
                "weak_concepts": score_output.weak_concepts,
                "feedback": score_output.feedback,
                "adaptation_triggered": score_output.total_score < LOW_SCORE_THRESHOLD,
            },
            deep=True,
        )
        saved_attempt = create_or_replace(
            create=self.quizzes.create_attempt,
            save=self.quizzes.save_attempt,
            record=attempt,
        )
        return saved_quiz, saved_attempt

    def _build_quiz(
        self,
        goal: LearningGoalDTO,
        curriculum: CurriculumDTO,
        progress_state: ProgressStateDTO,
        *,
        quiz_id: str | None = None,
    ) -> QuizDTO:
        topics = _curriculum_topics(curriculum)
        payload = QuizAgentInput(
            goal_text=goal.goal_text,
            curriculum_topics=topics,
            target_concepts=progress_state.weak_concepts,
            difficulty=curriculum.weeks[0].topics[0].difficulty
            if curriculum.weeks and curriculum.weeks[0].topics
            else DifficultyLevel.INTERMEDIATE,
            question_count=min(6, max(3, len(progress_state.weak_concepts))),
        )
        quiz_output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=QuizAgentOutput,
            payload=self.agent.build_quiz(payload),
        )
        quiz = QuizDTO(
            quiz_id=quiz_id or demo.QUIZ_ID,
            goal_id=goal.goal_id,
            curriculum_id=curriculum.curriculum_id,
            target_topic_ids=_target_topic_ids(topics, quiz_output.questions),
            target_concept_ids=_target_concept_ids(quiz_output.questions),
            status=QuizStatus.COMPLETED,
            title=quiz_output.quiz_title,
            questions=quiz_output.questions,
            scoring_policy=quiz_output.scoring_policy,
            difficulty=payload.difficulty,
            created_at=demo.NOW,
            updated_at=demo.NOW,
        )
        return create_or_replace(
            create=self.quizzes.create_quiz,
            save=self.quizzes.save_quiz,
            record=quiz,
        )


def _curriculum_topics(curriculum: CurriculumDTO) -> list[CurriculumTopicDTO]:
    return [topic for week in curriculum.weeks for topic in week.topics]


def _target_concept_ids(questions: list[QuizQuestionDTO]) -> list[str]:
    values: list[str] = []
    for question in questions:
        values.extend(question.concept_ids)
    return _unique(values)


def _target_topic_ids(
    topics: list[CurriculumTopicDTO],
    questions: list[QuizQuestionDTO],
) -> list[str]:
    concept_ids = set(_target_concept_ids(questions))
    topic_ids = [
        topic.topic_id
        for topic in topics
        if set(topic.concept_ids) & concept_ids
    ]
    return topic_ids or [topics[0].topic_id]


def _unique(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return unique_values


def build_default_quiz_agent_service(quizzes: QuizService) -> QuizAgentService:
    """The quiz agent has no LLM mode (unlike assessment/knowledge-map/critic/
    curriculum) - it is always this deterministic default. Exists so
    `app/orchestration/quiz_submission_gateway.py` (the sanctioned seam the
    API layer uses to reach the real quiz-attempt submission path) never has
    to reference `app.agents.mock` directly - forbidden there by
    `test_agent_scope_security.py`, the same way `bundle.py` already keeps
    that reference confined to `app/agents/services/`."""
    return QuizAgentService(MockQuizAgent(), quizzes)
