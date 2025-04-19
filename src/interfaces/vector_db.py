from typing import Any

from pydantic import BaseModel


class Vector(BaseModel):
    id: str
    embedding: list[float]
    metadata: dict[str, Any]
    text: str


class VectorDB:
    """Interface for vector database implementations."""

    async def add_vectors(self, vectors: list[Vector]) -> None:
        """Add vectors to the database."""
        raise NotImplementedError

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[Vector]:
        """Search for similar vectors."""
        raise NotImplementedError

    async def delete_vectors(self, vector_ids: list[str]) -> None:
        """Delete vectors from the database."""
        raise NotImplementedError

    async def get_vector(self, vector_id: str) -> Vector | None:
        """Get a specific vector by ID."""
        raise NotImplementedError
