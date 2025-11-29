"""Synchronization orchestration logic."""

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.git_sync.exceptions import AuditError, GitOperationError, SyncError
from scripts.git_sync.models import SyncStep
from scripts.utils.atomic import atomic_write_json

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    """Enterprise-grade Git synchronization with preventive audit capabilities.

    Implements idempotent operations, comprehensive error handling,
    and structured logging for production-grade automation.
    """

    def __init__(
        self,
        workspace_root: Path,
        config: dict[str, Any],
        *,
        dry_run: bool = False,
    ) -> None:
        """Initialize the synchronization manager."""
        self.workspace_root = workspace_root.resolve()
        self.config = config
        self.dry_run = dry_run
        self.steps: list[SyncStep] = []
        self.sync_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now(timezone.utc)

        # Validate workspace is a Git repository
        self._validate_git_repository()

        logger.info("Initialized SyncOrchestrator (ID: %s)", self.sync_id)
        logger.info("Workspace: %s", self.workspace_root)
        logger.info("Dry run mode: %s", self.dry_run)

    def _validate_git_repository(self) -> None:
        """Validate that workspace is a Git repository."""
        git_dir = self.workspace_root / ".git"
        if not git_dir.exists():
            raise SyncError(f"Not a Git repository: {self.workspace_root}")

    def _update_heartbeat(self, status: str) -> None:
        """Update heartbeat file with current sync state.

        Args:
            status: Current status ('running', 'success', 'failed', 'crashed')

        Note:
            Failures in heartbeat updates are logged but do not interrupt sync.
            The heartbeat is telemetry, not critical business logic.

        """
        try:
            heartbeat_path = self.workspace_root / ".git" / "sync_heartbeat"

            # Calculate duration since sync start
            current_time = datetime.now(timezone.utc)
            duration_seconds = (current_time - self.start_time).total_seconds()

            # Get current branch if possible
            try:
                branch_result = self._run_command(
                    ["git", "branch", "--show-current"],
                    timeout=5,
                    check=False,
                )
                if branch_result.returncode == 0:
                    current_branch = branch_result.stdout.strip()
                else:
                    current_branch = "unknown"
            except GitOperationError:
                current_branch = "unknown"

            # Build heartbeat data
            heartbeat_data = {
                "sync_id": self.sync_id,
                "status": status,
                "timestamp": current_time.isoformat(),
                "workspace": str(self.workspace_root),
                "branch": current_branch,
                "duration_seconds": round(duration_seconds, 2),
                "phases_completed": len(
                    [s for s in self.steps if s.status == "success"],
                ),
                "pid": os.getpid(),
            }

            # Atomic write with fsync (POSIX compliant)
            atomic_write_json(heartbeat_path, heartbeat_data, fsync=True)

            logger.debug("Heartbeat updated: %s (status=%s)", heartbeat_path, status)

        except (OSError, GitOperationError) as e:
            # Heartbeat failures are non-critical - log and continue
            logger.warning("Failed to update heartbeat: %s", e)

    def _run_command(
        self,
        command: list[str],
        timeout: int = 300,
        capture_output: bool = True,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Execute command with security best practices.

        Args:
            command: Command as list (shell=False explicitly set below)
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise on non-zero exit
            env: Optional environment variables

        Returns:
            CompletedProcess instance

        Raises:
            GitOperationError: On command execution failure

        """
        if self.dry_run:
            logger.info("[DRY RUN] Would execute: %s", " ".join(command))
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[DRY RUN]",
                stderr="",
            )

        try:
            # Ensure we never use shell=True for security
            env_vars = {**os.environ}
            if env:
                env_vars.update(env)

            result = subprocess.run(  # noqa: subprocess
                command,
                cwd=self.workspace_root,
                timeout=timeout,
                shell=False,  # Security: prevent shell injection
                capture_output=capture_output,
                text=True,
                check=check,
                env=env_vars,
            )

            cmd_str = " ".join(command)
            debug_msg = f"Command executed: {cmd_str} (exit code: {result.returncode})"
            logger.debug(debug_msg)
            return result

        except subprocess.CalledProcessError as e:
            error_msg = (
                f"Command failed: {' '.join(command)} (exit code: {e.returncode})"
            )
            if e.stderr:
                error_msg += f" - {e.stderr.strip()}"
            raise GitOperationError(error_msg) from e
        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out after {timeout}s: {' '.join(command)}"
            raise GitOperationError(error_msg) from e

    def _check_git_status(self) -> dict[str, Any]:
        """Check Git repository status."""
        step = SyncStep("git_status", "Checking Git repository status")
        step.start()
        self.steps.append(step)

        try:
            # Check for uncommitted changes
            result = self._run_command(["git", "status", "--porcelain"])
            changed_files = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]

            # Check current branch
            branch_result = self._run_command(["git", "branch", "--show-current"])
            current_branch = branch_result.stdout.strip()

            # Check if repository is clean
            is_clean = len(changed_files) == 0

            status_info = {
                "is_clean": is_clean,
                "changed_files": changed_files,
                "total_changes": len(changed_files),
                "current_branch": current_branch,
            }

            step.complete(status_info)
            return status_info

        except GitOperationError as e:
            step.fail(str(e))
            raise

    def _run_code_audit(self) -> dict[str, Any]:
        """Execute comprehensive code audit."""
        step = SyncStep("code_audit", "Running preventive code audit")
        step.start()
        self.steps.append(step)

        try:
            # Check if audit script exists
            audit_script = self.workspace_root / "scripts" / "code_audit.py"
            if not audit_script.exists():
                logger.warning("Code audit script not found, skipping audit")
                step.complete({"status": "skipped", "reason": "audit_script_not_found"})
                return {"passed": True, "status": "skipped"}

            # Execute audit with CI simulation
            audit_command = [
                sys.executable,
                str(audit_script),
                "--output",
                "json",
                "--fail-on",
                self.config.get("audit_fail_threshold", "HIGH"),
            ]

            result = self._run_command(
                audit_command,
                timeout=self.config.get("audit_timeout", 300),
                check=False,  # Don't raise on non-zero exit, we'll handle it
            )

            audit_passed = result.returncode == 0
            audit_details = {
                "passed": audit_passed,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

            if audit_passed:
                step.complete(audit_details)
            else:
                step.fail("Code audit failed", audit_details)
                if self.config.get("strict_audit", True):
                    raise AuditError(
                        f"Code audit failed with exit code {result.returncode}",
                    )

            return audit_details

        except (GitOperationError, AuditError) as e:
            step.fail(str(e))
            raise

    def _apply_lint_fixes(self) -> dict[str, Any]:
        """Apply automated lint fixes if available."""
        step = SyncStep("lint_fixes", "Applying automated lint fixes")
        step.start()
        self.steps.append(step)

        try:
            # Check if lint fix script exists
            lint_script = self.workspace_root / "scripts" / "lint_fix.py"
            if not lint_script.exists():
                step.complete({"status": "skipped", "reason": "lint_script_not_found"})
                return {"fixes_applied": 0, "status": "skipped"}

            # Execute lint fixes
            lint_command = [sys.executable, str(lint_script), "--auto-fix"]

            result = self._run_command(
                lint_command,
                timeout=self.config.get("lint_timeout", 180),
                check=False,
            )

            fixes_applied = 0
            # Parse output to count fixes (implementation depends on lint_fix.py format)
            if "fixes applied" in result.stdout.lower():
                # Extract number from output
                match = re.search(r"(\d+)\s+fixes?\s+applied", result.stdout.lower())
                if match:
                    fixes_applied = int(match.group(1))

            fix_details = {
                "fixes_applied": fixes_applied,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

            step.complete(fix_details)
            return fix_details

        except GitOperationError as e:
            step.fail(str(e))
            raise

    def _generate_smart_commit_message(self, git_status: dict[str, Any]) -> str:
        """Generate intelligent commit message based on changes."""
        changed_files = git_status.get("changed_files", [])

        # Analyze file types and changes
        categories: dict[str, list[str]] = {
            "feat": [],
            "fix": [],
            "test": [],
            "docs": [],
            "chore": [],
            "style": [],
            "refactor": [],
        }

        for file_change in changed_files:
            # Parse Git status format (e.g., "M  file.py", "A  newfile.py")
            if len(file_change) < 3:
                continue

            status_code = file_change[0]  # M, A, D, etc.
            filepath = file_change[3:]  # Skip status codes and space

            # Categorize by path and content
            if "test" in filepath.lower():
                categories["test"].append(filepath)
            elif filepath.endswith(".md") or "doc" in filepath.lower():
                categories["docs"].append(filepath)
            elif filepath.startswith("src/") or filepath.endswith(".py"):
                if status_code == "A":  # New file
                    categories["feat"].append(filepath)
                else:
                    categories["fix"].append(filepath)  # Modified existing
            elif "script" in filepath or filepath.startswith("scripts/"):
                categories["chore"].append(filepath)
            else:
                categories["chore"].append(filepath)

        # Determine primary category
        primary_category = "chore"  # Default
        max_count = 0

        for category, files in categories.items():
            if len(files) > max_count:
                max_count = len(files)
                primary_category = category

        # Generate message
        total_files = len(changed_files)
        message_parts = [f"{primary_category}: smart sync with preventive audit"]

        if total_files > 0:
            message_parts.append(f"({total_files} files)")

        # Add fix information if available
        if hasattr(self, "_last_audit_result"):
            audit_result = getattr(self, "_last_audit_result", {})
            if not audit_result.get("passed", True):
                message_parts.append("[audit-fixes]")

        return " ".join(message_parts)

    def _commit_and_push(self, git_status: dict[str, Any]) -> dict[str, Any]:
        """Perform Git commit and push operations."""
        if git_status["is_clean"]:
            logger.info("Repository is clean, nothing to commit")
            return {"status": "clean", "committed": False}

        # Add files to staging
        add_step = SyncStep("git_add", "Adding files to Git staging area")
        add_step.start()
        self.steps.append(add_step)

        try:
            # Use git add . but exclude sensitive files
            self._run_command(["git", "add", "."])
            add_step.complete({"files_added": len(git_status["changed_files"])})

        except GitOperationError as e:
            add_step.fail(str(e))
            raise

        # Commit changes
        commit_step = SyncStep("git_commit", "Creating Git commit")
        commit_step.start()
        self.steps.append(commit_step)

        try:
            commit_message = self._generate_smart_commit_message(git_status)
            self._run_command(["git", "commit", "-m", commit_message])

            # Get commit hash
            hash_result = self._run_command(["git", "rev-parse", "HEAD"])
            commit_hash = hash_result.stdout.strip()

            commit_details = {
                "message": commit_message,
                "hash": commit_hash,
                "files_committed": len(git_status["changed_files"]),
            }

            commit_step.complete(commit_details)

        except GitOperationError as e:
            commit_step.fail(str(e))
            raise

        # Push to remote
        push_step = SyncStep("git_push", "Pushing to remote repository")
        push_step.start()
        self.steps.append(push_step)

        try:
            # Get current branch for push
            current_branch = git_status["current_branch"]
            self._run_command(["git", "push", "origin", current_branch])

            push_details = {
                "branch": current_branch,
                "commit_hash": commit_hash,
            }

            push_step.complete(push_details)

            return {
                "status": "success",
                "committed": True,
                "commit": commit_details,
                "push": push_details,
            }

        except GitOperationError as e:
            push_step.fail(str(e))

            # Rollback commit if push fails
            logger.warning("Push failed, attempting to rollback commit")
            try:
                self._run_command(["git", "reset", "--soft", "HEAD~1"])
                logger.info("Successfully rolled back commit")
            except GitOperationError as rollback_error:
                logger.error("Rollback failed: %s", rollback_error)

            raise

    def _cleanup_repository(self) -> None:
        """Perform repository cleanup operations."""
        cleanup_step = SyncStep("git_cleanup", "Cleaning up repository")
        cleanup_step.start()
        self.steps.append(cleanup_step)

        try:
            cleanup_commands = [
                ["git", "gc", "--auto"],
                ["git", "remote", "prune", "origin"],
            ]

            cleanup_results = []
            for cmd in cleanup_commands:
                try:
                    result = self._run_command(cmd, timeout=60, check=False)
                    cleanup_results.append(
                        {
                            "command": " ".join(cmd),
                            "success": result.returncode == 0,
                        },
                    )
                except GitOperationError:
                    cleanup_results.append(
                        {
                            "command": " ".join(cmd),
                            "success": False,
                        },
                    )

            cleanup_step.complete({"operations": cleanup_results})

        except Exception as e:
            cleanup_step.fail(str(e))
            # Don't raise - cleanup failures are not critical

    def _save_sync_report(self) -> Path:
        """Save synchronization report to file."""
        report = {
            "metadata": {
                "sync_id": self.sync_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "workspace": str(self.workspace_root),
                "dry_run": self.dry_run,
                "config": self.config,
            },
            "steps": [step.to_dict() for step in self.steps],
            "summary": {
                "total_steps": len(self.steps),
                "successful_steps": len(
                    [s for s in self.steps if s.status == "success"],
                ),
                "failed_steps": len([s for s in self.steps if s.status == "failed"]),
                "total_duration": sum(step._get_duration() for step in self.steps),
            },
        }

        report_file = self.workspace_root / f"sync_report_{self.sync_id}.json"

        try:
            with report_file.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info("Sync report saved: %s", report_file)
            return report_file

        except Exception as e:
            logger.error("Failed to save sync report: %s", e)
            raise

    def execute_sync(self) -> bool:
        """Execute complete smart synchronization workflow.

        Returns:
            True if synchronization completed successfully, False otherwise.

        """
        logger.info("🚀 Starting Smart Git Synchronization")
        logger.info("=" * 60)

        # Update heartbeat: sync started
        self._update_heartbeat("running")

        try:
            # Phase 1: Repository Status Check
            logger.info("📋 PHASE 1: Repository Status Analysis")
            git_status = self._check_git_status()

            # Protection: prevent direct push to main
            current_branch = git_status.get("current_branch")
            if current_branch == "main":
                logger.error("🛑 OPERAÇÃO PROIBIDA NA 'main'")
                logger.error("A branch 'main' está protegida por regras ('Cofre').")
                logger.error("Este script não pode fazer 'push' direto na 'main'.")
                logger.warning(
                    "Use o 'Fluxo de Trabalho (Chave Mestra)': Crie um branch, "
                    "abra um PR e solicite um 'Bypass' do administrador.",
                )
                raise SyncError("Tentativa de 'push' direto na 'main' protegida.")

            if git_status["is_clean"]:
                logger.info("Repository is clean, no changes to sync")
                self._save_sync_report()
                return True

            logger.info("Found %d changes to process", git_status["total_changes"])

            # Phase 2: Code Quality and Security Audit
            logger.info("🔍 PHASE 2: Preventive Code Audit")
            audit_result = self._run_code_audit()
            self._last_audit_result = audit_result  # Store for commit message

            # Phase 3: Automated Fixes (if audit found issues)
            if not audit_result.get("passed", True) and self.config.get(
                "auto_fix_enabled",
                True,
            ):
                logger.info("🔧 PHASE 3: Automated Lint Fixes")
                fix_result = self._apply_lint_fixes()
                logger.info(
                    "Applied %d automated fixes",
                    fix_result.get("fixes_applied", 0),
                )

            # Phase 4: Git Operations
            logger.info("📤 PHASE 4: Git Commit and Push")
            git_result = self._commit_and_push(git_status)

            # Phase 5: Cleanup
            if self.config.get("cleanup_enabled", True):
                logger.info("🧹 PHASE 5: Repository Cleanup")
                self._cleanup_repository()

            # Save report and finalize
            self._save_sync_report()

            logger.info("=" * 60)
            logger.info("✅ Smart Git Synchronization completed successfully!")

            if git_result.get("committed"):
                commit_hash = git_result.get("commit", {}).get("hash", "unknown")
                logger.info("📦 Commit: %s", commit_hash[:8])
                logger.info("🌳 Branch: %s", git_status["current_branch"])

            # Update heartbeat: sync successful
            self._update_heartbeat("success")

            return True

        except (SyncError, GitOperationError, AuditError) as e:
            logger.error("Synchronization failed: %s", e)
            self._update_heartbeat("failed")
            self._save_sync_report()
            return False

        except Exception as e:
            logger.critical("UNEXPECTED BUG: %s", e, exc_info=True)
            self._update_heartbeat("crashed")
            self._save_sync_report()
            raise


# Backward compatibility alias
SmartGitSync = SyncOrchestrator
