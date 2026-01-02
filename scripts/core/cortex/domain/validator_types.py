"""Domain Types for Knowledge Graph Validation.

This module contains pure domain models (dataclasses) representing
the core entities and value objects for Knowledge Graph validation.

These types are infrastructure-agnostic and contain no business logic,
following the principles of Hexagonal Architecture.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class NodeRanking:
    """Ranking of a Knowledge Node by inbound link count.

    Attributes:
        node_id: Knowledge Node identifier
        inbound_count: Number of inbound links
        rank: Position in ranking (1 = most cited)
    """

    node_id: str
    inbound_count: int
    rank: int


@dataclass
class BrokenLinkDetail:
    """Detailed information about a broken link.

    Attributes:
        source_id: Source Knowledge Node ID
        target_raw: Raw target string that failed to resolve
        line_number: Line number where the link appears
        context: Snippet of surrounding text for context
    """

    source_id: str
    target_raw: str
    line_number: int
    context: str


@dataclass
class HealthMetrics:
    """Health metrics for the Knowledge Graph.

    Attributes:
        total_nodes: Total number of Knowledge Nodes
        total_links: Total number of links (all statuses)
        valid_links: Number of successfully resolved links
        broken_links: Number of broken links
        connectivity_score: Percentage of connected nodes (0-100)
        link_health_score: Percentage of valid links (0-100)
        health_score: Overall health score (0-100)
        top_hubs: Top N most referenced nodes
        generated_at: Timestamp of metrics generation
    """

    total_nodes: int
    total_links: int
    valid_links: int
    broken_links: int
    connectivity_score: float
    link_health_score: float
    health_score: float
    top_hubs: list[NodeRanking] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AnomalyReport:
    """Report of structural anomalies in the Knowledge Graph.

    Attributes:
        orphan_nodes: Node IDs with 0 inbound links
        dead_end_nodes: Node IDs with 0 outbound links
        broken_links: Detailed list of broken links
        total_issues: Total count of all anomalies
    """

    orphan_nodes: list[str] = field(default_factory=list)
    dead_end_nodes: list[str] = field(default_factory=list)
    broken_links: list[BrokenLinkDetail] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        """Calculate total number of issues."""
        return (
            len(self.orphan_nodes)
            + len(self.dead_end_nodes)
            + len(
                self.broken_links,
            )
        )


@dataclass
class ValidationReport:
    """Complete validation report for the Knowledge Graph.

    Attributes:
        metrics: Health metrics
        anomalies: Detected anomalies
        is_healthy: True if no critical issues found
        critical_errors: List of critical error messages
        warnings: List of warning messages
    """

    metrics: HealthMetrics
    anomalies: AnomalyReport
    is_healthy: bool = True
    critical_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
