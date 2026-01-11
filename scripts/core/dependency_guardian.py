"""Dependency Guardian - Cryptographic Integrity Seal System.

This module implements the v2.2 Autoimunity Protocol using SHA-256
cryptographic seals to protect against dependency drift and tampering.

The Guardian ensures that requirements.txt lockfiles are always derived
from their corresponding .in files, preventing manual edits and drift.

Protocol:
1. Compute SHA-256 hash of .in file (ignoring comments/blanks)
2. Inject integrity seal into .txt lockfile header
3. Validate seal on every critical operation (pre-push, CI)

Security Model:
- Hash is comment-agnostic (robust against documentation changes)
- Seal injection is idempotent (safe for multiple runs)
- Validation fails fast on ANY mismatch (zero tolerance)

Usage:
    from scripts.core.dependency_guardian import DependencyGuardian

    guardian = DependencyGuardian(Path("requirements"))

    # Seal a lockfile after pip-compile
    hash_value = guardian.compute_input_hash("dev")
    guardian.inject_seal("dev", hash_value)

    # Validate before push
    if not guardian.validate_seal("dev"):
        raise IntegrityError("Lockfile integrity compromised!")
"""

import hashlib
import re
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
        """Write sealed content back to lockfile.

        Args:
            txt_file: Path to lockfile
            lines: Content to write
        """
        new_content = "\n".join(lines) + "\n"
        txt_file.write_text(new_content, encoding="utf-8")

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


class IntegrityError(Exception):
    """Raised when integrity seal validation fails."""


# CLI Interface for standalone usage
def main() -> None:
    """CLI entry point for dependency guardian operations."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Dependency Guardian - Integrity Seal Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compute hash of dev.in
  python -m scripts.core.dependency_guardian compute dev

  # Inject seal into dev.txt
  python -m scripts.core.dependency_guardian seal dev

  # Validate dev.txt integrity
  python -m scripts.core.dependency_guardian validate dev

Exit Codes:
  0 - Success / Validation passed
  1 - Failure / Validation failed
        """,
    )

    parser.add_argument(
        "action",
        choices=["compute", "seal", "validate"],
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
                print("✅ Integrity seal VALID")
                sys.exit(0)
            else:
                print("❌ Integrity seal INVALID or MISSING")
                sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
