#!/usr/bin/env python3
"""CORTEX Dynamic Document Generator.

Generates documentation (README.md, CONTRIBUTING.md, etc.) automatically
from live project data:
- pyproject.toml (project metadata)
- .cortex/context.json (graph statistics)
- docs/reports/KNOWLEDGE_HEALTH.md (health score)
- CLI introspection (command help texts)

Supports drift detection for CI/CD governance.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import difflib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import frontmatter

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from jinja2 import Environment, FileSystemLoader, select_autoescape


class DocumentType(Enum):
    """Supported document types."""

    README = "README.md"
    CONTRIBUTING = "CONTRIBUTING.md"
    SECURITY = "SECURITY.md"


@dataclass
class DriftResult:
    """Result of drift detection check."""

    has_drift: bool
    diff: str
    current_content: str
    expected_content: str


@dataclass
class ProjectMetadata:
    """Project metadata extracted from pyproject.toml."""

    name: str
    version: str
    description: str
    python_version: str
    author_name: str = "Engineering Team"
    author_email: str = "team@example.com"


@dataclass
class GraphStatistics:
    """Knowledge graph statistics from .cortex/context.json."""

    total_nodes: int
    total_links: int
    valid_links: int
    broken_links: int
    connectivity_score: float
    link_health_score: float


@dataclass
class HealthScore:
    """Health score from KNOWLEDGE_HEALTH.md."""

    score: float
    status: str
    generated_at: str


@dataclass
class CLICommand:
    """CLI command information."""

    name: str
    description: str
    script_path: str


@dataclass
class ReadmeData:
    """Complete data for document generation."""

    project: ProjectMetadata
    graph: GraphStatistics
    health: HealthScore
    cli_commands: list[CLICommand]
    generated_at: str


class DocumentGenerator:
    """Dynamic document generator using Jinja2 templates.

    Supports multiple document types (README, CONTRIBUTING, SECURITY)
    and drift detection for CI/CD governance.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize generator.

        Args:
            project_root: Root directory of the project. If None, auto-detects.
        """
        self.project_root = project_root or self._detect_project_root()
        self.template_dir = self.project_root / "docs" / "templates"

    @staticmethod
    def _detect_project_root() -> Path:
        """Auto-detect project root from current file location."""
        current_file = Path(__file__).resolve()
        # Navigate up from scripts/core/cortex/readme_generator.py to project root
        return current_file.parent.parent.parent.parent

    def extract_project_metadata(self) -> ProjectMetadata:
        """Extract metadata from pyproject.toml.

        Returns:
            ProjectMetadata with name, version, python_version, etc.
        """
        pyproject_path = self.project_root / "pyproject.toml"

        if not pyproject_path.exists():
            msg = f"pyproject.toml not found: {pyproject_path}"
            raise FileNotFoundError(msg)

        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})

        # Extract python version (e.g., ">=3.10" -> "3.10+")
        python_version = project.get("requires-python", ">=3.10")
        python_clean = python_version.replace(">=", "").strip() + "+"

        # Extract author
        authors = project.get("authors", [])
        author_name = (
            authors[0].get("name", "Engineering Team")
            if authors
            else "Engineering Team"
        )
        author_email = (
            authors[0].get("email", "team@example.com")
            if authors
            else "team@example.com"
        )

        return ProjectMetadata(
            name=project.get("name", "unknown"),
            version=project.get("version", "0.0.0"),
            description=project.get("description", "No description"),
            python_version=python_clean,
            author_name=author_name,
            author_email=author_email,
        )

    def extract_graph_statistics(self) -> GraphStatistics:
        """Extract statistics from .cortex/context.json.

        Returns:
            GraphStatistics with metrics like total_nodes, broken_links, etc.
        """
        context_path = self.project_root / ".cortex" / "context.json"

        if not context_path.exists():
            # Return default values if context doesn't exist yet
            return GraphStatistics(
                total_nodes=0,
                total_links=0,
                valid_links=0,
                broken_links=0,
                connectivity_score=0.0,
                link_health_score=100.0,
            )

        with open(context_path, encoding="utf-8") as f:
            data = json.load(f)

        # Extract graph metrics if available
        graph_metrics = data.get("knowledge_graph", {}).get("metrics", {})

        return GraphStatistics(
            total_nodes=graph_metrics.get("total_nodes", 0),
            total_links=graph_metrics.get("total_links", 0),
            valid_links=graph_metrics.get("valid_links", 0),
            broken_links=graph_metrics.get("broken_links", 0),
            connectivity_score=graph_metrics.get("connectivity_score", 0.0),
            link_health_score=graph_metrics.get("link_health_score", 100.0),
        )

    def extract_health_score(self) -> HealthScore:
        """Extract health score from KNOWLEDGE_HEALTH.md.

        Returns:
            HealthScore with score, status, and generation timestamp.
        """
        health_path = self.project_root / "docs" / "reports" / "KNOWLEDGE_HEALTH.md"

        if not health_path.exists():
            return HealthScore(
                score=0.0,
                status="unknown",
                generated_at=datetime.now(tz=timezone.utc).isoformat(),
            )

        # Parse frontmatter using python-frontmatter
        doc = frontmatter.load(str(health_path))

        score = doc.get("health_score", 0.0)
        status = doc.get("status", "unknown")
        generated_at = doc.get(
            "generated_at",
            datetime.now(tz=timezone.utc).isoformat(),
        )

        return HealthScore(
            score=float(score) if isinstance(score, (int, float, str)) else 0.0,
            status=str(status),
            generated_at=str(generated_at),
        )

    def extract_cli_commands(self) -> list[CLICommand]:
        """Extract CLI commands from .cortex/context.json.

        Returns:
            List of CLICommand objects.
        """
        context_path = self.project_root / ".cortex" / "context.json"

        if not context_path.exists():
            return []

        with context_path.open(encoding="utf-8") as f:
            data = json.load(f)

        commands_data = data.get("cli_commands", [])

        return [
            CLICommand(
                name=cmd.get("name", "unknown"),
                description=cmd.get("description", ""),
                script_path=cmd.get("script_path", ""),
            )
            for cmd in commands_data
        ]

    def collect_all_data(self) -> ReadmeData:
        """Collect all data needed for README generation.

        Returns:
            ReadmeData with complete project information.
        """
        return ReadmeData(
            project=self.extract_project_metadata(),
            graph=self.extract_graph_statistics(),
            health=self.extract_health_score(),
            cli_commands=self.extract_cli_commands(),
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    def generate_document(
        self,
        template_name: str,
        output_path: Path | None = None,
    ) -> str:
        """Generate a document from template and live data.

        Args:
            template_name: Name of the Jinja2 template (e.g., "README.md.j2")
            output_path: Where to write the document. If None, returns string only.

        Returns:
            Generated document content as string.
        """
        # Collect data
        data = self.collect_all_data()

        # Setup Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=False,  # Preserve indentation and final lines
            keep_trailing_newline=True,
        )

        # Load template
        template = env.get_template(template_name)

        # Render (str() for mypy; Jinja2 types template.render as Any)
        content = str(
            template.render(
                project=data.project,
                graph=data.graph,
                health=data.health,
                cli_commands=data.cli_commands,
                generated_at=data.generated_at,
            ),
        )

        # Write to file if requested
        if output_path:
            output_path.write_text(content, encoding="utf-8")

        return content

    def generate_readme(self, output_path: Path | None = None) -> str:
        """Generate README.md from template and live data.

        Args:
            output_path: Where to write the README. If None, returns string only.

        Returns:
            Generated README content as string.
        """
        if output_path is None:
            output_path = self.project_root / "README.md"
        return self.generate_document("README.md.j2", output_path)

    def generate_contributing(self, output_path: Path | None = None) -> str:
        """Generate CONTRIBUTING.md from template and live data.

        Args:
            output_path: Where to write the file. If None, returns string only.

        Returns:
            Generated content as string.
        """
        if output_path is None:
            output_path = self.project_root / "CONTRIBUTING.md"
        return self.generate_document("CONTRIBUTING.md.j2", output_path)

    def check_drift(self, file_path: Path, template_name: str) -> DriftResult:
        """Check if a file has drifted from its template.

        Args:
            file_path: Path to the file to check
            template_name: Name of the template that should generate this file

        Returns:
            DriftResult with drift status and diff if applicable
        """
        # Generate expected content (without writing)
        expected_content = self.generate_document(template_name, output_path=None)

        # Read current content
        if not file_path.exists():
            # File doesn't exist - it's drifted
            return DriftResult(
                has_drift=True,
                diff="File does not exist",
                current_content="",
                expected_content=expected_content,
            )

        current_content = file_path.read_text(encoding="utf-8")

        # Normalize: remove timestamp lines for comparison
        # (timestamps change on every generation, but that's not drift)
        def normalize_content(content: str) -> str:
            """Remove timestamp lines for drift comparison."""
            lines = []
            for line in content.splitlines():
                # Skip lines with timestamp patterns
                if "gerado dinamicamente em" in line.lower():
                    continue
                if "generated dynamically at" in line.lower():
                    continue
                if "última atualização:" in line.lower():
                    continue
                if "last updated:" in line.lower():
                    continue
                lines.append(line)
            return "\n".join(lines)

        current_normalized = normalize_content(current_content)
        expected_normalized = normalize_content(expected_content)

        # Compare
        if current_normalized.strip() == expected_normalized.strip():
            return DriftResult(
                has_drift=False,
                diff="",
                current_content=current_content,
                expected_content=expected_content,
            )

        # Generate unified diff
        diff = difflib.unified_diff(
            current_content.splitlines(keepends=True),
            expected_content.splitlines(keepends=True),
            fromfile=str(file_path),
            tofile=f"{file_path} (expected)",
            lineterm="",
        )

        return DriftResult(
            has_drift=True,
            diff="".join(diff),
            current_content=current_content,
            expected_content=expected_content,
        )


# Backward compatibility alias
ReadmeGenerator = DocumentGenerator


def main() -> None:
    """CLI entry point for testing."""
    generator = ReadmeGenerator()
    readme = generator.generate_readme()
    print(readme)


if __name__ == "__main__":
    main()
