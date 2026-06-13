import pytest

from app.prompts import PromptNotFoundError, PromptRenderError, get_prompt_registry


def test_prompt_registry_loads_and_renders_template() -> None:
    registry = get_prompt_registry()

    prompt = registry.render("llm_health_check", {"context": "test context"})

    assert prompt.name == "llm_health_check"
    assert prompt.version == "v1"
    assert "Prompt-Version: v1" in prompt.content
    assert "test context" in prompt.content


def test_prompt_registry_missing_prompt_raises_clear_error() -> None:
    registry = get_prompt_registry()

    with pytest.raises(PromptNotFoundError):
        registry.load_template("missing_prompt")


def test_prompt_registry_missing_variable_raises_clear_error() -> None:
    registry = get_prompt_registry()

    with pytest.raises(PromptRenderError):
        registry.render("assessment_question_draft", {"goal": "Learn RAG"})


def test_prompt_registry_renders_resource_rerank_prompt() -> None:
    registry = get_prompt_registry()

    prompt = registry.render(
        "resource_rerank",
        {
            "learner_goal": "Learn RAG systems",
            "topic": "Vector search",
            "difficulty": "intermediate",
            "knowledge_map_context": '{"weak": ["retrieval"], "missing": ["reranking"]}',
            "candidate_resources": '[{"title": "Vector Search Guide"}]',
            "required_output_schema": '{"ranked_resources": []}',
        },
    )

    assert prompt.name == "resource_rerank"
    assert "Vector search" in prompt.content
    assert "ranked_resources" in prompt.content
