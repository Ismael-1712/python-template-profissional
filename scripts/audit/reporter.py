"""Audit reporter module."""

from __future__ import annotations

import datetime
import json
import logging
import sys
from io import StringIO
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# --- FIX: Adiciona raiz do projeto ao path para imports funcionarem via pre-commit ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# -----------------------------------------------------------------------------------

from scripts.utils.atomic import AtomicFileWriter  # noqa: E402

try:
    import gettext
    import os

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
        # Fallback if translation fails
        def _(message: str) -> str:
            return message
except ImportError:
    # Fallback if gettext is not available
    def _(message: str) -> str:
        return message


class ConsoleAuditFormatter:
    """Formatter for audit reports to console output using Rich components."""

    def format(self, report: dict[str, Any]) -> str:
        """Format audit report as a console-ready string using Rich.

        Maintains backward compatibility by capturing Rich output to a string
        buffer, ensuring existing tests continue to work.
        """
        metadata = report["metadata"]
        summary = report["summary"]
        findings = report["findings"]

        # Create Rich console with string buffer for backward compatibility
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=100)

        # === HEADER PANEL ===
        header = Panel(
            Text(_("🔍 CODE SECURITY AUDIT REPORT"), justify="center"),
            style="bold blue",
            border_style="blue",
        )
        console.print(header)

        # === METADATA GRID ===
        metadata_grid = Table.grid(padding=1)
        metadata_grid.add_column(style="cyan", justify="right")
        metadata_grid.add_column(style="white")

        metadata_grid.add_row(
            _("📅 Timestamp:"),
            metadata["timestamp"],
        )
        metadata_grid.add_row(
            _("📁 Workspace:"),
            metadata["workspace"],
        )
        metadata_grid.add_row(
            _("⏱️  Duration:"),
            f"{metadata['duration_seconds']:.2f}s",
        )
        metadata_grid.add_row(
            _("📄 Files Scanned:"),
            str(metadata["files_scanned"]),
        )

        console.print(metadata_grid)
        console.print()

        # === OVERALL STATUS PANEL ===
        status = summary["overall_status"]
        status_emoji = "✅" if status == "PASS" else "⚠️"
        status_style = "bold green" if status == "PASS" else "bold yellow"

        if status == "FAIL":
            status_style = "bold red"

        status_panel = Panel(
            Text(f"{status_emoji} {status}", justify="center"),
            title=_("OVERALL STATUS"),
            style=status_style,
            border_style=status_style.split()[1],  # Extract color
        )
        console.print(status_panel)
        console.print()

        # === SEVERITY DISTRIBUTION TABLE ===
        severity_dist = summary["severity_distribution"]
        if any(count > 0 for count in severity_dist.values()):
            severity_table = Table(
                title=_("📊 SEVERITY DISTRIBUTION"),
                show_header=True,
                header_style="bold magenta",
            )
            severity_table.add_column(_("Severity"), style="cyan", no_wrap=True)
            severity_table.add_column(_("Count"), justify="right", style="yellow")
            severity_table.add_column(_("Icon"), justify="center")

            severity_icons = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🔵",
                "LOW": "🟢",
            }

            severity_styles = {
                "CRITICAL": "bold red",
                "HIGH": "bold orange3",
                "MEDIUM": "bold blue",
                "LOW": "bold green",
            }

            for severity, count in severity_dist.items():
                if count > 0:
                    severity_table.add_row(
                        severity,
                        str(count),
                        severity_icons.get(severity, "⚪"),
                        style=severity_styles.get(severity, "white"),
                    )

            console.print(severity_table)
            console.print()

        # === TOP FINDINGS TABLE ===
        if findings:
            findings_table = Table(
                title=_("🔍 TOP FINDINGS"),
                show_header=True,
                header_style="bold cyan",
                show_lines=True,
            )
            findings_table.add_column(_("File"), style="magenta", no_wrap=False)
            findings_table.add_column(_("Line"), justify="right", style="cyan")
            findings_table.add_column(_("Severity"), style="yellow")
            findings_table.add_column(_("Description"), style="white")

            # Limit to top 5 findings
            for finding in findings[:5]:
                severity_style = {
                    "CRITICAL": "bold red",
                    "HIGH": "bold orange3",
                    "MEDIUM": "bold blue",
                    "LOW": "bold green",
                }.get(finding.get("severity", "LOW"), "white")

                findings_table.add_row(
                    finding["file"],
                    str(finding["line"]),
                    finding.get("severity", "UNKNOWN"),
                    finding["description"],
                    style=severity_style,
                )

            console.print(findings_table)
            console.print()

        # === RECOMMENDATIONS ===
        if summary["recommendations"]:
            recommendations_md = "## " + _("💡 RECOMMENDATIONS") + "\n\n"
            for rec in summary["recommendations"]:
                recommendations_md += f"- {rec}\n"

            console.print(Markdown(recommendations_md))

        # Return captured string for backward compatibility
        return buf.getvalue()


class AuditReporter:
    """Handles reporting of audit results."""

    def __init__(self, workspace_root: Path):
        """Initialize the reporter."""
        self.workspace_root = workspace_root
        self.logger = logging.getLogger(__name__)

    def generate_summary(
        self,
        findings: list[dict[str, Any]],
        stats: dict[str, Any],
        duration: float,
        scanned_count: int,
    ) -> dict[str, Any]:
        """Generate a summary dictionary from audit results."""
        # Calculate severity distribution
        severity_dist = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in findings:
            severity_dist[f["severity"]] += 1

        # Determine overall status
        if severity_dist["CRITICAL"] > 0 or severity_dist["HIGH"] > 0:
            status = "FAIL"
        elif severity_dist["MEDIUM"] > 0:
            status = "WARNING"
        else:
            status = "PASS"

        # Generate recommendations
        recommendations = self.generate_recommendations(
            severity_dist,
            stats.get("ci_simulation", {}),
        )

        return {
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "workspace": str(self.workspace_root),
                "duration_seconds": duration,
                "files_scanned": scanned_count,
            },
            "summary": {
                "overall_status": status,
                "total_findings": len(findings),
                "severity_distribution": severity_dist,
                "recommendations": recommendations,
            },
            "findings": [f for f in findings],  # Serializeable copy
        }

    def print_summary(self, report: dict[str, Any]) -> None:
        """Print audit summary to console using ConsoleAuditFormatter."""
        formatter = ConsoleAuditFormatter()
        print(formatter.format(report))

    def save_report(
        self,
        report: dict[str, Any],
        output_path: str,
        format: str = "json",
    ) -> None:
        """Save report to file with atomic write guarantees.

        Uses temporary file + atomic move to prevent data corruption
        during write failures (power loss, disk full, etc.).
        """
        path = Path(output_path)

        # Detect format from extension if not specified
        if path.suffix == ".json":
            format = "json"
        elif path.suffix in [".yaml", ".yml"]:
            format = "yaml"

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Use atomic writer with fsync guarantees
        try:
            with AtomicFileWriter(path, fsync=True) as f:
                if format == "json":
                    json.dump(report, f, indent=2, ensure_ascii=False)
                    f.write("\n")  # POSIX compliance
                elif format == "yaml":
                    yaml.dump(report, f, allow_unicode=True)
                else:
                    msg = f"Unsupported format: {format}"
                    raise ValueError(msg)

            self.logger.info(f"Report saved to {path}")

        except Exception:
            # AtomicFileWriter handles cleanup automatically
            raise

    def generate_recommendations(
        self,
        severity_dist: dict[str, int],
        ci_stats: dict[str, Any],
        *args: Any,
    ) -> list[str]:
        """Generate actionable recommendations based on findings."""
        recs = []

        if severity_dist["CRITICAL"] > 0:
            recs.append(_("🔴 CRITICAL: Fix security vulnerabilities before commit"))

        if severity_dist["HIGH"] > 0:
            recs.append(_("🟠 HIGH: Address high-priority security issues"))

        # Check mock usage
        if "_check_test_mocks" in AuditReporter.__dict__:
            missing_mocks = AuditReporter._check_test_mocks()
            if missing_mocks > 0:
                recs.append(
                    _("🧪 Add mocks to {count} test files").format(count=missing_mocks),
                )

        if not ci_stats.get("tests_passed", True):
            recs.append(_("⚠️ Fix failing tests before CI/CD pipeline"))

        if not recs:
            recs.append(_("✅ Code quality meets security standards!"))

        return recs

    @staticmethod
    def _check_test_mocks() -> int:
        """Placeholder for checking test mocks."""
        return 0
