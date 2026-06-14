from dataclasses import dataclass

from app.adapter.service import AdapterService
from app.assessment.service import AssessmentService
from app.critic.service import CriticService
from app.curriculum.service import CurriculumService
from app.evaluation.service import EvaluationService
from app.progress.service import ProgressService
from app.quiz.service import QuizService
from app.rag.service import ResourceService
from app.repositories import RepositoryBundle
from app.repositories.runtime import get_repository_bundle


@dataclass(frozen=True)
class RuntimeServices:
    assessment: AssessmentService
    curriculum: CurriculumService
    progress: ProgressService
    quiz: QuizService
    adapter: AdapterService
    critic: CriticService
    resources: ResourceService
    evaluation: EvaluationService


def build_runtime_services(
    bundle: RepositoryBundle | None = None,
) -> RuntimeServices:
    repositories = bundle or get_repository_bundle()
    resource_service = ResourceService(repository=repositories.resource)
    critic_service = CriticService(repository=repositories.critic)
    return RuntimeServices(
        assessment=AssessmentService(repository=repositories.assessment),
        curriculum=CurriculumService(repository=repositories.curriculum),
        progress=ProgressService(repository=repositories.progress),
        quiz=QuizService(repository=repositories.quiz),
        adapter=AdapterService(
            repository=repositories.adapter,
            resource_service=resource_service,
            critic_service=critic_service,
        ),
        critic=critic_service,
        resources=resource_service,
        evaluation=EvaluationService(repository=repositories.evaluation),
    )
