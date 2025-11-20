"""Git operations wrapper for Smart Git Sync.

This module provides a safe, high-level interface for Git operations,
encapsulating subprocess calls and providing semantic methods.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from scripts.git_sync.exceptions import GitOperationError

logger = logging.getLogger(__name__)


class GitWrapper:  # noqa: subprocess
    """Safe wrapper for Git operations with subprocess management.

    This class encapsulates all Git command execution, providing:
    - Security: Never uses shell=False (never shell with True)
    - Type safety: Returns structured data
    - Error handling: Converts subprocess errors to GitOperationError
    - Dry-run support: Can simulate operations without executing
    - Logging: Comprehensive operation logging

    Attributes:
        workspace_root: Path to the Git repository root
        dry_run: If True, simulates operations without executing
        timeout: Default timeout for Git operations (seconds)
    """

    def __init__(
        self,
        workspace_root: Path,
        dry_run: bool = False,
        timeout: int = 120,
    ) -> None:
        """Initialize Git wrapper.

        Args:
            workspace_root: Path to Git repository root
            dry_run: If True, only simulate operations
            timeout: Default timeout for Git commands in seconds
        """
        self.workspace_root = workspace_root.resolve()
        self.dry_run = dry_run
        self.timeout = timeout

        # Validate Git repository
        if not (self.workspace_root / ".git").exists():
            msg = f"Not a Git repository: {self.workspace_root}"
            raise GitOperationError(msg)

        logger.debug(
            "GitWrapper initialized: workspace=%s, dry_run=%s",
            self.workspace_root,
            self.dry_run,
        )

    def _run_git(
        self,
        args: list[str],
        timeout: int | None = None,
        capture_output: bool = True,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Execute Git command with security best practices.

        Args:
            args: Git command arguments (without 'git' prefix)
            timeout: Command timeout in seconds (uses default if None)
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise on non-zero exit
            env: Optional environment variables to add

        Returns:
            CompletedProcess instance with command results

        Raises:
            GitOperationError: On command execution failure or timeout
        """
        command = ["git", *args]
        cmd_timeout = timeout or self.timeout

        # Dry-run mode: simulate execution
        if self.dry_run:
            logger.info("[DRY RUN] Would execute: %s", " ".join(command))
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[DRY RUN]",
                stderr="",
            )

        # Prepare environment
        env_vars = {**os.environ}
        if env:
            env_vars.update(env)

        try:
            # Execute command (never uses shell=True for security)
            result = subprocess.run(  # noqa: subprocess
                command,
                cwd=self.workspace_root,
                timeout=cmd_timeout,
                capture_output=capture_output,
                text=True,
                check=check,
                env=env_vars,
            )

            logger.debug(
                "Git command executed: %s (exit code: %d)",
                " ".join(command),
                result.returncode,
            )
            return result

        except subprocess.CalledProcessError as e:
            error_msg = (
                f"Git command failed: {' '.join(command)} (exit code: {e.returncode})"
            )
            if e.stderr:
                error_msg += f" - {e.stderr.strip()}"
            raise GitOperationError(error_msg) from e

        except subprocess.TimeoutExpired as e:
            error_msg = (
                f"Git command timed out after {cmd_timeout}s: {' '.join(command)}"
            )
            raise GitOperationError(error_msg) from e

    # High-level semantic methods

    def get_current_branch(self) -> str:
        """Get the name of the current Git branch.

        Returns:
            Current branch name (e.g., "main", "feature/my-feature")

        Raises:
            GitOperationError: If command fails
        """
        result = self._run_git(["branch", "--show-current"])
        branch = result.stdout.strip()
        logger.debug("Current branch: %s", branch)
        return branch

    def is_clean(self) -> bool:
        """Check if the working directory is clean (no uncommitted changes).

        Returns:
            True if working directory is clean, False otherwise

        Raises:
            GitOperationError: If command fails
        """
        result = self._run_git(["status", "--porcelain"])
        is_clean = len(result.stdout.strip()) == 0
        logger.debug("Repository clean: %s", is_clean)
        return is_clean

    def get_status(self) -> list[str]:
        """Get list of changed files in the working directory.

        Returns:
            List of file status lines (e.g., ["M  file.py", "A  newfile.py"])

        Raises:
            GitOperationError: If command fails
        """
        result = self._run_git(["status", "--porcelain"])
        files = [
            line.strip() for line in result.stdout.strip().split("\n") if line.strip()
        ]
        logger.debug("Status: %d files changed", len(files))
        return files

    def add_all(self) -> None:
        """Add all changes to the staging area (git add .).

        Raises:
            GitOperationError: If command fails
        """
        self._run_git(["add", "."])
        logger.debug("Added all files to staging area")

    def add_files(self, patterns: list[str]) -> None:
        """Add specific files/patterns to the staging area.

        Args:
            patterns: List of file patterns to add (e.g., ["*.py", "docs/"])

        Raises:
            GitOperationError: If command fails
        """
        self._run_git(["add", *patterns])
        logger.debug("Added files to staging area: %s", patterns)

    def commit(self, message: str) -> str:
        """Create a Git commit with the given message.

        Args:
            message: Commit message

        Returns:
            Commit hash (short form)

        Raises:
            GitOperationError: If command fails
        """
        self._run_git(["commit", "-m", message])

        # Get commit hash
        result = self._run_git(["rev-parse", "HEAD"])
        commit_hash = result.stdout.strip()

        logger.info("Created commit: %s", commit_hash[:8])
        return commit_hash

    def push(self, branch: str, remote: str = "origin", force: bool = False) -> None:
        """Push commits to remote repository.

        Args:
            branch: Branch name to push
            remote: Remote name (default: "origin")
            force: If True, use force push (dangerous!)

        Raises:
            GitOperationError: If command fails
        """
        args = ["push", remote, branch]
        if force:
            args.append("--force")
            logger.warning("Force pushing to %s/%s", remote, branch)

        self._run_git(args)
        logger.info("Pushed to %s/%s", remote, branch)

    def checkout(self, branch: str, create: bool = False) -> None:
        """Checkout a Git branch.

        Args:
            branch: Branch name to checkout
            create: If True, create the branch if it doesn't exist

        Raises:
            GitOperationError: If command fails
        """
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(branch)

        self._run_git(args)
        logger.info("Checked out branch: %s", branch)

    def create_branch(self, branch: str, base: str | None = None) -> None:
        """Create a new branch without checking it out.

        Args:
            branch: Name of the new branch
            base: Base branch/commit to create from (default: current HEAD)

        Raises:
            GitOperationError: If command fails
        """
        args = ["branch", branch]
        if base:
            args.append(base)

        self._run_git(args)
        logger.info("Created branch: %s", branch)

    def get_remote_url(self, remote: str = "origin") -> str:
        """Get the URL of a remote repository.

        Args:
            remote: Remote name (default: "origin")

        Returns:
            Remote URL

        Raises:
            GitOperationError: If command fails
        """
        result = self._run_git(["remote", "get-url", remote])
        url = result.stdout.strip()
        logger.debug("Remote %s URL: %s", remote, url)
        return url

    def fetch(self, remote: str = "origin") -> None:
        """Fetch changes from remote repository.

        Args:
            remote: Remote name (default: "origin")

        Raises:
            GitOperationError: If command fails
        """
        self._run_git(["fetch", remote])
        logger.debug("Fetched from %s", remote)

    def pull(self, branch: str | None = None, remote: str = "origin") -> None:
        """Pull changes from remote repository.

        Args:
            branch: Branch name to pull (default: current branch)
            remote: Remote name (default: "origin")

        Raises:
            GitOperationError: If command fails
        """
        args = ["pull", remote]
        if branch:
            args.append(branch)

        self._run_git(args)
        logger.info("Pulled from %s", remote)

    def reset_soft(self, target: str = "HEAD~1") -> None:
        """Reset to a previous commit, keeping changes staged.

        Args:
            target: Git reference to reset to (default: HEAD~1)

        Raises:
            GitOperationError: If command fails
        """
        self._run_git(["reset", "--soft", target])
        logger.warning("Soft reset to %s", target)

    def reset_hard(self, target: str = "HEAD") -> None:
        """Reset to a previous commit, discarding all changes.

        WARNING: This operation is destructive and cannot be undone easily!

        Args:
            target: Git reference to reset to (default: HEAD)

        Raises:
            GitOperationError: If command fails
        """
        self._run_git(["reset", "--hard", target])
        logger.warning("Hard reset to %s (destructive!)", target)

    def gc(self, auto: bool = True) -> None:
        """Run Git garbage collection to optimize repository.

        Args:
            auto: If True, only run if needed (git gc --auto)

        Raises:
            GitOperationError: If command fails
        """
        args = ["gc"]
        if auto:
            args.append("--auto")

        self._run_git(args, timeout=300)
        logger.debug("Git garbage collection completed")

    def prune_remote(self, remote: str = "origin") -> None:
        """Remove stale remote-tracking branches.

        Args:
            remote: Remote name (default: "origin")

        Raises:
            GitOperationError: If command fails
        """
        self._run_git(["remote", "prune", remote])
        logger.debug("Pruned remote %s", remote)

    def get_commit_info(self, ref: str = "HEAD") -> dict[str, Any]:
        """Get information about a specific commit.

        Args:
            ref: Git reference (default: HEAD)

        Returns:
            Dictionary with commit information (hash, author, date, message)

        Raises:
            GitOperationError: If command fails
        """
        # Get commit hash
        hash_result = self._run_git(["rev-parse", ref])
        commit_hash = hash_result.stdout.strip()

        # Get commit details
        format_str = "%an%n%ae%n%ai%n%s"
        show_result = self._run_git(["show", "-s", f"--format={format_str}", ref])
        lines = show_result.stdout.strip().split("\n")

        return {
            "hash": commit_hash,
            "author_name": lines[0] if len(lines) > 0 else "",
            "author_email": lines[1] if len(lines) > 1 else "",
            "date": lines[2] if len(lines) > 2 else "",
            "message": lines[3] if len(lines) > 3 else "",
        }
