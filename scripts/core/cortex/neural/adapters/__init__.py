"""Adapters for neural subsystem.

This package contains concrete implementations of the ports defined
in scripts.core.cortex.neural.ports.

Available adapters:
- InMemoryVectorStore: Simple in-memory vector storage with JSON persistence
- SentenceTransformerAdapter: Real AI embedding using sentence-transformers
"""

from scripts.core.cortex.neural.adapters.memory import InMemoryVectorStore

__all__ = [
    "InMemoryVectorStore",
]

# Lazy import for SentenceTransformerAdapter (optional dependency)
try:
    from scripts.core.cortex.neural.adapters.sentence_transformer import (
        SentenceTransformerAdapter,
    )

    __all__.append("SentenceTransformerAdapter")
except ImportError:
    # sentence-transformers not installed - this is OK
    SentenceTransformerAdapter = None  # type: ignore[assignment,misc]
