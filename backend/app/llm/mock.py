from collections.abc import Iterable

from app.llm.types import LLMMessage, LLMRequestOptions, LLMResponse


class MockLLMClient:
    def __init__(self, responses: Iterable[str] | None = None) -> None:
        self._responses = list(responses or [])
        self.calls: list[list[LLMMessage]] = []

    async def complete(
        self,
        messages: list[LLMMessage],
        options: LLMRequestOptions | None = None,
    ) -> LLMResponse:
        self.calls.append(messages)
        content = self._responses.pop(0) if self._responses else self._default_response()
        model = options.model if options and options.model else "mock-pathai-llm"
        return LLMResponse(
            content=content,
            model=model,
            finish_reason="stop",
            usage={"mock": True},
            raw={"mock": True, "content": content},
        )

    def _default_response(self) -> str:
        return (
            '{"status":"ok","message":"Mock LLM structured output validated.",'
            '"model":"mock-pathai-llm"}'
        )
