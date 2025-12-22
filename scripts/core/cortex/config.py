"""Configuration constants for CORTEX documentation system.

This module contains all validation patterns, default values, and
configuration constants used throughout the CORTEX system.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ============================================================================
# VALIDATION PATTERNS
# ============================================================================

# Regex pattern for validating document IDs (kebab-case)
# Valid: "testing-guide", "api-v2", "sprint-1-summary"
# Invalid: "TestingGuide", "testing_guide", "testing guide"
ID_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Regex pattern for validating semantic version strings
# Valid: "1.0.0", "2.3.1", "10.20.30"
# Invalid: "1.0", "v1.0.0", "1.0.0-beta"
VERSION_PATTERN: re.Pattern[str] = re.compile(r"^\d+\.\d+\.\d+$")

# Regex pattern for validating ISO 8601 date format (YYYY-MM-DD)
# Valid: "2025-11-30", "2024-01-15"
# Invalid: "30/11/2025", "2025-11-30T10:00:00", "Nov 30, 2025"
DATE_PATTERN: re.Pattern[str] = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Regex pattern for validating context tags (kebab-case)
# Valid: "testing", "ci-cd", "api-v2"
# Invalid: "Testing", "ci_cd", "API v2"
TAG_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# ============================================================================
# ALLOWED VALUES
# ============================================================================

# Valid document types (must match DocType enum)
ALLOWED_TYPES: list[str] = ["guide", "arch", "reference", "history", "knowledge"]

# Valid document statuses (must match DocStatus enum)
ALLOWED_STATUSES: list[str] = ["draft", "active", "deprecated", "archived"]

# ============================================================================
# REQUIRED FIELDS
# ============================================================================

# Fields that MUST be present in frontmatter (validation will fail if missing)
REQUIRED_FIELDS: list[str] = [
    "id",
    "type",
    "status",
    "version",
    "author",
    "date",
]

# Fields that are strongly RECOMMENDED (will generate warnings if missing)
RECOMMENDED_FIELDS: list[str] = [
    "context_tags",
    "linked_code",
]

# Optional fields (no warnings if missing)
OPTIONAL_FIELDS: list[str] = [
    "dependencies",
    "related_docs",
]

# ============================================================================
# VALIDATION CONSTRAINTS
# ============================================================================

# Minimum length for author field (prevents empty or too-short values)
MIN_AUTHOR_LENGTH: int = 3

# Maximum number of context tags (prevents excessive tagging)
MAX_CONTEXT_TAGS: int = 10

# Maximum number of linked code files (prevents overly broad linking)
MAX_LINKED_CODE: int = 20

# Maximum number of related docs (prevents circular reference issues)
MAX_RELATED_DOCS: int = 10

# ============================================================================
# DEFAULT VALUES
# ============================================================================

# Default configuration for CORTEX operations
DEFAULT_CONFIG: dict[str, Any] = {
    # Directories to scan for documentation
    "scan_paths": ["docs/"],
    # File patterns to include in scans
    "file_patterns": ["*.md"],
    # Directories to exclude from scans
    "exclude_paths": [
        ".git/",
        "__pycache__/",
        ".venv/",
        "venv/",
        "node_modules/",
        ".pytest_cache/",
    ],
    # Whether to validate links to code files
    "validate_code_links": True,
    # Whether to validate links to other docs
    "validate_doc_links": True,
    # Whether to fail on validation warnings (or just errors)
    "strict_mode": False,
    # Maximum number of validation errors to report per file
    "max_errors_per_file": 50,
}

# ============================================================================
# ERROR MESSAGES
# ============================================================================

# Template error messages for common validation failures
ERROR_MESSAGES: dict[str, str] = {
    "missing_field": "Required field '{field}' is missing from frontmatter",
    "invalid_id": "Field 'id' must be in kebab-case format (e.g., 'my-doc-id')",
    "invalid_type": "Field 'type' must be one of: {allowed}",
    "invalid_status": "Field 'status' must be one of: {allowed}",
    "invalid_version": "Field 'version' must be in semver format (e.g., '1.0.0')",
    "invalid_date": "Field 'date' must be in ISO 8601 format (YYYY-MM-DD)",
    "invalid_author": "Field 'author' must be at least {min_length} characters",
    "invalid_tag": "Tag '{tag}' must be in kebab-case format",
    "too_many_tags": "Number of context_tags ({count}) exceeds maximum ({max})",
    "too_many_links": "Number of linked_code ({count}) exceeds maximum ({max})",
    "broken_code_link": "Linked code file does not exist: {path}",
    "broken_doc_link": "Related documentation file does not exist: {path}",
}

# ============================================================================
# WARNING MESSAGES
# ============================================================================

# Template warning messages for non-critical issues
WARNING_MESSAGES: dict[str, str] = {
    "missing_recommended": "Recommended field '{field}' is missing (not required)",
    "empty_tags": "Field 'context_tags' is empty (recommended for discoverability)",
    "empty_links": "Field 'linked_code' is empty (recommended for traceability)",
    "no_frontmatter": "File has no YAML frontmatter header",
}


# ============================================================================
# CONFIGURATION SCHEMA
# ============================================================================


@dataclass(frozen=True)
class CortexConfigSchema:
    """Immutable configuration schema for CORTEX operations.

    Provides type-safe configuration with defaults from DEFAULT_CONFIG.
    All fields are frozen to prevent accidental modification.

    Attributes:
        scan_paths: Directories to scan for documentation
        file_patterns: Glob patterns for files to include
        exclude_paths: Directories to exclude from scans
        validate_code_links: Whether to validate links to code files
        validate_doc_links: Whether to validate links to other docs
        strict_mode: Whether to fail on warnings (or just errors)
        max_errors_per_file: Maximum validation errors to report per file

    Examples:
        >>> config = CortexConfigSchema.from_dict({"scan_paths": ["custom/"]})
        >>> print(config.scan_paths)
        ["custom/"]
        >>> print(config.file_patterns)  # From defaults
        ["*.md"]
    """

    scan_paths: list[str] = field(default_factory=lambda: ["docs/"])
    file_patterns: list[str] = field(default_factory=lambda: ["*.md"])
    exclude_paths: list[str] = field(
        default_factory=lambda: [
            ".git/",
            "__pycache__/",
            ".venv/",
            "venv/",
            "node_modules/",
            ".pytest_cache/",
        ],
    )
    validate_code_links: bool = True
    validate_doc_links: bool = True
    strict_mode: bool = False
    max_errors_per_file: int = 50

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> CortexConfigSchema:
        """Create schema from dictionary, using defaults for missing keys.

        Args:
            config_dict: Configuration dictionary (possibly partial)

        Returns:
            Validated CortexConfigSchema instance

        Examples:
            >>> config = CortexConfigSchema.from_dict({
            ...     "scan_paths": ["custom/"],
            ...     "strict_mode": True
            ... })
        """
        # Extract only known fields
        known_fields = {
            "scan_paths",
            "file_patterns",
            "exclude_paths",
            "validate_code_links",
            "validate_doc_links",
            "strict_mode",
            "max_errors_per_file",
        }
        filtered = {k: v for k, v in config_dict.items() if k in known_fields}
        return cls(**filtered)

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary representation.

        Returns:
            Configuration as mutable dictionary

        Examples:
            >>> config = CortexConfigSchema()
            >>> config_dict = config.to_dict()
        """
        return {
            "scan_paths": list(self.scan_paths),
            "file_patterns": list(self.file_patterns),
            "exclude_paths": list(self.exclude_paths),
            "validate_code_links": self.validate_code_links,
            "validate_doc_links": self.validate_doc_links,
            "strict_mode": self.strict_mode,
            "max_errors_per_file": self.max_errors_per_file,
        }
