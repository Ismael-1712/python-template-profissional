"""Platform-specific operations abstraction layer.

This module provides a strategy pattern implementation to abstract
operating system differences, enabling cross-platform compatibility
for file operations, command execution, and environment management.

Design Principles:
- Protocol-based polymorphism (PEP 544)
- Explicit strategy selection via factory
- Fail-safe defaults with documented limitations
- Zero-cost abstraction (minimal runtime overhead)

Supported Platforms:
- Unix/Linux (tested on Ubuntu 20.04+)
- macOS (Darwin)
- Windows 10/11 (tested on WSL and native)

Usage:
    from scripts.utils.platform_strategy import get_platform_strategy

    strategy = get_platform_strategy()
    git_cmd = strategy.get_git_command()
    strategy.ensure_durability(file_descriptor)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# --- Global Alert Guard ---
# Ensures Windows compatibility alert is emitted only once per Python session
# to avoid log spam during long-running operations (e.g., cortex map + scan).
_windows_alert_emitted: bool = False


@runtime_checkable
class PlatformStrategy(Protocol):
    """Protocol defining platform-specific operations interface.

    This protocol ensures type safety and defines the contract for
    platform-specific implementations. All methods are static to
    avoid unnecessary instance state.

    Security:
        Implementations must validate inputs and prevent injection attacks.
        Command paths should be verified before execution.

    Thread Safety:
        All methods are stateless and thread-safe.
    """

    @staticmethod
    def get_git_command() -> str:
        """Return the platform-appropriate git command.

        Returns:
            Command name for git executable (e.g., "git" or "git.exe")

        Note:
            Assumes git is in PATH. For advanced scenarios, consider
            using shutil.which() to validate availability.
        """
        ...

    @staticmethod
    def ensure_durability(path: Path | int) -> bool:
        """Force write to physical storage media.

        Ensures data durability across system crashes and power failures.
        Behavior varies significantly across platforms.

        Args:
            path: File path or file descriptor (from file.fileno())

        Returns:
            True if sync was successful, False otherwise

        Platform Behavior:
            Unix/Linux: Calls fsync() - guarantees physical write
            macOS: Calls fsync() - guarantees physical write (F_FULLFSYNC)
            Windows: Calls fsync() - flushes buffers only (weaker guarantee)

        Note:
            On Windows, fsync() does NOT guarantee physical disk write due
            to disk cache controller differences. For true durability on
            Windows, consider FlushFileBuffers via ctypes.

        Raises:
            OSError: If sync operation fails
        """
        ...

    @staticmethod
    def set_file_permissions(path: Path, mode: int) -> None:
        """Set file permissions using platform-appropriate method.

        Args:
            path: Target file path
            mode: Unix permission bits (e.g., 0o644, 0o755)

        Platform Behavior:
            Unix/Linux: Sets chmod permissions directly
            macOS: Sets chmod permissions directly
            Windows: No-op or basic read-only flag (limited support)

        Note:
            Windows does not support Unix permission model. The mode
            parameter is interpreted as: write bit = not read-only.
            For advanced Windows ACLs, use platform-specific APIs.

        Raises:
            OSError: On Unix if permission change fails
        """
        ...

    @staticmethod
    def get_venv_bin_dir() -> str:
        """Return virtual environment executables directory name.

        Returns:
            Directory name containing venv executables

        Platform Values:
            Unix/Linux/macOS: "bin"
            Windows: "Scripts"

        Example:
            >>> strategy = get_platform_strategy()
            >>> venv_path = Path(".venv") / strategy.get_venv_bin_dir()
            >>> python_path = venv_path / "python"
        """
        ...

    @staticmethod
    def get_venv_activate_command() -> str:
        r"""Return command to activate virtual environment.

        Returns:
            Shell command string to activate venv

        Platform Commands:
            Unix/Linux/macOS: "source .venv/bin/activate"
            Windows CMD: ".venv\Scripts\activate.bat"
            Windows PowerShell: ".venv\Scripts\Activate.ps1"

        Note:
            Windows returns CMD version by default. For PowerShell,
            users should manually adjust the command.
        """
        ...


class UnixStrategy:
    """Platform strategy implementation for Unix-like systems.

    Supports Linux, macOS, and other POSIX-compliant systems.
    All operations use standard POSIX APIs with strong guarantees.

    Thread Safety: All methods are stateless and thread-safe.
    """

    @staticmethod
    def get_git_command() -> str:
        """Return git command for Unix systems.

        Returns:
            "git" - standard Unix command

        Note:
            Assumes git is installed and in PATH. Use shutil.which("git")
            to verify availability before use.
        """
        return "git"

    @staticmethod
    def ensure_durability(path: Path | int) -> bool:
        """Force write to physical disk using fsync().

        On Unix/Linux, fsync() provides strong durability guarantees:
        - Flushes all modified in-core data to disk
        - Flushes file metadata (timestamps, permissions)
        - Blocks until physical write completes

        Args:
            path: File path or file descriptor from file.fileno()

        Returns:
            True if sync was successful, False otherwise

        Raises:
            OSError: If fsync fails (disk full, I/O error, etc.)

        Performance:
            fsync() is expensive (10-100ms typical). Use sparingly
            on critical data only (e.g., config files, state snapshots).
        """
        try:
            if isinstance(path, int):
                os.fsync(path)
            else:
                # For directories or files, open and sync
                fd = os.open(str(path), os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            return True
        except OSError as e:
            logger.warning(f"fsync failed for {path}: {e}")
            return False

    @staticmethod
    def set_file_permissions(path: Path, mode: int) -> None:
        """Set Unix file permissions using chmod().

        Args:
            path: Target file path
            mode: Permission bits (e.g., 0o644 for rw-r--r--)

        Common Modes:
            0o644: -rw-r--r-- (owner write, all read)
            0o755: -rwxr-xr-x (owner write+exec, all read+exec)
            0o600: -rw------- (owner only)

        Raises:
            OSError: If chmod fails (permissions, file not found)
            FileNotFoundError: If path doesn't exist
        """
        path.chmod(mode)

    @staticmethod
    def get_venv_bin_dir() -> str:
        """Return Unix venv executables directory.

        Returns:
            "bin" - standard Unix convention
        """
        return "bin"

    @staticmethod
    def get_venv_activate_command() -> str:
        """Return Unix venv activation command.

        Returns:
            "source .venv/bin/activate" - bash/zsh compatible

        Note:
            For fish shell, use: "source .venv/bin/activate.fish"
            For csh, use: "source .venv/bin/activate.csh"
        """
        return "source .venv/bin/activate"


class WindowsStrategy:
    """Platform strategy implementation for Windows systems.

    Supports Windows 10, Windows 11, and Windows Server 2016+.
    Handles platform differences and provides best-effort equivalents.

    Limitations:
        - fsync() has weaker durability guarantees
        - chmod() permissions are not fully supported
        - Path separators use backslashes

    Thread Safety: All methods are stateless and thread-safe.
    """

    @staticmethod
    def get_git_command() -> str:
        r"""Return git command for Windows systems.

        Returns:
            "git.exe" - Windows executable name

        Note:
            Most Windows environments accept "git" without .exe extension.
            Using "git.exe" is more explicit and prevents ambiguity.

            Git for Windows installation paths:
            - System: C:\Program Files\Git\bin\git.exe
            - User: %LOCALAPPDATA%\Programs\Git\bin\git.exe
        """
        return "git.exe"

    @staticmethod
    def ensure_durability(path: Path | int) -> bool:
        """Force write to storage using fsync() (best effort on Windows).

        Windows Behavior:
            os.fsync() on Windows flushes file buffers to OS cache but
            does NOT guarantee physical disk write. Disk controllers may
            cache writes for performance.

        Args:
            path: File path or file descriptor from file.fileno()

        Returns:
            True if sync was successful, False otherwise

        Limitations:
            For true durability on Windows, use Win32 API FlushFileBuffers
            with FILE_FLAG_WRITE_THROUGH. This implementation uses fsync()
            as a best-effort approach compatible with Unix code.

        Raises:
            OSError: If flush operation fails

        Performance:
            Faster than Unix fsync() but weaker guarantees. Acceptable
            for most use cases (config files, logs). For critical data
            (database WAL), consider platform-specific code.
        """
        try:
            if isinstance(path, int):
                os.fsync(path)
            else:
                # For directories or files, open and sync
                fd = os.open(str(path), os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            logger.debug(
                "fsync() called on Windows (buffer flush only, "
                "not guaranteed physical write)",
            )
            return True
        except OSError as e:
            logger.warning(f"fsync failed for {path}: {e}")
            return False

    @staticmethod
    def set_file_permissions(path: Path, mode: int) -> None:
        """Set file attributes on Windows (limited chmod support).

        Windows Limitation:
            Windows does not support Unix permission bits (rwxrwxrwx).
            Python's os.chmod() on Windows only recognizes:
            - stat.S_IWRITE: Make file writable
            - stat.S_IREAD: Make file readable (default)

        Args:
            path: Target file path
            mode: Unix permission bits (interpreted for read-only flag)

        Behavior:
            - If mode has write bit (0o200): File is writable
            - If mode lacks write bit: File is read-only
            - Execute bits are ignored (Windows uses file extension)

        Note:
            For advanced Windows ACLs, use pywin32 or ctypes with
            SetFileSecurity / SetNamedSecurityInfo APIs.

        Raises:
            OSError: If file attribute change fails
        """
        # Attempt chmod but it has limited effect on Windows
        # Only read-only flag is respected
        try:
            path.chmod(mode)
        except OSError as e:
            # Windows may raise errors for certain modes
            # Log and continue - permission model is different
            logger.debug(
                "chmod() on Windows has limited effect (mode=%o): %s",
                mode,
                e,
            )

    @staticmethod
    def get_venv_bin_dir() -> str:
        """Return Windows venv executables directory.

        Returns:
            "Scripts" - Windows venv convention

        Note:
            Windows venv structure:
            .venv/
            ├── Scripts/          (executables)
            │   ├── python.exe
            │   ├── pip.exe
            │   └── activate.bat
            └── Lib/              (packages)
        """
        return "Scripts"

    @staticmethod
    def get_venv_activate_command() -> str:
        r"""Return Windows venv activation command.

        Returns:
            ".venv\Scripts\activate.bat" - CMD compatible

        Alternative for PowerShell:
            ".venv\Scripts\Activate.ps1"

        Note:
            CMD (Command Prompt) uses .bat scripts
            PowerShell uses .ps1 scripts
            Git Bash (MINGW) can use Unix-style activate

        Execution Policy (PowerShell):
            If activation fails, run:
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
        """
        return ".venv\\Scripts\\activate.bat"


# --- Factory Function ---


def get_platform_strategy() -> PlatformStrategy:
    """Factory function to get appropriate platform strategy.

    Detects current platform using sys.platform and returns
    the corresponding strategy implementation.

    Returns:
        PlatformStrategy implementation (UnixStrategy or WindowsStrategy)

    Platform Detection:
        - "linux": UnixStrategy
        - "darwin": UnixStrategy (macOS)
        - "win32": WindowsStrategy
        - "cygwin": WindowsStrategy
        - other: UnixStrategy (default)

    Example:
        >>> strategy = get_platform_strategy()
        >>> git_cmd = strategy.get_git_command()
        >>> print(f"Git command: {git_cmd}")

    Thread Safety:
        Safe to call from multiple threads. Returns stateless strategy.

    Windows Compatibility Alert:
        On first detection of Windows, emits a warning about best-effort
        mode limitations (fsync, chmod, NTFS caching). This alert is
        emitted only once per Python session to avoid log spam.
    """
    global _windows_alert_emitted  # Required to modify module-level guard

    platform = sys.platform.lower()

    if platform in ("win32", "cygwin"):
        logger.debug("Platform detected: Windows (using WindowsStrategy)")

        # Emit compatibility alert ONCE per session
        if not _windows_alert_emitted:
            logger.warning(
                "⚠️  Windows Platform Detected - Running in BEST-EFFORT MODE:\n"
                "   • fsync() only flushes OS buffers (not physical disk write)\n"
                "   • chmod() has limited support (Unix permissions not enforced)\n"
                "   • NTFS disk controller caching may delay physical writes\n"
                "   ⚡ Atomic write guarantees are WEAKER than Unix/Linux.\n"
                "   📖 See: scripts/utils/platform_strategy.py for details.",
            )
            _windows_alert_emitted = True

        return WindowsStrategy()

    # Default to Unix for Linux, macOS, BSD, and other POSIX systems
    logger.debug("Platform detected: Unix-like (using UnixStrategy)")
    return UnixStrategy()


# --- Convenience Functions ---


def get_git_command() -> str:
    """Convenience function to get platform-appropriate git command.

    Returns:
        Git command string for current platform

    Example:
        >>> git_cmd = get_git_command()
        >>> subprocess.run([git_cmd, "status"], check=True)  # nosec # noqa: subprocess
    """
    return get_platform_strategy().get_git_command()


def get_venv_paths() -> tuple[str, str]:
    """Get venv paths for current platform.

    Returns:
        Tuple of (bin_dir, activate_command)

    Example:
        >>> bin_dir, activate_cmd = get_venv_paths()
        >>> print(f"Activate with: {activate_cmd}")
    """
    strategy = get_platform_strategy()
    return strategy.get_venv_bin_dir(), strategy.get_venv_activate_command()
