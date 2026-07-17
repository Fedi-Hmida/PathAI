from __future__ import annotations

from typing import Protocol

from app.schemas.adaptation import AdaptationAgentInput, AdaptationAgentOutput
from app.schemas.assessment import (
    AssessmentAgentInput,
    AssessmentAgentOutput,
    AssessmentAnswerDTO,
    AssessmentScoreOutput,
)
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput, CurriculumDTO
from app.schemas.evaluation import EvaluationAgentInput, EvaluationAgentOutput
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import (
    QuizAgentInput,
    QuizAgentOutput,
    QuizAttemptDTO,
    QuizQuestionDTO,
    QuizScoreOutput,
)
from app.schemas.resource import ResourceAgentInput, ResourceAgentOutput


class AssessorAgent(Protocol):
    agent_name: str

    def generate_question(self, payload: AssessmentAgentInput) -> AssessmentAgentOutput: ...

    def score_answer(self, answer: AssessmentAnswerDTO) -> AssessmentScoreOutput: ...


class KnowledgeMapAgent(Protocol):
    agent_name: str

    def build_knowledge_map(self, payload: KnowledgeMapAgentInput) -> KnowledgeMapAgentOutput: ...


class CurriculumAgent(Protocol):
    agent_name: str

    def build_curriculum(self, payload: CurriculumAgentInput) -> CurriculumAgentOutput: ...


class ResourceAgent(Protocol):
    agent_name: str

    def attach_resources(self, payload: ResourceAgentInput) -> ResourceAgentOutput: ...


class CriticAgent(Protocol):
    agent_name: str

    def review_curriculum(self, payload: CriticAgentInput) -> CriticAgentOutput: ...


class ProgressAgent(Protocol):
    agent_name: str

    def build_progress_state(
        self,
        goal: LearningGoalDTO,
        curriculum: CurriculumDTO,
        quiz_attempt: QuizAttemptDTO | None = None,
    ) -> ProgressStateDTO: ...


class QuizAgent(Protocol):
    agent_name: str

    def build_quiz(self, payload: QuizAgentInput) -> QuizAgentOutput: ...

    def score_attempt(
        self,
        attempt: QuizAttemptDTO,
        questions: list[QuizQuestionDTO],
    ) -> QuizScoreOutput: ...


class AdapterAgent(Protocol):
    agent_name: str

    def plan_adaptation(self, payload: AdaptationAgentInput) -> AdaptationAgentOutput: ...


class EvaluationAgent(Protocol):
    agent_name: str

    def evaluate_run(self, payload: EvaluationAgentInput) -> EvaluationAgentOutput: ...
