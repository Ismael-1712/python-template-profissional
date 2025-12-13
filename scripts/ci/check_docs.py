#!/usr/bin/env python3
"""CI/CD Documentation Validator.

This script validates that the CLI documentation is up-to-date by comparing
the generated content with the committed version. It's designed to run in
CI/CD pipelines to prevent outdated documentation from being merged.

Features:
- Generates documentation in-memory (no file changes)
- Normalizes content by removing timestamps
- Shows diff when documentation is outdated
- Returns appropriate exit codes for CI/CD integration

Exit Codes:
    0: Documentation is up-to-date
    1: Documentation is outdated or validation failed

Usage:
    python scripts/ci/check_docs.py

Integration:
    Add to your CI/CD pipeline (GitHub Actions, GitLab CI, etc.):

    ```yaml
    - name: Validate Documentation
      run: python scripts/ci/check_docs.py
    ```

Author: DevOps Engineering Team
License: MIT
Version: 1.0.0
"""

from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.core.doc_gen import CLIDocGenerator  # noqa: E402


def normalize_content(content: str) -> str:
    """Normalize documentation content for comparison.

    Removes or normalizes elements that change on every generation
    but don't represent meaningful documentation changes.

    Args:
        content: Raw documentation content

    Returns:
        Normalized content ready for comparison
    """
    lines = content.split("\n")
    normalized_lines = []

    for line in lines:
        # Skip timestamp lines that change on every generation
        # Examples:
        # - "Gerado em: **2024-12-13 20:30 UTC**"
        # - "**Última Atualização:** 2024-12-13 20:30 UTC"
        # - "> Generated at: ..."
        if any(
            pattern in line.lower()
            for pattern in [
                "gerado em:",
                "generated at:",
                "última atualização:",
                "last update:",
            ]
        ):
            # Replace the timestamp with a placeholder
            line = re.sub(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}( UTC)?",
                "TIMESTAMP",
                line,
            )

        normalized_lines.append(line)

    return "\n".join(normalized_lines)


def show_diff(expected: str, actual: str, context_lines: int = 3) -> None:
    """Display a unified diff between expected and actual content.

    Args:
        expected: Expected content (from repository)
        actual: Actual generated content
        context_lines: Number of context lines to show around differences
    """
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)

    diff = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile="docs/reference/CLI_COMMANDS.md (committed)",
        tofile="docs/reference/CLI_COMMANDS.md (generated)",
        lineterm="",
        n=context_lines,
    )

    print("\n📊 Diff (committed vs generated):\n")
    print("".join(diff))


def validate_documentation() -> int:
    """Validate that committed documentation matches generated version.

    Returns:
        Exit code (0 = valid, 1 = outdated or error)
    """
    try:
        # Path to the committed documentation file
        docs_path = PROJECT_ROOT / "docs" / "reference" / "CLI_COMMANDS.md"

        # Check if file exists
        if not docs_path.exists():
            print("❌ Documentation file not found!")
            print(f"   Expected: {docs_path}")
            print("\n💡 Hint: Run 'python scripts/core/doc_gen.py' to generate it.")
            return 1

        # Read committed documentation
        committed_content = docs_path.read_text(encoding="utf-8")

        # Generate fresh documentation (in-memory, no file writes)
        print("🔄 Generating documentation for validation...")
        generator = CLIDocGenerator(docs_path)
        generated_content = generator.generate_documentation()

        # Normalize both versions for comparison
        normalized_committed = normalize_content(committed_content)
        normalized_generated = normalize_content(generated_content)

        # Compare normalized content
        if normalized_committed == normalized_generated:
            print("✅ Documentation is up-to-date.")
            return 0

        # Documentation is outdated
        print("❌ Documentation is outdated!")
        print("\n📋 The committed documentation doesn't match the generated version.")
        print(
            "   This usually means CLI commands were modified but docs "
            "weren't updated.",
        )

        # Show diff for debugging
        show_diff(normalized_committed, normalized_generated)

        print("\n🔧 To fix this:")
        print("   1. Run: python scripts/core/doc_gen.py")
        print("   2. Review the changes in docs/reference/CLI_COMMANDS.md")
        print("   3. Commit the updated documentation")
        print("   4. Push the changes")

        return 1

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements/dev.txt")
        return 1

    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point for CI documentation validation.

    Returns:
        Exit code for CI/CD pipeline
    """
    print("=" * 70)
    print("🔍 CI/CD Documentation Validator")
    print("=" * 70)
    print()

    exit_code = validate_documentation()

    print()
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
