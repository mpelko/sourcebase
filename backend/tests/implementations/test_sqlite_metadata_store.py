import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict

import aiosqlite
import pytest

from backend.src.implementations.sqlite_metadata_store import (
    SQLiteMetadataStore,
)
from backend.src.models import Document, DocumentType


@pytest.fixture(scope="module")
def event_loop():
    """A module-scoped event loop.
    pytest-asyncio will use this for all tests in the module.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def temp_db_path() -> AsyncGenerator[str, None]:
    """Provides a temporary database path that is cleaned up after the test."""
    db_file = f"./test_metadata_store_async_{uuid.uuid4().hex}.db"
    yield db_file
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture
async def metadata_store(
    temp_db_path: str,
) -> AsyncGenerator[SQLiteMetadataStore, None]:
    """Provides an initialized instance of SQLiteMetadataStore with a temporary
    database."""
    store = SQLiteMetadataStore(database_path=temp_db_path)
    await store.initialize()
    yield store
    await store.close()


@pytest.fixture
def sample_doc1() -> Document:
    return Document(
        id="doc_test_1",
        title="Test Document Alpha",
        author="Author One",
        publication_date="2023-01-15",
        document_type=DocumentType.TXT,
        date_added=datetime.now(timezone.utc),  # Use timezone-aware datetime
        file_path="/path/to/alpha.txt",
        metadata={"custom_key": "value1"},  # Will not be stored by current schema
        source="test_upload",
    )


@pytest.fixture
def sample_doc2() -> Document:
    return Document(
        id="doc_test_2",
        title="Test Document Beta",
        author="Author Two",
        publication_date="2024",
        document_type=DocumentType.PDF,
        date_added=datetime.now(timezone.utc).replace(
            microsecond=0
        ),  # Ensure no microseconds for comparison
        file_path="/path/to/beta.pdf",
    )


@pytest.mark.asyncio
async def test_add_and_get_document(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document
):
    """Test adding a document and then retrieving it."""
    await metadata_store.add_document_metadata(sample_doc1)
    retrieved_doc = await metadata_store.get_document_metadata(sample_doc1.id)

    assert retrieved_doc is not None
    assert retrieved_doc.id == sample_doc1.id
    assert retrieved_doc.title == sample_doc1.title
    assert retrieved_doc.author == sample_doc1.author
    assert retrieved_doc.publication_date == sample_doc1.publication_date
    assert retrieved_doc.document_type == sample_doc1.document_type
    assert retrieved_doc.date_added.replace(
        microsecond=0
    ) == sample_doc1.date_added.replace(microsecond=0)
    assert retrieved_doc.file_path == sample_doc1.file_path
    assert retrieved_doc.metadata == {}
    assert retrieved_doc.source is None


@pytest.mark.asyncio
async def test_get_non_existent_document(metadata_store: SQLiteMetadataStore):
    """Test retrieving a non-existent document returns None."""
    assert await metadata_store.get_document_metadata("non_existent_id") is None


@pytest.mark.asyncio
async def test_add_duplicate_document_id(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document
):
    """Test that adding a document with a duplicate ID raises an IntegrityError."""
    await metadata_store.add_document_metadata(sample_doc1)
    with pytest.raises(aiosqlite.IntegrityError):
        await metadata_store.add_document_metadata(sample_doc1)


@pytest.mark.asyncio
async def test_list_documents_empty(metadata_store: SQLiteMetadataStore):
    """Test listing documents from an empty store."""
    assert await metadata_store.list_documents_metadata() == []


@pytest.mark.asyncio
async def test_list_documents_multiple(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document, sample_doc2: Document
):
    """Test listing multiple documents."""
    await metadata_store.add_document_metadata(sample_doc1)
    await metadata_store.add_document_metadata(sample_doc2)

    docs = await metadata_store.list_documents_metadata()
    assert len(docs) == 2
    doc_ids = {doc.id for doc in docs}
    assert sample_doc1.id in doc_ids
    assert sample_doc2.id in doc_ids


@pytest.mark.asyncio
async def test_list_documents_with_filter_type(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document, sample_doc2: Document
):
    """Test listing documents filtered by document_type."""
    await metadata_store.add_document_metadata(sample_doc1)  # TXT
    await metadata_store.add_document_metadata(sample_doc2)  # PDF

    txt_docs = await metadata_store.list_documents_metadata(
        filters={"document_type": DocumentType.TXT}
    )
    assert len(txt_docs) == 1
    assert txt_docs[0].id == sample_doc1.id
    assert txt_docs[0].document_type == DocumentType.TXT

    pdf_docs = await metadata_store.list_documents_metadata(
        filters={"document_type": DocumentType.PDF}
    )
    assert len(pdf_docs) == 1
    assert pdf_docs[0].id == sample_doc2.id
    assert pdf_docs[0].document_type == DocumentType.PDF


@pytest.mark.asyncio
async def test_list_documents_with_filter_author(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document, sample_doc2: Document
):
    """Test listing documents filtered by author."""
    await metadata_store.add_document_metadata(sample_doc1)  # Author One
    await metadata_store.add_document_metadata(sample_doc2)  # Author Two

    author_one_docs = await metadata_store.list_documents_metadata(
        filters={"author": "Author One"}
    )
    assert len(author_one_docs) == 1
    assert author_one_docs[0].id == sample_doc1.id


@pytest.mark.asyncio
async def test_list_documents_pagination(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document, sample_doc2: Document
):
    """Test pagination when listing documents."""
    docs_to_add = [
        sample_doc1,
        sample_doc2,
        Document(
            id="doc_test_3",
            title="C Doc",
            document_type=DocumentType.MD,
            date_added=datetime.now(timezone.utc),
        ),
        Document(
            id="doc_test_4",
            title="D Doc",
            document_type=DocumentType.TXT,
            date_added=datetime.now(timezone.utc),
        ),
        Document(
            id="doc_test_5",
            title="E Doc",
            document_type=DocumentType.HTML,
            date_added=datetime.now(timezone.utc),
        ),
    ]
    for doc_to_add in docs_to_add:
        existing_doc = await metadata_store.get_document_metadata(doc_to_add.id)
        if not existing_doc:
            await metadata_store.add_document_metadata(doc_to_add)
        else:
            await metadata_store.update_document_metadata(
                doc_to_add.id, {"title": doc_to_add.title}
            )

    all_docs_sorted_by_id = sorted(docs_to_add, key=lambda d: d.id)

    listed_docs = await metadata_store.list_documents_metadata(
        limit=2, sort_by="id", sort_order="asc"
    )
    assert len(listed_docs) == 2
    assert listed_docs[0].id == all_docs_sorted_by_id[0].id
    assert listed_docs[1].id == all_docs_sorted_by_id[1].id

    listed_docs_offset = await metadata_store.list_documents_metadata(
        limit=2, offset=2, sort_by="id", sort_order="asc"
    )
    assert len(listed_docs_offset) == 2
    assert listed_docs_offset[0].id == all_docs_sorted_by_id[2].id
    assert listed_docs_offset[1].id == all_docs_sorted_by_id[3].id

    listed_docs_offset_beyond = await metadata_store.list_documents_metadata(
        limit=2, offset=4, sort_by="id", sort_order="asc"
    )
    assert len(listed_docs_offset_beyond) == 1
    assert listed_docs_offset_beyond[0].id == all_docs_sorted_by_id[4].id


@pytest.mark.asyncio
async def test_list_documents_sorting(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document, sample_doc2: Document
):
    """Test sorting when listing documents."""
    doc3 = Document(
        id="doc_test_3",
        title="Another Test Doc",
        document_type=DocumentType.MD,
        date_added=datetime.now(timezone.utc),
    )
    await metadata_store.add_document_metadata(sample_doc1)
    await metadata_store.add_document_metadata(sample_doc2)
    await metadata_store.add_document_metadata(doc3)

    sorted_docs_asc = await metadata_store.list_documents_metadata(
        sort_by="title", sort_order="asc"
    )
    assert len(sorted_docs_asc) == 3
    assert sorted_docs_asc[0].title == "Another Test Doc"
    assert sorted_docs_asc[1].title == "Test Document Alpha"
    assert sorted_docs_asc[2].title == "Test Document Beta"

    sorted_docs_desc = await metadata_store.list_documents_metadata(
        sort_by="title", sort_order="desc"
    )
    assert len(sorted_docs_desc) == 3
    assert sorted_docs_desc[0].title == "Test Document Beta"
    assert sorted_docs_desc[1].title == "Test Document Alpha"
    assert sorted_docs_desc[2].title == "Another Test Doc"


@pytest.mark.asyncio
async def test_update_document(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document
):
    """Test updating an existing document's metadata."""
    await metadata_store.add_document_metadata(sample_doc1)

    updates: Dict[str, Any] = {
        "title": "Updated Title for Alpha",
        "author": "Author One Revised",
        "publication_date": "2023-02-28",
        "document_type": DocumentType.MD,
        "file_path": "/new/path/to/alpha.md",
    }
    updated_doc = await metadata_store.update_document_metadata(sample_doc1.id, updates)
    assert updated_doc is not None
    assert updated_doc.id == sample_doc1.id
    assert updated_doc.title == updates["title"]
    assert updated_doc.author == updates["author"]
    assert updated_doc.publication_date == updates["publication_date"]
    assert updated_doc.document_type == updates["document_type"]
    assert updated_doc.file_path == updates["file_path"]
    assert updated_doc.date_added.replace(
        microsecond=0
    ) == sample_doc1.date_added.replace(microsecond=0)

    refetched_doc = await metadata_store.get_document_metadata(sample_doc1.id)
    assert refetched_doc is not None
    assert refetched_doc.title == updates["title"]


@pytest.mark.asyncio
async def test_update_non_existent_document(metadata_store: SQLiteMetadataStore):
    """Test that updating a non-existent document returns None."""
    updates = {"title": "New Title"}
    assert (
        await metadata_store.update_document_metadata(
            "non_existent_id_for_update", updates
        )
    ) is None


@pytest.mark.asyncio
async def test_update_with_no_valid_fields(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document
):
    """Test updating with fields not in the whitelist or invalid fields."""
    await metadata_store.add_document_metadata(sample_doc1)
    updates = {
        "invalid_field": "some_value",
        "id": "new_id_attempt",
    }
    updated_doc = await metadata_store.update_document_metadata(sample_doc1.id, updates)

    assert updated_doc is not None
    assert updated_doc.title == sample_doc1.title
    assert updated_doc.author == sample_doc1.author


@pytest.mark.asyncio
async def test_delete_document(
    metadata_store: SQLiteMetadataStore, sample_doc1: Document
):
    """Test deleting an existing document."""
    await metadata_store.add_document_metadata(sample_doc1)
    assert (await metadata_store.get_document_metadata(sample_doc1.id)) is not None

    delete_success = await metadata_store.delete_document_metadata(sample_doc1.id)
    assert delete_success is True
    assert (await metadata_store.get_document_metadata(sample_doc1.id)) is None


@pytest.mark.asyncio
async def test_delete_non_existent_document(metadata_store: SQLiteMetadataStore):
    """Test that deleting a non-existent document returns False."""
    assert (
        await metadata_store.delete_document_metadata("non_existent_id_for_delete")
    ) is False


# Consider adding tests for date handling specifically, like various date formats for
# publication_date
# if the schema/logic were to support parsing them into a canonical form.
# Current schema stores publication_date as TEXT, so it's stored as provided.
