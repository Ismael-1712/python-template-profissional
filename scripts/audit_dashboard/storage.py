"""Persistent storage for audit metrics.

This module handles thread-safe loading, saving, and validation
of audit metrics data.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.audit_dashboard.models import (
    DEFAULT_TIME_PER_FAILURE_MINUTES,
    MAX_HISTORY_RECORDS,
    METRICS_FILE_PERMISSIONS,
    AuditMetricsError,
)

logger = logging.getLogger(__name__)


class MetricsStorage:
    """Thread-safe persistent storage for audit metrics."""

    def __init__(
        self,
        metrics_file: Path,
        lock: threading.RLock | None = None,
    ) -> None:
        """Initialize metrics storage.

        Args:
            metrics_file: Path to the metrics JSON file
            lock: Optional threading lock (creates new if not provided)

        """
        self.metrics_file = metrics_file
        self._lock = lock or threading.RLock()

    def load_metrics(self) -> dict[str, Any]:
        """Load metrics from persistent storage with error handling.

        Returns:
            Dictionary containing metrics data

        """
        with self._lock:
            try:
                if self.metrics_file.exists():
                    with open(self.metrics_file, encoding="utf-8") as f:
                        metrics: dict[str, Any] = json.load(f)
                    logger.info(f"Loaded metrics from {self.metrics_file}")
                else:
                    metrics = self._get_default_metrics()
                    logger.info("Initialized default metrics")

                # Validate and migrate metrics structure
                self._validate_metrics_structure(metrics)
                return metrics

            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load metrics: {e}")
                logger.info("Initializing with default metrics")
                return self._get_default_metrics()

    def save_metrics(self, metrics: dict[str, Any]) -> None:
        """Save metrics with atomic write guarantees (POSIX).

        Args:
            metrics: Dictionary containing metrics data

        Raises:
            AuditMetricsError: If save operation fails

        """
        # Create unique temp file to avoid race conditions between processes
        temp_file = self.metrics_file.with_suffix(f".tmp.{os.getpid()}")

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk physical media

            # Atomic replace (POSIX guarantee)
            # If target exists, it is replaced atomically
            temp_file.replace(self.metrics_file)

            # Restore permissions
            try:
                os.chmod(self.metrics_file, METRICS_FILE_PERMISSIONS)
            except OSError as e:
                logger.debug(
                    "Could not set permissions on %s: %s",
                    self.metrics_file,
                    e,
                )

        except Exception as e:
            # Cleanup temp file on failure
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError as cleanup_error:
                    logger.debug(
                        "Failed to cleanup temp file %s: %s",
                        temp_file,
                        cleanup_error,
                    )
            raise AuditMetricsError(f"Cannot save metrics: {e}") from e

    def _get_default_metrics(self) -> dict[str, Any]:
        """Return default metrics structure.

        Returns:
            Dictionary with default metrics

        """
        return {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "audits_performed": 0,
            "failures_prevented": 0,
            "time_saved_minutes": 0,
            "last_audit": None,
            "audit_history": [],
            "pattern_statistics": {},
            "monthly_stats": {},
            "success_rate": 100.0,
            "configuration": {
                "time_per_failure_minutes": DEFAULT_TIME_PER_FAILURE_MINUTES,
                "max_history_records": MAX_HISTORY_RECORDS,
            },
        }

    def _validate_metrics_structure(self, metrics: dict[str, Any]) -> None:
        """Validate and migrate metrics structure if needed.

        Args:
            metrics: Dictionary to validate (modified in place)

        """
        required_keys = [
            "audits_performed",
            "failures_prevented",
            "time_saved_minutes",
            "audit_history",
            "pattern_statistics",
            "monthly_stats",
            "success_rate",
        ]

        for key in required_keys:
            if key not in metrics:
                logger.warning(f"Missing metric key '{key}', initializing with default")
                if key in [
                    "audits_performed",
                    "failures_prevented",
                    "time_saved_minutes",
                ]:
                    metrics[key] = 0
                elif key == "success_rate":
                    metrics[key] = 100.0
                else:
                    metrics[key] = {}

        # Ensure configuration exists
        if "configuration" not in metrics:
            metrics["configuration"] = {
                "time_per_failure_minutes": DEFAULT_TIME_PER_FAILURE_MINUTES,
                "max_history_records": MAX_HISTORY_RECORDS,
            }
