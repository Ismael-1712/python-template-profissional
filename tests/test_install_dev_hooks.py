#!/usr/bin/env python3
"""TDD Test: Verify install_dev.py installs Git hooks automatically.

This test implements the RED STAGE of TDD for Task [005]:
- Tests that install_dev_environment() calls 'pre-commit install'
- Currently EXPECTED TO FAIL (pre-commit install is not executed)

After implementing the fix, this test should PASS.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from scripts.cli.install_dev import install_dev_environment


class TestInstallDevHooksIntegrity:
    """Test suite for Git hooks installation during dev environment setup."""

    @patch("scripts.cli.install_dev.subprocess.run")
    @patch("scripts.cli.install_dev._setup_direnv")
    @patch("scripts.cli.install_dev._display_success_panel")
    @patch("scripts.cli.install_dev._cleanup_backup")
    @patch("scripts.cli.install_dev._create_backup")
    @patch("scripts.cli.install_dev.shutil.which")
    @patch("scripts.cli.install_dev.safe_pip_compile")
    def test_install_dev_must_install_git_hooks(
        self,
        mock_safe_pip: MagicMock,
        mock_which: MagicMock,
        mock_create_backup: MagicMock,
        mock_cleanup_backup: MagicMock,
        mock_display_panel: MagicMock,
        mock_setup_direnv: MagicMock,
        mock_subprocess_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """CRITICAL: Verify that pre-commit hooks are installed automatically.

        Security Rationale:
            A developer who runs 'make install-dev' MUST have Git hooks active.
            Without this enforcement, developers can commit code bypassing all
            quality gates (ruff, mypy, security audit, CORTEX guardian).

        Expected Behavior:
            install_dev_environment() MUST execute pre-commit installation
            via subprocess with: ["pre-commit", "install", "--install-hooks"]

        Current State (Red Stage):
            ❌ This test WILL FAIL because the code doesn't install hooks yet.

        After Fix (Green Stage):
            ✅ This test will PASS when implementation is added.
        """
        # Arrange: Setup mocks for successful installation
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        (workspace_root / "requirements").mkdir()

        mock_which.return_value = str(workspace_root / "bin" / "pip-compile")
        mock_create_backup.return_value = None

        # Mock subprocess.run to return success for all commands
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        # Mock safe_pip_compile
        mock_safe_pip.return_value = mock_result

        # Act: Execute the installation function
        exit_code = install_dev_environment(workspace_root)

        # Assert: Verify exit code is success
        assert exit_code == 0, "Installation should complete successfully"

        # 🔴 CRITICAL ASSERTION (Red Stage - Expected to FAIL):
        # Verify that 'pre-commit install' was called
        pre_commit_install_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if len(c[0]) > 0
            and isinstance(c[0][0], list)
            and "pre-commit" in c[0][0]
            and "install" in c[0][0]
        ]

        assert len(pre_commit_install_calls) >= 1, (
            "🚨 SECURITY VULNERABILITY: install_dev_environment() MUST call "
            "'pre-commit install' to ensure Git hooks are active. "
            "Without this, developers can bypass all quality gates!\n"
            f"Actual calls: {[str(c) for c in mock_subprocess_run.call_args_list]}"
        )

    @patch("scripts.cli.install_dev.subprocess.run")
    @patch("scripts.cli.install_dev._setup_direnv")
    @patch("scripts.cli.install_dev._display_success_panel")
    @patch("scripts.cli.install_dev._cleanup_backup")
    @patch("scripts.cli.install_dev._create_backup")
    @patch("scripts.cli.install_dev.shutil.which")
    @patch("scripts.cli.install_dev.safe_pip_compile")
    def test_hooks_installation_with_flag_install_hooks(
        self,
        mock_safe_pip: MagicMock,
        mock_which: MagicMock,
        mock_create_backup: MagicMock,
        mock_cleanup_backup: MagicMock,
        mock_display_panel: MagicMock,
        mock_setup_direnv: MagicMock,
        mock_subprocess_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Verify that pre-commit install uses --install-hooks flag.

        Best Practice:
            Using 'pre-commit install --install-hooks' ensures that the
            hook environments are created immediately, not on first run.
            This prevents CI failures due to missing hook dependencies.

        Expected Command:
            ['pre-commit', 'install', '--install-hooks']

        Current State (Red Stage):
            ❌ This test WILL FAIL (hooks not installed at all).
        """
        # Arrange
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        (workspace_root / "requirements").mkdir()

        mock_which.return_value = str(workspace_root / "bin" / "pip-compile")
        mock_create_backup.return_value = None

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result
        mock_safe_pip.return_value = mock_result

        # Act
        exit_code = install_dev_environment(workspace_root)

        # Assert
        assert exit_code == 0

        # 🔴 BEST PRACTICE ASSERTION (Red Stage - Expected to FAIL):
        # Check if --install-hooks flag is used
        has_install_hooks_flag = any(
            "pre-commit" in str(call_obj)
            and "install" in str(call_obj)
            and "--install-hooks" in str(call_obj)
            for call_obj in mock_subprocess_run.call_args_list
        )

        assert has_install_hooks_flag, (
            "Best Practice: Use 'pre-commit install --install-hooks' "
            "to create hook environments immediately.\n"
            f"Actual calls: {mock_subprocess_run.call_args_list}"
        )

    @patch("scripts.cli.install_dev.subprocess.run")
    @patch("scripts.cli.install_dev._setup_direnv")
    @patch("scripts.cli.install_dev._display_success_panel")
    @patch("scripts.cli.install_dev._cleanup_backup")
    @patch("scripts.cli.install_dev._create_backup")
    @patch("scripts.cli.install_dev.shutil.which")
    @patch("scripts.cli.install_dev.safe_pip_compile")
    def test_hooks_installation_failure_should_warn_not_block(
        self,
        mock_safe_pip: MagicMock,
        mock_which: MagicMock,
        mock_create_backup: MagicMock,
        mock_cleanup_backup: MagicMock,
        mock_display_panel: MagicMock,
        mock_setup_direnv: MagicMock,
        mock_subprocess_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Verify that hooks installation failure logs warning but continues.

        Design Decision:
            If 'pre-commit install' fails (e.g., .git not initialized),
            the installation should WARN but NOT FAIL completely.
            This prevents breaking dev setup in edge cases.

        Expected Behavior:
            - Log critical warning about missing hooks
            - Return exit code 0 (success with warning)

        Current State (Red Stage):
            ❌ This test WILL FAIL (hooks installation not attempted).
        """
        # Arrange
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        (workspace_root / "requirements").mkdir()

        mock_which.return_value = str(workspace_root / "bin" / "pip-compile")
        mock_create_backup.return_value = None

        def subprocess_side_effect(*args: Any, **kwargs: Any) -> MagicMock:  # noqa: S603
            """Simulate success for pip, failure for pre-commit."""
            cmd = args[0] if args else kwargs.get("args", [])
            if "pre-commit" in cmd:
                # Simulate pre-commit install failure
                err = subprocess.CalledProcessError(1, cmd, stderr="Git not found")  # noqa: S603
                raise err  # noqa: TRY301
            # Success for other commands
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Success"
            mock_result.stderr = ""
            return mock_result

        mock_subprocess_run.side_effect = subprocess_side_effect

        # Mock safe_pip_compile to succeed
        mock_result = MagicMock()
        mock_result.stdout = "Compiled"
        mock_safe_pip.return_value = mock_result

        # Act
        exit_code = install_dev_environment(workspace_root)

        # Assert: Should succeed despite hooks failure
        # (This part will fail too because hooks aren't even attempted)
        assert exit_code == 0, (
            "Installation should succeed with warning when hooks fail"
        )


if __name__ == "__main__":
    # Run tests with verbose output to show Red Stage failures
    pytest.main([__file__, "-v", "--tb=short"])
