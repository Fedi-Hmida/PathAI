from typing import TypedDict

from app.assessment.constants import DifficultyLevel
from app.assessment.schemas import AssessmentQuestion


class QuestionBlueprint(TypedDict):
    topic: str
    prompt: str
    expected_concepts: list[str]
    skill_tags: list[str]


def build_question_bank(goal: str, target_level: DifficultyLevel) -> list[AssessmentQuestion]:
    domain = _infer_domain(goal)
    difficulty_plan = _difficulty_plan(target_level)
    blueprints = _domain_blueprints(domain)

    questions: list[AssessmentQuestion] = []
    for index, blueprint in enumerate(blueprints, start=1):
        difficulty = difficulty_plan[(index - 1) % len(difficulty_plan)]
        questions.append(
            AssessmentQuestion(
                question_id=f"{domain}-{index}",
                topic=blueprint["topic"],
                prompt=blueprint["prompt"],
                difficulty=difficulty,
                expected_concepts=blueprint["expected_concepts"],
                skill_tags=blueprint["skill_tags"],
                source="question_bank",
            )
        )
    return questions


def select_question(
    question_bank: list[AssessmentQuestion],
    asked_question_ids: set[str],
    preferred_difficulty: DifficultyLevel,
) -> AssessmentQuestion:
    for question in question_bank:
        is_unasked = question.question_id not in asked_question_ids
        is_preferred_level = question.difficulty == preferred_difficulty
        if is_unasked and is_preferred_level:
            return question
    for question in question_bank:
        if question.question_id not in asked_question_ids:
            return question
    return question_bank[-1]


def _difficulty_plan(target_level: DifficultyLevel) -> list[DifficultyLevel]:
    if target_level == "advanced":
        return ["intermediate", "advanced", "advanced", "intermediate"]
    if target_level == "beginner":
        return ["beginner", "beginner", "intermediate", "beginner"]
    return ["beginner", "intermediate", "intermediate", "advanced"]


def _infer_domain(goal: str) -> str:
    normalized = goal.lower()
    if "rag" in normalized or "retrieval" in normalized:
        return "rag"
    if "nlp" in normalized or "language" in normalized:
        return "nlp"
    if "computer vision" in normalized or "vision" in normalized:
        return "cv"
    if "backend" in normalized or "api" in normalized:
        return "backend"
    return "ai"


def _domain_blueprints(domain: str) -> list[QuestionBlueprint]:
    common: dict[str, list[QuestionBlueprint]] = {
        "rag": [
            {
                "topic": "Embeddings",
                "prompt": "Explain what an embedding represents in a RAG system.",
                "expected_concepts": ["vector representation", "semantic similarity"],
                "skill_tags": ["rag", "embeddings"],
            },
            {
                "topic": "Chunking",
                "prompt": "Why does chunk size matter when building a retrieval pipeline?",
                "expected_concepts": [
                    "context window",
                    "retrieval precision",
                    "semantic coherence",
                ],
                "skill_tags": ["rag", "chunking"],
            },
            {
                "topic": "Vector Search",
                "prompt": (
                    "Describe how a vector database helps retrieve relevant context for an LLM."
                ),
                "expected_concepts": [
                    "nearest neighbors",
                    "similarity search",
                    "indexed embeddings",
                ],
                "skill_tags": ["rag", "retrieval"],
            },
            {
                "topic": "Reranking",
                "prompt": "What problem does reranking solve after initial retrieval?",
                "expected_concepts": ["relevance ordering", "top-k results", "precision"],
                "skill_tags": ["rag", "reranking"],
            },
            {
                "topic": "Grounded Generation",
                "prompt": "How does RAG reduce hallucination compared with a plain LLM answer?",
                "expected_concepts": [
                    "grounded context",
                    "source documents",
                    "reduced hallucination",
                ],
                "skill_tags": ["rag", "generation"],
            },
            {
                "topic": "RAG Evaluation",
                "prompt": "Name one metric or method for evaluating retrieval quality.",
                "expected_concepts": ["precision", "recall", "relevance"],
                "skill_tags": ["rag", "evaluation"],
            },
            {
                "topic": "Prompt Injection",
                "prompt": (
                    "What is one security risk when retrieved documents are inserted "
                    "into an LLM prompt?"
                ),
                "expected_concepts": [
                    "prompt injection",
                    "untrusted context",
                    "instruction isolation",
                ],
                "skill_tags": ["rag", "security"],
            },
            {
                "topic": "RAG Architecture",
                "prompt": "List the main stages of a production RAG pipeline.",
                "expected_concepts": ["ingestion", "embedding", "retrieval", "generation"],
                "skill_tags": ["rag", "architecture"],
            },
        ],
        "ai": [
            {
                "topic": "Machine Learning Basics",
                "prompt": "Explain the difference between training data and test data.",
                "expected_concepts": ["generalization", "evaluation", "unseen data"],
                "skill_tags": ["ml", "evaluation"],
            },
            {
                "topic": "Model Evaluation",
                "prompt": "Why is accuracy sometimes a weak metric for classification?",
                "expected_concepts": ["class imbalance", "precision", "recall"],
                "skill_tags": ["ml", "metrics"],
            },
            {
                "topic": "Neural Networks",
                "prompt": "What is the role of backpropagation in neural network training?",
                "expected_concepts": ["gradient", "loss", "weight update"],
                "skill_tags": ["deep-learning"],
            },
            {
                "topic": "LLM Basics",
                "prompt": "What does a token mean in the context of large language models?",
                "expected_concepts": ["text unit", "subword", "context window"],
                "skill_tags": ["llm"],
            },
            {
                "topic": "Prompting",
                "prompt": (
                    "Give one reason why structured output validation is useful "
                    "in LLM applications."
                ),
                "expected_concepts": ["schema", "reliability", "validation"],
                "skill_tags": ["llm", "structured-output"],
            },
            {
                "topic": "Data Quality",
                "prompt": (
                    "Why can poor data quality hurt an AI system even if the model is strong?"
                ),
                "expected_concepts": ["noise", "bias", "incorrect labels"],
                "skill_tags": ["data"],
            },
            {
                "topic": "Deployment",
                "prompt": "Name one reliability concern when deploying an AI-backed API.",
                "expected_concepts": ["latency", "timeout", "fallback"],
                "skill_tags": ["backend", "reliability"],
            },
            {
                "topic": "AI Safety",
                "prompt": (
                    "Why should user data be redacted before sending prompts to an LLM service?"
                ),
                "expected_concepts": ["privacy", "PII", "secret"],
                "skill_tags": ["security", "privacy"],
            },
        ],
    }

    if domain == "nlp":
        return common["ai"]
    if domain == "cv":
        return common["ai"]
    if domain == "backend":
        return common["ai"]
    return common.get(domain, common["ai"])
