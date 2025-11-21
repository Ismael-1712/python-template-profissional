"""Data models for the Git synchronization system."""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class SyncStep:
    """Represents a single synchronization step with metadata."""

    def __init__(self, name: str, description: str) -> None:
        """Initialize a sync step with name and description."""
        self.name = name
        self.description = description
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.status: str = "pending"
        self.error: str | None = None
        self.details: dict[str, Any] = {}

    def start(self) -> None:
        """Mark step as started."""
        self.start_time = datetime.now(timezone.utc)
        self.status = "running"
        logger.info("🔄 Starting: %s - %s", self.name, self.description)

    def complete(self, details: dict[str, Any] | None = None) -> None:
        """Mark step as completed successfully."""
        self.end_time = datetime.now(timezone.utc)
        self.status = "success"
        if details:
            self.details.update(details)

        duration = self._get_duration()
        logger.info("✅ Completed: %s (%.2fs)", self.name, duration)

    def fail(self, error: str, details: dict[str, Any] | None = None) -> None:
        """Mark step as failed."""
        self.end_time = datetime.now(timezone.utc)
        self.status = "failed"
        self.error = error
        if details:
            self.details.update(details)

        duration = self._get_duration()
        logger.error("❌ Failed: %s (%.2fs) - %s", self.name, duration, error)

    def _get_duration(self) -> float:
        """Calculate step duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert step to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self._get_duration(),
            "error": self.error,
            "details": self.details,
        }
