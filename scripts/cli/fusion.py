#!/usr/bin/env python3
"""TOML Fusion CLI - Fusionista de TOML.

Command-line interface for merging TOML files while preserving
comments, formatting, and user customizations.

Usage:
    toml-fusion template.toml target.toml                # Merge files
    toml-fusion template.toml target.toml --dry-run      # Preview changes
    toml-fusion template.toml target.toml --strategy=template  # Force template
    toml-fusion --help                                   # Show help

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

from scripts.utils.banner import print_startup_banner  # noqa: E402
from scripts.utils.logger import setup_logging  # noqa: E402
from scripts.utils.toml_merger import (  # noqa: E402
    MergeResult,
    MergeStrategy,
    merge_toml,
)

# Configure logging
logger = setup_logging(__name__, log_file="toml_fusion.log")

# Create Typer app
app = typer.Typer(
    name="toml-fusion",
    help="TOML Fusion - Intelligent TOML file merger",
    add_completion=False,
)


# ======================================================================
# CLI COMMANDS
# ======================================================================
@app.command()
def main(
    source: Annotated[
        Path,
        typer.Argument(
            help="Source TOML file (template to merge from)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    target: Annotated[
        Path,
        typer.Argument(
            help="Target TOML file (project file to merge into)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            writable=True,
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (defaults to target file)",
        ),
    ] = None,
    strategy: Annotated[
        str,
        typer.Option(
            "--strategy",
            "-s",
            help="Merge strategy: smart (default), template, user",
        ),
    ] = "smart",
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Preview changes without modifying files",
        ),
    ] = False,
    no_backup: Annotated[
        bool,
        typer.Option(
            "--no-backup",
            help="Skip backup creation (not recommended)",
        ),
    ] = False,
) -> int:
    """Merge TOML files intelligently while preserving comments.

    This tool merges a source TOML file (template) into a target TOML file
    (project) while preserving:

    - Comments (both section and inline)
    - Formatting (indentation, quote styles)
    - User customizations

    Merge Strategies:

    - smart (default): Union lists, recursive merge dicts
    - template: Template values overwrite user values
    - user: User values take priority (template fills gaps)

    Examples:
        # Preview merge (dry run)
        $ toml-fusion template/pyproject.toml pyproject.toml --dry-run

        # Merge with backup
        $ toml-fusion template/pyproject.toml pyproject.toml

        # Force template values
        $ toml-fusion template/pyproject.toml pyproject.toml --strategy=template

        # Merge to different output file
        $ toml-fusion template/pyproject.toml pyproject.toml -o merged.toml
    """
    print_startup_banner(
        tool_name="TOML Fusion",
        version="1.0.0",
        description="Intelligent TOML File Merger",
        script_path=Path(__file__),
    )

    logger.info(
        "Starting TOML merge",
        extra={
            "source": str(source),
            "target": str(target),
            "strategy": strategy,
            "dry_run": dry_run,
        },
    )

    # Validate strategy
    try:
        merge_strategy = MergeStrategy(strategy.lower())
    except ValueError:
        typer.secho(
            f"❌ Invalid strategy: {strategy}",
            fg=typer.colors.RED,
            err=True,
        )
        typer.secho(
            "   Valid strategies: smart, template, user",
            fg=typer.colors.YELLOW,
            err=True,
        )
        return 1

    # Perform merge
    typer.echo(f"\n📄 Source: {source}")
    typer.echo(f"📄 Target: {target}")
    typer.echo(f"🎯 Strategy: {merge_strategy.value}")

    if dry_run:
        typer.secho(
            "\n🔍 DRY RUN MODE - No files will be modified",
            fg=typer.colors.CYAN,
        )

    result: MergeResult = merge_toml(
        source_path=source,
        target_path=target,
        output_path=output,
        strategy=merge_strategy,
        dry_run=dry_run,
        backup=not no_backup,
    )

    # Handle result
    if not result.success:
        typer.secho("\n❌ Merge failed!", fg=typer.colors.RED, err=True)
        for conflict in result.conflicts:
            typer.secho(f"   • {conflict}", fg=typer.colors.YELLOW, err=True)

        logger.error(
            "Merge failed",
            extra={"conflicts": result.conflicts},
        )
        return 1

    # Success!
    if dry_run:
        typer.secho("\n✅ Dry run completed successfully!", fg=typer.colors.GREEN)

        if result.diff:
            typer.echo("\n📊 Preview of changes:")
            typer.echo("─" * 70)
            _print_colored_diff(result.diff)
            typer.echo("─" * 70)
        else:
            typer.secho("   No changes detected.", fg=typer.colors.CYAN)

    else:
        typer.secho("\n✅ Merge completed successfully!", fg=typer.colors.GREEN)

        output_file = output or target
        typer.echo(f"   Output: {output_file}")

        if result.backup_path:
            typer.secho(
                f"   Backup: {result.backup_path}",
                fg=typer.colors.CYAN,
            )

    logger.info(
        "Merge completed",
        extra={
            "success": result.success,
            "backup_path": str(result.backup_path) if result.backup_path else None,
        },
    )

    return 0


def _print_colored_diff(diff: str) -> None:
    """Print diff with colored syntax.

    Args:
        diff: Unified diff string
    """
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            # Added line - green
            typer.secho(line, fg=typer.colors.GREEN)
        elif line.startswith("-") and not line.startswith("---"):
            # Removed line - red
            typer.secho(line, fg=typer.colors.RED)
        elif line.startswith("@@"):
            # Hunk header - cyan
            typer.secho(line, fg=typer.colors.CYAN)
        else:
            # Context line - default
            typer.echo(line)


# ======================================================================
# ENTRY POINT
# ======================================================================
if __name__ == "__main__":
    try:
        sys.exit(app())
    except KeyboardInterrupt:
        typer.secho("\n\n⚠️  Operation cancelled by user", fg=typer.colors.YELLOW)
        sys.exit(130)
    except Exception as e:
        typer.secho(f"\n\n❌ Unexpected error: {e}", fg=typer.colors.RED, err=True)
        logger.exception("Unexpected error in CLI")
        sys.exit(1)
