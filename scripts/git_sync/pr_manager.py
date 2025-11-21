"""Pull Request management for Smart Git Sync.

This module provides automation for creating Pull Requests on GitHub/GitLab,
enabling safe workflows for protected branches.
"""

import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from scripts.git_sync.exceptions import SyncError

logger = logging.getLogger(__name__)


class PRManager:
    """Manages Pull Request creation and automation.

    This class provides integration with GitHub CLI (gh) or manual PR URL
    generation for creating pull requests when working with protected branches.

    Attributes:
        provider: PR provider ("github" or "gitlab")
        api_token_env: Environment variable name for API token
        default_reviewers: List of default reviewer usernames
        auto_assign: Whether to auto-assign the PR creator
        labels: List of labels to apply to PRs
        workspace_root: Root directory of the Git repository

    Example:
        >>> manager = PRManager.from_config(config)
        >>> pr_url = manager.create_pr(
        ...     source_branch="feature/new-feature",
        ...     target_branch="main",
        ...     title="Add new feature",
        ...     body="This PR adds a new feature",
        ... )
    """

    def __init__(
        self,
        workspace_root: Path,
        provider: str = "github",
        api_token_env: str = "GITHUB_TOKEN",
        default_reviewers: list[str] | None = None,
        auto_assign: bool = True,
        labels: list[str] | None = None,
    ) -> None:
        """Initialize PR manager.

        Args:
            workspace_root: Root directory of the Git repository
            provider: PR provider ("github" or "gitlab")
            api_token_env: Environment variable name for API token
            default_reviewers: List of default reviewer usernames
            auto_assign: Whether to auto-assign the PR creator
            labels: List of labels to apply to PRs
        """
        self.workspace_root = workspace_root.resolve()
        self.provider = provider.lower()
        self.api_token_env = api_token_env
        self.default_reviewers = default_reviewers or []
        self.auto_assign = auto_assign
        self.labels = labels or []

        logger.debug(
            "PRManager initialized: provider=%s, workspace=%s",
            self.provider,
            self.workspace_root,
        )

    def has_gh_cli(self) -> bool:
        """Check if GitHub CLI (gh) is available in PATH.

        Returns:
            True if gh command is available, False otherwise

        Example:
            >>> manager = PRManager(Path("."))
            >>> if manager.has_gh_cli():
            ...     print("GitHub CLI is available")
        """
        gh_path = shutil.which("gh")
        if gh_path:
            logger.debug("GitHub CLI found at: %s", gh_path)
            return True
        logger.debug("GitHub CLI (gh) not found in PATH")
        return False

    def _get_remote_url(self) -> str:
        """Get the remote repository URL.

        Returns:
            Remote URL (e.g., "https://github.com/user/repo")

        Raises:
            SyncError: If unable to determine remote URL
        """
        try:
            result = subprocess.run(  # noqa: subprocess
                ["git", "remote", "get-url", "origin"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            url = result.stdout.strip()

            # Convert SSH URL to HTTPS
            if url.startswith("git@github.com:"):
                url = url.replace("git@github.com:", "https://github.com/")
            url = url.removesuffix(".git")

            logger.debug("Remote URL: %s", url)
            return url

        except subprocess.CalledProcessError as e:
            msg = f"Failed to get remote URL: {e}"
            raise SyncError(msg) from e

    def _parse_repo_info(self, remote_url: str) -> tuple[str, str]:
        """Parse owner and repository name from remote URL.

        Args:
            remote_url: Git remote URL

        Returns:
            Tuple of (owner, repo_name)

        Raises:
            SyncError: If URL format is invalid
        """
        # Match GitHub/GitLab URL patterns
        patterns = [
            r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",
            r"gitlab\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",
        ]

        for pattern in patterns:
            match = re.search(pattern, remote_url)
            if match:
                owner, repo = match.groups()
                logger.debug("Parsed repo: %s/%s", owner, repo)
                return owner, repo

        msg = f"Could not parse repository info from URL: {remote_url}"
        raise SyncError(msg)

    def _generate_manual_pr_url(
        self,
        source_branch: str,
        target_branch: str,
    ) -> str:
        """Generate manual PR creation URL.

        Args:
            source_branch: Source branch name
            target_branch: Target branch name

        Returns:
            URL for manual PR creation

        Example:
            >>> manager = PRManager(Path("."))
            >>> url = manager._generate_manual_pr_url("feature/test", "main")
            >>> print(url)
            https://github.com/owner/repo/compare/main...feature/test
        """
        remote_url = self._get_remote_url()
        owner, repo = self._parse_repo_info(remote_url)

        if self.provider == "github":
            url = (
                f"https://github.com/{owner}/{repo}/"
                f"compare/{target_branch}...{source_branch}"
            )
        elif self.provider == "gitlab":
            url = (
                f"https://gitlab.com/{owner}/{repo}/"
                f"-/merge_requests/new?"
                f"merge_request[source_branch]={source_branch}&"
                f"merge_request[target_branch]={target_branch}"
            )
        else:
            url = f"{remote_url}/compare/{target_branch}...{source_branch}"

        logger.debug("Generated manual PR URL: %s", url)
        return url

    def create_pr(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
        body: str,
    ) -> str:
        """Create a Pull Request using GitHub CLI or generate manual URL.

        This method attempts to create a PR using GitHub CLI (gh) if available.
        If gh is not installed, it generates a manual PR creation URL.

        Args:
            source_branch: Source branch name (e.g., "feature/new-feature")
            target_branch: Target branch name (e.g., "main")
            title: PR title
            body: PR description/body

        Returns:
            PR URL or instructions message

        Raises:
            SyncError: If PR creation fails

        Example:
            >>> manager = PRManager(Path("."))
            >>> pr_url = manager.create_pr(
            ...     "feature/test", "main",
            ...     "Test PR", "This is a test PR"
            ... )
        """
        logger.info(
            "Creating PR: %s -> %s",
            source_branch,
            target_branch,
        )

        # Try using GitHub CLI if available
        if self.has_gh_cli():
            return self._create_pr_with_gh(
                source_branch,
                target_branch,
                title,
                body,
            )

        # Fallback: Generate manual PR URL
        manual_url = self._generate_manual_pr_url(source_branch, target_branch)

        logger.warning("GitHub CLI (gh) not found - manual PR creation required")
        logger.info(
            "💡 Dica: Instale o GitHub CLI ('gh') para automatizar "
            "a criação de Pull Requests.",
        )
        logger.info("   Veja: https://cli.github.com/")
        logger.info("📝 Please create PR manually at: %s", manual_url)

        return (
            f"🔗 PR URL: {manual_url}\n"
            f"📋 Title: {title}\n"
            f"📄 Body: {body}\n\n"
            "⚠️  GitHub CLI (gh) not installed. "
            "Please open the URL above to create the PR manually.\n\n"
            "💡 Dica: Instale o GitHub CLI para automatizar PRs: https://cli.github.com/"
        )

    def _create_pr_with_gh(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
        body: str,
    ) -> str:
        """Create PR using GitHub CLI.

        Args:
            source_branch: Source branch name
            target_branch: Target branch name
            title: PR title
            body: PR description

        Returns:
            PR URL from GitHub CLI output

        Raises:
            SyncError: If gh command fails
        """
        command = [
            "gh",
            "pr",
            "create",
            "--base",
            target_branch,
            "--head",
            source_branch,
            "--title",
            title,
            "--body",
            body,
        ]

        # Add labels if configured
        for label in self.labels:
            command.extend(["--label", label])

        # Add reviewers if configured
        for reviewer in self.default_reviewers:
            command.extend(["--reviewer", reviewer])

        try:
            logger.debug("Executing: %s", " ".join(command))
            result = subprocess.run(  # noqa: subprocess
                command,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )

            # Extract PR URL from output
            pr_url = result.stdout.strip().split("\n")[-1]
            logger.info("✅ PR created successfully: %s", pr_url)
            return pr_url

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            logger.exception("Failed to create PR with gh: %s", error_msg)

            # Try to provide helpful error messages
            if "already exists" in error_msg.lower():
                msg = (
                    f"PR from {source_branch} to {target_branch} already exists. "
                    "Check existing PRs with: gh pr list"
                )
            elif "authentication" in error_msg.lower():
                msg = "GitHub authentication failed. Run: gh auth login"
            else:
                msg = f"Failed to create PR: {error_msg}"

            raise SyncError(msg) from e

    def check_existing_pr(
        self,
        source_branch: str,
        target_branch: str,
    ) -> str | None:
        """Check if a PR already exists for the given branches.

        Args:
            source_branch: Source branch name
            target_branch: Target branch name

        Returns:
            PR URL if exists, None otherwise

        Example:
            >>> manager = PRManager(Path("."))
            >>> existing_pr = manager.check_existing_pr("feature/test", "main")
            >>> if existing_pr:
            ...     print(f"PR already exists: {existing_pr}")
        """
        if not self.has_gh_cli():
            logger.debug("GitHub CLI not available, cannot check existing PRs")
            return None

        try:
            command = [
                "gh",
                "pr",
                "list",
                "--head",
                source_branch,
                "--base",
                target_branch,
                "--json",
                "url",
                "--jq",
                ".[0].url",
            ]

            result = subprocess.run(  # noqa: subprocess
                command,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            pr_url = result.stdout.strip()
            if pr_url and pr_url != "null":
                logger.info("Found existing PR: %s", pr_url)
                return pr_url

            logger.debug("No existing PR found")
            return None

        except subprocess.TimeoutExpired:
            logger.warning("Timeout checking for existing PRs")
            return None
        except (subprocess.SubprocessError, OSError) as e:
            logger.warning("Error checking for existing PRs: %s", e)
            return None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "PRManager":
        """Create PRManager from configuration dictionary.

        Args:
            config: Configuration dictionary with 'pull_request' section

        Returns:
            Configured PRManager instance

        Example:
            >>> config = {
            ...     "pull_request": {
            ...         "provider": "github",
            ...         "api_token_env": "GITHUB_TOKEN",
            ...         "default_reviewers": ["reviewer1"],
            ...         "labels": ["automated-sync"],
            ...     }
            ... }
            >>> manager = PRManager.from_config(config)
        """
        pr_config = config.get("pull_request", {})
        workspace_root = config.get("workspace_root", Path.cwd())

        return cls(
            workspace_root=Path(workspace_root),
            provider=pr_config.get("provider", "github"),
            api_token_env=pr_config.get("api_token_env", "GITHUB_TOKEN"),
            default_reviewers=pr_config.get("default_reviewers", []),
            auto_assign=pr_config.get("auto_assign", True),
            labels=pr_config.get("labels", []),
        )
