"""Atomic file operations utilities.

Provides POSIX-compliant atomic write operations to prevent
data corruption from crashes, interruptions, or disk failures.

Key Features:
- Atomic file replacement using Path.replace() (POSIX guarantee)
- Optional fsync() for durability guarantees
- Automatic cleanup of temporary files on failure
- Context manager interface for safe resource management

Usage:
    # Using context manager
    with AtomicFileWriter(target_path) as f:
        json.dump(data, f)

    # Using convenience function
    atomic_write_json(target_path, {"key": "value"})
"""

import contextlib
import json
import os
from pathlib import Path
from types import TracebackType
from typing import Any


class AtomicFileWriter:
    """Context manager for atomic file writes with fsync guarantees.

    Implements the "write to temp file + atomic rename" pattern to ensure
    that file writes are atomic and durable. This prevents corruption from:
    - Process crashes (SIGINT, SIGKILL)
    - Disk full conditions
    - Power failures (when fsync=True)
    - Concurrent access races

    Args:
        target: Destination file path
        fsync: If True, force write to physical disk before atomic replace
        mode: File open mode (default: "w" for text)

    Example:
        >>> with AtomicFileWriter(Path("config.json")) as f:
        ...     json.dump({"setting": "value"}, f)

    Thread Safety:
        Uses PID-based temporary file naming to avoid conflicts between
        concurrent processes writing to the same target.
    """

    def __init__(
        self,
        target: Path,
        *,
        fsync: bool = True,
        mode: str = "w",
    ) -> None:
        """Initialize atomic writer.

        Args:
            target: Destination file path
            fsync: If True, call os.fsync() before atomic replace
            mode: File open mode ("w" for text, "wb" for binary)
        """
        self.target = Path(target)
        self.fsync = fsync
        self.mode = mode
        # Use PID in temp filename to avoid race conditions
        self.temp_path = target.with_suffix(f".tmp.{os.getpid()}")
        self._file = None  # type: ignore

    def __enter__(self):  # type: ignore
        """Open temporary file for writing."""
        # Ensure parent directory exists
        self.target.parent.mkdir(parents=True, exist_ok=True)

        # Open temporary file
        self._file = self.temp_path.open(self.mode, encoding="utf-8")
        return self._file

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Close file and perform atomic replace or cleanup.

        On success (exc_type is None):
            - Flush and optionally fsync
            - Atomically replace target with temp file

        On failure (exception occurred):
            - Clean up temporary file
            - Re-raise exception
        """
        try:
            if exc_type is None and self._file is not None:
                # Success path: flush and atomic replace
                if self.fsync:
                    self._file.flush()
                    os.fsync(self._file.fileno())
                self._file.close()

                # Atomic replace (POSIX guarantees atomicity)
                # This is safe even if target exists - it will be replaced atomically
                self.temp_path.replace(self.target)
            elif self._file is not None:
                # Failure path: cleanup temp file
                self._file.close()
                if self.temp_path.exists():
                    with contextlib.suppress(OSError):
                        self.temp_path.unlink()
        except Exception:
            # If anything fails during cleanup, still close the file
            if self._file and not self._file.closed:
                with contextlib.suppress(OSError):
                    self._file.close()
            raise

        # Don't suppress exceptions - let them propagate
        return False


def atomic_write_json(
    target: Path,
    data: dict[str, Any],
    *,
    fsync: bool = True,
) -> None:
    """Convenience function for atomic JSON writes.

    Writes JSON data to a file atomically with proper formatting.

    Args:
        target: Destination file path
        data: Dictionary to serialize as JSON
        fsync: If True, force write to disk before atomic replace

    Example:
        >>> atomic_write_json(Path("data.json"), {"status": "success"})

    Raises:
        OSError: If write fails
        TypeError: If data is not JSON-serializable
    """
    with AtomicFileWriter(target, fsync=fsync) as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")  # Add trailing newline for POSIX compliance
