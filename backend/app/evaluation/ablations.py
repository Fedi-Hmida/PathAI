from app.evaluation.schemas import BaselineDefinition


def get_ablation_definitions() -> list[BaselineDefinition]:
    return [
        BaselineDefinition(
            system_variant="no_rag",
            label="No-RAG Ablation",
            description="PathAI without curated resource retrieval and attachment.",
            expected_strengths=["Isolates curriculum generation quality"],
            limitations=["Cannot validate resource relevance or coverage"],
            is_ablation=True,
        ),
        BaselineDefinition(
            system_variant="no_critic",
            label="No-Critic Ablation",
            description="PathAI without the structured critic review and revision decision.",
            expected_strengths=["Isolates first-pass curriculum/resource output"],
            limitations=["Higher risk of pacing, coverage, or explanation defects"],
            is_ablation=True,
        ),
        BaselineDefinition(
            system_variant="no_adapter",
            label="No-Adapter Ablation",
            description="PathAI without progress and quiz based replanning decisions.",
            expected_strengths=["Measures value of the initial plan before adaptation"],
            limitations=["Cannot respond to stuck learners or low quiz score patterns"],
            is_ablation=True,
        ),
    ]
