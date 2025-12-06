"""File Discovery and Scanning for Code Audit System.

This module handles the discovery of Python files to be audited,
with support for glob patterns, path exclusion, and workspace traversal.

Classes:
    FileScanner: Scans workspace for Python files based on configuration

Author: DevOps Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
from pathlib import Path

from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem

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
        fs_adapter: FileSystemAdapter | None = None,
    ) -> None:
        """Initialize the file scanner.

        Args:
            workspace_root: Root directory of the workspace
            scan_paths: List of relative paths to scan (e.g., ['src/', 'tests/'])
            file_patterns: List of glob patterns (e.g., ['*.py'])
            exclude_paths: List of path patterns to exclude
                (e.g., ['.venv/', '__pycache__/'])
            fs_adapter: FileSystemAdapter for I/O operations (default: RealFileSystem)
        """
        self.workspace_root = workspace_root.resolve()
        self.scan_paths = scan_paths
        self.file_patterns = file_patterns
        self.exclude_paths = exclude_paths
        self.fs = fs_adapter or RealFileSystem()

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
            if not self.fs.exists(scan_dir):
                logger.warning("Scan path does not exist: %s", scan_dir)
                continue

            for pattern in self.file_patterns:
                # Use recursive glob pattern for adapter compatibility
                recursive_pattern = f"**/{pattern}"
                matched_files = self.fs.glob(scan_dir, recursive_pattern)

                for file_path in matched_files:
                    # Skip excluded paths
                    if self._should_exclude(file_path):
                        continue
                    # Ensure it's a file (not directory)
                    if self.fs.is_file(file_path):
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
