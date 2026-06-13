class LLMError(Exception):
    """Base exception for LLM infrastructure failures."""


class LLMConfigurationError(LLMError):
    """Raised when the configured LLM provider is missing required settings."""


class LLMRequestError(LLMError):
    """Raised when an LLM request fails after retry handling."""


class LLMTimeoutError(LLMRequestError):
    """Raised when the LLM provider times out after retry handling."""


class LLMResponseError(LLMError):
    """Raised when the LLM provider returns an unsupported response shape."""


class StructuredOutputError(LLMError):
    """Base exception for structured output validation failures."""


class InvalidJSONError(StructuredOutputError):
    """Raised when LLM output cannot be parsed as JSON."""


class SchemaValidationError(StructuredOutputError):
    """Raised when parsed JSON does not match the target Pydantic schema."""
