import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiosqlite

from ..interfaces import MetadataStore
from ..models import Document, DocumentType

# Set up logger for this module
logger = logging.getLogger(__name__)

# Default database URL, can be overridden by environment variable or constructor
# For consistency with Flask app, let's ensure this default path is relative to
# backend/ or an absolute path. If METADATA_DATABASE_URL is set in app.config,
# that should be used. For now, using a path that would typically resolve inside
# `backend/` if app runs from there. Or, it could be defined in the Flask app's
# config and passed to the store.
DEFAULT_DB_PATH = os.path.join(
    os.getcwd(), "metadata.db"
)  # Fallback, ideally get from app config
DATABASE_URL: str = os.environ.get(
    "METADATA_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}"
)


def get_db_path() -> str:
    if DATABASE_URL.startswith("sqlite:///./"):
        # Relative path from where the app is run.
        # If app runs from /Users/mpelko/ws/sourcebase, this will be
        # /Users/mpelko/ws/sourcebase/backend/src/instance/metadata.db
        # This should align with where Flask's app.instance_path might be if
        # configured. For now, let's assume instance_path is preferred.
        # This needs to be consistent with the Flask app's database configuration.
        # The path from your Flask app was 'sqlite:///instance/sourcebase.db'
        # Let's aim for consistency with that.
        return DATABASE_URL.replace(
            "sqlite:///", "", 1
        )  # Remove only the first instance
    elif DATABASE_URL.startswith("sqlite:///"):
        return DATABASE_URL.replace("sqlite:///", "", 1)  # Absolute path
    else:  # Assume it's just a path
        return DATABASE_URL


async def get_db_connection(db_path: Optional[str] = None) -> aiosqlite.Connection:
    actual_db_path: str = db_path or get_db_path()

    # Ensure the directory for the database exists
    db_dir: str = os.path.dirname(actual_db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn: aiosqlite.Connection = await aiosqlite.connect(actual_db_path)
    conn.row_factory = aiosqlite.Row
    return conn


async def create_metadata_tables(conn: aiosqlite.Connection) -> None:
    """Creates metadata tables on the given database connection if they don't exist."""
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT,
        publication_date TEXT,
        document_type TEXT NOT NULL,
        date_added TIMESTAMP NOT NULL,
        file_path TEXT
    );
    """)
    await conn.commit()


class SQLiteMetadataStore(MetadataStore):
    """
    Asynchronous SQLite implementation of the MetadataStore protocol using aiosqlite.
    Manages a single persistent connection for its lifetime.
    """

    def __init__(self, database_path: Optional[str] = None) -> None:
        self.db_path: str = database_path or get_db_path()
        self._conn: Optional[aiosqlite.Connection] = None
        self._initialized: bool = False

    async def initialize(self) -> None:
        """Initializes the database connection and creates tables if they don't
        exist.
        """
        if self._initialized:
            return

        db_dir: str = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await create_metadata_tables(self._conn)
        self._initialized = True
        logger.info(f"SQLiteMetadataStore initialized for {self.db_path}")

    async def close(self) -> None:
        """Closes the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            self._initialized = False  # Mark as uninitialized after closing
            logger.info(f"SQLiteMetadataStore connection closed for {self.db_path}")

    async def _ensure_initialized(self) -> None:
        """Ensures the database is initialized before performing an operation."""
        if not self._initialized or self._conn is None:
            raise RuntimeError(
                "Database not initialized or connection is closed. "
                "Call await store.initialize() first or ensure it has not been closed."
            )

    def _row_to_document(self, row: aiosqlite.Row) -> Optional[Document]:
        if not row:
            return None
        try:
            date_added_val: Any = row["date_added"]
            date_added_dt: datetime
            if isinstance(date_added_val, str):
                date_added_dt = datetime.fromisoformat(date_added_val)
            elif isinstance(date_added_val, (int, float)):
                date_added_dt = datetime.fromtimestamp(date_added_val)
            elif isinstance(date_added_val, datetime):
                date_added_dt = date_added_val
            else:
                logger.error(
                    f"Unexpected type for date_added: {type(date_added_val)}. "
                    f"Value: {date_added_val}"
                )
                try:
                    date_added_dt = datetime.fromisoformat(str(date_added_val))
                except ValueError:
                    logger.error(
                        f"Could not parse date_added: {date_added_val} "
                        f"for document id {row['id']}"
                    )
                    return None

            return Document(
                id=row["id"],
                title=row["title"],
                author=row["author"],
                publication_date=row["publication_date"],
                document_type=DocumentType(row["document_type"]),
                date_added=date_added_dt,
                file_path=row["file_path"],
                metadata={},
                source=None,
            )
        except Exception as e:
            logger.error(
                f"Error converting row to Document: {e}. Row data: {dict(row)}"
            )
            return None

    # --- Interface methods ---
    # Note: These are synchronous implementations of an async interface.

    async def add_document_metadata(self, document: Document) -> None:
        await self._ensure_initialized()
        assert self._conn is not None  # For type checker, after _ensure_initialized
        try:
            await self._conn.execute(
                """ 
                INSERT INTO documents (id, title, author, publication_date, document_type, date_added, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?) 
            """,  # noqa: E501
                (
                    document.id,
                    document.title,
                    document.author,
                    document.publication_date,
                    document.document_type.value,
                    document.date_added.isoformat(),
                    document.file_path,
                ),
            )
            await self._conn.commit()
        except aiosqlite.IntegrityError as e:
            logger.error(f"Error adding document metadata for {document.id}: {e}")
            raise

    async def get_document_metadata(self, document_id: str) -> Optional[Document]:
        await self._ensure_initialized()
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            return self._row_to_document(row)
        return None

    async def list_documents_metadata(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> List[Document]:
        await self._ensure_initialized()
        assert self._conn is not None

        query: str = "SELECT * FROM documents"
        params: List[Any] = []

        if filters:
            conditions: List[str] = []
            for key, value in filters.items():
                if value is not None:
                    if key == "document_type" and isinstance(value, DocumentType):
                        conditions.append(f"{key} = ?")
                        params.append(value.value)
                    elif key in [
                        "id",
                        "title",
                        "author",
                        "publication_date",
                        "file_path",
                    ]:
                        conditions.append(f"{key} = ?")
                        params.append(value)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        if sort_by in [
            "id",
            "title",
            "author",
            "publication_date",
            "document_type",
            "date_added",
        ]:
            order: str = "DESC" if sort_order.lower() == "desc" else "ASC"
            query += f" ORDER BY {sort_by} {order}"

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with self._conn.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()

        return [
            doc
            for row_data in rows
            if (doc := self._row_to_document(row_data)) is not None
        ]

    async def update_document_metadata(
        self, document_id: str, updates: Dict[str, Any]
    ) -> Optional[Document]:
        await self._ensure_initialized()
        assert self._conn is not None

        fields_to_update: List[str] = []
        update_params: List[Any] = []
        allowed_fields: List[str] = [
            "title",
            "author",
            "publication_date",
            "document_type",
            "file_path",
        ]

        for key, value in updates.items():
            if key in allowed_fields:
                fields_to_update.append(f"{key} = ?")
                if key == "document_type" and isinstance(value, DocumentType):
                    update_params.append(value.value)
                else:
                    update_params.append(value)

        if not fields_to_update:
            return await self.get_document_metadata(document_id)

        query = f"UPDATE documents SET {', '.join(fields_to_update)} WHERE id = ?"
        update_params.append(document_id)

        try:
            cursor = await self._conn.execute(query, tuple(update_params))
            await self._conn.commit()
            if cursor.rowcount == 0:
                await (
                    cursor.close()
                )  # Close cursor if no rows updated before returning None
                return None
            await cursor.close()  # Ensure cursor is closed after successful update
        except aiosqlite.Error as e:
            logger.error(f"Error updating document metadata for {document_id}: {e}")
            # Assuming rollback is handled by aiosqlite if commit fails,
            # or manage explicitly if needed
            return None

        return await self.get_document_metadata(document_id)

    async def delete_document_metadata(self, document_id: str) -> bool:
        await self._ensure_initialized()
        assert self._conn is not None
        try:
            cursor = await self._conn.execute(
                "DELETE FROM documents WHERE id = ?", (document_id,)
            )
            await self._conn.commit()
            rowcount = cursor.rowcount
            await cursor.close()
            return bool(rowcount > 0)  # Explicitly cast to bool
        except aiosqlite.Error as e:
            logger.error(f"Error deleting document metadata for {document_id}: {e}")
            return False


# Example Usage (for testing or direct script execution)
async def main_example() -> None:
    # Basic logging configuration for when script is run directly
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Running SQLiteMetadataStore example...")
    # Use a specific DB for this example to avoid conflicts and allow easy cleanup
    test_db_path: str = "./test_metadata_store_async.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        logger.info(f"Removed existing test database: {test_db_path}")

    store: SQLiteMetadataStore = SQLiteMetadataStore(database_path=test_db_path)
    try:
        await store.initialize()
        logger.info(f"SQLiteMetadataStore initialized with database: {store.db_path}")
        logger.info("Database and table should be initialized.")

        # Create sample documents using the Document model from src.models
        doc1_id: str = "test_doc_001"
        doc1: Document = Document(
            id=doc1_id,
            title="Test Document Alpha",
            author="Author One",
            publication_date="2023-01-15",
            document_type=DocumentType.TXT,  # Using DocumentType enum
            date_added=datetime.utcnow(),  # Using datetime object
            file_path="/path/to/alpha.txt",
            metadata={
                "custom_key": "custom_value"
            },  # Will not be stored in this schema version
            source="file_upload",  # Will not be stored
        )

        doc2_id: str = "test_doc_002"
        doc2: Document = Document(
            id=doc2_id,
            title="Test Document Beta",
            author="Author Two",
            publication_date="2024",
            document_type=DocumentType.PDF,
            date_added=datetime.utcnow(),
            file_path="/path/to/beta.pdf",
            source=None,  # Explicitly provide source=None
        )

        logger.info("\n--- Testing add_document_metadata ---")
        try:
            await store.add_document_metadata(doc1)
            logger.info(f"Added document: {doc1.title} (ID: {doc1.id})")
            await store.add_document_metadata(doc2)
            logger.info(f"Added document: {doc2.title} (ID: {doc2.id})")
        except Exception as e:
            logger.error(f"Error during add: {e}")

        logger.info("\n--- Testing get_document_metadata ---")
        retrieved_doc1: Optional[Document] = await store.get_document_metadata(doc1_id)
        if retrieved_doc1:
            logger.info(
                f"Retrieved: {retrieved_doc1.title}, "
                f"Type: {retrieved_doc1.document_type.value}, "
                f"Path: {retrieved_doc1.file_path}"
            )
            assert retrieved_doc1.id == doc1_id
            assert retrieved_doc1.title == doc1.title
        else:
            logger.warning(f"Document {doc1_id} not found after add.")

        logger.info("\n--- Testing list_documents_metadata (all) ---")
        all_docs: List[Document] = await store.list_documents_metadata(limit=5)
        logger.info(f"Found {len(all_docs)} documents:")
        for d in all_docs:
            logger.info(
                f" - {d.title} (ID: {d.id}, "
                f"Added: {d.date_added.strftime('%Y-%m-%d %H:%M')})"
            )
        assert len(all_docs) >= 2  # Could be more if run multiple times without cleanup

        logger.info("\n--- Testing list_documents_metadata (filtered by type) ---")
        pdf_docs: List[Document] = await store.list_documents_metadata(
            filters={"document_type": DocumentType.PDF}
        )
        logger.info(f"Found {len(pdf_docs)} PDF documents:")
        for d in pdf_docs:
            logger.info(f" - {d.title} (Type: {d.document_type.value})")
            assert d.document_type == DocumentType.PDF

        logger.info("\n--- Testing list_documents_metadata (filtered by author) ---")
        author_one_docs: List[Document] = await store.list_documents_metadata(
            filters={"author": "Author One"}
        )
        logger.info(f"Found {len(author_one_docs)} documents by Author One:")
        for d in author_one_docs:
            logger.info(f" - {d.title} (Author: {d.author})")
            assert d.author == "Author One"

        logger.info("\n--- Testing list_documents_metadata (sorted by title asc) ---")
        sorted_docs: List[Document] = await store.list_documents_metadata(
            sort_by="title", sort_order="asc", limit=5
        )
        logger.info(f"Found {len(sorted_docs)} documents, sorted by title:")
        for d in sorted_docs:
            logger.info(f" - {d.title}")
        # Add assertion for order if docs are distinct enough

        logger.info("\n--- Testing update_document_metadata ---")
        updates: Dict[str, str] = {
            "title": "Test Document Alpha (Updated)",
            "author": "Author One (Revised)",
        }
        updated_doc1: Optional[Document] = await store.update_document_metadata(
            doc1_id, updates
        )
        if updated_doc1:
            logger.info(f"Updated: {updated_doc1.title}, Author: {updated_doc1.author}")
            assert updated_doc1.title == "Test Document Alpha (Updated)"
            assert updated_doc1.author == "Author One (Revised)"
        else:
            logger.warning(f"Document {doc1_id} not found for update or update failed.")

        retrieved_after_update: Optional[Document] = await store.get_document_metadata(
            doc1_id
        )
        if retrieved_after_update:
            logger.info(f"Retrieved after update: {retrieved_after_update.title}")
            assert retrieved_after_update.title == "Test Document Alpha (Updated)"

        logger.info("\n--- Testing delete_document_metadata ---")
        delete_success: bool = await store.delete_document_metadata(doc1_id)
        logger.info(f"Deletion of {doc1_id} was successful: {delete_success}")
        assert delete_success

        retrieved_after_delete: Optional[Document] = await store.get_document_metadata(
            doc1_id
        )
        if not retrieved_after_delete:
            logger.info(f"Document {doc1_id} successfully confirmed deleted.")
        else:
            logger.error(f"Document {doc1_id} still found after deletion attempt.")
        assert retrieved_after_delete is None

        # Test deleting non-existent document
        delete_non_existent_success: bool = await store.delete_document_metadata(
            "non_existent_id_123"
        )
        logger.info(
            "Deletion of non_existent_id_123 was successful: "
            f"{delete_non_existent_success}"
        )
        assert not delete_non_existent_success

    except Exception:
        logger.exception("An error occurred during the example run:")
    finally:
        await store.close()
        if os.path.exists(test_db_path):
            # os.remove(test_db_path) # Optionally leave db for inspection
            logger.info(f"\nCleaned up test database: {test_db_path}")
    logger.info("\nExample run finished.")


if __name__ == "__main__":
    asyncio.run(main_example())
