"""SentenceTransformer Adapter - Real AI Embedding Service.

This adapter implements the EmbeddingPort using the Sentence Transformers library,
providing production-ready text-to-vector conversion using state-of-the-art models.

Model: all-MiniLM-L6-v2
- Size: ~90MB (lightweight)
- Dimension: 384
- Speed: Fast (~3000 sentences/sec on CPU)
- Quality: Good for semantic search tasks
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.core.cortex.neural.domain import Embedding

from scripts.core.cortex.neural.ports import EmbeddingPort

logger = logging.getLogger(__name__)


class SentenceTransformerAdapter(EmbeddingPort):
    """Real AI embedding adapter using Sentence Transformers.

    This adapter loads the all-MiniLM-L6-v2 model and provides embedding
    generation for semantic search capabilities in Cortex.

    Attributes:
        model: The loaded SentenceTransformer model instance
        model_name: Name of the model being used

    Raises:
        RuntimeError: If the model fails to load
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize the SentenceTransformer adapter.

        Args:
            model_name: Name of the Sentence Transformers model to load.
                       Default is all-MiniLM-L6-v2 (lightweight and efficient).

        Raises:
            RuntimeError: If model loading fails
        """
        self.model_name = model_name
        logger.info(f"Loading SentenceTransformer model: {model_name}")

        try:
            # Import here to avoid loading at module import time
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
            logger.info(f"✅ Model {model_name} loaded successfully")
        except Exception as e:
            error_msg = f"Failed to load SentenceTransformer model '{model_name}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def embed(self, text: str) -> Embedding:
        """Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Vector embedding as list of floats (384 dimensions for all-MiniLM-L6-v2)

        Example:
            >>> adapter = SentenceTransformerAdapter()
            >>> embedding = adapter.embed("Hello world")
            >>> len(embedding)
            384
        """
        logger.debug(f"Generating embedding for text of length {len(text)}")

        # convert_to_numpy=False returns a list directly
        raw_embedding = self.model.encode(text, convert_to_numpy=False)

        # Ensure it's a list of floats (sentence-transformers may return numpy array)
        if hasattr(raw_embedding, "tolist"):
            embedding: Embedding = raw_embedding.tolist()  # type: ignore[assignment]
        else:
            embedding = raw_embedding  # type: ignore[assignment]

        return embedding

    def batch_embed(self, texts: list[str]) -> list[Embedding]:
        """Generate embeddings for multiple texts efficiently.

        This method processes texts in batch for better performance compared
        to calling embed() multiple times.

        Args:
            texts: List of input texts to embed

        Returns:
            List of vector embeddings

        Example:
            >>> adapter = SentenceTransformerAdapter()
            >>> embeddings = adapter.batch_embed(["First text", "Second text"])
            >>> len(embeddings)
            2
        """
        logger.debug(f"Generating batch embeddings for {len(texts)} texts")

        # Batch encoding is more efficient
        raw_embeddings = self.model.encode(texts, convert_to_numpy=False)

        # Ensure it's a list of lists (handle numpy arrays)
        if hasattr(raw_embeddings, "tolist"):
            embeddings: list[Embedding] = raw_embeddings.tolist()  # type: ignore[assignment]
        else:
            embeddings = raw_embeddings  # type: ignore[assignment]

        return embeddings
