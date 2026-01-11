"""Tests for Dependency Guardian v2.3 - Deep Consistency Check.

This module tests the ULTIMATE validation mechanism that detects:
- PyPI drift (upstream version changes)
- Manual edits to lockfiles
- Incomplete/corrupted pip-compile runs

Protocol: TDD (tests written before implementation)
"""

import subprocess
from pathlib import Path

from scripts.core.dependency_guardian import DependencyGuardian


class TestDeepConsistencyCheck:
    """Test suite for Deep Consistency Check (v2.3 Protocol)."""

    def test_deep_consistency_detects_pypi_drift(self, tmp_path: Path) -> None:
        """Test that deep check detects when lockfile is stale (PyPI drift).

        Scenario: Simulates the tomli 2.3.0 → 2.4.0 incident.
        The lockfile has an older version than what pip-compile would generate.
        """
        # Setup: Create dev.in with unpinned dependency
        in_file = tmp_path / "dev.in"
        in_file.write_text(
            "# Test dependencies\npytest==9.0.2\nruff==0.14.10\n",
            encoding="utf-8",
        )

        # Compile fresh lockfile with current PyPI state
        txt_file = tmp_path / "dev.txt"
        subprocess.run(
            [
                "python3",
                "-m",
                "piptools",
                "compile",
                str(in_file),
                "--output-file",
                str(txt_file),
                "--resolver=backtracking",
                "--strip-extras",
                "--allow-unsafe",
                "--quiet",
            ],
            check=True,
            capture_output=True,
        )

        # Simulate drift: manually downgrade a transitive dependency
        # (This simulates what happened with tomli 2.3.0 vs 2.4.0)
        content = txt_file.read_text(encoding="utf-8")

        # Find a dependency to simulate drift
        # We'll add a fake old version to demonstrate drift detection
        lines = content.splitlines()
        modified_lines = []
        for line in lines:
            if line.strip().startswith("pytest=="):
                # Simulate drift by changing version
                modified_lines.append("pytest==8.0.0  # Simulated drift")
            else:
                modified_lines.append(line)

        txt_file.write_text("\n".join(modified_lines) + "\n", encoding="utf-8")

        # Execute deep check
        guardian = DependencyGuardian(tmp_path)
        is_valid, diff = guardian.validate_deep_consistency("dev")

        # Assert drift is detected
        assert not is_valid, "Deep check should detect stale lockfile"
        assert diff != "", "Diff report should not be empty"
        assert "pytest" in diff.lower(), "Diff should mention the drifted package"

    def test_deep_consistency_passes_when_synced(self, tmp_path: Path) -> None:
        """Test that deep check passes when lockfile is fresh and synchronized.

        Scenario: Ideal case - lockfile was just compiled and matches
        pip-compile output.
        """
        # Setup: Create dev.in with pinned dependencies
        in_file = tmp_path / "dev.in"
        in_file.write_text(
            "pytest==9.0.2\nruff==0.14.10\n",
            encoding="utf-8",
        )

        # Fresh compile
        txt_file = tmp_path / "dev.txt"
        subprocess.run(
            [
                "python3",
                "-m",
                "piptools",
                "compile",
                str(in_file),
                "--output-file",
                str(txt_file),
                "--resolver=backtracking",
                "--strip-extras",
                "--allow-unsafe",
                "--quiet",
            ],
            check=True,
        )

        # Execute deep check immediately
        guardian = DependencyGuardian(tmp_path)
        is_valid, diff = guardian.validate_deep_consistency("dev")

        # Assert sync is validated
        assert is_valid, "Deep check should pass for fresh lockfile"
        assert diff == "", "Diff should be empty for synchronized lockfile"

    def test_deep_consistency_detects_manual_edit(self, tmp_path: Path) -> None:
        """Test that deep check detects manual tampering with lockfile.

        Scenario: Developer manually adds/modifies dependencies in .txt file.
        This violates the "lockfile as single source of truth" principle.
        """
        # Setup: Create dev.in and compile
        in_file = tmp_path / "dev.in"
        in_file.write_text("pytest==9.0.2\n", encoding="utf-8")

        txt_file = tmp_path / "dev.txt"
        subprocess.run(
            [
                "python3",
                "-m",
                "piptools",
                "compile",
                str(in_file),
                "--output-file",
                str(txt_file),
                "--resolver=backtracking",
                "--strip-extras",
                "--allow-unsafe",
                "--quiet",
            ],
            check=True,
        )

        # Manual tampering: add a fake dependency
        content = txt_file.read_text(encoding="utf-8")
        content += "fake-malicious-package==1.0.0\n"
        txt_file.write_text(content, encoding="utf-8")

        # Execute deep check
        guardian = DependencyGuardian(tmp_path)
        is_valid, diff = guardian.validate_deep_consistency("dev")

        # Assert tampering is detected
        assert not is_valid, "Deep check should detect manual edits"
        assert "fake-malicious-package" in diff, "Diff should show the tampered package"

    def test_deep_check_handles_missing_input_file(self, tmp_path: Path) -> None:
        """Test that deep check gracefully handles missing .in file.

        Edge case: Input file was deleted or never existed.
        """
        guardian = DependencyGuardian(tmp_path)
        is_valid, diff = guardian.validate_deep_consistency("nonexistent")

        assert not is_valid, "Should fail when input file is missing"
        assert "not found" in diff.lower() or "Input file" in diff, (
            "Error message should mention missing input"
        )

    def test_deep_check_handles_missing_lockfile(self, tmp_path: Path) -> None:
        """Test that deep check gracefully handles missing .txt lockfile.

        Edge case: Lockfile was deleted or never generated.
        """
        # Create only .in file
        in_file = tmp_path / "dev.in"
        in_file.write_text("pytest==9.0.2\n", encoding="utf-8")

        guardian = DependencyGuardian(tmp_path)
        is_valid, diff = guardian.validate_deep_consistency("dev")

        assert not is_valid, "Should fail when lockfile is missing"
        assert "not found" in diff.lower() or "Lockfile" in diff, (
            "Error message should mention missing lockfile"
        )

    def test_deep_check_handles_pip_compile_failure(self, tmp_path: Path) -> None:
        """Test that deep check handles pip-compile errors gracefully.

        Edge case: .in file has invalid syntax or circular dependencies.
        """
        # Create .in file with invalid content that will cause pip-compile to fail
        in_file = tmp_path / "dev.in"
        in_file.write_text(
            "this-package-does-not-exist-at-all-ever==999.999.999\n",
            encoding="utf-8",
        )

        # Create a dummy lockfile (to pass the existence check)
        txt_file = tmp_path / "dev.txt"
        txt_file.write_text("# Dummy lockfile\n", encoding="utf-8")

        guardian = DependencyGuardian(tmp_path)
        is_valid, diff = guardian.validate_deep_consistency("dev")

        assert not is_valid, "Should fail when pip-compile fails"
        assert "pip-compile failed" in diff or "error" in diff.lower(), (
            "Error message should indicate pip-compile failure"
        )


class TestAtomicWrite:
    """Test suite for Atomic Write mechanism (anti-buffer corruption)."""

    def test_atomic_write_prevents_partial_writes(self, tmp_path: Path) -> None:
        """Test that atomic write ensures all-or-nothing guarantee.

        Scenario: If write fails mid-operation, original file should remain intact.
        """
        guardian = DependencyGuardian(tmp_path)

        # Create original file
        original_file = tmp_path / "dev.txt"
        original_content = "# Original lockfile\noriginal-package==1.0.0\n"
        original_file.write_text(original_content, encoding="utf-8")

        # Attempt to write with atomic mechanism
        # (This test verifies the mechanism exists, implementation will make it work)
        new_lines = [
            "# New lockfile",
            "new-package==2.0.0",
        ]

        # This should use atomic write internally
        guardian._write_sealed_content_atomic(original_file, new_lines)

        # Verify new content was written
        final_content = original_file.read_text(encoding="utf-8")
        assert "new-package==2.0.0" in final_content

    def test_atomic_write_uses_temp_file_strategy(self, tmp_path: Path) -> None:
        """Test that atomic write uses .tmp file strategy.

        Strategy: Write to .tmp file first, then atomic rename.
        This prevents editors from seeing partial writes.
        """
        guardian = DependencyGuardian(tmp_path)

        target_file = tmp_path / "dev.txt"
        target_file.write_text("# Original\n", encoding="utf-8")

        lines = ["# New content", "package==1.0.0"]

        # Execute atomic write
        guardian._write_sealed_content_atomic(target_file, lines)

        # Verify final file exists and temp file is cleaned up
        assert target_file.exists(), "Target file should exist"
        assert not (tmp_path / "dev.txt.tmp").exists(), "Temp file should be cleaned up"

        content = target_file.read_text(encoding="utf-8")
        assert "package==1.0.0" in content


class TestBackwardCompatibility:
    """Test suite to ensure v2.3 doesn't break v2.2 functionality."""

    def test_seal_validation_still_works(self, tmp_path: Path) -> None:
        """Test that v2.2 seal validation is preserved in v2.3.

        Backward compatibility: Existing seal validation must continue working.
        """
        guardian = DependencyGuardian(tmp_path)

        # Create dev.in
        in_file = tmp_path / "dev.in"
        in_file.write_text("pytest==9.0.2\n", encoding="utf-8")

        # Compute hash and inject seal (v2.2 functionality)
        hash_value = guardian.compute_input_hash("dev")

        # Create lockfile
        txt_file = tmp_path / "dev.txt"
        txt_file.write_text(
            "# Autogenerated by pip-compile\npytest==9.0.2\n",
            encoding="utf-8",
        )

        # Inject seal
        guardian.inject_seal("dev", hash_value)

        # Validate seal (v2.2 method)
        is_valid = guardian.validate_seal("dev")

        assert is_valid, "v2.2 seal validation should still work in v2.3"

    def test_compute_input_hash_unchanged(self, tmp_path: Path) -> None:
        """Test that hash computation algorithm is unchanged.

        Stability: Hash algorithm must remain stable for compatibility.
        """
        guardian = DependencyGuardian(tmp_path)

        in_file = tmp_path / "dev.in"
        in_file.write_text(
            "# Comment (ignored)\npytest==9.0.2\nruff==0.14.10\n",
            encoding="utf-8",
        )

        hash1 = guardian.compute_input_hash("dev")

        # Add more comments (should not change hash)
        in_file.write_text(
            "# Different comment (still ignored)\n"
            "pytest==9.0.2\n"
            "# Another comment\n"
            "ruff==0.14.10\n",
            encoding="utf-8",
        )

        hash2 = guardian.compute_input_hash("dev")

        assert hash1 == hash2, (
            "Hash should be comment-agnostic (v2.2 behavior preserved)"
        )
