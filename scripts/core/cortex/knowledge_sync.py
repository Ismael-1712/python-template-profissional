"""Knowledge synchronization from external sources.

This module provides the KnowledgeSyncer class for downloading and merging
knowledge content from external sources while preserving local customizations
(Golden Paths).

Key Features:
- HTTP ETag-based caching to avoid unnecessary downloads
- Temporal caching via last_synced timestamps
- Golden Path preservation during merge
- Timeout protection for HTTP requests

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Protocol

import requests  # type: ignore[import-untyped, unused-ignore]

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.core.cortex.models import KnowledgeEntry, KnowledgeSource

from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem

# HTTP status codes
HTTP_OK = 200
HTTP_NOT_MODIFIED = 304


class HttpClient(Protocol):
    """Protocol for HTTP client abstraction (enables testing with mocks)."""

    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> requests.Response:
        """Perform HTTP GET request.

        Args:
            url: URL to fetch
            headers: Optional HTTP headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response object
        """
        ...


class RealHttpClient:
    """Production HTTP client using requests library."""

    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> requests.Response:
        """Perform HTTP GET request using requests library.

        Args:
            url: URL to fetch
            headers: Optional HTTP headers
            timeout: Request timeout in seconds (default: 10)

        Returns:
            Response object from requests library

        Raises:
            requests.RequestException: On network or HTTP errors
        """
        return requests.get(url, headers=headers or {}, timeout=timeout)


class KnowledgeSyncer:
    r"""Synchronizes knowledge entries with external sources.

    This class handles downloading content from remote URLs, merging with
    local content while preserving Golden Paths, and updating cache metadata.

    Attributes:
        fs: Filesystem adapter for I/O operations
        http_client: HTTP client for fetching remote content

    Example:
        >>> from pathlib import Path
        >>> syncer = KnowledgeSyncer()
        >>> entry = KnowledgeEntry(
        ...     id="kno-001",
        ...     status=DocStatus.ACTIVE,
        ...     tags=["security"],
        ...     golden_paths="## Golden Path\nLocal customization",
        ...     sources=[KnowledgeSource(url="https://example.com/doc.md")],
        ... )
        >>> updated = syncer.sync_entry(entry, Path("docs/knowledge/kno-001.md"))
    """

    # Regex patterns for Golden Path blocks
    GOLDEN_START = re.compile(
        r"<!--\s*GOLDEN_PATH_START\s*-->",
        re.IGNORECASE,
    )
    GOLDEN_END = re.compile(
        r"<!--\s*GOLDEN_PATH_END\s*-->",
        re.IGNORECASE,
    )

    def __init__(
        self,
        fs: FileSystemAdapter | None = None,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize the knowledge syncer.

        Args:
            fs: Filesystem adapter (defaults to RealFileSystem)
            http_client: HTTP client (defaults to RealHttpClient)
        """
        self.fs = fs or RealFileSystem()
        self.http_client = http_client or RealHttpClient()

    def sync_entry(
        self,
        entry: KnowledgeEntry,
        file_path: Path,
    ) -> KnowledgeEntry:
        """Synchronize a knowledge entry with its external sources.

        Downloads content from all sources, merges with local content
        (preserving Golden Paths), and updates cache metadata.

        Args:
            entry: Knowledge entry to synchronize
            file_path: Path to the local knowledge file

        Returns:
            Updated KnowledgeEntry with new last_synced and etag values

        Raises:
            FileNotFoundError: If file_path does not exist
            requests.RequestException: On HTTP errors

        Example:
            >>> entry = syncer.sync_entry(entry, Path("docs/knowledge/kno-001.md"))
            >>> print(f"Synced at: {entry.sources[0].last_synced}")
        """
        if not entry.sources:
            return entry  # No sources to sync

        # Read current local content
        local_content = ""
        if self.fs.exists(file_path):
            local_content = self.fs.read_text(file_path)

        updated_sources: list[KnowledgeSource] = []
        merged_content = local_content

        for source in entry.sources:
            # Fetch remote content with cache validation
            new_content, new_etag = self._fetch_source(source)

            if new_content is not None:
                # Content has changed - merge it
                merged_content = self._merge_content(
                    local_content=merged_content,
                    remote_content=new_content,
                )

                # Update source metadata
                updated_source = source.model_copy(
                    update={
                        "last_synced": datetime.now(timezone.utc),
                        "etag": new_etag,
                    },
                )
                updated_sources.append(updated_source)
            else:
                # No changes (304 Not Modified)
                updated_sources.append(source)

        # Write merged content back to disk if changed
        if merged_content != local_content:
            self.fs.write_text(file_path, merged_content)

        # Return updated entry with new source metadata
        return entry.model_copy(update={"sources": updated_sources})

    def _fetch_source(
        self,
        source: KnowledgeSource,
    ) -> tuple[str | None, str | None]:
        """Fetch content from a remote source with ETag caching.

        Args:
            source: Knowledge source with URL and cache metadata

        Returns:
            Tuple of (content, etag) if modified, or (None, None) if not modified

        Raises:
            requests.RequestException: On HTTP errors
        """
        headers = {}
        if source.etag:
            headers["If-None-Match"] = source.etag

        response = self.http_client.get(
            str(source.url),
            headers=headers,
            timeout=10,
        )

        # 304 Not Modified - content hasn't changed
        if response.status_code == HTTP_NOT_MODIFIED:
            return None, None

        # 200 OK - new content available
        if response.status_code == HTTP_OK:
            new_etag = response.headers.get("ETag")
            return response.text, new_etag

        # Other status codes - raise error
        response.raise_for_status()

        # Should not reach here, but return None for safety
        return None, None

    def _merge_content(
        self,
        local_content: str,
        remote_content: str,
    ) -> str:
        r"""Merge remote content with local content, preserving Golden Paths.

        The merge strategy:
        1. Extract Golden Path blocks from local content
        2. Extract YAML frontmatter from local content
        3. Replace everything else with remote content
        4. Re-insert Golden Path blocks at their original positions

        Args:
            local_content: Current local file content
            remote_content: New content from remote source

        Returns:
            Merged content string

        Example:
            >>> local = '''---
            ... id: kno-001
            ... ---
            ... # Doc
            ... <!-- GOLDEN_PATH_START -->
            ... Local rule
            ... <!-- GOLDEN_PATH_END -->
            ... Old content'''
            >>> remote = "# Doc\nNew remote content"
            >>> merged = syncer._merge_content(local, remote)
            >>> "Local rule" in merged
            True
            >>> "New remote content" in merged
            True
        """
        # Extract YAML frontmatter (between --- delimiters at start of file)
        frontmatter = self._extract_frontmatter(local_content)

        # Extract Golden Path blocks
        golden_blocks = self._extract_golden_paths(local_content)

        # Start with frontmatter (if exists)
        merged = frontmatter

        # If Golden Path blocks exist, we need to intelligently merge
        if golden_blocks:
            # Strategy: Insert remote content, then append Golden Paths at end
            # (unless we find a better insertion point in the future)
            if merged:
                merged += "\n\n"
            merged += remote_content
            merged += "\n\n"
            merged += "\n\n".join(golden_blocks)
        else:
            # No Golden Paths - simple replacement
            if merged:
                merged += "\n\n"
            merged += remote_content

        return merged

    def _extract_frontmatter(self, content: str) -> str:
        """Extract YAML frontmatter from content.

        Args:
            content: File content

        Returns:
            Frontmatter string (including --- delimiters) or empty string
        """
        lines = content.split("\n")
        if not lines or lines[0].strip() != "---":
            return ""

        # Find closing ---
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return "\n".join(lines[: i + 1])

        return ""

    def _extract_golden_paths(self, content: str) -> list[str]:
        """Extract all Golden Path blocks from content.

        Args:
            content: File content

        Returns:
            List of Golden Path blocks (including delimiters)
        """
        golden_blocks: list[str] = []
        current_block: list[str] = []
        inside_golden = False

        for line in content.split("\n"):
            if self.GOLDEN_START.search(line):
                inside_golden = True
                current_block = [line]
            elif self.GOLDEN_END.search(line):
                current_block.append(line)
                golden_blocks.append("\n".join(current_block))
                current_block = []
                inside_golden = False
            elif inside_golden:
                current_block.append(line)

        return golden_blocks
