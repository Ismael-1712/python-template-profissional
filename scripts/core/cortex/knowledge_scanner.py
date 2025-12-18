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
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from scripts.core.cortex.link_analyzer import LinkAnalyzer
from scripts.core.cortex.metadata import FrontmatterParser
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
        force_parallel: bool = False,
    ) -> None:
        """Initialize the Knowledge Scanner.

        Args:
            workspace_root: Root directory of the workspace
            fs: FileSystemAdapter implementation (defaults to RealFileSystem)
            force_parallel: Force parallel processing (experimental).
                           If True, uses parallel processing for 10+ files.
                           If False (default), uses sequential processing.
        """
        self.workspace_root = workspace_root
        self.fs = fs or RealFileSystem()
        self.force_parallel = force_parallel
        self.link_analyzer = LinkAnalyzer()
        self.frontmatter_parser = FrontmatterParser(fs=self.fs)
        logger.debug(
            "KnowledgeScanner initialized for workspace: %s (parallel=%s)",
            workspace_root,
            force_parallel,
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

        Performance Notes:
            This method automatically uses parallel processing (ThreadPoolExecutor)
            when scanning 10 or more files, using up to 4 worker threads.
            For smaller sets (<10 files), sequential processing is used to
            avoid thread overhead.

            Thread Safety: This method is thread-safe when using MemoryFileSystem
            (v1.1.0+) or RealFileSystem. Concurrent calls to scan() on the same
            scanner instance are safe, but may cause redundant work.

            See docs/architecture/PERFORMANCE_NOTES.md for detailed benchmarks
            and optimization strategies.

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

        # Parallelism disabled by default due to GIL overhead (PERFORMANCE_NOTES.md).
        # Benchmarks show 34% regression (0.66x) with ThreadPoolExecutor.
        # Sequential processing used unless explicitly enabled via force_parallel.
        # Users can opt-in via CLI flag --parallel for experimental parallel mode.
        if self.force_parallel:
            parallel_threshold = 10  # Original threshold: enable for 10+ files
        else:
            parallel_threshold = sys.maxsize  # Effectively disabled

        # Use parallel processing for large sets of files
        if len(markdown_files) >= parallel_threshold:
            # Determine optimal number of workers
            max_workers = min(4, os.cpu_count() or 1)
            logger.info(
                "🚀 Running in EXPERIMENTAL PARALLEL mode (%d workers)",
                max_workers,
            )
            logger.debug(
                "Processing %d files with %d workers (GIL may impact performance)",
                len(markdown_files),
                max_workers,
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all parsing tasks
                future_to_file = {
                    executor.submit(
                        self._parse_knowledge_file_safe,
                        file_path,
                    ): file_path
                    for file_path in markdown_files
                }

                # Collect results as they complete
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        entry = future.result()
                        if entry is not None:
                            entries.append(entry)
                            logger.debug(
                                "Successfully parsed: %s -> %s",
                                file_path,
                                entry.id,
                            )
                    except Exception as e:
                        # Errors are caught in _parse_knowledge_file_safe
                        logger.error(
                            "Unexpected error processing %s: %s",
                            file_path,
                            str(e),
                            exc_info=True,
                        )
        else:
            # Sequential processing for small sets (avoid thread overhead)
            if not self.force_parallel:
                logger.debug(
                    "Running in standard sequential mode (%d files) - "
                    "using sequential processing",
                    len(markdown_files),
                )
            else:
                logger.debug(
                    "Using sequential processing for %d files (below threshold)",
                    len(markdown_files),
                )
            for file_path in markdown_files:
                entry = self._parse_knowledge_file_safe(file_path)
                if entry is not None:
                    entries.append(entry)
                    logger.debug("Successfully parsed: %s -> %s", file_path, entry.id)

        logger.info(
            "Knowledge scan complete: %d/%d files successfully parsed",
            len(entries),
            len(markdown_files),
        )
        return entries

    def _parse_knowledge_file_safe(self, file_path: Path) -> KnowledgeEntry | None:
        """Thread-safe wrapper for parsing knowledge files with error handling.

        This method wraps _parse_knowledge_file to provide graceful error
        handling suitable for parallel execution. Individual file failures
        are logged but don't stop the overall scan process.

        Args:
            file_path: Path to the Markdown file to parse

        Returns:
            KnowledgeEntry object if parsing succeeds, None if it fails
        """
        try:
            return self._parse_knowledge_file(file_path)
        except (KeyError, ValueError, ValidationError) as e:
            # Log error but continue processing other files (resilience)
            logger.warning(
                "Failed to parse knowledge file %s: %s",
                file_path,
                str(e),
                exc_info=True,
            )
            return None

    def _parse_knowledge_file(self, file_path: Path) -> KnowledgeEntry:
        """Parse a single Knowledge Node Markdown file.

        Reads the file, extracts YAML frontmatter using the centralized parser,
        and creates a validated KnowledgeEntry object.

        Args:
            file_path: Path to the Markdown file to parse

        Returns:
            Validated KnowledgeEntry object

        Raises:
            KeyError: If required frontmatter fields are missing
            ValidationError: If frontmatter data doesn't match KnowledgeEntry schema
            ValueError: If frontmatter parsing fails
        """
        # Read file content for cached_content extraction
        import frontmatter

        content = self.fs.read_text(file_path)
        post = frontmatter.loads(content)
        metadata: dict[str, Any] = post.metadata

        # Extract required fields
        try:
            entry_id = metadata["id"]
            status_str = metadata["status"]
        except KeyError as e:
            msg = f"Missing required field in frontmatter: {e}"
            raise KeyError(msg) from e

        # Extract Knowledge-specific optional fields
        golden_paths = metadata.get("golden_paths", [])
        tags = metadata.get("tags", [])
        sources_data = metadata.get("sources", [])

        # Convert status string to enum
        try:
            status = DocStatus(status_str)
        except ValueError as e:
            valid_values = [s.value for s in DocStatus]
            msg = f"Invalid status value '{status_str}'. Must be one of: {valid_values}"
            raise ValueError(msg) from e

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
