"""Tests for SyncExecutor - Pipeline pattern for batch sync operations.

This module tests the SyncExecutor class that extracts the sync loop
from KnowledgeOrchestrator.sync_multiple (Phase 3 of refactoring).

TDD Approach: Tests written FIRST, implementation follows.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.core.cortex.knowledge_sync import KnowledgeSyncer, SyncResult, SyncStatus
from scripts.core.cortex.models import DocStatus, KnowledgeEntry, KnowledgeSource

# Module under test (will be created in implementation phase)
# from scripts.core.cortex.sync_executor import SyncExecutor


@pytest.fixture
def mock_syncer():
    """Fixture providing a mocked KnowledgeSyncer."""
    return Mock(spec=KnowledgeSyncer)


@pytest.fixture
def sample_entry():
    """Fixture providing a valid sample KnowledgeEntry."""
    return KnowledgeEntry(
        id="kno-001",
        status=DocStatus.ACTIVE,
        tags=["test"],
        sources=[KnowledgeSource(url="https://example.com")],
        file_path=Path("/workspace/docs/sample.md"),
    )


@pytest.fixture
def sample_entry_no_path():
    """Fixture providing entry without file_path (edge case)."""
    return KnowledgeEntry(
        id="kno-002",
        status=DocStatus.ACTIVE,
        tags=["test"],
        sources=[KnowledgeSource(url="https://example.com")],
        file_path=None,  # Missing path
    )


class TestSyncExecutor:
    """Tests for SyncExecutor class (TDD - Red Phase)."""

    def test_executor_initialization(self, mock_syncer):
        """Test that SyncExecutor initializes with syncer and dry_run flag.

        GIVEN: A KnowledgeSyncer instance and dry_run flag
        WHEN: SyncExecutor is instantiated
        THEN: Executor stores syncer and dry_run configuration
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        executor = SyncExecutor(syncer=mock_syncer, dry_run=False)

        assert executor.syncer is mock_syncer
        assert executor.dry_run is False

    def test_execute_batch_empty_list(self, mock_syncer):
        """Test that executor handles empty entry list gracefully.

        GIVEN: An empty list of entries
        WHEN: execute_batch is called
        THEN: Returns empty list of results
        AND: No calls to syncer.sync_entry
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        executor = SyncExecutor(syncer=mock_syncer, dry_run=False)

        results = executor.execute_batch([])

        assert results == []
        mock_syncer.sync_entry.assert_not_called()

    def test_execute_batch_success(self, mock_syncer, sample_entry):
        """Test successful sync of a single entry.

        GIVEN: One valid entry with file_path
        WHEN: execute_batch is called (not dry run)
        THEN: Syncer is called with entry and file_path
        AND: Result is added to results list
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        # Setup: Mock syncer returns success
        mock_result = SyncResult(
            entry=sample_entry,
            status=SyncStatus.UPDATED,
            error_message=None,
        )
        mock_syncer.sync_entry.return_value = mock_result

        executor = SyncExecutor(syncer=mock_syncer, dry_run=False)

        results = executor.execute_batch([sample_entry])

        assert len(results) == 1
        assert results[0].status == SyncStatus.UPDATED
        mock_syncer.sync_entry.assert_called_once_with(
            sample_entry,
            sample_entry.file_path,
        )

    def test_execute_batch_multiple_entries(self, mock_syncer, sample_entry):
        """Test batch sync of multiple entries.

        GIVEN: Three valid entries
        WHEN: execute_batch is called
        THEN: Syncer is called three times
        AND: Results list contains three SyncResult objects
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        entries = [sample_entry] * 3  # Same entry 3 times for simplicity

        # Mock syncer returns success for all
        mock_result = SyncResult(
            entry=sample_entry,
            status=SyncStatus.UPDATED,
            error_message=None,
        )
        mock_syncer.sync_entry.return_value = mock_result

        executor = SyncExecutor(syncer=mock_syncer, dry_run=False)

        results = executor.execute_batch(entries)

        assert len(results) == 3
        assert mock_syncer.sync_entry.call_count == 3
        assert all(r.status == SyncStatus.UPDATED for r in results)

    def test_execute_batch_missing_file_path(self, mock_syncer, sample_entry_no_path):
        """Test that executor handles entries without file_path.

        GIVEN: Entry with file_path=None
        WHEN: execute_batch is called
        THEN: Returns ERROR result without calling syncer
        AND: Error message indicates missing file_path
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        executor = SyncExecutor(syncer=mock_syncer, dry_run=False)

        results = executor.execute_batch([sample_entry_no_path])

        assert len(results) == 1
        assert results[0].status == SyncStatus.ERROR
        assert "file_path" in results[0].error_message.lower()
        mock_syncer.sync_entry.assert_not_called()

    def test_execute_batch_syncer_exception(self, mock_syncer, sample_entry):
        """Test that executor catches and wraps syncer exceptions.

        GIVEN: Syncer that raises exception
        WHEN: execute_batch is called
        THEN: Exception is caught and converted to ERROR result
        AND: Error message contains exception details
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        # Mock syncer raises exception
        mock_syncer.sync_entry.side_effect = RuntimeError("Network timeout")

        executor = SyncExecutor(syncer=mock_syncer, dry_run=False)

        results = executor.execute_batch([sample_entry])

        assert len(results) == 1
        assert results[0].status == SyncStatus.ERROR
        assert "Network timeout" in results[0].error_message

    def test_execute_batch_dry_run_mode(self, mock_syncer, sample_entry):
        """Test that dry_run mode skips actual sync.

        GIVEN: Executor in dry_run mode
        WHEN: execute_batch is called
        THEN: Syncer is NOT called
        AND: Results contain NOT_MODIFIED status for all entries
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        executor = SyncExecutor(syncer=mock_syncer, dry_run=True)

        results = executor.execute_batch([sample_entry])

        assert len(results) == 1
        assert results[0].status == SyncStatus.NOT_MODIFIED
        mock_syncer.sync_entry.assert_not_called()

    def test_execute_batch_mixed_results(self, mock_syncer, sample_entry):
        """Test batch with mixed success/failure results.

        GIVEN: Three entries, where one fails
        WHEN: execute_batch is called
        THEN: Results contain mix of UPDATED and ERROR statuses
        AND: Batch continues despite individual failure
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        entries = [sample_entry] * 3

        # Setup: First two succeed, third fails
        mock_syncer.sync_entry.side_effect = [
            SyncResult(sample_entry, SyncStatus.UPDATED, None),
            SyncResult(sample_entry, SyncStatus.UPDATED, None),
            RuntimeError("Sync failed"),
        ]

        executor = SyncExecutor(syncer=mock_syncer, dry_run=False)

        results = executor.execute_batch(entries)

        assert len(results) == 3
        assert results[0].status == SyncStatus.UPDATED
        assert results[1].status == SyncStatus.UPDATED
        assert results[2].status == SyncStatus.ERROR

    def test_execute_batch_preserves_entry_reference(self, mock_syncer, sample_entry):
        """Test that results contain original entry reference.

        GIVEN: Entry with specific attributes
        WHEN: execute_batch is called
        THEN: Result.entry references the same original entry object
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        mock_syncer.sync_entry.return_value = SyncResult(
            sample_entry,
            SyncStatus.UPDATED,
            None,
        )

        executor = SyncExecutor(syncer=mock_syncer, dry_run=False)

        results = executor.execute_batch([sample_entry])

        assert results[0].entry is sample_entry


class TestSyncExecutorEdgeCases:
    """Edge case tests for SyncExecutor."""

    def test_executor_with_none_syncer_raises_error(self):
        """Test that SyncExecutor requires valid syncer.

        GIVEN: None passed as syncer
        WHEN: SyncExecutor is instantiated
        THEN: Raises TypeError or ValueError
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        with pytest.raises((TypeError, ValueError)):
            SyncExecutor(syncer=None, dry_run=False)

    def test_dry_run_default_is_false(self, mock_syncer):
        """Test that dry_run defaults to False if not specified.

        GIVEN: SyncExecutor instantiated without dry_run parameter
        WHEN: Executor is created
        THEN: dry_run attribute is False
        """
        from scripts.core.cortex.sync_executor import SyncExecutor

        executor = SyncExecutor(syncer=mock_syncer)

        assert executor.dry_run is False
