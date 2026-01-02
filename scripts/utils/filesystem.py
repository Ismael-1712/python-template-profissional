"""Filesystem abstraction layer for easier testing and isolation."""

import shutil
import threading
from collections.abc import Iterator
from pathlib import Path


class FileSystemAdapter:
    """Abstract base class for filesystem operations."""

    def read_text(self, path: str | Path, encoding: str = "utf-8") -> str:
        """Read text from a file."""
        raise NotImplementedError

    def write_text(
        self,
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
    ) -> None:
        """Write text to a file."""
        raise NotImplementedError

    def exists(self, path: str | Path) -> bool:
        """Check if a path exists."""
        raise NotImplementedError

    def is_file(self, path: str | Path) -> bool:
        """Check if a path is a file."""
        raise NotImplementedError

    def is_dir(self, path: str | Path) -> bool:
        """Check if a path is a directory."""
        raise NotImplementedError

    def mkdir(
        self,
        path: str | Path,
        parents: bool = True,
        exist_ok: bool = True,
    ) -> None:
        """Create a directory."""
        raise NotImplementedError

    def glob(self, path: str | Path, pattern: str) -> Iterator[Path]:
        """Glob search in a directory."""
        raise NotImplementedError

    def rglob(self, path: str | Path, pattern: str) -> Iterator[Path]:
        """Recursive glob search."""
        raise NotImplementedError

    def copy(self, src: str | Path, dst: str | Path) -> None:
        """Copy a file or directory."""
        raise NotImplementedError


class RealFileSystem(FileSystemAdapter):
    """Concrete implementation using the real OS filesystem."""

    def read_text(self, path: str | Path, encoding: str = "utf-8") -> str:
        """Read text from real filesystem."""
        return Path(path).read_text(encoding=encoding)

    def write_text(
        self,
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
    ) -> None:
        """Write text to real filesystem."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)

    def exists(self, path: str | Path) -> bool:
        """Check real filesystem path."""
        return Path(path).exists()

    def is_file(self, path: str | Path) -> bool:
        """Check if real path is file."""
        return Path(path).is_file()

    def is_dir(self, path: str | Path) -> bool:
        """Check if real path is directory."""
        return Path(path).is_dir()

    def mkdir(
        self,
        path: str | Path,
        parents: bool = True,
        exist_ok: bool = True,
    ) -> None:
        """Create real directory."""
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)

    def glob(self, path: str | Path, pattern: str) -> Iterator[Path]:
        """Glob real directory."""
        return Path(path).glob(pattern)

    def rglob(self, path: str | Path, pattern: str) -> Iterator[Path]:
        """Recursive glob real directory."""
        return Path(path).rglob(pattern)

    def copy(self, src: str | Path, dst: str | Path) -> None:
        """Copy real file."""
        dst_path = Path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


class MemoryFileSystem(FileSystemAdapter):
    """In-memory filesystem implementation for testing."""

    def __init__(self) -> None:
        """Initialize empty memory filesystem."""
        self._files: dict[Path, str] = {}
        self._dirs: set[Path] = set()
        self._lock = threading.RLock()

    def read_text(self, path: str | Path, encoding: str = "utf-8") -> str:
        """Read from memory."""
        path = Path(path)
        with self._lock:
            if path not in self._files:
                raise FileNotFoundError(f"File not found: {path}")
            return self._files[path]

    def write_text(
        self,
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
    ) -> None:
        """Write to memory."""
        path = Path(path)
        with self._lock:
            self._ensure_parent_dirs(path)
            self._files[path] = content

    def exists(self, path: str | Path) -> bool:
        """Check memory existence."""
        path = Path(path)
        with self._lock:
            return path in self._files or path in self._dirs

    def is_file(self, path: str | Path) -> bool:
        """Check if memory path is file."""
        path = Path(path)
        with self._lock:
            return path in self._files

    def is_dir(self, path: str | Path) -> bool:
        """Check if memory path is directory."""
        path = Path(path)
        with self._lock:
            return path in self._dirs

    def mkdir(
        self,
        path: str | Path,
        parents: bool = True,
        exist_ok: bool = True,
    ) -> None:
        """Create directory in memory."""
        path = Path(path)
        with self._lock:
            if path in self._dirs and not exist_ok:
                raise FileExistsError(f"Directory already exists: {path}")

            if parents:
                # Hack to reuse ensure_parent logic
                self._ensure_parent_dirs(path / "placeholder")

            self._dirs.add(path)

    def glob(self, path: str | Path, pattern: str) -> Iterator[Path]:
        """Glob search in memory filesystem.

        Args:
            path: Base directory to search in
            pattern: Glob pattern (e.g., "*.md", "*.py")

        Returns:
            Iterator of matching Path objects
        """
        import fnmatch

        path = Path(path)
        with self._lock:
            # Find all files that start with the base path
            for file_path in self._files:
                # Check if file is direct child of path
                if file_path.parent == path:
                    if fnmatch.fnmatch(file_path.name, pattern):
                        yield file_path

    def rglob(self, path: str | Path, pattern: str) -> Iterator[Path]:
        """Recursive glob search in memory filesystem.

        Args:
            path: Base directory to search in
            pattern: Glob pattern (e.g., "*.md", "*.py")

        Returns:
            Iterator of matching Path objects (recursively)
        """
        import fnmatch

        path = Path(path)
        with self._lock:
            # Find all files recursively under path
            for file_path in self._files:
                # Check if file is under path (or equal to path)
                try:
                    file_path.relative_to(path)
                    if fnmatch.fnmatch(file_path.name, pattern):
                        yield file_path
                except ValueError:
                    # file_path is not relative to path, skip it
                    continue

    def copy(self, src: str | Path, dst: str | Path) -> None:
        """Copy in memory."""
        src = Path(src)
        dst = Path(dst)
        if src not in self._files:
            raise FileNotFoundError(f"Source file not found: {src}")
        content = self.read_text(src)
        self.write_text(dst, content)

    def _ensure_parent_dirs(self, path: Path) -> None:
        """Ensure parent directories exist recursively."""
        path = Path(path)
        current = path.parent
        while current != current.parent:
            self._dirs.add(current)
            current = current.parent
