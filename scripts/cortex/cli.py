#!/usr/bin/env python3
"""CORTEX - Documentation as Code CLI.

Command-line interface for managing documentation metadata and frontmatter
using the CORTEX system.

Usage:
    cortex init <file>              # Add frontmatter to a markdown file
    cortex init <file> --force      # Overwrite existing frontmatter
    cortex --help                   # Show help

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

# Add project root to sys.path
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.core.cortex.knowledge_orchestrator import (  # noqa: E402
    KnowledgeOrchestrator,
)
from scripts.core.cortex.metadata import (  # noqa: E402
    FrontmatterParseError,
    FrontmatterParser,
)
from scripts.core.cortex.project_orchestrator import (  # noqa: E402
    ProjectOrchestrator,
)
from scripts.core.cortex.readme_generator import (  # noqa: E402
    DocumentGenerator,
)
from scripts.core.guardian.hallucination_probe import HallucinationProbe  # noqa: E402
from scripts.utils.banner import print_startup_banner  # noqa: E402
from scripts.utils.context import trace_context  # noqa: E402
from scripts.utils.logger import setup_logging  # noqa: E402

# Configure logging
logger = setup_logging(__name__, log_file="cortex.log")

# Create Typer app
app = typer.Typer(
    name="cortex",
    help="CORTEX - Documentation as Code Manager",
    add_completion=False,
)


@app.command()
def init(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the Markdown file to initialize with frontmatter",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing frontmatter if present",
        ),
    ] = False,
) -> None:
    """Add YAML frontmatter to a Markdown file.

    Generates and inserts standard CORTEX frontmatter at the beginning
    of a Markdown file. If frontmatter already exists, will prompt for
    confirmation unless --force is used.

    Examples:
        cortex init docs/new-guide.md
        cortex init docs/existing.md --force
    """
    try:
        logger.info(f"Initializing frontmatter for: {path}")

        # Check if file is a markdown file
        if path.suffix.lower() not in [".md", ".markdown"]:
            typer.secho(
                f"⚠️  Warning: File {path} is not a Markdown file (.md)",
                fg=typer.colors.YELLOW,
            )
            if not typer.confirm("Continue anyway?"):
                raise typer.Abort()

        # Initialize orchestrator
        workspace_root = Path.cwd()
        orchestrator = ProjectOrchestrator(workspace_root=workspace_root)

        # Handle interactive confirmation for existing frontmatter
        if not force:
            # Check if file already has frontmatter
            parser = FrontmatterParser()
            try:
                parser.parse_file(path)
                # File has frontmatter, prompt user
                typer.secho(
                    f"⚠️  File {path.name} already has YAML frontmatter.",
                    fg=typer.colors.YELLOW,
                )

                # Show existing frontmatter preview
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                lines = content.split("\n")
                if lines[0].strip() == "---":
                    typer.echo("Current frontmatter:")
                    typer.echo("---")
                    for line in lines[1:]:
                        if line.strip() == "---":
                            break
                        typer.echo(f"  {line}")
                    typer.echo("---")

                if not typer.confirm(
                    "\nDo you want to overwrite it? (Use --force to skip this prompt)",
                ):
                    typer.secho(
                        "✋ Aborted. No changes made.",
                        fg=typer.colors.BLUE,
                    )
                    logger.info("User aborted overwrite")
                    raise typer.Abort()

                # User confirmed, set force=True for orchestrator
                force = True
                logger.info("User confirmed overwrite")

            except FrontmatterParseError:
                # No frontmatter found, proceed normally
                logger.info("No existing frontmatter found")

        # Delegate to orchestrator
        result = orchestrator.initialize_file(path=path, force=force)

        # Handle result based on status
        if result.status == "success":
            typer.secho(
                f"✅ Success! Added frontmatter to {path}",
                fg=typer.colors.GREEN,
            )
            typer.echo()
            typer.echo("Generated frontmatter:")
            # Show the new frontmatter from result
            import yaml

            frontmatter_yaml = yaml.dump(
                result.new_frontmatter,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            typer.echo("---")
            typer.echo(frontmatter_yaml.rstrip())
            typer.echo("---")
            logger.info(f"Successfully added frontmatter to {path}")

        elif result.status == "skipped":
            typer.secho(
                f"⚠️  File {path.name} already has frontmatter. "
                "Use --force to overwrite.",
                fg=typer.colors.YELLOW,
            )
            logger.info(f"Skipped {path} (already has frontmatter)")

        elif result.status == "error":
            typer.secho(f"❌ Error: {result.error}", fg=typer.colors.RED, err=True)
            logger.error(f"Error initializing {path}: {result.error}")
            raise typer.Exit(code=1)

    except typer.Abort:
        raise

    except Exception as e:
        logger.error(f"Error initializing frontmatter: {e}", exc_info=True)
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def migrate(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory containing Markdown files to migrate (e.g., docs/)",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    apply: Annotated[
        bool,
        typer.Option(
            "--apply",
            help="Apply changes to files (default is dry-run mode)",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing frontmatter if present",
        ),
    ] = False,
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive/--no-recursive",
            "-r",
            help="Process subdirectories recursively",
        ),
    ] = True,
) -> None:
    """Migrate documentation files to CORTEX format.

    Intelligently adds YAML frontmatter to Markdown files by:
    - Generating kebab-case IDs from filenames
    - Inferring document type from directory structure
    - Extracting title from first heading
    - Detecting code references automatically

    By default runs in dry-run mode (shows what would be changed).
    Use --apply to actually modify files.

    Examples:
        cortex migrate docs/ --dry-run      # Preview changes (default)
        cortex migrate docs/ --apply         # Apply changes to files
        cortex migrate docs/ --apply --force # Overwrite existing frontmatter
        cortex migrate docs/guides/ --apply  # Migrate specific directory
    """
    try:
        workspace_root = Path.cwd()
        dry_run = not apply

        logger.info("Starting migration of %s (dry_run=%s)", path, dry_run)

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

        # Initialize orchestrator
        orchestrator = ProjectOrchestrator(workspace_root=workspace_root)

        # Perform migration
        typer.echo(f"📂 Scanning {path} for Markdown files...\n")

        summary = orchestrator.migrate_project(
            directory=path,
            dry_run=dry_run,
            force=force,
            recursive=recursive,
        )

        # Print detailed results
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

        # Provide next steps
        if dry_run and (summary.created + summary.updated > 0):
            typer.echo("\n" + "=" * 70)
            typer.secho(
                "\n💡 To apply these changes, run:\n",
                fg=typer.colors.CYAN,
                bold=True,
            )
            typer.secho(f"   cortex migrate {path} --apply", fg=typer.colors.WHITE)
            typer.echo()

        if summary.errors > 0:
            logger.warning("Migration completed with %d error(s)", summary.errors)
            raise typer.Exit(code=1)

        logger.info("Migration completed successfully")

    except typer.Exit:
        # Re-raise Exit exceptions
        raise

    except Exception as e:
        logger.exception("Error during migration")
        typer.secho(f"❌ Migration failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def audit(
    path: Annotated[
        Path | None,
        typer.Argument(
            help="Path to directory or file to audit (default: docs/)",
            exists=False,
            resolve_path=True,
        ),
    ] = None,
    fail_on_error: Annotated[
        bool,
        typer.Option(
            "--fail-on-error",
            help="Exit with error code if validation fails (useful for CI)",
        ),
    ] = False,
    links: Annotated[
        bool,
        typer.Option(
            "--links",
            help="Validate Knowledge Graph links and generate health report",
        ),
    ] = False,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Fail on broken links (requires --links)",
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help=(
                "Output path for health report "
                "(default: docs/reports/KNOWLEDGE_HEALTH.md)"
            ),
        ),
    ] = None,
) -> None:
    """Audit documentation files for metadata and link integrity.

    Scans Markdown files to verify:
    - Valid YAML frontmatter
    - Required metadata fields
    - Links to code files exist
    - Links to other docs exist
    - Knowledge Graph connectivity (with --links flag)

    Examples:
        cortex audit                    # Audit all docs in docs/
        cortex audit docs/guides/       # Audit specific directory
        cortex audit docs/guide.md      # Audit single file
        cortex audit --fail-on-error    # Exit 1 if errors found (CI mode)
        cortex audit --links            # Validate Knowledge Graph
        cortex audit --links --strict   # Fail CI on broken links
    """
    try:
        # ============================================================
        # KNOWLEDGE GRAPH VALIDATION (--links flag)
        # ============================================================
        if links:
            from scripts.cortex.adapters.ui import UIPresenter
            from scripts.cortex.core.knowledge_auditor import (
                KnowledgeAuditor,
                ValidationReport,
            )

            ui = UIPresenter()
            ui.display_knowledge_graph_header()

            workspace_root = Path.cwd()

            # ============================================================
            # RUN AUDITOR (Business Logic Extracted to Core)
            # ============================================================
            ui.show_info("📚 Scanning Knowledge Nodes...")
            auditor = KnowledgeAuditor(
                workspace_root=workspace_root,
                knowledge_dir=workspace_root / "docs/knowledge",
            )
            validation_report: ValidationReport
            validation_report, resolved_entries = auditor.validate()

            # Count and display progress
            num_entries = len(resolved_entries)
            total_links = sum(len(e.links) for e in resolved_entries)
            valid_links = sum(
                sum(1 for link in e.links if link.status.value == "valid")
                for e in resolved_entries
            )
            broken_links_count = sum(
                sum(1 for link in e.links if link.status.value == "broken")
                for e in resolved_entries
            )

            ui.display_knowledge_scan_progress(num_entries, total_links)
            ui.display_link_resolution(valid_links, broken_links_count)

            # Display metrics
            ui.display_knowledge_metrics(validation_report)

            # Save report
            output_path = output or (
                workspace_root / "docs/reports/KNOWLEDGE_HEALTH.md"
            )
            auditor.save_report(validation_report, output_path)
            typer.secho(
                f"\n📄 Report saved to: {output_path.relative_to(workspace_root)}",
                fg=typer.colors.CYAN,
            )

            # Determine exit code
            if strict and len(validation_report.anomalies.broken_links) > 0:
                ui.show_error(
                    "Validation FAILED: Broken links detected (--strict mode)",
                    bold=True,
                )
                raise typer.Exit(code=1)

            if not validation_report.is_healthy:
                ui.show_warning("Validation completed with warnings")
                if fail_on_error:
                    raise typer.Exit(code=1)
            else:
                ui.show_success("Validation PASSED", bold=True)

            return  # Exit after link validation

        # ============================================================
        # STANDARD METADATA AUDIT (original behavior)
        # ============================================================
        from scripts.cortex.core.metadata_auditor import MetadataAuditor

        # Default to docs/ if no path provided
        if path is None:
            path = Path("docs")

        workspace_root = Path.cwd()
        logger.info(f"Starting audit of {path}")

        # Collect markdown files to audit
        md_files: list[Path] = []

        if not path.exists():
            typer.secho(
                f"❌ Error: Path {path} does not exist",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

        if path.is_file():
            if path.suffix in [".md", ".markdown"]:
                md_files = [path]
            else:
                typer.secho(
                    f"❌ Error: {path} is not a Markdown file",
                    fg=typer.colors.RED,
                    err=True,
                )
                raise typer.Exit(code=1)
        elif path.is_dir():
            # Recursively find all .md files
            md_files = list(path.rglob("*.md")) + list(path.rglob("*.markdown"))
        else:
            typer.secho(
                f"❌ Error: {path} is neither a file nor directory",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

        if not md_files:
            typer.secho(
                f"⚠️  No Markdown files found in {path}",
                fg=typer.colors.YELLOW,
            )
            return

        typer.echo(f"\n📋 Found {len(md_files)} Markdown file(s) to audit\n")

        # ============================================================
        # RUN AUDITOR (Business Logic Extracted to Core)
        # ============================================================
        from scripts.cortex.adapters.ui import UIPresenter
        from scripts.cortex.core.metadata_auditor import AuditReport

        ui = UIPresenter()
        metadata_auditor = MetadataAuditor(workspace_root=workspace_root)
        report: AuditReport = metadata_auditor.audit(md_files)

        # ============================================================
        # DISPLAY RESULTS (Interface Layer)
        # ============================================================
        ui.display_audit_results(report)

        logger.info(
            f"Audit complete: {report.total_errors} errors, "
            f"{report.total_warnings} warnings",
        )

        # Exit with error code if requested and errors found
        if fail_on_error and report.total_errors > 0:
            raise typer.Exit(code=1)

    except typer.Exit:
        # Re-raise Exit exceptions
        raise

    except Exception as e:
        logger.error(f"Error during audit: {e}", exc_info=True)
        typer.secho(f"❌ Audit failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command(name="setup-hooks")
def setup_hooks() -> None:
    """Install Git hooks to auto-regenerate context map.

    Creates Git hooks that automatically run 'cortex map' after:
    - git pull / git merge (post-merge hook)
    - git checkout (post-checkout hook)
    - git rebase / git commit --amend (post-rewrite hook)

    This ensures the AI context stays fresh after repository changes.

    Example:
        cortex setup-hooks
    """
    logger.info("Installing Git hooks for CORTEX...")
    typer.echo("🔧 Installing Git hooks for CORTEX...")
    typer.echo()

    # Find .git directory
    git_dir = _project_root / ".git"
    if not git_dir.exists():
        typer.secho(
            "❌ Error: .git directory not found. Are you in a Git repository?",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    # Define hook script content
    hook_script = """#!/bin/bash
# Auto-generated by CORTEX - Do not edit manually
# This hook regenerates the project context map after Git operations

# Check if cortex command exists
if ! command -v cortex &> /dev/null; then
    echo "⚠️  Warning: 'cortex' command not found. Skipping context map regeneration."
    exit 0
fi

echo "🔄 Regenerating CORTEX context map..."
cortex map --output .cortex/context.json

if [ $? -eq 0 ]; then
    echo "✅ Context map updated successfully!"
else
    echo "⚠️  Warning: Failed to update context map"
fi
"""

    # Create hooks
    hooks_to_create = {
        "post-merge": "Runs after git pull/merge",
        "post-checkout": "Runs after git checkout (branch switch)",
        "post-rewrite": "Runs after git rebase/commit --amend",
    }

    installed_hooks = []
    for hook_name, description in hooks_to_create.items():
        hook_path = hooks_dir / hook_name

        # Backup existing hook if present
        if hook_path.exists():
            backup_path = hook_path.with_suffix(".backup")
            typer.echo(f"📦 Backing up existing {hook_name} to {backup_path.name}")
            hook_path.rename(backup_path)
            logger.info("Backed up existing hook: %s", hook_name)

        # Write hook script
        with hook_path.open("w", encoding="utf-8") as f:
            f.write(hook_script)

        # Make executable
        hook_path.chmod(0o755)

        installed_hooks.append((hook_name, description))
        logger.info("Installed hook: %s", hook_name)

    # Display results
    typer.secho("✅ Git hooks installed successfully!", fg=typer.colors.GREEN)
    typer.echo()
    typer.echo("📋 Installed hooks:")
    for hook_name, description in installed_hooks:
        typer.echo(f"  • {hook_name:<20} - {description}")

    typer.echo()
    typer.secho(
        "🎉 Context map will now auto-regenerate after Git operations!",
        fg=typer.colors.GREEN,
    )
    typer.echo()
    typer.echo("💡 Test it: git checkout - (to switch back and forth)")


@app.command(name="knowledge-scan")
def knowledge_scan(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed information about each entry",
        ),
    ] = False,
    parallel: Annotated[
        bool,
        typer.Option(
            "--parallel",
            "--experimental-parallel",
            help=(
                "Force parallel processing (EXPERIMENTAL). "
                "May cause performance regression on some systems due to GIL overhead. "
                "Use for large datasets or high-performance hardware."
            ),
        ),
    ] = False,
) -> None:
    """Scan and validate the Knowledge Base (docs/knowledge).

    Scans the docs/knowledge directory for markdown files with valid
    frontmatter representing knowledge entries. Validates the structure
    and displays a summary of found entries.

    Knowledge entries should have:
    - id: Unique identifier
    - status: Entry status (active, deprecated, draft)
    - golden_paths: Related code paths
    - tags: (optional) Classification tags
    - sources: (optional) External reference URLs

    Examples:
        cortex knowledge-scan              # Scan knowledge base (sequential mode)
        cortex knowledge-scan --verbose    # Show detailed info
        cortex knowledge-scan --parallel   # Use experimental parallel mode
    """
    try:
        workspace_root = Path.cwd()
        logger.info("Scanning Knowledge Base...")

        typer.secho("\n🧠 Knowledge Base Scanner", bold=True, fg=typer.colors.CYAN)
        typer.echo(f"Workspace: {workspace_root}")
        typer.echo("Knowledge Directory: docs/knowledge/\n")

        # Show mode indicator
        if parallel:
            typer.secho(
                "⚡ Mode: EXPERIMENTAL PARALLEL",
                fg=typer.colors.YELLOW,
                bold=True,
            )
            typer.secho(
                "   (GIL may impact performance on some systems)\n",
                fg=typer.colors.YELLOW,
            )
        else:
            typer.echo("📋 Mode: Standard Sequential\n")

        # Instantiate orchestrator and scan
        orchestrator = KnowledgeOrchestrator(
            workspace_root=workspace_root,
            force_parallel=parallel,
        )
        result = orchestrator.scan(verbose=verbose)

        # Display results
        if not result.entries:
            typer.secho(
                "⚠️  No knowledge entries found",
                fg=typer.colors.YELLOW,
            )
            typer.echo(
                "\nTip: Create knowledge entries in docs/knowledge/ "
                "with valid YAML frontmatter.",
            )
            return

        # Success summary
        entry_word = "entry" if result.total_count == 1 else "entries"
        typer.secho(
            f"✅ Found {result.total_count} knowledge {entry_word}",
            fg=typer.colors.GREEN,
            bold=True,
        )
        typer.echo()

        # List entries
        for entry in result.entries:
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

        logger.info(f"Knowledge scan completed: {result.total_count} entries found")

    except Exception as e:
        logger.error(f"Error scanning knowledge base: {e}", exc_info=True)
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command(name="knowledge-sync")
def knowledge_sync(
    entry_id: Annotated[
        str | None,
        typer.Option(
            "--entry-id",
            help="Specific entry ID to synchronize (e.g., 'kno-001'). "
            "If omitted, syncs all entries.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview sync operations without writing to disk",
        ),
    ] = False,
) -> None:
    """Synchronize knowledge entries with external sources.

    Downloads content from external sources defined in knowledge entry
    frontmatter, merges with local content while preserving Golden Paths,
    and updates cache metadata (last_synced, etag).

    If --entry-id is provided, only that specific entry will be synchronized.
    Otherwise, all entries with external sources will be processed.

    Use --dry-run to preview what would be synced without making changes.

    Examples:
        cortex knowledge-sync                    # Sync all entries
        cortex knowledge-sync --entry-id kno-001 # Sync specific entry
        cortex knowledge-sync --dry-run          # Preview sync operations
    """
    try:
        workspace_root = Path.cwd()
        logger.info("Starting knowledge synchronization...")

        typer.secho("\n🔄 Knowledge Synchronizer", bold=True, fg=typer.colors.CYAN)
        typer.echo(f"Workspace: {workspace_root}")
        if entry_id:
            typer.echo(f"Target Entry: {entry_id}")
        if dry_run:
            typer.echo("Mode: DRY RUN (no changes will be saved)\n")
        else:
            typer.echo()

        # Use orchestrator to handle scan, filter, and sync logic
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)
        summary = orchestrator.sync_multiple(entry_id=entry_id, dry_run=dry_run)

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

        # Display summary
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

        logger.info(
            f"Knowledge sync completed: "
            f"{summary.successful_count} succeeded, {summary.error_count} failed",
        )

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error during knowledge sync: {e}", exc_info=True)
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command(name="guardian-probe")
def guardian_probe(
    canary_id: Annotated[
        str,
        typer.Option(
            "--canary-id",
            help="ID of the canary knowledge entry to search for (default: kno-001)",
        ),
    ] = "kno-001",
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed validation information",
        ),
    ] = False,
) -> None:
    """Run the Hallucination Probe to verify Knowledge Node integrity.

    The Hallucination Probe implements the "Needle Test" pattern to detect
    hallucination in the knowledge system. It searches for a specific canary
    knowledge entry and validates its properties to ensure the system is not
    fabricating or losing knowledge.

    This serves as a sanity check for the Knowledge Scanner and ensures the
    integrity of the knowledge base.

    Examples:
        cortex guardian-probe                      # Run probe with default canary
        cortex guardian-probe --canary-id kno-002  # Test specific entry
        cortex guardian-probe --verbose            # Show detailed validation
    """
    try:
        workspace_root = Path.cwd()
        logger.info(f"Running Hallucination Probe for canary: {canary_id}")

        typer.secho("\n🔍 Hallucination Probe", bold=True, fg=typer.colors.CYAN)
        typer.echo(f"Workspace: {workspace_root}")
        typer.echo(f"Target Canary: {canary_id}\n")

        # Initialize and run probe
        probe = HallucinationProbe(
            workspace_root=workspace_root,
            canary_id=canary_id,
        )

        if verbose:
            # Detailed validation mode
            result = probe.run()

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
                logger.error(f"Hallucination probe failed: {result.message}")
                raise typer.Exit(code=1)
        # Simple boolean check
        elif probe.probe():
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
            logger.error(f"Hallucination probe failed for canary: {canary_id}")
            raise typer.Exit(code=1)

        logger.info("Hallucination probe completed successfully")

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error during hallucination probe: {e}", exc_info=True)
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command(name="config")
def config_manager(
    show: Annotated[
        bool,
        typer.Option(
            "--show",
            help="Display current audit configuration",
        ),
    ] = False,
    validate: Annotated[
        bool,
        typer.Option(
            "--validate",
            help="Validate configuration file syntax",
        ),
    ] = False,
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Path to audit configuration file",
        ),
    ] = Path("scripts/audit_config.yaml"),
) -> None:
    """Manage CORTEX and Audit configurations.

    Display, validate, or manage configuration files used by the auditor
    and other CORTEX tools.

    Examples:
        cortex config --show                    # Display current config
        cortex config --validate                # Validate YAML syntax
        cortex config --path custom_config.yaml --show
    """
    import yaml

    try:
        # Resolve path relative to project root
        config_path = _project_root / path if not path.is_absolute() else path

        if not config_path.exists():
            typer.secho(
                f"❌ Configuration file not found: {config_path}",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

        # Read configuration
        logger.info(f"Reading configuration from: {config_path}")
        with config_path.open("r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        # Validate YAML syntax
        if validate:
            typer.echo("🔍 Validating configuration file...")
            if config_data is None:
                typer.secho(
                    "⚠️  Configuration file is empty",
                    fg=typer.colors.YELLOW,
                )
                raise typer.Exit(code=1)

            # Check for required keys
            required_keys = ["scan_paths", "file_patterns", "exclude_paths"]
            missing_keys = [key for key in required_keys if key not in config_data]

            if missing_keys:
                typer.secho(
                    f"❌ Missing required keys: {', '.join(missing_keys)}",
                    fg=typer.colors.RED,
                    err=True,
                )
                raise typer.Exit(code=1)

            typer.secho("✓ Configuration is valid!", fg=typer.colors.GREEN)
            typer.echo()

        # Display configuration
        if show:
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

        # If neither show nor validate, display help
        if not show and not validate:
            typer.echo("💡 Use --show to display configuration")
            typer.echo("💡 Use --validate to check syntax")
            typer.echo("💡 Use --help for more options")

    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}", exc_info=True)
        typer.secho(
            f"❌ Invalid YAML syntax: {e}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1) from e
    except OSError as e:
        logger.error(f"File error: {e}", exc_info=True)
        typer.secho(
            f"❌ Error reading file: {e}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1) from e
    except Exception as e:
        logger.error(f"Error managing configuration: {e}", exc_info=True)
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command(name="map")
def project_map(
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output path for context JSON file",
        ),
    ] = Path(".cortex/context.json"),
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed output",
        ),
    ] = False,
    include_knowledge: Annotated[
        bool,
        typer.Option(
            "--include-knowledge/--no-knowledge",
            help=(
                "Include Project Rules & Golden Paths from Knowledge Node "
                "(default: True)"
            ),
        ),
    ] = True,
    update_config: Annotated[
        bool,
        typer.Option(
            "--update-config",
            help="Sync pyproject.toml from template after mapping",
        ),
    ] = False,
    template_path: Annotated[
        Path | None,
        typer.Option(
            "--template",
            help="Path to template TOML (default: templates/pyproject.toml)",
        ),
    ] = None,
) -> None:
    """Generate project context map for introspection.

    Scans the project structure and generates a comprehensive context map
    containing information about CLI commands, documentation, dependencies,
    and architecture. This map can be used by LLMs or automation tools.

    The output is saved to .cortex/context.json by default.

    By default, the map includes Project Rules & Golden Paths from the
    Knowledge Node (docs/knowledge). Use --no-knowledge to disable this.

    NEW: Use --update-config to synchronize pyproject.toml from template
    after generating the context map.

    Example:
        cortex map                          # Generate context map with knowledge
        cortex map --verbose               # Show detailed information
        cortex map --no-knowledge          # Skip knowledge extraction
        cortex map -o custom/path.json     # Custom output location
        cortex map --update-config         # Map + sync config from template
        cortex map --update-config --template=custom.toml  # Custom template
    """
    try:
        from scripts.cortex.adapters.ui import UIPresenter
        from scripts.cortex.core.context_mapper import ContextMapper

        logger.info("Generating project context map...")
        ui = UIPresenter()

        if verbose:
            ui.show_info("🔍 Scanning project structure...")
            if include_knowledge:
                ui.show_info("🧠 Including Knowledge Node rules...")

        # Generate context map
        mapper = ContextMapper(project_root=_project_root)

        if update_config:
            # Map + Config Sync
            result = mapper.map_and_sync_config(
                output=output,
                include_knowledge=include_knowledge,
                template_path=template_path,
            )

            # Display context summary
            ui.display_context_summary(result.context, output, include_knowledge)

            if verbose:
                ui.display_context_verbose(result.context, include_knowledge)

            logger.info(f"Context map saved to {output}")

            # Display config sync results
            if result.config_sync_result is None:
                # Template not found
                ui.display_config_sync_header()
                template = mapper.get_template_path(template_path)
                ui.show_warning(
                    f"Template not found: {template.relative_to(_project_root)}",
                )
                ui.show_info("   Skipping configuration sync.")
                return

            ui.display_config_sync_header()
            template = mapper.get_template_path(template_path)
            target = _project_root / "pyproject.toml"
            ui.display_config_sync_template_info(template, target, _project_root)

            ui.display_config_sync_result(result.config_sync_result, _project_root)

            if not result.config_sync_result.success:
                logger.error(
                    "Config sync failed",
                    extra={"conflicts": result.config_sync_result.conflicts},
                )
        else:
            # Map only
            result = mapper.map_project(
                output=output,
                include_knowledge=include_knowledge,
            )

            ui.display_context_summary(result.context, output, include_knowledge)

            if verbose:
                ui.display_context_verbose(result.context, include_knowledge)

            logger.info(f"Context map saved to {output}")

    except Exception as e:
        logger.error(f"Error generating context map: {e}", exc_info=True)
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


# ============================================================================
# Guardian Commands - Visibility Guardian for orphaned configs
# ============================================================================

guardian_app = typer.Typer(
    name="guardian",
    help="Visibility Guardian - Detect undocumented configurations",
)
app.add_typer(guardian_app, name="guardian")


# ============================================================================
# Neural Commands - Semantic Search and Vector Indexing
# ============================================================================

from scripts.cli.neural import app as neural_app  # noqa: E402

app.add_typer(neural_app, name="neural")


@guardian_app.command("check")
def guardian_check(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to scan for configurations (file or directory)",
            exists=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    fail_on_error: Annotated[
        bool,
        typer.Option(
            "--fail-on-error",
            "-f",
            help="Exit with error code if orphans are found",
        ),
    ] = False,
    docs_path: Annotated[
        Path,
        typer.Option(
            "--docs",
            "-d",
            help="Path to documentation directory",
            exists=True,
            dir_okay=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = Path("docs"),
) -> None:
    """Check for undocumented configurations (orphans).

    Scans Python code for environment variables and other configurations,
    then checks if they are documented. Reports any "orphans" - configurations
    that appear in code but not in documentation.

    Examples:
        cortex guardian check src/
        cortex guardian check src/config.py --fail-on-error
        cortex guardian check . --docs custom_docs/
    """
    try:
        from scripts.cortex.core.guardian_orchestrator import GuardianOrchestrator

        typer.secho("\n🔍 Visibility Guardian - Orphan Detection", bold=True)
        typer.echo(f"Scanning: {path}")
        typer.echo(f"Documentation: {docs_path}\n")

        # Execute orphan detection
        orchestrator = GuardianOrchestrator()
        result = orchestrator.check_orphans(scan_path=path, docs_path=docs_path)

        # Display scan errors if any
        if result.scan_errors:
            typer.secho(
                "⚠️  Some files had errors during scanning:",
                fg=typer.colors.YELLOW,
            )
            for error in result.scan_errors:
                typer.echo(f"   • {error}")

        # Display findings
        findings_msg = (
            f"   Found {result.total_findings} configurations in "
            f"{result.files_scanned} files"
        )
        typer.echo(findings_msg)

        if result.total_findings == 0:
            typer.secho(
                "✅ No configurations found - nothing to check!",
                fg=typer.colors.GREEN,
            )
            return

        # Display results
        typer.echo("\n" + "=" * 70)
        typer.secho("📊 RESULTS", bold=True)
        typer.echo("=" * 70)

        if not result.has_orphans:
            typer.secho(
                "\n✅ SUCCESS: All configurations are documented!",
                fg=typer.colors.GREEN,
                bold=True,
            )
            msg = f"   {len(result.documented)} configurations found in documentation"
            typer.echo(msg)
        else:
            orphan_msg = (
                f"\n❌ ORPHANS DETECTED: {len(result.orphans)} "
                "undocumented configurations"
            )
            typer.secho(
                orphan_msg,
                fg=typer.colors.RED,
                bold=True,
            )
            typer.echo()

            for orphan in result.orphans:
                typer.secho(f"  • {orphan.key}", fg=typer.colors.RED, bold=True)
                typer.echo(f"    Location: {orphan.source_file}:{orphan.line_number}")
                if orphan.context:
                    typer.echo(f"    Context: {orphan.context}")
                if orphan.default_value:
                    typer.echo(f"    Default: {orphan.default_value}")
                typer.echo()

            if result.documented:
                doc_msg = f"✅ {len(result.documented)} configurations ARE documented:"
                typer.echo(doc_msg)
                for key, files in result.documented.items():
                    typer.echo(f"   • {key} → {', '.join(str(f.name) for f in files)}")

            if fail_on_error:
                typer.echo()
                typer.secho(
                    "💥 Exiting with error (--fail-on-error)",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=1)

        typer.echo()

    except Exception as e:
        logger.error("Error during guardian check: %s", e, exc_info=True)
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command(name="generate")
def generate_docs(
    target: Annotated[
        str,
        typer.Argument(
            help="Document to generate: 'readme', 'contributing', or 'all'",
        ),
    ] = "readme",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Custom output path (only valid for single target)",
            dir_okay=False,
            writable=True,
            resolve_path=True,
        ),
    ] = None,
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Check if document is in sync (for CI/CD drift detection)",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would be generated without writing to file",
        ),
    ] = False,
) -> None:
    """Generate dynamic documentation from templates and live data.

    Extracts data from:
    - pyproject.toml (project name, version, Python version)
    - .cortex/context.json (knowledge graph statistics)
    - docs/reports/KNOWLEDGE_HEALTH.md (health score)
    - CLI introspection (available commands)

    Examples:
        cortex generate readme              # Generate README.md
        cortex generate contributing        # Generate CONTRIBUTING.md
        cortex generate all                 # Generate all documents
        cortex generate readme --check      # Check if README is in sync (CI)
        cortex generate --dry-run           # Preview without writing
    """
    try:
        with trace_context():
            # Validate target
            valid_targets = ["readme", "contributing", "all"]
            if target not in valid_targets:
                typer.secho(
                    f"❌ Invalid target: {target}",
                    fg=typer.colors.RED,
                    err=True,
                )
                typer.echo(f"Valid targets: {', '.join(valid_targets)}")
                raise typer.Exit(code=1)

            # Validate options
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

            # Initialize generator
            generator = DocumentGenerator()

            # Determine which documents to generate
            targets_to_process = []
            if target == "all":
                targets_to_process = [
                    ("readme", "README.md.j2", generator.project_root / "README.md"),
                    (
                        "contributing",
                        "CONTRIBUTING.md.j2",
                        generator.project_root / "CONTRIBUTING.md",
                    ),
                ]
            elif target == "readme":
                output_path = output or generator.project_root / "README.md"
                targets_to_process = [("readme", "README.md.j2", output_path)]
            elif target == "contributing":
                output_path = output or generator.project_root / "CONTRIBUTING.md"
                targets_to_process = [
                    ("contributing", "CONTRIBUTING.md.j2", output_path),
                ]

            # Header
            typer.echo()
            mode = "CHECK MODE" if check else "GENERATION MODE"
            typer.secho(f"🔨 CORTEX Dynamic Document Generator ({mode})", bold=True)
            typer.echo("=" * 70)

            # Collect data once
            typer.echo()
            typer.secho("📊 Collecting data sources...", fg=typer.colors.CYAN)
            data = generator.collect_all_data()

            # Display collected data
            typer.echo()
            typer.secho("✓ Project Metadata:", fg=typer.colors.GREEN)
            typer.echo(f"  Name: {data.project.name}")
            typer.echo(f"  Version: {data.project.version}")
            typer.echo(f"  Python: {data.project.python_version}")

            typer.echo()
            typer.secho("✓ Knowledge Graph:", fg=typer.colors.GREEN)
            typer.echo(f"  Nodes: {data.graph.total_nodes}")
            typer.echo(f"  Links: {data.graph.total_links}")
            typer.echo(f"  Connectivity: {data.graph.connectivity_score:.1f}%")

            typer.echo()
            typer.secho("✓ Health Score:", fg=typer.colors.GREEN)
            health_color = (
                typer.colors.GREEN
                if data.health.score >= 70
                else typer.colors.YELLOW
                if data.health.score >= 50
                else typer.colors.RED
            )
            typer.secho(f"  Score: {data.health.score}/100", fg=health_color, bold=True)
            typer.echo(f"  Status: {data.health.status}")

            # Process each target
            has_drift = False
            for target_name, template_name, output_path in targets_to_process:
                typer.echo()
                typer.secho(
                    f"{'🔍' if check else '🎨'} Processing {target_name.upper()}...",
                    fg=typer.colors.CYAN,
                )

                if check:
                    # Drift detection mode
                    result = generator.check_drift(output_path, template_name)

                    if result.has_drift:
                        has_drift = True
                        typer.secho(
                            f"❌ DRIFT DETECTED in {output_path.name}",
                            fg=typer.colors.RED,
                            bold=True,
                        )
                        typer.echo()
                        typer.secho("📋 Diff:", fg=typer.colors.YELLOW)
                        typer.echo(result.diff)
                        typer.echo()
                    else:
                        typer.secho(
                            f"✅ {output_path.name} is in sync",
                            fg=typer.colors.GREEN,
                        )
                else:
                    # Generation mode
                    content = generator.generate_document(
                        template_name,
                        output_path=None if dry_run else output_path,
                    )

                    if dry_run:
                        typer.echo()
                        typer.secho(
                            f"📄 DRY RUN - Preview of {output_path.name} "
                            f"(first 30 lines):",
                            bold=True,
                        )
                        typer.echo("=" * 70)
                        preview_lines = content.split("\n")[:30]
                        for line in preview_lines:
                            typer.echo(line)
                        typer.echo("...")
                        typer.echo("=" * 70)
                        typer.secho(
                            f"✅ Would write to: {output_path}",
                            fg=typer.colors.YELLOW,
                        )
                    else:
                        typer.secho(
                            f"✅ Generated: {output_path}",
                            fg=typer.colors.GREEN,
                        )
                        typer.echo(f"   Size: {len(content)} bytes")

            # Final summary
            typer.echo()
            typer.echo("=" * 70)

            if check:
                if has_drift:
                    typer.secho(
                        "💥 DRIFT DETECTED - Documents are out of sync!",
                        fg=typer.colors.RED,
                        bold=True,
                    )
                    typer.echo()
                    typer.echo("💡 To fix, run:")
                    typer.echo(f"   cortex generate {target}")
                    typer.echo()
                    logger.warning("Drift detected in generated documents")
                    raise typer.Exit(code=1)
                typer.secho(
                    "✅ All documents are in sync!",
                    fg=typer.colors.GREEN,
                    bold=True,
                )
                logger.info("Drift check passed")
            elif dry_run:
                typer.secho("✅ Dry run completed", fg=typer.colors.GREEN)
            else:
                typer.secho(
                    f"✅ SUCCESS - {len(targets_to_process)} document(s) generated!",
                    fg=typer.colors.GREEN,
                    bold=True,
                )
                typer.echo(f"📅 Generated at: {data.generated_at}")
                logger.info(
                    f"Document generation completed: {len(targets_to_process)} files",
                )

            typer.echo()

    except FileNotFoundError as e:
        typer.secho(f"❌ Missing file: {e}", fg=typer.colors.RED, err=True)
        typer.echo()
        typer.echo("💡 Tip: Ensure the following files exist:")
        typer.echo("   • pyproject.toml")
        typer.echo("   • docs/templates/[template_name].jinja")
        typer.echo("   • .cortex/context.json (run 'cortex map' first)")
        raise typer.Exit(code=1) from e

    except Exception as e:
        logger.error(f"Error generating documents: {e}", exc_info=True)
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo("CORTEX v0.1.0 - Documentation as Code")
        raise typer.Exit()


@app.callback()
def callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """CORTEX - Documentation as Code Manager.

    Manage documentation with YAML frontmatter, validate links between docs
    and code, and ensure documentation quality.
    """
    # Print banner when starting (but not for --help or --version)
    if "--help" not in sys.argv and "-h" not in sys.argv and not version:
        print_startup_banner(
            tool_name="CORTEX",
            version="0.1.0",
            description="Documentation as Code Manager",
            script_path=Path(__file__),
        )


def main() -> None:
    """Entry point for the cortex CLI."""
    with trace_context():
        app()


if __name__ == "__main__":
    with trace_context():
        app()
