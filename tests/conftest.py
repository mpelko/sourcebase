"""Common test fixtures and configuration."""

from typing import AsyncGenerator, List, Optional

import pytest

from src.interfaces.llm import LLM, LLMResponse, Message
from src.interfaces.vector_db import Vector, VectorDB


class MockVectorDB(VectorDB):
    """Mock implementation of VectorDB for testing."""

    def __init__(self):
        self.vectors: dict[str, Vector] = {}

    async def add_vectors(self, vectors: List[Vector]) -> None:
        for vector in vectors:
            self.vectors[vector.id] = vector

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> List[Vector]:
        # Simple mock implementation that returns all vectors
        return list(self.vectors.values())[:top_k]

    async def delete_vectors(self, vector_ids: List[str]) -> None:
        for vector_id in vector_ids:
            self.vectors.pop(vector_id, None)

    async def get_vector(self, vector_id: str) -> Optional[Vector]:
        return self.vectors.get(vector_id)


class MockLLM(LLM):
    """Mock implementation of LLM for testing."""

    def __init__(self):
        self.max_context_length = 4096

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        return LLMResponse(
            content="Mock response", usage={"prompt_tokens": 10, "completion_tokens": 5}
        )

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Return mock embeddings (all zeros)
        return [[0.0] * 1536 for _ in texts]


@pytest.fixture
async def mock_vector_db() -> AsyncGenerator[MockVectorDB, None]:
    """Fixture providing a mock vector database."""
    yield MockVectorDB()


@pytest.fixture
async def mock_llm() -> AsyncGenerator[MockLLM, None]:
    """Fixture providing a mock LLM."""
    yield MockLLM()
