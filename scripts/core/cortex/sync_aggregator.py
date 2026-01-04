"""Aggregation utilities for synchronization results.

This module provides pure domain logic for aggregating sync results
into summary statistics.

Following Hexagonal Architecture principles:
- Pure domain logic (no I/O, no logging)
- Stateless functions (class methods as namespace)
- Explicit data structures (SyncSummary from orchestrator)

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.core.cortex.knowledge_sync import SyncResult, SyncStatus

if TYPE_CHECKING:
    from scripts.core.cortex.knowledge_orchestrator import SyncSummary


class SyncAggregator:
    """Pure domain logic for aggregating synchronization results.

    This class provides static methods for transforming lists of SyncResult
    into statistical summaries (SyncSummary).

    All methods are stateless and can be called without instantiation.
    """

    @staticmethod
    def aggregate(results: list[SyncResult]) -> SyncSummary:
        """Aggregate a list of sync results into a summary with statistics.

        Calculates:
        - Total processed count
        - Updated count (SyncStatus.UPDATED)
        - Not modified count (SyncStatus.NOT_MODIFIED)
        - Error count (SyncStatus.ERROR)
        - Successful count (updated + not_modified)

        Args:
            results: List of SyncResult objects from sync operations

        Returns:
            SyncSummary with aggregated statistics and original results

        Example:
            >>> results = [
            ...     SyncResult(entry1, SyncStatus.UPDATED, None),
            ...     SyncResult(entry2, SyncStatus.ERROR, "Network timeout"),
            ... ]
            >>> summary = SyncAggregator.aggregate(results)
            >>> summary.total_processed
            2
            >>> summary.updated_count
            1
            >>> summary.error_count
            1
        """
        # Import at runtime to avoid circular dependency
        from scripts.core.cortex.knowledge_orchestrator import SyncSummary

        # Count results by status
        updated_count = sum(1 for r in results if r.status == SyncStatus.UPDATED)
        not_modified_count = sum(
            1 for r in results if r.status == SyncStatus.NOT_MODIFIED
        )
        error_count = sum(1 for r in results if r.status == SyncStatus.ERROR)

        # Calculate derived statistics
        successful_count = updated_count + not_modified_count
        total_processed = len(results)

        return SyncSummary(
            results=results,
            total_processed=total_processed,
            successful_count=successful_count,
            updated_count=updated_count,
            not_modified_count=not_modified_count,
            error_count=error_count,
        )
