"""File Discovery and Scanning for Code Audit System.

This module handles the discovery of Python files to be audited,
with support for glob patterns, path exclusion, and workspace traversal.

Classes:
    FileScanner: Scans workspace for Python files based on configuration

Author: DevOps Engineering Team
License: MIT
"""

import logging
from pathlib import Path

# Configure module logger
logger = logging.getLogger(__name__)


class FileScanner:
    """Handles file discovery for code auditing.

    Scans a workspace directory for Python files matching specified patterns,
    while excluding certain paths like virtual environments and cache directories.
    """

    def __init__(
        self,
        workspace_root: Path,
        scan_paths: list[str],
        file_patterns: list[str],
        exclude_paths: list[str],
    ) -> None:
        """Initialize the file scanner.

        Args:
            workspace_root: Root directory of the workspace
            scan_paths: List of relative paths to scan (e.g., ['src/', 'tests/'])
            file_patterns: List of glob patterns (e.g., ['*.py'])
            exclude_paths: List of path patterns to exclude
                (e.g., ['.venv/', '__pycache__/'])
        """
        self.workspace_root = workspace_root.resolve()
        self.scan_paths = scan_paths
        self.file_patterns = file_patterns
        self.exclude_paths = exclude_paths

    def scan(self) -> list[Path]:
        """Scan workspace for Python files matching criteria.

        Returns:
            List of Path objects for Python files found

        Example:
            >>> scanner = FileScanner(Path('.'), ['src/'], ['*.py'], ['.venv/'])
            >>> files = scanner.scan()
            >>> print(f"Found {len(files)} Python files")
        """
        python_files = []

        for scan_path in self.scan_paths:
            scan_dir = self.workspace_root / scan_path
            if not scan_dir.exists():
                logger.warning("Scan path does not exist: %s", scan_dir)
                continue

            for pattern in self.file_patterns:
                for file_path in scan_dir.rglob(pattern):
                    # Skip excluded paths
                    if self._should_exclude(file_path):
                        continue
                    python_files.append(file_path)

        logger.info("Found %d Python files to audit (Full Scan)", len(python_files))
        return python_files

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if a file path should be excluded.

        Args:
            file_path: Path to check

        Returns:
            True if the path should be excluded, False otherwise
        """
        file_path_str = str(file_path)
        return any(exclude in file_path_str for exclude in self.exclude_paths)


def scan_workspace(
    workspace_root: Path,
    scan_paths: list[str],
    file_patterns: list[str],
    exclude_paths: list[str],
) -> list[Path]:
    """Convenience function to scan workspace for Python files.

    Args:
        workspace_root: Root directory of the workspace
        scan_paths: List of relative paths to scan
        file_patterns: List of glob patterns to match
        exclude_paths: List of path patterns to exclude

    Returns:
        List of Path objects for Python files found

    Example:
        >>> files = scan_workspace(
        ...     Path('.'),
        ...     ['src/', 'tests/'],
        ...     ['*.py'],
        ...     ['.venv/', '__pycache__/']
        ... )
    """
    scanner = FileScanner(workspace_root, scan_paths, file_patterns, exclude_paths)
    return scanner.scan()
