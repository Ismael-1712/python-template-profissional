"""Data models and constants for the Audit Dashboard.

This module contains all data structures, constants, and exceptions
used by the audit dashboard system.
"""

from dataclasses import dataclass, field
from typing import Any

# Configuration constants
DEFAULT_TIME_PER_FAILURE_MINUTES = 7
MAX_HISTORY_RECORDS = 50
METRICS_FILE_PERMISSIONS = 0o644
DEFAULT_METRICS_FILENAME = "audit_metrics.json"


class AuditMetricsError(Exception):
    """Custom exception for audit metrics operations."""


@dataclass
class MetricsConfiguration:
    """Configuration for metrics calculation and storage."""

    time_per_failure_minutes: int = DEFAULT_TIME_PER_FAILURE_MINUTES
    max_history_records: int = MAX_HISTORY_RECORDS

    def to_dict(self) -> dict[str, int]:
        """Convert configuration to dictionary."""
        return {
            "time_per_failure_minutes": self.time_per_failure_minutes,
            "max_history_records": self.max_history_records,
        }


@dataclass
class PatternStatistics:
    """Statistics for a detected pattern."""

    pattern: str
    count: int = 0
    files_affected: set[str] = field(default_factory=set)
    severity_distribution: dict[str, int] = field(
        default_factory=lambda: {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert pattern statistics to dictionary."""
        return {
            "count": self.count,
            "files_affected": list(self.files_affected),
            "severity_distribution": self.severity_distribution,
        }


@dataclass
class MonthlyStatistics:
    """Monthly aggregated statistics."""

    month: str
    audits: int = 0
    failures_prevented: int = 0
    time_saved: int = 0

    def to_dict(self) -> dict[str, int]:
        """Convert monthly statistics to dictionary."""
        return {
            "audits": self.audits,
            "failures_prevented": self.failures_prevented,
            "time_saved": self.time_saved,
        }


@dataclass
class AuditHistoryRecord:
    """Individual audit history record."""

    timestamp: str
    failures_prevented: int
    high_severity_count: int
    time_saved: int
    ci_simulation_passed: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert audit record to dictionary."""
        return {
            "timestamp": self.timestamp,
            "failures_prevented": self.failures_prevented,
            "high_severity_count": self.high_severity_count,
            "time_saved": self.time_saved,
            "ci_simulation_passed": self.ci_simulation_passed,
        }
