from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from backend.src.models import Document, DocumentType, SearchResult, TextChunk


def test_document_type_enum():
    """Tests the DocumentType enum members."""
    assert DocumentType.PDF == "pdf"
    assert DocumentType.DOCX == "docx"
    assert DocumentType.HTML == "html"
    assert DocumentType.TXT == "txt"
    assert DocumentType.MD == "md"


def test_document_creation_valid():
    """Tests successful creation of a Document model with valid data."""
    now = datetime.now(timezone.utc)
    doc_data = {
        "id": "doc_123",
        "title": "Test Document Title",
        "author": "Test Author",
        "publication_date": "2023-01-01",
        "document_type": DocumentType.PDF,
        "file_path": "/path/to/doc.pdf",
        "source": "file_upload",
        "metadata": {"custom_key": "custom_value"},
    }
    doc = Document(
        **doc_data, date_added=now
    )  # Pass date_added explicitly for consistent testing

    assert doc.id == "doc_123"
    assert doc.title == "Test Document Title"
    assert doc.author == "Test Author"
    assert doc.publication_date == "2023-01-01"
    assert doc.document_type == DocumentType.PDF
    assert abs((doc.date_added - now).total_seconds()) < 1  # Check if close to now
    assert doc.file_path == "/path/to/doc.pdf"
    assert doc.source == "file_upload"
    assert doc.metadata == {"custom_key": "custom_value"}


def test_document_creation_minimal():
    """Tests successful creation of a Document model with minimal required data."""
    doc_data: Dict[str, Any] = {
        "id": "doc_456",
        "title": "Minimal Document",
        "document_type": DocumentType.TXT,
    }
    doc = Document(**doc_data)

    assert doc.id == "doc_456"
    assert doc.title == "Minimal Document"
    assert doc.document_type == DocumentType.TXT
    assert doc.author is None
    assert doc.publication_date is None
    assert doc.file_path is None
    assert doc.source is None
    assert isinstance(doc.date_added, datetime)
    assert doc.metadata == {}


def test_document_validation_error_missing_required():
    """Tests Pydantic ValidationError when required fields are missing for Document."""
    with pytest.raises(ValidationError) as excinfo:
        Document(id="doc_789")  # Missing title and document_type
    errors = excinfo.value.errors()
    assert len(errors) == 2
    field_errors = {e["loc"][0] for e in errors}
    assert "title" in field_errors
    assert "document_type" in field_errors


def test_document_validation_error_invalid_type():
    """Tests Pydantic ValidationError for invalid document_type."""
    with pytest.raises(ValidationError):
        Document(
            id="doc_101", title="Invalid Type Doc", document_type="invalid_type_string"
        )


def test_text_chunk_creation_valid():
    """Tests successful creation of a TextChunk model."""
    chunk_data = {
        "id": "chunk_abc",
        "document_id": "doc_123",
        "text": "This is a sample text chunk.",
        "metadata": {"page": 1, "source_index": 0},
    }
    chunk = TextChunk(**chunk_data)
    assert chunk.id == "chunk_abc"
    assert chunk.document_id == "doc_123"
    assert chunk.text == "This is a sample text chunk."
    assert chunk.metadata == {"page": 1, "source_index": 0}


def test_text_chunk_validation_error_missing_required():
    """Tests Pydantic ValidationError for missing required fields in TextChunk."""
    with pytest.raises(ValidationError):
        TextChunk(id="chunk_def")  # Missing document_id and text


def test_search_result_creation_valid():
    """Tests successful creation of a SearchResult model."""
    result_data = {
        "chunk_id": "chunk_abc",
        "document_id": "doc_123",
        "text": "This is a sample text chunk.",
        "score": 0.95,
        "chunk_metadata": {"page": 1},
    }
    result = SearchResult(**result_data)
    assert result.chunk_id == "chunk_abc"
    assert result.document_id == "doc_123"
    assert result.text == "This is a sample text chunk."
    assert result.score == 0.95
    assert result.chunk_metadata == {"page": 1}


def test_search_result_validation_error_missing_required():
    """Tests Pydantic ValidationError for missing required fields in SearchResult."""
    with pytest.raises(ValidationError):
        SearchResult(chunk_id="res_xyz", score=0.5)  # Missing document_id, text
