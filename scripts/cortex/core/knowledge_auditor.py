"""Knowledge Graph Auditor - Validates semantic links and connectivity.

This module contains the business logic for auditing the Knowledge Graph.
It validates links between knowledge nodes, calculates health metrics,
and generates comprehensive reports about graph connectivity.

Extracted from cli.py as part of Iteration 3: God Function Elimination.

Architecture: Core Domain Logic (Hexagonal Architecture)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
from scripts.core.cortex.knowledge_validator import (
    KnowledgeValidator,
    ValidationReport,
)
from scripts.core.cortex.link_analyzer import LinkAnalyzer
from scripts.core.cortex.link_resolver import LinkResolver
from scripts.core.cortex.models import KnowledgeEntry


class KnowledgeAuditor:
    """Auditor for Knowledge Graph validation.

    This class encapsulates the business logic for validating the Knowledge
    Graph. It scans knowledge nodes, extracts semantic links, resolves targets,
    and calculates health metrics.

    Usage:
        auditor = KnowledgeAuditor(workspace_root=Path.cwd())
        report = auditor.validate()

        if not report.is_healthy:
            print(f"Health score: {report.metrics.health_score}")
    """

    def __init__(
        self,
        workspace_root: Path,
        knowledge_dir: Path | None = None,
    ) -> None:
        """Initialize the Knowledge Graph auditor.

        Args:
            workspace_root: Root directory of the workspace/project.
            knowledge_dir: Directory containing knowledge nodes
                (default: workspace_root/docs/knowledge).
        """
        self.workspace_root = workspace_root
        self.knowledge_dir = knowledge_dir or (workspace_root / "docs/knowledge")

    def validate(self) -> tuple[ValidationReport, list[KnowledgeEntry]]:
        """Validate the Knowledge Graph and generate health report.

        This is the main entry point for Knowledge Graph validation.

        Returns:
            A tuple of (ValidationReport, list of resolved KnowledgeEntry).
            The ValidationReport contains metrics and anomalies.
            The list of KnowledgeEntry contains all nodes with resolved links.

        Raises:
            FileNotFoundError: If knowledge directory doesn't exist.
            ValueError: If scanning or validation fails.
        """
        # Load Knowledge Entries using KnowledgeScanner
        scanner = KnowledgeScanner(workspace_root=self.workspace_root)
        entries = scanner.scan(knowledge_dir=self.knowledge_dir)

        if not entries:
            # Return empty report if no entries found
            from scripts.core.cortex.knowledge_validator import (
                AnomalyReport,
                HealthMetrics,
            )

            empty_report = ValidationReport(
                metrics=HealthMetrics(
                    total_nodes=0,
                    total_links=0,
                    valid_links=0,
                    broken_links=0,
                    connectivity_score=0.0,
                    link_health_score=0.0,
                    health_score=0.0,
                ),
                anomalies=AnomalyReport(
                    orphan_nodes=[],
                    dead_end_nodes=[],
                    broken_links=[],
                ),
                critical_errors=[],
                warnings=[],
                is_healthy=True,
            )
            return empty_report, []

        # Extract links from cached content
        analyzer = LinkAnalyzer()
        entries_with_links: list[KnowledgeEntry] = []

        for entry in entries:
            if entry.cached_content:
                extracted_links: list[Any] = analyzer.extract_links(
                    entry.cached_content,
                    entry.id,
                )
                # Create new entry with links (Pydantic is frozen)
                entry_updated = entry.model_copy(update={"links": extracted_links})
                entries_with_links.append(entry_updated)
            else:
                entries_with_links.append(entry)

        # Resolve links
        resolver = LinkResolver(entries_with_links, self.workspace_root)
        resolved_entries = resolver.resolve_all()

        # Validate graph and generate report
        validator = KnowledgeValidator(resolved_entries)
        report = validator.validate()

        return report, resolved_entries

    def save_report(
        self,
        report: ValidationReport,
        output_path: Path,
    ) -> None:
        """Save health report to Markdown file.

        Delegates to KnowledgeValidator.save_report().

        Args:
            report: The ValidationReport to save.
            output_path: Path where to save the Markdown report.
        """
        # Create a validator instance just to use save_report
        # This is a temporary solution - ideally save_report would be a
        # standalone function
        validator = KnowledgeValidator([])  # Empty entries, we just need the method
        validator.save_report(report, output_path)
