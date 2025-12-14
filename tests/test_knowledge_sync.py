"""Unit tests for KnowledgeSyncer.

This test suite validates the synchronization logic for knowledge entries,
including ETag caching, content merging, and Golden Path preservation.

Test Coverage:
- Cache hit (304 Not Modified) scenarios
- New content (200 OK) scenarios
- Golden Path preservation during merge
- Resilience to network failures
- Error handling and logging

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from pydantic import HttpUrl

if TYPE_CHECKING:
    from requests import Response

from scripts.core.cortex.knowledge_sync import (
    HTTP_NOT_MODIFIED,
    HTTP_OK,
    KnowledgeSyncer,
)
from scripts.core.cortex.models import (
    DocStatus,
    KnowledgeEntry,
    KnowledgeSource,
)
from scripts.utils.filesystem import MemoryFileSystem


def _url(url_str: str) -> HttpUrl:
    """Helper to create HttpUrl from string in tests.

    Args:
        url_str: URL string

    Returns:
        HttpUrl instance
    """
    return HttpUrl(url_str)


class MockHttpClient:
    """Mock HTTP client for testing without network calls.

    Allows configuring the response (status, text, headers) before calling get.
    """

    def __init__(self) -> None:
        """Initialize mock HTTP client with default 200 OK response."""
        self.status_code: int = HTTP_OK
        self.response_text: str = ""
        self.response_headers: dict[str, str] = {}
        self.exception: Exception | None = None

    def configure(
        self,
        status_code: int = HTTP_OK,
        text: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        """Configure the mock response.

        Args:
            status_code: HTTP status code to return
            text: Response body text
            headers: Response headers (e.g., ETag)
        """
        self.status_code = status_code
        self.response_text = text
        self.response_headers = headers or {}
        self.exception = None

    def configure_exception(self, exception: Exception) -> None:
        """Configure the mock to raise an exception.

        Args:
            exception: Exception to raise when get() is called
        """
        self.exception = exception

    def get(
        self,
        url: str,  # noqa: ARG002
        headers: dict[str, str] | None = None,  # noqa: ARG002
        timeout: int = 10,  # noqa: ARG002
    ) -> Response:
        """Mock HTTP GET request.

        Args:
            url: URL to fetch (ignored in mock)
            headers: Request headers
            timeout: Request timeout (ignored in mock)

        Returns:
            Mock response object

        Raises:
            Exception: If configured via configure_exception()
        """
        if self.exception:
            raise self.exception

        # Create a mock Response object
        response = Mock()
        response.status_code = self.status_code
        response.text = self.response_text
        response.headers = self.response_headers

        # Mock raise_for_status behavior
        def raise_for_status() -> None:
            http_error_min = 400
            http_error_max = 600
            if http_error_min <= self.status_code < http_error_max:
                msg = f"HTTP {self.status_code} Error"
                raise ConnectionError(msg)

        response.raise_for_status = raise_for_status

        return response


@pytest.fixture
def memory_fs() -> MemoryFileSystem:
    """Provide a clean in-memory filesystem for each test."""
    return MemoryFileSystem()


@pytest.fixture
def mock_http() -> MockHttpClient:
    """Provide a mock HTTP client for each test."""
    return MockHttpClient()


@pytest.fixture
def syncer(memory_fs: MemoryFileSystem, mock_http: MockHttpClient) -> KnowledgeSyncer:
    """Provide a KnowledgeSyncer with mocked dependencies."""
    return KnowledgeSyncer(fs=memory_fs, http_client=mock_http)


class TestCacheHit:
    """Test scenarios where remote content has not changed (304 Not Modified)."""

    def test_cache_hit_preserves_local_file(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """When server returns 304, local file should not be modified."""
        # Arrange
        file_path = Path("docs/knowledge/kno-001.md")
        original_content = textwrap.dedent(
            """\
            ---
            id: kno-001
            ---
            # Knowledge Document
            This is the original content.
            """,
        )
        memory_fs.write_text(file_path, original_content)

        entry = KnowledgeEntry(
            id="kno-001",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[
                KnowledgeSource(
                    url=_url("https://example.com/doc.md"),
                    etag='"abc123"',
                ),
            ],
        )

        # Configure mock to return 304 Not Modified
        mock_http.configure(status_code=HTTP_NOT_MODIFIED)

        # Act
        updated_entry = syncer.sync_entry(entry, file_path)

        # Assert
        # File content should remain unchanged
        assert memory_fs.read_text(file_path) == original_content

        # Source metadata should remain unchanged (no new etag or last_synced)
        assert updated_entry.sources[0].etag == '"abc123"'
        assert updated_entry.sources[0].last_synced is None

    def test_cache_hit_with_multiple_sources(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """Multiple sources returning 304 should preserve local file."""
        # Arrange
        file_path = Path("docs/knowledge/kno-002.md")
        original_content = "# Original content"
        memory_fs.write_text(file_path, original_content)

        entry = KnowledgeEntry(
            id="kno-002",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[
                KnowledgeSource(
                    url=_url("https://example.com/doc1.md"),
                    etag='"etag1"',
                ),
                KnowledgeSource(
                    url=_url("https://example.com/doc2.md"),
                    etag='"etag2"',
                ),
            ],
        )

        # Configure mock to always return 304
        mock_http.configure(status_code=HTTP_NOT_MODIFIED)

        # Act
        updated_entry = syncer.sync_entry(entry, file_path)

        # Assert
        assert memory_fs.read_text(file_path) == original_content
        assert len(updated_entry.sources) == 2


class TestNewContent:
    """Test scenarios where remote content has changed (200 OK)."""

    def test_new_content_updates_file(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """When server returns 200, file should be updated with new content."""
        # Arrange
        file_path = Path("docs/knowledge/kno-003.md")
        original_content = textwrap.dedent(
            """\
            ---
            id: kno-003
            ---
            # Old Content
            This is outdated.
            """,
        )
        memory_fs.write_text(file_path, original_content)

        new_remote_content = textwrap.dedent(
            """\
            # New Remote Content
            This is the updated version from the source.
            """,
        )

        entry = KnowledgeEntry(
            id="kno-003",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[
                KnowledgeSource(
                    url=_url("https://example.com/doc.md"),
                    etag='"old-etag"',
                ),
            ],
        )

        # Configure mock to return 200 with new content
        mock_http.configure(
            status_code=HTTP_OK,
            text=new_remote_content,
            headers={"ETag": '"new-etag"'},
        )

        # Act
        updated_entry = syncer.sync_entry(entry, file_path)

        # Assert
        # File should contain new remote content
        actual_content = memory_fs.read_text(file_path)
        assert "New Remote Content" in actual_content
        assert "This is the updated version from the source." in actual_content

        # ETag should be updated
        assert updated_entry.sources[0].etag == '"new-etag"'

        # last_synced should be updated
        assert updated_entry.sources[0].last_synced is not None
        assert isinstance(updated_entry.sources[0].last_synced, datetime)

    def test_new_content_preserves_frontmatter(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """New content should preserve existing YAML frontmatter."""
        # Arrange
        file_path = Path("docs/knowledge/kno-004.md")
        original_content = textwrap.dedent(
            """\
            ---
            id: kno-004
            status: active
            tags:
              - security
            ---
            # Old Body
            Old content here.
            """,
        )
        memory_fs.write_text(file_path, original_content)

        new_remote_content = "# New Body\nNew content without frontmatter."

        entry = KnowledgeEntry(
            id="kno-004",
            status=DocStatus.ACTIVE,
            tags=["security"],
            golden_paths="",
            sources=[KnowledgeSource(url=_url("https://example.com/doc.md"))],
        )

        mock_http.configure(
            status_code=HTTP_OK,
            text=new_remote_content,
            headers={"ETag": '"etag-new"'},
        )

        # Act
        _ = syncer.sync_entry(entry, file_path)

        # Assert
        actual_content = memory_fs.read_text(file_path)

        # Frontmatter should be preserved
        assert actual_content.startswith("---")
        assert "id: kno-004" in actual_content
        assert "status: active" in actual_content

        # New content should be present
        assert "New Body" in actual_content
        assert "New content without frontmatter." in actual_content


class TestGoldenPathPreservation:
    """Test scenarios involving Golden Path preservation during merge."""

    def test_golden_path_preserved_during_update(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """Golden Path blocks should be preserved when remote content changes."""
        # Arrange
        file_path = Path("docs/knowledge/kno-005.md")
        original_content = textwrap.dedent(
            """\
            # Document Title
            Some content before golden path.

            <!-- GOLDEN_PATH_START -->
            ## Local Customization
            This is our local rule that should never change.
            <!-- GOLDEN_PATH_END -->

            More content after golden path.
            """,
        )
        memory_fs.write_text(file_path, original_content)

        new_remote_content = textwrap.dedent(
            """\
            # Updated Document Title
            Completely new content from remote source.
            Everything should be replaced except Golden Paths.
            """,
        )

        entry = KnowledgeEntry(
            id="kno-005",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[KnowledgeSource(url=_url("https://example.com/doc.md"))],
        )

        mock_http.configure(
            status_code=HTTP_OK,
            text=new_remote_content,
            headers={"ETag": '"etag-005"'},
        )

        # Act
        syncer.sync_entry(entry, file_path)

        # Assert
        actual_content = memory_fs.read_text(file_path)

        # Golden Path content should be preserved
        assert "<!-- GOLDEN_PATH_START -->" in actual_content
        assert "## Local Customization" in actual_content
        assert "This is our local rule that should never change." in actual_content
        assert "<!-- GOLDEN_PATH_END -->" in actual_content

        # New remote content should also be present
        assert "Updated Document Title" in actual_content
        assert "Completely new content from remote source." in actual_content

    def test_multiple_golden_paths_preserved(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """Multiple Golden Path blocks should all be preserved."""
        # Arrange
        file_path = Path("docs/knowledge/kno-006.md")
        original_content = textwrap.dedent(
            """\
            # Document

            <!-- GOLDEN_PATH_START -->
            First golden path block.
            <!-- GOLDEN_PATH_END -->

            Middle content.

            <!-- GOLDEN_PATH_START -->
            Second golden path block.
            <!-- GOLDEN_PATH_END -->

            End content.
            """,
        )
        memory_fs.write_text(file_path, original_content)

        new_remote_content = "# New Document\nAll new content."

        entry = KnowledgeEntry(
            id="kno-006",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[KnowledgeSource(url=_url("https://example.com/doc.md"))],
        )

        mock_http.configure(status_code=HTTP_OK, text=new_remote_content)

        # Act
        syncer.sync_entry(entry, file_path)

        # Assert
        actual_content = memory_fs.read_text(file_path)

        # Both golden paths should be preserved
        assert actual_content.count("<!-- GOLDEN_PATH_START -->") == 2
        assert actual_content.count("<!-- GOLDEN_PATH_END -->") == 2
        assert "First golden path block." in actual_content
        assert "Second golden path block." in actual_content

    def test_case_insensitive_golden_path_markers(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """Golden Path markers should be recognized case-insensitively."""
        # Arrange
        file_path = Path("docs/knowledge/kno-007.md")
        original_content = textwrap.dedent(
            """\
            # Document

            <!-- golden_path_start -->
            Lowercase markers.
            <!-- golden_path_end -->

            Middle.

            <!-- GOLDEN_PATH_START -->
            Uppercase markers.
            <!-- GOLDEN_PATH_END -->
            """,
        )
        memory_fs.write_text(file_path, original_content)

        new_remote_content = "# New Content"

        entry = KnowledgeEntry(
            id="kno-007",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[KnowledgeSource(url=_url("https://example.com/doc.md"))],
        )

        mock_http.configure(status_code=HTTP_OK, text=new_remote_content)

        # Act
        syncer.sync_entry(entry, file_path)

        # Assert
        actual_content = memory_fs.read_text(file_path)

        # Both variations should be preserved
        assert "Lowercase markers." in actual_content
        assert "Uppercase markers." in actual_content


class TestResilienceToFailures:
    """Test error handling and resilience to network failures."""

    def test_http_exception_preserves_file(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """When HTTP request fails, file should not be corrupted."""
        # Arrange
        file_path = Path("docs/knowledge/kno-008.md")
        original_content = "# Original Content\nDo not corrupt this."
        memory_fs.write_text(file_path, original_content)

        entry = KnowledgeEntry(
            id="kno-008",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[KnowledgeSource(url=_url("https://example.com/doc.md"))],
        )

        # Configure mock to raise exception
        mock_http.configure_exception(ConnectionError("Network unreachable"))

        # Act & Assert
        with pytest.raises(ConnectionError, match="Network unreachable"):
            syncer.sync_entry(entry, file_path)

        # File should remain unchanged
        assert memory_fs.read_text(file_path) == original_content

    def test_http_error_status_preserves_file(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """When server returns error status, file should not be corrupted."""
        # Arrange
        file_path = Path("docs/knowledge/kno-009.md")
        original_content = "# Original Content"
        memory_fs.write_text(file_path, original_content)

        entry = KnowledgeEntry(
            id="kno-009",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[KnowledgeSource(url=_url("https://example.com/doc.md"))],
        )

        # Configure mock to return 500 Internal Server Error
        mock_http.configure(status_code=500)

        # Act & Assert
        with pytest.raises(Exception, match="HTTP 500"):
            syncer.sync_entry(entry, file_path)

        # File should remain unchanged
        assert memory_fs.read_text(file_path) == original_content

    def test_missing_file_creates_new(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """When local file doesn't exist, it should be created."""
        # Arrange
        file_path = Path("docs/knowledge/kno-010.md")

        new_content = "# New Document\nCreated from remote source."

        entry = KnowledgeEntry(
            id="kno-010",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[KnowledgeSource(url=_url("https://example.com/doc.md"))],
        )

        mock_http.configure(status_code=HTTP_OK, text=new_content)

        # Act
        syncer.sync_entry(entry, file_path)

        # Assert
        # File should be created with remote content
        assert memory_fs.exists(file_path)
        actual_content = memory_fs.read_text(file_path)
        assert "New Document" in actual_content
        assert "Created from remote source." in actual_content


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_sources_list(
        self,
        syncer: KnowledgeSyncer,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """Entry with no sources should return unchanged."""
        # Arrange
        file_path = Path("docs/knowledge/kno-011.md")
        original_content = "# Content"
        memory_fs.write_text(file_path, original_content)

        entry = KnowledgeEntry(
            id="kno-011",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[],  # No sources
        )

        # Act
        updated_entry = syncer.sync_entry(entry, file_path)

        # Assert
        assert updated_entry == entry
        assert memory_fs.read_text(file_path) == original_content

    def test_source_without_etag(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """Source without ETag should still work (no If-None-Match header)."""
        # Arrange
        file_path = Path("docs/knowledge/kno-012.md")
        memory_fs.write_text(file_path, "# Old")

        entry = KnowledgeEntry(
            id="kno-012",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[
                KnowledgeSource(
                    url=_url("https://example.com/doc.md"),
                    etag=None,  # No ETag
                ),
            ],
        )

        new_content = "# New Content"
        mock_http.configure(status_code=HTTP_OK, text=new_content)

        # Act
        updated_entry = syncer.sync_entry(entry, file_path)

        # Assert
        actual_content = memory_fs.read_text(file_path)
        assert "New Content" in actual_content
        assert updated_entry.sources[0].last_synced is not None

    def test_response_without_etag_header(
        self,
        syncer: KnowledgeSyncer,
        mock_http: MockHttpClient,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """Response without ETag header should be handled gracefully."""
        # Arrange
        file_path = Path("docs/knowledge/kno-013.md")
        memory_fs.write_text(file_path, "# Old")

        entry = KnowledgeEntry(
            id="kno-013",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths="",
            sources=[KnowledgeSource(url=_url("https://example.com/doc.md"))],
        )

        # Configure mock without ETag header
        mock_http.configure(
            status_code=HTTP_OK,
            text="# New Content",
            headers={},  # No ETag header
        )

        # Act
        updated_entry = syncer.sync_entry(entry, file_path)

        # Assert
        # Should succeed even without ETag
        assert updated_entry.sources[0].etag is None
        actual_content = memory_fs.read_text(file_path)
        assert "New Content" in actual_content
