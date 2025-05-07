from typing import Any, Dict, List, Optional, Protocol

from .models import (  # Added DocumentType
    Document,
    DocumentType,
    SearchResult,
    TextChunk,
)


class DocumentStore(Protocol):
    """Interface for physical document storage operations.

    This protocol defines how raw document files are saved, loaded, and deleted,
    abstracting the underlying storage mechanism (e.g., local filesystem, cloud
    storage). All operations are designed to be asynchronous.
    """

    async def save_document(
        self, file_content: bytes, original_filename: str, document_type: DocumentType
    ) -> str:
        """Saves the raw content of a document.

        Args:
            file_content: The binary content of the file.
            original_filename: The original name of the file, which can be used for
                               generating a storage path or for metadata.
            document_type: The type of the document being saved.

        Returns:
            A unique string (e.g., file path or storage key) identifying the
            location of the saved document.
        """
        ...

    async def load_document(self, file_path: str) -> bytes:
        """Loads the raw content of a document given its storage path or key.

        Args:
            file_path: The unique path or key identifying the document in the store.

        Returns:
            The binary content of the document.

        Raises:
            FileNotFoundError: If the document at the given path is not found.
        """
        ...

    async def delete_document(self, file_path: str) -> None:
        """Deletes the physical document file from the store.

        Args:
            file_path: The unique path or key identifying the document in the store.
        """
        ...


class MetadataStore(Protocol):
    """Interface for managing metadata associated with documents.

    This protocol defines CRUD (Create, Read, Update, Delete) operations for
    document metadata, abstracting the database (e.g., SQLite, PostgreSQL).
    All operations are designed to be asynchronous.
    """

    async def add_document_metadata(self, document: Document) -> None:
        """Adds metadata for a new document to the store.

        Args:
            document: A Document object containing the metadata to be saved.
        """
        ...

    async def get_document_metadata(self, document_id: str) -> Optional[Document]:
        """Retrieves metadata for a specific document by its unique ID.

        Args:
            document_id: The unique identifier of the document.

        Returns:
            A Document object if found, otherwise None.
        """
        ...

    async def list_documents_metadata(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> List[Document]:
        """Lists document metadata with optional filtering, pagination, and sorting.

        Args:
            filters: A dictionary of field-value pairs to filter the documents.
                     (e.g., {"document_type": "pdf", "author": "John Doe"})
            offset: The number of documents to skip for pagination.
            limit: The maximum number of documents to return.
            sort_by: The field name to sort the documents by (e.g., 'date_added',
            'title').
            sort_order: The order of sorting, either 'asc' (ascending) or 'desc'
            (descending).

        Returns:
            A list of Document objects matching the criteria.
        """
        ...

    async def update_document_metadata(
        self, document_id: str, updates: Dict[str, Any]
    ) -> Optional[Document]:
        """Updates specific fields of a document's metadata.

        Args:
            document_id: The unique identifier of the document to update.
            updates: A dictionary where keys are field names (attributes of the
                     Document model) and values are their new values.

        Returns:
            The updated Document object if the update was successful and the
            document was found, otherwise None.
        """
        ...

    async def delete_document_metadata(self, document_id: str) -> bool:
        """Deletes a document's metadata from the store.

        Args:
            document_id: The unique identifier of the document whose metadata is to be
            deleted.

        Returns:
            True if the metadata was successfully deleted, False otherwise (e.g., if
            the document_id was not found).
        """
        ...


class VectorStore(Protocol):
    """Interface for managing and searching text embeddings.

    This protocol defines operations for adding text chunks, searching for similar
    chunks based on vector embeddings, and deleting chunks associated with documents.
    It abstracts the underlying vector database technology (e.g., FAISS, Pinecone).
    All operations are designed to be asynchronous.
    """

    async def add_text_chunks(self, chunks: List[TextChunk]) -> List[str]:
        """Adds text chunks to the vector store.

        If the TextChunk objects do not contain pre-computed embeddings, the
        implementing class is responsible for generating them before storage.

        Args:
            chunks: A list of TextChunk objects to be added.

        Returns:
            A list of unique identifiers for the chunks that were successfully added or
            updated.
        """
        ...

    async def search_similar_chunks(
        self,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Searches for text chunks semantically similar to a given query.

        The query can be provided either as raw text (which will be embedded by the
        store) or as a pre-computed vector embedding.

        Args:
            query_text: The raw text of the query. If provided, query_embedding should
                        be None.
            query_embedding: A pre-computed vector embedding for the query. If provided,
                             query_text should be None.
            top_k: The maximum number of similar chunks to return.
            document_ids: An optional list of document IDs to restrict the search to.
                          If provided, only chunks from these documents will be
                          considered.
            metadata_filter: An optional dictionary to filter chunks based on their
                             metadata. The exact filtering capabilities depend on the
                             The exact filtering capabilities depend on the underlying
                             vector store.

        Returns:
            A list of SearchResult objects, ordered by similarity score.

        Raises:
            ValueError: If neither query_text nor query_embedding is provided, or if
            both are.
        """
        ...

    async def delete_document_chunks(self, document_id: str) -> bool:
        """Deletes all text chunks associated with a specific document ID from the
        store.

        Args:
            document_id: The unique identifier of the document whose chunks are to be
            deleted.

        Returns:
            True if chunks were successfully deleted or if no chunks were found for the
            document_id, False if an error occurred during deletion.
        """
        ...

    async def get_text_chunk(self, chunk_id: str) -> Optional[TextChunk]:
        """Retrieves a specific text chunk by its unique ID.

        This method is optional and might not be supported by all vector store
        implementations, especially those that don't store the original text alongside
        embeddings.

        Args:
            chunk_id: The unique identifier of the text chunk.

        Returns:
            A TextChunk object if found, otherwise None.
        """
        ...

    async def update_text_chunk(
        self, chunk_id: str, updates: Dict[str, Any]
    ) -> Optional[TextChunk]:
        """Updates specific attributes of a text chunk, such as its text or metadata.

        If the text of a chunk is updated, it may require re-embedding, which should
        be handled by the implementing class.
        This method is optional and might not be supported by all vector store
        implementations.

        Args:
            chunk_id: The unique identifier of the chunk to update.
            updates: A dictionary where keys are field names (attributes of TextChunk)
                     and values are their new values.

        Returns:
            The updated TextChunk object if successful, otherwise None.
        """
        ...
