import pytest
from pydantic import ValidationError

from app.llm import MockLLMClient, StructuredOutputRequest
from app.llm.structured_output_spike import (
    parse_structured_payload,
    run_mock_structured_output_spike,
)
from app.schemas.llm_spike import MiniCurriculumOutput, MiniKnowledgeMapOutput, MiniQuizOutput


@pytest.mark.asyncio
async def test_mock_llm_returns_valid_knowledge_map_output() -> None:
    client = MockLLMClient()
    request = StructuredOutputRequest(prompt="demo", schema_name="MiniKnowledgeMapOutput")

    result = await client.generate_structured(request, MiniKnowledgeMapOutput)

    assert result.concepts[0].concept_id == "retrieval_evaluation"
    assert result.concepts[0].classification == "weak"


@pytest.mark.asyncio
async def test_mock_llm_spike_supports_all_minimal_schemas() -> None:
    knowledge_map = await run_mock_structured_output_spike(MiniKnowledgeMapOutput)
    curriculum = await run_mock_structured_output_spike(MiniCurriculumOutput)
    quiz = await run_mock_structured_output_spike(MiniQuizOutput)

    assert knowledge_map.summary
    assert curriculum.weeks[0].topics
    assert quiz.questions[0].concept_ids


def test_malformed_structured_payload_fails_validation() -> None:
    with pytest.raises(ValidationError):
        parse_structured_payload({"concepts": [], "summary": ""}, MiniKnowledgeMapOutput)
