"""Filtering utilities for knowledge entry synchronization.

This module provides pure domain logic for filtering knowledge entries
based on various criteria (ID, presence of sources, validation for sync).

Following Hexagonal Architecture principles:
- Pure domain logic (no I/O, no logging)
- Stateless functions (class methods as namespace)
- Explicit error handling via exceptions and validation results

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass

from scripts.core.cortex.models import KnowledgeEntry


@dataclass
class ValidationResult:
    """Result of validating an entry for sync operations.

    Attributes:
        is_valid: Whether the entry is valid for synchronization
        error_message: Description of validation failure (None if valid)
    """

    is_valid: bool
    error_message: str | None = None


class EntryFilter:
    """Pure domain logic for filtering knowledge entries.

    This class provides static methods for filtering entries based on
    various criteria. No side effects (I/O, logging) - pure functions only.

    All methods are stateless and can be called without instantiation.
    """

    @staticmethod
    def filter_by_id(
        entries: list[KnowledgeEntry],
        entry_id: str,
    ) -> list[KnowledgeEntry]:
        """Filter entries to find a specific entry by ID.

        Args:
            entries: List of knowledge entries to search
            entry_id: Target entry ID to find

        Returns:
            List containing single matching entry

        Raises:
            ValueError: If entry_id is not found in the list

        Example:
            >>> entries = [entry1, entry2, entry3]
            >>> result = EntryFilter.filter_by_id(entries, "kno-002")
            >>> len(result)
            1
        """
        filtered = [e for e in entries if e.id == entry_id]

        if not filtered:
            # Provide helpful error with available IDs
            available_ids = ", ".join(e.id for e in entries)
            msg = f"Entry '{entry_id}' not found"
            if available_ids:
                msg += f". Available entries: {available_ids}"
            raise ValueError(msg)

        return filtered

    @staticmethod
    def filter_by_sources(
        entries: list[KnowledgeEntry],
    ) -> list[KnowledgeEntry]:
        """Filter entries to only those with external sources.

        Args:
            entries: List of knowledge entries to filter

        Returns:
            List of entries that have at least one external source

        Example:
            >>> entries = [entry_with_source, entry_without_source]
            >>> result = EntryFilter.filter_by_sources(entries)
            >>> all(len(e.sources) > 0 for e in result)
            True
        """
        return [e for e in entries if e.sources]

    @staticmethod
    def validate_entry_for_sync(entry: KnowledgeEntry) -> ValidationResult:
        """Validate that an entry is ready for synchronization.

        Checks:
        - Entry has a file_path (required for writing updates)
        - Entry has at least one external source

        Args:
            entry: Knowledge entry to validate

        Returns:
            ValidationResult with success/failure status and error details

        Example:
            >>> result = EntryFilter.validate_entry_for_sync(entry)
            >>> if not result.is_valid:
            ...     print(f"Validation failed: {result.error_message}")
        """
        # Check for file_path (required for persistence)
        if not entry.file_path:
            return ValidationResult(
                is_valid=False,
                error_message=f"Missing file_path attribute for entry {entry.id}",
            )

        # Check for external sources
        if not entry.sources:
            return ValidationResult(
                is_valid=False,
                error_message=f"Entry '{entry.id}' has no external sources",
            )

        # All validations passed
        return ValidationResult(is_valid=True, error_message=None)
