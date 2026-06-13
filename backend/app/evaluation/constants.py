from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

EvaluationSystemVariant = Literal[
    "static_expert",
    "single_agent_llm",
    "pathai_full",
    "no_rag",
    "no_critic",
    "no_adapter",
]
MetricCategory = Literal[
    "assessment",
    "curriculum",
    "resources",
    "critic",
    "adaptation",
    "learning_gain",
    "baseline",
    "ablation",
]
RubricAudience = Literal[
    "curriculum_expert",
    "resource_reviewer",
    "assessment_reviewer",
    "adaptation_reviewer",
]

DEFAULT_EVALUATION_DATASET = "synthetic_pathai_v1"
SYNTHETIC_DATASET_DESCRIPTION = (
    "Synthetic local fixtures for offline engineering validation. These data do not "
    "prove real learner outcome improvement."
)
DEFAULT_PASS_THRESHOLD = 0.70
DEFAULT_MIN_RESOURCE_COVERAGE = 2


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_evaluation_id() -> str:
    return f"eval_{uuid4().hex}"
