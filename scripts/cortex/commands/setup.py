"""Comandos de setup e inicialização do CORTEX.

Este módulo contém comandos relacionados à configuração inicial e
preparação do ambiente do CORTEX.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from scripts.core.cortex.metadata import (
    FrontmatterParseError,
    FrontmatterParser,
)
from scripts.core.cortex.project_orchestrator import ProjectOrchestrator
from scripts.cortex.adapters.ui import UIPresenter
from scripts.cortex.core.interaction_service import InteractionService
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__, log_file="cortex.log")

# Create sub-app for setup commands
app = typer.Typer(
    name="setup",
    help="Comandos de inicialização e configuração do CORTEX",
)


@app.command()
def init(
    ctx: typer.Context,
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
    ctx: typer.Context,
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
