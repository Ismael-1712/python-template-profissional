"""VectorBridge - Use Case Orchestrator for Neural Subsystem.

This module implements the VectorBridge as a hexagonal use case orchestrator
that coordinates between EmbeddingPort and VectorStorePort to provide
document indexing and semantic search capabilities.
"""

import logging
import re
from pathlib import Path

from scripts.core.cortex.neural.domain import DocumentChunk, SearchResult
from scripts.core.cortex.neural.ports import EmbeddingPort, VectorStorePort

logger = logging.getLogger(__name__)


class VectorBridge:
    """Orchestrates document indexing and semantic search.

    This class acts as a use case in the hexagonal architecture,
    coordinating between embedding generation and vector storage
    without depending on specific implementations.

    Attributes:
        embedding_service: Port for generating text embeddings
        vector_store: Port for storing and searching document chunks
    """

    def __init__(
        self,
        embedding_service: EmbeddingPort,
        vector_store: VectorStorePort,
    ) -> None:
        """Initialize the VectorBridge with injected dependencies.

        Args:
            embedding_service: Service implementing EmbeddingPort
            vector_store: Service implementing VectorStorePort
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def index_document(self, content: str, source_file: Path) -> None:
        """Index a document by chunking, embedding, and storing.

        This orchestrates the complete indexing pipeline:
        1. Chunk the document content
        2. Generate embeddings for each chunk
        3. Store enriched chunks in vector store

        Args:
            content: The full text content of the document
            source_file: Path to the source document
        """
        # Step 1: Chunk the content
        chunks = self._chunk_content(content, source_file)

        if not chunks:
            logger.warning("No chunks created for %s", source_file)
            return

        # Step 2: Generate embeddings for all chunks
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.batch_embed(chunk_texts)

        # Step 3: Enrich chunks with embeddings
        enriched_chunks: list[DocumentChunk] = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            # Create new chunk with embedding (dataclass is frozen)
            enriched_chunk = DocumentChunk(
                content=chunk.content,
                source_file=chunk.source_file,
                line_start=chunk.line_start,
                metadata=chunk.metadata,
                embedding=embedding,
            )
            enriched_chunks.append(enriched_chunk)

        # Step 4: Store in vector store
        self.vector_store.add(enriched_chunks)

        logger.info(
            "Indexed %d chunks from %s",
            len(enriched_chunks),
            source_file,
        )

    def query_similar(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Search for similar content using semantic search.

        This orchestrates the search pipeline:
        1. Generate embedding for the query
        2. Search vector store for similar chunks
        3. Return ranked results

        Args:
            query: The search query text
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects ranked by similarity
        """
        # Step 1: Generate query embedding
        query_embedding = self.embedding_service.embed(query)

        # Step 2: Search vector store
        results = self.vector_store.search(query_embedding, limit=limit)

        logger.info("Found %d similar documents for query", len(results))

        return results

    def _chunk_content(
        self,
        text: str,
        source_file: Path,
    ) -> list[DocumentChunk]:
        """Divide text into chunks based on markdown headers.

        Args:
            text: Full markdown content
            source_file: Path to the source file

        Returns:
            List of DocumentChunk objects (without embeddings)
        """
        if not text.strip():
            return []

        chunks: list[DocumentChunk] = []
        max_chunk_size = 1000
        line_number = 1  # Track line numbers

        # Split by markdown headers
        sections = re.split(r"(^#{1,6}\s+.*$)", text, flags=re.MULTILINE)

        current_section = ""
        current_header = ""
        section_start_line = 1

        for section in sections:
            # Check if it's a header
            if re.match(r"^#{1,6}\s+", section):
                # Save previous section if exists
                if current_section.strip():
                    section_chunks = self._create_chunks_from_section(
                        current_section,
                        source_file,
                        current_header,
                        max_chunk_size,
                        section_start_line,
                    )
                    chunks.extend(section_chunks)

                current_header = section.strip()
                current_section = section + "\n"
                section_start_line = line_number
                line_number += section.count("\n") + 1
            else:
                current_section += section
                line_number += section.count("\n")

        # Add last section
        if current_section.strip():
            section_chunks = self._create_chunks_from_section(
                current_section,
                source_file,
                current_header,
                max_chunk_size,
                section_start_line,
            )
            chunks.extend(section_chunks)

        return chunks

    def _create_chunks_from_section(
        self,
        section: str,
        source_file: Path,
        header: str,
        max_size: int,
        start_line: int,
    ) -> list[DocumentChunk]:
        """Create chunks from a section, subdividing if necessary.

        Args:
            section: Section text
            source_file: Source file path
            header: Section header
            max_size: Maximum chunk size in characters
            start_line: Starting line number for this section

        Returns:
            List of DocumentChunk objects
        """
        chunks: list[DocumentChunk] = []
        current_line = start_line

        if len(section) <= max_size:
            # Section is small enough, create single chunk
            chunks.append(
                DocumentChunk(
                    content=section.strip(),
                    source_file=source_file,
                    line_start=current_line,
                    metadata={"header": header} if header else {},
                    embedding=None,  # Will be added during indexing
                ),
            )
        else:
            # Section is too large, split by paragraphs
            paragraphs = section.split("\n\n")
            current_chunk = ""
            chunk_start_line = current_line

            for para in paragraphs:
                if len(current_chunk) + len(para) > max_size and current_chunk:
                    # Save current chunk
                    chunks.append(
                        DocumentChunk(
                            content=current_chunk.strip(),
                            source_file=source_file,
                            line_start=chunk_start_line,
                            metadata={"header": header} if header else {},
                            embedding=None,
                        ),
                    )
                    current_chunk = para + "\n\n"
                    chunk_start_line = current_line
                else:
                    current_chunk += para + "\n\n"

                current_line += para.count("\n") + 2  # +2 for paragraph separator

            # Add remaining chunk
            if current_chunk.strip():
                chunks.append(
                    DocumentChunk(
                        content=current_chunk.strip(),
                        source_file=source_file,
                        line_start=chunk_start_line,
                        metadata={"header": header} if header else {},
                        embedding=None,
                    ),
                )

        return chunks
