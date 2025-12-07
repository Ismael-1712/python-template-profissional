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

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class SecuritySeverity(str, Enum):
    """Severity levels for security patterns.

    Attributes:
        CRITICAL: Critical security issue requiring immediate attention
        HIGH: High severity issue that should be addressed soon
        MEDIUM: Medium severity issue for regular attention
        LOW: Low severity issue for informational purposes
    """

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SecurityCategory(str, Enum):
    """Categories for security patterns.

    Attributes:
        SECURITY: General security-related patterns
        SUBPROCESS: Subprocess execution and shell command patterns
        NETWORK: Network requests and socket operations
        FILESYSTEM: File system operations
    """

    SECURITY = "security"
    SUBPROCESS = "subprocess"
    NETWORK = "network"
    FILESYSTEM = "filesystem"


class SecurityPattern(BaseModel):
    """Represents a security pattern to detect in code.

    Attributes:
        pattern: The regex pattern or string to match in code
        severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        description: Human-readable description of the risk
        category: Category of the pattern (security, subprocess, network, etc.)
    """

    pattern: str
    severity: SecuritySeverity
    description: str
    category: SecurityCategory = SecurityCategory.SECURITY

    model_config = {"frozen": True}  # Make immutable


class AuditResult(BaseModel):
    """Represents an audit finding.

    Attributes:
        file_path: Path to the file containing the finding
        line_number: Line number where the pattern was found (must be > 0)
        pattern: The SecurityPattern that was matched
        code_snippet: The actual code snippet that matched
        suggestion: Optional suggestion for fixing the issue
    """

    file_path: Path
    line_number: int = Field(gt=0, description="Line number must be greater than 0")
    pattern: SecurityPattern
    code_snippet: str = Field(min_length=1, description="Code snippet cannot be empty")
    suggestion: str | None = None

    def to_dict(self) -> dict[str, str | int | None]:
        """Convert to dictionary for JSON serialization.

        Provided for backward compatibility. Prefer using model_dump() directly.

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
