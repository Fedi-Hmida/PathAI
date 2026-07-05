from pydantic import BaseModel

from app.llm.client import StructuredModel, StructuredOutputRequest
from app.schemas.llm_spike import (
    MiniCurriculumOutput,
    MiniKnowledgeMapOutput,
    MiniQuizOutput,
)


class MockLLMClient:
    provider = "mock"
    model = "deterministic-spike"

    async def generate_structured(
        self,
        request: StructuredOutputRequest,
        output_schema: type[StructuredModel],
    ) -> StructuredModel:
        payload = self._payload_for_schema(output_schema)
        return output_schema.model_validate(payload)

    def _payload_for_schema(self, output_schema: type[BaseModel]) -> dict[str, object]:
        if output_schema is MiniKnowledgeMapOutput:
            return {
                "concepts": [
                    {
                        "concept_id": "retrieval_evaluation",
                        "label": "Retrieval evaluation",
                        "mastery_score": 0.35,
                        "classification": "weak",
                    }
                ],
                "summary": "The learner needs more practice with retrieval evaluation.",
            }
        if output_schema is MiniCurriculumOutput:
            return {
                "title": "RAG Foundations Sprint",
                "weeks": [
                    {
                        "week_number": 1,
                        "theme": "Retrieval basics",
                        "topics": ["RAG overview", "Retriever role"],
                    }
                ],
            }
        if output_schema is MiniQuizOutput:
            return {
                "questions": [
                    {
                        "prompt": "What does recall@k measure?",
                        "options": [
                            "Relevant items retrieved in the top k",
                            "Response fluency",
                            "Prompt length",
                            "Frontend latency",
                        ],
                        "correct_answer": "Relevant items retrieved in the top k",
                        "concept_ids": ["retrieval_evaluation"],
                    }
                ],
            }
        msg = f"No deterministic mock payload for schema {output_schema.__name__}"
        raise ValueError(msg)

