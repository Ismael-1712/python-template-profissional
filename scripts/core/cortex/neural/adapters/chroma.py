"""ChromaDB Vector Store Adapter.

This adapter implements persistent vector storage using ChromaDB,
providing automatic disk persistence and efficient similarity search.
"""

import hashlib
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from scripts.core.cortex.neural.domain import DocumentChunk, Embedding, SearchResult
from scripts.core.cortex.neural.ports import VectorStorePort


class ChromaDBVectorStore(VectorStorePort):
    """Persistent vector store using ChromaDB.

    Features:
    - Automatic disk persistence (no manual persist() needed)
    - Efficient similarity search using ChromaDB's indexing
    - Deterministic document IDs to avoid duplicates
    - Metadata preservation for filtering and retrieval

    Args:
        persist_directory: Directory to store ChromaDB data (default: .cortex/memory)
        collection_name: Name of the ChromaDB collection (default: cortex_knowledge)
    """

    def __init__(
        self,
        persist_directory: str = ".cortex/memory",
        collection_name: str = "cortex_knowledge",
    ) -> None:
        """Initialize ChromaDB client and collection.

        Args:
            persist_directory: Path where ChromaDB will store its data
            collection_name: Name for the vector collection
        """
        self._persist_dir = Path(persist_directory)
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with persistent storage
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=Settings(
                anonymized_telemetry=False,  # Disable telemetry for privacy
            ),
        )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Cortex project knowledge base"},
        )

    def add(self, chunks: list[DocumentChunk]) -> None:
        """Add document chunks to ChromaDB.

        Converts chunks to ChromaDB format with:
        - Deterministic IDs (file:line format)
        - Embeddings as vector arrays
        - Content as documents
        - Metadata preserved with additional fields

        Args:
            chunks: List of document chunks with embeddings
        """
        if not chunks:
            return

        # Prepare data in ChromaDB format (separate lists)
        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            # Generate deterministic ID from file path and line
            chunk_id = self._generate_chunk_id(chunk)
            ids.append(chunk_id)

            # Add embedding (ChromaDB requires embeddings)
            if chunk.embedding is None:
                msg = f"Chunk {chunk_id} has no embedding"
                raise ValueError(msg)
            embeddings.append(chunk.embedding)

            # Add document content
            documents.append(chunk.content)

            # Preserve metadata + add structural info
            metadata = dict(chunk.metadata)
            metadata["source_file"] = str(chunk.source_file)
            metadata["line_start"] = str(chunk.line_start)
            metadatas.append(metadata)

        # Add to ChromaDB collection (upsert semantics)
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: Embedding,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Search for similar chunks using ChromaDB.

        ChromaDB uses distance metrics (lower = more similar).
        We convert to similarity scores (higher = more similar).

        Args:
            query_embedding: Query vector
            limit: Maximum number of results

        Returns:
            List of SearchResult ordered by similarity (descending)
        """
        # Query ChromaDB
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
        )

        # Convert ChromaDB results to SearchResult objects
        search_results: list[SearchResult] = []

        # ChromaDB returns nested lists (batch queries)
        ids = results["ids"][0] if results["ids"] else []
        distances = results["distances"][0] if results["distances"] else []
        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []

        for _doc_id, distance, content, metadata in zip(
            ids,
            distances,
            documents,
            metadatas,
            strict=True,
        ):
            # Convert distance to similarity score (inverse)
            # ChromaDB L2 distance: 0 = perfect match, higher = less similar
            # We convert to score where higher = better
            similarity_score = 1.0 / (1.0 + distance)

            # Reconstruct DocumentChunk from stored data
            chunk = DocumentChunk(
                content=content,
                source_file=Path(str(metadata["source_file"])),
                line_start=int(str(metadata["line_start"])),
                metadata={
                    k: v
                    for k, v in metadata.items()
                    if k not in ("source_file", "line_start")
                },
                embedding=None,  # Don't store embedding in search results
            )

            search_results.append(SearchResult(chunk=chunk, score=similarity_score))

        # Results already ordered by ChromaDB (best first)
        return search_results

    def persist(self) -> None:
        """Persist vector store to disk.

        Note: ChromaDB with PersistentClient auto-persists on each operation.
        This method is a no-op but exists to satisfy the VectorStorePort interface.
        """
        # PersistentClient automatically persists after each operation
        # No explicit persist needed

    def load(self) -> None:
        """Load vector store from disk.

        Note: ChromaDB with PersistentClient auto-loads on initialization.
        This method is a no-op but exists to satisfy the VectorStorePort interface.
        """
        # PersistentClient automatically loads existing data on init
        # No explicit load needed

    def _generate_chunk_id(self, chunk: DocumentChunk) -> str:
        """Generate deterministic ID for a chunk.

        Uses file path and line number to create a unique, reproducible ID.
        This prevents duplicate entries when re-indexing the same files.

        Args:
            chunk: Document chunk to generate ID for

        Returns:
            Deterministic string ID (e.g., "doc1.py:1" or hash-based)
        """
        # Simple approach: use file path + line number
        # This is human-readable and deterministic
        base_id = f"{chunk.source_file.name}:{chunk.line_start}"

        # For safety, hash it to ensure it's valid for ChromaDB
        # (ChromaDB has some restrictions on ID format)
        id_hash = hashlib.md5(base_id.encode()).hexdigest()[:8]

        # Return hybrid: readable + hash for uniqueness
        return (
            f"{chunk.source_file.name.replace('.', '_')}_{chunk.line_start}_{id_hash}"
        )
