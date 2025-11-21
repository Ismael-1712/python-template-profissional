#!/usr/bin/env python3
"""Test Suite for Smart Git Synchronization System.

Comprehensive test suite to validate the Smart Git Sync functionality
in various scenarios and edge cases.

Usage:
    python3 scripts/test_smart_git_sync.py
    python3 scripts/test_smart_git_sync.py --verbose
    python3 scripts/test_smart_git_sync.py --unit-tests-only
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

# Adiciona a raiz do projeto ao sys.path
PROJECT_ROOT = Path(__file__).parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the module under test from git_sync package
# isort: off
from scripts.git_sync.config import load_config  # noqa: E402
from scripts.git_sync.exceptions import AuditError, GitOperationError, SyncError  # noqa: E402
from scripts.git_sync.models import SyncStep  # noqa: E402
from scripts.git_sync.sync_logic import SyncOrchestrator  # noqa: E402
# isort: on


class TestSyncStep(unittest.TestCase):
    """Test cases for SyncStep class."""

    def test_sync_step_initialization(self) -> None:
        """Test SyncStep initialization."""
        step = SyncStep("test_step", "Test step description")
        self.assertEqual(step.name, "test_step")
        self.assertEqual(step.description, "Test step description")
        self.assertEqual(step.status, "pending")
        self.assertIsNone(step.start_time)
        self.assertIsNone(step.end_time)
        self.assertIsNone(step.error)
        self.assertEqual(step.details, {})

    def test_sync_step_start(self) -> None:
        """Test SyncStep start method."""
        step = SyncStep("test_step", "Test step description")
        step.start()
        self.assertEqual(step.status, "running")
        self.assertIsNotNone(step.start_time)

    def test_sync_step_complete(self) -> None:
        """Test SyncStep complete method."""
        step = SyncStep("test_step", "Test step description")
        step.start()
        step.complete({"result": "success"})

        self.assertEqual(step.status, "success")
        self.assertIsNotNone(step.end_time)
        self.assertEqual(step.details["result"], "success")

    def test_sync_step_fail(self) -> None:
        """Test SyncStep fail method."""
        step = SyncStep("test_step", "Test step description")
        step.start()
        step.fail("Test error", {"error_code": 500})

        self.assertEqual(step.status, "failed")
        self.assertEqual(step.error, "Test error")
        self.assertEqual(step.details["error_code"], 500)

    def test_sync_step_to_dict(self) -> None:
        """Test SyncStep to_dict serialization."""
        step = SyncStep("test_step", "Test step description")
        step.start()
        step.complete({"result": "success"})

        result_dict = step.to_dict()
        self.assertEqual(result_dict["name"], "test_step")
        self.assertEqual(result_dict["status"], "success")
        self.assertIn("start_time", result_dict)
        self.assertIn("end_time", result_dict)


class TestConfigLoading(unittest.TestCase):
    """Test cases for configuration loading."""

    def test_load_default_config(self) -> None:
        """Test loading default configuration."""
        config = load_config()

        # Check that default values are present
        self.assertTrue(config["audit_enabled"])
        self.assertEqual(config["audit_timeout"], 300)
        self.assertEqual(config["audit_fail_threshold"], "HIGH")
        self.assertTrue(config["strict_audit"])

    def test_load_config_from_file(self) -> None:
        """Test loading configuration from YAML file."""
        test_config = {
            "audit_enabled": False,
            "audit_timeout": 600,
            "custom_setting": "test_value",
        }

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False,
        ) as f:
            yaml.dump(test_config, f)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)

            # Check that custom values override defaults
            self.assertFalse(config["audit_enabled"])
            self.assertEqual(config["audit_timeout"], 600)
            self.assertEqual(config["custom_setting"], "test_value")

            # Check that unspecified defaults are still present
            self.assertEqual(config["audit_fail_threshold"], "HIGH")

        finally:
            config_path.unlink()  # Clean up

    def test_load_config_nonexistent_file(self) -> None:
        """Test loading configuration with non-existent file."""
        nonexistent_path = Path("/nonexistent/config.yaml")
        config = load_config(nonexistent_path)

        # Should return default config
        self.assertTrue(config["audit_enabled"])


class TestSyncOrchestrator(unittest.TestCase):
    """Test cases for SyncOrchestrator class."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.git_dir = self.temp_dir / ".git"
        self.git_dir.mkdir()

        self.config = {
            "audit_enabled": True,
            "strict_audit": True,
            "auto_fix_enabled": True,
            "cleanup_enabled": False,  # Disable for testing
        }

    def tearDown(self) -> None:
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_sync_orchestrator_initialization(self) -> None:
        """Test SyncOrchestrator initialization."""
        sync = SyncOrchestrator(
            workspace_root=self.temp_dir,
            config=self.config,
            dry_run=True,
        )

        self.assertEqual(sync.workspace_root, self.temp_dir)
        self.assertEqual(sync.config, self.config)
        self.assertTrue(sync.dry_run)
        self.assertEqual(len(sync.steps), 0)

    def test_validate_git_repository_success(self) -> None:
        """Test Git repository validation success."""
        # Should not raise an exception
        SyncOrchestrator(
            workspace_root=self.temp_dir,
            config=self.config,
            dry_run=True,
        )

    def test_validate_git_repository_failure(self) -> None:
        """Test Git repository validation failure."""
        # Remove .git directory
        self.git_dir.rmdir()

        with self.assertRaises(SyncError):
            SyncOrchestrator(
                workspace_root=self.temp_dir,
                config=self.config,
                dry_run=True,
            )

    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_run_command_dry_run(self, mock_run: MagicMock) -> None:
        """Test command execution in dry run mode."""
        sync = SyncOrchestrator(
            workspace_root=self.temp_dir,
            config=self.config,
            dry_run=True,
        )

        result = sync._run_command(["git", "status"])

        # Should not actually execute command
        mock_run.assert_not_called()
        self.assertEqual(result.stdout, "[DRY RUN]")
        self.assertEqual(result.returncode, 0)

    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_run_command_success(self, mock_run: MagicMock) -> None:
        """Test successful command execution."""
        # Mock successful subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        sync = SyncOrchestrator(
            workspace_root=self.temp_dir,
            config=self.config,
            dry_run=False,
        )

        result = sync._run_command(["git", "status"])

        mock_run.assert_called_once()
        self.assertEqual(result.stdout, "test output")
        self.assertEqual(result.returncode, 0)

    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_run_command_failure(self, mock_run: MagicMock) -> None:
        """Test command execution failure."""
        # Mock failed subprocess execution
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(
            returncode=1,
            cmd=["git", "status"],
            stderr="error message",
        )

        sync = SyncOrchestrator(
            workspace_root=self.temp_dir,
            config=self.config,
            dry_run=False,
        )

        with self.assertRaises(GitOperationError):
            sync._run_command(["git", "status"])


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling and edge cases."""

    def test_sync_error_inheritance(self) -> None:
        """Test that custom exceptions inherit correctly."""
        self.assertTrue(issubclass(GitOperationError, SyncError))
        self.assertTrue(issubclass(AuditError, SyncError))
        self.assertTrue(issubclass(SyncError, Exception))

    def test_sync_error_messages(self) -> None:
        """Test that error messages are handled correctly."""
        error = SyncError("Test sync error")
        self.assertEqual(str(error), "Test sync error")

        git_error = GitOperationError("Git operation failed")
        self.assertEqual(str(git_error), "Git operation failed")

        audit_error = AuditError("Audit check failed")
        self.assertEqual(str(audit_error), "Audit check failed")


class TestIntegration(unittest.TestCase):
    """Integration test cases."""

    def test_config_yaml_format(self) -> None:
        """Test that the config YAML file is properly formatted."""
        config_path = Path(__file__).parent / "smart_git_sync_config.yaml"

        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Validate required keys are present
            required_keys = [
                "audit_enabled",
                "audit_timeout",
                "audit_fail_threshold",
                "auto_fix_enabled",
            ]

            for key in required_keys:
                self.assertIn(key, config, f"Missing required config key: {key}")
        else:
            self.skipTest("Config file not found")

    def test_script_executable(self) -> None:
        """Test that the main script is executable."""
        script_path = Path(__file__).parent / "smart_git_sync.py"

        if script_path.exists():
            with open(script_path, encoding="utf-8") as f:
                first_line = f.readline().strip()

            self.assertTrue(
                first_line.startswith("#!"),
                "Script should have shebang line",
            )

            # Check that the file has execution permissions
            # (This is platform-dependent, so we just check the shebang)
            self.assertIn("python", first_line.lower())
        else:
            self.skipTest("Main script not found")


def run_security_checks() -> None:
    """Run basic security checks on the codebase."""
    print("\n🔒 Running Security Checks...")

    script_path = Path(__file__).parent / "smart_git_sync.py"

    if not script_path.exists():
        print("❌ Main script not found")
        return

    with open(script_path, encoding="utf-8") as f:
        content = f.read()

    # Check for security anti-patterns
    security_issues = []

    if "shell=True" in content:
        security_issues.append("⚠️  Found shell=True - security risk")

    if "os.system(" in content:
        security_issues.append("⚠️  Found os.system() - security risk")

    if "eval(" in content:
        security_issues.append("⚠️  Found eval() - security risk")

    if "exec(" in content:
        security_issues.append("⚠️  Found exec() - security risk")

    if security_issues:
        print("Security issues found:")
        for issue in security_issues:
            print(f"  {issue}")
    else:
        print("✅ No obvious security issues found")


def run_code_quality_checks() -> None:
    """Run basic code quality checks."""
    print("\n📊 Running Code Quality Checks...")

    script_path = Path(__file__).parent / "smart_git_sync.py"

    if not script_path.exists():
        print("❌ Main script not found")
        return

    with open(script_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Basic quality metrics
    total_lines = len(lines)
    code_lines = len(
        [line for line in lines if line.strip() and not line.strip().startswith("#")],
    )
    comment_lines = len([line for line in lines if line.strip().startswith("#")])

    print(f"📈 Total lines: {total_lines}")
    print(f"📝 Code lines: {code_lines}")
    print(f"💬 Comment lines: {comment_lines}")

    if comment_lines > 0:
        comment_ratio = comment_lines / total_lines * 100
        print(f"📊 Comment ratio: {comment_ratio:.1f}%")

        if comment_ratio >= 15:
            print("✅ Good documentation coverage")
        else:
            print("⚠️  Consider adding more documentation")


def main() -> None:
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Smart Git Sync Test Suite")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose test output",
    )
    parser.add_argument(
        "--unit-tests-only",
        action="store_true",
        help="Run only unit tests, skip security/quality checks",
    )

    args = parser.parse_args()

    print("🧪 Smart Git Sync Test Suite")
    print("=" * 40)

    # Configure test verbosity
    verbosity = 2 if args.verbose else 1

    # Run unit tests
    print("\n🔍 Running Unit Tests...")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Run additional checks
    if not args.unit_tests_only:
        run_security_checks()
        run_code_quality_checks()

    # Summary
    print("\n" + "=" * 40)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        exit_code = 0
    else:
        print(
            f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)",
        )
        exit_code = 1

    print(f"📊 Ran {result.testsRun} test(s)")

    import sys

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
