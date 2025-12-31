"""Frontmatter parser and validator for CORTEX documentation system.

This module provides functionality to extract and validate YAML frontmatter
from Markdown files, ensuring compliance with the CORTEX schema.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

import frontmatter
import yaml

from scripts.core.cortex.config import (
    ALLOWED_STATUSES,
    ALLOWED_TYPES,
    DATE_PATTERN,
    ERROR_MESSAGES,
    ID_PATTERN,
    MAX_CONTEXT_TAGS,
    MAX_LINKED_CODE,
    MAX_RELATED_DOCS,
    MIN_AUTHOR_LENGTH,
    RECOMMENDED_FIELDS,
    REQUIRED_FIELDS,
    TAG_PATTERN,
    VERSION_PATTERN,
    WARNING_MESSAGES,
)
from scripts.core.cortex.models import (
    DocStatus,
    DocType,
    DocumentMetadata,
    ValidationResult,
)
from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem

logger = logging.getLogger(__name__)


class FrontmatterParseError(Exception):
    """Raised when frontmatter cannot be parsed from a file."""


class FrontmatterParser:
    """Parser for YAML frontmatter in Markdown documentation files.

    This class handles extraction of metadata from Markdown files and
    validates it against the CORTEX schema defined in config.py.

    Example:
        >>> parser = FrontmatterParser()
        >>> metadata = parser.parse_file(Path("docs/guide.md"))
        >>> result = parser.validate_metadata(metadata_dict)
    """

    def __init__(self, fs: FileSystemAdapter | None = None) -> None:
        """Initialize the frontmatter parser.

        Args:
            fs: FileSystemAdapter for I/O operations (default: RealFileSystem)
        """
        if fs is None:
            fs = RealFileSystem()
        self.fs = fs
        self.logger = logging.getLogger(__name__)

    def parse_file(self, path: Path) -> DocumentMetadata:
        """Extract and validate frontmatter from a Markdown file.

        Reads a Markdown file, extracts YAML frontmatter, validates it
        against the CORTEX schema, and returns a DocumentMetadata object.

        Args:
            path: Path to the Markdown file to parse

        Returns:
            DocumentMetadata object with validated metadata

        Raises:
            FrontmatterParseError: If file cannot be read or has no frontmatter
            ValueError: If frontmatter validation fails

        Example:
            >>> parser = FrontmatterParser()
            >>> metadata = parser.parse_file(Path("docs/testing-guide.md"))
            >>> print(metadata.id)
            'testing-guide'
        """
        # Validate file exists
        if not self.fs.exists(path):
            raise FrontmatterParseError(f"File does not exist: {path}")

        # Validate file is readable
        if not self.fs.is_file(path):
            raise FrontmatterParseError(f"Path is not a file: {path}")

        try:
            # Read file and parse frontmatter
            content = self.fs.read_text(path)
            post = frontmatter.loads(content)

            # Check if frontmatter exists
            if not post.metadata:
                raise FrontmatterParseError(
                    f"No YAML frontmatter found in file: {path}",
                )

            # Validate metadata schema
            validation_result = self.validate_metadata(post.metadata)

            if not validation_result.is_valid:
                error_msg = "\n  ".join(validation_result.errors)
                raise ValueError(
                    f"Frontmatter validation failed for {path}:\n  {error_msg}",
                )

            # Log warnings if any
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    self.logger.warning(f"{path}: {warning}")

            # Convert to DocumentMetadata
            metadata = self._dict_to_metadata(post.metadata, path)
            return metadata

        except yaml.YAMLError as e:
            raise FrontmatterParseError(f"Invalid YAML in frontmatter: {e}") from e
        except OSError as e:
            raise FrontmatterParseError(f"Cannot read file {path}: {e}") from e

    # TODO: Refactor God Function - split validation rules into dedicated validators
    def validate_metadata(self, metadata: dict[str, Any]) -> ValidationResult:  # noqa: C901
        """Validate frontmatter metadata against CORTEX schema.

        Checks all required fields, validates formats (ID, version, date),
        and ensures enum values are valid.

        Args:
            metadata: Dictionary of frontmatter metadata to validate

        Returns:
            ValidationResult with is_valid flag and any errors/warnings

        Example:
            >>> parser = FrontmatterParser()
            >>> result = parser.validate_metadata({
            ...     "id": "test-doc",
            ...     "type": "guide",
            ...     "status": "active",
            ...     "version": "1.0.0",
            ...     "author": "Team",
            ...     "date": "2025-11-30",
            ... })
            >>> print(result.is_valid)
            True
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in metadata or metadata[field] is None:
                errors.append(ERROR_MESSAGES["missing_field"].format(field=field))

        # If missing required fields, return early
        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Validate ID format (kebab-case)
        if not ID_PATTERN.match(metadata["id"]):
            errors.append(ERROR_MESSAGES["invalid_id"])

        # Validate type enum
        if metadata["type"] not in ALLOWED_TYPES:
            errors.append(
                ERROR_MESSAGES["invalid_type"].format(allowed=", ".join(ALLOWED_TYPES)),
            )

        # Validate status enum
        if metadata["status"] not in ALLOWED_STATUSES:
            errors.append(
                ERROR_MESSAGES["invalid_status"].format(
                    allowed=", ".join(ALLOWED_STATUSES),
                ),
            )

        # Validate version format (semver)
        if not VERSION_PATTERN.match(metadata["version"]):
            errors.append(ERROR_MESSAGES["invalid_version"])

        # Validate date format (ISO 8601)
        date_str = str(metadata["date"])
        if not DATE_PATTERN.match(date_str):
            errors.append(ERROR_MESSAGES["invalid_date"])

        # Validate author minimum length
        if len(metadata["author"]) < MIN_AUTHOR_LENGTH:
            errors.append(
                ERROR_MESSAGES["invalid_author"].format(min_length=MIN_AUTHOR_LENGTH),
            )

        # Validate context_tags format (if present)
        if metadata.get("context_tags"):
            tags = metadata["context_tags"]
            if not isinstance(tags, list):
                errors.append("Field 'context_tags' must be a list")
            else:
                for tag in tags:
                    if not TAG_PATTERN.match(tag):
                        errors.append(ERROR_MESSAGES["invalid_tag"].format(tag=tag))

                if len(tags) > MAX_CONTEXT_TAGS:
                    errors.append(
                        ERROR_MESSAGES["too_many_tags"].format(
                            count=len(tags),
                            max=MAX_CONTEXT_TAGS,
                        ),
                    )

        # Validate linked_code constraints (if present)
        if metadata.get("linked_code"):
            links = metadata["linked_code"]
            if not isinstance(links, list):
                errors.append("Field 'linked_code' must be a list")
            elif len(links) > MAX_LINKED_CODE:
                errors.append(
                    ERROR_MESSAGES["too_many_links"].format(
                        count=len(links),
                        max=MAX_LINKED_CODE,
                    ),
                )

        # Validate related_docs constraints (if present)
        if metadata.get("related_docs"):
            docs = metadata["related_docs"]
            if not isinstance(docs, list):
                errors.append("Field 'related_docs' must be a list")
            elif len(docs) > MAX_RELATED_DOCS:
                errors.append(
                    f"Number of related_docs ({len(docs)}) exceeds maximum "
                    f"({MAX_RELATED_DOCS})",
                )

        # Validate Knowledge Nodes MUST have golden_paths
        if metadata.get("type") == "knowledge":
            golden_paths = metadata.get("golden_paths")
            if not golden_paths:
                errors.append("Knowledge Nodes MUST have 'golden_paths' field")
            elif not isinstance(golden_paths, list):
                errors.append("Field 'golden_paths' must be a list")
            elif len(golden_paths) == 0:
                errors.append("Knowledge Nodes MUST have non-empty 'golden_paths' list")

        # Check for recommended fields (warnings only)
        for field in RECOMMENDED_FIELDS:
            if field not in metadata or not metadata[field]:
                warnings.append(
                    WARNING_MESSAGES["missing_recommended"].format(field=field),
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _dict_to_metadata(
        self,
        metadata: dict[str, Any],
        source_file: Path,
    ) -> DocumentMetadata:
        """Convert validated metadata dictionary to DocumentMetadata object.

        Args:
            metadata: Validated metadata dictionary
            source_file: Path to source .md file

        Returns:
            DocumentMetadata instance
        """
        # Parse date string to date object
        date_str = str(metadata["date"])
        if isinstance(metadata["date"], date):
            doc_date = metadata["date"]
        else:
            doc_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Convert type and status strings to enums
        doc_type = DocType(metadata["type"])
        doc_status = DocStatus(metadata["status"])

        # Build DocumentMetadata
        return DocumentMetadata(
            id=metadata["id"],
            type=doc_type,
            status=doc_status,
            version=metadata["version"],
            author=metadata["author"],
            date=doc_date,
            context_tags=metadata.get("context_tags", []),
            linked_code=metadata.get("linked_code", []),
            dependencies=metadata.get("dependencies"),
            related_docs=metadata.get("related_docs"),
            source_file=source_file,
        )

    def extract_missing_fields(self, metadata: dict[str, Any]) -> list[str]:
        """Identify required fields that are missing from metadata.

        Args:
            metadata: Metadata dictionary to check

        Returns:
            List of missing required field names

        Example:
            >>> parser = FrontmatterParser()
            >>> missing = parser.extract_missing_fields({"id": "test"})
            >>> print(missing)
            ['type', 'status', 'version', 'author', 'date']
        """
        return [
            field
            for field in REQUIRED_FIELDS
            if field not in metadata or metadata[field] is None
        ]
