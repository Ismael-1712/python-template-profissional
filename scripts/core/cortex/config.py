"""Configuration constants for CORTEX documentation system.

This module contains all validation patterns, default values, and
configuration constants used throughout the CORTEX system.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import re
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
