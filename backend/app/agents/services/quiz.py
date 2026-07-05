from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import QuizAgent
from app.agents.services.common import create_or_get, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO
from app.schemas.enums import DifficultyLevel, QuizStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import (
    QuizAgentInput,
    QuizAgentOutput,
    QuizAttemptDTO,
    QuizDTO,
    QuizScoreOutput,
)
from app.services import QuizService


@dataclass(slots=True)
class QuizAgentService:
    agent: QuizAgent
    quizzes: QuizService

    def build(
        self,
        goal: LearningGoalDTO,
        curriculum: CurriculumDTO,
        progress_state: ProgressStateDTO,
    ) -> tuple[QuizDTO, QuizAttemptDTO]:
        topics = _curriculum_topics(curriculum)
        payload = QuizAgentInput(
            goal_text=goal.goal_text,
            curriculum_topics=topics,
            target_concepts=progress_state.weak_concepts or demo.QUIZ.target_concept_ids,
            difficulty=curriculum.weeks[0].topics[0].difficulty
            if curriculum.weeks and curriculum.weeks[0].topics
            else DifficultyLevel.INTERMEDIATE,
            question_count=len(demo.QUIZ.questions),
        )
        quiz_output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=QuizAgentOutput,
            payload=self.agent.build_quiz(payload),
        )
        quiz = QuizDTO(
            quiz_id=demo.QUIZ_ID,
            goal_id=goal.goal_id,
            curriculum_id=curriculum.curriculum_id,
            target_topic_ids=demo.QUIZ.target_topic_ids,
            target_concept_ids=demo.QUIZ.target_concept_ids,
            status=QuizStatus.COMPLETED,
            title=quiz_output.quiz_title,
            questions=quiz_output.questions,
            scoring_policy=quiz_output.scoring_policy,
            difficulty=demo.QUIZ.difficulty,
            created_at=demo.NOW,
            updated_at=demo.NOW,
        )
        saved_quiz = create_or_get(
            create=self.quizzes.create_quiz,
            get=self.quizzes.get_quiz_by_id,
            record=quiz,
            record_id=quiz.quiz_id,
        )
        attempt_template = demo.QUIZ_ATTEMPT.model_copy(
            update={
                "goal_id": goal.goal_id,
                "curriculum_id": curriculum.curriculum_id,
                "quiz_id": saved_quiz.quiz_id,
            },
            deep=True,
        )
        score_output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=QuizScoreOutput,
            payload=self.agent.score_attempt(attempt_template),
        )
        attempt = attempt_template.model_copy(
            update={
                "total_score": score_output.total_score,
                "correct_count": score_output.correct_count,
                "total_questions": score_output.total_questions,
                "concept_scores": score_output.concept_scores,
                "weak_concepts": score_output.weak_concepts,
                "feedback": score_output.feedback,
            },
            deep=True,
        )
        saved_attempt = create_or_get(
            create=self.quizzes.create_attempt,
            get=self.quizzes.get_attempt_by_id,
            record=attempt,
            record_id=attempt.quiz_attempt_id,
        )
        return saved_quiz, saved_attempt


def _curriculum_topics(curriculum: CurriculumDTO) -> list[CurriculumTopicDTO]:
    return [topic for week in curriculum.weeks for topic in week.topics]
