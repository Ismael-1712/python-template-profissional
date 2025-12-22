"""Unit tests for KnowledgeOrchestrator.

This test suite validates the orchestration logic for knowledge base operations,
including scanning, filtering, and bulk synchronization.

Test Coverage:
- Scan operation with and without entries
- Sync with specific entry_id filtering
- Sync all entries
- Dry run mode
- Error handling and aggregation
- Edge cases (empty workspace, missing sources, etc.)

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import HttpUrl

from scripts.core.cortex.knowledge_orchestrator import (
    KnowledgeOrchestrator,
    ScanResult,
    SyncSummary,
)
from scripts.core.cortex.knowledge_sync import SyncResult, SyncStatus
from scripts.core.cortex.models import DocStatus, KnowledgeEntry, KnowledgeSource
from scripts.utils.filesystem import MemoryFileSystem


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


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """Provide a temporary workspace root for each test."""
    return tmp_path


@pytest.fixture
def memory_fs() -> MemoryFileSystem:
    """Provide a clean in-memory filesystem for each test."""
    return MemoryFileSystem()


class TestScan:
    """Test cases for the scan operation."""

    def test_scan_returns_structured_result(self, workspace_root: Path) -> None:
        """Scan should return ScanResult with metadata."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        # Mock scanner to return test entries
        mock_entries = [
            _create_entry("kno-001", has_sources=True),
            _create_entry("kno-002", has_sources=False),
            _create_entry("kno-003", has_sources=True),
        ]

        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Act
            result = orchestrator.scan()

        # Assert
        assert isinstance(result, ScanResult)
        assert result.total_count == 3
        assert len(result.entries) == 3
        assert len(result.entries_with_sources) == 2
        assert result.entries_with_sources[0].id == "kno-001"
        assert result.entries_with_sources[1].id == "kno-003"

    def test_scan_with_no_entries(self, workspace_root: Path) -> None:
        """Scan should handle empty workspace gracefully."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        with patch.object(orchestrator.scanner, "scan", return_value=[]):
            # Act
            result = orchestrator.scan()

        # Assert
        assert result.total_count == 0
        assert len(result.entries) == 0
        assert len(result.entries_with_sources) == 0

    def test_scan_verbose_mode(self, workspace_root: Path) -> None:
        """Scan with verbose=True should log entry details."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)
        mock_entries = [_create_entry("kno-001", has_sources=True)]

        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Act
            result = orchestrator.scan(verbose=True)

        # Assert
        assert result.total_count == 1
        # Verbose mode should work without errors (logging is tested separately)


class TestSyncMultiple:
    """Test cases for the sync_multiple operation."""

    def test_sync_all_entries_success(self, workspace_root: Path) -> None:
        """Sync all entries should process all entries with sources."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        entry1 = _create_entry("kno-001", has_sources=True, file_path=Path("doc1.md"))
        entry2 = _create_entry("kno-002", has_sources=True, file_path=Path("doc2.md"))
        entry3 = _create_entry("kno-003", has_sources=False)

        mock_entries = [entry1, entry2, entry3]

        # Mock scanner
        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Mock syncer to return successful results
            mock_sync_results = [
                SyncResult(
                    entry=entry1,
                    status=SyncStatus.UPDATED,
                    error_message=None,
                ),
                SyncResult(
                    entry=entry2,
                    status=SyncStatus.NOT_MODIFIED,
                    error_message=None,
                ),
            ]

            with patch.object(
                orchestrator.syncer,
                "sync_entry",
                side_effect=mock_sync_results,
            ):
                # Act
                summary = orchestrator.sync_multiple()

        # Assert
        assert isinstance(summary, SyncSummary)
        assert summary.total_processed == 2  # Only entries with sources
        assert summary.successful_count == 2
        assert summary.updated_count == 1
        assert summary.not_modified_count == 1
        assert summary.error_count == 0

    def test_sync_specific_entry_by_id(self, workspace_root: Path) -> None:
        """Sync with entry_id should filter and sync only that entry."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        entry1 = _create_entry("kno-001", has_sources=True, file_path=Path("doc1.md"))
        entry2 = _create_entry("kno-002", has_sources=True, file_path=Path("doc2.md"))

        mock_entries = [entry1, entry2]

        # Mock scanner
        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Mock syncer
            mock_result = SyncResult(
                entry=entry1,
                status=SyncStatus.UPDATED,
                error_message=None,
            )

            with patch.object(
                orchestrator.syncer,
                "sync_entry",
                return_value=mock_result,
            ) as mock_sync:
                # Act
                summary = orchestrator.sync_multiple(entry_id="kno-001")

        # Assert
        assert summary.total_processed == 1
        assert summary.updated_count == 1
        # Verify syncer was called only once (for kno-001)
        mock_sync.assert_called_once()
        assert mock_sync.call_args[0][0].id == "kno-001"

    def test_sync_nonexistent_entry_id_raises_error(
        self,
        workspace_root: Path,
    ) -> None:
        """Sync with non-existent entry_id should raise ValueError."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        entry1 = _create_entry("kno-001", has_sources=True)
        mock_entries = [entry1]

        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Act & Assert
            with pytest.raises(ValueError, match="Entry 'kno-999' not found"):
                orchestrator.sync_multiple(entry_id="kno-999")

    def test_sync_entry_without_sources_raises_error(
        self,
        workspace_root: Path,
    ) -> None:
        """Sync entry_id that has no sources should raise ValueError."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        entry1 = _create_entry("kno-001", has_sources=False)
        mock_entries = [entry1]

        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Act & Assert
            with pytest.raises(ValueError, match="has no external sources"):
                orchestrator.sync_multiple(entry_id="kno-001")

    def test_sync_dry_run_mode(self, workspace_root: Path) -> None:
        """Dry run should not call syncer.sync_entry."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        entry1 = _create_entry("kno-001", has_sources=True, file_path=Path("doc1.md"))
        mock_entries = [entry1]

        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            with patch.object(
                orchestrator.syncer,
                "sync_entry",
            ) as mock_sync:
                # Act
                summary = orchestrator.sync_multiple(dry_run=True)

        # Assert
        assert summary.total_processed == 1
        assert summary.not_modified_count == 1  # Dry run returns NOT_MODIFIED
        assert summary.error_count == 0
        # Syncer should NOT be called in dry run
        mock_sync.assert_not_called()

    def test_sync_handles_syncer_exception(self, workspace_root: Path) -> None:
        """Sync should catch exceptions from syncer and record as errors."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        entry1 = _create_entry("kno-001", has_sources=True, file_path=Path("doc1.md"))
        mock_entries = [entry1]

        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Mock syncer to raise exception
            with patch.object(
                orchestrator.syncer,
                "sync_entry",
                side_effect=RuntimeError("Network error"),
            ):
                # Act
                summary = orchestrator.sync_multiple()

        # Assert
        assert summary.total_processed == 1
        assert summary.error_count == 1
        assert summary.successful_count == 0
        assert summary.results[0].error_message is not None
        assert "Network error" in summary.results[0].error_message

    def test_sync_entry_missing_file_path(self, workspace_root: Path) -> None:
        """Sync should handle entries with missing file_path gracefully."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        # Entry with sources but no file_path
        entry1 = _create_entry("kno-001", has_sources=True, file_path=None)
        mock_entries = [entry1]

        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Act
            summary = orchestrator.sync_multiple()

        # Assert
        assert summary.total_processed == 1
        assert summary.error_count == 1
        assert summary.results[0].error_message is not None
        assert "Missing file_path" in summary.results[0].error_message

    def test_sync_empty_workspace(self, workspace_root: Path) -> None:
        """Sync on empty workspace should return empty summary."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        with patch.object(orchestrator.scanner, "scan", return_value=[]):
            # Act
            summary = orchestrator.sync_multiple()

        # Assert
        assert summary.total_processed == 0
        assert summary.successful_count == 0
        assert summary.error_count == 0

    def test_sync_no_entries_with_sources(self, workspace_root: Path) -> None:
        """Sync when no entries have sources should return empty summary."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        entry1 = _create_entry("kno-001", has_sources=False)
        entry2 = _create_entry("kno-002", has_sources=False)
        mock_entries = [entry1, entry2]

        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Act
            summary = orchestrator.sync_multiple()

        # Assert
        assert summary.total_processed == 0
        assert summary.successful_count == 0

    def test_sync_mixed_results(self, workspace_root: Path) -> None:
        """Sync should correctly aggregate mixed results.

        Tests aggregation of: updated, not_modified, error.
        """
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        entry1 = _create_entry("kno-001", has_sources=True, file_path=Path("doc1.md"))
        entry2 = _create_entry("kno-002", has_sources=True, file_path=Path("doc2.md"))
        entry3 = _create_entry("kno-003", has_sources=True, file_path=Path("doc3.md"))

        mock_entries = [entry1, entry2, entry3]

        with patch.object(orchestrator.scanner, "scan", return_value=mock_entries):
            # Mock different results for each entry
            mock_results = [
                SyncResult(entry=entry1, status=SyncStatus.UPDATED),
                SyncResult(entry=entry2, status=SyncStatus.NOT_MODIFIED),
                SyncResult(
                    entry=entry3,
                    status=SyncStatus.ERROR,
                    error_message="Sync failed",
                ),
            ]

            with patch.object(
                orchestrator.syncer,
                "sync_entry",
                side_effect=mock_results,
            ):
                # Act
                summary = orchestrator.sync_multiple()

        # Assert
        assert summary.total_processed == 3
        assert summary.updated_count == 1
        assert summary.not_modified_count == 1
        assert summary.error_count == 1
        assert summary.successful_count == 2  # updated + not_modified


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_orchestrator_initialization(self, workspace_root: Path) -> None:
        """Orchestrator should initialize scanner and syncer correctly."""
        # Act
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        # Assert
        assert orchestrator.workspace_root == workspace_root
        assert orchestrator.scanner is not None
        assert orchestrator.syncer is not None

    def test_orchestrator_with_parallel_mode(self, workspace_root: Path) -> None:
        """Orchestrator should support force_parallel flag."""
        # Act
        orchestrator = KnowledgeOrchestrator(
            workspace_root=workspace_root,
            force_parallel=True,
        )

        # Assert
        assert orchestrator.scanner.force_parallel is True

    def test_sync_result_aggregation_accuracy(self, workspace_root: Path) -> None:
        """Sync summary statistics should be accurately calculated."""
        # Arrange
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)

        entries = [
            _create_entry(
                f"kno-{i:03d}",
                has_sources=True,
                file_path=Path(f"doc{i}.md"),
            )
            for i in range(10)
        ]

        # Create specific result pattern: 5 updated, 3 not_modified, 2 errors
        mock_results = (
            [SyncResult(entry=e, status=SyncStatus.UPDATED) for e in entries[:5]]
            + [
                SyncResult(entry=e, status=SyncStatus.NOT_MODIFIED)
                for e in entries[5:8]
            ]
            + [
                SyncResult(entry=e, status=SyncStatus.ERROR, error_message="Error")
                for e in entries[8:]
            ]
        )

        with patch.object(orchestrator.scanner, "scan", return_value=entries):
            with patch.object(
                orchestrator.syncer,
                "sync_entry",
                side_effect=mock_results,
            ):
                # Act
                summary = orchestrator.sync_multiple()

        # Assert
        assert summary.total_processed == 10
        assert summary.updated_count == 5
        assert summary.not_modified_count == 3
        assert summary.error_count == 2
        assert summary.successful_count == 8  # 5 + 3
