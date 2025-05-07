from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Enumeration for supported document types.

    Each member represents a file extension or format that the system can process.
    """

    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    TXT = "txt"
    MD = "md"


class Document(BaseModel):
    """Represents a document processed and stored by the system.

    Attributes:
        id: Unique identifier for the document (e.g., UUID or hash of content).
        title: The title of the document.
        author: Optional author of the document.
        publication_date: Optional publication date as a string (YYYY or YYYY-MM-DD).
        document_type: The type of the document, from the DocumentType enum.
        date_added: Timestamp indicating when the document was added to the system.
        file_path: Optional path or key to the original document file. This might be
                   relative or an identifier used by a specific DocumentStore.
        metadata: A dictionary for any other arbitrary metadata associated with the
                  document.
        source: Optional string indicating the origin of the document (e.g.,
                'file_upload', 'web_scrape').
    """

    id: str = Field(..., description="Unique identifier for the document")
    title: str = Field(..., description="Title of the document")
    author: Optional[str] = Field(None, description="Author of the document")
    publication_date: Optional[str] = Field(
        None, description="Publication date (YYYY or YYYY-MM-DD)"
    )
    document_type: DocumentType = Field(..., description="Type of the document")
    date_added: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the document was added",
    )
    file_path: Optional[str] = Field(
        None, description="Path or key to the original document file"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Other arbitrary metadata"
    )
    source: Optional[str] = Field(None, description="Origin of the document")


class TextChunk(BaseModel):
    """Represents a segment of text extracted from a document.

    These chunks are typically used for creating vector embeddings.

    Attributes:
        id: Unique identifier for the text chunk (e.g., f"{document_id}_chunk_{index}").
        document_id: Identifier of the document from which this chunk was extracted.
        text: The actual text content of the chunk.
        metadata: Metadata specific to this chunk (e.g., page number, section header,
                  position within the document).
    """

    id: str = Field(..., description="Unique identifier for the text chunk")
    document_id: str = Field(..., description="Identifier of the parent document")
    text: str = Field(..., description="The actual text content of the chunk")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata specific to this chunk"
    )


class SearchResult(BaseModel):
    """Represents a single item returned from a similarity search in the vector store.

    Attributes:
        chunk_id: Identifier of the matched text chunk.
        document_id: Identifier of the document containing the matched chunk.
        text: The text of the matched chunk.
        score: A numerical score indicating the relevance or similarity of the chunk
               to the search query. Higher scores typically mean higher relevance.
        chunk_metadata: Metadata associated with the matched text chunk.
    """

    chunk_id: str = Field(..., description="ID of the matched text chunk")
    document_id: str = Field(..., description="ID of the document containing the chunk")
    text: str = Field(..., description="Text of the matched chunk")
    score: float = Field(..., description="Similarity score of the search result")
    chunk_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata of the matched chunk"
    )
