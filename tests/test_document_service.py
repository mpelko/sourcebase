"""Tests for the DocumentService."""

import pytest

from src.services.document_service import DocumentService


@pytest.mark.asyncio
async def test_add_document(mock_vector_db, mock_llm):
    """Test adding a document."""
    service = DocumentService(mock_vector_db, mock_llm)
    doc_id = await service.add_document(
        text="Test document content", metadata={"title": "Test Document"}
    )

    # Verify the document was added
    vector = await mock_vector_db.get_vector(doc_id)
    assert vector is not None
    assert vector.text == "Test document content"
    assert vector.metadata["title"] == "Test Document"


@pytest.mark.asyncio
async def test_search_documents(mock_vector_db, mock_llm):
    """Test searching documents."""
    service = DocumentService(mock_vector_db, mock_llm)

    # Add some test documents
    await service.add_document("First document", {"title": "First"})
    await service.add_document("Second document", {"title": "Second"})

    # Search for documents
    results = await service.search_documents("document")
    assert len(results) == 2


@pytest.mark.asyncio
async def test_query_documents(mock_vector_db, mock_llm):
    """Test querying documents."""
    service = DocumentService(mock_vector_db, mock_llm)

    # Add a test document
    doc_id = await service.add_document(
        "This is a test document about Python programming.", {"title": "Python Test"}
    )

    # Get the document for context
    vector = await mock_vector_db.get_vector(doc_id)
    assert vector is not None

    # Query the document
    response = await service.query_documents("What is this document about?", [vector])

    assert response == "Mock response"  # From our mock LLM
