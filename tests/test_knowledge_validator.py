"""Tests for Knowledge Graph Validator.

This module tests the graph inversion, anomaly detection, and health metrics
functionality of the CORTEX Knowledge Validator.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.core.cortex.knowledge_validator import (
    AnomalyReport,
    BrokenLinkDetail,
    HealthMetrics,
    KnowledgeValidator,
    NodeRanking,
    ValidationReport,
)
from scripts.core.cortex.models import (
    DocStatus,
    KnowledgeEntry,
    KnowledgeLink,
    LinkStatus,
    LinkType,
)


@pytest.fixture
def sample_entries() -> list[KnowledgeEntry]:
    """Create sample Knowledge Entries for testing.

    Graph structure:
        A → B (valid)
        A → C (valid)
        B → C (valid)
        C → X (broken - X doesn't exist)
        D (orphan - no inbound links)
        E (dead end - no outbound links)
    """
    entry_a = KnowledgeEntry(
        id="kno-a",
        status=DocStatus.ACTIVE,
        golden_paths=["test"],
        tags=["test"],
        cached_content="Some content with links",
        links=[
            KnowledgeLink(
                source_id="kno-a",
                target_raw="[[B]]",
                target_resolved="kno-b",
                target_id="kno-b",
                type=LinkType.WIKILINK,
                line_number=1,
                context="Link to [[B]]",
                status=LinkStatus.VALID,
                is_valid=True,
            ),
            KnowledgeLink(
                source_id="kno-a",
                target_raw="[[C]]",
                target_resolved="kno-c",
                target_id="kno-c",
                type=LinkType.WIKILINK,
                line_number=2,
                context="Link to [[C]]",
                status=LinkStatus.VALID,
                is_valid=True,
            ),
        ],
        file_path=Path("/fake/path/a.md"),
    )

    entry_b = KnowledgeEntry(
        id="kno-b",
        status=DocStatus.ACTIVE,
        golden_paths=["test"],
        tags=["test"],
        cached_content="Content with link to C",
        links=[
            KnowledgeLink(
                source_id="kno-b",
                target_raw="[[C]]",
                target_resolved="kno-c",
                target_id="kno-c",
                type=LinkType.WIKILINK,
                line_number=1,
                context="See [[C]]",
                status=LinkStatus.VALID,
                is_valid=True,
            ),
        ],
        file_path=Path("/fake/path/b.md"),
    )

    entry_c = KnowledgeEntry(
        id="kno-c",
        status=DocStatus.ACTIVE,
        golden_paths=["test"],
        tags=["test"],
        cached_content="Content with broken link",
        links=[
            KnowledgeLink(
                source_id="kno-c",
                target_raw="[[X]]",
                target_resolved=None,
                target_id=None,
                type=LinkType.WIKILINK,
                line_number=1,
                context="Broken link to [[X]]",
                status=LinkStatus.BROKEN,
                is_valid=False,
            ),
        ],
        file_path=Path("/fake/path/c.md"),
    )

    entry_d = KnowledgeEntry(
        id="kno-d",
        status=DocStatus.ACTIVE,
        golden_paths=["test"],
        tags=["orphan"],
        cached_content="Orphan node - nobody links to this",
        links=[],  # Dead end as well
        file_path=Path("/fake/path/d.md"),
    )

    entry_e = KnowledgeEntry(
        id="kno-e",
        status=DocStatus.ACTIVE,
        golden_paths=["test"],
        tags=["dead-end"],
        cached_content="Dead end node",
        links=[],  # No outbound links
        file_path=Path("/fake/path/e.md"),
    )

    return [entry_a, entry_b, entry_c, entry_d, entry_e]


class TestKnowledgeValidator:
    """Test suite for KnowledgeValidator class."""

    def test_init(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test validator initialization."""
        validator = KnowledgeValidator(sample_entries)

        assert len(validator.entries) == 5
        assert len(validator._id_index) == 5
        assert "kno-a" in validator._id_index
        assert "kno-e" in validator._id_index

    def test_build_inbound_index(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test inbound link index construction.

        Expected inbound links:
        - kno-b: [kno-a]
        - kno-c: [kno-a, kno-b]
        - kno-d: []  (orphan)
        - kno-e: []  (orphan)
        """
        validator = KnowledgeValidator(sample_entries)
        inbound_index = validator.build_inbound_index()

        # Check kno-b has 1 inbound link from kno-a
        assert "kno-b" in inbound_index
        assert len(inbound_index["kno-b"]) == 1
        assert "kno-a" in inbound_index["kno-b"]

        # Check kno-c has 2 inbound links
        assert "kno-c" in inbound_index
        assert len(inbound_index["kno-c"]) == 2
        assert "kno-a" in inbound_index["kno-c"]
        assert "kno-b" in inbound_index["kno-c"]

        # Check orphans (kno-d, kno-e) have no inbound links
        assert "kno-d" not in inbound_index
        assert "kno-e" not in inbound_index

        # kno-a should not be in index (nobody points to it)
        assert "kno-a" not in inbound_index

    def test_detect_orphans(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test orphan node detection.

        Expected orphans: kno-a (entry point), kno-d, kno-e
        """
        validator = KnowledgeValidator(sample_entries)
        orphans = validator.detect_orphans()

        assert len(orphans) == 3
        assert "kno-a" in orphans
        assert "kno-d" in orphans
        assert "kno-e" in orphans

        # kno-b and kno-c should NOT be orphans
        assert "kno-b" not in orphans
        assert "kno-c" not in orphans

    def test_detect_dead_ends(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test dead end node detection.

        Expected dead ends: kno-d, kno-e (both have no outbound links)
        """
        validator = KnowledgeValidator(sample_entries)
        dead_ends = validator.detect_dead_ends()

        assert len(dead_ends) == 2
        assert "kno-d" in dead_ends
        assert "kno-e" in dead_ends

        # Nodes with outbound links should NOT be dead ends
        assert "kno-a" not in dead_ends
        assert "kno-b" not in dead_ends
        assert "kno-c" not in dead_ends

    def test_detect_broken_links(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test broken link detection.

        Expected: 1 broken link from kno-c to X
        """
        validator = KnowledgeValidator(sample_entries)
        broken = validator.detect_broken_links()

        assert len(broken) == 1
        assert broken[0].source_id == "kno-c"
        assert broken[0].target_raw == "[[X]]"
        assert broken[0].line_number == 1
        assert "Broken link" in broken[0].context

    def test_calculate_connectivity_score(
        self,
        sample_entries: list[KnowledgeEntry],
    ) -> None:
        """Test connectivity score calculation.

        Total nodes: 5
        Connected nodes: 3 (kno-a has outbound, kno-b has both, kno-c has both)
        Disconnected: 2 (kno-d and kno-e have neither)
        Score: 3/5 = 60%
        """
        validator = KnowledgeValidator(sample_entries)
        score = validator.calculate_connectivity_score()

        assert score == 60.0

    def test_calculate_link_health_score(
        self,
        sample_entries: list[KnowledgeEntry],
    ) -> None:
        """Test link health score calculation.

        Total links: 4 (2 from A, 1 from B, 1 from C)
        Valid links: 3
        Broken links: 1
        Score: 3/4 = 75%
        """
        validator = KnowledgeValidator(sample_entries)
        score = validator.calculate_link_health_score()

        assert score == 75.0

    def test_calculate_link_health_score_no_links(self) -> None:
        """Test link health score with no links (should return 100%)."""
        entry = KnowledgeEntry(
            id="kno-empty",
            status=DocStatus.ACTIVE,
            golden_paths=["test"],
            tags=[],
            links=[],
            file_path=Path("/fake/empty.md"),
        )

        validator = KnowledgeValidator([entry])
        score = validator.calculate_link_health_score()

        assert score == 100.0

    def test_calculate_top_hubs(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test hub ranking calculation.

        Expected order:
        1. kno-c (2 inbound links)
        2. kno-b (1 inbound link)
        """
        validator = KnowledgeValidator(sample_entries)
        hubs = validator.calculate_top_hubs(top_n=5)

        assert len(hubs) == 2  # Only 2 nodes have inbound links

        # First hub should be kno-c with 2 inbound
        assert hubs[0].node_id == "kno-c"
        assert hubs[0].inbound_count == 2
        assert hubs[0].rank == 1

        # Second hub should be kno-b with 1 inbound
        assert hubs[1].node_id == "kno-b"
        assert hubs[1].inbound_count == 1
        assert hubs[1].rank == 2

    def test_calculate_metrics(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test comprehensive metrics calculation."""
        validator = KnowledgeValidator(sample_entries)
        metrics = validator.calculate_metrics()

        assert isinstance(metrics, HealthMetrics)
        assert metrics.total_nodes == 5
        assert metrics.total_links == 4
        assert metrics.valid_links == 3
        assert metrics.broken_links == 1
        assert metrics.connectivity_score == 60.0
        assert metrics.link_health_score == 75.0

        # Overall score: 0.4 * 60 + 0.6 * 75 = 24 + 45 = 69
        assert metrics.health_score == pytest.approx(69.0)

        # Check top hubs
        assert len(metrics.top_hubs) == 2
        assert metrics.top_hubs[0].node_id == "kno-c"

    def test_detect_anomalies(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test comprehensive anomaly detection."""
        validator = KnowledgeValidator(sample_entries)
        anomalies = validator.detect_anomalies()

        assert isinstance(anomalies, AnomalyReport)
        assert len(anomalies.orphan_nodes) == 3
        assert len(anomalies.dead_end_nodes) == 2
        assert len(anomalies.broken_links) == 1
        assert anomalies.total_issues == 6

    def test_validate(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test complete validation workflow."""
        validator = KnowledgeValidator(sample_entries)
        report = validator.validate()

        assert isinstance(report, ValidationReport)
        assert isinstance(report.metrics, HealthMetrics)
        assert isinstance(report.anomalies, AnomalyReport)

        # Should not be healthy due to broken links
        assert report.is_healthy is False

        # Should have critical errors
        assert len(report.critical_errors) > 0
        assert any("broken links" in err.lower() for err in report.critical_errors)

    def test_validate_healthy_graph(self) -> None:
        """Test validation with a healthy graph (no issues)."""
        # Create a simple healthy graph: A → B, B → A (circular reference)
        entry_a = KnowledgeEntry(
            id="kno-a",
            status=DocStatus.ACTIVE,
            golden_paths=["test"],
            tags=[],
            links=[
                KnowledgeLink(
                    source_id="kno-a",
                    target_raw="[[B]]",
                    target_id="kno-b",
                    type=LinkType.WIKILINK,
                    line_number=1,
                    context="Link to B",
                    status=LinkStatus.VALID,
                    is_valid=True,
                ),
            ],
            file_path=Path("/fake/a.md"),
        )

        entry_b = KnowledgeEntry(
            id="kno-b",
            status=DocStatus.ACTIVE,
            golden_paths=["test"],
            tags=[],
            links=[
                KnowledgeLink(
                    source_id="kno-b",
                    target_raw="[[A]]",
                    target_id="kno-a",
                    type=LinkType.WIKILINK,
                    line_number=1,
                    context="Link to A",
                    status=LinkStatus.VALID,
                    is_valid=True,
                ),
            ],
            file_path=Path("/fake/b.md"),
        )

        validator = KnowledgeValidator([entry_a, entry_b])
        report = validator.validate()

        # Should be healthy
        assert report.is_healthy is True
        assert len(report.critical_errors) == 0

        # Metrics should be perfect
        assert report.metrics.connectivity_score == 100.0
        assert report.metrics.link_health_score == 100.0
        assert report.metrics.health_score == 100.0

    def test_generate_report(self, sample_entries: list[KnowledgeEntry]) -> None:
        """Test Markdown report generation."""
        validator = KnowledgeValidator(sample_entries)
        report = validator.validate()
        markdown = validator.generate_report(report)

        # Check report structure
        assert "# 📊 Knowledge Graph Health Report" in markdown
        assert "## 📈 Executive Summary" in markdown
        assert "## 🏆 Top 5 Most Referenced Documents" in markdown
        assert "## 🔴 Critical Issues" in markdown
        assert "## ⚠️  Warnings" in markdown

        # Check metrics are present
        assert "Total Nodes" in markdown
        assert "Total Links" in markdown
        assert "Overall Health Score" in markdown

        # Check anomalies are reported
        assert "Broken Links" in markdown
        assert "Orphan Nodes" in markdown
        assert "Dead End Nodes" in markdown

        # Check specific data
        assert "kno-c" in markdown  # Top hub
        assert "[[X]]" in markdown  # Broken link target

    def test_generate_report_exclude_sections(
        self,
        sample_entries: list[KnowledgeEntry],
    ) -> None:
        """Test report generation with excluded sections."""
        validator = KnowledgeValidator(sample_entries)
        report = validator.validate()
        markdown = validator.generate_report(
            report,
            include_orphans=False,
            include_dead_ends=False,
        )

        # Orphans and dead ends should not be in the report
        assert "Orphan Nodes" not in markdown
        assert "Dead End Nodes" not in markdown

        # But critical issues should still be there
        assert "Broken Links" in markdown

    def test_save_report(
        self,
        sample_entries: list[KnowledgeEntry],
        tmp_path: Path,
    ) -> None:
        """Test saving report to file."""
        validator = KnowledgeValidator(sample_entries)
        report = validator.validate()

        output_path = tmp_path / "test_report.md"
        validator.save_report(report, output_path)

        # Check file was created
        assert output_path.exists()

        # Check file contains expected content
        content = output_path.read_text(encoding="utf-8")
        assert "# 📊 Knowledge Graph Health Report" in content
        assert "kno-c" in content

    def test_empty_graph(self) -> None:
        """Test validation with empty graph."""
        validator = KnowledgeValidator([])
        report = validator.validate()

        assert report.metrics.total_nodes == 0
        assert report.metrics.total_links == 0
        assert report.metrics.connectivity_score == 0.0
        assert report.metrics.link_health_score == 100.0  # No links = perfect
        assert len(report.anomalies.orphan_nodes) == 0
        assert len(report.anomalies.broken_links) == 0

    def test_inbound_index_caching(
        self,
        sample_entries: list[KnowledgeEntry],
    ) -> None:
        """Test that inbound index is cached after first build."""
        validator = KnowledgeValidator(sample_entries)

        # First call builds the index
        validator.build_inbound_index()

        # Manually modify the cached index
        validator._inbound_index["test-key"] = ["test-value"]

        # Second call should return the cached (modified) index
        index2 = validator.build_inbound_index()

        # Should be the same object (cached)
        assert "test-key" in index2
        assert index2["test-key"] == ["test-value"]


class TestDataModels:
    """Test suite for data model classes."""

    def test_node_ranking_creation(self) -> None:
        """Test NodeRanking dataclass."""
        ranking = NodeRanking(
            node_id="kno-001",
            inbound_count=10,
            rank=1,
        )

        assert ranking.node_id == "kno-001"
        assert ranking.inbound_count == 10
        assert ranking.rank == 1

    def test_broken_link_detail_creation(self) -> None:
        """Test BrokenLinkDetail dataclass."""
        detail = BrokenLinkDetail(
            source_id="kno-001",
            target_raw="[[missing]]",
            line_number=42,
            context="See [[missing]] for details",
        )

        assert detail.source_id == "kno-001"
        assert detail.target_raw == "[[missing]]"
        assert detail.line_number == 42
        assert "missing" in detail.context

    def test_health_metrics_creation(self) -> None:
        """Test HealthMetrics dataclass."""
        metrics = HealthMetrics(
            total_nodes=100,
            total_links=250,
            valid_links=240,
            broken_links=10,
            connectivity_score=95.0,
            link_health_score=96.0,
            health_score=95.6,
        )

        assert metrics.total_nodes == 100
        assert metrics.broken_links == 10
        assert metrics.health_score == 95.6
        assert isinstance(metrics.generated_at, type(metrics.generated_at))

    def test_anomaly_report_total_issues(self) -> None:
        """Test AnomalyReport total_issues property."""
        report = AnomalyReport(
            orphan_nodes=["a", "b", "c"],
            dead_end_nodes=["d", "e"],
            broken_links=[
                BrokenLinkDetail("x", "[[y]]", 1, "context"),
            ],
        )

        assert report.total_issues == 6  # 3 + 2 + 1

    def test_validation_report_creation(self) -> None:
        """Test ValidationReport dataclass."""
        metrics = HealthMetrics(
            total_nodes=10,
            total_links=20,
            valid_links=18,
            broken_links=2,
            connectivity_score=90.0,
            link_health_score=90.0,
            health_score=90.0,
        )

        anomalies = AnomalyReport()

        report = ValidationReport(
            metrics=metrics,
            anomalies=anomalies,
            is_healthy=True,
        )

        assert report.is_healthy is True
        assert report.metrics.total_nodes == 10
        assert len(report.critical_errors) == 0
