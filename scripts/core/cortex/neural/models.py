"""Data models for Neural Interface (Vector Store)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorChunk:
    """Representa um fragmento de conhecimento vetorizado.

    Attributes:
        chunk_id: Hash único do chunk (SHA256).
        source_id: Caminho do arquivo de origem.
        content: Conteúdo textual do chunk.
        vector: Embedding vetorial do conteúdo.
        metadata: Metadados contextuais (headers, seção, etc).
    """

    chunk_id: str
    source_id: str
    content: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
