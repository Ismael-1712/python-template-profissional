"""TDD tests for VectorBridge hexagonal refactoring.

This test suite ensures VectorBridge acts as a use case orchestrator,
delegating to EmbeddingPort and VectorStorePort interfaces.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.core.cortex.neural.domain import DocumentChunk, SearchResult
from scripts.core.cortex.neural.ports import EmbeddingPort, VectorStorePort
from scripts.core.cortex.neural.vector_bridge import VectorBridge


@pytest.fixture
def mock_embedding_service() -> Mock:
    """Create a mock EmbeddingPort."""
    mock = Mock(spec=EmbeddingPort)
    # Default behavior: return a simple embedding
    mock.embed.return_value = [0.1, 0.2, 0.3, 0.4]

    # batch_embed should match the number of inputs
    def batch_embed_side_effect(texts: list[str]) -> list[list[float]]:
        return [[0.1 + i * 0.1, 0.2, 0.3, 0.4] for i in range(len(texts))]

    mock.batch_embed.side_effect = batch_embed_side_effect
    return mock


@pytest.fixture
def mock_vector_store() -> Mock:
    """Create a mock VectorStorePort."""
    mock = Mock(spec=VectorStorePort)
    # Default behavior for search: return empty results
    mock.search.return_value = []
    return mock


@pytest.fixture
def vector_bridge(
    mock_embedding_service: Mock,
    mock_vector_store: Mock,
) -> VectorBridge:
    """Create a VectorBridge with mocked dependencies."""
    return VectorBridge(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
    )


class TestVectorBridgeIndexing:
    """Test suite for document indexing operations."""

    def test_index_document_calls_embedding_service(
        self,
        vector_bridge: VectorBridge,
        mock_embedding_service: Mock,
    ) -> None:
        """Should call embedding service to generate embeddings."""
        content = "Python is a programming language"
        source_file = Path("test.md")

        vector_bridge.index_document(content, source_file)

        # Verify embedding service was called
        assert (
            mock_embedding_service.embed.called
            or mock_embedding_service.batch_embed.called
        )

    def test_index_document_calls_vector_store_add(
        self,
        vector_bridge: VectorBridge,
        mock_vector_store: Mock,
    ) -> None:
        """Should call vector store to persist chunks."""
        content = "Python is a programming language"
        source_file = Path("test.md")

        vector_bridge.index_document(content, source_file)

        # Verify vector store add was called
        mock_vector_store.add.assert_called_once()
        # Verify it was called with a list of DocumentChunk
        call_args = mock_vector_store.add.call_args[0][0]
        assert isinstance(call_args, list)
        if call_args:
            assert isinstance(call_args[0], DocumentChunk)

    def test_index_document_chunks_are_enriched_with_embeddings(
        self,
        vector_bridge: VectorBridge,
        mock_embedding_service: Mock,
        mock_vector_store: Mock,
    ) -> None:
        """Should enrich chunks with embeddings before storing."""
        content = "Python is great"
        source_file = Path("test.md")

        vector_bridge.index_document(content, source_file)

        # Get the chunks that were passed to add()
        call_args = mock_vector_store.add.call_args[0][0]
        assert len(call_args) > 0

        # Verify chunks have embeddings
        for chunk in call_args:
            assert chunk.embedding is not None
            assert isinstance(chunk.embedding, list)

    def test_index_document_preserves_source_metadata(
        self,
        vector_bridge: VectorBridge,
        mock_vector_store: Mock,
    ) -> None:
        """Should preserve source file and line information."""
        content = "Test content"
        source_file = Path("docs/test.md")

        vector_bridge.index_document(content, source_file)

        # Get stored chunks
        call_args = mock_vector_store.add.call_args[0][0]
        assert len(call_args) > 0

        # Verify source metadata
        for chunk in call_args:
            assert chunk.source_file == source_file
            assert isinstance(chunk.line_start, int)
            assert chunk.line_start >= 0


class TestVectorBridgeQuerying:
    """Test suite for semantic search operations."""

    def test_query_similar_calls_embedding_service(
        self,
        vector_bridge: VectorBridge,
        mock_embedding_service: Mock,
    ) -> None:
        """Should embed the query text."""
        query = "How to use Python?"

        vector_bridge.query_similar(query, limit=5)

        # Verify query was embedded
        mock_embedding_service.embed.assert_called_once_with(query)

    def test_query_similar_calls_vector_store_search(
        self,
        vector_bridge: VectorBridge,
        mock_embedding_service: Mock,
        mock_vector_store: Mock,
    ) -> None:
        """Should search vector store with query embedding."""
        query = "How to use Python?"
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_service.embed.return_value = query_embedding

        vector_bridge.query_similar(query, limit=5)

        # Verify search was called with correct embedding and limit
        mock_vector_store.search.assert_called_once_with(query_embedding, limit=5)

    def test_query_similar_returns_search_results(
        self,
        vector_bridge: VectorBridge,
        mock_embedding_service: Mock,
        mock_vector_store: Mock,
    ) -> None:
        """Should return SearchResult objects from vector store."""
        query = "Python"
        expected_chunk = DocumentChunk(
            content="Python is great",
            source_file=Path("test.md"),
            line_start=1,
            metadata={},
            embedding=[0.1, 0.2, 0.3, 0.4],
        )
        expected_result = SearchResult(chunk=expected_chunk, score=0.95)
        mock_vector_store.search.return_value = [expected_result]

        results = vector_bridge.query_similar(query, limit=1)

        assert len(results) == 1
        assert results[0] == expected_result
        assert results[0].score == 0.95

    def test_query_similar_respects_limit_parameter(
        self,
        vector_bridge: VectorBridge,
        mock_vector_store: Mock,
    ) -> None:
        """Should pass limit parameter to vector store."""
        query = "Test query"

        vector_bridge.query_similar(query, limit=10)

        # Verify limit was passed correctly
        call_args = mock_vector_store.search.call_args
        assert call_args[1]["limit"] == 10


class TestVectorBridgeChunking:
    """Test suite for document chunking logic."""

    def test_index_document_creates_chunks(
        self,
        vector_bridge: VectorBridge,
        mock_vector_store: Mock,
    ) -> None:
        """Should split document into chunks."""
        # Use a longer content to ensure chunking happens
        content = "# Header 1\n\nSome content here.\n\n# Header 2\n\nMore content."
        source_file = Path("test.md")

        vector_bridge.index_document(content, source_file)

        # Verify chunks were created
        call_args = mock_vector_store.add.call_args[0][0]
        assert len(call_args) >= 1  # At least one chunk should be created

    def test_chunks_contain_content_and_metadata(
        self,
        vector_bridge: VectorBridge,
        mock_vector_store: Mock,
    ) -> None:
        """Should populate chunk fields correctly."""
        content = "Test content for chunking"
        source_file = Path("docs/example.md")

        vector_bridge.index_document(content, source_file)

        call_args = mock_vector_store.add.call_args[0][0]
        chunk = call_args[0]

        # Verify chunk structure
        assert isinstance(chunk.content, str)
        assert len(chunk.content) > 0
        assert chunk.source_file == source_file
        assert isinstance(chunk.metadata, dict)


class TestVectorBridgeEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_index_empty_document(
        self,
        vector_bridge: VectorBridge,
        mock_vector_store: Mock,
    ) -> None:
        """Should handle empty documents gracefully."""
        content = ""
        source_file = Path("empty.md")

        vector_bridge.index_document(content, source_file)

        # Should either not call add, or call with empty list
        if mock_vector_store.add.called:
            call_args = mock_vector_store.add.call_args[0][0]
            assert len(call_args) == 0

    def test_query_similar_with_empty_results(
        self,
        vector_bridge: VectorBridge,
        mock_vector_store: Mock,
    ) -> None:
        """Should handle no matches gracefully."""
        query = "Nonexistent topic"
        mock_vector_store.search.return_value = []

        results = vector_bridge.query_similar(query, limit=5)

        assert results == []
        assert isinstance(results, list)
