"""Code Analysis Engine for Security Pattern Detection.

This module contains the core analysis logic for detecting security
vulnerabilities and code quality issues in Python files.

Classes:
    CodeAnalyzer: Performs static analysis on Python code

Author: DevOps Engineering Team
License: MIT
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path

from scripts.audit.models import AuditResult, SecurityPattern
from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem

# Configure module logger
logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Static code analyzer for security patterns.

    Analyzes Python source files to detect security vulnerabilities,
    unsafe patterns, and code quality issues based on configurable patterns.
    """

    def __init__(
        self,
        patterns: list[SecurityPattern],
        workspace_root: Path,
        max_findings_per_file: int = 50,
        fs_adapter: FileSystemAdapter | None = None,
    ) -> None:
        """Initialize the code analyzer.

        Args:
            patterns: List of SecurityPattern objects to detect
            workspace_root: Root directory of the workspace
            max_findings_per_file: Maximum findings to report per file
            fs_adapter: FileSystemAdapter for I/O operations (default: RealFileSystem)
        """
        self.patterns = patterns
        self.workspace_root = workspace_root.resolve()
        self.max_findings_per_file = max_findings_per_file
        self.fs = fs_adapter or RealFileSystem()

    # TODO: Refactor God Function - split into smaller validators
    def analyze_file(self, file_path: Path) -> list[AuditResult]:  # noqa: C901
        """Analyze a single Python file for security patterns.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            List of AuditResult objects containing findings

        Example:
            >>> analyzer = CodeAnalyzer(patterns, Path('.'))
            >>> findings = analyzer.analyze_file(Path('script.py'))
            >>> print(f"Found {len(findings)} issues")
        """
        findings: list[AuditResult] = []

        try:
            content = self.fs.read_text(file_path, encoding="utf-8")
            lines = content.splitlines()

            # Parse AST for syntax validation
            try:
                ast.parse(content)
            except SyntaxError as e:
                logger.warning("Syntax error in %s: %s", file_path, e)
                return findings

            # Check for patterns in each line
            for line_num, line in enumerate(lines, 1):
                for pattern in self.patterns:
                    if pattern.pattern in line:
                        # Check for suppression comments (noqa)
                        if self._is_suppressed(line, pattern):
                            continue

                        # Skip if it's in a comment or string literal
                        stripped_line = line.strip()
                        if stripped_line.startswith("#"):
                            continue
                        if self._is_in_string_literal(line, pattern.pattern):
                            continue

                        # Create suggestion based on pattern
                        suggestion = self._generate_suggestion(pattern, line)

                        # Make path relative to workspace
                        relative_path = self._get_relative_path(file_path)

                        finding = AuditResult(
                            file_path=relative_path,
                            line_number=line_num,
                            pattern=pattern,
                            code_snippet=line.strip(),
                            suggestion=suggestion,
                        )
                        findings.append(finding)

                        # Limit findings per file to avoid noise
                        if len(findings) >= self.max_findings_per_file:
                            logger.warning(
                                "Max findings reached for %s",
                                file_path,
                            )
                            return findings

        except OSError:
            logger.exception("Error reading file %s", file_path)
        except UnicodeDecodeError:
            logger.exception("Error decoding file %s", file_path)

        return findings

    def _is_suppressed(self, line: str, pattern: SecurityPattern) -> bool:
        """Check if a pattern is suppressed by noqa comment.

        Args:
            line: The line of code to check
            pattern: The security pattern to check suppression for

        Returns:
            True if the pattern is suppressed, False otherwise
        """
        noqa_match = re.search(r"#\s*noqa:\s*([\w,-]+)", line)
        if noqa_match:
            try:
                suppressed_categories = [
                    cat.strip().lower() for cat in noqa_match.group(1).split(",")
                ]
                if pattern.category.lower() in suppressed_categories:
                    return True
            except (AttributeError, IndexError):
                pass  # Ignore malformed noqa comments
        return False

    def _is_in_string_literal(self, line: str, pattern: str) -> bool:
        """Check if pattern is inside a string literal.

        Args:
            line: The line of code to check
            pattern: The pattern to look for

        Returns:
            True if pattern is inside a string literal, False otherwise
        """
        # Simple heuristic - check if pattern is between quotes
        pattern_index = line.find(pattern)
        if pattern_index == -1:
            return False

        before = line[:pattern_index]
        single_quotes = before.count("'") - before.count("\\'")
        double_quotes = before.count('"') - before.count('\\"')

        return (single_quotes % 2 == 1) or (double_quotes % 2 == 1)

    def _generate_suggestion(
        self,
        pattern: SecurityPattern,
        line: str,
    ) -> str:
        """Generate improvement suggestion based on pattern.

        Args:
            pattern: The security pattern that was matched
            line: The line of code containing the pattern

        Returns:
            Suggestion string for fixing the issue
        """
        suggestions = {
            "shell=True": (
                "Use shell=False with list arguments: "
                "subprocess.run(['command', 'arg1', 'arg2'])"
            ),
            "os.system(": "Replace with subprocess.run() using shell=False",
            "requests.get(": (
                "Consider mocking this request in tests using @patch or pytest-httpx"
            ),
            "subprocess.run(": "Ensure shell=False and validate all inputs",
        }

        for key, suggestion in suggestions.items():
            if key in line:
                return suggestion

        return f"Review {pattern.category} usage for security best practices"

    def _get_relative_path(self, file_path: Path) -> Path:
        """Convert absolute path to relative path from workspace root.

        Args:
            file_path: Path to convert

        Returns:
            Relative path from workspace root, or original if not in workspace
        """
        if not file_path.is_absolute():
            return file_path

        try:
            return file_path.relative_to(self.workspace_root)
        except ValueError:
            # Path is outside workspace, keep it absolute
            return file_path
