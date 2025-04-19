from typing import Any, Optional

from ..interfaces.llm import LLM, Message
from ..interfaces.vector_db import Vector, VectorDB


class DocumentService:
    """Service for managing documents and interacting with them using LLMs."""

    def __init__(self, vector_db: VectorDB, llm: LLM):
        self.vector_db = vector_db
        self.llm = llm

    async def add_document(self, text: str, metadata: dict[str, Any]) -> str:
        """Add a document to the vector database."""
        # Get embeddings for the document
        embeddings = await self.llm.get_embeddings([text])

        # Create a vector
        vector = Vector(
            id=f"doc_{len(embeddings)}",  # Simple ID generation, should be improved
            embedding=embeddings[0],
            metadata=metadata,
            text=text,
        )

        # Add to vector database
        await self.vector_db.add_vectors([vector])
        return vector.id

    async def search_documents(
        self, query: str, top_k: int = 5, filter: Optional[dict[str, Any]] = None
    ) -> list[Vector]:
        """Search for relevant documents."""
        # Get embedding for the query
        query_embedding = (await self.llm.get_embeddings([query]))[0]

        # Search in vector database
        return await self.vector_db.search(
            query_embedding=query_embedding, top_k=top_k, filter=filter
        )

    async def query_documents(
        self,
        query: str,
        context_documents: list[Vector],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Query the documents using the LLM."""
        # Prepare the context
        context = "\n\n".join(doc.text for doc in context_documents)

        # Prepare messages
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))

        messages.append(
            Message(role="user", content=f"Context:\n{context}\n\nQuestion: {query}")
        )

        # Generate response
        response = await self.llm.generate(messages)
        return response.content
