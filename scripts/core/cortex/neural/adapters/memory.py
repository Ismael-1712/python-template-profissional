"""In-memory vector store adapter for testing and lightweight usage.

This adapter implements VectorStorePort using an in-memory list for storage
and simple cosine similarity for search operations.
"""

import json
import math
from pathlib import Path

from scripts.core.cortex.neural.domain import DocumentChunk, Embedding, SearchResult
from scripts.core.cortex.neural.ports import VectorStorePort


class InMemoryVectorStore(VectorStorePort):
    """In-memory implementation of vector store.

    Uses a simple list to store document chunks and implements
    cosine similarity for search operations. Suitable for testing
    and small-scale applications.

    Attributes:
        store_path: Optional path for persistence
        _chunks: Internal list of stored document chunks
    """

    def __init__(self, store_path: Path | None = None) -> None:
        """Initialize the in-memory vector store.

        Args:
            store_path: Optional path for persisting/loading data
        """
        self.store_path = store_path
        self._chunks: list[DocumentChunk] = []

    def add(self, chunks: list[DocumentChunk]) -> None:
        """Add document chunks to the vector store.

        Args:
            chunks: List of document chunks with embeddings

        Raises:
            ValueError: If any chunk is missing an embedding
        """
        for chunk in chunks:
            if chunk.embedding is None:
                msg = "All chunks must have an embedding"
                raise ValueError(msg)
            self._chunks.append(chunk)

    def search(
        self,
        query_embedding: Embedding,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Search for similar chunks using cosine similarity.

        Args:
            query_embedding: Vector embedding of the search query
            limit: Maximum number of results to return

        Returns:
            List of search results ordered by similarity score (descending)

        Raises:
            ValueError: If query embedding dimension doesn't match stored chunks
        """
        if not self._chunks:
            return []

        # Validate dimensions
        if self._chunks and self._chunks[0].embedding is not None:
            expected_dim = len(self._chunks[0].embedding)
            if len(query_embedding) != expected_dim:
                msg = (
                    f"Query embedding dimension {len(query_embedding)} "
                    f"doesn't match store dimension {expected_dim}"
                )
                raise ValueError(msg)

        # Calculate similarity for all chunks
        results: list[SearchResult] = []
        for chunk in self._chunks:
            if chunk.embedding is not None:
                similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                results.append(SearchResult(chunk=chunk, score=similarity))

        # Sort by score (descending) and limit
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def persist(self) -> None:
        """Persist the vector store to disk as JSON.

        Raises:
            ValueError: If store_path is not set
        """
        if self.store_path is None:
            msg = "Cannot persist without store_path"
            raise ValueError(msg)

        # Serialize chunks to dict format
        serialized = {
            "chunks": [
                {
                    "content": chunk.content,
                    "source_file": str(chunk.source_file),
                    "line_start": chunk.line_start,
                    "metadata": chunk.metadata,
                    "embedding": chunk.embedding,
                }
                for chunk in self._chunks
            ]
        }

        # Write to file
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("w") as f:
            json.dump(serialized, f, indent=2)

    def load(self) -> None:
        """Load the vector store from disk.

        Raises:
            ValueError: If store_path is not set
            FileNotFoundError: If the store file doesn't exist
        """
        if self.store_path is None:
            msg = "Cannot load without store_path"
            raise ValueError(msg)

        if not self.store_path.exists():
            msg = f"Store file not found: {self.store_path}"
            raise FileNotFoundError(msg)

        # Read from file
        with self.store_path.open("r") as f:
            data = json.load(f)

        # Deserialize chunks
        self._chunks = [
            DocumentChunk(
                content=chunk_data["content"],
                source_file=Path(chunk_data["source_file"]),
                line_start=chunk_data["line_start"],
                metadata=chunk_data["metadata"],
                embedding=chunk_data["embedding"],
            )
            for chunk_data in data["chunks"]
        ]

    def _cosine_similarity(self, vec1: Embedding, vec2: Embedding) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0 to 1, where 1 is identical)
        """
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=True))

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)
