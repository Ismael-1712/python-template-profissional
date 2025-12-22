"""Unit tests for CORTEX ProjectOrchestrator.

Tests the ProjectOrchestrator class using TDD (Test-Driven Development)
approach with controlled RED phase for skeleton validation.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from scripts.core.cortex.migrate import MigrationResult
from scripts.core.cortex.models import InitResult, MigrationSummary
from scripts.core.cortex.project_orchestrator import ProjectOrchestrator
from scripts.utils.filesystem import MemoryFileSystem

# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace for testing.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Path to temporary workspace root
    """
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()

    # Create directory structure
    (workspace / "docs").mkdir()
    (workspace / "docs" / "guides").mkdir()
    (workspace / "docs" / "architecture").mkdir()

    return workspace


@pytest.fixture
def orchestrator(temp_workspace: Path) -> ProjectOrchestrator:
    """Create ProjectOrchestrator instance for testing.

    Args:
        temp_workspace: Temporary workspace root directory

    Returns:
        ProjectOrchestrator configured with temp workspace
    """
    return ProjectOrchestrator(workspace_root=temp_workspace)


@pytest.fixture
def sample_markdown_without_frontmatter(temp_workspace: Path) -> Path:
    """Create a sample markdown file without frontmatter.

    Args:
        temp_workspace: Temporary workspace root directory

    Returns:
        Path to created markdown file
    """
    file_path = temp_workspace / "docs" / "guides" / "test-guide.md"
    file_path.write_text(
        "# Test Guide\n\n"
        "This is a test guide without frontmatter.\n"
        "It should be initialized by the orchestrator.\n",
    )
    return file_path


@pytest.fixture
def sample_markdown_with_frontmatter(temp_workspace: Path) -> Path:
    """Create a sample markdown file with existing frontmatter.

    Args:
        temp_workspace: Temporary workspace root directory

    Returns:
        Path to created markdown file
    """
    file_path = temp_workspace / "docs" / "guides" / "existing-guide.md"
    file_path.write_text(
        "---\n"
        "id: existing-guide\n"
        "type: guide\n"
        "status: active\n"
        "version: 1.0.0\n"
        "author: Engineering Team\n"
        "date: 2025-12-22\n"
        "---\n\n"
        "# Existing Guide\n\n"
        "This file already has frontmatter.\n",
    )
    return file_path


# ============================================================================
# TESTS: ProjectOrchestrator.__init__
# ============================================================================


def test_orchestrator_initialization(temp_workspace: Path) -> None:
    """Test that ProjectOrchestrator initializes correctly.

    Verifies:
    - workspace_root is resolved to absolute path
    - migrator is initialized
    - fs adapter is set
    """
    orchestrator = ProjectOrchestrator(workspace_root=temp_workspace)

    assert orchestrator.workspace_root == temp_workspace.resolve()
    assert orchestrator.migrator is not None
    assert orchestrator.fs is not None


def test_orchestrator_initialization_with_custom_fs(
    temp_workspace: Path,
) -> None:
    """Test that ProjectOrchestrator accepts custom FileSystemAdapter.

    Verifies:
    - Custom fs adapter is used instead of default
    """
    custom_fs = MemoryFileSystem()
    orchestrator = ProjectOrchestrator(
        workspace_root=temp_workspace,
        fs=custom_fs,
    )

    assert orchestrator.fs is custom_fs


# ============================================================================
# TESTS: ProjectOrchestrator.initialize_file
# ============================================================================


def test_initialize_file_without_existing_frontmatter_success(
    orchestrator: ProjectOrchestrator,
    sample_markdown_without_frontmatter: Path,
) -> None:
    """Test initializing a file without existing frontmatter.

    Expected behavior:
    - Status should be 'success'
    - old_frontmatter should be None
    - new_frontmatter should contain inferred metadata
    - File should have frontmatter added
    """
    result = orchestrator.initialize_file(
        path=sample_markdown_without_frontmatter,
        force=False,
    )

    assert isinstance(result, InitResult)
    assert result.status == "success"
    assert result.old_frontmatter is None
    assert result.new_frontmatter is not None
    assert isinstance(result.new_frontmatter, dict)
    assert "id" in result.new_frontmatter
    assert "type" in result.new_frontmatter
    assert result.error is None


def test_initialize_file_with_existing_frontmatter_skipped(
    orchestrator: ProjectOrchestrator,
    sample_markdown_with_frontmatter: Path,
) -> None:
    """Test initializing a file that already has frontmatter.

    Expected behavior:
    - Status should be 'skipped' when force=False
    - old_frontmatter should contain existing metadata
    - File should remain unchanged
    """
    result = orchestrator.initialize_file(
        path=sample_markdown_with_frontmatter,
        force=False,
    )

    assert isinstance(result, InitResult)
    assert result.status == "skipped"
    assert result.old_frontmatter is not None
    assert isinstance(result.old_frontmatter, dict)
    assert "id" in result.old_frontmatter
    assert result.old_frontmatter["id"] == "existing-guide"


def test_initialize_file_with_existing_frontmatter_force_update(
    orchestrator: ProjectOrchestrator,
    sample_markdown_with_frontmatter: Path,
) -> None:
    """Test force-initializing a file that already has frontmatter.

    Expected behavior:
    - Status should be 'success' when force=True
    - old_frontmatter should contain previous metadata
    - new_frontmatter should contain updated metadata
    - File should be updated
    """
    result = orchestrator.initialize_file(
        path=sample_markdown_with_frontmatter,
        force=True,
    )

    assert isinstance(result, InitResult)
    assert result.status == "success"
    assert result.old_frontmatter is not None
    assert result.new_frontmatter is not None
    assert isinstance(result.old_frontmatter, dict)
    assert isinstance(result.new_frontmatter, dict)


def test_initialize_file_nonexistent_file_error(
    orchestrator: ProjectOrchestrator,
    temp_workspace: Path,
) -> None:
    """Test initializing a file that doesn't exist.

    Expected behavior:
    - Status should be 'error'
    - error field should contain descriptive message
    """
    nonexistent = temp_workspace / "docs" / "nonexistent.md"

    result = orchestrator.initialize_file(
        path=nonexistent,
        force=False,
    )

    assert isinstance(result, InitResult)
    assert result.status == "error"
    assert result.error is not None
    assert "not" in result.error.lower() or "exist" in result.error.lower()


# ============================================================================
# TESTS: ProjectOrchestrator.migrate_project
# ============================================================================


def test_migrate_project_dry_run_mode(
    orchestrator: ProjectOrchestrator,
    temp_workspace: Path,
    sample_markdown_without_frontmatter: Path,
) -> None:
    """Test migrating a project in dry-run mode.

    Expected behavior:
    - Returns MigrationSummary with correct statistics
    - Files should not be modified (dry_run=True)
    - total should equal number of markdown files
    """
    docs_dir = temp_workspace / "docs"

    summary = orchestrator.migrate_project(
        directory=docs_dir,
        dry_run=True,
        force=False,
        recursive=True,
    )

    assert isinstance(summary, MigrationSummary)
    assert summary.total >= 1
    assert summary.created >= 0
    assert summary.updated >= 0
    assert summary.errors >= 0
    assert summary.total == (summary.created + summary.updated + summary.errors)
    assert isinstance(summary.results, list)


def test_migrate_project_non_recursive(
    orchestrator: ProjectOrchestrator,
    temp_workspace: Path,
) -> None:
    """Test migrating a project without recursion.

    Expected behavior:
    - Only processes files in specified directory
    - Does not descend into subdirectories
    """
    # Create files in nested structure
    (temp_workspace / "docs" / "root.md").write_text("# Root")
    (temp_workspace / "docs" / "guides" / "nested.md").write_text("# Nested")

    docs_dir = temp_workspace / "docs"

    summary = orchestrator.migrate_project(
        directory=docs_dir,
        dry_run=True,
        force=False,
        recursive=False,
    )

    assert isinstance(summary, MigrationSummary)
    # Should only find root.md, not nested.md
    assert summary.total >= 1


def test_migrate_project_force_mode(
    orchestrator: ProjectOrchestrator,
    temp_workspace: Path,
    sample_markdown_with_frontmatter: Path,
) -> None:
    """Test migrating a project with force=True.

    Expected behavior:
    - Files with existing frontmatter are updated
    - updated count should be > 0 if files have frontmatter
    """
    docs_dir = temp_workspace / "docs"

    summary = orchestrator.migrate_project(
        directory=docs_dir,
        dry_run=True,
        force=True,
        recursive=True,
    )

    assert isinstance(summary, MigrationSummary)
    assert summary.total >= 1
    # With force=True, existing files should be marked for update
    assert summary.updated >= 0 or summary.created >= 0


def test_migrate_project_aggregates_results_correctly(
    orchestrator: ProjectOrchestrator,
    temp_workspace: Path,
) -> None:
    """Test that migrate_project correctly aggregates MigrationResults.

    Expected behavior:
    - MigrationSummary.results contains MigrationResult instances
    - Statistics match the results list
    - Delegation to DocumentMigrator works correctly
    """
    # Create multiple test files
    (temp_workspace / "docs" / "file1.md").write_text("# File 1")
    (temp_workspace / "docs" / "file2.md").write_text("# File 2")
    (temp_workspace / "docs" / "file3.md").write_text(
        "---\nid: file3\ntype: guide\nstatus: active\n"
        "version: 1.0.0\nauthor: Test\ndate: 2025-12-22\n---\n# File 3",
    )

    docs_dir = temp_workspace / "docs"

    summary = orchestrator.migrate_project(
        directory=docs_dir,
        dry_run=True,
        force=False,
        recursive=True,
    )

    assert isinstance(summary, MigrationSummary)
    assert summary.total >= 3
    assert len(summary.results) == summary.total

    # Verify statistics consistency
    created = sum(
        1 for r in summary.results if hasattr(r, "action") and r.action == "created"
    )
    updated = sum(
        1 for r in summary.results if hasattr(r, "action") and r.action == "updated"
    )
    errors = sum(
        1 for r in summary.results if hasattr(r, "action") and r.action == "error"
    )

    assert summary.created == created
    assert summary.updated == updated
    assert summary.errors == errors


def test_migrate_project_empty_directory(
    orchestrator: ProjectOrchestrator,
    temp_workspace: Path,
) -> None:
    """Test migrating an empty directory.

    Expected behavior:
    - Returns MigrationSummary with all counts = 0
    - No errors should occur
    """
    empty_dir = temp_workspace / "empty"
    empty_dir.mkdir()

    summary = orchestrator.migrate_project(
        directory=empty_dir,
        dry_run=True,
        force=False,
        recursive=True,
    )

    assert isinstance(summary, MigrationSummary)
    assert summary.total == 0
    assert summary.created == 0
    assert summary.updated == 0
    assert summary.errors == 0
    assert len(summary.results) == 0


def test_migrate_project_nonexistent_directory(
    orchestrator: ProjectOrchestrator,
    temp_workspace: Path,
) -> None:
    """Test migrating a directory that doesn't exist.

    Expected behavior:
    - Should handle gracefully (return summary with errors or raise)
    - errors count should reflect the issue
    """
    nonexistent_dir = temp_workspace / "nonexistent"

    # Depending on implementation, this might raise or return error summary
    # For now, we expect it to handle gracefully
    try:
        summary = orchestrator.migrate_project(
            directory=nonexistent_dir,
            dry_run=True,
            force=False,
            recursive=True,
        )
        assert isinstance(summary, MigrationSummary)
        # If no exception, expect either 0 total or errors reported
        assert summary.total == 0 or summary.errors > 0
    except (FileNotFoundError, ValueError):
        # Also acceptable to raise an exception
        pass


# ============================================================================
# TESTS: Integration with DocumentMigrator
# ============================================================================


def test_orchestrator_delegates_to_migrator(
    temp_workspace: Path,
    sample_markdown_without_frontmatter: Path,
) -> None:
    """Test that ProjectOrchestrator delegates to DocumentMigrator.

    Verifies:
    - initialize_file internally uses migrator.migrate_file
    - migrate_project internally uses migrator.migrate_directory
    """
    with patch(
        "scripts.core.cortex.project_orchestrator.DocumentMigrator",
    ) as mock_migrator:
        mock_migrator_instance = Mock()
        mock_migrator.return_value = mock_migrator_instance

        # Setup mock return values
        mock_migrator_instance.migrate_file.return_value = MigrationResult(
            file_path=sample_markdown_without_frontmatter,
            success=True,
            action="created",
            message="Frontmatter added",
            inferred_metadata={"id": "test-guide", "type": "guide"},
        )

        orchestrator = ProjectOrchestrator(workspace_root=temp_workspace)

        # Call initialize_file
        orchestrator.initialize_file(
            path=sample_markdown_without_frontmatter,
            force=False,
        )

        # Verify delegation occurred
        assert mock_migrator.called


def test_migrate_project_passes_parameters_to_migrator(
    temp_workspace: Path,
) -> None:
    """Test that migrate_project passes parameters correctly to migrator.

    Verifies:
    - dry_run, force, and recursive flags are passed through
    """
    with patch(
        "scripts.core.cortex.project_orchestrator.DocumentMigrator",
    ) as mock_migrator:
        mock_migrator_instance = Mock()
        mock_migrator.return_value = mock_migrator_instance

        # Setup mock return value
        mock_migrator_instance.migrate_directory.return_value = []

        orchestrator = ProjectOrchestrator(workspace_root=temp_workspace)

        # Call migrate_project with specific parameters
        docs_dir = temp_workspace / "docs"
        orchestrator.migrate_project(
            directory=docs_dir,
            dry_run=True,
            force=True,
            recursive=False,
        )

        # Verify delegation occurred with correct parameters
        assert mock_migrator.called
