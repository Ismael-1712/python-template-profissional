"""Unit tests for sync aggregator module.

This test suite validates aggregation logic for sync results,
following TDD principles (tests written before implementation).

Test Coverage:
- Aggregate empty results
- Aggregate mixed success/error results
- Aggregate all successful results
- Aggregate all failed results
- Count accuracy (total, success, updated, not_modified, errors)

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path

from pydantic import HttpUrl

from scripts.core.cortex.knowledge_sync import SyncResult, SyncStatus
from scripts.core.cortex.models import DocStatus, KnowledgeEntry, KnowledgeSource
from scripts.core.cortex.sync_aggregator import SyncAggregator


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


class TestSyncAggregator:
    """Test cases for sync result aggregation."""

    def test_aggregate_empty_results(self) -> None:
        """Aggregator should handle empty result list."""
        # Arrange
        results: list[SyncResult] = []

        # Act
        summary = SyncAggregator.aggregate(results)

        # Assert
        assert summary.total_processed == 0
        assert summary.successful_count == 0
        assert summary.updated_count == 0
        assert summary.not_modified_count == 0
        assert summary.error_count == 0
        assert summary.results == []

    def test_aggregate_all_updated(self) -> None:
        """Aggregator should count all UPDATED statuses correctly."""
        # Arrange
        entry1 = _create_entry("kno-001")
        entry2 = _create_entry("kno-002")
        entry3 = _create_entry("kno-003")

        results = [
            SyncResult(entry=entry1, status=SyncStatus.UPDATED, error_message=None),
            SyncResult(entry=entry2, status=SyncStatus.UPDATED, error_message=None),
            SyncResult(entry=entry3, status=SyncStatus.UPDATED, error_message=None),
        ]

        # Act
        summary = SyncAggregator.aggregate(results)

        # Assert
        assert summary.total_processed == 3
        assert summary.successful_count == 3
        assert summary.updated_count == 3
        assert summary.not_modified_count == 0
        assert summary.error_count == 0

    def test_aggregate_all_not_modified(self) -> None:
        """Aggregator should count all NOT_MODIFIED statuses correctly."""
        # Arrange
        entry1 = _create_entry("kno-001")
        entry2 = _create_entry("kno-002")

        results = [
            SyncResult(
                entry=entry1,
                status=SyncStatus.NOT_MODIFIED,
                error_message=None,
            ),
            SyncResult(
                entry=entry2,
                status=SyncStatus.NOT_MODIFIED,
                error_message=None,
            ),
        ]

        # Act
        summary = SyncAggregator.aggregate(results)

        # Assert
        assert summary.total_processed == 2
        assert summary.successful_count == 2  # NOT_MODIFIED is still success
        assert summary.updated_count == 0
        assert summary.not_modified_count == 2
        assert summary.error_count == 0

    def test_aggregate_all_errors(self) -> None:
        """Aggregator should count all ERROR statuses correctly."""
        # Arrange
        entry1 = _create_entry("kno-001")
        entry2 = _create_entry("kno-002")

        results = [
            SyncResult(
                entry=entry1,
                status=SyncStatus.ERROR,
                error_message="Network timeout",
            ),
            SyncResult(entry=entry2, status=SyncStatus.ERROR, error_message="HTTP 500"),
        ]

        # Act
        summary = SyncAggregator.aggregate(results)

        # Assert
        assert summary.total_processed == 2
        assert summary.successful_count == 0
        assert summary.updated_count == 0
        assert summary.not_modified_count == 0
        assert summary.error_count == 2

    def test_aggregate_mixed_results(self) -> None:
        """Aggregator should handle mixed success/error results correctly."""
        # Arrange
        entry1 = _create_entry("kno-001")
        entry2 = _create_entry("kno-002")
        entry3 = _create_entry("kno-003")
        entry4 = _create_entry("kno-004")
        entry5 = _create_entry("kno-005")

        results = [
            SyncResult(entry=entry1, status=SyncStatus.UPDATED, error_message=None),
            SyncResult(
                entry=entry2,
                status=SyncStatus.NOT_MODIFIED,
                error_message=None,
            ),
            SyncResult(entry=entry3, status=SyncStatus.UPDATED, error_message=None),
            SyncResult(entry=entry4, status=SyncStatus.ERROR, error_message="Timeout"),
            SyncResult(
                entry=entry5,
                status=SyncStatus.NOT_MODIFIED,
                error_message=None,
            ),
        ]

        # Act
        summary = SyncAggregator.aggregate(results)

        # Assert
        assert summary.total_processed == 5
        assert summary.successful_count == 4  # 2 UPDATED + 2 NOT_MODIFIED
        assert summary.updated_count == 2
        assert summary.not_modified_count == 2
        assert summary.error_count == 1

    def test_aggregate_preserves_results_list(self) -> None:
        """Aggregator should preserve the original results list."""
        # Arrange
        entry1 = _create_entry("kno-001")
        entry2 = _create_entry("kno-002")

        results = [
            SyncResult(entry=entry1, status=SyncStatus.UPDATED, error_message=None),
            SyncResult(entry=entry2, status=SyncStatus.ERROR, error_message="Failed"),
        ]

        # Act
        summary = SyncAggregator.aggregate(results)

        # Assert
        assert len(summary.results) == 2
        assert summary.results[0].entry.id == "kno-001"
        assert summary.results[1].entry.id == "kno-002"
        assert summary.results == results  # Should be the same object

    def test_aggregate_success_count_calculation(self) -> None:
        """Successful count should be sum of updated + not_modified."""
        # Arrange
        entry1 = _create_entry("kno-001")
        entry2 = _create_entry("kno-002")
        entry3 = _create_entry("kno-003")

        results = [
            SyncResult(entry=entry1, status=SyncStatus.UPDATED, error_message=None),
            SyncResult(
                entry=entry2,
                status=SyncStatus.NOT_MODIFIED,
                error_message=None,
            ),
            SyncResult(entry=entry3, status=SyncStatus.ERROR, error_message="Error"),
        ]

        # Act
        summary = SyncAggregator.aggregate(results)

        # Assert
        assert (
            summary.successful_count
            == summary.updated_count + summary.not_modified_count
        )
        assert summary.successful_count == 2
