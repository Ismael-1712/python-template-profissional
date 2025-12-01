"""Data models for CORTEX documentation system.

This module defines the core data structures used throughout CORTEX,
including enums for document types and statuses, and dataclasses for
representing document metadata and validation results.

Author: Engineering Team
License: MIT
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path


class DocType(Enum):
    """Types of documentation files.

    Attributes:
        GUIDE: User guides and how-to documentation
        ARCH: Architecture and design documents
        REFERENCE: API references and technical specs
        HISTORY: Historical records and changelog entries
    """

    GUIDE = "guide"
    ARCH = "arch"
    REFERENCE = "reference"
    HISTORY = "history"


class DocStatus(Enum):
    """Lifecycle status of documentation files.

    Attributes:
        DRAFT: Document is in draft state, not yet published
        ACTIVE: Document is current and actively maintained
        DEPRECATED: Document is outdated but kept for reference
        ARCHIVED: Document is historical and no longer relevant
    """

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class DocumentMetadata:
    """Structured representation of YAML frontmatter in documentation.

    This class represents all metadata extracted from a documentation file's
    YAML frontmatter header. All fields map directly to the YAML schema
    defined in the CORTEX design specification.

    Attributes:
        id: Unique identifier in kebab-case format
        type: Document type (guide, arch, reference, or history)
        status: Lifecycle status of the document
        version: Semantic version string (e.g., "1.0.0")
        author: Author or team name
        date: Publication or last update date
        context_tags: List of tags for categorization and search
        linked_code: List of relative paths to related Python files
        dependencies: Optional list of external package dependencies
        related_docs: Optional list of paths to related documentation
        source_file: Path to the source .md file (set during parsing)

    Example:
        >>> metadata = DocumentMetadata(
        ...     id="testing-guide",
        ...     type=DocType.GUIDE,
        ...     status=DocStatus.ACTIVE,
        ...     version="1.0.0",
        ...     author="Engineering Team",
        ...     date=date(2025, 11, 30),
        ...     context_tags=["testing", "pytest"],
        ...     linked_code=["tests/conftest.py"],
        ... )
    """

    id: str
    type: DocType
    status: DocStatus
    version: str
    author: str
    date: date
    context_tags: list[str] = field(default_factory=list)
    linked_code: list[str] = field(default_factory=list)
    dependencies: list[str] | None = None
    related_docs: list[str] | None = None
    source_file: Path | None = None


@dataclass
class ValidationResult:
    """Result of frontmatter metadata validation.

    Contains the validation status and any errors or warnings found
    during metadata schema validation.

    Attributes:
        is_valid: True if metadata passes all validation rules
        errors: List of validation error messages (blocking issues)
        warnings: List of validation warning messages (non-blocking)

    Example:
        >>> result = ValidationResult(
        ...     is_valid=False,
        ...     errors=["Field 'id' must be in kebab-case format"],
        ...     warnings=["Field 'context_tags' is empty but recommended"],
        ... )
    """

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class LinkCheckResult:
    """Result of documentation link validation.

    Contains information about broken or missing links between
    documentation and code files.

    Attributes:
        file: Path to the documentation file being checked
        broken_code_links: List of linked_code paths that don't exist
        broken_doc_links: List of related_docs paths that don't exist
        missing_files: List of any other referenced files that are missing

    Example:
        >>> result = LinkCheckResult(
        ...     file=Path("docs/guide.md"),
        ...     broken_code_links=["scripts/missing.py"],
        ...     broken_doc_links=[],
        ...     missing_files=[],
        ... )
    """

    file: Path
    broken_code_links: list[str] = field(default_factory=list)
    broken_doc_links: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
