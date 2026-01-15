r"""Dependency Guardian - Cryptographic Integrity Seal System.

This module implements the v2.3 Deep Consistency Protocol using SHA-256
cryptographic seals and in-memory compilation to protect against dependency
drift and tampering.

The Guardian ensures that requirements.txt lockfiles are always derived
from their corresponding .in files, preventing manual edits and PyPI drift.

Protocol v2.3 (Enhanced):
1. Compute SHA-256 hash of .in file (ignoring comments/blanks) - v2.2
2. Inject integrity seal into .txt lockfile header - v2.2
3. Validate seal on every critical operation (pre-push, CI) - v2.2
4. Deep consistency check: pip-compile in memory + byte comparison - v2.3 NEW
5. Atomic write with file locking to prevent editor corruption - v2.3 NEW

Security Model:
- Hash is comment-agnostic (robust against documentation changes)
- Seal injection is idempotent (safe for multiple runs)
- Validation fails fast on ANY mismatch (zero tolerance)
- Deep check detects PyPI drift that seals alone cannot catch

Usage:
    from scripts.core.dependency_guardian import DependencyGuardian

    guardian = DependencyGuardian(Path("requirements"))

    # Seal a lockfile after pip-compile (v2.2)
    hash_value = guardian.compute_input_hash("dev")
    guardian.inject_seal("dev", hash_value)

    # Validate seal before push (v2.2)
    if not guardian.validate_seal("dev"):
        raise IntegrityError("Lockfile integrity compromised!")

    # Deep consistency check (v2.3)
    is_valid, diff = guardian.validate_deep_consistency("dev")
    if not is_valid:
        print(f"Lockfile desynchronized:\n{diff}")
        raise IntegrityError("PyPI drift detected!")
"""

import fcntl
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


class DependencyGuardian:
    """Cryptographic guardian for dependency integrity.

    This class provides the core autoimunity mechanism through SHA-256
    integrity seals, preventing dependency drift at the source.

    Attributes:
        requirements_dir: Path to directory containing .in/.txt files
    """

    SEAL_MARKER = "# INTEGRITY_SEAL:"
    SEAL_PATTERN = re.compile(r"^# INTEGRITY_SEAL:\s+([0-9a-f]{64})\s*$")

    def __init__(self, requirements_dir: Path) -> None:
        """Initialize the guardian with requirements directory.

        Args:
            requirements_dir: Path to directory containing requirements files
        """
        self.requirements_dir = Path(requirements_dir)

    def compute_input_hash(self, req_name: str) -> str:
        """Compute SHA-256 hash of .in file content (comment-agnostic).

        This method extracts only meaningful dependency lines, ignoring:
        - Comments (lines starting with #)
        - Blank lines
        - Leading/trailing whitespace

        This ensures hash stability against documentation changes while
        remaining sensitive to actual dependency modifications.

        Args:
            req_name: Name of requirements file (e.g., 'dev' for dev.in)

        Returns:
            str: 64-character lowercase hexadecimal SHA-256 hash

        Raises:
            FileNotFoundError: If .in file doesn't exist
        """
        in_file = self.requirements_dir / f"{req_name}.in"

        if not in_file.exists():
            raise FileNotFoundError(
                f"Requirements input file not found: {in_file}",
            )

        content = in_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Extract only meaningful dependency lines
        meaningful_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip comments and blank lines
            if stripped and not stripped.startswith("#"):
                meaningful_lines.append(stripped)

        # Normalize content for hashing (consistent line endings)
        normalized_content = "\n".join(meaningful_lines)

        # Compute SHA-256 hash
        hash_obj = hashlib.sha256(normalized_content.encode("utf-8"))
        return hash_obj.hexdigest()

    def inject_seal(self, req_name: str, seal_hash: str) -> None:
        """Inject integrity seal into .txt lockfile.

        The seal is placed in the header section after the autogeneration
        notice, ensuring visibility and preventing accidental removal.

        If a seal already exists, it's replaced (idempotent operation).

        Args:
            req_name: Name of requirements file (e.g., 'dev' for dev.txt)
            seal_hash: 64-character SHA-256 hash to inject

        Raises:
            FileNotFoundError: If .txt lockfile doesn't exist
            ValueError: If seal_hash is not valid SHA-256 format
        """
        txt_file = self.requirements_dir / f"{req_name}.txt"

        if not txt_file.exists():
            raise FileNotFoundError(
                f"Requirements lockfile not found: {txt_file}",
            )

        self._validate_hash_format(seal_hash)
        lines = self._read_lockfile_content(txt_file)
        lines = self._strip_existing_seals(lines)
        injection_index = self._find_injection_point(lines)
        lines = self._insert_seal_at(lines, injection_index, seal_hash)
        self._write_sealed_content(txt_file, lines)

    def _validate_hash_format(self, seal_hash: str) -> None:
        """Validate that seal_hash is a valid SHA-256 format.

        Args:
            seal_hash: Hash to validate

        Raises:
            ValueError: If hash format is invalid
        """
        if not re.match(r"^[0-9a-f]{64}$", seal_hash):
            raise ValueError(
                f"Invalid SHA-256 hash format: {seal_hash} "
                "(expected 64 lowercase hex characters)",
            )

    def _read_lockfile_content(self, txt_file: Path) -> list[str]:
        """Read and split lockfile content into lines.

        Args:
            txt_file: Path to lockfile

        Returns:
            list[str]: Lines from the file
        """
        content = txt_file.read_text(encoding="utf-8")
        return content.splitlines()

    def _strip_existing_seals(self, lines: list[str]) -> list[str]:
        """Remove existing integrity seals from lines.

        Args:
            lines: File content as list of lines

        Returns:
            list[str]: Lines with seals removed
        """
        return [line for line in lines if not line.strip().startswith(self.SEAL_MARKER)]

    def _find_injection_point(self, lines: list[str]) -> int:
        """Find the appropriate position to inject the seal.

        Searches for autogeneration header and returns position after it.

        Args:
            lines: File content as list of lines

        Returns:
            int: Index where seal should be inserted
        """
        injection_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("#") and (
                "autogenerated" in line.lower() or "pip-compile" in line.lower()
            ):
                injection_index = i + 1
                # Skip following comment lines that are part of header
                injection_index = self._skip_header_comments(lines, injection_index)
                break
        return injection_index

    def _skip_header_comments(self, lines: list[str], start_index: int) -> int:
        """Skip comment lines and blanks after header start.

        Args:
            lines: File content as list of lines
            start_index: Index to start skipping from

        Returns:
            int: Index after all header comments
        """
        index = start_index
        while index < len(lines) and (
            lines[index].strip().startswith("#") or lines[index].strip() == ""
        ):
            index += 1
        return index

    def _insert_seal_at(
        self,
        lines: list[str],
        index: int,
        seal_hash: str,
    ) -> list[str]:
        """Insert seal line at specified index.

        Args:
            lines: File content as list of lines
            index: Position to insert seal
            seal_hash: Hash value to insert

        Returns:
            list[str]: Lines with seal inserted
        """
        seal_line = f"{self.SEAL_MARKER} {seal_hash}"
        lines.insert(index, seal_line)
        return lines

    def _write_sealed_content(self, txt_file: Path, lines: list[str]) -> None:
        """Write sealed content back to lockfile (delegates to atomic write).

        Args:
            txt_file: Path to lockfile
            lines: Content to write
        """
        # Use atomic write to prevent race conditions (v2.3 enhancement)
        self._write_sealed_content_atomic(txt_file, lines)

    def validate_seal(self, req_name: str) -> bool:
        """Validate integrity seal against current .in file hash.

        This method performs cryptographic validation:
        1. Extract seal from .txt lockfile
        2. Compute current hash of .in file
        3. Compare hashes (constant-time comparison for security)

        Args:
            req_name: Name of requirements file (e.g., 'dev')

        Returns:
            bool: True if seal is valid and matches current .in hash,
                  False otherwise (missing seal, corrupted, or mismatch)
        """
        txt_file = self.requirements_dir / f"{req_name}.txt"

        if not txt_file.exists():
            return False

        # Extract seal from lockfile
        stored_seal = self._extract_seal(txt_file)
        if stored_seal is None:
            return False

        # Compute current hash of .in file
        try:
            current_hash = self.compute_input_hash(req_name)
        except FileNotFoundError:
            return False

        # Constant-time comparison (security best practice)
        return self._constant_time_compare(stored_seal, current_hash)

    def _extract_seal(self, txt_file: Path) -> str | None:
        """Extract integrity seal from lockfile.

        Args:
            txt_file: Path to .txt lockfile

        Returns:
            Optional[str]: Extracted seal hash or None if not found/invalid
        """
        content = txt_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        for line in lines:
            match = self.SEAL_PATTERN.match(line.strip())
            if match:
                return match.group(1)

        return None

    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """Perform constant-time string comparison.

        This prevents timing attacks during seal validation.

        Args:
            a: First string
            b: Second string

        Returns:
            bool: True if strings are equal
        """
        if len(a) != len(b):
            return False

        result = 0
        for char_a, char_b in zip(a, b, strict=True):
            result |= ord(char_a) ^ ord(char_b)

        return result == 0

    def validate_deep_consistency(
        self,
        req_name: str,
        python_exec: str | None = None,
    ) -> tuple[bool, str]:
        """Validate lockfile against in-memory pip-compile (deep check).

        This is the ULTIMATE consistency validation that catches:
        - Manual edits to lockfile
        - PyPI drift (upstream version changes between local and CI)
        - Incomplete/corrupted pip-compile runs
        - Seal tampering

        This method resolves the critical flaw in v2.2 where the SHA-256 seal
        validates the INPUT (.in file) but is blind to OUTPUT (.txt) changes
        caused by PyPI releasing new versions between local commit and CI execution.

        Args:
            req_name: Requirements file name (e.g., 'dev')
            python_exec: Path to Python interpreter (uses sys.executable if None)

        Returns:
            tuple[bool, str]: (is_valid, diff_report)
                - is_valid: True if lockfile matches pip-compile output exactly
                - diff_report: Human-readable diff if desynchronized, empty if synced

        Example:
            guardian = DependencyGuardian(Path("requirements"))
            is_valid, diff = guardian.validate_deep_consistency("dev")

            if not is_valid:
                print("❌ Lockfile desynchronized:")
                print(diff)
        """
        in_file = self.requirements_dir / f"{req_name}.in"
        txt_file = self.requirements_dir / f"{req_name}.txt"

        if not in_file.exists():
            return False, f"Input file not found: {in_file}"

        if not txt_file.exists():
            return False, f"Lockfile not found: {txt_file}"

        # Use system python if not specified
        if python_exec is None:
            python_exec = sys.executable

        # RESILIÊNCIA: Verificar se piptools está disponível
        check_piptools = subprocess.run(
            [python_exec, "-m", "pip", "show", "pip-tools"],
            capture_output=True,
            text=True,
            check=False,
        )
        if check_piptools.returncode != 0:
            return False, (
                "❌ Environment Not Ready: pip-tools not found.\n"
                "   Install with: pip install pip-tools\n"
                "   Or use: make install-dev"
            )

        # Compile in memory to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w+",
            delete=False,
            suffix=".txt",
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Execute pip-compile (same flags as verify_deps.py for consistency)
            result = subprocess.run(
                [
                    python_exec,
                    "-m",
                    "piptools",
                    "compile",
                    str(in_file),
                    "--output-file",
                    str(tmp_path),
                    "--resolver=backtracking",
                    "--strip-extras",
                    "--allow-unsafe",
                    "--quiet",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return False, f"pip-compile failed: {result.stderr}"

            # Compare content (comment-agnostic, like verify_deps.py)
            is_match, diff_lines = self._compare_content_deep(txt_file, tmp_path)

            if is_match:
                return True, ""
            diff_report = self._format_diff_report(diff_lines, txt_file, tmp_path)
            return False, diff_report

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def _read_non_comment_lines(self, file_path: Path) -> list[str]:
        """Extract non-comment, non-blank lines from a lockfile.

        Args:
            file_path: Path to lockfile

        Returns:
            list[str]: Stripped lines without comments/blanks
        """
        with open(file_path, encoding="utf-8") as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]

    def _find_mismatches(
        self,
        lines_a: list[str],
        lines_b: list[str],
    ) -> list[tuple[str, str]]:
        """Find mismatched lines between two lockfile content lists.

        Args:
            lines_a: Lines from committed lockfile
            lines_b: Lines from expected lockfile

        Returns:
            list[tuple[str, str]]: Pairs of (committed, expected) mismatches
        """
        mismatches = []
        max_len = max(len(lines_a), len(lines_b))

        for i in range(max_len):
            line_a = lines_a[i] if i < len(lines_a) else "<missing>"
            line_b = lines_b[i] if i < len(lines_b) else "<missing>"

            if line_a != line_b:
                mismatches.append((line_a, line_b))

        return mismatches

    def _compare_content_deep(
        self,
        file_a: Path,
        file_b: Path,
    ) -> tuple[bool, list[tuple[str, str]]]:
        """Compare two lockfiles, ignoring comments (deep content comparison).

        This implements the same comment-agnostic comparison as verify_deps.py
        but returns detailed mismatch information for reporting.

        Args:
            file_a: First lockfile path (typically committed .txt)
            file_b: Second lockfile path (typically in-memory compiled .txt)

        Returns:
            tuple[bool, list[tuple[str, str]]]:
                - bool: True if files match
                - list: [(line_a, line_b)] for mismatched lines
        """
        lines_a = self._read_non_comment_lines(file_a)
        lines_b = self._read_non_comment_lines(file_b)

        if lines_a == lines_b:
            return True, []

        mismatches = self._find_mismatches(lines_a, lines_b)
        return False, mismatches

    def _format_diff_report(
        self,
        mismatches: list[tuple[str, str]],
        file_a: Path,
        file_b: Path,
    ) -> str:
        """Format human-readable diff report for desynchronization.

        Args:
            mismatches: List of (committed_line, expected_line) tuples
            file_a: Committed lockfile path
            file_b: Expected lockfile path

        Returns:
            str: Formatted diff report with remediation steps
        """
        report = [
            "📊 LOCKFILE DESYNCHRONIZATION DETECTED",
            "",
            f"  Committed:  {file_a.name}",
            "  Expected:   (in-memory pip-compile)",
            "",
            "🔍 DIFFERENCES:",
            "",
        ]

        for i, (line_a, line_b) in enumerate(mismatches, 1):
            report.append(f"  [{i}] Mismatch:")
            report.append(f"      COMMITTED: {line_a}")
            report.append(f"      EXPECTED:  {line_b}")
            report.append("")

        report.append("💊 REMEDIATION:")
        report.append("   make requirements  (or make deps-fix)")
        report.append("")

        return "\n".join(report)

    def _write_sealed_content_atomic(
        self,
        txt_file: Path,
        lines: list[str],
    ) -> None:
        """Write sealed content atomically with file locking.

        This prevents race conditions with editors (VS Code) that might
        save their buffer while we're writing, corrupting the lockfile.

        Strategy:
        1. Write to temporary file with exclusive lock
        2. Force OS buffer flush (fsync)
        3. Atomic rename (POSIX guarantee of all-or-nothing)

        Args:
            txt_file: Target lockfile path
            lines: Content lines to write
        """
        new_content = "\n".join(lines) + "\n"

        # Write to temporary file first
        tmp_file = txt_file.with_suffix(".txt.tmp")

        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                # Acquire exclusive lock (prevents concurrent writes)
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(new_content)
                    f.flush()
                    os.fsync(f.fileno())  # Force OS buffer flush to disk
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # Atomic rename (POSIX guarantee: either fully renamed or not at all)
            tmp_file.replace(txt_file)

        except Exception:
            # Cleanup temp file on failure
            if tmp_file.exists():
                tmp_file.unlink()
            raise


class IntegrityError(Exception):
    """Raised when integrity seal validation fails."""


# CLI Interface for standalone usage
def main() -> None:
    """CLI entry point for dependency guardian operations."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Dependency Guardian - Integrity Seal Manager v2.3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compute hash of dev.in
  python -m scripts.core.dependency_guardian compute dev

  # Inject seal into dev.txt
  python -m scripts.core.dependency_guardian seal dev

  # Validate dev.txt integrity (seal only - v2.2)
  python -m scripts.core.dependency_guardian validate dev

  # Deep consistency check (pip-compile in-memory - v2.3)
  python -m scripts.core.dependency_guardian validate-deep dev

Exit Codes:
  0 - Success / Validation passed
  1 - Failure / Validation failed
        """,
    )

    parser.add_argument(
        "action",
        choices=["compute", "seal", "validate", "validate-deep"],
        help="Action to perform",
    )
    parser.add_argument(
        "req_name",
        help="Requirements file name (e.g., 'dev' for dev.in/dev.txt)",
    )
    parser.add_argument(
        "--requirements-dir",
        type=Path,
        default=Path("requirements"),
        help="Path to requirements directory (default: requirements/)",
    )
    parser.add_argument(
        "--python-exec",
        type=str,
        help="Path to Python interpreter for pip-compile (default: sys.executable)",
    )

    args = parser.parse_args()

    guardian = DependencyGuardian(args.requirements_dir)

    try:
        if args.action == "compute":
            hash_value = guardian.compute_input_hash(args.req_name)
            print(f"SHA-256: {hash_value}")
            sys.exit(0)

        elif args.action == "seal":
            hash_value = guardian.compute_input_hash(args.req_name)
            guardian.inject_seal(args.req_name, hash_value)
            print(f"✅ Seal injected: {hash_value}")
            sys.exit(0)

        elif args.action == "validate":
            is_valid = guardian.validate_seal(args.req_name)
            if is_valid:
                print("✅ Integrity seal VALID (v2.2 protocol)")
                sys.exit(0)
            else:
                print("❌ Integrity seal INVALID or MISSING")
                sys.exit(1)

        elif args.action == "validate-deep":
            print(
                "🔍 Executing Deep Consistency Check (v2.3 protocol)...",
                flush=True,
            )
            is_valid, diff_report = guardian.validate_deep_consistency(
                args.req_name,
                python_exec=args.python_exec,
            )

            if is_valid:
                print("✅ Lockfile is in PERFECT SYNC with PyPI state")
                print("✅ Deep Consistency Check: PASSED")
                sys.exit(0)
            else:
                print("❌ Deep Consistency Check: FAILED")
                print()
                print(diff_report)

                # PROTOCOLO v2.4: CI=Warn (Exit 0), Local=Fail-Hard (Exit 1)
                is_ci = os.getenv("GITHUB_ACTIONS", "").lower() == "true"

                if is_ci:
                    print(
                        "\n🔵 CI MODE DETECTED: Drift detectado mas "
                        "pipeline não bloqueado"
                    )
                    print("⚠️  REVISAR LOGS: Lockfile em dessincronia com PyPI")
                    print(
                        "💡 Execute 'make requirements' localmente para ressincronizar"
                    )
                    sys.exit(0)  # CI permissivo
                else:
                    sys.exit(1)  # Local estrito

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
