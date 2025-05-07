from typing import Any, Dict, List, Optional, Set

from backend.src.interfaces import DocumentStore, MetadataStore, VectorStore
from backend.src.models import Document, DocumentType, SearchResult, TextChunk


class MockDocumentStore(DocumentStore):
    """Mock implementation of DocumentStore for testing purposes."""

    def __init__(self):
        self.documents_content: Dict[str, bytes] = {}
        self.saved_paths: Set[str] = set()

    async def save_document(
        self, file_content: bytes, original_filename: str, document_type: DocumentType
    ) -> str:
        # Simulate path generation, e.g., based on document_id or a unique name
        # For mock, let's use original_filename if unique, or add a counter
        file_path = f"mock_store/{original_filename}"
        # Ensure somewhat unique paths for mock testing if multiple saves happen
        count = 0
        while file_path in self.saved_paths:
            count += 1
            name, ext = (
                original_filename.rsplit(".", 1)
                if "." in original_filename
                else (original_filename, "")
            )
            file_path = f"mock_store/{name}_{count}{'.' + ext if ext else ''}"

        self.documents_content[file_path] = file_content
        self.saved_paths.add(file_path)
        # print(f"MockDocumentStore: Saved {original_filename} to {file_path}")
        return file_path

    async def load_document(self, file_path: str) -> bytes:
        if file_path not in self.documents_content:
            raise FileNotFoundError(f"Document not found at path: {file_path}")
        # print(f"MockDocumentStore: Loaded document from {file_path}")
        return self.documents_content[file_path]

    async def delete_document(self, file_path: str) -> None:
        if file_path in self.documents_content:
            del self.documents_content[file_path]
            self.saved_paths.remove(file_path)
            # print(f"MockDocumentStore: Deleted document from {file_path}")
        # else: print(f"MockDocumentStore: No document to delete at {file_path}")
        pass  # Deletion is silent if not found, or could raise error


class MockMetadataStore(MetadataStore):
    """Mock implementation of MetadataStore for testing purposes."""

    def __init__(self):
        self.metadata: Dict[str, Document] = {}

    async def add_document_metadata(self, document: Document) -> None:
        self.metadata[document.id] = document
        # print(f"MockMetadataStore: Added metadata for doc ID {document.id}")

    async def get_document_metadata(self, document_id: str) -> Optional[Document]:
        # print(f"MockMetadataStore: Getting metadata for doc ID {document_id}")
        return self.metadata.get(document_id)

    async def list_documents_metadata(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> List[Document]:
        # print(f"MockMetadataStore: Listing metadata with filters: {filters}")
        results = list(self.metadata.values())
        # Basic filtering (can be expanded)
        if filters:
            for key, value in filters.items():
                results = [doc for doc in results if getattr(doc, key, None) == value]

        # Basic sorting (can be expanded)
        if sort_by:
            results.sort(
                key=lambda doc: getattr(doc, sort_by, None),
                reverse=(sort_order == "desc"),
            )

        return results[offset : offset + limit]

    async def update_document_metadata(
        self, document_id: str, updates: Dict[str, Any]
    ) -> Optional[Document]:
        if document_id in self.metadata:
            doc = self.metadata[document_id]
            updated_doc_data = doc.model_dump().copy()
            updated_doc_data.update(updates)
            # Re-validate with Pydantic model
            try:
                self.metadata[document_id] = Document(**updated_doc_data)
                # print(f"MockMetadataStore: Updated metadata for doc ID {document_id}")
                return self.metadata[document_id]
            except Exception:  # Could be pydantic.ValidationError
                return None  # Or re-raise / log
        return None

    async def delete_document_metadata(self, document_id: str) -> bool:
        if document_id in self.metadata:
            del self.metadata[document_id]
            # print(f"MockMetadataStore: Deleted metadata for doc ID {document_id}")
            return True
        return False


class MockVectorStore(VectorStore):
    """Mock implementation of VectorStore for testing purposes."""

    def __init__(self):
        self.chunks: Dict[str, TextChunk] = {}
        self.embeddings: Dict[str, List[float]] = {}
        # print("MockVectorStore initialized")

    async def add_text_chunks(self, chunks_to_add: List[TextChunk]) -> List[str]:
        added_ids = []
        for chunk in chunks_to_add:
            self.chunks[chunk.id] = chunk
            # Simulate embedding generation if not present
            self.embeddings[chunk.id] = [0.1] * 128  # Dummy embedding
            added_ids.append(chunk.id)
        # print(f"MockVectorStore: Added chunks with IDs: {added_ids}")
        return added_ids

    async def search_similar_chunks(
        self,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        if not query_text and not query_embedding:
            raise ValueError("Either query_text or query_embedding must be provided.")
        if query_text and query_embedding:
            raise ValueError("Provide either query_text or query_embedding, not both.")

        # Mock search: return some chunks, possibly filtered
        # This is a very simplistic mock. Real tests would need sophisticated matching.
        results: List[SearchResult] = []
        candidate_chunks = list(self.chunks.values())

        if document_ids:
            candidate_chunks = [
                c for c in candidate_chunks if c.document_id in document_ids
            ]

        # Basic metadata filtering (can be expanded)
        if metadata_filter:
            temp_candidates = []
            for chunk in candidate_chunks:
                match = True
                for key, value in metadata_filter.items():
                    if chunk.metadata.get(key) != value:
                        match = False
                        break
                if match:
                    temp_candidates.append(chunk)
            candidate_chunks = temp_candidates

        for chunk in candidate_chunks:
            if len(results) < top_k:
                results.append(
                    SearchResult(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        text=chunk.text,
                        score=0.8,  # Dummy score
                        chunk_metadata=chunk.metadata,
                    )
                )
            else:
                break
        return results

    async def delete_document_chunks(self, document_id: str) -> bool:
        chunks_to_delete = [
            cid
            for cid, chunk in self.chunks.items()
            if chunk.document_id == document_id
        ]
        if not chunks_to_delete:
            return True  # No chunks for this doc, considered success
        deleted_count = 0
        for chunk_id in chunks_to_delete:
            if chunk_id in self.chunks:
                del self.chunks[chunk_id]
                if chunk_id in self.embeddings:
                    del self.embeddings[chunk_id]
                deleted_count += 1

        return deleted_count > 0 or not chunks_to_delete

    async def get_text_chunk(self, chunk_id: str) -> Optional[TextChunk]:
        return self.chunks.get(chunk_id)

    async def update_text_chunk(
        self, chunk_id: str, updates: Dict[str, Any]
    ) -> Optional[TextChunk]:
        if chunk_id in self.chunks:
            chunk = self.chunks[chunk_id]
            updated_data = chunk.model_dump().copy()
            updated_data.update(updates)
            try:
                self.chunks[chunk_id] = TextChunk(**updated_data)
                if "text" in updates:  # Simulate re-embedding if text changes
                    self.embeddings[chunk_id] = [0.2] * 128  # New dummy embedding
                return self.chunks[chunk_id]
            except Exception:
                return None
        return None
