"""Unit tests for KnowledgeScanner.

Tests the Knowledge Node scanner's ability to parse Markdown files with
YAML frontmatter, handle errors gracefully, and work with the FileSystemAdapter.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
from scripts.core.cortex.models import DocStatus
from scripts.utils.filesystem import MemoryFileSystem


class TestKnowledgeScannerValid:
    """Tests for valid knowledge file scanning."""

    def test_scan_single_valid_file(self) -> None:
        """Test scanning a single valid knowledge file."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")
        knowledge_dir = workspace / "docs" / "knowledge"

        # YAML must be at column 0 (no extra indentation)
        valid_frontmatter = textwrap.dedent("""
            ---
            id: kno-001
            status: active
            golden_paths: auth/jwt.py -> docs/auth.md
            tags:
              - authentication
              - jwt
            sources:
              - url: https://example.com/docs/auth.md
            ---
            # Authentication Guide

            This is the cached content about authentication.
            """).strip()
        fs.write_text(knowledge_dir / "kno-001.md", valid_frontmatter)

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert
        assert len(entries) == 1
        entry = entries[0]
        assert entry.id == "kno-001"
        assert entry.status == DocStatus.ACTIVE
        assert entry.golden_paths == "auth/jwt.py -> docs/auth.md"
        assert entry.tags == ["authentication", "jwt"]
        assert len(entry.sources) == 1
        assert str(entry.sources[0].url) == "https://example.com/docs/auth.md"
        assert entry.cached_content is not None
        assert "Authentication Guide" in entry.cached_content

    def test_scan_minimal_required_fields(self) -> None:
        """Test scanning file with only required fields."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")
        knowledge_dir = workspace / "docs" / "knowledge"

        minimal_file = textwrap.dedent("""
            ---
            id: kno-minimal
            status: active
            golden_paths: minimal/path
            ---
            """).strip()
        fs.write_text(knowledge_dir / "minimal.md", minimal_file)

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert
        assert len(entries) == 1
        entry = entries[0]
        assert entry.id == "kno-minimal"
        assert entry.status == DocStatus.ACTIVE
        assert entry.tags == []
        assert entry.sources == []
        assert entry.cached_content is None


class TestKnowledgeScannerResilience:
    """Tests for error handling and resilience."""

    def test_scan_nonexistent_directory(self) -> None:
        """Test scanning a directory that doesn't exist."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert - should return empty list, not crash
        assert entries == []

    def test_scan_path_is_file_not_directory(self) -> None:
        """Test scanning when path exists but is a file, not directory."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")
        fake_dir = workspace / "docs" / "knowledge"

        # Create a file at the path where directory should be
        fs.write_text(fake_dir, "I'm a file, not a directory!")

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert - should return empty list, not crash
        assert entries == []

    def test_scan_missing_required_field_id(self) -> None:
        """Test scanning file missing required 'id' field."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")
        knowledge_dir = workspace / "docs" / "knowledge"

        missing_id = textwrap.dedent("""
            ---
            status: active
            golden_paths: some/path
            ---
            Content
            """).strip()
        fs.write_text(knowledge_dir / "no-id.md", missing_id)

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert - should skip file with missing required field
        assert entries == []

    def test_scan_invalid_status_value(self) -> None:
        """Test scanning file with invalid status enum value."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")
        knowledge_dir = workspace / "docs" / "knowledge"

        invalid_status = textwrap.dedent("""
            ---
            id: kno-bad-status
            status: invalid_status_value
            golden_paths: some/path
            ---
            Content
            """).strip()
        fs.write_text(knowledge_dir / "bad-status.md", invalid_status)

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert - should skip file with invalid status
        assert entries == []

    def test_scan_partial_success_mixed_files(self) -> None:
        """Test scanning directory with both valid and invalid files."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")
        knowledge_dir = workspace / "docs" / "knowledge"

        # Valid file
        valid_file = textwrap.dedent("""
            ---
            id: kno-valid
            status: active
            golden_paths: valid/path
            ---
            Valid content
            """).strip()
        # Invalid file (missing id)
        invalid_file = textwrap.dedent("""
            ---
            status: active
            golden_paths: invalid/path
            ---
            Invalid content
            """).strip()
        fs.write_text(knowledge_dir / "valid.md", valid_file)
        fs.write_text(knowledge_dir / "invalid.md", invalid_file)

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert - should parse valid file, skip invalid
        assert len(entries) == 1
        assert entries[0].id == "kno-valid"


class TestKnowledgeScannerEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_scan_empty_directory(self) -> None:
        """Test scanning an empty directory."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")
        knowledge_dir = workspace / "docs" / "knowledge"
        fs.mkdir(knowledge_dir)

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert - should return empty list
        assert entries == []

    def test_scan_directory_with_non_markdown_files(self) -> None:
        """Test scanning directory with non-.md files (should be ignored)."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")
        knowledge_dir = workspace / "docs" / "knowledge"

        # Create non-markdown files
        fs.write_text(knowledge_dir / "readme.txt", "Not a markdown file")
        fs.write_text(knowledge_dir / "config.yaml", "key: value")

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert - should ignore non-.md files
        assert entries == []


class TestKnowledgeScannerDependencyInjection:
    """Tests for FileSystemAdapter dependency injection."""

    def test_scanner_uses_injected_filesystem(self) -> None:
        """Test that scanner uses the injected FileSystemAdapter."""
        # Arrange
        fs = MemoryFileSystem()
        workspace = Path("/project")
        knowledge_dir = workspace / "docs" / "knowledge"

        valid_file = textwrap.dedent("""
            ---
            id: kno-inject
            status: active
            golden_paths: inject/path
            ---
            Injected FS test
            """).strip()
        fs.write_text(knowledge_dir / "inject.md", valid_file)

        # Act
        scanner = KnowledgeScanner(workspace_root=workspace, fs=fs)
        entries = scanner.scan()

        # Assert - if it works, the injected FS was used
        assert len(entries) == 1
        assert entries[0].id == "kno-inject"

    def test_scanner_defaults_to_real_filesystem(self) -> None:
        """Test that scanner defaults to RealFileSystem when fs=None."""
        # Arrange
        workspace = Path("/project")

        # Act - create scanner without fs parameter
        scanner = KnowledgeScanner(workspace_root=workspace)

        # Assert - should have a filesystem adapter
        assert scanner.fs is not None
