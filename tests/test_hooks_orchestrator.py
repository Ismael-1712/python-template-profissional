"""Unit tests for HooksOrchestrator.

Tests Git hooks detection, generation, and installation.
Following TDD approach - these tests will FAIL initially (RED phase).

Author: GEM & SRE Team
License: MIT
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from scripts.core.cortex.hooks_orchestrator import (
    GitDirectoryNotFoundError,
    HookInstallationError,
    HooksOrchestrator,
)


class TestHooksOrchestratorInit:
    """Test HooksOrchestrator initialization."""

    def test_init_with_valid_path(self, tmp_path: Path) -> None:
        """HooksOrchestrator should initialize with valid project root."""
        orchestrator = HooksOrchestrator(project_root=tmp_path)
        assert orchestrator.project_root == tmp_path

    def test_init_stores_project_root(self, tmp_path: Path) -> None:
        """HooksOrchestrator should store project root for operations."""
        orchestrator = HooksOrchestrator(project_root=tmp_path)
        assert orchestrator.project_root.exists()


class TestDetectGitDirectory:
    """Test Git directory detection."""

    def test_detect_git_directory_exists(self, tmp_path: Path) -> None:
        """detect_git_directory() should return .git path when it exists."""
        # Arrange
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        result = orchestrator.detect_git_directory()

        # Assert
        assert result == git_dir
        assert result.exists()

    def test_detect_git_directory_not_found(self, tmp_path: Path) -> None:
        """detect_git_directory() should raise error when .git missing."""
        # Arrange
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act & Assert
        with pytest.raises(GitDirectoryNotFoundError, match=".git"):
            orchestrator.detect_git_directory()

    def test_detect_git_directory_is_file(self, tmp_path: Path) -> None:
        """detect_git_directory() should raise error if .git is a file."""
        # Arrange
        git_file = tmp_path / ".git"
        git_file.write_text("gitdir: ../other/.git")  # Submodule format
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act & Assert
        # Should handle .git file (worktree/submodule) or raise appropriate error
        with pytest.raises(GitDirectoryNotFoundError):
            orchestrator.detect_git_directory()


class TestGenerateHookScript:
    """Test Git hook script generation."""

    def test_generate_hook_script_post_merge(self) -> None:
        """generate_hook_script() should create valid bash script."""
        # Arrange
        orchestrator = HooksOrchestrator(project_root=Path("/tmp"))

        # Act
        script = orchestrator.generate_hook_script(
            hook_type="post-merge",
            command="cortex map --output .cortex/context.json",
        )

        # Assert
        assert script.startswith("#!/bin/bash")
        # Should NOT call cortex directly, should use Python module
        assert (
            "python -m scripts.cortex.cli" in script or "scripts.cortex.cli" in script
        )

    def test_generate_hook_script_includes_comments(self) -> None:
        """generate_hook_script() should include explanatory comments."""
        # Arrange
        orchestrator = HooksOrchestrator(project_root=Path("/tmp"))

        # Act
        script = orchestrator.generate_hook_script(
            hook_type="post-checkout",
            command="echo test",
        )

        # Assert
        assert "Auto-generated" in script or "CORTEX" in script
        assert "#" in script  # Should have comments

    def test_generate_hook_script_uses_git_repo_root(self) -> None:
        """generate_hook_script() should use git rev-parse to find repo root."""
        # Arrange
        orchestrator = HooksOrchestrator(project_root=Path("/tmp"))

        # Act
        script = orchestrator.generate_hook_script(
            hook_type="post-merge",
            command="cortex map --output .cortex/context.json",
        )

        # Assert - NEW: Must use git rev-parse to be portable
        assert "git rev-parse --show-toplevel" in script
        assert "REPO_ROOT=" in script

    def test_generate_hook_script_uses_venv_python(self) -> None:
        """generate_hook_script() should use .venv/bin/python from repo."""
        # Arrange
        orchestrator = HooksOrchestrator(project_root=Path("/tmp"))

        # Act
        script = orchestrator.generate_hook_script(
            hook_type="post-checkout",
            command="cortex map --output .cortex/context.json",
        )

        # Assert - NEW: Must use venv Python instead of 'cortex' command
        assert "VENV_PYTHON=" in script
        assert ".venv/bin/python" in script
        assert '"$VENV_PYTHON"' in script

    def test_generate_hook_script_validates_venv_exists(self) -> None:
        """generate_hook_script() should check if venv exists before running."""
        # Arrange
        orchestrator = HooksOrchestrator(project_root=Path("/tmp"))

        # Act
        script = orchestrator.generate_hook_script(
            hook_type="post-rewrite",
            command="cortex map --output .cortex/context.json",
        )

        # Assert - NEW: Must validate venv exists
        assert '[ -f "$VENV_PYTHON" ]' in script or 'if [ -f "$VENV_PYTHON" ]' in script

    def test_generate_hook_script_graceful_failure(self) -> None:
        """generate_hook_script() should allow graceful failure if venv missing."""
        # Arrange
        orchestrator = HooksOrchestrator(project_root=Path("/tmp"))

        # Act
        script = orchestrator.generate_hook_script(
            hook_type="post-rewrite",
            command="missing-command",
        )

        # Assert
        # Should exit 0 (gracefully) even if venv doesn't exist
        assert "exit 0" in script


class TestInstallHook:
    """Test single hook installation."""

    def test_install_hook_creates_file(self, tmp_path: Path) -> None:
        """install_hook() should create hook file with correct content."""
        # Arrange
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        script_content = "#!/bin/bash\necho test"
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        orchestrator.install_hook("post-merge", script_content, hooks_dir)

        # Assert
        hook_file = hooks_dir / "post-merge"
        assert hook_file.exists()
        assert hook_file.read_text() == script_content

    def test_install_hook_makes_executable(self, tmp_path: Path) -> None:
        """install_hook() should make hook file executable (Unix)."""
        # Arrange
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        script_content = "#!/bin/bash\necho test"
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        orchestrator.install_hook("post-checkout", script_content, hooks_dir)

        # Assert
        hook_file = hooks_dir / "post-checkout"
        if os.name == "posix":  # Only test on Unix
            file_stat = hook_file.stat()
            # Check if file has execute permission
            assert file_stat.st_mode & stat.S_IXUSR  # Owner execute

    def test_install_hook_with_backup(self, tmp_path: Path) -> None:
        """install_hook() should backup existing hook when backup=True."""
        # Arrange
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        existing_hook = hooks_dir / "post-merge"
        existing_hook.write_text("#!/bin/bash\necho old", encoding="utf-8")

        orchestrator = HooksOrchestrator(project_root=tmp_path)
        new_content = "#!/bin/bash\necho new"

        # Act
        orchestrator.install_hook("post-merge", new_content, hooks_dir, backup=True)

        # Assert
        assert existing_hook.exists()
        assert existing_hook.read_text() == new_content
        backup_file = hooks_dir / "post-merge.backup"
        assert backup_file.exists()
        assert backup_file.read_text() == "#!/bin/bash\necho old"

    def test_install_hook_without_backup(self, tmp_path: Path) -> None:
        """install_hook() should overwrite without backup when backup=False."""
        # Arrange
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        existing_hook = hooks_dir / "post-merge"
        existing_hook.write_text("#!/bin/bash\necho old", encoding="utf-8")

        orchestrator = HooksOrchestrator(project_root=tmp_path)
        new_content = "#!/bin/bash\necho new"

        # Act
        orchestrator.install_hook("post-merge", new_content, hooks_dir, backup=False)

        # Assert
        assert existing_hook.read_text() == new_content
        assert not (hooks_dir / "post-merge.backup").exists()


class TestMakeExecutable:
    """Test making files executable."""

    def test_make_executable_sets_permissions(self, tmp_path: Path) -> None:
        """make_executable() should set 0o755 permissions on Unix."""
        # Arrange
        test_file = tmp_path / "test_script.sh"
        test_file.write_text("#!/bin/bash\necho test")
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        orchestrator.make_executable(test_file)

        # Assert
        if os.name == "posix":
            file_stat = test_file.stat()
            # Check for 0o755 (rwxr-xr-x)
            assert file_stat.st_mode & stat.S_IXUSR  # Owner execute
            assert file_stat.st_mode & stat.S_IXGRP  # Group execute
            assert file_stat.st_mode & stat.S_IXOTH  # Others execute

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_make_executable_windows_no_error(self, tmp_path: Path) -> None:
        """make_executable() should not raise error on Windows."""
        # Arrange
        test_file = tmp_path / "test_script.bat"
        test_file.write_text("@echo test")
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act & Assert - should not raise
        orchestrator.make_executable(test_file)


class TestBackupExistingHook:
    """Test hook backup functionality."""

    def test_backup_existing_hook_creates_backup(self, tmp_path: Path) -> None:
        """backup_existing_hook() should create .backup file."""
        # Arrange
        hook_file = tmp_path / "post-merge"
        hook_file.write_text("#!/bin/bash\necho original", encoding="utf-8")
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        backup_path = orchestrator.backup_existing_hook(hook_file)

        # Assert
        assert backup_path.exists()
        assert backup_path.name == "post-merge.backup"
        assert backup_path.read_text() == "#!/bin/bash\necho original"
        assert not hook_file.exists()  # Original moved

    def test_backup_existing_hook_custom_suffix(self, tmp_path: Path) -> None:
        """backup_existing_hook() should use custom suffix."""
        # Arrange
        hook_file = tmp_path / "post-checkout"
        hook_file.write_text("#!/bin/bash\necho test", encoding="utf-8")
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        backup_path = orchestrator.backup_existing_hook(hook_file, suffix=".old")

        # Assert
        assert backup_path.name == "post-checkout.old"
        assert backup_path.exists()

    def test_backup_existing_hook_file_not_found(self, tmp_path: Path) -> None:
        """backup_existing_hook() should raise error if file doesn't exist."""
        # Arrange
        hook_file = tmp_path / "nonexistent"
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act & Assert
        with pytest.raises(HookInstallationError):
            orchestrator.backup_existing_hook(hook_file)


class TestInstallCortexHooks:
    """Test installation of all CORTEX hooks."""

    def test_install_cortex_hooks_creates_all_hooks(self, tmp_path: Path) -> None:
        """install_cortex_hooks() installs all CORTEX hooks."""
        # Arrange
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        installed = orchestrator.install_cortex_hooks()

        # Assert
        assert "post-merge" in installed
        assert "post-checkout" in installed
        assert "post-rewrite" in installed
        assert len(installed) == 3

        # Verify files exist
        hooks_dir = git_dir / "hooks"
        assert (hooks_dir / "post-merge").exists()
        assert (hooks_dir / "post-checkout").exists()
        assert (hooks_dir / "post-rewrite").exists()

    def test_install_cortex_hooks_creates_hooks_directory(self, tmp_path: Path) -> None:
        """install_cortex_hooks() should create hooks directory if missing."""
        # Arrange
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        # Don't create hooks directory
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        orchestrator.install_cortex_hooks()

        # Assert
        hooks_dir = git_dir / "hooks"
        assert hooks_dir.exists()
        assert hooks_dir.is_dir()

    def test_install_cortex_hooks_no_git_directory(self, tmp_path: Path) -> None:
        """install_cortex_hooks() should raise error when .git missing."""
        # Arrange
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act & Assert
        with pytest.raises(GitDirectoryNotFoundError):
            orchestrator.install_cortex_hooks()

    def test_install_cortex_hooks_all_executable(self, tmp_path: Path) -> None:
        """install_cortex_hooks() should make all hooks executable."""
        # Arrange
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        orchestrator.install_cortex_hooks()

        # Assert
        if os.name == "posix":
            hooks_dir = git_dir / "hooks"
            for hook_name in ["post-merge", "post-checkout", "post-rewrite"]:
                hook_file = hooks_dir / hook_name
                file_stat = hook_file.stat()
                assert file_stat.st_mode & stat.S_IXUSR  # Executable


class TestEnsureHooksDirectory:
    """Test hooks directory creation."""

    def test_ensure_hooks_directory_creates_if_missing(self, tmp_path: Path) -> None:
        """_ensure_hooks_directory() should create hooks directory."""
        # Arrange
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        hooks_dir = orchestrator._ensure_hooks_directory(git_dir)

        # Assert
        assert hooks_dir.exists()
        assert hooks_dir.is_dir()
        assert hooks_dir == git_dir / "hooks"

    def test_ensure_hooks_directory_idempotent(self, tmp_path: Path) -> None:
        """_ensure_hooks_directory() should be idempotent."""
        # Arrange
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()  # Pre-create
        orchestrator = HooksOrchestrator(project_root=tmp_path)

        # Act
        result = orchestrator._ensure_hooks_directory(git_dir)

        # Assert
        assert result == hooks_dir
        assert result.exists()
