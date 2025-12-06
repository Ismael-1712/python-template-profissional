"""FileSystem Abstraction Layer for Testable I/O Operations.

This module provides a protocol-based abstraction for filesystem operations,
enabling dependency injection and clean unit testing without touching the disk.

Design Pattern: Adapter Pattern + Protocol-based Dependency Injection
Motivation: Decouple business logic from I/O to enable fast, reliable unit tests

Classes:
    FileSystemAdapter: Protocol defining filesystem interface
    RealFileSystem: Production implementation using real disk operations
    MemoryFileSystem: In-memory implementation for unit testing

Usage:
    # Production code
    fs = RealFileSystem()
    content = fs.read_text(Path("config.yaml"))

    # Test code
    fs = MemoryFileSystem()
    fs.write_text(Path("config.yaml"), "test: true")
    assert fs.exists(Path("config.yaml"))

Author: DevOps Engineering Team
License: MIT
Version: 1.0.0
"""

from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class FileSystemAdapter(Protocol):
    """Protocol defining the filesystem operations interface.

    This protocol allows both real filesystem and in-memory implementations
    to be used interchangeably, enabling true unit testing without I/O.

    All implementations must support pathlib.Path objects for type safety.
    """

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Read text content from a file.

        Args:
            path: Path to the file to read
            encoding: Text encoding (default: utf-8)

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If the file does not exist
            UnicodeDecodeError: If encoding fails
        """
        ...

    def write_text(
        self,
        path: Path,
        content: str,
        encoding: str = "utf-8",
    ) -> None:
        """Write text content to a file.

        Creates parent directories automatically if they don't exist.

        Args:
            path: Path to the file to write
            content: Text content to write
            encoding: Text encoding (default: utf-8)

        Raises:
            OSError: If write operation fails
        """
        ...

    def exists(self, path: Path) -> bool:
        """Check if a path exists (file or directory).

        Args:
            path: Path to check

        Returns:
            True if path exists, False otherwise
        """
        ...

    def is_file(self, path: Path) -> bool:
        """Check if path is a file.

        Args:
            path: Path to check

        Returns:
            True if path is a file, False otherwise
        """
        ...

    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory.

        Args:
            path: Path to check

        Returns:
            True if path is a directory, False otherwise
        """
        ...

    def mkdir(
        self,
        path: Path,
        parents: bool = True,
        exist_ok: bool = True,
    ) -> None:
        """Create a directory.

        Args:
            path: Path to the directory to create
            parents: If True, create parent directories as needed
            exist_ok: If True, don't raise error if directory exists

        Raises:
            FileExistsError: If exist_ok=False and directory exists
            OSError: If directory creation fails
        """
        ...

    def glob(self, path: Path, pattern: str) -> list[Path]:
        """Find files matching a glob pattern.

        Args:
            path: Directory path to search in
            pattern: Glob pattern (e.g., "*.py", "test_*.py")

        Returns:
            List of Path objects matching the pattern

        Example:
            >>> fs.glob(Path("tests"), "test_*.py")
            [Path("tests/test_foo.py"), Path("tests/test_bar.py")]
        """
        ...

    def rglob(self, path: Path, pattern: str) -> list[Path]:
        """Find files matching a pattern recursively.

        Equivalent to path.rglob(pattern) but works through the adapter.
        Searches recursively in all subdirectories under the given path.

        Args:
            path: Directory path to search in
            pattern: Glob pattern (e.g., "*.py", "test_*.py")

        Returns:
            List of Path objects matching the pattern recursively

        Example:
            >>> fs.rglob(Path("tests"), "*.py")
            [Path("tests/test_foo.py"), Path("tests/sub/test_bar.py")]
        """
        ...

    def copy(self, src: Path, dst: Path) -> None:
        """Copy a file from source to destination.

        Preserves file metadata (timestamps, permissions).

        Args:
            src: Source file path
            dst: Destination file path

        Raises:
            FileNotFoundError: If source file does not exist
            OSError: If copy operation fails
        """
        ...


class RealFileSystem:
    """Production filesystem implementation using real disk operations.

    Delegates all operations to pathlib.Path and shutil for actual I/O.
    Use this implementation in production code.

    Thread Safety:
        Operations are thread-safe at the OS level, but concurrent writes
        to the same file may result in race conditions. Use atomic writes
        (see scripts.utils.atomic) for critical data.

    Example:
        >>> fs = RealFileSystem()
        >>> fs.write_text(Path("config.yaml"), "key: value")
        >>> content = fs.read_text(Path("config.yaml"))
    """

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Read text content from a file on disk.

        Args:
            path: Path to the file to read
            encoding: Text encoding (default: utf-8)

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If the file does not exist
            UnicodeDecodeError: If encoding fails
        """
        return path.read_text(encoding=encoding)

    def write_text(
        self,
        path: Path,
        content: str,
        encoding: str = "utf-8",
    ) -> None:
        """Write text content to a file on disk.

        Automatically creates parent directories if they don't exist.

        Args:
            path: Path to the file to write
            content: Text content to write
            encoding: Text encoding (default: utf-8)

        Raises:
            OSError: If write operation fails
        """
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)

    def exists(self, path: Path) -> bool:
        """Check if a path exists on disk.

        Args:
            path: Path to check

        Returns:
            True if path exists, False otherwise
        """
        return path.exists()

    def is_file(self, path: Path) -> bool:
        """Check if path is a file on disk.

        Args:
            path: Path to check

        Returns:
            True if path is a file, False otherwise
        """
        return path.is_file()

    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory on disk.

        Args:
            path: Path to check

        Returns:
            True if path is a directory, False otherwise
        """
        return path.is_dir()

    def mkdir(
        self,
        path: Path,
        parents: bool = True,
        exist_ok: bool = True,
    ) -> None:
        """Create a directory on disk.

        Args:
            path: Path to the directory to create
            parents: If True, create parent directories as needed
            exist_ok: If True, don't raise error if directory exists

        Raises:
            FileExistsError: If exist_ok=False and directory exists
            OSError: If directory creation fails
        """
        path.mkdir(parents=parents, exist_ok=exist_ok)

    def glob(self, path: Path, pattern: str) -> list[Path]:
        """Find files matching a glob pattern on disk.

        Args:
            path: Directory path to search in
            pattern: Glob pattern (e.g., "*.py", "test_*.py")

        Returns:
            List of Path objects matching the pattern

        Example:
            >>> fs = RealFileSystem()
            >>> fs.glob(Path("tests"), "test_*.py")
            [Path("tests/test_foo.py"), Path("tests/test_bar.py")]
        """
        return list(path.glob(pattern))

    def rglob(self, path: Path, pattern: str) -> list[Path]:
        """Find files matching a pattern recursively on disk.

        Args:
            path: Directory path to search in
            pattern: Glob pattern (e.g., "*.py", "test_*.py")

        Returns:
            List of Path objects matching the pattern recursively

        Example:
            >>> fs = RealFileSystem()
            >>> fs.rglob(Path("tests"), "*.py")
            [Path("tests/test_foo.py"), Path("tests/sub/test_bar.py")]
        """
        return list(path.rglob(pattern))

    def copy(self, src: Path, dst: Path) -> None:
        """Copy a file from source to destination on disk.

        Preserves file metadata (timestamps, permissions) using shutil.copy2.

        Args:
            src: Source file path
            dst: Destination file path

        Raises:
            FileNotFoundError: If source file does not exist
            OSError: If copy operation fails
        """
        # Ensure destination parent directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


class MemoryFileSystem:
    """In-memory filesystem implementation for fast unit testing.

    Stores all files in a dictionary, enabling tests to run without
    touching the disk. This results in:
    - 10-100x faster test execution
    - No filesystem cleanup needed
    - Complete isolation between tests
    - Deterministic behavior

    Limitations:
        - Does not support binary files (text only)
        - Glob patterns are simplified (basic * and ? wildcards)
        - No filesystem metadata (permissions, timestamps)
        - Not thread-safe (use separate instances per thread)

    Example:
        >>> fs = MemoryFileSystem()
        >>> fs.write_text(Path("test.txt"), "hello")
        >>> assert fs.read_text(Path("test.txt")) == "hello"
        >>> assert fs.exists(Path("test.txt"))
    """

    def __init__(self) -> None:
        """Initialize empty in-memory filesystem."""
        self._files: dict[Path, str] = {}
        self._dirs: set[Path] = set()

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Read text content from memory.

        Args:
            path: Path to the file to read
            encoding: Ignored (memory storage is already unicode)

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If the file does not exist in memory
        """
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path]

    def write_text(
        self,
        path: Path,
        content: str,
        encoding: str = "utf-8",
    ) -> None:
        """Write text content to memory.

        Automatically creates parent directories in memory.

        Args:
            path: Path to the file to write
            content: Text content to write
            encoding: Ignored (memory storage is already unicode)
        """
        # Auto-create parent directories
        self._ensure_parent_dirs(path)
        self._files[path] = content

    def exists(self, path: Path) -> bool:
        """Check if a path exists in memory.

        Args:
            path: Path to check

        Returns:
            True if path exists (as file or directory), False otherwise
        """
        return path in self._files or path in self._dirs

    def is_file(self, path: Path) -> bool:
        """Check if path is a file in memory.

        Args:
            path: Path to check

        Returns:
            True if path is a file, False otherwise
        """
        return path in self._files

    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory in memory.

        Args:
            path: Path to check

        Returns:
            True if path is a directory, False otherwise
        """
        return path in self._dirs

    def mkdir(
        self,
        path: Path,
        parents: bool = True,
        exist_ok: bool = True,
    ) -> None:
        """Create a directory in memory.

        Args:
            path: Path to the directory to create
            parents: If True, create parent directories as needed
            exist_ok: If True, don't raise error if directory exists

        Raises:
            FileExistsError: If exist_ok=False and directory exists
        """
        if path in self._dirs and not exist_ok:
            raise FileExistsError(f"Directory already exists: {path}")

        if parents:
            # Create all parent directories
            current = path
            dirs_to_create = []
            while current.parent != current:
                dirs_to_create.append(current)
                current = current.parent
            # Add in reverse order (parent first)
            for directory in reversed(dirs_to_create):
                self._dirs.add(directory)
        else:
            self._dirs.add(path)

    def glob(self, path: Path, pattern: str) -> list[Path]:
        """Find files matching a glob pattern in memory.

        Supports wildcards (* and ?) via fnmatch, and recursive patterns (**).

        Args:
            path: Directory path to search in
            pattern: Glob pattern (e.g., "*.py", "**/*.py", "test_*.py")

        Returns:
            List of Path objects matching the pattern

        Example:
            >>> fs = MemoryFileSystem()
            >>> fs.write_text(Path("tests/test_foo.py"), "")
            >>> fs.glob(Path("tests"), "test_*.py")
            [Path("tests/test_foo.py")]
            >>> fs.glob(Path("tests"), "**/*.py")
            [Path("tests/test_foo.py"), Path("tests/subdir/bar.py")]
        """
        results: list[Path] = []

        # Check if pattern is recursive
        is_recursive = pattern.startswith("**/")
        file_pattern = pattern[3:] if is_recursive else pattern

        # Search in files
        for file_path in self._files:
            # Check if file is under the search path
            try:
                relative = file_path.relative_to(path)

                if is_recursive:
                    # Recursive: match anywhere under path
                    if fnmatch.fnmatch(file_path.name, file_pattern):
                        results.append(file_path)
                # Non-recursive: match only direct children
                elif "/" not in str(relative) and "\\" not in str(relative):
                    if fnmatch.fnmatch(file_path.name, file_pattern):
                        results.append(file_path)
            except ValueError:
                # File is not under the search path
                continue

        return sorted(results)

    def rglob(self, path: Path, pattern: str) -> list[Path]:
        """Find files matching a pattern recursively in memory.

        Args:
            path: Directory path to search in
            pattern: Glob pattern (e.g., "*.py", "test_*.py")

        Returns:
            List of Path objects matching the pattern recursively

        Example:
            >>> fs = MemoryFileSystem()
            >>> fs.write_text(Path("tests/sub/test.py"), "")
            >>> fs.rglob(Path("tests"), "*.py")
            [Path("tests/sub/test.py")]
        """
        # Reuse existing glob logic with recursive pattern
        return self.glob(path, f"**/{pattern}")

    def copy(self, src: Path, dst: Path) -> None:
        """Copy a file in memory.

        Args:
            src: Source file path
            dst: Destination file path

        Raises:
            FileNotFoundError: If source file does not exist
        """
        if src not in self._files:
            raise FileNotFoundError(f"Source file not found: {src}")

        # Auto-create parent directories for destination
        self._ensure_parent_dirs(dst)
        self._files[dst] = self._files[src]

    def _ensure_parent_dirs(self, path: Path) -> None:
        """Ensure all parent directories exist in memory.

        Args:
            path: File path whose parents should be created
        """
        current = path.parent
        while current.parent != current:
            self._dirs.add(current)
            current = current.parent


__all__ = [
    "FileSystemAdapter",
    "MemoryFileSystem",
    "RealFileSystem",
]
