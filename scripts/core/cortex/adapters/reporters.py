"""Output Adapters for Knowledge Graph Validation Reports.

This module implements the Adapters layer of Hexagonal Architecture,
handling presentation (Markdown formatting) and persistence (file I/O)
concerns independently from the core domain logic.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from scripts.core.cortex.domain.validator_types import (
    AnomalyReport,
    HealthMetrics,
    NodeRanking,
    ValidationReport,
)

logger = logging.getLogger(__name__)


class MarkdownReporter:
    """Adapter for generating Markdown-formatted health reports.

    This class handles the presentation concern of converting
    ValidationReport domain objects into human-readable Markdown.

    Follows the Adapter pattern (Hexagonal Architecture).
    """

    @staticmethod
    def _get_status_info(health_score: float) -> tuple[str, str]:
        """Determine status emoji and text from health score.

        Args:
            health_score: Overall health score (0-100)

        Returns:
            Tuple of (emoji, status_text)
        """
        if health_score >= 90:
            return "🟢", "Excellent"
        if health_score >= 80:
            return "🟢", "Healthy"
        if health_score >= 70:
            return "🟡", "Needs Attention"
        return "🔴", "Critical"

    @staticmethod
    def _build_header(
        generated_at: datetime,
        health_score: float,
        status_emoji: str,
        status_text: str,
    ) -> list[str]:
        """Build report header with frontmatter and title.

        Args:
            generated_at: Timestamp of generation
            health_score: Overall health score
            status_emoji: Status emoji
            status_text: Status text

        Returns:
            List of header lines
        """
        return [
            "---",
            f"generated_at: {generated_at.isoformat()}",
            f"health_score: {health_score:.1f}",
            f"status: {status_text.lower()}",
            "---",
            "",
            "# 📊 Knowledge Graph Health Report",
            "",
            f"**Generated:** {generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Overall Health Score:** {health_score:.1f}/100 ({status_emoji} {status_text})",  # noqa: E501
            "",
            "---",
            "",
        ]

    @staticmethod
    def _build_metrics_table(metrics: HealthMetrics) -> list[str]:
        """Build executive summary metrics table.

        Args:
            metrics: HealthMetrics object

        Returns:
            List of table lines
        """
        m = metrics
        return [
            "## 📈 Executive Summary",
            "",
            "| Metric                  | Value    | Status |",
            "|-------------------------|----------|--------|",
            f"| Total Nodes             | {m.total_nodes}       | -      |",
            f"| Total Links             | {m.total_links}      | -      |",
            f"| Valid Links             | {m.valid_links}      | {'🟢' if m.valid_links == m.total_links else '⚠️'} |",  # noqa: E501
            f"| Broken Links            | {m.broken_links}        | {'🟢' if m.broken_links == 0 else '🔴'} |",  # noqa: E501
            f"| Connectivity Score      | {m.connectivity_score:.1f}%    | {'🟢' if m.connectivity_score >= 80 else '⚠️'} |",  # noqa: E501
            f"| Link Health Score       | {m.link_health_score:.1f}%    | {'🟢' if m.link_health_score >= 90 else '⚠️'} |",  # noqa: E501
            f"| **Overall Health Score**| **{m.health_score:.1f}**| {'🟢' if m.health_score >= 80 else '⚠️'} |",  # noqa: E501
            "",
            "---",
            "",
        ]

    @staticmethod
    def _build_top_hubs(top_hubs: list[NodeRanking]) -> list[str]:
        """Build top hubs section.

        Args:
            top_hubs: List of NodeRanking objects

        Returns:
            List of section lines
        """
        if not top_hubs:
            return []

        lines = [
            "## 🏆 Top 5 Most Referenced Documents (Hubs)",
            "",
            "| Rank | Document ID | Inbound Links | Status |",
            "|------|-------------|---------------|--------|",
        ]
        for hub in top_hubs:
            lines.append(
                f"| {hub.rank}    | {hub.node_id}     | {hub.inbound_count}            | 🟢     |",  # noqa: E501
            )
        lines.extend(
            [
                "",
                "**Interpretation:** These documents are critical references. Ensure they are well-maintained.",  # noqa: E501
                "",
                "---",
                "",
            ],
        )
        return lines

    @staticmethod
    def _build_critical_issues(report: ValidationReport) -> list[str]:
        """Build critical issues section.

        Args:
            report: ValidationReport object

        Returns:
            List of section lines
        """
        a = report.anomalies
        if not (report.critical_errors or a.broken_links):
            return []

        lines = ["## 🔴 Critical Issues", ""]

        if report.critical_errors:
            for error in report.critical_errors:
                lines.append(f"- {error}")
            lines.append("")

        if a.broken_links:
            lines.extend(
                [
                    f"### Broken Links ({len(a.broken_links)} total)",
                    "",
                    "| Source      | Target       | Line | Context                           |",  # noqa: E501
                    "|-------------|--------------|------|-----------------------------------|",
                ],
            )
            for broken in a.broken_links[:10]:
                context_short = (
                    broken.context[:30] + "..."
                    if len(broken.context) > 30
                    else broken.context
                )
                lines.append(
                    f"| {broken.source_id} | `{broken.target_raw}` | {broken.line_number} | {context_short} |",  # noqa: E501
                )
            if len(a.broken_links) > 10:
                lines.append(
                    f"| ... | ... | ... | ... ({len(a.broken_links) - 10} more) |",
                )
            lines.extend(
                [
                    "",
                    "**Recommendation:** Fix these links immediately or mark them as external.",  # noqa: E501
                    "",
                ],
            )

        lines.extend(["---", ""])
        return lines

    @staticmethod
    def _build_orphans_section(orphan_nodes: list[str], total_nodes: int) -> list[str]:
        """Build orphan nodes subsection.

        Args:
            orphan_nodes: List of orphan node IDs
            total_nodes: Total number of nodes

        Returns:
            List of section lines
        """
        if not orphan_nodes:
            return []

        orphan_pct = (len(orphan_nodes) / total_nodes * 100) if total_nodes > 0 else 0
        lines = [
            f"### Orphan Nodes ({len(orphan_nodes)} total - {orphan_pct:.1f}%)",
            "",
            "Documents with no incoming links:",
            "",
        ]
        for orphan in orphan_nodes[:10]:
            lines.append(f"- `{orphan}`")
        if len(orphan_nodes) > 10:
            lines.append(f"- ... ({len(orphan_nodes) - 10} more)")
        lines.extend(
            [
                "",
                (
                    "**Recommendation:** Add links from main navigation "
                    "or index documents."
                ),
                "",
            ],
        )
        return lines

    @staticmethod
    def _build_dead_ends_section(
        dead_end_nodes: list[str], total_nodes: int,
    ) -> list[str]:
        """Build dead end nodes subsection.

        Args:
            dead_end_nodes: List of dead end node IDs
            total_nodes: Total number of nodes

        Returns:
            List of section lines
        """
        if not dead_end_nodes:
            return []

        dead_end_pct = (
            (len(dead_end_nodes) / total_nodes * 100) if total_nodes > 0 else 0
        )
        lines = [
            f"### Dead End Nodes ({len(dead_end_nodes)} total - {dead_end_pct:.1f}%)",
            "",
            "Documents with no outgoing links:",
            "",
        ]
        for dead_end in dead_end_nodes[:10]:
            lines.append(f"- `{dead_end}`")
        if len(dead_end_nodes) > 10:
            lines.append(f"- ... ({len(dead_end_nodes) - 10} more)")
        lines.extend(
            [
                "",
                '**Recommendation:** Add "See Also" sections to enrich navigation.',
                "",
            ],
        )
        return lines

    @staticmethod
    def _build_warnings(
        report: ValidationReport,
        include_orphans: bool,
        include_dead_ends: bool,
    ) -> list[str]:
        """Build warnings section.

        Args:
            report: ValidationReport object
            include_orphans: Include orphan nodes
            include_dead_ends: Include dead end nodes

        Returns:
            List of section lines
        """
        m = report.metrics
        a = report.anomalies

        if not (
            report.warnings
            or (include_orphans and a.orphan_nodes)
            or (include_dead_ends and a.dead_end_nodes)
        ):
            return []

        lines = ["## ⚠️  Warnings", ""]

        for warning in report.warnings:
            lines.append(f"- {warning}")
        if report.warnings:
            lines.append("")

        if include_orphans:
            lines.extend(
                MarkdownReporter._build_orphans_section(a.orphan_nodes, m.total_nodes),
            )

        if include_dead_ends:
            lines.extend(
                MarkdownReporter._build_dead_ends_section(
                    a.dead_end_nodes,
                    m.total_nodes,
                ),
            )

        lines.extend(["---", ""])
        return lines

    @staticmethod
    def _build_action_items(anomalies: AnomalyReport, total_nodes: int) -> list[str]:
        """Build action items section.

        Args:
            anomalies: AnomalyReport object
            total_nodes: Total number of nodes

        Returns:
            List of section lines
        """
        lines = [
            "## 🎯 Action Items",
            "",
            "### High Priority",
            "",
        ]
        if anomalies.broken_links:
            lines.append(
                f"1. ✅ Fix {len(anomalies.broken_links)} broken links "
                "(see table above)",
            )
        if len(anomalies.orphan_nodes) > total_nodes * 0.3:
            lines.append("2. ⚠️  Review orphan nodes and add navigation links")

        lines.extend(
            [
                "",
                "### Medium Priority",
                "",
                '3. ℹ️  Add "See Also" sections to dead end nodes',
                "4. ℹ️  Update top hubs to ensure accuracy",
                "",
                "### Low Priority",
                "",
                "5. 📊 Monitor connectivity score (target: >90%)",
                "",
                "---",
                "",
                "## 📚 How to Improve This Score",
                "",
                "**To reach 95+:**",
                "",
                "- Fix all broken links (→ +5 points)",
                "- Reduce orphans to <5% (→ +3 points)",
                "",
                "**Commands:**",
                "",
                "```bash",
                "# Re-run analysis",
                "cortex audit --links",
                "",
                "# Generate updated report",
                "cortex report --health",
                "```",
                "",
                "---",
                "",
                "**Report generated by CORTEX Knowledge Validator v0.1.0**",
            ],
        )
        return lines

    @staticmethod
    def generate(
        report: ValidationReport,
        include_orphans: bool = True,
        include_dead_ends: bool = True,
    ) -> str:
        """Generate Markdown report from validation results.

        Args:
            report: ValidationReport to format
            include_orphans: Include orphan nodes section
            include_dead_ends: Include dead end nodes section

        Returns:
            Markdown-formatted report string
        """
        m = report.metrics
        status_emoji, status_text = MarkdownReporter._get_status_info(m.health_score)

        lines = []
        lines.extend(
            MarkdownReporter._build_header(
                m.generated_at,
                m.health_score,
                status_emoji,
                status_text,
            ),
        )
        lines.extend(MarkdownReporter._build_metrics_table(m))
        lines.extend(MarkdownReporter._build_top_hubs(m.top_hubs))
        lines.extend(MarkdownReporter._build_critical_issues(report))
        lines.extend(
            MarkdownReporter._build_warnings(
                report,
                include_orphans,
                include_dead_ends,
            ),
        )
        lines.extend(
            MarkdownReporter._build_action_items(report.anomalies, m.total_nodes),
        )

        return "\n".join(lines)


class FileReportWriter:
    """Adapter for persisting reports to the filesystem.

    This class handles the I/O concern of writing reports to disk,
    independently from report generation and validation logic.

    Follows the Adapter pattern (Hexagonal Architecture).
    """

    @staticmethod
    def save(content: str, output_path: Path) -> None:
        """Save report content to file.

        Args:
            content: Report content (typically Markdown string)
            output_path: Path where to save the report
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write report
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Report saved to {output_path}")
