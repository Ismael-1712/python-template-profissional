"""Unit tests for KnowledgeSyncer network resilience.

This module tests the robustness of the knowledge synchronization system
against various network failures (timeouts, connection errors, HTTP errors).
The system should never crash due to network issues, and should preserve
local content when remote fetching fails.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
from pydantic import HttpUrl

from scripts.core.cortex.knowledge_sync import KnowledgeSyncer
from scripts.core.cortex.models import (
    DocStatus,
    KnowledgeEntry,
    KnowledgeSource,
)
from scripts.utils.filesystem import FileSystemAdapter


class MockFileSystem(FileSystemAdapter):
    """Mock filesystem for testing."""

    def __init__(self) -> None:
        """Initialize mock filesystem."""
        self.files: dict[Path, str] = {}

    def read_text(self, path: str | Path, encoding: str = "utf-8") -> str:
        """Read text from mock file."""
        path = Path(path)
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]

    def write_text(
        self,
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
    ) -> None:
        """Write text to mock file."""
        path = Path(path)
        self.files[path] = content

    def exists(self, path: str | Path) -> bool:
        """Check if mock file exists."""
        return Path(path) in self.files

    def is_file(self, path: str | Path) -> bool:
        """Check if path is a file."""
        return Path(path) in self.files

    def is_dir(self, path: str | Path) -> bool:
        """Check if path is a directory."""
        return False

    def mkdir(
        self,
        path: str | Path,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        """Mock mkdir - no-op for tests."""

    def glob(self, path: str | Path, pattern: str) -> Iterator[Path]:
        """Mock glob - returns empty iterator."""
        return iter([])

    def rglob(self, path: str | Path, pattern: str) -> Iterator[Path]:
        """Mock rglob - returns empty iterator."""
        return iter([])

    def copy(self, src: str | Path, dst: str | Path) -> None:
        """Mock copy - copies between mock files."""
        src_path = Path(src)
        dst_path = Path(dst)
        if src_path in self.files:
            self.files[dst_path] = self.files[src_path]


@pytest.fixture
def mock_fs() -> MockFileSystem:
    """Provide a mock filesystem for tests."""
    return MockFileSystem()


@pytest.fixture
def sample_entry() -> KnowledgeEntry:
    """Provide a sample knowledge entry for tests."""
    return KnowledgeEntry(
        id="kno-001",
        status=DocStatus.ACTIVE,
        tags=["security"],
        golden_paths=[],
        sources=[
            KnowledgeSource(
                url=HttpUrl("https://example.com/doc.md"),
                last_synced=None,
                etag=None,
            ),
        ],
    )


class TestKnowledgeSyncerResilience:
    """Test suite for network resilience in KnowledgeSyncer."""

    def test_fetch_source_timeout(self, mock_fs: MockFileSystem) -> None:
        """Test that Timeout exception is handled gracefully.

        The syncer should:
        - Catch requests.exceptions.Timeout
        - Return (None, None) to signal no changes
        - NOT raise the exception (preserve local content)
        """
        # Arrange
        mock_http = Mock()
        mock_http.get.side_effect = requests.exceptions.Timeout(
            "Connection timed out after 10 seconds",
        )

        syncer = KnowledgeSyncer(fs=mock_fs, http_client=mock_http)
        source = KnowledgeSource(
            url=HttpUrl("https://example.com/slow-server.md"),
            last_synced=None,
            etag=None,
        )

        # Act - should NOT raise exception
        result = syncer._fetch_source(source)

        # Assert
        assert result == (None, None), "Should return (None, None) on timeout"
        mock_http.get.assert_called_once()

    def test_fetch_source_connection_error(
        self,
        mock_fs: MockFileSystem,
    ) -> None:
        """Test that ConnectionError is handled gracefully.

        The syncer should:
        - Catch requests.exceptions.ConnectionError
        - Return (None, None) to signal no changes
        - NOT raise the exception
        """
        # Arrange
        mock_http = Mock()
        mock_http.get.side_effect = requests.exceptions.ConnectionError(
            "Failed to establish connection: Network is unreachable",
        )

        syncer = KnowledgeSyncer(fs=mock_fs, http_client=mock_http)
        source = KnowledgeSource(
            url=HttpUrl("https://unreachable-server.com/doc.md"),
            last_synced=None,
            etag=None,
        )

        # Act
        result = syncer._fetch_source(source)

        # Assert
        assert result == (None, None), "Should return (None, None) on connection error"

    def test_fetch_source_http_error(self, mock_fs: MockFileSystem) -> None:
        """Test that HTTPError (4xx/5xx) is handled gracefully.

        The syncer should:
        - Catch requests.exceptions.HTTPError
        - Return (None, None) to signal no changes
        - NOT raise the exception
        """
        # Arrange
        mock_http = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "500 Server Error: Internal Server Error",
            response=mock_response,
        )

        mock_http.get.return_value = mock_response

        syncer = KnowledgeSyncer(fs=mock_fs, http_client=mock_http)
        source = KnowledgeSource(
            url=HttpUrl("https://broken-server.com/doc.md"),
            last_synced=None,
            etag=None,
        )

        # Act
        result = syncer._fetch_source(source)

        # Assert
        assert result == (None, None), "Should return (None, None) on HTTP error"

    def test_fetch_source_generic_request_exception(
        self,
        mock_fs: MockFileSystem,
    ) -> None:
        """Test that generic RequestException is handled gracefully.

        This is the catch-all for any other network errors.
        """
        # Arrange
        mock_http = Mock()
        mock_http.get.side_effect = requests.exceptions.RequestException(
            "Unknown network error",
        )

        syncer = KnowledgeSyncer(fs=mock_fs, http_client=mock_http)
        source = KnowledgeSource(
            url=HttpUrl("https://example.com/doc.md"),
            last_synced=None,
            etag=None,
        )

        # Act
        result = syncer._fetch_source(source)

        # Assert
        assert result == (None, None), "Should return (None, None) on generic error"

    def test_fetch_source_success(self, mock_fs: MockFileSystem) -> None:
        """Test the happy path - successful fetch with new content.

        Verify that the error handling does NOT interfere with normal operation.
        """
        # Arrange
        mock_http = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "# Remote Content\n\nNew documentation"
        mock_response.headers = {"ETag": '"abc123"'}
        mock_http.get.return_value = mock_response

        syncer = KnowledgeSyncer(fs=mock_fs, http_client=mock_http)
        source = KnowledgeSource(
            url=HttpUrl("https://example.com/doc.md"),
            last_synced=None,
            etag=None,
        )

        # Act
        content, etag = syncer._fetch_source(source)

        # Assert
        assert content == "# Remote Content\n\nNew documentation"
        assert etag == '"abc123"'

    def test_fetch_source_not_modified(self, mock_fs: MockFileSystem) -> None:
        """Test that 304 Not Modified is handled correctly.

        When content hasn't changed (ETag match), should return (None, None).
        """
        # Arrange
        mock_http = Mock()
        mock_response = Mock()
        mock_response.status_code = 304  # Not Modified
        mock_http.get.return_value = mock_response

        syncer = KnowledgeSyncer(fs=mock_fs, http_client=mock_http)
        source = KnowledgeSource(
            url=HttpUrl("https://example.com/doc.md"),
            last_synced=datetime.now(timezone.utc),
            etag='"old-etag"',
        )

        # Act
        result = syncer._fetch_source(source)

        # Assert
        assert result == (None, None), "Should return (None, None) on 304"
        # Verify If-None-Match header was sent
        call_kwargs = mock_http.get.call_args[1]
        assert call_kwargs["headers"]["If-None-Match"] == '"old-etag"'

    def test_sync_entry_preserves_local_on_network_failure(
        self,
        mock_fs: MockFileSystem,
        sample_entry: KnowledgeEntry,
    ) -> None:
        """Test that local content is preserved when network fetch fails.

        This is the integration test that verifies the whole system:
        - Network fails
        - sync_entry continues without crashing
        - Local file is NOT modified
        """
        # Arrange
        file_path = Path("docs/knowledge/kno-001.md")
        original_content = """---
id: kno-001
---
# Local Content

<!-- GOLDEN_PATH_START -->
Local customization
<!-- GOLDEN_PATH_END -->
"""
        mock_fs.files[file_path] = original_content

        # Simulate network timeout
        mock_http = Mock()
        mock_http.get.side_effect = requests.exceptions.Timeout("Network timeout")

        syncer = KnowledgeSyncer(fs=mock_fs, http_client=mock_http)

        # Act
        result = syncer.sync_entry(sample_entry, file_path)

        # Assert
        # Local file should NOT be modified
        assert mock_fs.files[file_path] == original_content
        # Entry should be returned unchanged (no new sync timestamp)
        assert result.entry.sources[0].last_synced is None
        assert result.entry.sources[0].etag is None
