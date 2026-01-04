"""Unit tests for sync filters module.

This test suite validates filtering logic for knowledge entries,
following TDD principles (tests written before implementation).

Test Coverage:
- Filter by entry ID (exact match, not found, empty list)
- Filter by sources (entries with/without sources)
- Edge cases (empty inputs, None values)

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import HttpUrl

from scripts.core.cortex.models import DocStatus, KnowledgeEntry, KnowledgeSource
from scripts.core.cortex.sync_filters import EntryFilter


def _create_entry(
    entry_id: str,
    has_sources: bool = False,
    file_path: Path | None = None,
) -> KnowledgeEntry:
    """Helper to create KnowledgeEntry for tests.

    Args:
        entry_id: Unique identifier for the entry
        has_sources: If True, adds a dummy external source
        file_path: Optional file path for the entry

    Returns:
        KnowledgeEntry instance
    """
    sources = []
    if has_sources:
        sources = [
            KnowledgeSource(
                url=HttpUrl("https://example.com/doc.md"),
                etag='"test-etag"',
            ),
        ]

    return KnowledgeEntry(
        id=entry_id,
        status=DocStatus.ACTIVE,
        tags=["test"],
        golden_paths=[],
        sources=sources,
        file_path=file_path,
    )


class TestEntryFilterById:
    """Test cases for filtering entries by ID."""

    def test_filter_by_id_found(self) -> None:
        """Filter should return single matching entry when ID exists."""
        # Arrange
        entries = [
            _create_entry("kno-001"),
            _create_entry("kno-002"),
            _create_entry("kno-003"),
        ]

        # Act
        result = EntryFilter.filter_by_id(entries, "kno-002")

        # Assert
        assert len(result) == 1
        assert result[0].id == "kno-002"

    def test_filter_by_id_not_found_raises_error(self) -> None:
        """Filter should raise ValueError when ID doesn't exist."""
        # Arrange
        entries = [
            _create_entry("kno-001"),
            _create_entry("kno-002"),
        ]

        # Act & Assert
        with pytest.raises(ValueError, match="Entry 'kno-999' not found"):
            EntryFilter.filter_by_id(entries, "kno-999")

    def test_filter_by_id_includes_available_ids_in_error(self) -> None:
        """Error message should include list of available IDs."""
        # Arrange
        entries = [
            _create_entry("kno-001"),
            _create_entry("kno-002"),
            _create_entry("kno-003"),
        ]

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Available entries:.*kno-001.*kno-002.*kno-003",
        ):
            EntryFilter.filter_by_id(entries, "kno-999")

    def test_filter_by_id_empty_list_raises_error(self) -> None:
        """Filter should raise ValueError when entry list is empty."""
        # Arrange
        entries: list[KnowledgeEntry] = []

        # Act & Assert
        with pytest.raises(ValueError, match="Entry 'kno-001' not found"):
            EntryFilter.filter_by_id(entries, "kno-001")

    def test_filter_by_id_case_sensitive(self) -> None:
        """Filter should be case-sensitive for entry IDs."""
        # Arrange
        entries = [_create_entry("kno-001")]

        # Act & Assert
        with pytest.raises(ValueError, match="Entry 'KNO-001' not found"):
            EntryFilter.filter_by_id(entries, "KNO-001")


class TestEntryFilterBySources:
    """Test cases for filtering entries by presence of sources."""

    def test_filter_by_sources_returns_only_entries_with_sources(self) -> None:
        """Filter should return only entries that have sources."""
        # Arrange
        entries = [
            _create_entry("kno-001", has_sources=True),
            _create_entry("kno-002", has_sources=False),
            _create_entry("kno-003", has_sources=True),
            _create_entry("kno-004", has_sources=False),
        ]

        # Act
        result = EntryFilter.filter_by_sources(entries)

        # Assert
        assert len(result) == 2
        assert result[0].id == "kno-001"
        assert result[1].id == "kno-003"
        # Verify all results have sources
        for entry in result:
            assert len(entry.sources) > 0

    def test_filter_by_sources_empty_list(self) -> None:
        """Filter should return empty list when no entries have sources."""
        # Arrange
        entries = [
            _create_entry("kno-001", has_sources=False),
            _create_entry("kno-002", has_sources=False),
        ]

        # Act
        result = EntryFilter.filter_by_sources(entries)

        # Assert
        assert len(result) == 0

    def test_filter_by_sources_all_have_sources(self) -> None:
        """Filter should return all entries when all have sources."""
        # Arrange
        entries = [
            _create_entry("kno-001", has_sources=True),
            _create_entry("kno-002", has_sources=True),
        ]

        # Act
        result = EntryFilter.filter_by_sources(entries)

        # Assert
        assert len(result) == 2

    def test_filter_by_sources_empty_input(self) -> None:
        """Filter should handle empty input list gracefully."""
        # Arrange
        entries: list[KnowledgeEntry] = []

        # Act
        result = EntryFilter.filter_by_sources(entries)

        # Assert
        assert len(result) == 0
        assert result == []


class TestEntryFilterValidateEntryForSync:
    """Test cases for validating entries before sync."""

    def test_validate_entry_with_file_path_success(self) -> None:
        """Validation should pass for entry with file_path."""
        # Arrange
        entry = _create_entry("kno-001", has_sources=True, file_path=Path("doc.md"))

        # Act
        result = EntryFilter.validate_entry_for_sync(entry)

        # Assert
        assert result.is_valid is True
        assert result.error_message is None

    def test_validate_entry_without_file_path_fails(self) -> None:
        """Validation should fail for entry without file_path."""
        # Arrange
        entry = _create_entry("kno-001", has_sources=True, file_path=None)

        # Act
        result = EntryFilter.validate_entry_for_sync(entry)

        # Assert
        assert result.is_valid is False
        assert result.error_message is not None
        assert "Missing file_path" in result.error_message

    def test_validate_entry_without_sources_fails(self) -> None:
        """Validation should fail for entry without sources."""
        # Arrange
        entry = _create_entry("kno-001", has_sources=False, file_path=Path("doc.md"))

        # Act
        result = EntryFilter.validate_entry_for_sync(entry)

        # Assert
        assert result.is_valid is False
        assert result.error_message is not None
        assert "no external sources" in result.error_message
