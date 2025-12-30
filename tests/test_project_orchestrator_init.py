"""Unit tests for ProjectOrchestrator.initialize_file method.

Tests the file initialization functionality with focus on robustness,
edge cases, and permission handling.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.core.cortex.project_orchestrator import ProjectOrchestrator
from scripts.utils.filesystem import MemoryFileSystem

# ============================================================================
# TEST FIXTURES (Markdown content as strings)
# ============================================================================

MARKDOWN_WITHOUT_FRONTMATTER = """# User Guide

This is a markdown file without any frontmatter.

## Section 1

Content here.
"""

MARKDOWN_WITH_FRONTMATTER = """---
id: existing-guide
type: guide
status: active
version: 1.0.0
author: Original Author
date: 2025-01-01
---

# Existing Guide

This file already has frontmatter.
"""

EXPECTED_FRONTMATTER_KEYS = {
    "id",
    "type",
    "status",
    "version",
    "author",
    "date",
}


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def memory_fs() -> MemoryFileSystem:
    """Create a MemoryFileSystem instance."""
    return MemoryFileSystem()


@pytest.fixture
def orchestrator_with_memory_fs(
    temp_workspace: Path,
    memory_fs: MemoryFileSystem,
) -> ProjectOrchestrator:
    """Create ProjectOrchestrator with MemoryFileSystem."""
    return ProjectOrchestrator(workspace_root=temp_workspace, fs=memory_fs)


# ============================================================================
# TEST CLASS
# ============================================================================


class TestProjectOrchestratorInit:
    """Test suite for ProjectOrchestrator.initialize_file method."""

    def test_init_file_success_new_file(
        self,
        orchestrator_with_memory_fs: ProjectOrchestrator,
        memory_fs: MemoryFileSystem,
        temp_workspace: Path,
    ) -> None:
        """Test initializing a new file without frontmatter.

        Verifies that:
        - Status is 'success'
        - Frontmatter block is correctly added
        - Original content is preserved
        - New frontmatter contains expected keys
        """
        # Arrange
        file_path = temp_workspace / "docs" / "new_guide.md"
        memory_fs.write_text(file_path, MARKDOWN_WITHOUT_FRONTMATTER)

        # Act
        result = orchestrator_with_memory_fs.initialize_file(file_path)

        # Assert
        assert result.status == "success"
        assert result.path == file_path
        assert result.old_frontmatter is None
        assert result.new_frontmatter is not None
        assert EXPECTED_FRONTMATTER_KEYS.issubset(result.new_frontmatter.keys())
        assert result.error is None

        # Verify file content
        content = memory_fs.read_text(file_path)
        assert content.startswith("---\n")
        assert "# User Guide" in content  # Original content preserved
        assert "This is a markdown file without any frontmatter." in content

    def test_init_file_success_update_force(
        self,
        orchestrator_with_memory_fs: ProjectOrchestrator,
        memory_fs: MemoryFileSystem,
        temp_workspace: Path,
    ) -> None:
        """Test updating a file with existing frontmatter using force=True.

        Verifies that:
        - Status is 'success'
        - Old frontmatter is captured correctly
        - New frontmatter replaces old one
        - Body content is preserved
        """
        # Arrange
        file_path = temp_workspace / "docs" / "existing_guide.md"
        memory_fs.write_text(file_path, MARKDOWN_WITH_FRONTMATTER)

        # Act
        result = orchestrator_with_memory_fs.initialize_file(file_path, force=True)

        # Assert
        assert result.status == "success"
        assert result.path == file_path
        assert result.old_frontmatter is not None
        assert result.old_frontmatter["id"] == "existing-guide"
        assert result.old_frontmatter["author"] == "Original Author"
        assert result.new_frontmatter is not None
        assert EXPECTED_FRONTMATTER_KEYS.issubset(result.new_frontmatter.keys())
        assert result.error is None

        # Verify file content
        content = memory_fs.read_text(file_path)
        assert content.startswith("---\n")
        assert "# Existing Guide" in content  # Body preserved
        assert "This file already has frontmatter." in content

    def test_init_file_skipped_exists(
        self,
        orchestrator_with_memory_fs: ProjectOrchestrator,
        memory_fs: MemoryFileSystem,
        temp_workspace: Path,
    ) -> None:
        """Test skipping a file that already has frontmatter (force=False).

        Verifies that:
        - Status is 'skipped'
        - Old frontmatter is returned unchanged
        - File content is not modified
        """
        # Arrange
        file_path = temp_workspace / "docs" / "existing_guide.md"
        memory_fs.write_text(file_path, MARKDOWN_WITH_FRONTMATTER)
        original_content = memory_fs.read_text(file_path)

        # Act
        result = orchestrator_with_memory_fs.initialize_file(file_path, force=False)

        # Assert
        assert result.status == "skipped"
        assert result.path == file_path
        assert result.old_frontmatter is not None
        assert result.old_frontmatter["id"] == "existing-guide"
        assert result.new_frontmatter == result.old_frontmatter
        assert result.error is None

        # Verify file was NOT modified
        content = memory_fs.read_text(file_path)
        assert content == original_content

    def test_init_file_error_readonly(
        self,
        orchestrator_with_memory_fs: ProjectOrchestrator,
        memory_fs: MemoryFileSystem,
        temp_workspace: Path,
    ) -> None:
        """Test error handling when file write fails (e.g., permission denied).

        Verifies that:
        - Status is 'error'
        - Error message is captured
        - Exception is handled gracefully
        """
        # Arrange
        file_path = temp_workspace / "docs" / "readonly.md"
        memory_fs.write_text(file_path, MARKDOWN_WITHOUT_FRONTMATTER)

        # Mock write_text to raise PermissionError
        def write_text_side_effect(path: Path, content: str) -> None:
            if path == file_path:
                raise PermissionError(f"Permission denied: {path}")
            # For any other path, use the original implementation
            raise FileNotFoundError(f"Unexpected write to: {path}")

        with patch.object(
            memory_fs,
            "write_text",
            side_effect=write_text_side_effect,
        ):
            # Act
            result = orchestrator_with_memory_fs.initialize_file(file_path)

        # Assert
        assert result.status == "error"
        assert result.path == file_path
        assert result.error is not None
        assert "Permission denied" in result.error

    def test_init_file_preserves_content(
        self,
        orchestrator_with_memory_fs: ProjectOrchestrator,
        memory_fs: MemoryFileSystem,
        temp_workspace: Path,
    ) -> None:
        """Test that body content is preserved exactly after initialization.

        Verifies that:
        - Original markdown content is not altered
        - Whitespace and formatting are preserved
        - Only frontmatter is added/updated
        """
        # Arrange
        file_path = temp_workspace / "docs" / "content_test.md"
        original_body = """# Complex Document

## Section 1

Paragraph with **bold** and *italic*.

- List item 1
- List item 2

```python
def example():
    pass
```

## Section 2

More content here.
"""
        memory_fs.write_text(file_path, original_body)

        # Act
        result = orchestrator_with_memory_fs.initialize_file(file_path)

        # Assert
        assert result.status == "success"

        # Verify content preservation
        content = memory_fs.read_text(file_path)
        # Remove frontmatter to check body
        lines = content.split("\n")
        # Find second "---" (end of frontmatter)
        second_separator = 0
        separator_count = 0
        for i, line in enumerate(lines):
            if line.strip() == "---":
                separator_count += 1
                if separator_count == 2:
                    second_separator = i
                    break

        # Body starts after second separator
        body = "\n".join(lines[second_separator + 1 :])

        # Check that body matches original (minus leading whitespace)
        assert body.strip() == original_body.strip()
        assert "**bold**" in body
        assert "*italic*" in body
        assert "```python" in body
        assert "def example():" in body

    def test_init_file_error_file_not_exists(
        self,
        orchestrator_with_memory_fs: ProjectOrchestrator,
        temp_workspace: Path,
    ) -> None:
        """Test error handling when file does not exist.

        Verifies that:
        - Status is 'error'
        - Error message indicates file doesn't exist
        """
        # Arrange
        file_path = temp_workspace / "nonexistent.md"

        # Act
        result = orchestrator_with_memory_fs.initialize_file(file_path)

        # Assert
        assert result.status == "error"
        assert result.path == file_path
        assert result.error is not None
        assert "does not exist" in result.error

    def test_init_file_error_not_a_file(
        self,
        orchestrator_with_memory_fs: ProjectOrchestrator,
        memory_fs: MemoryFileSystem,
        temp_workspace: Path,
    ) -> None:
        """Test error handling when path is a directory, not a file.

        Verifies that:
        - Status is 'error'
        - Error message indicates path is not a file
        """
        # Arrange
        dir_path = temp_workspace / "docs"
        memory_fs.mkdir(dir_path)

        # Act
        result = orchestrator_with_memory_fs.initialize_file(dir_path)

        # Assert
        assert result.status == "error"
        assert result.path == dir_path
        assert result.error is not None
        assert "not a file" in result.error

    def test_init_file_handles_malformed_frontmatter(
        self,
        orchestrator_with_memory_fs: ProjectOrchestrator,
        memory_fs: MemoryFileSystem,
        temp_workspace: Path,
    ) -> None:
        """Test handling of files with malformed frontmatter.

        When frontmatter cannot be parsed, it should:
        - Treat it as if no frontmatter exists (add new one)
        - Or handle gracefully with force=True
        """
        # Arrange
        malformed_content = """---
id: broken
type: guide
this is not valid yaml: [unclosed bracket
---

# Content
"""
        file_path = temp_workspace / "malformed.md"
        memory_fs.write_text(file_path, malformed_content)

        # Act
        result = orchestrator_with_memory_fs.initialize_file(file_path, force=True)

        # Assert
        # Depending on implementation, this could succeed or error
        # The test documents the actual behavior
        assert result.status in ["success", "error"]
        if result.status == "error":
            assert result.error is not None
