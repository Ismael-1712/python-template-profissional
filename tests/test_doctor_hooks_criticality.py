#!/usr/bin/env python3
"""TDD Test: Verify doctor.py treats missing hooks as CRITICAL error.

This test implements the RED STAGE of TDD for Task [005]:
- Tests that check_git_hooks() returns critical=True when hooks are missing
- Currently EXPECTED TO FAIL (critical=False in current implementation)

After implementing the fix, this test should PASS.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.cli.doctor import DevDoctor, DiagnosticResult


class TestDoctorHooksCriticality:
    """Test suite for Git hooks criticality in dev-doctor diagnostics."""

    @patch.dict(os.environ, {}, clear=True)  # Ensure not in CI
    def test_missing_hooks_must_be_critical_error(self, tmp_path: Path) -> None:
        """CRITICAL: Missing Git hooks MUST be treated as critical failure.

        Security Rationale:
            A development environment without Git hooks is INSECURE.
            Developers can commit code bypassing:
            - Code quality checks (ruff, mypy)
            - Security audits
            - Documentation validation
            - CORTEX Guardian (shadow config detection)

            Therefore, dev-doctor MUST return critical=True to BLOCK
            developers from proceeding until hooks are installed.

        Expected Behavior:
            When .git/hooks/pre-commit does NOT exist:
                result.critical == True

        Current State (Red Stage):
            ❌ This test WILL FAIL because current code returns critical=False
               (see scripts/cli/doctor.py line 354)

        After Fix (Green Stage):
            ✅ This test will PASS when critical=True is implemented.
        """
        # Arrange: Create fake project structure WITHOUT git hooks
        fake_project_root = tmp_path / "project"
        fake_project_root.mkdir()

        # Create .git directory but WITHOUT hooks
        git_dir = fake_project_root / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        # Explicitly do NOT create pre-commit file

        # Create DevDoctor instance
        doctor = DevDoctor(fake_project_root)

        # Act: Check git hooks status
        result = doctor.check_git_hooks()

        # Assert: Verify result structure
        assert isinstance(result, DiagnosticResult), (
            "check_git_hooks() should return DiagnosticResult"
        )
        assert result.name == "Git Hooks", (
            f"Expected name 'Git Hooks', got {result.name}"
        )
        assert result.passed is False, (
            "Missing hooks should result in failed diagnostic"
        )

        # 🔴 CRITICAL ASSERTION (Red Stage - Expected to FAIL):
        assert result.critical is True, (
            "🚨 SECURITY VULNERABILITY: Missing Git hooks MUST be treated "
            "as CRITICAL error!\n"
            f"Expected: critical=True\n"
            f"Actual: critical={result.critical}\n"
            f"Message: {result.message}\n\n"
            "Without this enforcement, developers can work in INSECURE "
            "environments where commits bypass all quality gates. "
            "This creates a compliance gap and allows low-quality/insecure "
            "code to enter the repository.\n\n"
            "Fix required in: scripts/cli/doctor.py:354\n"
            "Change: critical=False → critical=True"
        )

        # Verify prescriptive message is present
        assert "pre-commit install" in result.message, (
            "Diagnostic should suggest 'pre-commit install' as remedy"
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_hooks_installed_but_not_executable_is_critical(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify that non-executable hooks are also treated as critical.

        Edge Case:
            If .git/hooks/pre-commit exists but is NOT executable (chmod -x),
            commits will silently bypass hooks without error.

        Expected Behavior:
            result.critical == True (already implemented correctly)

        Current State:
            ✅ This test SHOULD PASS (already returns critical=True for this case)
        """
        # Arrange: Create pre-commit file WITHOUT execute permission
        fake_project_root = tmp_path / "project"
        fake_project_root.mkdir()
        git_dir = fake_project_root / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        pre_commit_hook = hooks_dir / "pre-commit"
        pre_commit_hook.write_text("#!/bin/sh\necho 'hook'")
        pre_commit_hook.chmod(0o644)  # Readable but NOT executable

        doctor = DevDoctor(fake_project_root)

        # Act
        result = doctor.check_git_hooks()

        # Assert
        assert result.passed is False, "Non-executable hook should fail diagnostic"
        assert result.critical is True, (
            "Non-executable hook MUST be critical error "
            "(this is already correctly implemented)"
        )
        assert (
            "não é executável" in result.message or "not executable" in result.message
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_hooks_installed_and_executable_passes(self, tmp_path: Path) -> None:
        """Verify that properly installed hooks pass the diagnostic.

        Happy Path:
            When .git/hooks/pre-commit exists AND is executable,
            the diagnostic should pass.

        Expected Behavior:
            result.passed == True
            result.critical == (any value, not checked when passed=True)
        """
        # Arrange: Create executable pre-commit hook
        fake_project_root = tmp_path / "project"
        fake_project_root.mkdir()
        git_dir = fake_project_root / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        pre_commit_hook = hooks_dir / "pre-commit"
        pre_commit_hook.write_text("#!/bin/sh\necho 'hook'")
        pre_commit_hook.chmod(0o755)  # Executable

        doctor = DevDoctor(fake_project_root)

        # Act
        result = doctor.check_git_hooks()

        # Assert
        assert result.passed is True, "Properly installed hooks should pass diagnostic"
        assert (
            "instalados e executáveis" in result.message
            or "installed and executable" in result.message
        )

    @patch.dict(os.environ, {"CI": "true"}, clear=False)
    def test_ci_environment_skips_hooks_check(self, tmp_path: Path) -> None:
        """Verify that CI environment skips hooks check (by design).

        CI Rationale:
            In CI/CD pipelines (GitHub Actions), Git hooks are not needed
            because validation is enforced by the pipeline itself.

        Expected Behavior:
            When CI=true, return passed=True with skip message.

        Current State:
            ✅ This test SHOULD PASS (already implemented correctly)
        """
        # Arrange: Create project WITHOUT hooks (should be skipped in CI)
        fake_project_root = tmp_path / "project"
        fake_project_root.mkdir()

        doctor = DevDoctor(fake_project_root)

        # Act
        result = doctor.check_git_hooks()

        # Assert
        assert result.passed is True, "CI should skip hooks check"
        assert "CI" in result.message, "Message should indicate CI skip"

    def test_missing_git_directory_fails_gracefully(self, tmp_path: Path) -> None:
        """Verify that missing .git directory is handled gracefully.

        Edge Case:
            If .git/ doesn't exist (not a git repo), the check should
            fail but not crash.

        Expected Behavior:
            result.passed == False
            result.critical == True (after fix)

        Current State (Red Stage):
            ❌ Will FAIL on critical=True assertion (returns False currently)
        """
        # Arrange: Create project WITHOUT .git directory
        fake_project_root = tmp_path / "project"
        fake_project_root.mkdir()
        # Do NOT create .git/

        doctor = DevDoctor(fake_project_root)

        # Act
        result = doctor.check_git_hooks()

        # Assert
        assert isinstance(result, DiagnosticResult), "Should return DiagnosticResult"
        assert result.passed is False, ".git missing should fail diagnostic"

        # 🔴 CRITICAL ASSERTION (Red Stage - Expected to FAIL):
        assert result.critical is True, (
            "Missing .git directory means hooks CAN'T be installed - "
            "this is a CRITICAL environment issue!"
        )


class TestDoctorIntegrationWithRunDiagnostics:
    """Integration tests for DevDoctor.run_diagnostics() workflow."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("scripts.cli.doctor.print")  # Suppress output
    def test_run_diagnostics_fails_when_hooks_missing(
        self,
        mock_print: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Verify that run_diagnostics() returns False when hooks are missing.

        Integration Test:
            run_diagnostics() aggregates all checks. If hooks are missing
            AND marked as critical, the overall result MUST be False.

        Expected Behavior:
            DevDoctor.run_diagnostics() -> False (critical failures detected)

        Current State (Red Stage):
            ⚠️ This test behavior depends on critical=True fix.
               Currently returns True (warning only) - INCORRECT.

        After Fix (Green Stage):
            ✅ Will return False (critical failure detected)
        """
        # Arrange: Create minimal project WITHOUT hooks
        fake_project_root = tmp_path / "project"
        fake_project_root.mkdir()
        git_dir = fake_project_root / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        # No pre-commit file

        # Create minimal .python-version to pass version check
        python_version_file = fake_project_root / ".python-version"
        python_version_file.write_text("3.10.0")

        doctor = DevDoctor(fake_project_root)

        # Mock other checks to pass (focus on hooks check)
        with (
            patch.object(
                doctor,
                "check_platform",
                return_value=DiagnosticResult("Platform", True, "OK"),
            ),
            patch.object(
                doctor,
                "check_python_version",
                return_value=DiagnosticResult("Python", True, "OK"),
            ),
            patch.object(
                doctor,
                "check_virtual_environment",
                return_value=DiagnosticResult("Venv", True, "OK"),
            ),
            patch.object(
                doctor,
                "check_tool_paths",
                return_value=DiagnosticResult("Tools", True, "OK"),
            ),
            patch.object(
                doctor,
                "check_vital_dependencies",
                return_value=DiagnosticResult("Deps", True, "OK"),
            ),
        ):
            # Act
            success = doctor.run_diagnostics()

        # Assert
        # 🔴 INTEGRATION ASSERTION (Red Stage - Expected to FAIL):
        assert success is False, (
            "run_diagnostics() MUST return False when critical checks fail.\n"
            "Missing Git hooks is a CRITICAL security issue that should "
            "block development.\n"
            f"Current result: {success}\n"
            "This indicates the environment is INSECURE and should not be used."
        )


if __name__ == "__main__":
    # Run tests with verbose output to show Red Stage failures
    pytest.main([__file__, "-v", "--tb=short", "-x"])
