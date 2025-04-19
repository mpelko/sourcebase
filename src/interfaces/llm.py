from typing import Any, List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    content: str
    usage: dict[str, Any]  # tokens used, etc.


class LLM:
    """Interface for LLM implementations."""

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        raise NotImplementedError

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        raise NotImplementedError

    @property
    def max_context_length(self) -> int:
        """Get the maximum context length supported by the LLM."""
        raise NotImplementedError
