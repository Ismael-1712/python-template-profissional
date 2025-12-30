"""UI Presentation Layer - Handles all output formatting for CORTEX CLI.

This module contains all presentation logic, separating it from business logic.
It provides clean interfaces for displaying results, errors, and progress.

Extracted from cli.py as part of Iteration 4: God Function Elimination.

Architecture: Adapter Layer (Hexagonal Architecture)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from scripts.core.cortex.knowledge_orchestrator import SyncSummary
from scripts.core.cortex.mapper import ProjectContext
from scripts.core.cortex.models import (
    DriftCheckResult,
    KnowledgeEntry,
    MigrationSummary,
    SingleGenerationResult,
)
from scripts.core.guardian.hallucination_probe import ProbeResult
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

    @staticmethod
    def display_hooks_installation(installed_hooks: list[str]) -> None:
        """Display Git hooks installation results with hook descriptions.

        Args:
            installed_hooks: List of successfully installed Git hook names
        """
        hook_descriptions = {
            "post-merge": "Runs after git pull/merge",
            "post-checkout": "Runs after git checkout (branch switch)",
            "post-rewrite": "Runs after git rebase/commit --amend",
        }

        typer.secho("✅ Git hooks installed successfully!", fg=typer.colors.GREEN)
        typer.echo()
        typer.echo("📋 Installed hooks:")

        for hook_name in installed_hooks:
            description = hook_descriptions.get(hook_name, "Git hook")
            typer.echo(f"  • {hook_name:<20} - {description}")

        typer.echo()
        typer.secho(
            "🎉 Context map will now auto-regenerate after Git operations!",
            fg=typer.colors.GREEN,
        )
        typer.echo()
        typer.echo("💡 Test it: git checkout - (to switch back and forth)")

    @staticmethod
    def display_migration_summary(
        summary: MigrationSummary,
        path: Path,
        dry_run: bool,
    ) -> None:
        """Display migration summary with mode banner, stats, and sample results.

        Args:
            summary: Migration summary containing stats and detailed results
            path: Directory path that was migrated
            dry_run: Whether this was a dry-run (preview) or apply mode
        """
        # Display mode banner
        if dry_run:
            typer.secho(
                "\n🔍 DRY-RUN MODE: No files will be modified\n",
                fg=typer.colors.YELLOW,
                bold=True,
            )
        else:
            typer.secho(
                "\n⚠️  APPLY MODE: Files will be modified!\n",
                fg=typer.colors.RED,
                bold=True,
            )

        # Display scanning message
        typer.echo(f"📂 Scanning {path} for Markdown files...\n")

        # Print detailed results if files were processed
        if summary.total > 0:
            typer.echo("\n" + "=" * 70)
            typer.secho("\n📊 Migration Summary:", fg=typer.colors.CYAN, bold=True)
            typer.echo("=" * 70)
            typer.echo(f"Total files processed: {summary.total}")
            typer.secho(
                f"  ✅ Created: {summary.created}",
                fg=typer.colors.GREEN,
            )
            typer.secho(
                f"  🔄 Updated: {summary.updated}",
                fg=typer.colors.YELLOW,
            )
            if summary.errors > 0:
                typer.secho(
                    f"  ❌ Errors:  {summary.errors}",
                    fg=typer.colors.RED,
                )
            typer.echo("=" * 70)

            # Show sample of results
            if len(summary.results) > 0:
                typer.echo("\nSample results:")
                for result in summary.results[:5]:
                    status_icon = {
                        "created": "✅",
                        "updated": "🔄",
                        "skipped": "⏭️ ",
                        "error": "❌",
                    }.get(result.action, "❓")
                    file_info = f"{result.file_path.name}: {result.message}"
                    typer.echo(f"  {status_icon} {file_info}")

                if len(summary.results) > 5:
                    typer.echo(f"  ... and {len(summary.results) - 5} more files")
        else:
            typer.secho(
                "\n⚠️  No Markdown files found in the specified directory.",
                fg=typer.colors.YELLOW,
            )

        # Provide next steps for dry-run mode
        if dry_run and (summary.created + summary.updated > 0):
            typer.echo("\n" + "=" * 70)
            typer.secho(
                "\n💡 To apply these changes, run:\n",
                fg=typer.colors.CYAN,
                bold=True,
            )
            typer.secho(f"   cortex migrate {path} --apply", fg=typer.colors.WHITE)
            typer.echo()

    @staticmethod
    def display_config(config_data: dict[str, Any], config_path: Path) -> None:
        """Display audit configuration with YAML formatting and stats.

        Args:
            config_data: Parsed configuration dictionary
            config_path: Path to the configuration file
        """
        import yaml

        typer.echo(f"📄 Configuration: {config_path}")
        typer.echo("=" * 60)
        typer.echo()

        # Format and display YAML
        formatted_yaml = yaml.dump(
            config_data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        typer.echo(formatted_yaml)

        typer.echo("=" * 60)
        typer.echo()

        # Display summary statistics
        typer.secho("📊 Configuration Summary:", fg=typer.colors.CYAN, bold=True)
        typer.echo(f"  Scan Paths: {len(config_data.get('scan_paths', []))}")
        typer.echo(
            f"  File Patterns: {len(config_data.get('file_patterns', []))}",
        )
        typer.echo(
            f"  Exclude Paths: {len(config_data.get('exclude_paths', []))}",
        )
        typer.echo(
            f"  Custom Patterns: {len(config_data.get('custom_patterns', []))}",
        )
        typer.echo()

    @staticmethod
    def display_validation_success() -> None:
        """Display config validation success message."""
        typer.secho("✓ Configuration is valid!", fg=typer.colors.GREEN)
        typer.echo()

    @staticmethod
    def display_config_hints() -> None:
        """Display help hints for config command."""
        typer.echo("💡 Use --show to display configuration")
        typer.echo("💡 Use --validate to check syntax")
        typer.echo("💡 Use --help for more options")

    @staticmethod
    def display_sync_summary(
        summary: SyncSummary,
        entry_id: str | None,
        dry_run: bool,
    ) -> None:
        """Display knowledge sync summary with progress and results.

        Handles complex tri-state display logic:
        - Dry-run mode: Shows what would be synced
        - Success mode: Shows synchronized entries
        - Error mode: Shows mixed success/failure results

        Args:
            summary: Sync summary containing results and counts
            entry_id: Specific entry ID being synced (None = all entries)
            dry_run: Whether this is a dry-run preview
        """
        # Display header
        typer.secho("\n🔄 Knowledge Synchronizer", bold=True, fg=typer.colors.CYAN)
        typer.echo(f"Workspace: {Path.cwd()}")
        if entry_id:
            typer.echo(f"Target Entry: {entry_id}")
        if dry_run:
            typer.echo("Mode: DRY RUN (no changes will be saved)\n")
        else:
            typer.echo()

        # Display progress for each result
        if summary.results:
            typer.echo(f"Processing {summary.total_processed} entries...\n")

            for result in summary.results:
                typer.echo(
                    f"📄 {result.entry.id} ({len(result.entry.sources)} source(s))",
                )

                if dry_run:
                    for source in result.entry.sources:
                        typer.echo(f"   Would sync: {source.url}")
                elif result.status.value == "updated":
                    typer.secho("   ✅ Synchronized", fg=typer.colors.GREEN)
                elif result.status.value == "not_modified":
                    typer.echo("   ℹ️  No changes (304 Not Modified)")
                else:  # error
                    typer.secho(
                        f"   ❌ Failed: {result.error_message}",
                        fg=typer.colors.RED,
                    )

        # Display final summary with tri-state logic
        typer.echo()
        if dry_run:
            typer.secho(
                f"🔍 Dry run complete: "
                f"{summary.total_processed} entries would be synced",
                fg=typer.colors.BLUE,
                bold=True,
            )
        elif summary.error_count == 0:
            typer.secho(
                f"✅ Synchronization complete: "
                f"{summary.successful_count} entries processed",
                fg=typer.colors.GREEN,
                bold=True,
            )
        else:
            typer.secho(
                f"⚠️  Synchronization complete with errors: "
                f"{summary.successful_count} succeeded, {summary.error_count} failed",
                fg=typer.colors.YELLOW,
                bold=True,
            )

    @staticmethod
    def display_probe_result(
        result: ProbeResult,
        canary_id: str,
        verbose: bool,
    ) -> None:
        """Display hallucination probe results (verbose or simple mode).

        Handles dual-mode display:
        - Verbose mode: Detailed scan info with golden paths, tags, metadata
        - Simple mode: Quick pass/fail with actionable hints

        Args:
            result: Probe result containing success status and canary entry
            canary_id: ID of the canary knowledge entry being tested
            verbose: Whether to show detailed validation information
        """
        # Display header
        typer.secho("\n🔍 Hallucination Probe", bold=True, fg=typer.colors.CYAN)
        typer.echo(f"Workspace: {Path.cwd()}")
        typer.echo(f"Target Canary: {canary_id}\n")

        if verbose:
            # Detailed validation mode
            if result.passed:
                typer.secho(
                    f"✅ PASSED: Canary '{canary_id}' found and validated",
                    fg=typer.colors.GREEN,
                    bold=True,
                )
                typer.echo("\n📊 Scan Details:")
                typer.echo(f"   Total entries scanned: {result.total_entries_scanned}")
                if result.found_entry:
                    typer.echo(f"   Canary status: {result.found_entry.status.value}")
                    if result.found_entry.golden_paths:
                        typer.echo(
                            f"   Golden paths: {result.found_entry.golden_paths}",
                        )
                    if result.found_entry.tags:
                        tags_str = ", ".join(result.found_entry.tags)
                        typer.echo(f"   Tags: {tags_str}")
                typer.echo(f"\n💬 Message: {result.message}")
            else:
                typer.secho(
                    f"❌ FAILED: {result.message}",
                    fg=typer.colors.RED,
                    bold=True,
                )
                typer.echo("\n📊 Scan Details:")
                typer.echo(f"   Total entries scanned: {result.total_entries_scanned}")
                typer.echo(
                    "\n⚠️  WARNING: Knowledge system may be hallucinating or "
                    "canary entry is missing!",
                )
        # Simple boolean check mode
        elif result.passed:
            typer.secho(
                f"✅ System healthy - canary '{canary_id}' found and active",
                fg=typer.colors.GREEN,
                bold=True,
            )
            typer.echo("\n💡 Tip: Use --verbose for detailed validation info")
        else:
            typer.secho(
                f"❌ System check failed - canary '{canary_id}' not found or inactive",
                fg=typer.colors.RED,
                bold=True,
            )
            typer.echo(
                f"\n⚠️  WARNING: Knowledge system may be hallucinating!\n"
                f"   - Verify that docs/knowledge/{canary_id}.md exists\n"
                f"   - Check that the entry has status: active\n"
                f"   - Run 'cortex knowledge-scan' to see all entries",
            )
