"""Audit report generation module.

This module provides functionality for generating audit reports
in multiple formats (JSON, YAML, console).
"""

import gettext
import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml

# i18n setup
_locale_dir = Path(__file__).parent.parent.parent / "locales"
try:
    _translation = gettext.translation(
        "messages",
        localedir=str(_locale_dir),
        languages=[os.getenv("LANGUAGE", "pt_BR")],
        fallback=True,
    )
    _ = _translation.gettext
except Exception:
    # Fallback se não encontrar traduções
    def _(message: str) -> str:
        return message


logger = logging.getLogger(__name__)


class AuditReporter:
    """Generates and saves audit reports in multiple formats."""

    def __init__(self, workspace_root: Path) -> None:
        """Initialize the reporter.

        Args:
            workspace_root: Root directory of the workspace
        """
        self.workspace_root = workspace_root

    def save_report(
        self,
        report: dict[str, Any],
        output_path: Path,
        format_type: str = "json",
    ) -> None:
        """Save audit report in specified format.

        Args:
            report: Report data to save
            output_path: Path where the report will be saved
            format_type: Format type ('json' or 'yaml')

        Raises:
            ValueError: If unsupported format type is provided
        """
        if format_type.lower() == "json":
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        elif format_type.lower() == "yaml":
            with output_path.open("w", encoding="utf-8") as f:
                yaml.dump(report, f, default_flow_style=False, allow_unicode=True)
        else:
            msg = f"Unsupported format: {format_type}"
            raise ValueError(msg)

        logger.info("Report saved to %s", output_path)

    def print_summary(self, report: dict[str, Any]) -> None:
        """Print executive summary of audit results.

        Args:
            report: Complete audit report data
        """
        metadata = report["metadata"]
        summary = report["summary"]

        print(f"\n{'=' * 60}")
        print(_("🔍 CODE SECURITY AUDIT REPORT"))
        print(f"{'=' * 60}")
        print(_("📅 Timestamp: {timestamp}").format(timestamp=metadata["timestamp"]))
        print(_("📁 Workspace: {workspace}").format(workspace=metadata["workspace"]))
        print(
            _("⏱️  Duration: {duration:.2f}s").format(
                duration=metadata["duration_seconds"],
            ),
        )
        print(
            _("📄 Files Scanned: {count}").format(
                count=metadata["files_scanned"],
            ),
        )

        status = summary["overall_status"]
        status_emoji = {
            "PASS": "✅",
            "WARNING": "⚠️",
            "FAIL": "❌",
            "CRITICAL": "🔴",
        }
        print(
            _("\n{emoji} OVERALL STATUS: {status}").format(
                emoji=status_emoji.get(status, "❓"),
                status=status,
            ),
        )

        print(_("\n📊 SEVERITY DISTRIBUTION:"))
        for severity, count in summary["severity_distribution"].items():
            if count > 0:
                emoji = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🔵",
                }.get(severity, "⚪")
                print(
                    _("  {emoji} {severity}: {count}").format(
                        emoji=emoji,
                        severity=severity,
                        count=count,
                    ),
                )

        if report["findings"]:
            print(_("\n🔍 TOP FINDINGS:"))
            for finding in report["findings"][:5]:  # Show top 5
                print(
                    _("  • {file}:{line} - {description}").format(
                        file=finding["file"],
                        line=finding["line"],
                        description=finding["description"],
                    ),
                )

        print(_("\n💡 RECOMMENDATIONS:"))
        for rec in summary["recommendations"]:
            print(f"  {rec}")

        print(f"\n{'=' * 60}")

    @staticmethod
    def generate_recommendations(
        severity_counts: dict[str, int],
        mock_coverage: dict[str, Any],
        ci_simulation: dict[str, Any],
    ) -> list[str]:
        """Generate actionable recommendations based on audit results.

        Args:
            severity_counts: Count of findings by severity level
            mock_coverage: Mock coverage statistics
            ci_simulation: CI simulation results

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if severity_counts.get("CRITICAL", 0) > 0:
            recommendations.append(
                _("🔴 CRITICAL: Fix security vulnerabilities before commit"),
            )

        if severity_counts.get("HIGH", 0) > 0:
            recommendations.append(
                _("🟠 HIGH: Address high-priority security issues"),
            )

        if mock_coverage["files_needing_mocks"]:
            recommendations.append(
                _("🧪 Add mocks to {count} test files").format(
                    count=len(mock_coverage["files_needing_mocks"]),
                ),
            )

        if not ci_simulation.get("passed", True):
            recommendations.append(
                _("⚠️ Fix failing tests before CI/CD pipeline"),
            )

        if not recommendations:
            recommendations.append(
                _("✅ Code quality meets security standards!"),
            )

        return recommendations
