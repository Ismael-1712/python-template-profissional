#!/usr/bin/env python3
"""CI/CD Failure Recovery System - Professional Template

A robust, secure, and portable system for automatic CI/CD failure recovery.
Follows industry best practices for DevOps automation.

Usage:
    python scripts/ci_failure_recovery.py [--commit HASH] [--dry-run]

Environment Variables:
    CI_RECOVERY_DRY_RUN: Set to 'true' for dry-run mode
    CI_RECOVERY_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR)
"""

import json
import logging
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.ci_recovery.models import (
    FileRiskAnalysis,
    RecoveryReport,
    RecoveryStatus,
    RecoveryStep,
    RiskLevel,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ci_recovery.log"),
    ],
)
logger = logging.getLogger(__name__)


class CIFailureRecoverySystem:
    """Professional CI/CD failure recovery system.

    Implements industry best practices:
    - Idempotent operations
    - Secure subprocess execution
    - Structured logging
    - Comprehensive error handling
    - Portable POSIX compliance
    """

    def __init__(
        self,
        repository_path: Path | None = None,
        commit_hash: str | None = None,
        dry_run: bool = False,
    ) -> None:
        """Initialize the recovery system.

        Args:
            repository_path: Path to git repository (defaults to current directory)
            commit_hash: Specific commit to analyze (defaults to HEAD)
            dry_run: If True, only simulate operations without making changes

        """
        self.repository_path = repository_path or Path.cwd()
        self.commit_hash = commit_hash
        self.dry_run = dry_run
        self.report = RecoveryReport(
            timestamp=datetime.now(timezone.utc),
            commit_hash="",
            repository_path=self.repository_path,
        )

        # Validate repository
        if not self._is_git_repository():
            raise ValueError(f"Not a git repository: {self.repository_path}")

        # Get actual commit hash
        self.commit_hash = self.commit_hash or self._get_current_commit_hash()
        self.report.commit_hash = self.commit_hash

        logger.info(
            f"Initialized CI Recovery System - Repository: {self.repository_path}, "
            f"Commit: {self.commit_hash}, Dry Run: {self.dry_run}",
        )

    def _is_git_repository(self) -> bool:
        """Check if the current directory is a git repository."""
        try:
            result = self._run_command(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repository_path,
                capture_output=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_current_commit_hash(self) -> str:
        """Get the current commit hash."""
        try:
            result = self._run_command(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repository_path,
                capture_output=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]
            return "unknown"
        except Exception as e:
            logger.error(f"Failed to get commit hash: {e}")
            return "unknown"

    def _run_command(
        self,
        command: list[str],
        cwd: Path | None = None,
        capture_output: bool = True,
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """Securely run a command using subprocess.

        Args:
            command: Command as list of strings for secure execution
            cwd: Working directory
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess instance

        Raises:
            subprocess.TimeoutExpired: If command times out
            subprocess.SubprocessError: On subprocess errors
            ValueError: If command is invalid or unsafe

        """
        # Validate command security
        if not command or not isinstance(command, list):
            raise ValueError("Command must be a non-empty list")

        # Additional security validation - prevent path traversal and dangerous commands
        if any("/../" in str(arg) or str(arg).startswith("/") for arg in command):
            raise ValueError("Command contains potentially unsafe paths")

        # Sanitize command arguments
        sanitized_command = [
            shlex.quote(str(arg)) if " " in str(arg) else str(arg) for arg in command
        ]

        logger.debug(f"Executing command: {' '.join(sanitized_command)}")

        if self.dry_run:
            logger.info(f"DRY RUN: Would execute: {' '.join(sanitized_command)}")
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        try:
            result = subprocess.run(  # noqa: subprocess
                command,  # Use original command, not sanitized
                cwd=cwd or self.repository_path,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False,  # Don't raise on non-zero exit
                shell=False,  # Explicit security measure
            )

            if result.returncode != 0:
                logger.warning(
                    f"Command failed with exit code {result.returncode}: "
                    f"{' '.join(sanitized_command)}",
                )
                if result.stderr:
                    logger.warning(f"STDERR: {result.stderr}")

            return result

        except subprocess.TimeoutExpired:
            logger.error(
                f"Command timed out after {timeout}s: {' '.join(sanitized_command)}",
            )
            raise
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise

    def _log_step(
        self,
        step_name: str,
        status: RecoveryStatus,
        details: str = "",
        error_message: str = "",
        duration: float = 0.0,
    ) -> None:
        """Log a recovery step and add to report."""
        step = RecoveryStep(
            name=step_name,
            status=status,
            timestamp=datetime.now(timezone.utc),
            details=details,
            error_message=error_message,
            duration_seconds=duration,
        )

        self.report.steps.append(step)

        # Log with appropriate level
        emoji_map = {
            RecoveryStatus.SUCCESS: "✅",
            RecoveryStatus.FAILED: "❌",
            RecoveryStatus.IN_PROGRESS: "🔄",
            RecoveryStatus.PARTIAL_SUCCESS: "⚠️",
            RecoveryStatus.PENDING: "⏳",
        }

        emoji = emoji_map.get(status, "📋")
        log_message = f"{emoji} {step_name}"

        if details:
            log_message += f" - {details}"

        if status == RecoveryStatus.SUCCESS:
            logger.info(log_message)
        elif status == RecoveryStatus.FAILED:
            logger.error(f"{log_message} - Error: {error_message}")
        elif status == RecoveryStatus.IN_PROGRESS:
            logger.info(log_message)
        else:
            logger.warning(log_message)

    def analyze_changed_files(self) -> FileRiskAnalysis:
        """Analyze files changed in the current commit for CI failure risk.

        Returns:
            FileRiskAnalysis with categorized files

        """
        self._log_step("File Risk Analysis", RecoveryStatus.IN_PROGRESS)

        try:
            # Get changed files for the commit
            result = self._run_command(
                [
                    "git",
                    "show",
                    "--name-only",
                    "--format=",
                    self.commit_hash,
                ],
            )

            if result.returncode != 0:
                self._log_step(
                    "File Risk Analysis",
                    RecoveryStatus.FAILED,
                    error_message="Failed to get changed files",
                )
                return FileRiskAnalysis()

            changed_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
            analysis = FileRiskAnalysis()

            for file_path in changed_files:
                risk = self._assess_file_risk(file_path)

                if risk == RiskLevel.CRITICAL:
                    analysis.critical_risk.append(file_path)
                elif risk == RiskLevel.HIGH:
                    analysis.high_risk.append(file_path)
                elif risk == RiskLevel.MEDIUM:
                    analysis.medium_risk.append(file_path)
                else:
                    analysis.low_risk.append(file_path)

            # Determine overall risk
            if analysis.critical_risk:
                analysis.overall_risk = RiskLevel.CRITICAL
            elif analysis.high_risk:
                analysis.overall_risk = RiskLevel.HIGH
            elif analysis.medium_risk:
                analysis.overall_risk = RiskLevel.MEDIUM
            else:
                analysis.overall_risk = RiskLevel.LOW

            self.report.file_analysis = analysis

            self._log_step(
                "File Risk Analysis",
                RecoveryStatus.SUCCESS,
                f"Analyzed {len(changed_files)} files - "
                f"Overall risk: {analysis.overall_risk.value}",
            )

            return analysis

        except Exception as e:
            self._log_step(
                "File Risk Analysis",
                RecoveryStatus.FAILED,
                error_message=str(e),
            )
            return FileRiskAnalysis()

    def _assess_file_risk(self, file_path: str) -> RiskLevel:
        """Assess the CI failure risk of a single file.

        Args:
            file_path: Path to the file

        Returns:
            Risk level for the file

        """
        file_path_lower = file_path.lower()

        # Critical risk files
        critical_patterns = [
            "dockerfile",
            "docker-compose",
            ".github/workflows",
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "makefile",
            ".gitignore",
        ]

        if any(pattern in file_path_lower for pattern in critical_patterns):
            return RiskLevel.CRITICAL

        # High risk files
        high_risk_patterns = [
            "test_",
            "_test.py",
            "/tests/",
            "conftest.py",
            "tox.ini",
            ".pre-commit",
            "pytest.ini",
        ]

        if any(pattern in file_path_lower for pattern in high_risk_patterns):
            return RiskLevel.HIGH

        # Medium risk files
        medium_risk_patterns = [
            "src/",
            "lib/",
            "__init__.py",
            "config",
            "settings",
        ]

        if any(pattern in file_path_lower for pattern in medium_risk_patterns):
            return RiskLevel.MEDIUM

        # Everything else is low risk
        return RiskLevel.LOW

    def run_code_quality_checks(self) -> bool:
        """Run code quality checks (linting, type checking, etc.).

        Returns:
            True if all checks pass, False otherwise

        """
        self._log_step("Code Quality Checks", RecoveryStatus.IN_PROGRESS)

        checks = [
            ([sys.executable, "-m", "flake8", "src/"], "Flake8 linting"),
            ([sys.executable, "-m", "black", "--check", "src/"], "Black formatting"),
            ([sys.executable, "-m", "isort", "--check-only", "src/"], "Import sorting"),
            ([sys.executable, "-m", "mypy", "src/"], "Type checking"),
        ]

        all_passed = True

        for command, check_name in checks:
            try:
                result = self._run_command(command, timeout=120)

                if result.returncode == 0:
                    logger.info(f"✅ {check_name} passed")
                else:
                    logger.warning(f"⚠️ {check_name} failed")
                    all_passed = False

            except subprocess.TimeoutExpired:
                logger.error(f"❌ {check_name} timed out")
                all_passed = False
            except Exception as e:
                logger.error(f"❌ {check_name} error: {e}")
                all_passed = False

        status = (
            RecoveryStatus.SUCCESS if all_passed else RecoveryStatus.PARTIAL_SUCCESS
        )
        self._log_step("Code Quality Checks", status)

        return all_passed

    def run_tests(self) -> bool:
        """Run the test suite.

        Returns:
            True if tests pass, False otherwise

        """
        self._log_step("Test Execution", RecoveryStatus.IN_PROGRESS)

        try:
            # Run tests with coverage
            result = self._run_command(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/",
                    "-v",
                    "--tb=short",
                    "--maxfail=5",
                    "--timeout=300",
                ],
                timeout=600,
            )

            if result.returncode == 0:
                self._log_step(
                    "Test Execution",
                    RecoveryStatus.SUCCESS,
                    "All tests passed",
                )
                return True
            self._log_step(
                "Test Execution",
                RecoveryStatus.FAILED,
                f"Tests failed with exit code {result.returncode}",
            )
            return False

        except subprocess.TimeoutExpired:
            self._log_step("Test Execution", RecoveryStatus.FAILED, "Tests timed out")
            return False
        except Exception as e:
            self._log_step(
                "Test Execution",
                RecoveryStatus.FAILED,
                error_message=str(e),
            )
            return False

    def generate_recovery_suggestions(self) -> list[str]:
        """Generate actionable recovery suggestions based on analysis.

        Returns:
            List of recovery suggestions

        """
        suggestions = []

        if not self.report.file_analysis:
            return ["Run file analysis first"]

        risk = self.report.file_analysis.overall_risk

        if risk == RiskLevel.CRITICAL:
            suggestions.extend(
                [
                    "Review critical infrastructure changes carefully",
                    "Test in isolated environment before deployment",
                    "Consider rolling back changes if CI continues to fail",
                ],
            )

        if risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            suggestions.extend(
                [
                    "Run full test suite locally before pushing",
                    "Check for missing dependencies or configuration",
                    "Verify environment variables are set correctly",
                ],
            )

        # Add specific suggestions based on file types
        if self.report.file_analysis.high_risk:
            test_files = [
                f for f in self.report.file_analysis.high_risk if "test" in f.lower()
            ]
            if test_files:
                suggestions.append(
                    "Review test changes - ensure mocks and fixtures are correct",
                )

        if not suggestions:
            suggestions.append(
                "No specific issues detected - CI failure may be transient",
            )

        return suggestions

    def save_report(self) -> Path:
        """Save the recovery report to a JSON file.

        Returns:
            Path to the saved report file

        """
        report_file = (
            self.repository_path / f"ci_recovery_report_{self.commit_hash}_"
            f"{int(datetime.now().timestamp())}.json"
        )

        try:
            # Convert dataclass to dict for JSON serialization
            report_dict = {
                "timestamp": self.report.timestamp.isoformat(),
                "commit_hash": self.report.commit_hash,
                "repository_path": str(self.report.repository_path),
                "steps": [
                    {
                        "name": step.name,
                        "status": step.status.value,
                        "timestamp": step.timestamp.isoformat(),
                        "details": step.details,
                        "error_message": step.error_message,
                        "duration_seconds": step.duration_seconds,
                    }
                    for step in self.report.steps
                ],
                "file_analysis": {
                    "low_risk": self.report.file_analysis.low_risk
                    if self.report.file_analysis
                    else [],
                    "medium_risk": self.report.file_analysis.medium_risk
                    if self.report.file_analysis
                    else [],
                    "high_risk": self.report.file_analysis.high_risk
                    if self.report.file_analysis
                    else [],
                    "critical_risk": self.report.file_analysis.critical_risk
                    if self.report.file_analysis
                    else [],
                    "overall_risk": self.report.file_analysis.overall_risk.value
                    if self.report.file_analysis
                    else "low",
                }
                if self.report.file_analysis
                else None,
                "fixes_applied": self.report.fixes_applied,
                "final_status": self.report.final_status.value,
                "total_duration_seconds": self.report.total_duration_seconds,
                "metadata": self.report.metadata,
            }

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Recovery report saved to: {report_file}")
            return report_file

        except Exception as e:
            logger.error(f"Failed to save recovery report: {e}")
            raise

    def execute_recovery(self) -> bool:
        """Execute the complete CI failure recovery process.

        Returns:
            True if recovery was successful, False otherwise

        """
        start_time = datetime.now()

        logger.info(f"🚨 Starting CI/CD Failure Recovery for commit {self.commit_hash}")
        logger.info("=" * 70)

        try:
            # Phase 1: File Analysis
            logger.info("🔍 Phase 1: File Risk Analysis")
            self.analyze_changed_files()

            # Phase 2: Code Quality Checks
            logger.info("🔧 Phase 2: Code Quality Checks")
            quality_passed = self.run_code_quality_checks()

            # Phase 3: Test Execution
            logger.info("🧪 Phase 3: Test Execution")
            tests_passed = self.run_tests()

            # Phase 4: Generate Suggestions
            logger.info("💡 Phase 4: Recovery Suggestions")
            suggestions = self.generate_recovery_suggestions()

            for suggestion in suggestions:
                logger.info(f"   • {suggestion}")

            # Determine final status
            if quality_passed and tests_passed:
                self.report.final_status = RecoveryStatus.SUCCESS
                logger.info("✅ Recovery completed successfully")
                success = True
            elif quality_passed or tests_passed:
                self.report.final_status = RecoveryStatus.PARTIAL_SUCCESS
                logger.warning("⚠️ Recovery partially successful")
                success = False
            else:
                self.report.final_status = RecoveryStatus.FAILED
                logger.error("❌ Recovery failed")
                success = False

            # Calculate total duration
            end_time = datetime.now()
            self.report.total_duration_seconds = (end_time - start_time).total_seconds()

            # Save report
            self.save_report()

            logger.info("=" * 70)
            logger.info(
                f"🎯 CI Recovery completed in "
                f"{self.report.total_duration_seconds:.2f}s",
            )

            return success

        except Exception as e:
            logger.error(f"Recovery process failed with exception: {e}")
            self.report.final_status = RecoveryStatus.FAILED
            self._log_step(
                "Recovery Process",
                RecoveryStatus.FAILED,
                error_message=str(e),
            )

            try:
                self.save_report()
            except Exception:
                logger.error("Failed to save error report")

            return False


def main() -> None:
    """Main entry point for the CI recovery system."""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Professional CI/CD Failure Recovery System",
    )
    parser.add_argument(
        "--commit",
        help="Specific commit hash to analyze (defaults to HEAD)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operations without making changes",
    )
    parser.add_argument(
        "--repository",
        type=Path,
        help="Path to git repository (defaults to current directory)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level",
    )

    args = parser.parse_args()

    # Configure logging level
    log_level = getattr(logging, args.log_level)
    logging.getLogger().setLevel(log_level)

    # Check for environment variable overrides
    dry_run = args.dry_run or os.getenv("CI_RECOVERY_DRY_RUN", "").lower() == "true"

    try:
        recovery_system = CIFailureRecoverySystem(
            repository_path=args.repository,
            commit_hash=args.commit,
            dry_run=dry_run,
        )

        success = recovery_system.execute_recovery()
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Failed to initialize recovery system: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
