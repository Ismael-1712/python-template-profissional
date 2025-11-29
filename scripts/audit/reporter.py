"""Audit reporter module."""

import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

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
    """Formatter for audit reports to console output."""

    def format(self, report: dict[str, Any]) -> str:
        """Format audit report as a console-ready string."""
        metadata = report["metadata"]
        summary = report["summary"]
        findings = report["findings"]

        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append(_("🔍 CODE SECURITY AUDIT REPORT"))
        lines.append("=" * 60)
        lines.append(
            _("📅 Timestamp: {timestamp}").format(timestamp=metadata["timestamp"]),
        )
        lines.append(
            _("📁 Workspace: {workspace}").format(workspace=metadata["workspace"]),
        )
        lines.append(
            _("⏱️  Duration: {duration:.2f}s").format(
                duration=metadata["duration_seconds"],
            ),
        )
        lines.append(
            _("📄 Files Scanned: {count}").format(count=metadata["files_scanned"]),
        )
        lines.append("-" * 60)

        # Status
        status_emoji = "✅" if summary["overall_status"] == "PASS" else "⚠️"
        lines.append(
            _("\n{emoji} OVERALL STATUS: {status}").format(
                emoji=status_emoji,
                status=summary["overall_status"],
            ),
        )

        # Severity Distribution
        lines.append(_("\n📊 SEVERITY DISTRIBUTION:"))
        for severity, count in summary["severity_distribution"].items():
            if count > 0:
                icon = (
                    "🔴"
                    if severity == "CRITICAL"
                    else "🟠"
                    if severity == "HIGH"
                    else "🔵"
                )
                lines.append(
                    _("  {emoji} {severity}: {count}").format(
                        emoji=icon,
                        severity=severity,
                        count=count,
                    ),
                )

        # Top Findings
        if findings:
            lines.append(_("\n🔍 TOP FINDINGS:"))
            for finding in findings[:5]:
                lines.append(
                    _("  • {file}:{line} - {description}").format(
                        file=finding["file"],
                        line=finding["line"],
                        description=finding["description"],
                    ),
                )

        # Recommendations
        if summary["recommendations"]:
            lines.append(_("\n💡 RECOMMENDATIONS:"))
            for rec in summary["recommendations"]:
                lines.append(f"  • {rec}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


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
            missing_mocks = AuditReporter._check_test_mocks()  # type: ignore
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
