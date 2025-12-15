"""Knowledge Scanner for CORTEX Knowledge Node System.

Module for scanning and parsing Markdown files with YAML frontmatter
to populate KnowledgeEntry objects. Provides resilient parsing with
graceful error handling for malformed documents.

Usage:
    scanner = KnowledgeScanner(workspace_root=Path('/project'))
    entries = scanner.scan()  # Scans docs/knowledge/ by default
    entries = scanner.scan(Path('/custom/knowledge'))  # Custom path

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import frontmatter
from pydantic import ValidationError

from scripts.core.cortex.link_analyzer import LinkAnalyzer
from scripts.core.cortex.models import DocStatus, KnowledgeEntry, KnowledgeSource
from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem

logger = logging.getLogger(__name__)


class KnowledgeScanner:
    """Scanner for parsing Knowledge Node files into KnowledgeEntry objects.

    Recursively scans a directory for Markdown files with YAML frontmatter,
    parses the metadata, and instantiates validated KnowledgeEntry objects.
    Implements graceful error handling - malformed files are logged but don't
    abort the entire scan operation.

    Attributes:
        workspace_root: Root directory of the workspace
        fs: FileSystemAdapter for I/O operations (supports dependency injection)

    Example:
        >>> scanner = KnowledgeScanner(workspace_root=Path('/project'))
        >>> entries = scanner.scan()
        >>> for entry in entries:
        ...     print(f"{entry.id}: {', '.join(entry.tags)}")
    """

    def __init__(
        self,
        workspace_root: Path,
        fs: FileSystemAdapter | None = None,
    ) -> None:
        """Initialize the Knowledge Scanner.

        Args:
            workspace_root: Root directory of the workspace
            fs: FileSystemAdapter implementation (defaults to RealFileSystem)
        """
        self.workspace_root = workspace_root
        self.fs = fs or RealFileSystem()
        self.link_analyzer = LinkAnalyzer()
        logger.debug(
            "KnowledgeScanner initialized for workspace: %s",
            workspace_root,
        )

    def scan(self, knowledge_dir: Path | None = None) -> list[KnowledgeEntry]:
        """Scan directory for Knowledge Node files and parse into entries.

        Recursively finds all .md files in the knowledge directory,
        parses their YAML frontmatter, and creates KnowledgeEntry objects.
        Malformed files are logged as warnings but don't stop the scan.

        Args:
            knowledge_dir: Directory to scan (defaults to workspace_root/docs/knowledge)

        Returns:
            List of validated KnowledgeEntry objects. Empty list if directory
            doesn't exist or contains no valid files.

        Example:
            >>> scanner = KnowledgeScanner(Path('/project'))
            >>> entries = scanner.scan()
            >>> len(entries)
            5
            >>> entries[0].id
            'kno-001'
        """
        # Set default knowledge directory
        if knowledge_dir is None:
            knowledge_dir = self.workspace_root / "docs" / "knowledge"

        # Check if directory exists
        if not self.fs.exists(knowledge_dir):
            logger.warning(
                "Knowledge directory does not exist: %s. Returning empty list.",
                knowledge_dir,
            )
            return []

        if not self.fs.is_dir(knowledge_dir):
            logger.error(
                "Knowledge path exists but is not a directory: %s",
                knowledge_dir,
            )
            return []

        # Scan for Markdown files
        logger.info("Scanning knowledge directory: %s", knowledge_dir)
        markdown_files = self.fs.rglob(knowledge_dir, "*.md")
        logger.debug("Found %d Markdown files to process", len(markdown_files))

        entries: list[KnowledgeEntry] = []

        for file_path in markdown_files:
            try:
                entry = self._parse_knowledge_file(file_path)
                entries.append(entry)
                logger.debug("Successfully parsed: %s -> %s", file_path, entry.id)
            except (KeyError, ValueError, ValidationError) as e:
                # Log error but continue processing other files (resilience)
                logger.warning(
                    "Failed to parse knowledge file %s: %s",
                    file_path,
                    str(e),
                    exc_info=True,
                )

        logger.info(
            "Knowledge scan complete: %d/%d files successfully parsed",
            len(entries),
            len(markdown_files),
        )
        return entries

    def _parse_knowledge_file(self, file_path: Path) -> KnowledgeEntry:
        """Parse a single Knowledge Node Markdown file.

        Reads the file, extracts YAML frontmatter, and creates a validated
        KnowledgeEntry object. Raises exceptions for malformed files.

        Args:
            file_path: Path to the Markdown file to parse

        Returns:
            Validated KnowledgeEntry object

        Raises:
            KeyError: If required frontmatter fields are missing
            ValidationError: If frontmatter data doesn't match KnowledgeEntry schema
            ValueError: If frontmatter parsing fails
        """
        # Read file content
        content = self.fs.read_text(file_path)

        # Parse frontmatter
        try:
            post = frontmatter.loads(content)
            metadata: dict[str, Any] = post.metadata
        except Exception as e:
            msg = f"Failed to parse frontmatter: {e}"
            raise ValueError(msg) from e

        # Extract required fields
        try:
            entry_id = metadata["id"]
            status_str = metadata["status"]
        except KeyError as e:
            msg = f"Missing required field in frontmatter: {e}"
            raise KeyError(msg) from e

        # Extract optional fields
        golden_paths = metadata.get("golden_paths", [])

        # Convert status string to enum
        try:
            status = DocStatus(status_str)
        except ValueError as e:
            valid_values = [s.value for s in DocStatus]
            msg = f"Invalid status value '{status_str}'. Must be one of: {valid_values}"
            raise ValueError(msg) from e

        # Extract optional fields
        tags = metadata.get("tags", [])
        sources_data = metadata.get("sources", [])

        # Parse sources (list of dicts -> list of KnowledgeSource)
        # Note: Individual source validation errors are logged but don't
        # fail the whole entry parsing
        sources: list[KnowledgeSource] = []
        for source_dict in sources_data:
            try:
                source = KnowledgeSource(**source_dict)
            except ValidationError as e:
                logger.warning(
                    "Invalid source in %s: %s. Skipping.",
                    file_path,
                    str(e),
                )
                continue
            sources.append(source)

        # Cache the content body (text after frontmatter)
        cached_content = post.content.strip() if post.content else None

        # Extract semantic links from cached content
        links = []
        if cached_content and entry_id:
            links = self.link_analyzer.extract_links(cached_content, entry_id)
            logger.debug(
                "Extracted %d links from %s",
                len(links),
                file_path,
            )

        # Construct and validate KnowledgeEntry
        return KnowledgeEntry(
            id=entry_id,
            status=status,
            tags=tags,
            golden_paths=golden_paths,
            sources=sources,
            cached_content=cached_content,
            links=links,
            file_path=file_path,
        )
