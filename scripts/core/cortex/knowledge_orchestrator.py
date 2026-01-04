"""Knowledge Orchestrator - High-level coordination of Knowledge Base operations.

This module provides the KnowledgeOrchestrator class, which acts as a Facade
for Knowledge Base operations by coordinating KnowledgeScanner and KnowledgeSyncer.

The orchestrator encapsulates business logic that was previously in the CLI layer,
following the Hexagonal Architecture pattern (Ports & Adapters).

Key Responsibilities:
- Coordinating scan and sync operations
- Filtering entries by ID
- Aggregating sync results
- Providing a clean API for the presentation layer (CLI)

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.core.cortex.models import KnowledgeEntry

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
from scripts.core.cortex.knowledge_sync import KnowledgeSyncer, SyncResult
from scripts.core.cortex.sync_aggregator import SyncAggregator
from scripts.core.cortex.sync_executor import SyncExecutor
from scripts.core.cortex.sync_filters import EntryFilter
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__)


@dataclass
class ScanResult:
    """Result of scanning the knowledge base.

    Attributes:
        entries: List of all knowledge entries found
        total_count: Total number of entries scanned
        entries_with_sources: Filtered list of entries that have external sources
    """

    entries: list[KnowledgeEntry]
    total_count: int
    entries_with_sources: list[KnowledgeEntry]


@dataclass
class SyncSummary:
    """Summary of bulk synchronization operations.

    Attributes:
        results: List of individual sync results
        total_processed: Total number of entries attempted
        successful_count: Number of entries successfully synced
            (UPDATED or NOT_MODIFIED)
        updated_count: Number of entries actually updated
        not_modified_count: Number of entries with no changes
        error_count: Number of entries that failed to sync
    """

    results: list[SyncResult]
    total_processed: int
    successful_count: int
    updated_count: int
    not_modified_count: int
    error_count: int


class KnowledgeOrchestrator:
    """High-level orchestrator for Knowledge Base operations.

    This class provides a unified interface for scanning and synchronizing
    knowledge entries, abstracting away the complexity of coordinating
    multiple core components.

    It implements the Facade pattern, simplifying the interaction between
    the CLI (presentation layer) and the core business logic.

    Attributes:
        workspace_root: Root directory of the workspace
        scanner: Knowledge scanner instance
        syncer: Knowledge syncer instance

    Example:
        >>> orchestrator = KnowledgeOrchestrator(workspace_root=Path('/project'))
        >>>
        >>> # Scan knowledge base
        >>> scan_result = orchestrator.scan()
        >>> print(f"Found {scan_result.total_count} entries")
        >>>
        >>> # Sync all entries
        >>> summary = orchestrator.sync_multiple()
        >>> print(f"Updated: {summary.updated_count}, Errors: {summary.error_count}")
        >>>
        >>> # Sync specific entry
        >>> summary = orchestrator.sync_multiple(entry_id="kno-001")
    """

    def __init__(self, workspace_root: Path, force_parallel: bool = False) -> None:
        """Initialize the Knowledge Orchestrator.

        Args:
            workspace_root: Root directory of the workspace
            force_parallel: Force parallel processing in scanner (experimental)
        """
        self.workspace_root = workspace_root
        self.scanner = KnowledgeScanner(
            workspace_root=workspace_root,
            force_parallel=force_parallel,
        )
        self.syncer = KnowledgeSyncer()

        logger.debug(
            "KnowledgeOrchestrator initialized for workspace: %s",
            workspace_root,
        )

    def scan(self, verbose: bool = False) -> ScanResult:
        """Scan the knowledge base for entries.

        This method wraps the KnowledgeScanner and provides structured results
        with additional metadata useful for the presentation layer.

        Args:
            verbose: If True, log detailed information about each entry

        Returns:
            ScanResult containing all entries and useful metadata

        Example:
            >>> result = orchestrator.scan(verbose=True)
            >>> for entry in result.entries_with_sources:
            ...     print(f"{entry.id}: {len(entry.sources)} sources")
        """
        logger.info("Orchestrator: Starting knowledge base scan")

        # Delegate to scanner
        entries = self.scanner.scan()

        # Filter entries with sources
        entries_with_sources = [e for e in entries if e.sources]

        if verbose:
            logger.debug(
                "Scan complete: %d total, %d with sources",
                len(entries),
                len(entries_with_sources),
            )
            for entry in entries:
                logger.debug(
                    "Entry %s: %d sources, %d tags",
                    entry.id,
                    len(entry.sources),
                    len(entry.tags),
                )

        return ScanResult(
            entries=entries,
            total_count=len(entries),
            entries_with_sources=entries_with_sources,
        )

    def sync_multiple(
        self,
        entry_id: str | None = None,
        dry_run: bool = False,
    ) -> SyncSummary:
        """Synchronize multiple knowledge entries with their external sources.

        This method orchestrates the complete sync workflow:
        1. Scan for knowledge entries
        2. Filter by entry_id if provided
        3. Filter entries with sources
        4. Execute sync for each entry
        5. Aggregate results into summary

        This logic was previously scattered in the CLI layer and is now
        properly encapsulated in the core business logic.

        Args:
            entry_id: Optional specific entry ID to sync. If None, syncs all entries.
            dry_run: If True, simulates sync without writing to disk

        Returns:
            SyncSummary with aggregated results and statistics

        Raises:
            ValueError: If entry_id is provided but not found
            ValueError: If entry_id is provided but has no sources

        Example:
            >>> # Sync all entries
            >>> summary = orchestrator.sync_multiple()
            >>> print(f"Updated: {summary.updated_count}")
            >>>
            >>> # Sync specific entry
            >>> summary = orchestrator.sync_multiple(entry_id="kno-001")
            >>>
            >>> # Dry run
            >>> summary = orchestrator.sync_multiple(dry_run=True)
        """
        logger.info(
            "Orchestrator: Starting sync (entry_id=%s, dry_run=%s)",
            entry_id,
            dry_run,
        )

        # Step 1: Scan for all entries
        scan_result = self.scan()
        all_entries = scan_result.entries

        if not all_entries:
            logger.warning("No knowledge entries found in workspace")
            return SyncSummary(
                results=[],
                total_processed=0,
                successful_count=0,
                updated_count=0,
                not_modified_count=0,
                error_count=0,
            )

        # Step 2: Filter by entry_id if provided
        if entry_id:
            try:
                entries_to_sync = EntryFilter.filter_by_id(all_entries, entry_id)
                logger.debug("Filtered to specific entry: %s", entry_id)
            except ValueError as e:
                logger.error(str(e))
                raise
        else:
            entries_to_sync = all_entries
            logger.debug("Processing all %d entries", len(entries_to_sync))

        # Step 3: Filter entries that have external sources
        entries_with_sources = EntryFilter.filter_by_sources(entries_to_sync)

        if not entries_with_sources:
            if entry_id:
                msg = f"Entry '{entry_id}' has no external sources"
                logger.warning(msg)
                raise ValueError(msg)
            logger.warning("No entries with external sources found")
            return SyncSummary(
                results=[],
                total_processed=0,
                successful_count=0,
                updated_count=0,
                not_modified_count=0,
                error_count=0,
            )

        # Step 4: Execute sync for each entry
        logger.info("Processing %d entries with sources", len(entries_with_sources))

        executor = SyncExecutor(self.syncer, dry_run=dry_run)
        results = executor.execute_batch(entries_with_sources)

        # Step 5: Aggregate results into summary
        summary = SyncAggregator.aggregate(results)

        logger.info(
            "Sync complete: %d updated, %d not modified, %d errors",
            summary.updated_count,
            summary.not_modified_count,
            summary.error_count,
        )

        return summary
