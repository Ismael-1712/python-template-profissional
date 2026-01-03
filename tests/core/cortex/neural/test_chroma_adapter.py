"""TDD tests for ChromaDBVectorStore adapter.

This test suite follows the Red-Green-Refactor cycle:
1. RED: Tests written first (will fail)
2. GREEN: Implementation makes tests pass
3. REFACTOR: Code quality improvements

Uses unittest.mock to avoid creating real ChromaDB files during tests.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from scripts.core.cortex.neural.domain import DocumentChunk


@pytest.fixture
def sample_chunks() -> list[DocumentChunk]:
    """Create sample document chunks with embeddings for testing."""
    return [
        DocumentChunk(
            content="Python is a programming language",
            source_file=Path("doc1.py"),
            line_start=1,
            metadata={"topic": "programming"},
            embedding=[0.1, 0.2, 0.3, 0.4],
        ),
        DocumentChunk(
            content="Java is also a programming language",
            source_file=Path("doc2.py"),
            line_start=5,
            metadata={"topic": "programming"},
            embedding=[0.15, 0.25, 0.35, 0.45],
        ),
        DocumentChunk(
            content="Machine learning uses Python",
            source_file=Path("doc3.py"),
            line_start=10,
            metadata={"topic": "ml"},
            embedding=[0.8, 0.1, 0.2, 0.3],
        ),
    ]


@pytest.fixture
def mock_chroma_client() -> dict[str, Any]:  # type: ignore[misc]
    """Create a mocked ChromaDB client."""
    with patch("scripts.core.cortex.neural.adapters.chroma.chromadb") as mock_chromadb:
        mock_client = MagicMock()
        mock_collection = MagicMock()

        # Configure the mock client to return a mock collection
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        yield {
            "chromadb": mock_chromadb,
            "client": mock_client,
            "collection": mock_collection,
        }


class TestChromaDBVectorStoreInit:
    """Test suite for ChromaDBVectorStore initialization."""

    def test_init_with_default_directory(
        self, mock_chroma_client: dict[str, Any]
    ) -> None:
        """Should initialize with default persist directory."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        _ = ChromaDBVectorStore()

        # Verify PersistentClient was called with correct path
        mock_chroma_client["chromadb"].PersistentClient.assert_called_once()
        call_kwargs = mock_chroma_client["chromadb"].PersistentClient.call_args[1]
        assert ".cortex/memory" in str(call_kwargs["path"])

    def test_init_with_custom_directory(
        self, mock_chroma_client: dict[str, Any]
    ) -> None:
        """Should initialize with custom persist directory."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        custom_path = "/tmp/custom_chroma"
        _ = ChromaDBVectorStore(persist_directory=custom_path)

        # Verify PersistentClient was called with custom path
        call_kwargs = mock_chroma_client["chromadb"].PersistentClient.call_args[1]
        assert custom_path in str(call_kwargs["path"])

    def test_init_creates_collection(self, mock_chroma_client: dict[str, Any]) -> None:
        """Should create or get the 'cortex_knowledge' collection."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        _ = ChromaDBVectorStore()

        # Verify collection was created/retrieved
        mock_chroma_client["client"].get_or_create_collection.assert_called_once()
        call_args = mock_chroma_client["client"].get_or_create_collection.call_args[1]
        assert call_args["name"] == "cortex_knowledge"


class TestChromaDBVectorStoreAdd:
    """Test suite for the add method."""

    def test_add_single_chunk(
        self,
        mock_chroma_client: dict[str, Any],
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should add a single chunk to ChromaDB collection."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        store = ChromaDBVectorStore()
        store.add([sample_chunks[0]])

        # Verify collection.add was called
        mock_collection = mock_chroma_client["collection"]
        mock_collection.add.assert_called_once()

        # Verify the call structure
        call_kwargs = mock_collection.add.call_args[1]
        assert "ids" in call_kwargs
        assert "embeddings" in call_kwargs
        assert "documents" in call_kwargs
        assert "metadatas" in call_kwargs

        # Verify content
        assert len(call_kwargs["ids"]) == 1
        assert len(call_kwargs["embeddings"]) == 1
        assert call_kwargs["embeddings"][0] == [0.1, 0.2, 0.3, 0.4]

    def test_add_multiple_chunks(
        self,
        mock_chroma_client: dict[str, Any],
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should add multiple chunks to ChromaDB collection."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        store = ChromaDBVectorStore()
        store.add(sample_chunks)

        mock_collection = mock_chroma_client["collection"]
        call_kwargs = mock_collection.add.call_args[1]

        # Verify we have 3 chunks
        assert len(call_kwargs["ids"]) == 3
        assert len(call_kwargs["embeddings"]) == 3
        assert len(call_kwargs["documents"]) == 3
        assert len(call_kwargs["metadatas"]) == 3

    def test_add_generates_deterministic_ids(
        self,
        mock_chroma_client: dict[str, Any],
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should generate deterministic IDs based on content."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        store = ChromaDBVectorStore()
        store.add([sample_chunks[0]])

        mock_collection = mock_chroma_client["collection"]
        call_kwargs = mock_collection.add.call_args[1]

        # ID should be consistent and unique
        chunk_id = call_kwargs["ids"][0]
        assert isinstance(chunk_id, str)
        assert len(chunk_id) > 0
        # Should contain file path info
        assert "doc1.py" in chunk_id or "1" in chunk_id

    def test_add_preserves_metadata(
        self,
        mock_chroma_client: dict[str, Any],
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should preserve chunk metadata in ChromaDB."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        store = ChromaDBVectorStore()
        store.add([sample_chunks[0]])

        mock_collection = mock_chroma_client["collection"]
        call_kwargs = mock_collection.add.call_args[1]

        metadata = call_kwargs["metadatas"][0]
        assert "topic" in metadata
        assert metadata["topic"] == "programming"
        assert "source_file" in metadata
        assert "line_start" in metadata


class TestChromaDBVectorStoreSearch:
    """Test suite for the search method."""

    def test_search_returns_results(
        self,
        mock_chroma_client: dict[str, Any],
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should search and return SearchResult objects."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        # Configure mock collection to return search results
        mock_collection = mock_chroma_client["collection"]
        mock_collection.query.return_value = {
            "ids": [["doc1.py:1", "doc2.py:5"]],
            "distances": [[0.1, 0.3]],
            "documents": [
                [
                    "Python is a programming language",
                    "Java is also a programming language",
                ],
            ],
            "metadatas": [
                [
                    {
                        "topic": "programming",
                        "source_file": "doc1.py",
                        "line_start": "1",
                    },
                    {
                        "topic": "programming",
                        "source_file": "doc2.py",
                        "line_start": "5",
                    },
                ],
            ],
        }

        store = ChromaDBVectorStore()
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        results = store.search(query_embedding, limit=2)

        # Verify query was called
        mock_collection.query.assert_called_once()

        # Verify results structure
        assert len(results) == 2
        assert results[0].score > 0
        assert results[0].chunk.content == "Python is a programming language"

    def test_search_respects_limit(
        self,
        mock_chroma_client: dict[str, Any],
    ) -> None:
        """Should respect the limit parameter."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        mock_collection = mock_chroma_client["collection"]
        mock_collection.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "documents": [[]],
            "metadatas": [[]],
        }

        store = ChromaDBVectorStore()
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        store.search(query_embedding, limit=10)

        # Verify limit was passed to query
        call_kwargs = mock_collection.query.call_args[1]
        assert call_kwargs["n_results"] == 10

    def test_search_converts_distance_to_similarity_score(
        self,
        mock_chroma_client: dict[str, Any],
    ) -> None:
        """Should convert ChromaDB distance to similarity score."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        # ChromaDB returns distances (lower is better)
        # We should convert to similarity scores (higher is better)
        mock_collection = mock_chroma_client["collection"]
        mock_collection.query.return_value = {
            "ids": [["doc1.py:1"]],
            "distances": [[0.2]],  # Small distance = high similarity
            "documents": [["Python is a programming language"]],
            "metadatas": [
                [{"topic": "programming", "source_file": "doc1.py", "line_start": "1"}],
            ],
        }

        store = ChromaDBVectorStore()
        results = store.search([0.1, 0.2, 0.3, 0.4], limit=1)

        # Score should be inverse of distance (or similar conversion)
        assert results[0].score > 0


class TestChromaDBVectorStorePersist:
    """Test suite for the persist method."""

    def test_persist_is_automatic(self, mock_chroma_client: dict[str, Any]) -> None:
        """Should handle persist (ChromaDB auto-persists with PersistentClient)."""
        from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

        store = ChromaDBVectorStore()

        # persist() should not raise an error
        # With PersistentClient, persistence is automatic
        store.persist()
        # No exception means success
