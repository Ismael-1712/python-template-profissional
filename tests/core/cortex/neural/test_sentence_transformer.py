"""Unit tests for SentenceTransformerAdapter.

This module tests the real AI embedding adapter using mocks to avoid
loading the actual 500MB model during unit tests.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock heavy dependencies in sys.modules BEFORE any imports
# This prevents ModuleNotFoundError in CI where these libs may not be installed
if "sentence_transformers" not in sys.modules:
    sys.modules["sentence_transformers"] = MagicMock()

from scripts.core.cortex.neural.adapters.sentence_transformer import (
    SentenceTransformerAdapter,
)


class TestSentenceTransformerAdapter:
    """Test suite for SentenceTransformerAdapter."""

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_single_text(
        self,
        mock_sentence_transformer_class: MagicMock,
    ) -> None:
        """Test embedding generation for a single text."""
        # Arrange: Mock the model to return a fake embedding
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3, 0.4]
        mock_sentence_transformer_class.return_value = mock_model

        adapter = SentenceTransformerAdapter()

        # Act: Generate embedding
        result = adapter.embed("Hello world")

        # Assert: Verify the model was called correctly
        mock_model.encode.assert_called_once_with("Hello world", convert_to_numpy=False)
        assert result == [0.1, 0.2, 0.3, 0.4]
        assert isinstance(result, list)
        assert all(isinstance(x, (int, float)) for x in result)

    @patch("sentence_transformers.SentenceTransformer")
    def test_batch_embed_multiple_texts(
        self,
        mock_sentence_transformer_class: MagicMock,
    ) -> None:
        """Test embedding generation for multiple texts."""
        # Arrange: Mock the model to return fake embeddings
        mock_model = MagicMock()
        mock_model.encode.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]
        mock_sentence_transformer_class.return_value = mock_model

        adapter = SentenceTransformerAdapter()

        # Act: Generate batch embeddings
        texts = ["First text", "Second text"]
        result = adapter.batch_embed(texts)

        # Assert: Verify batch processing
        mock_model.encode.assert_called_once_with(texts, convert_to_numpy=False)
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]

    @patch("sentence_transformers.SentenceTransformer")
    def test_adapter_uses_correct_model(
        self,
        mock_sentence_transformer_class: MagicMock,
    ) -> None:
        """Test that the adapter loads the correct model."""
        # Arrange & Act
        SentenceTransformerAdapter()

        # Assert: Verify the correct model is loaded
        mock_sentence_transformer_class.assert_called_once_with("all-MiniLM-L6-v2")

    @patch("sentence_transformers.SentenceTransformer")
    def test_adapter_handles_model_loading_error(
        self,
        mock_sentence_transformer_class: MagicMock,
    ) -> None:
        """Test graceful error handling when model fails to load."""
        # Arrange: Make the model loading fail
        mock_sentence_transformer_class.side_effect = RuntimeError("Model not found")

        # Act & Assert: Verify exception is raised with clear message
        with pytest.raises(
            RuntimeError,
            match="Failed to load SentenceTransformer model",
        ):
            SentenceTransformerAdapter()

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_empty_string(
        self,
        mock_sentence_transformer_class: MagicMock,
    ) -> None:
        """Test embedding generation for empty string."""
        # Arrange
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.0] * 384
        mock_sentence_transformer_class.return_value = mock_model

        adapter = SentenceTransformerAdapter()

        # Act
        result = adapter.embed("")

        # Assert: Should handle empty string gracefully
        mock_model.encode.assert_called_once_with("", convert_to_numpy=False)
        assert len(result) == 384

    @patch("sentence_transformers.SentenceTransformer")
    def test_batch_embed_empty_list(
        self,
        mock_sentence_transformer_class: MagicMock,
    ) -> None:
        """Test batch embedding with empty list."""
        # Arrange
        mock_model = MagicMock()
        mock_model.encode.return_value = []
        mock_sentence_transformer_class.return_value = mock_model

        adapter = SentenceTransformerAdapter()

        # Act
        result = adapter.batch_embed([])

        # Assert
        mock_model.encode.assert_called_once_with([], convert_to_numpy=False)
        assert result == []
