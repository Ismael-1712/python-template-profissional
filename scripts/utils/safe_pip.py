"""Safe pip-compile wrapper with atomic output guarantees.

Provides a safer interface to pip-compile that ensures output files
are written atomically, preventing corruption from interruptions.

Key Features:
- Atomic output file creation (temp file + atomic replace)
- Output validation (non-empty, basic syntax check)
- Automatic cleanup on failure
- Preserves pip-compile exit codes and output
"""

import contextlib
import os
import subprocess
from pathlib import Path


def safe_pip_compile(
    input_file: Path,
    output_file: Path,
    pip_compile_path: str,
    *,
    workspace_root: Path | None = None,
) -> subprocess.CompletedProcess:
    """Execute pip-compile with atomic output guarantees.

    Strategy:
    1. Run pip-compile to temporary file
    2. Validate output (non-empty, starts with expected header)
    3. Atomically replace target file

    This prevents corruption if pip-compile is interrupted (Ctrl+C),
    crashes, or encounters disk full conditions.

    Args:
        input_file: Path to requirements input file (.in)
        output_file: Path to requirements output file (.txt)
        pip_compile_path: Path to pip-compile executable
        workspace_root: Optional working directory for subprocess

    Returns:
        CompletedProcess with stdout, stderr, and returncode

    Raises:
        subprocess.CalledProcessError: If pip-compile fails
        RuntimeError: If output validation fails
        OSError: If file operations fail

    Example:
        >>> result = safe_pip_compile(
        ...     Path("requirements/dev.in"),
        ...     Path("requirements/dev.txt"),
        ...     "/path/to/pip-compile"
        ... )
    """
    # Create temporary output path with PID to avoid race conditions
    temp_output = output_file.with_suffix(f".tmp.{os.getpid()}.txt")

    try:
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Run pip-compile to temporary file
        result = subprocess.run(  # nosec # noqa: subprocess
            [
                pip_compile_path,
                "--output-file",
                str(temp_output),
                str(input_file),
            ],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=True,
        )

        # Validate output file
        if not temp_output.exists():
            msg = f"pip-compile did not create output file: {temp_output}"
            raise RuntimeError(msg)

        if temp_output.stat().st_size == 0:
            msg = f"pip-compile produced empty output file: {temp_output}"
            raise RuntimeError(msg)

        # Basic sanity check: file should start with comment
        first_line = temp_output.read_text(encoding="utf-8").split("\n")[0]
        if not first_line.startswith("#"):
            msg = (
                f"pip-compile output has unexpected format "
                f"(expected comment header): {first_line[:50]}"
            )
            raise RuntimeError(msg)

        # Atomic replace (POSIX guarantees atomicity)
        temp_output.replace(output_file)

        return result

    except Exception:
        # Cleanup temporary file on any failure
        if temp_output.exists():
            with contextlib.suppress(OSError):
                temp_output.unlink()
        raise
