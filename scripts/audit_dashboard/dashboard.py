"""Main dashboard orchestrator.

This module provides the high-level AuditDashboard class that
orchestrates all metrics operations.
"""

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.audit_dashboard.calculator import MetricsCalculator
from scripts.audit_dashboard.exporters import (
    ConsoleReporter,
    HTMLExporter,
    JSONExporter,
)
from scripts.audit_dashboard.models import AuditMetricsError
from scripts.audit_dashboard.storage import MetricsStorage

logger = logging.getLogger(__name__)


class AuditDashboard:
    """Thread-safe dashboard for DevOps audit metrics tracking.

    Provides comprehensive metrics collection, persistence, and reporting
    for CI/CD audit operations with enterprise-grade reliability.
    """

    def __init__(
        self,
        workspace_root: Path | None = None,
        metrics_filename: str = "audit_metrics.json",
    ) -> None:
        """Initialize audit dashboard with thread-safe operations.

        Args:
            workspace_root: Root directory for metrics storage
            metrics_filename: Name of the metrics file

        """
        self.workspace_root = workspace_root or Path.cwd()
        self.metrics_file = self.workspace_root / metrics_filename
        self._lock = threading.RLock()

        # Ensure workspace directory exists
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.storage = MetricsStorage(self.metrics_file, self._lock)
        self.calculator = MetricsCalculator()
        self.html_exporter = HTMLExporter()
        self.json_exporter = JSONExporter()
        self.console_reporter = ConsoleReporter()

        # Load metrics
        with self._lock:
            self._metrics = self.storage.load_metrics()

        logger.info(f"Dashboard initialized for workspace: {self.workspace_root}")

    def record_audit(self, audit_result: dict[str, Any]) -> None:
        """Record audit results with comprehensive validation.

        Args:
            audit_result: Dictionary containing audit results with structure:
                {
                    "external_dependencies": [
                        {"severity": str, "pattern": str, "file": str}, ...
                    ],
                    "ci_simulation": {"tests_passed": bool},
                    ...
                }

        Raises:
            AuditMetricsError: If recording fails

        """
        if not isinstance(audit_result, dict):
            msg = "audit_result must be a dictionary"
            raise ValueError(msg)

        with self._lock:
            try:
                now = datetime.now(timezone.utc).isoformat()

                self._metrics["audits_performed"] += 1
                self._metrics["last_audit"] = now

                # Process external dependencies
                dependencies = audit_result.get("external_dependencies", [])
                if not isinstance(dependencies, list):
                    logger.warning(
                        "external_dependencies is not a list, treating as empty",
                    )
                    dependencies = []

                failures_prevented = len(dependencies)
                high_severity_count = sum(
                    1
                    for dep in dependencies
                    if isinstance(dep, dict) and dep.get("severity") == "HIGH"
                )

                self._metrics["failures_prevented"] += failures_prevented

                # Calculate time saved with configurable rate
                time_per_failure = self._metrics["configuration"][
                    "time_per_failure_minutes"
                ]
                time_saved = failures_prevented * time_per_failure
                self._metrics["time_saved_minutes"] += time_saved

                # Update statistics using calculator
                self.calculator.update_pattern_statistics(self._metrics, dependencies)
                self.calculator.update_monthly_statistics(
                    self._metrics,
                    failures_prevented,
                    time_saved,
                )
                self.calculator.record_audit_history(
                    self._metrics,
                    now,
                    failures_prevented,
                    high_severity_count,
                    time_saved,
                    audit_result,
                )
                self.calculator.update_success_rate(self._metrics)

                # Persist changes
                self.storage.save_metrics(self._metrics)

                logger.info(
                    "Audit recorded: %d failures prevented, %d minutes saved",
                    failures_prevented,
                    time_saved,
                )

            except Exception as e:
                logger.exception("Failed to record audit: %s", e)
                msg = f"Cannot record audit: {e}"
                raise AuditMetricsError(msg) from e

    def generate_html_dashboard(self) -> str:
        """Generate secure HTML dashboard with sanitized content.

        Returns:
            HTML string with complete dashboard

        """
        with self._lock:
            return self.html_exporter.export(self._metrics)

    def export_html_dashboard(self) -> Path:
        """Export dashboard as HTML file.

        Returns:
            Path to generated HTML file

        Raises:
            AuditMetricsError: If export fails

        """
        try:
            html_content = self.generate_html_dashboard()
            html_file = self.workspace_root / "audit_dashboard.html"

            with html_file.open("w", encoding="utf-8") as f:
                f.write(html_content)

            html_file.chmod(0o644)
            logger.info("HTML dashboard exported to %s", html_file)
            return html_file

        except OSError as e:
            msg = f"Cannot export HTML dashboard: {e}"
            raise AuditMetricsError(msg) from e

    def export_json_metrics(self, output_file: Path | None = None) -> Path:
        """Export metrics as JSON for external monitoring systems.

        Args:
            output_file: Optional custom output file path

        Returns:
            Path to exported JSON file

        Raises:
            AuditMetricsError: If export fails

        """
        with self._lock:
            try:
                if output_file is None:
                    output_file = self.workspace_root / "audit_metrics_export.json"

                json_content = self.json_exporter.export(self._metrics)

                with output_file.open("w", encoding="utf-8") as f:
                    f.write(json_content)

                output_file.chmod(0o644)
                logger.info("Metrics exported to %s", output_file)
                return output_file

            except OSError as e:
                msg = f"Cannot export JSON metrics: {e}"
                raise AuditMetricsError(msg) from e

    def print_console_dashboard(self) -> None:
        """Print formatted dashboard to console."""
        with self._lock:
            self.console_reporter.print_dashboard(self._metrics)

    def reset_metrics(self) -> None:
        """Reset all metrics to default state.

        Raises:
            AuditMetricsError: If reset fails

        """
        with self._lock:
            try:
                # Backup current metrics
                if self.metrics_file.exists():
                    backup_file = self.metrics_file.with_suffix(".backup")
                    self.metrics_file.rename(backup_file)
                    logger.info("Metrics backed up to %s", backup_file)

                # Reload default metrics
                self._metrics = self.storage._get_default_metrics()
                self.storage.save_metrics(self._metrics)
                logger.info("Metrics reset to default state")

            except OSError as e:
                msg = f"Cannot reset metrics: {e}"
                raise AuditMetricsError(msg) from e

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get current metrics summary for programmatic access.

        Returns:
            Dictionary with current metrics

        """
        with self._lock:
            return {
                "audits_performed": self._metrics["audits_performed"],
                "failures_prevented": self._metrics["failures_prevented"],
                "time_saved_hours": self._metrics["time_saved_minutes"] / 60,
                "success_rate": self._metrics["success_rate"],
                "last_audit": self._metrics.get("last_audit"),
                "pattern_count": len(self._metrics["pattern_statistics"]),
                "history_count": len(self._metrics["audit_history"]),
            }
