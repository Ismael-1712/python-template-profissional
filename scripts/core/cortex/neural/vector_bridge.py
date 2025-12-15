"""Vector Bridge module for CORTEX (Neural Interface)."""

import hashlib
import logging
import re
from pathlib import Path
from typing import Any

from scripts.core.cortex.neural.models import VectorChunk

logger = logging.getLogger(__name__)


class VectorBridge:
    """Bridge between CORTEX knowledge and Vector Database.

    Uses Lazy Loading to avoid importing heavy ML libraries at module level.
    """

    def __init__(self, persistence_path: Path) -> None:
        """Initialize the Vector Bridge.

        Args:
            persistence_path: Directory to store the ChromaDB database.
        """
        self.persistence_path = persistence_path
        # Use Any to satisfy MyPy with Lazy Loading
        self.client: Any = None
        self.collection: Any = None
        self.model: Any = None

    def _initialize_resources(self) -> None:
        """Lazy load ChromaDB and SentenceTransformer."""
        if self.client is not None:
            return

        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            logger.error(
                "Neural dependencies not found. "
                "Run 'pip install chromadb sentence-transformers'",
            )
            msg = "Missing neural dependencies"
            raise ImportError(msg) from e

        logger.info("Initializing Vector Store at %s", self.persistence_path)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.persistence_path))

        # Initialize Collection
        self.collection = self.client.get_or_create_collection(
            name="cortex_knowledge",
        )

        # Initialize Model (downloading if necessary)
        # cache_folder ensures we don't redownload models constantly
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _chunk_content(self, text: str, source_id: str) -> list[VectorChunk]:
        """Divide texto Markdown em chunks baseados em headers.

        Args:
            text: Conteúdo Markdown completo.
            source_id: Identificador do documento fonte.

        Returns:
            Lista de VectorChunk objects.
        """
        chunks: list[VectorChunk] = []
        max_chunk_size = 1000

        # Split by markdown headers
        sections = re.split(r"(^#{1,6}\s+.*$)", text, flags=re.MULTILINE)

        current_section = ""
        current_header = ""

        for section in sections:
            # Check if it's a header
            if re.match(r"^#{1,6}\s+", section):
                # Save previous section if exists
                if current_section.strip():
                    chunks.extend(
                        self._create_chunks_from_section(
                            current_section,
                            source_id,
                            current_header,
                            max_chunk_size,
                        ),
                    )
                current_header = section.strip()
                current_section = section + "\n"
            else:
                current_section += section

        # Add last section
        if current_section.strip():
            chunks.extend(
                self._create_chunks_from_section(
                    current_section,
                    source_id,
                    current_header,
                    max_chunk_size,
                ),
            )

        return chunks

    def _create_chunks_from_section(
        self,
        section: str,
        source_id: str,
        header: str,
        max_size: int,
    ) -> list[VectorChunk]:
        """Cria chunks de uma seção, subdividindo se necessário.

        Args:
            section: Texto da seção.
            source_id: ID do documento.
            header: Header da seção.
            max_size: Tamanho máximo do chunk.

        Returns:
            Lista de VectorChunk.
        """
        chunks: list[VectorChunk] = []

        if len(section) <= max_size:
            # Section is small enough, create single chunk
            chunk_id = hashlib.sha256(section.encode()).hexdigest()[:16]
            chunks.append(
                VectorChunk(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    content=section.strip(),
                    vector=[],  # Will be populated during indexing
                    metadata={"header": header, "chunk_index": 0},
                ),
            )
        else:
            # Section is too large, split by paragraphs
            paragraphs = section.split("\n\n")
            current_chunk = ""
            chunk_index = 0

            for para in paragraphs:
                if len(current_chunk) + len(para) > max_size and current_chunk:
                    # Save current chunk
                    chunk_id = hashlib.sha256(current_chunk.encode()).hexdigest()[:16]
                    chunks.append(
                        VectorChunk(
                            chunk_id=chunk_id,
                            source_id=source_id,
                            content=current_chunk.strip(),
                            vector=[],
                            metadata={"header": header, "chunk_index": chunk_index},
                        ),
                    )
                    current_chunk = para + "\n\n"
                    chunk_index += 1
                else:
                    current_chunk += para + "\n\n"

            # Add remaining chunk
            if current_chunk.strip():
                chunk_id = hashlib.sha256(current_chunk.encode()).hexdigest()[:16]
                chunks.append(
                    VectorChunk(
                        chunk_id=chunk_id,
                        source_id=source_id,
                        content=current_chunk.strip(),
                        vector=[],
                        metadata={"header": header, "chunk_index": chunk_index},
                    ),
                )

        return chunks

    def index_document(self, entry: Any) -> bool:
        """Index a document into the vector store.

        Args:
            entry: KnowledgeEntry object (typed as Any to avoid circular imports)

        Returns:
            True if indexed, False if skipped.
        """
        self._initialize_resources()

        # Extract content from entry
        if not hasattr(entry, "content") or not entry.content:
            logger.warning("Entry has no content, skipping indexing")
            return False

        source_id = str(entry.file_path) if hasattr(entry, "file_path") else "unknown"

        # Chunk the content
        chunks = self._chunk_content(entry.content, source_id)

        if not chunks:
            logger.warning("No chunks created for %s", source_id)
            return False

        # Generate embeddings for all chunks
        contents = [chunk.content for chunk in chunks]
        embeddings = self.model.encode(contents, show_progress_bar=False)

        # Prepare data for ChromaDB
        ids = [chunk.chunk_id for chunk in chunks]
        documents = contents
        metadatas = [chunk.metadata for chunk in chunks]

        # Upsert into ChromaDB
        try:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
            )
            logger.info("Indexed %d chunks from %s", len(chunks), source_id)
            return True
        except Exception as e:
            logger.error("Failed to index %s: %s", source_id, e)
            return False

    def query_similar(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search for similar content in the vector store.

        Args:
            query: The search text.
            n_results: Number of results to return.

        Returns:
            List of matches with content and metadata.
        """
        self._initialize_resources()

        # Generate embedding for query
        query_embedding = self.model.encode([query], show_progress_bar=False)[0]

        # Query ChromaDB
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
            )

            # Format results
            matches: list[dict[str, Any]] = []

            if results and "documents" in results:
                documents = results["documents"][0] if results["documents"] else []
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []

                for i, doc in enumerate(documents):
                    match = {
                        "content": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "distance": distances[i] if i < len(distances) else 0.0,
                    }
                    matches.append(match)

            logger.info("Found %d similar documents for query", len(matches))
            return matches

        except Exception as e:
            logger.error("Query failed: %s", e)
            return []
