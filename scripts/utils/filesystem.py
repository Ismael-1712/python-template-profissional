"""Filesystem abstraction layer for easier testing and isolation."""
import shutil
import threading
from pathlib import Path
from typing import Iterator, Union


class FileSystemAdapter:
    """Abstract base class for filesystem operations."""

    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read text from a file."""
        raise NotImplementedError

    def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> None:
        """Write text to a file."""
        raise NotImplementedError

    def exists(self, path: Union[str, Path]) -> bool:
        """Check if a path exists."""
        raise NotImplementedError

    def is_file(self, path: Union[str, Path]) -> bool:
        """Check if a path is a file."""
        raise NotImplementedError

    def is_dir(self, path: Union[str, Path]) -> bool:
        """Check if a path is a directory."""
        raise NotImplementedError

    def mkdir(
        self, path: Union[str, Path], parents: bool = True, exist_ok: bool = True
    ) -> None:
        """Create a directory."""
        raise NotImplementedError

    def glob(self, path: Union[str, Path], pattern: str) -> Iterator[Path]:
        """Glob search in a directory."""
        raise NotImplementedError

    def rglob(self, path: Union[str, Path], pattern: str) -> Iterator[Path]:
        """Recursive glob search."""
        raise NotImplementedError

    def copy(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """Copy a file or directory."""
        raise NotImplementedError


class RealFileSystem(FileSystemAdapter):
    """Concrete implementation using the real OS filesystem."""

    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read text from real filesystem."""
        return Path(path).read_text(encoding=encoding)

    def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> None:
        """Write text to real filesystem."""
        Path(path).write_text(content, encoding=encoding)

    def exists(self, path: Union[str, Path]) -> bool:
        """Check real filesystem path."""
        return Path(path).exists()

    def is_file(self, path: Union[str, Path]) -> bool:
        """Check if real path is file."""
        return Path(path).is_file()

    def is_dir(self, path: Union[str, Path]) -> bool:
        """Check if real path is directory."""
        return Path(path).is_dir()

    def mkdir(
        self, path: Union[str, Path], parents: bool = True, exist_ok: bool = True
    ) -> None:
        """Create real directory."""
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)

    def glob(self, path: Union[str, Path], pattern: str) -> Iterator[Path]:
        """Glob real directory."""
        return Path(path).glob(pattern)

    def rglob(self, path: Union[str, Path], pattern: str) -> Iterator[Path]:
        """Recursive glob real directory."""
        return Path(path).rglob(pattern)

    def copy(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """Copy real file."""
        shutil.copy2(src, dst)


class MemoryFileSystem(FileSystemAdapter):
    """In-memory filesystem implementation for testing."""

    def __init__(self) -> None:
        """Initialize empty memory filesystem."""
        self._files: dict[Path, str] = {}
        self._dirs: set[Path] = set()
        self._lock = threading.RLock()

    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read from memory."""
        path = Path(path)
        with self._lock:
            if path not in self._files:
                raise FileNotFoundError(f"File not found: {path}")
            return self._files[path]

    def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> None:
        """Write to memory."""
        path = Path(path)
        with self._lock:
            self._ensure_parent_dirs(path)
            self._files[path] = content

    def exists(self, path: Union[str, Path]) -> bool:
        """Check memory existence."""
        path = Path(path)
        with self._lock:
            return path in self._files or path in self._dirs

    def is_file(self, path: Union[str, Path]) -> bool:
        """Check if memory path is file."""
        path = Path(path)
        with self._lock:
            return path in self._files

    def is_dir(self, path: Union[str, Path]) -> bool:
        """Check if memory path is directory."""
        path = Path(path)
        with self._lock:
            return path in self._dirs

    def mkdir(
        self, path: Union[str, Path], parents: bool = True, exist_ok: bool = True
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

    def glob(self, path: Union[str, Path], pattern: str) -> Iterator[Path]:
        """Stub for glob."""
        _ = Path(path)
        return iter([])

    def rglob(self, path: Union[str, Path], pattern: str) -> Iterator[Path]:
        """Stub for rglob."""
        _ = Path(path)
        return iter([])

    def copy(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """Copy in memory."""
        src = Path(src)
        dst = Path(dst)
        content = self.read_text(src)
        self.write_text(dst, content)

    def _ensure_parent_dirs(self, path: Path) -> None:
        """Ensure parent directories exist recursively."""
        path = Path(path)
        current = path.parent
        while current != current.parent:
            self._dirs.add(current)
            current = current.parent
