from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import QuizAgent
from app.agents.deterministic.quiz import (
    LOW_SCORE_THRESHOLD,
    seeded_answers_for_questions,
)
from app.agents.services.common import create_or_get, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO
from app.schemas.enums import DifficultyLevel, QuizAttemptStatus, QuizStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import (
    QuizAgentInput,
    QuizAgentOutput,
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
            question_count=min(6, max(3, len(progress_state.weak_concepts))),
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
        saved_quiz = create_or_get(
            create=self.quizzes.create_quiz,
            get=self.quizzes.get_quiz_by_id,
            record=quiz,
            record_id=quiz.quiz_id,
        )
        attempt_template = QuizAttemptDTO(
            quiz_attempt_id=demo.QUIZ_ATTEMPT_ID,
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
                "adaptation_triggered": score_output.total_score < LOW_SCORE_THRESHOLD,
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
