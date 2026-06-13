from app.evaluation.schemas import BaselineDefinition


def get_baseline_definitions() -> list[BaselineDefinition]:
    return [
        BaselineDefinition(
            system_variant="static_expert",
            label="Static Expert Curriculum",
            description=(
                "A fixed expert-made curriculum for the broad goal category, without "
                "personalized assessment, RAG resources, or adaptation."
            ),
            expected_strengths=["Stable structure", "Easy to review manually"],
            limitations=["Not personalized", "No adaptive replanning", "No retrieval evidence"],
        ),
        BaselineDefinition(
            system_variant="single_agent_llm",
            label="Single-Agent LLM Baseline",
            description=(
                "One structured LLM call that generates a learning plan directly from "
                "the learner goal."
            ),
            expected_strengths=["Fast generation", "Simple orchestration"],
            limitations=["No explicit critique loop", "No curated resource grounding"],
        ),
        BaselineDefinition(
            system_variant="pathai_full",
            label="Full PathAI Multi-Stage Pipeline",
            description=(
                "Assessment, curriculum planning, curated resource retrieval, critic "
                "quality control, progress tracking, quizzes, and adaptation signals."
            ),
            expected_strengths=["Traceable stages", "Quality checks", "Adaptation-ready"],
            limitations=["Current evaluation is synthetic until real user study data exists"],
        ),
    ]
