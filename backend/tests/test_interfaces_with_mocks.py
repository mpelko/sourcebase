import pytest

from backend.src.interfaces import (  # For type hinting
    DocumentStore,
    MetadataStore,
    VectorStore,
)
from backend.src.models import Document, DocumentType, TextChunk
from backend.tests.mocks.store_mocks import (
    MockDocumentStore,
    MockMetadataStore,
    MockVectorStore,
)


@pytest.fixture
def mock_doc_store() -> DocumentStore:
    return MockDocumentStore()


@pytest.fixture
def mock_meta_store() -> MetadataStore:
    return MockMetadataStore()


@pytest.fixture
def mock_vec_store() -> VectorStore:
    return MockVectorStore()


@pytest.mark.asyncio
async def test_mock_document_store_save_load_delete(mock_doc_store: MockDocumentStore):
    """Tests save, load, and delete operations for MockDocumentStore."""
    file_content = b"This is a test PDF content."
    original_filename = "test_doc.pdf"
    doc_type = DocumentType.PDF

    # Save
    file_path = await mock_doc_store.save_document(
        file_content, original_filename, doc_type
    )
    assert file_path.startswith("mock_store/")
    assert original_filename in file_path
    assert file_path in mock_doc_store.saved_paths
    assert mock_doc_store.documents_content[file_path] == file_content

    # Load
    loaded_content = await mock_doc_store.load_document(file_path)
    assert loaded_content == file_content

    # Load non-existent
    with pytest.raises(FileNotFoundError):
        await mock_doc_store.load_document("mock_store/non_existent.pdf")

    # Delete
    await mock_doc_store.delete_document(file_path)
    assert file_path not in mock_doc_store.saved_paths
    assert file_path not in mock_doc_store.documents_content

    # Delete non-existent (should not raise error)
    await mock_doc_store.delete_document("mock_store/non_existent.pdf")


@pytest.mark.asyncio
async def test_mock_metadata_store_add_get_list_delete(
    mock_meta_store: MockMetadataStore,
):
    """Tests add, get, list, and delete operations for MockMetadataStore."""
    doc1_data = {
        "id": "doc_001",
        "title": "Document Alpha",
        "document_type": DocumentType.MD,
        "author": "Author A",
        "publication_date": "2023",
    }
    doc1 = Document(**doc1_data)

    doc2_data = {
        "id": "doc_002",
        "title": "Document Beta PDF",
        "document_type": DocumentType.PDF,
        "author": "Author B",
        "publication_date": "2024-01-01",
    }
    doc2 = Document(**doc2_data)

    # Add
    await mock_meta_store.add_document_metadata(doc1)
    await mock_meta_store.add_document_metadata(doc2)
    assert len(mock_meta_store.metadata) == 2

    # Get
    retrieved_doc1 = await mock_meta_store.get_document_metadata("doc_001")
    assert retrieved_doc1 is not None
    assert retrieved_doc1.title == "Document Alpha"

    retrieved_non_existent = await mock_meta_store.get_document_metadata("doc_999")
    assert retrieved_non_existent is None

    # List (all)
    all_docs = await mock_meta_store.list_documents_metadata()
    assert len(all_docs) == 2

    # List (filtered)
    pdf_docs = await mock_meta_store.list_documents_metadata(
        filters={"document_type": DocumentType.PDF}
    )
    assert len(pdf_docs) == 1
    assert pdf_docs[0].id == "doc_002"

    # List (sorted and paginated - basic check)
    sorted_docs = await mock_meta_store.list_documents_metadata(
        sort_by="title", sort_order="asc", limit=1
    )
    assert len(sorted_docs) == 1
    assert sorted_docs[0].id == "doc_001"  # Alpha before Beta

    # Update
    update_data = {"title": "Document Alpha (Updated)", "author": "Author A Revised"}
    updated_doc = await mock_meta_store.update_document_metadata("doc_001", update_data)
    assert updated_doc is not None
    assert updated_doc.title == "Document Alpha (Updated)"
    assert updated_doc.author == "Author A Revised"

    retrieved_updated_doc1 = await mock_meta_store.get_document_metadata("doc_001")
    assert retrieved_updated_doc1.title == "Document Alpha (Updated)"

    # Delete
    assert await mock_meta_store.delete_document_metadata("doc_001") is True
    assert len(mock_meta_store.metadata) == 1
    assert (
        await mock_meta_store.delete_document_metadata("doc_999") is False
    )  # Non-existent


@pytest.mark.asyncio
async def test_mock_vector_store_add_search_delete(mock_vec_store: MockVectorStore):
    """Tests add, search, and delete operations for MockVectorStore."""
    chunk1 = TextChunk(
        id="chunk_1_1", document_id="doc_1", text="First chunk from doc1 about apples."
    )
    chunk2 = TextChunk(
        id="chunk_1_2",
        document_id="doc_1",
        text="Second chunk from doc1 about oranges.",
    )
    chunk3 = TextChunk(
        id="chunk_2_1",
        document_id="doc_2",
        text="First chunk from doc2 also about apples.",
    )

    # Add
    added_ids = await mock_vec_store.add_text_chunks([chunk1, chunk2, chunk3])
    assert len(added_ids) == 3
    assert "chunk_1_1" in mock_vec_store.chunks
    assert "chunk_1_1" in mock_vec_store.embeddings

    # Get chunk
    retrieved_chunk = await mock_vec_store.get_text_chunk("chunk_1_1")
    assert retrieved_chunk is not None
    assert retrieved_chunk.text == "First chunk from doc1 about apples."

    # Search (simple mock search)
    search_results = await mock_vec_store.search_similar_chunks(
        query_text="apples", top_k=2
    )
    assert (
        len(search_results) <= 2
    )  # Mock returns up to all available if less than top_k
    # A more sophisticated mock would allow asserting specific content based on query

    # Search with document_id filter
    doc1_results = await mock_vec_store.search_similar_chunks(
        query_text="anything", document_ids=["doc_1"]
    )
    assert all(res.document_id == "doc_1" for res in doc1_results)
    assert len(doc1_results) == 2  # chunk_1_1, chunk_1_2

    doc2_results = await mock_vec_store.search_similar_chunks(
        query_text="anything", document_ids=["doc_2"]
    )
    assert all(res.document_id == "doc_2" for res in doc2_results)
    assert len(doc2_results) == 1  # chunk_2_1

    # Update chunk
    updated_chunk = await mock_vec_store.update_text_chunk(
        "chunk_1_1", {"text": "Updated text about apples and pears"}
    )
    assert updated_chunk is not None
    assert updated_chunk.text == "Updated text about apples and pears"
    retrieved_updated_chunk = await mock_vec_store.get_text_chunk("chunk_1_1")
    assert retrieved_updated_chunk.text == "Updated text about apples and pears"

    # Delete document chunks
    assert await mock_vec_store.delete_document_chunks("doc_1") is True
    assert "chunk_1_1" not in mock_vec_store.chunks
    assert "chunk_1_2" not in mock_vec_store.chunks
    assert "chunk_1_1" not in mock_vec_store.embeddings
    assert "chunk_2_1" in mock_vec_store.chunks  # Chunks from doc_2 should remain

    assert (
        await mock_vec_store.delete_document_chunks("doc_non_existent") is True
    )  # Should be true if no chunks
