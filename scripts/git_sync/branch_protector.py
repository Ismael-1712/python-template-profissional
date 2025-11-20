"""Branch protection validation for Smart Git Sync.

This module provides validation for protected branches, ensuring that
direct pushes to protected branches are prevented according to the
configured branch protection rules.
"""

import fnmatch
import logging
from typing import Any

from scripts.git_sync.exceptions import SyncError

logger = logging.getLogger(__name__)


class BranchProtector:
    """Validates branch protection rules before Git operations.

    This class encapsulates branch protection logic, checking if a branch
    is protected and whether direct pushes are allowed based on configuration.

    Attributes:
        protected_branches: List of branch patterns (supports wildcards)
        allow_direct_push: Whether direct pushes to protected branches are allowed
        require_pr: Whether pull requests are required for protected branches

    Example:
        >>> protector = BranchProtector(
        ...     protected_branches=["main", "release/*"],
        ...     allow_direct_push=False,
        ... )
        >>> protector.validate_push("main")  # Raises SyncError
        >>> protector.validate_push("feature/new-feature")  # OK
    """

    def __init__(
        self,
        protected_branches: list[str] | None = None,
        allow_direct_push: bool = False,
        require_pr: bool = True,
    ) -> None:
        """Initialize branch protector.

        Args:
            protected_branches: List of protected branch patterns (supports wildcards).
                               Default: ["main", "master", "develop", "release/*"]
            allow_direct_push: If True, allows direct push to protected branches.
                              Default: False (blocks direct push)
            require_pr: If True, requires pull request for protected branches.
                       Default: True
        """
        self.protected_branches = protected_branches or [
            "main",
            "master",
            "develop",
            "release/*",
        ]
        self.allow_direct_push = allow_direct_push
        self.require_pr = require_pr

        logger.debug(
            "BranchProtector initialized: protected=%s, allow_direct_push=%s",
            self.protected_branches,
            self.allow_direct_push,
        )

    def is_protected(self, branch: str) -> bool:
        """Check if a branch matches any protected branch pattern.

        Supports wildcard patterns using fnmatch (e.g., "release/*").

        Args:
            branch: Branch name to check

        Returns:
            True if branch is protected, False otherwise

        Example:
            >>> protector = BranchProtector(protected_branches=["main", "release/*"])
            >>> protector.is_protected("main")
            True
            >>> protector.is_protected("release/v1.0")
            True
            >>> protector.is_protected("feature/test")
            False
        """
        for pattern in self.protected_branches:
            if fnmatch.fnmatch(branch, pattern):
                logger.debug(
                    "Branch '%s' matches protected pattern '%s'",
                    branch,
                    pattern,
                )
                return True
        return False

    def validate_push(self, branch: str) -> None:
        """Validate if direct push to the branch is allowed.

        This method checks if the branch is protected and whether direct
        pushes are permitted based on configuration.

        Args:
            branch: Branch name to validate

        Raises:
            SyncError: If branch is protected and direct push is not allowed

        Example:
            >>> protector = BranchProtector(allow_direct_push=False)
            >>> protector.validate_push("main")  # Raises SyncError
            >>> protector.validate_push("feature/test")  # OK
        """
        if not self.is_protected(branch):
            logger.debug("Branch '%s' is not protected, push allowed", branch)
            return

        # Branch is protected
        if self.allow_direct_push:
            logger.warning(
                "Branch '%s' is protected, but direct push is allowed by configuration",
                branch,
            )
            return

        # Protected branch + direct push not allowed = ERROR
        logger.error(
            "🛑 OPERAÇÃO PROIBIDA: Push direto na branch protegida '%s'",
            branch,
        )
        logger.error("A branch '%s' está protegida por regras de segurança.", branch)
        logger.error("Este script não pode fazer push direto em branches protegidas.")

        if self.require_pr:
            logger.warning(
                "Use o 'Fluxo de Trabalho com Pull Request': "
                "Crie uma feature branch, faça commit, abra um PR e solicite revisão.",
            )

        msg = (
            f"Tentativa de push direto na branch protegida '{branch}' bloqueada. "
            f"Configure 'allow_direct_push: true' ou use uma feature branch com PR."
        )
        raise SyncError(msg)

    def get_protected_branches(self) -> list[str]:
        """Get the list of protected branch patterns.

        Returns:
            List of protected branch patterns

        Example:
            >>> protector = BranchProtector()
            >>> patterns = protector.get_protected_branches()
            >>> print(patterns)
            ['main', 'master', 'develop', 'release/*']
        """
        return self.protected_branches.copy()

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "BranchProtector":
        """Create BranchProtector from configuration dictionary.

        Args:
            config: Configuration dictionary with 'branch_protection' section

        Returns:
            Configured BranchProtector instance

        Example:
            >>> config = {
            ...     "branch_protection": {
            ...         "protected_branches": ["main", "release/*"],
            ...         "allow_direct_push": False,
            ...         "require_pr": True,
            ...     }
            ... }
            >>> protector = BranchProtector.from_config(config)
        """
        branch_protection = config.get("branch_protection", {})

        return cls(
            protected_branches=branch_protection.get("protected_branches"),
            allow_direct_push=branch_protection.get("allow_direct_push", False),
            require_pr=branch_protection.get("require_pr", True),
        )
