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

# Add project root to sys.path dynamically
# Note: Will be set up in the main callback to avoid global state
_script_dir = Path(__file__).resolve().parent
_project_root_for_path = _script_dir.parent.parent
if str(_project_root_for_path) not in sys.path:
    sys.path.insert(0, str(_project_root_for_path))

from scripts.core.cortex.audit_orchestrator import (  # noqa: E402
    AuditOrchestrator,
)
from scripts.core.cortex.generation_orchestrator import (  # noqa: E402
    GenerationOrchestrator,
    GenerationTarget,
)
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
from scripts.core.guardian.hallucination_probe import HallucinationProbe  # noqa: E402
from scripts.cortex.adapters.ui import UIPresenter  # noqa: E402
from scripts.cortex.core.interaction_service import InteractionService  # noqa: E402
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


@app.callback()
def setup_context(ctx: typer.Context) -> None:
    """CORTEX: Advanced Project Governance & Observability System.

    Dependency Injection: Initializes project_root in context for all commands.
    """
    # Define project root relative to this file location dynamically
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    # Store in context for dependency injection
    ctx.ensure_object(dict)
    ctx.obj["project_root"] = project_root


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
        ui = UIPresenter()
        if path.suffix.lower() not in [".md", ".markdown"]:
            ui.display_init_file_warning(path)
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
                ui.display_init_existing_frontmatter_warning(path.name)

                # Show existing frontmatter preview
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                lines = content.split("\n")
                if lines[0].strip() == "---":
                    # Extract existing frontmatter
                    existing_fm_lines = []
                    for line in lines[1:]:
                        if line.strip() == "---":
                            break
                        existing_fm_lines.append(line)
                    ui.display_init_preview(
                        existing_frontmatter="\n".join(existing_fm_lines),
                    )

                # Use InteractionService for confirmation
                InteractionService.confirm_action(
                    "\nDo you want to overwrite it? (Use --force to skip this prompt)",
                    abort_message="Aborted. No changes made.",
                )

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
            # Show the new frontmatter from result
            import yaml

            frontmatter_yaml = yaml.dump(
                result.new_frontmatter,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            ui.display_init_success(path, frontmatter_yaml)
            logger.info(f"Successfully added frontmatter to {path}")

        elif result.status == "skipped":
            ui.display_init_skip_warning(path.name)
            logger.info(f"Skipped {path} (already has frontmatter)")

        elif result.status == "error":
            ui.show_error(f"Error: {result.error}")
            logger.error(f"Error initializing {path}: {result.error}")
            raise typer.Exit(code=1)

    except typer.Abort:
        raise

    except Exception as e:
        logger.error(f"Error initializing frontmatter: {e}", exc_info=True)
        ui = UIPresenter()
        ui.show_error(f"Error: {e}")
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

        # Initialize orchestrator
        orchestrator = ProjectOrchestrator(workspace_root=workspace_root)
        ui = UIPresenter()

        # Perform migration
        summary = orchestrator.migrate_project(
            directory=path,
            dry_run=dry_run,
            force=force,
            recursive=recursive,
        )

        # Display results
        ui.display_migration_summary(summary, path, dry_run)

        if summary.errors > 0:
            logger.warning("Migration completed with %d error(s)", summary.errors)
            raise typer.Exit(code=1)

        logger.info("Migration completed successfully")

    except typer.Exit:
        # Re-raise Exit exceptions
        raise

    except Exception as e:
        logger.exception("Error during migration")
        ui = UIPresenter()
        ui.show_error(f"Migration failed: {e}")
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
        workspace_root = Path.cwd()
        ui = UIPresenter()

        # ============================================================
        # ORCHESTRATE AUDIT VIA AuditOrchestrator (Thin CLI Pattern)
        # ============================================================
        orchestrator = AuditOrchestrator(workspace_root=workspace_root)

        # Run full audit with all parameters
        result = orchestrator.run_full_audit(
            path=path,
            check_links=links,
            fail_on_error=fail_on_error,
            strict=strict,
            output_path=output,
        )

        # ============================================================
        # DISPLAY RESULTS (Interface Layer Only)
        # ============================================================

        # Display Knowledge Graph results if --links was used
        if result.knowledge_result:
            ui.display_knowledge_graph_header()
            ui.show_info("📚 Scanning Knowledge Nodes...")

            kg_result = result.knowledge_result

            ui.display_knowledge_scan_progress(
                kg_result.num_entries,
                kg_result.total_links,
            )
            ui.display_link_resolution(
                kg_result.valid_links,
                kg_result.broken_links,
            )

            # Display metrics
            ui.display_knowledge_metrics(kg_result.validation_report)

            # Show report saved message
            report_path = kg_result.output_path.relative_to(workspace_root)
            ui.show_info(f"📄 Report saved to: {report_path}")
            ui.show_blank_line()

            # Determine Knowledge Graph validation status
            if strict and kg_result.broken_links > 0:
                ui.show_error(
                    "Validation FAILED: Broken links detected (--strict mode)",
                    bold=True,
                )
                raise typer.Exit(code=1)

            if not kg_result.validation_report.is_healthy:
                ui.show_warning("Validation completed with warnings")
                if fail_on_error:
                    raise typer.Exit(code=1)
            else:
                ui.show_success("Validation PASSED", bold=True)

            # If only Knowledge Graph was requested, exit here
            if not result.metadata_result:
                return

        # Display Metadata audit results if performed
        if result.metadata_result:
            meta_result = result.metadata_result

            # Only show header if we didn't show Knowledge Graph header
            if not result.knowledge_result:
                ui.show_blank_line()
                ui.show_info(
                    f"📋 Found {len(meta_result.files_audited)} "
                    f"Markdown file(s) to audit",
                )
                ui.show_blank_line()

            ui.display_audit_results(meta_result.report)

            logger.info(
                f"Audit complete: {meta_result.report.total_errors} errors, "
                f"{meta_result.report.total_warnings} warnings",
            )

            # Exit with error code if requested and errors found
            if meta_result.should_fail:
                raise typer.Exit(code=1)

    except typer.Exit:
        # Re-raise Exit exceptions
        raise

    except FileNotFoundError as e:
        ui = UIPresenter()
        ui.show_error(f"Error: {e}")
        raise typer.Exit(code=1) from e

    except ValueError as e:
        ui = UIPresenter()
        ui.show_error(f"Error: {e}")
        raise typer.Exit(code=1) from e

    except Exception as e:
        logger.error(f"Error during audit: {e}", exc_info=True)
        ui = UIPresenter()
        ui.show_error(f"Audit failed: {e}")
        raise typer.Exit(code=1) from e


@app.command(name="setup-hooks")
def setup_hooks(ctx: typer.Context) -> None:
    """Install Git hooks to auto-regenerate context map.

    Creates Git hooks that automatically run 'cortex map' after:
    - git pull / git merge (post-merge hook)
    - git checkout (post-checkout hook)
    - git rebase / git commit --amend (post-rewrite hook)

    This ensures the AI context stays fresh after repository changes.

    Example:
        cortex setup-hooks
    """
    from scripts.core.cortex.hooks_orchestrator import (
        GitDirectoryNotFoundError,
        HookInstallationError,
        HooksOrchestrator,
    )

    # Get project_root from context
    project_root = ctx.obj["project_root"]

    logger.info("Installing Git hooks for CORTEX...")
    ui = UIPresenter()
    ui.display_hooks_installing()

    try:
        # Use HooksOrchestrator to handle all hook installation logic
        orchestrator = HooksOrchestrator(project_root=project_root)
        installed_hooks = orchestrator.install_cortex_hooks()

        # Display results
        ui.display_hooks_installation(installed_hooks)

    except GitDirectoryNotFoundError as e:
        ui.display_hooks_git_error()
        logger.error("Git directory not found in project root")
        raise typer.Exit(code=1) from e

    except HookInstallationError as e:
        ui.show_error(f"Error installing hooks: {e}")
        logger.error(f"Hook installation failed: {e}", exc_info=True)
        raise typer.Exit(code=1) from e


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

        ui = UIPresenter()
        mode = "EXPERIMENTAL PARALLEL" if parallel else "Standard Sequential"
        ui.display_scan_header(workspace_root, mode)

        # Instantiate orchestrator and scan
        orchestrator = KnowledgeOrchestrator(
            workspace_root=workspace_root,
            force_parallel=parallel,
        )
        result = orchestrator.scan(verbose=verbose)

        # Display results
        if not result.entries:
            ui.display_scan_empty_warning()
            return

        # Success summary
        ui.display_scan_success(result.total_count)

        # List entries using UIPresenter
        ui.display_knowledge_entries(result.entries, verbose=verbose)

        logger.info(f"Knowledge scan completed: {result.total_count} entries found")

    except Exception as e:
        logger.error(f"Error scanning knowledge base: {e}", exc_info=True)
        ui = UIPresenter()
        ui.show_error(f"Error: {e}")
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

        # Use orchestrator to handle scan, filter, and sync logic
        orchestrator = KnowledgeOrchestrator(workspace_root=workspace_root)
        summary = orchestrator.sync_multiple(entry_id=entry_id, dry_run=dry_run)

        # Display results
        ui = UIPresenter()
        ui.display_sync_summary(summary, entry_id, dry_run)

        logger.info(
            f"Knowledge sync completed: "
            f"{summary.successful_count} succeeded, {summary.error_count} failed",
        )

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error during knowledge sync: {e}", exc_info=True)
        ui = UIPresenter()
        ui.show_error(f"Error: {e}")
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

        # Initialize and run probe
        probe = HallucinationProbe(
            workspace_root=workspace_root,
            canary_id=canary_id,
        )

        # Get result and display
        ui = UIPresenter()

        if verbose:
            # Detailed validation mode
            result = probe.run()
            ui.display_probe_result(result, canary_id, verbose=True)

            if not result.passed:
                logger.error(f"Hallucination probe failed: {result.message}")
                raise typer.Exit(code=1)
        else:
            # Simple boolean check mode
            simple_result = probe.run()
            ui.display_probe_result(simple_result, canary_id, verbose=False)

            if not simple_result.passed:
                logger.error(f"Hallucination probe failed for canary: {canary_id}")
                raise typer.Exit(code=1)

        logger.info("Hallucination probe completed successfully")

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error during hallucination probe: {e}", exc_info=True)
        ui = UIPresenter()
        ui.show_error(f"Error: {e}")
        raise typer.Exit(code=1) from e


@app.command(name="config")
def config_manager(
    ctx: typer.Context,
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
    from scripts.core.cortex.config_orchestrator import (
        ConfigLoadError,
        ConfigOrchestrator,
        ConfigValidationError,
    )

    # Get project_root from context
    project_root = ctx.obj["project_root"]

    try:
        # Resolve path relative to project root
        config_path = project_root / path if not path.is_absolute() else path

        ui = UIPresenter()
        if not config_path.exists():
            ui.show_error(f"Configuration file not found: {config_path}")
            raise typer.Exit(code=1)

        # Use ConfigOrchestrator to load and validate configuration
        logger.info(f"Reading configuration from: {config_path}")
        orchestrator = ConfigOrchestrator(project_root=project_root)

        # Validate YAML syntax and required keys
        if validate:
            ui.show_info("🔍 Validating configuration file...")
            try:
                required_keys = ["scan_paths", "file_patterns", "exclude_paths"]
                config_data = orchestrator.load_config_with_defaults(
                    config_path,
                    required_keys,
                )
                ui.display_validation_success()
            except ConfigValidationError as e:
                ui.show_error(f"Validation failed: {e}")
                raise typer.Exit(code=1) from e

        # Display configuration
        if show:
            # Load config without validation for display
            config_data = orchestrator.load_yaml(config_path)

            if config_data is None:
                ui.show_warning("Configuration file is empty")
                raise typer.Exit(code=1)

            ui.display_config(config_data, config_path)

        # If neither show nor validate, display help
        if not show and not validate:
            ui.display_config_hints()

    except ConfigLoadError as e:
        logger.error(f"Configuration load error: {e}", exc_info=True)
        ui.show_error(f"Error loading configuration: {e}")
        raise typer.Exit(code=1) from e
    except OSError as e:
        logger.error(f"File error: {e}", exc_info=True)
        ui.show_error(f"Error reading file: {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        logger.error(f"Error managing configuration: {e}", exc_info=True)
        ui.show_error(f"Error: {e}")
        raise typer.Exit(code=1) from e


@app.command(name="map")
def project_map(
    ctx: typer.Context,
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
        from scripts.cortex.core.context_mapper import ContextMapper

        # Get project_root from context
        project_root = ctx.obj["project_root"]

        logger.info("Generating project context map...")
        ui = UIPresenter()

        if verbose:
            ui.show_info("🔍 Scanning project structure...")
            if include_knowledge:
                ui.show_info("🧠 Including Knowledge Node rules...")

        # Generate context map
        mapper = ContextMapper(project_root=project_root)

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
                    f"Template not found: {template.relative_to(project_root)}",
                )
                ui.show_info("   Skipping configuration sync.")
                return

            ui.display_config_sync_header()
            template = mapper.get_template_path(template_path)
            target = project_root / "pyproject.toml"
            ui.display_config_sync_template_info(template, target, project_root)

            ui.display_config_sync_result(result.config_sync_result, project_root)

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
        ui = UIPresenter()
        ui.show_error(f"Error: {e}")
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

        ui = UIPresenter()
        ui.display_guardian_header(path, docs_path)

        # Execute orphan detection
        orchestrator = GuardianOrchestrator()
        result = orchestrator.check_orphans(scan_path=path, docs_path=docs_path)

        # Display scan errors if any
        if result.scan_errors:
            ui.display_guardian_scan_errors(result.scan_errors)

        # Display findings
        ui.display_guardian_findings(result.total_findings, result.files_scanned)

        if result.total_findings == 0:
            ui.display_guardian_no_configs()
            return

        # Display results
        ui.display_guardian_results_header()

        if not result.has_orphans:
            ui.display_guardian_success(len(result.documented))
        else:
            ui.display_guardian_orphans_header(len(result.orphans))

            # Display orphans using UIPresenter
            ui.display_guardian_orphans(result.orphans, result.documented)

            if fail_on_error:
                ui.display_guardian_fail_exit()
                raise typer.Exit(code=1)

        ui.show_blank_line()

    except Exception as e:
        logger.error("Error during guardian check: %s", e, exc_info=True)
        ui = UIPresenter()
        ui.show_error(f"Error: {e}")
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
            # Validate CLI arguments
            ui = UIPresenter()
            ui.validate_generate_args(target, output, check, dry_run)

            # Initialize orchestrator
            orchestrator = GenerationOrchestrator()

            # Map target string to enum
            target_enum_map = {
                "readme": GenerationTarget.README,
                "contributing": GenerationTarget.CONTRIBUTING,
                "all": GenerationTarget.ALL,
            }
            target_enum = target_enum_map[target]

            # Print header
            mode = "CHECK MODE" if check else "GENERATION MODE"
            ui.display_generate_mode_header(mode)

            # === DRIFT CHECK MODE ===
            if check:
                if target == "all":
                    drift_results = orchestrator.check_batch_drift()

                    for drift_result in drift_results:
                        ui.display_drift_result(
                            drift_result,
                            drift_result.target.upper(),
                        )

                    has_drift = any(r.has_drift for r in drift_results)

                    if has_drift:
                        ui.display_generate_drift_fix_hint(target)
                        logger.warning("Drift detected in generated documents")
                        raise typer.Exit(code=1)

                    ui.show_success("All documents are in sync!", bold=True)
                else:
                    drift_result = orchestrator.check_drift(target_enum)
                    ui.display_drift_result(
                        drift_result,
                        drift_result.output_path.name,
                    )

                    if drift_result.has_drift:
                        ui.display_generate_drift_fix_hint(target)
                        logger.warning(f"Drift detected in {target}")
                        raise typer.Exit(code=1)

                    ui.show_success(
                        f"{drift_result.output_path.name} is in sync",
                        bold=True,
                    )

            # === GENERATION MODE ===
            elif target == "all":
                batch_result = orchestrator.generate_batch(dry_run=dry_run)

                for gen_result in batch_result.results:
                    ui.display_generation_result(gen_result, dry_run)

                ui.display_generate_batch_summary(
                    batch_result.success,
                    batch_result.success_count,
                    batch_result.error_count,
                    batch_result.total_bytes,
                    dry_run,
                )

                if not batch_result.success:
                    raise typer.Exit(code=1)

            else:
                # Generate single document
                gen_result = orchestrator.generate_single(
                    target=target_enum,
                    output_path=output,
                    dry_run=dry_run,
                )

                ui.display_generate_processing(target, dry_run)

                if gen_result.success:
                    if dry_run:
                        ui.display_generate_dry_run_preview(gen_result.content)
                        ui.display_generate_dry_run_result(
                            gen_result.output_path,
                            gen_result.content_size,
                        )
                    else:
                        ui.display_generate_success_single(
                            gen_result.output_path,
                            gen_result.content_size,
                            gen_result.template_name,
                        )

                    ui.display_generate_final_success()
                else:
                    ui.show_error(
                        f"Generation failed: {gen_result.error_message}",
                        bold=True,
                    )
                    raise typer.Exit(code=1)

            ui.show_blank_line()

    except typer.Exit:
        raise

    except FileNotFoundError as e:
        ui = UIPresenter()
        ui.show_error(f"Missing file: {e}")
        ui.display_generate_missing_file_tips()
        raise typer.Exit(code=1) from e

    except Exception as e:
        logger.exception("Error generating documents")
        ui = UIPresenter()
        ui.show_error(f"Error: {e}")
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
