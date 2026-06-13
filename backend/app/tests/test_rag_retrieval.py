import pytest

from app.rag.reranker import rerank_with_mock_llm
from app.rag.schemas import ResourceRerankRequest, ResourceRetrievalRequest
from app.rag.service import ResourceService


def test_retrieves_resources_by_topic_subtopic_and_difficulty() -> None:
    service = ResourceService()

    result = service.retrieve_for_topic(
        ResourceRetrievalRequest(
            topic="Reranking",
            goal="Learn RAG systems",
            difficulty="advanced",
            subtopics=["neural retrieval"],
            top_k=2,
        )
    )

    assert result.candidates
    assert result.candidates[0].resource.title.startswith("ColBERT")
    assert result.candidates[0].difficulty_score == 1.0
    assert result.candidates[0].match_score > 0.4


def test_retrieval_uses_foundational_fallback_for_no_match() -> None:
    service = ResourceService()

    result = service.retrieve_for_topic(
        ResourceRetrievalRequest(
            topic="Quantum compiler design",
            goal="Learn an unrelated topic",
            difficulty="beginner",
            top_k=2,
        )
    )

    assert result.candidates
    assert all(
        candidate.retrieval_source == "foundational_fallback" for candidate in result.candidates
    )
    assert result.warnings == []


def test_retrieval_can_return_no_match_without_fallback() -> None:
    service = ResourceService()

    result = service.retrieve_for_topic(
        ResourceRetrievalRequest(
            topic="Quantum compiler design",
            difficulty="beginner",
            include_foundational_fallback=False,
        )
    )

    assert result.candidates == []
    assert result.warnings


@pytest.mark.asyncio
async def test_mock_llm_reranking_uses_structured_output_without_real_llm() -> None:
    service = ResourceService()
    retrieval = service.retrieve_for_topic(
        ResourceRetrievalRequest(
            topic="Embeddings",
            goal="Learn RAG systems",
            difficulty="beginner",
            top_k=2,
        )
    )

    reranked = await rerank_with_mock_llm(
        ResourceRerankRequest(
            goal="Learn RAG systems",
            topic="Embeddings",
            difficulty="beginner",
            candidates=retrieval.candidates,
            top_k=2,
        )
    )

    assert reranked.used_mock_llm is True
    assert reranked.ranked_candidates
    assert reranked.ranked_candidates[0].resource_id == retrieval.candidates[0].resource.resource_id
