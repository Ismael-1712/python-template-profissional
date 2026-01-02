"""TDD tests for InMemoryVectorStore adapter.

This test suite follows the Red-Green-Refactor cycle:
1. RED: Tests written first (will fail)
2. GREEN: Implementation makes tests pass
3. REFACTOR: Code quality improvements
"""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.core.cortex.neural.adapters.memory import InMemoryVectorStore
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
def vector_store() -> InMemoryVectorStore:
    """Create a fresh InMemoryVectorStore instance."""
    return InMemoryVectorStore()


class TestInMemoryVectorStoreAdd:
    """Test suite for the add method."""

    def test_add_single_chunk(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should store a single chunk without errors."""
        vector_store.add([sample_chunks[0]])
        # Internal state check (assuming we can access _chunks)
        assert len(vector_store._chunks) == 1

    def test_add_multiple_chunks(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should store multiple chunks."""
        vector_store.add(sample_chunks)
        assert len(vector_store._chunks) == 3

    def test_add_empty_list(self, vector_store: InMemoryVectorStore) -> None:
        """Should handle empty list gracefully."""
        vector_store.add([])
        assert len(vector_store._chunks) == 0

    def test_add_chunks_without_embeddings(
        self, vector_store: InMemoryVectorStore
    ) -> None:
        """Should raise ValueError when chunk has no embedding."""
        chunk_no_embedding = DocumentChunk(
            content="No embedding",
            source_file=Path("test.py"),
            line_start=1,
            metadata={},
            embedding=None,
        )
        with pytest.raises(ValueError, match="must have an embedding"):
            vector_store.add([chunk_no_embedding])


class TestInMemoryVectorStoreSearch:
    """Test suite for the search method."""

    def test_search_returns_results(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should return search results sorted by similarity."""
        vector_store.add(sample_chunks)
        # Query similar to first chunk
        query = [0.1, 0.2, 0.3, 0.4]
        results = vector_store.search(query, limit=2)

        assert len(results) == 2
        assert results[0].chunk.content == "Python is a programming language"
        assert results[0].score > results[1].score  # Sorted descending

    def test_search_respects_limit(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should respect the limit parameter."""
        vector_store.add(sample_chunks)
        query = [0.5, 0.5, 0.5, 0.5]
        results = vector_store.search(query, limit=1)

        assert len(results) == 1

    def test_search_empty_store(self, vector_store: InMemoryVectorStore) -> None:
        """Should return empty list when store is empty."""
        query = [0.1, 0.2, 0.3, 0.4]
        results = vector_store.search(query, limit=5)

        assert len(results) == 0

    def test_search_similarity_calculation(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should calculate cosine similarity correctly."""
        vector_store.add(sample_chunks)
        # Exact match with first chunk
        query = [0.1, 0.2, 0.3, 0.4]
        results = vector_store.search(query, limit=1)

        # Cosine similarity with itself should be 1.0 (or very close)
        assert results[0].score == pytest.approx(1.0, abs=0.01)


class TestInMemoryVectorStorePersistence:
    """Test suite for persist and load methods."""

    def test_persist_creates_file(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should create a JSON file when persisting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "vector_store.json"
            vector_store_with_path = InMemoryVectorStore(store_path=store_path)
            vector_store_with_path.add(sample_chunks)
            vector_store_with_path.persist()

            assert store_path.exists()
            assert store_path.is_file()

    def test_persist_saves_correct_data(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should save chunks in correct JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "vector_store.json"
            vector_store_with_path = InMemoryVectorStore(store_path=store_path)
            vector_store_with_path.add(sample_chunks)
            vector_store_with_path.persist()

            with store_path.open("r") as f:
                data = json.load(f)

            assert "chunks" in data
            assert len(data["chunks"]) == 3
            assert data["chunks"][0]["content"] == "Python is a programming language"

    def test_load_restores_data(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should restore chunks from persisted file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "vector_store.json"

            # Persist data
            store1 = InMemoryVectorStore(store_path=store_path)
            store1.add(sample_chunks)
            store1.persist()

            # Load in new instance
            store2 = InMemoryVectorStore(store_path=store_path)
            store2.load()

            assert len(store2._chunks) == 3
            assert store2._chunks[0].content == "Python is a programming language"

    def test_load_nonexistent_file_raises_error(
        self, vector_store: InMemoryVectorStore
    ) -> None:
        """Should raise FileNotFoundError when loading from non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "nonexistent.json"
            vector_store_with_path = InMemoryVectorStore(store_path=store_path)

            with pytest.raises(FileNotFoundError):
                vector_store_with_path.load()

    def test_persist_without_path_raises_error(
        self, vector_store: InMemoryVectorStore
    ) -> None:
        """Should raise ValueError when persisting without store_path."""
        with pytest.raises(ValueError, match="store_path"):
            vector_store.persist()

    def test_load_without_path_raises_error(
        self, vector_store: InMemoryVectorStore
    ) -> None:
        """Should raise ValueError when loading without store_path."""
        with pytest.raises(ValueError, match="store_path"):
            vector_store.load()


class TestInMemoryVectorStoreEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_search_with_different_embedding_dimensions(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should handle query with different embedding dimensions."""
        vector_store.add(sample_chunks)
        # Query with wrong dimension
        query = [0.1, 0.2]  # 2D instead of 4D

        # Implementation should either handle gracefully or raise clear error
        with pytest.raises(ValueError, match="dimension"):
            vector_store.search(query, limit=1)

    def test_concurrent_adds(
        self,
        vector_store: InMemoryVectorStore,
        sample_chunks: list[DocumentChunk],
    ) -> None:
        """Should handle sequential adds correctly."""
        vector_store.add([sample_chunks[0]])
        vector_store.add([sample_chunks[1]])
        vector_store.add([sample_chunks[2]])

        assert len(vector_store._chunks) == 3
