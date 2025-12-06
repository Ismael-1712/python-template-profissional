"""Metrics calculation logic for the Audit Dashboard.

This module contains the business logic for calculating and updating
audit metrics, pattern statistics, and monthly aggregations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Business logic for calculating and updating audit metrics."""

    @staticmethod
    def update_pattern_statistics(
        metrics: dict[str, Any],
        dependencies: list[dict[str, Any]],
    ) -> None:
        """Update pattern detection statistics.

        Args:
            metrics: Metrics dictionary to update (modified in place)
            dependencies: List of detected dependencies

        """
        for dep in dependencies:
            if not isinstance(dep, dict):
                continue

            pattern = dep.get("pattern", "unknown")
            file_path = dep.get("file", "")
            severity = dep.get("severity", "MEDIUM")

            if pattern not in metrics["pattern_statistics"]:
                metrics["pattern_statistics"][pattern] = {
                    "count": 0,
                    "files_affected": [],
                    "severity_distribution": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                }

            pattern_stats = metrics["pattern_statistics"][pattern]
            pattern_stats["count"] += 1

            if file_path and file_path not in pattern_stats["files_affected"]:
                pattern_stats["files_affected"].append(file_path)

            if severity in pattern_stats["severity_distribution"]:
                pattern_stats["severity_distribution"][severity] += 1

    @staticmethod
    def update_monthly_statistics(
        metrics: dict[str, Any],
        failures_prevented: int,
        time_saved: int,
    ) -> None:
        """Update monthly aggregated statistics.

        Args:
            metrics: Metrics dictionary to update (modified in place)
            failures_prevented: Number of failures prevented
            time_saved: Time saved in minutes

        """
        month_key = datetime.now().strftime("%Y-%m")

        if month_key not in metrics["monthly_stats"]:
            metrics["monthly_stats"][month_key] = {
                "audits": 0,
                "failures_prevented": 0,
                "time_saved": 0,
            }

        monthly = metrics["monthly_stats"][month_key]
        monthly["audits"] += 1
        monthly["failures_prevented"] += failures_prevented
        monthly["time_saved"] += time_saved

    @staticmethod
    def record_audit_history(
        metrics: dict[str, Any],
        timestamp: str,
        failures_prevented: int,
        high_severity_count: int,
        time_saved: int,
        audit_result: dict[str, Any],
    ) -> None:
        """Record individual audit in history with size management.

        Args:
            metrics: Metrics dictionary to update (modified in place)
            timestamp: ISO format timestamp
            failures_prevented: Number of failures prevented
            high_severity_count: Count of high severity issues
            time_saved: Time saved in minutes
            audit_result: Complete audit result dictionary

        """
        audit_record = {
            "timestamp": timestamp,
            "failures_prevented": failures_prevented,
            "high_severity": high_severity_count,
            "time_saved": time_saved,
            "ci_simulation_passed": (
                audit_result.get("ci_simulation", {}).get("tests_passed", True)
            ),
        }

        metrics["audit_history"].append(audit_record)

        # Maintain history size limit
        max_records = metrics["configuration"]["max_history_records"]
        if len(metrics["audit_history"]) > max_records:
            metrics["audit_history"] = metrics["audit_history"][-max_records:]

    @staticmethod
    def update_success_rate(metrics: dict[str, Any]) -> None:
        """Calculate and update success rate based on CI simulation results.

        Args:
            metrics: Metrics dictionary to update (modified in place)

        """
        if not metrics["audit_history"]:
            metrics["success_rate"] = 100.0
            return

        successful_audits = sum(
            1
            for audit in metrics["audit_history"]
            if audit.get("ci_simulation_passed", True)
        )

        total_audits = len(metrics["audit_history"])
        metrics["success_rate"] = (successful_audits / total_audits) * 100
