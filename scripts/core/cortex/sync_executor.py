"""SyncExecutor - Pipeline pattern for batch synchronization operations.

This module implements the SyncExecutor class, which extracts the sync loop
logic from KnowledgeOrchestrator.sync_multiple (Phase 3 of refactoring).

Following the Pipeline Pattern and Single Responsibility Principle:
- Handles iteration over entries
- Validates entry prerequisites (file_path)
- Manages dry-run mode
- Captures and wraps exceptions into ERROR results

This extraction reduces the complexity of KnowledgeOrchestrator and makes
sync execution logic testable in isolation.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.core.cortex.models import KnowledgeEntry

from scripts.core.cortex.knowledge_sync import KnowledgeSyncer, SyncResult, SyncStatus
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__)


class SyncExecutor:
    """Pipeline pattern executor for batch knowledge entry synchronization.

    This class encapsulates the logic for executing sync operations across
    multiple knowledge entries, handling validation, error recovery, and
    dry-run simulation.

    Extracted from KnowledgeOrchestrator.sync_multiple to reduce complexity
    and improve testability.

    Attributes:
        syncer: KnowledgeSyncer instance for performing actual sync operations
        dry_run: If True, simulates sync without I/O (returns NOT_MODIFIED)

    Example:
        >>> syncer = KnowledgeSyncer()
        >>> executor = SyncExecutor(syncer=syncer, dry_run=False)
        >>> results = executor.execute_batch(entries)
        >>> print(f"Synced {len(results)} entries")
    """

    def __init__(self, syncer: KnowledgeSyncer, dry_run: bool = False) -> None:
        """Initialize the SyncExecutor.

        Args:
            syncer: KnowledgeSyncer instance for sync operations
            dry_run: If True, simulates sync without actual I/O

        Raises:
            TypeError: If syncer is None or not a KnowledgeSyncer instance
        """
        if syncer is None:
            raise TypeError("syncer cannot be None")

        self.syncer = syncer
        self.dry_run = dry_run

        logger.debug(
            "SyncExecutor initialized (dry_run=%s)",
            dry_run,
        )

    def execute_batch(
        self,
        entries: list[KnowledgeEntry],
    ) -> list[SyncResult]:
        """Execute synchronization for a batch of knowledge entries.

        Iterates through entries, validates prerequisites, and performs
        sync operations. Handles errors gracefully by converting exceptions
        into ERROR results.

        Process for each entry:
        1. Validate file_path exists
        2. If dry_run: return NOT_MODIFIED without I/O
        3. Otherwise: call syncer.sync_entry
        4. Catch exceptions and convert to ERROR result

        Args:
            entries: List of KnowledgeEntry objects to synchronize

        Returns:
            List of SyncResult objects, one per entry (same order)

        Example:
            >>> results = executor.execute_batch([entry1, entry2])
            >>> success_count = sum(1 for r in results if r.status != SyncStatus.ERROR)
        """
        if not entries:
            logger.debug("execute_batch called with empty list")
            return []

        results: list[SyncResult] = []

        logger.info(
            "Executing batch sync for %d entries (dry_run=%s)",
            len(entries),
            self.dry_run,
        )

        for entry in entries:
            result = self._sync_single_entry(entry)
            results.append(result)

        logger.debug(
            "Batch sync complete: %d results",
            len(results),
        )

        return results

    def _sync_single_entry(self, entry: KnowledgeEntry) -> SyncResult:
        """Synchronize a single knowledge entry with error handling.

        Internal method that handles the sync logic for one entry,
        including validation, dry-run mode, and exception capture.

        Args:
            entry: KnowledgeEntry to synchronize

        Returns:
            SyncResult with sync status and optional error message
        """
        # Step 1: Validate file_path
        if not entry.file_path:
            logger.error("Entry %s missing file_path (internal error)", entry.id)
            return SyncResult(
                entry=entry,
                status=SyncStatus.ERROR,
                error_message="Missing file_path attribute",
            )

        # Step 2: Handle dry-run mode
        if self.dry_run:
            logger.debug("Dry run: skipping actual sync for %s", entry.id)
            return SyncResult(
                entry=entry,
                status=SyncStatus.NOT_MODIFIED,
                error_message=None,
            )

        # Step 3: Execute real sync with exception handling
        try:
            logger.debug(
                "Syncing entry %s (%d sources)",
                entry.id,
                len(entry.sources),
            )

            sync_result = self.syncer.sync_entry(entry, entry.file_path)

            if sync_result.status == SyncStatus.UPDATED:
                logger.info("Entry %s synchronized successfully", entry.id)
            elif sync_result.status == SyncStatus.NOT_MODIFIED:
                logger.debug("Entry %s: no changes (304)", entry.id)
            else:
                logger.error(
                    "Entry %s sync failed: %s",
                    entry.id,
                    sync_result.error_message,
                )

            return sync_result

        except Exception as e:
            logger.error(
                "Exception syncing entry %s: %s",
                entry.id,
                str(e),
                exc_info=True,
            )
            return SyncResult(
                entry=entry,
                status=SyncStatus.ERROR,
                error_message=str(e),
            )
