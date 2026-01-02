"""Knowledge Graph Validator for CORTEX.

This module implements graph inversion, anomaly detection, and health metrics
for the CORTEX Knowledge Graph. It analyzes the connectivity of Knowledge Nodes
and generates diagnostic reports.

Usage:
    validator = KnowledgeValidator(entries)
    report = validator.validate()
    markdown = validator.generate_report(report)

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.core.cortex.models import KnowledgeEntry

from scripts.core.cortex.adapters.reporters import (
    FileReportWriter,
    MarkdownReporter,
)
from scripts.core.cortex.domain.validator_types import (
    AnomalyReport,
    BrokenLinkDetail,
    HealthMetrics,
    NodeRanking,
    ValidationReport,
)
from scripts.core.cortex.models import LinkStatus

logger = logging.getLogger(__name__)


class KnowledgeValidator:
    """Validates Knowledge Graph structure and generates health reports.

    This class implements graph inversion to calculate inbound links,
    detects structural anomalies, and computes health metrics.

    Attributes:
        entries: List of KnowledgeEntry objects to validate
        _id_index: Dictionary mapping node IDs to entries
        _inbound_index: Dictionary mapping node IDs to inbound link sources
    """

    def __init__(self, entries: list[KnowledgeEntry]) -> None:
        """Initialize the validator with a list of entries.

        Args:
            entries: List of KnowledgeEntry objects with resolved links
        """
        self.entries = entries
        self._id_index: dict[str, KnowledgeEntry] = {e.id: e for e in entries}
        self._inbound_index: dict[str, list[str]] = {}

        logger.debug(f"KnowledgeValidator initialized with {len(entries)} entries")

    def build_inbound_index(self) -> dict[str, list[str]]:
        """Build reverse index of inbound links.

        Iterates through all outbound links and creates a mapping of
        target_id -> [source_id_1, source_id_2, ...].

        Returns:
            Dictionary mapping target IDs to lists of source IDs

        Complexity:
            Time: O(N + E) where N = nodes, E = edges
            Space: O(N + E) for the index storage
        """
        # Return cached index if already built
        if self._inbound_index:
            return self._inbound_index

        inbound_index: dict[str, list[str]] = defaultdict(list)

        # Iterate over all entries (O(N))
        for entry in self.entries:
            # Iterate over all links (O(E) total across all entries)
            for link in entry.links:
                # Only count valid links that resolved to a Knowledge Node
                if link.status == LinkStatus.VALID and link.target_id:
                    inbound_index[link.target_id].append(entry.id)

        # Convert defaultdict to regular dict and cache
        self._inbound_index = dict(inbound_index)

        logger.debug(
            f"Built inbound index: {len(self._inbound_index)} nodes have inbound links",
        )

        return self._inbound_index

    def detect_orphans(self) -> list[str]:
        """Detect orphan nodes (nodes with 0 inbound links).

        Returns:
            List of node IDs that have no incoming links
        """
        if not self._inbound_index:
            self.build_inbound_index()

        orphans = [
            entry.id
            for entry in self.entries
            if entry.id not in self._inbound_index
            or len(self._inbound_index[entry.id]) == 0
        ]

        logger.debug(f"Detected {len(orphans)} orphan nodes")
        return orphans

    def detect_dead_ends(self) -> list[str]:
        """Detect dead end nodes (nodes with 0 outbound links).

        Returns:
            List of node IDs that have no outgoing links
        """
        dead_ends = [entry.id for entry in self.entries if len(entry.links) == 0]

        logger.debug(f"Detected {len(dead_ends)} dead end nodes")
        return dead_ends

    def detect_broken_links(self) -> list[BrokenLinkDetail]:
        """Detect all broken links in the graph.

        Returns:
            List of BrokenLinkDetail objects with information about each broken link
        """
        broken = []

        for entry in self.entries:
            for link in entry.links:
                if link.status == LinkStatus.BROKEN:
                    broken.append(
                        BrokenLinkDetail(
                            source_id=entry.id,
                            target_raw=link.target_raw,
                            line_number=link.line_number,
                            context=link.context,
                        ),
                    )

        logger.debug(f"Detected {len(broken)} broken links")
        return broken

    def calculate_connectivity_score(self) -> float:
        """Calculate connectivity score (percentage of connected nodes).

        A node is considered connected if it has at least one inbound OR
        one outbound link.

        Returns:
            Connectivity score (0-100)
        """
        if not self._inbound_index:
            self.build_inbound_index()

        total_nodes = len(self.entries)
        if total_nodes == 0:
            return 0.0

        connected_nodes = sum(
            1
            for entry in self.entries
            if len(entry.links) > 0 or len(self._inbound_index.get(entry.id, [])) > 0
        )

        score = (connected_nodes / total_nodes) * 100
        logger.debug(f"Connectivity score: {score:.2f}%")
        return score

    def calculate_link_health_score(self) -> float:
        """Calculate link health score (percentage of valid links).

        Returns:
            Link health score (0-100)
        """
        total_links = sum(len(entry.links) for entry in self.entries)
        if total_links == 0:
            return 100.0  # No links means perfect health by default

        valid_links = sum(
            sum(1 for link in entry.links if link.status == LinkStatus.VALID)
            for entry in self.entries
        )

        score = (valid_links / total_links) * 100
        logger.debug(f"Link health score: {score:.2f}%")
        return score

    def calculate_top_hubs(self, top_n: int = 5) -> list[NodeRanking]:
        """Calculate top N most referenced nodes (hubs).

        Args:
            top_n: Number of top hubs to return

        Returns:
            List of NodeRanking objects sorted by inbound count (descending)
        """
        if not self._inbound_index:
            self.build_inbound_index()

        # Create rankings from inbound index
        rankings = [
            (node_id, len(inbound_list))
            for node_id, inbound_list in self._inbound_index.items()
        ]

        # Sort by inbound count (descending)
        rankings.sort(key=lambda x: x[1], reverse=True)

        # Convert to NodeRanking objects
        top_hubs = [
            NodeRanking(node_id=node_id, inbound_count=count, rank=i + 1)
            for i, (node_id, count) in enumerate(rankings[:top_n])
        ]

        logger.debug(f"Calculated top {len(top_hubs)} hubs")
        return top_hubs

    def calculate_metrics(self) -> HealthMetrics:
        """Calculate all health metrics for the graph.

        Returns:
            HealthMetrics object with all calculated scores
        """
        total_nodes = len(self.entries)
        total_links = sum(len(entry.links) for entry in self.entries)
        valid_links = sum(
            sum(1 for link in entry.links if link.status == LinkStatus.VALID)
            for entry in self.entries
        )
        broken_links = sum(
            sum(1 for link in entry.links if link.status == LinkStatus.BROKEN)
            for entry in self.entries
        )

        connectivity_score = self.calculate_connectivity_score()
        link_health_score = self.calculate_link_health_score()

        # Overall health score: weighted average
        # 40% connectivity + 60% link health
        health_score = (0.4 * connectivity_score) + (0.6 * link_health_score)

        top_hubs = self.calculate_top_hubs()

        metrics = HealthMetrics(
            total_nodes=total_nodes,
            total_links=total_links,
            valid_links=valid_links,
            broken_links=broken_links,
            connectivity_score=connectivity_score,
            link_health_score=link_health_score,
            health_score=health_score,
            top_hubs=top_hubs,
        )

        logger.info(f"Calculated health metrics: Overall score = {health_score:.2f}")
        return metrics

    def detect_anomalies(self) -> AnomalyReport:
        """Detect all structural anomalies in the graph.

        Returns:
            AnomalyReport object with all detected anomalies
        """
        orphans = self.detect_orphans()
        dead_ends = self.detect_dead_ends()
        broken = self.detect_broken_links()

        anomalies = AnomalyReport(
            orphan_nodes=orphans,
            dead_end_nodes=dead_ends,
            broken_links=broken,
        )

        logger.info(f"Detected {anomalies.total_issues} total anomalies")
        return anomalies

    def validate(self) -> ValidationReport:
        """Run complete validation and generate report.

        Returns:
            ValidationReport with metrics, anomalies, and health status
        """
        logger.info("Starting Knowledge Graph validation...")

        # Build inbound index
        self.build_inbound_index()

        # Calculate metrics
        metrics = self.calculate_metrics()

        # Detect anomalies
        anomalies = self.detect_anomalies()

        # Determine health status
        is_healthy = True
        critical_errors = []
        warnings = []

        # Critical: Broken links
        if len(anomalies.broken_links) > 0:
            is_healthy = False
            critical_errors.append(
                f"🔴 {len(anomalies.broken_links)} broken links detected",
            )

        # Warning: Too many orphans
        orphan_percentage = (
            (len(anomalies.orphan_nodes) / metrics.total_nodes * 100)
            if metrics.total_nodes > 0
            else 0
        )
        if orphan_percentage >= 30:
            critical_errors.append(
                f"🔴 {orphan_percentage:.1f}% orphan nodes (threshold: 30%)",
            )
            is_healthy = False
        elif orphan_percentage >= 10:
            warnings.append(
                f"⚠️  {orphan_percentage:.1f}% orphan nodes (threshold: 10%)",
            )

        # Info: Dead ends
        if len(anomalies.dead_end_nodes) > 0:
            warnings.append(
                f"ℹ️  {len(anomalies.dead_end_nodes)} dead end nodes (can be enriched)",
            )

        # Warning: Low health score
        if metrics.health_score < 70:
            critical_errors.append(
                f"🔴 Health score {metrics.health_score:.1f} below threshold (70)",
            )
            is_healthy = False
        elif metrics.health_score < 80:
            warnings.append(
                f"⚠️  Health score {metrics.health_score:.1f} below target (80)",
            )

        report = ValidationReport(
            metrics=metrics,
            anomalies=anomalies,
            is_healthy=is_healthy,
            critical_errors=critical_errors,
            warnings=warnings,
        )

        logger.info(
            f"Validation complete: {'✅ Healthy' if is_healthy else '❌ Issues found'}",
        )
        return report

    def generate_report(
        self,
        report: ValidationReport,
        include_orphans: bool = True,
        include_dead_ends: bool = True,
    ) -> str:
        """Generate Markdown report from validation results.

        This method delegates to the MarkdownReporter adapter,
        following the Hexagonal Architecture pattern.

        Args:
            report: ValidationReport to format
            include_orphans: Include orphan nodes section
            include_dead_ends: Include dead end nodes section

        Returns:
            Markdown-formatted report string
        """
        return MarkdownReporter.generate(report, include_orphans, include_dead_ends)

    def save_report(self, report: ValidationReport, output_path: Path) -> None:
        """Save validation report to file.

        This method delegates to adapters (MarkdownReporter + FileReportWriter),
        following the Hexagonal Architecture pattern.

        Args:
            report: ValidationReport to save
            output_path: Path where to save the report
        """
        markdown = self.generate_report(report)
        FileReportWriter.save(markdown, output_path)
