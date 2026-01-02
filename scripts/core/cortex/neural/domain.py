"""Domain models for neural subsystem - Vector Store and Semantic Search.

This module defines the core domain entities for the Cortex neural subsystem,
following Domain-Driven Design principles with immutable dataclasses.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Type alias for embeddings (vector representations)
Embedding = list[float]


@dataclass(frozen=True)
class DocumentChunk:
    """Represents a chunk of a document with optional embedding.

    Attributes:
        content: The text content of the chunk
        source_file: Path to the source file
        line_start: Starting line number in the source file
        metadata: Additional metadata (tags, context, etc.)
        embedding: Optional vector embedding of the content
    """

    content: str
    source_file: Path
    line_start: int
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: Embedding | None = None


@dataclass(frozen=True)
class SearchResult:
    """Represents a search result with similarity score.

    Attributes:
        chunk: The matched document chunk
        score: Similarity score (higher is better)
    """

    chunk: DocumentChunk
    score: float
