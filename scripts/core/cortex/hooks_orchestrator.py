"""Git Hooks Orchestrator for CORTEX System.

Automated management of Git hooks for maintaining fresh AI context
after repository operations.

This module extracts hook installation logic from the CLI layer.

Author: GEM & SRE Team
License: MIT
"""

from __future__ import annotations

import logging
from pathlib import Path

# Configure module logger
logger = logging.getLogger(__name__)


class GitDirectoryNotFoundError(Exception):
    """Raised when .git directory cannot be found."""


class HookInstallationError(Exception):
    """Raised when hook installation fails."""


class HooksOrchestrator:
    """Orchestrator for Git hooks installation and management.

    Responsibilities:
    - Detect and validate Git repository structure
    - Generate Git hook scripts from templates
    - Install hooks with backup of existing files
    - Make hook files executable (Unix platforms)

    Examples:
        >>> orchestrator = HooksOrchestrator(project_root=Path("/project"))
        >>> git_dir = orchestrator.detect_git_directory()
        >>> installed = orchestrator.install_cortex_hooks()
        >>> print(installed)  # ["post-merge", "post-checkout", "post-rewrite"]
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize HooksOrchestrator.

        Args:
            project_root: Root directory of the Git repository
        """
        self.project_root = project_root
        logger.info(f"HooksOrchestrator initialized with root: {project_root}")

    def detect_git_directory(self) -> Path:
        """Detect and validate .git directory in project.

        Returns:
            Path to .git directory

        Raises:
            GitDirectoryNotFoundError: If .git directory not found

        Examples:
            >>> git_dir = orchestrator.detect_git_directory()
            >>> print(git_dir)  # Path("/project/.git")
        """
        git_dir = self.project_root / ".git"

        if not git_dir.exists():
            msg = f".git directory not found in {self.project_root}"
            logger.error(msg)
            raise GitDirectoryNotFoundError(msg)

        if not git_dir.is_dir():
            msg = f".git exists but is not a directory (submodule?): {git_dir}"
            logger.error(msg)
            raise GitDirectoryNotFoundError(msg)

        logger.debug(f"Detected .git directory: {git_dir}")
        return git_dir

    def generate_hook_script(
        self,
        hook_type: str,
        command: str,
    ) -> str:
        """Generate Git hook script content from template.

        Creates a bash script that checks for command availability and
        executes it after Git operations.

        Args:
            hook_type: Type of hook (e.g., "post-merge", "post-checkout")
            command: Command to execute (e.g., "cortex map --output .cortex/
                context.json")

        Returns:
            Bash script content as string

        Examples:
            >>> script = orchestrator.generate_hook_script(
            ...     "post-merge",
            ...     "cortex map --output .cortex/context.json"
            ... )
            >>> print(script)  # Contains #!/bin/bash and command
        """
        script = f"""#!/bin/bash
# Auto-generated CORTEX {hook_type} hook
# Maintains AI context fresh after Git operations

# Check if command exists
if command -v {command.split()[0]} >/dev/null 2>&1; then
    {command} || true  # Don't fail Git operation if command fails
fi

exit 0
"""
        logger.debug(f"Generated {hook_type} hook script ({len(script)} chars)")
        return script

    def install_hook(
        self,
        hook_name: str,
        script_content: str,
        hooks_dir: Path,
        backup: bool = True,
    ) -> None:
        r"""Install a single Git hook with optional backup.

        Writes hook script to file, makes it executable (Unix), and
        optionally backs up existing hook.

        Args:
            hook_name: Name of hook (e.g., "post-merge")
            script_content: Bash script content to write
            hooks_dir: Directory where hooks are stored
            backup: Whether to backup existing hook file

        Raises:
            HookInstallationError: If hook installation fails

        Examples:
            >>> orchestrator.install_hook(
            ...     "post-merge",
            ...     "#!/bin/bash\\necho test",
            ...     Path(".git/hooks")
            ... )
        """
        hook_path = hooks_dir / hook_name

        # Backup existing hook if requested
        if backup and hook_path.exists():
            self.backup_existing_hook(hook_path)

        # Write hook script
        try:
            hook_path.write_text(script_content, encoding="utf-8")
            logger.info(f"Wrote {hook_name} hook to {hook_path}")
        except OSError as e:
            msg = f"Failed to write {hook_name} hook: {e}"
            logger.error(msg)
            raise HookInstallationError(msg) from e

        # Make executable
        self.make_executable(hook_path)

    def make_executable(self, file_path: Path) -> None:
        """Make file executable on Unix platforms.

        Sets file permissions to 0o755 (rwxr-xr-x). On Windows, this
        operation may have no effect or raise an exception.

        Args:
            file_path: Path to file to make executable

        Raises:
            HookInstallationError: If chmod operation fails

        Examples:
            >>> orchestrator.make_executable(Path(".git/hooks/post-merge"))
        """
        try:
            file_path.chmod(0o755)
            logger.debug(f"Made executable: {file_path}")
        except (OSError, NotImplementedError) as e:
            # Windows may not support chmod or operation may fail
            msg = f"Failed to make {file_path} executable: {e}"
            logger.warning(msg)
            raise HookInstallationError(msg) from e

    def backup_existing_hook(self, hook_path: Path, suffix: str = ".backup") -> Path:
        """Create backup of existing hook file.

        Renames existing hook by adding suffix to preserve it.

        Args:
            hook_path: Path to existing hook file
            suffix: Suffix to add to backup file

        Returns:
            Path to backup file

        Raises:
            HookInstallationError: If backup operation fails

        Examples:
            >>> backup = orchestrator.backup_existing_hook(
            ...     Path(".git/hooks/post-merge")
            ... )
            >>> print(backup)  # Path(".git/hooks/post-merge.backup")
        """
        if not hook_path.exists():
            msg = f"Cannot backup non-existent hook: {hook_path}"
            logger.error(msg)
            raise HookInstallationError(msg)

        backup_path = hook_path.with_name(hook_path.name + suffix)

        try:
            hook_path.rename(backup_path)
            logger.info(f"Backed up {hook_path.name} to {backup_path.name}")
            return backup_path
        except OSError as e:
            msg = f"Failed to backup {hook_path}: {e}"
            logger.error(msg)
            raise HookInstallationError(msg) from e

    def install_cortex_hooks(self) -> list[str]:
        """Install all CORTEX Git hooks (post-merge, post-checkout, post-rewrite).

        Main orchestration method that:
        1. Detects .git directory
        2. Creates hooks directory if needed
        3. Generates hook scripts
        4. Installs each hook with backup
        5. Makes hooks executable

        Returns:
            List of installed hook names

        Raises:
            GitDirectoryNotFoundError: If .git directory not found
            HookInstallationError: If any hook installation fails

        Examples:
            >>> installed = orchestrator.install_cortex_hooks()
            >>> print(installed)
            ["post-merge", "post-checkout", "post-rewrite"]
        """
        # Step 1: Detect .git directory
        git_dir = self.detect_git_directory()

        # Step 2: Ensure hooks directory exists
        hooks_dir = self._ensure_hooks_directory(git_dir)

        # Step 3-5: Install each hook
        hook_types = ["post-merge", "post-checkout", "post-rewrite"]
        command = "cortex map --output .cortex/context.json"
        installed = []

        for hook_type in hook_types:
            script = self.generate_hook_script(hook_type, command)
            self.install_hook(hook_type, script, hooks_dir, backup=True)
            installed.append(hook_type)
            logger.info(f"Installed {hook_type} hook")

        logger.info(
            f"Successfully installed {len(installed)} CORTEX hooks: "
            f"{', '.join(installed)}",
        )
        return installed

    def _ensure_hooks_directory(self, git_dir: Path) -> Path:
        """Ensure hooks directory exists within .git directory.

        Creates hooks directory if it doesn't exist.

        Args:
            git_dir: Path to .git directory

        Returns:
            Path to hooks directory

        Examples:
            >>> hooks_dir = orchestrator._ensure_hooks_directory(Path(".git"))
        """
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured hooks directory exists: {hooks_dir}")
        return hooks_dir
