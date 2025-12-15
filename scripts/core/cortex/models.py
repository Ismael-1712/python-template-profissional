"""Data models for CORTEX documentation system.

This module defines the core data structures used throughout CORTEX,
including enums for document types and statuses, and dataclasses for
representing document metadata and validation results.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class DocType(Enum):
    """Types of documentation files.

    Attributes:
        GUIDE: User guides and how-to documentation
        ARCH: Architecture and design documents
        REFERENCE: API references and technical specs
        HISTORY: Historical records and changelog entries
        KNOWLEDGE: Knowledge base and contextual documentation
    """

    GUIDE = "guide"
    ARCH = "arch"
    REFERENCE = "reference"
    HISTORY = "history"
    KNOWLEDGE = "knowledge"


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


class LinkType(Enum):
    """Types of semantic links in CORTEX Knowledge Graph.

    Attributes:
        MARKDOWN: Standard markdown link [label](target)
        WIKILINK: Simple wikilink [[target]]
        WIKILINK_ALIASED: Aliased wikilink [[target|alias]]
        CODE_REFERENCE: Code reference [[code:path]] or [[code:path::Symbol]]
    """

    MARKDOWN = "markdown"
    WIKILINK = "wikilink"
    WIKILINK_ALIASED = "wikilink_aliased"
    CODE_REFERENCE = "code_reference"


class LinkStatus(Enum):
    """Status of link resolution and validation.

    Attributes:
        UNRESOLVED: Link has not been resolved yet
        VALID: Link was successfully resolved to a target
        BROKEN: Link target could not be found
        EXTERNAL: Link points to external resource (http/https)
        AMBIGUOUS: Link matches multiple targets
    """

    UNRESOLVED = "unresolved"
    VALID = "valid"
    BROKEN = "broken"
    EXTERNAL = "external"
    AMBIGUOUS = "ambiguous"


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


class KnowledgeSource(BaseModel):
    """External source of knowledge for the Knowledge Node.

    Represents an external URL that provides knowledge content,
    with metadata for synchronization and caching.

    Attributes:
        url: HTTP/HTTPS URL of the knowledge source
        last_synced: Timestamp of last successful sync (None if never synced)
        etag: HTTP ETag header for cache validation

    Example:
        >>> source = KnowledgeSource(
        ...     url="https://example.com/docs/guide.md",
        ...     last_synced=datetime(2025, 12, 7, 10, 30),
        ...     etag='"abc123"',
        ... )
    """

    url: HttpUrl
    last_synced: datetime | None = None
    etag: str | None = None

    model_config = ConfigDict(frozen=True)


class KnowledgeLink(BaseModel):
    """Semantic link between Knowledge Nodes.

    Represents a directional link from one Knowledge Node to another,
    extracted from markdown content using regex patterns.

    Attributes:
        source_id: ID of the source Knowledge Node
        target_raw: Raw string extracted from content (before resolution)
        target_resolved: Resolved target ID or path (None if unresolved)
        target_id: Resolved Knowledge Node ID (None if not a knowledge node)
        type: Type of link (markdown, wikilink, code reference)
        line_number: Line number where link was found (1-indexed)
        context: Snippet of text around the link for context
        status: Resolution status (UNRESOLVED, VALID, BROKEN, etc)
        is_valid: True if target was successfully resolved and validated (deprecated)

    Example:
        >>> link = KnowledgeLink(
        ...     source_id="kno-001",
        ...     target_raw="Fase 01",
        ...     target_resolved="kno-002",
        ...     target_id="kno-002",
        ...     type=LinkType.WIKILINK,
        ...     line_number=42,
        ...     context="...Veja [[Fase 01]] para mais...",
        ...     status=LinkStatus.VALID,
        ...     is_valid=True,
        ... )
    """

    source_id: str
    target_raw: str
    target_resolved: str | None = None
    target_id: str | None = None
    type: LinkType
    line_number: int
    context: str
    status: LinkStatus = LinkStatus.UNRESOLVED
    is_valid: bool = False

    model_config = ConfigDict(frozen=True)


class KnowledgeEntry(BaseModel):
    """Knowledge Node entry with rich metadata and external sources.

    Represents a unit of knowledge in the CORTEX system, with support
    for external sources, golden path rules, and content caching.

    Attributes:
        id: Unique identifier in kebab-case (e.g., "kno-001")
        type: Fixed literal "knowledge" for type discrimination
        status: Lifecycle status (uses DocStatus enum)
        tags: List of categorization tags
        golden_paths: Immutable rules or paths for this knowledge
        sources: List of external knowledge sources
        cached_content: Optional cached content from sources
        links: List of semantic links extracted from cached_content
        file_path: Path to the source .md file (excluded from serialization)

    Example:
        >>> entry = KnowledgeEntry(
        ...     id="kno-001",
        ...     status=DocStatus.ACTIVE,
        ...     tags=["api", "authentication"],
        ...     golden_paths="auth/jwt.py -> docs/auth.md",
        ...     sources=[
        ...         KnowledgeSource(url="https://example.com/docs/auth.md")
        ...     ],
        ... )
    """

    id: str
    type: Literal["knowledge"] = "knowledge"
    status: DocStatus
    tags: list[str] = Field(default_factory=list)
    golden_paths: list[str] = Field(default_factory=list)
    sources: list[KnowledgeSource] = Field(default_factory=list)
    cached_content: str | None = None
    links: list[KnowledgeLink] = Field(default_factory=list)
    inbound_links: list[str] = Field(default_factory=list)
    file_path: Path | None = Field(default=None, exclude=True)

    model_config = ConfigDict(frozen=True)
