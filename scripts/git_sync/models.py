"""Data models for Smart Git Sync.

This module contains dataclasses and model classes used to represent
synchronization steps, results, and related data structures.
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class SyncStep:
    """Represents a single synchronization step with metadata.

    This class tracks the execution of individual steps in the sync workflow,
    including timing, status, and detailed results.

    Attributes:
        name: Unique identifier for the step
        description: Human-readable description
        start_time: When the step started (UTC)
        end_time: When the step ended (UTC)
        status: Current status (pending, running, success, failed)
        error: Error message if failed
        details: Additional metadata and results
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize a sync step with name and description.

        Args:
            name: Unique identifier for the step
            description: Human-readable description of what the step does
        """
        self.name = name
        self.description = description
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.status: str = "pending"
        self.error: str | None = None
        self.details: dict[str, Any] = {}

    def start(self) -> None:
        """Mark step as started and log the event."""
        self.start_time = datetime.now(timezone.utc)
        self.status = "running"
        logger.info("🔄 Starting: %s - %s", self.name, self.description)

    def complete(self, details: dict[str, Any] | None = None) -> None:
        """Mark step as completed successfully.

        Args:
            details: Optional dictionary with additional result information
        """
        self.end_time = datetime.now(timezone.utc)
        self.status = "success"
        if details:
            self.details.update(details)

        duration = self._get_duration()
        logger.info("✅ Completed: %s (%.2fs)", self.name, duration)

    def fail(self, error: str, details: dict[str, Any] | None = None) -> None:
        """Mark step as failed and log the error.

        Args:
            error: Error message describing the failure
            details: Optional dictionary with additional error context
        """
        self.end_time = datetime.now(timezone.utc)
        self.status = "failed"
        self.error = error
        if details:
            self.details.update(details)

        duration = self._get_duration()
        logger.error("❌ Failed: %s (%.2fs) - %s", self.name, duration, error)

    def _get_duration(self) -> float:
        """Calculate step duration in seconds.

        Returns:
            Duration in seconds, or 0.0 if timing is incomplete
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self._get_duration(),
            "error": self.error,
            "details": self.details,
        }
