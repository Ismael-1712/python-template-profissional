"""Port interfaces for neural subsystem - Hexagonal Architecture.

This module defines the abstract interfaces (ports) that adapters must implement
to provide embedding generation and vector storage capabilities to Cortex.
"""

from abc import ABC, abstractmethod

from scripts.core.cortex.neural.domain import DocumentChunk, Embedding, SearchResult


class EmbeddingPort(ABC):
    """Port for embedding generation services.

    Adapters implementing this port provide text-to-vector conversion
    using various embedding models (e.g., OpenAI, Sentence Transformers).
    """

    @abstractmethod
    def embed(self, text: str) -> Embedding:
        """Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Vector embedding as list of floats
        """
        ...

    @abstractmethod
    def batch_embed(self, texts: list[str]) -> list[Embedding]:
        """Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of input texts to embed

        Returns:
            List of vector embeddings
        """
        ...


class VectorStorePort(ABC):
    """Port for vector storage and similarity search.

    Adapters implementing this port provide persistent storage
    and efficient similarity search over document embeddings.
    """

    @abstractmethod
    def add(self, chunks: list[DocumentChunk]) -> None:
        """Add document chunks to the vector store.

        Args:
            chunks: List of document chunks with embeddings
        """
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: Embedding,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Search for similar chunks using query embedding.

        Args:
            query_embedding: Vector embedding of the search query
            limit: Maximum number of results to return

        Returns:
            List of search results ordered by similarity score (descending)
        """
        ...

    @abstractmethod
    def persist(self) -> None:
        """Persist the vector store to disk."""
        ...

    @abstractmethod
    def load(self) -> None:
        """Load the vector store from disk."""
        ...
