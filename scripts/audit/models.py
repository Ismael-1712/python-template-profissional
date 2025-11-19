"""Data Models for Code Audit System.

This module contains the core data structures used throughout the audit
system. All models are immutable where possible and designed for easy
serialization and type safety.

Classes:
    SecurityPattern: Represents a security pattern to detect in code
    AuditResult: Represents an individual audit finding

Author: DevOps Engineering Team
License: MIT
"""

from pathlib import Path
from typing import Any


class SecurityPattern:
    """Represents a security pattern to detect in code."""

    def __init__(
        self,
        pattern: str,
        severity: str,
        description: str,
        category: str = "security",
    ) -> None:
        """Initialize a security pattern.

        Args:
            pattern: The regex pattern or string to match in code
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            description: Human-readable description of the risk
            category: Category of the pattern (security, subprocess, network, etc.)
        """
        self.pattern = pattern
        self.severity = severity
        self.description = description
        self.category = category

    def __repr__(self) -> str:
        """Return string representation of the pattern."""
        return (
            f"SecurityPattern(pattern={self.pattern!r}, "
            f"severity={self.severity!r}, category={self.category!r})"
        )


class AuditResult:
    """Represents an audit finding."""

    def __init__(
        self,
        file_path: Path,
        line_number: int,
        pattern: SecurityPattern,
        code_snippet: str,
        suggestion: str | None = None,
    ) -> None:
        """Initialize an audit result.

        Args:
            file_path: Path to the file containing the finding
            line_number: Line number where the pattern was found
            pattern: The SecurityPattern that was matched
            code_snippet: The actual code snippet that matched
            suggestion: Optional suggestion for fixing the issue
        """
        self.file_path = file_path
        self.line_number = line_number
        self.pattern = pattern
        self.code_snippet = code_snippet
        self.suggestion = suggestion

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the audit result
        """
        return {
            "file": str(self.file_path),
            "line": self.line_number,
            "severity": self.pattern.severity,
            "category": self.pattern.category,
            "description": self.pattern.description,
            "code": self.code_snippet,
            "suggestion": self.suggestion,
        }

    def __repr__(self) -> str:
        """Return string representation of the result."""
        return (
            f"AuditResult(file={self.file_path}, line={self.line_number}, "
            f"severity={self.pattern.severity})"
        )
