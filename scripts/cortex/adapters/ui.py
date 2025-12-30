"""UI Presentation Layer - Handles all output formatting for CORTEX CLI.

This module contains all presentation logic, separating it from business logic.
It provides clean interfaces for displaying results, errors, and progress.

Extracted from cli.py as part of Iteration 4: God Function Elimination.

Architecture: Adapter Layer (Hexagonal Architecture)
"""

from __future__ import annotations

from pathlib import Path

import typer

from scripts.core.cortex.mapper import ProjectContext
from scripts.core.cortex.models import (
    DriftCheckResult,
    KnowledgeEntry,
    SingleGenerationResult,
)
from scripts.core.guardian.models import ConfigFinding
from scripts.cortex.core.knowledge_auditor import ValidationReport
from scripts.cortex.core.metadata_auditor import AuditReport
from scripts.utils.toml_merger import MergeResult


class UIPresenter:
    """Handles all UI presentation for CORTEX CLI.

    This class encapsulates all typer.echo/secho logic, keeping the CLI
    layer focused on orchestration rather than presentation.

    Usage:
        ui = UIPresenter()
        ui.show_success("Operation completed!")
        ui.display_audit_results(report)
    """

    @staticmethod
    def show_success(message: str, bold: bool = False) -> None:
        """Display success message in green."""
        typer.secho(f"✅ {message}", fg=typer.colors.GREEN, bold=bold)

    @staticmethod
    def show_error(message: str, bold: bool = False) -> None:
        """Display error message in red."""
        typer.secho(f"❌ {message}", fg=typer.colors.RED, bold=bold, err=True)

    @staticmethod
    def show_warning(message: str) -> None:
        """Display warning message in yellow."""
        typer.secho(f"⚠️  {message}", fg=typer.colors.YELLOW)

    @staticmethod
    def show_info(message: str) -> None:
        """Display info message (no color)."""
        typer.echo(message)

    @staticmethod
    def show_header(title: str, width: int = 70) -> None:
        """Display a formatted header."""
        typer.echo("\n" + "=" * width)
        typer.echo(f"  {title}")
        typer.echo("=" * width + "\n")

    @staticmethod
    def show_separator(width: int = 70) -> None:
        """Display a separator line."""
        typer.echo("=" * width)

    @staticmethod
    def display_context_summary(
        context: ProjectContext,
        output: Path,
        include_knowledge: bool,
    ) -> None:
        """Display summary of generated context map.

        Args:
            context: The project context that was generated.
            output: Path where context was saved.
            include_knowledge: Whether knowledge was included.
        """
        UIPresenter.show_success("Context map generated successfully!")
        typer.echo(f"📍 Output: {output}")
        typer.echo()
        typer.echo(f"📦 Project: {context.project_name} v{context.version}")
        typer.echo(f"🐍 Python: {context.python_version}")
        typer.echo(f"🔧 CLI Commands: {len(context.cli_commands)}")
        typer.echo(f"📄 Documents: {len(context.documents)}")
        typer.echo(f"🏗️  Architecture Docs: {len(context.architecture_docs)}")
        typer.echo(f"📦 Dependencies: {len(context.dependencies)}")
        typer.echo(f"🛠️  Dev Dependencies: {len(context.dev_dependencies)}")

        if include_knowledge and context.golden_paths:
            typer.echo(f"✨ Golden Paths: {len(context.golden_paths)}")
            typer.echo("📚 Knowledge Rules: Included")

    @staticmethod
    def display_context_verbose(
        context: ProjectContext,
        include_knowledge: bool,
    ) -> None:
        """Display detailed context information.

        Args:
            context: The project context.
            include_knowledge: Whether knowledge was included.
        """
        typer.echo()
        typer.echo("Available CLI Commands:")
        for cmd in context.cli_commands:
            desc = f" - {cmd.description}" if cmd.description else ""
            typer.echo(f"  • {cmd.name}{desc}")

        if context.architecture_docs:
            typer.echo()
            typer.echo("Architecture Documents:")
            for doc in context.architecture_docs:
                typer.echo(f"  • {doc.title} ({doc.path})")

        if include_knowledge and context.golden_paths:
            typer.echo()
            typer.echo("Golden Paths:")
            for path in context.golden_paths[:5]:
                typer.echo(f"  • {path}")
            if len(context.golden_paths) > 5:
                typer.echo(f"  ... and {len(context.golden_paths) - 5} more")

    @staticmethod
    def display_config_sync_header() -> None:
        """Display header for configuration synchronization."""
        typer.echo()
        UIPresenter.show_separator()
        typer.secho(
            "🔧 Synchronizing configuration from template...",
            fg=typer.colors.CYAN,
            bold=True,
        )
        typer.echo()

    @staticmethod
    def display_config_sync_result(
        result: MergeResult,
        project_root: Path,
    ) -> None:
        """Display result of configuration synchronization.

        Args:
            result: The merge result.
            project_root: Project root for relative path display.
        """
        if result.success:
            UIPresenter.show_success("Configuration updated successfully!", bold=True)
            if result.backup_path:
                backup_rel = result.backup_path.relative_to(project_root)
                typer.echo(f"   Backup: {backup_rel}")

            typer.echo()
            typer.secho(
                "💡 Tip: Review changes with 'git diff pyproject.toml'",
                fg=typer.colors.CYAN,
            )
        else:
            UIPresenter.show_error("Configuration sync failed!", bold=True)
            for conflict in result.conflicts:
                typer.secho(f"   • {conflict}", fg=typer.colors.YELLOW, err=True)

    @staticmethod
    def display_config_sync_template_info(
        template: Path,
        target: Path,
        project_root: Path,
    ) -> None:
        """Display template and target information for config sync."""
        typer.echo(f"📄 Template: {template.relative_to(project_root)}")
        typer.echo(f"📄 Target:   {target.relative_to(project_root)}")
        typer.echo("🎯 Strategy: smart (union + recursive merge)")
        typer.echo()

    @staticmethod
    def display_audit_header() -> None:
        """Display header for audit operation."""
        UIPresenter.show_header("🔒 CORTEX Metadata Audit")

    @staticmethod
    def display_audit_results(report: AuditReport) -> None:
        """Display metadata audit results.

        Args:
            report: The audit report to display.
        """
        # Root Lockdown results
        typer.echo("🔒 Checking Root Lockdown policy...")
        if report.root_violations:
            typer.secho(
                f"  ❌ {len(report.root_violations)} violation(s):",
                fg=typer.colors.RED,
            )
            for violation in report.root_violations:
                typer.secho(f"     • {violation}", fg=typer.colors.RED)
            typer.echo()
        else:
            typer.secho("  ✅ Root Lockdown: OK", fg=typer.colors.GREEN)
            typer.echo()

        # Individual file results
        for result in report.file_results:
            typer.echo(f"🔍 Auditing {result.file_path}...")

            if result.errors:
                typer.secho(
                    f"  ❌ {len(result.errors)} error(s):",
                    fg=typer.colors.RED,
                )
                for error in result.errors:
                    typer.secho(f"     • {error}", fg=typer.colors.RED)

            if result.warnings:
                typer.secho(
                    f"  ⚠️  {len(result.warnings)} warning(s):",
                    fg=typer.colors.YELLOW,
                )
                for warning in result.warnings:
                    typer.secho(f"     • {warning}", fg=typer.colors.YELLOW)

            if result.is_clean:
                typer.secho("  ✅ No issues found", fg=typer.colors.GREEN)

            typer.echo()

        # Summary
        UIPresenter.show_separator()
        typer.echo("\n📊 Audit Summary\n")
        typer.echo(f"Files scanned: {report.files_scanned}")

        if report.total_errors > 0:
            error_msg = (
                f"Total errors: {report.total_errors} "
                f"(in {len(report.files_with_errors)} file(s))"
            )
            typer.secho(error_msg, fg=typer.colors.RED)

        if report.total_warnings > 0:
            warning_msg = f"Total warnings: {report.total_warnings}"
            typer.secho(warning_msg, fg=typer.colors.YELLOW)

        if report.total_errors == 0 and report.total_warnings == 0:
            UIPresenter.show_success("All checks passed!", bold=True)
        elif report.total_errors == 0:
            UIPresenter.show_success("No errors found (only warnings)")
        else:
            msg = (
                f"Found {report.total_errors} error(s) in "
                f"{len(report.files_with_errors)} file(s)"
            )
            UIPresenter.show_error(msg, bold=True)

    @staticmethod
    def display_knowledge_graph_header() -> None:
        """Display header for Knowledge Graph validation."""
        UIPresenter.show_header("🧠 CORTEX Knowledge Graph Validator")

    @staticmethod
    def display_knowledge_metrics(report: ValidationReport) -> None:
        """Display Knowledge Graph health metrics.

        Args:
            report: The validation report to display.
        """
        UIPresenter.show_header("📈 Health Metrics")

        m = report.metrics
        typer.echo(f"Total Nodes:          {m.total_nodes}")
        typer.echo(f"Total Links:          {m.total_links}")
        typer.echo(f"Valid Links:          {m.valid_links}")
        typer.echo(f"Broken Links:         {m.broken_links}")
        typer.echo(f"Connectivity Score:   {m.connectivity_score:.1f}%")
        typer.echo(f"Link Health Score:    {m.link_health_score:.1f}%")

        # Color-coded health score
        health_color = (
            typer.colors.GREEN
            if m.health_score >= 80
            else typer.colors.YELLOW
            if m.health_score >= 70
            else typer.colors.RED
        )
        typer.secho(
            f"\n🎯 Overall Health Score: {m.health_score:.1f}/100",
            fg=health_color,
            bold=True,
        )

        # Display anomalies
        if report.critical_errors:
            UIPresenter.show_header("🔴 Critical Issues")
            for error in report.critical_errors:
                typer.secho(f"  {error}", fg=typer.colors.RED)

        if report.warnings:
            UIPresenter.show_header("⚠️  Warnings")
            for warning in report.warnings:
                typer.secho(f"  {warning}", fg=typer.colors.YELLOW)

    @staticmethod
    def display_knowledge_scan_progress(num_entries: int, total_links: int) -> None:
        """Display progress of knowledge scanning.

        Args:
            num_entries: Number of knowledge entries found.
            total_links: Total number of links extracted.
        """
        typer.echo("📚 Scanning Knowledge Nodes...")
        typer.secho(
            f"  ✅ Found {num_entries} Knowledge Entries",
            fg=typer.colors.GREEN,
        )
        typer.echo(f"\n🔍 Extracted {total_links} semantic links...")

    @staticmethod
    def display_link_resolution(valid_links: int, broken_links: int) -> None:
        """Display link resolution results.

        Args:
            valid_links: Number of valid links found.
            broken_links: Number of broken links found.
        """
        color = typer.colors.GREEN if broken_links == 0 else typer.colors.YELLOW
        typer.secho(
            f"  ✅ Resolved: {valid_links} valid, {broken_links} broken",
            fg=color,
        )

    @staticmethod
    def display_project_info(
        name: str,
        version: str,
        python_version: str,
    ) -> None:
        """Display project metadata.

        Args:
            name: Project name
            version: Project version
            python_version: Python version requirement
        """
        typer.echo()
        typer.secho("✓ Project Metadata:", fg=typer.colors.GREEN)
        typer.echo(f"  Name: {name}")
        typer.echo(f"  Version: {version}")
        typer.echo(f"  Python: {python_version}")

    @staticmethod
    def display_graph_stats(
        total_nodes: int,
        total_links: int,
        connectivity_score: float,
    ) -> None:
        """Display knowledge graph statistics.

        Args:
            total_nodes: Total number of nodes in graph
            total_links: Total number of links in graph
            connectivity_score: Connectivity percentage
        """
        typer.echo()
        typer.secho("✓ Knowledge Graph:", fg=typer.colors.GREEN)
        typer.echo(f"  Nodes: {total_nodes}")
        typer.echo(f"  Links: {total_links}")
        typer.echo(f"  Connectivity: {connectivity_score:.1f}%")

    @staticmethod
    def display_health_score(score: float, status: str) -> None:
        """Display health score with color coding.

        Args:
            score: Health score (0-100)
            status: Health status description
        """
        typer.echo()
        typer.secho("✓ Health Score:", fg=typer.colors.GREEN)
        health_color = (
            typer.colors.GREEN
            if score >= 70
            else typer.colors.YELLOW
            if score >= 50
            else typer.colors.RED
        )
        typer.secho(f"  Score: {score}/100", fg=health_color, bold=True)
        typer.echo(f"  Status: {status}")

    @staticmethod
    def display_drift_result(
        drift_result: DriftCheckResult,
        target_name: str,
    ) -> None:
        """Display drift check result for a single document.

        Args:
            drift_result: DriftCheckResult with has_drift and diff attributes.
            target_name: Name of the target document being checked.
        """
        if drift_result.has_drift:
            typer.secho(
                f"❌ DRIFT DETECTED in {target_name}",
                fg=typer.colors.RED,
                bold=True,
            )
            typer.echo()
            typer.secho("📋 Diff:", fg=typer.colors.YELLOW)
            typer.echo(drift_result.diff)
            typer.echo()
        else:
            typer.secho(f"✅ {target_name} is in sync", fg=typer.colors.GREEN)

    @staticmethod
    def display_generation_result(
        gen_result: SingleGenerationResult,
        dry_run: bool,
    ) -> None:
        """Display generation result for a single document.

        Args:
            gen_result: SingleGenerationResult with success, output_path, etc.
            dry_run: Whether this is a dry-run operation.
        """
        target_name = gen_result.target.upper()
        icon = "📄" if dry_run else "🎨"
        typer.secho(f"{icon} Processing {target_name}...", fg=typer.colors.CYAN)

        if gen_result.success:
            if dry_run:
                typer.secho(
                    f"✅ Would write to: {gen_result.output_path}",
                    fg=typer.colors.YELLOW,
                )
                typer.echo(f"   Size: {gen_result.content_size} bytes")
            else:
                typer.secho(
                    f"✅ Generated: {gen_result.output_path}",
                    fg=typer.colors.GREEN,
                )
                typer.echo(f"   Size: {gen_result.content_size} bytes")
        else:
            typer.secho(
                f"❌ Failed: {gen_result.error_message}",
                fg=typer.colors.RED,
            )

    @staticmethod
    def validate_generate_args(
        target: str,
        output: Path | None,
        check: bool,
        dry_run: bool,
    ) -> None:
        """Validate CLI arguments for generate command.

        Args:
            target: Target document type (readme, contributing, all).
            output: Optional output path.
            check: Whether to check for drift.
            dry_run: Whether this is a dry-run operation.

        Raises:
            typer.Exit: If validation fails.
        """
        valid_targets = ["readme", "contributing", "all"]
        if target not in valid_targets:
            typer.secho(
                f"❌ Invalid target: {target}",
                fg=typer.colors.RED,
                err=True,
            )
            typer.echo(f"Valid targets: {', '.join(valid_targets)}")
            raise typer.Exit(code=1)

        if output and target == "all":
            typer.secho(
                "❌ Cannot use --output with target 'all'",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

        if check and dry_run:
            typer.secho(
                "❌ Cannot use --check with --dry-run",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

    @staticmethod
    def display_init_preview(
        existing_frontmatter: str | None = None,
        generated_frontmatter: str | None = None,
    ) -> None:
        """Display frontmatter preview for init command.

        Args:
            existing_frontmatter: Existing YAML frontmatter to show (optional).
            generated_frontmatter: Generated YAML frontmatter to show (optional).
        """
        if existing_frontmatter:
            typer.echo("Current frontmatter:")
            typer.echo("---")
            for line in existing_frontmatter.split("\n"):
                if line.strip():
                    typer.echo(f"  {line}")
            typer.echo("---")

        if generated_frontmatter:
            typer.echo("Generated frontmatter:")
            typer.echo("---")
            typer.echo(generated_frontmatter.rstrip())
            typer.echo("---")

    @staticmethod
    def display_knowledge_entries(
        entries: list[KnowledgeEntry],
        verbose: bool = False,
    ) -> None:
        """Display list of knowledge entries.

        Args:
            entries: List of KnowledgeEntry objects to display.
            verbose: Whether to show detailed information.
        """
        for entry in entries:
            # Status emoji mapping
            status_emoji = {
                "active": "✅",
                "deprecated": "🚫",
                "draft": "📝",
            }.get(entry.status.value, "📎")

            typer.echo(f"{status_emoji} {entry.id} ({entry.status.value})")

            if verbose:
                if entry.tags:
                    tags_str = ", ".join(entry.tags)
                    typer.echo(f"   Tags: {tags_str}")
                if entry.golden_paths:
                    typer.echo(f"   Golden Paths: {entry.golden_paths}")
                if entry.sources:
                    typer.echo(f"   Sources: {len(entry.sources)} reference(s)")
                if entry.cached_content:
                    content_preview = entry.cached_content[:80].replace("\n", " ")
                    typer.echo(f"   Content: {content_preview}...")
                typer.echo()  # Blank line between entries

    @staticmethod
    def display_guardian_orphans(
        orphans: list[ConfigFinding],
        documented: dict[str, list[Path]] | None = None,
    ) -> None:
        """Display orphaned configuration findings.

        Args:
            orphans: List of orphan configuration objects.
            documented: Dictionary of documented configurations (optional).
        """
        if orphans:
            for orphan in orphans:
                typer.secho(f"  • {orphan.key}", fg=typer.colors.RED, bold=True)
                typer.echo(
                    f"    Location: {orphan.source_file}:{orphan.line_number}",
                )
                if orphan.context:
                    typer.echo(f"    Context: {orphan.context}")
                if orphan.default_value:
                    typer.echo(f"    Default: {orphan.default_value}")
                typer.echo()

        if documented:
            doc_msg = f"✅ {len(documented)} configurations ARE documented:"
            typer.echo(doc_msg)
            for key, files in documented.items():
                file_names = ", ".join(str(f.name) for f in files)
                typer.echo(f"   • {key} → {file_names}")
