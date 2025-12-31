#!/usr/bin/env python3
"""CORTEX - Documentation as Code CLI.

Command-line interface for managing documentation metadata and frontmatter
using the CORTEX system.

Usage:
    cortex init <file>              # Add frontmatter to a markdown file
    cortex map                      # Generate project context map
    cortex audit docs/              # Audit documentation integrity
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

# Import command sub-modules (atomized by domain)
from scripts.cortex.commands import config as config_commands  # noqa: E402
from scripts.cortex.commands import docs as docs_commands  # noqa: E402
from scripts.cortex.commands import guardian as guardian_commands  # noqa: E402
from scripts.cortex.commands import knowledge as knowledge_commands  # noqa: E402
from scripts.cortex.commands import setup as setup_commands  # noqa: E402
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


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo("CORTEX v0.1.0 - Documentation as Code")
        raise typer.Exit()


@app.callback()
def setup_context(
    ctx: typer.Context,
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
    """CORTEX: Advanced Project Governance & Observability System.

    Dependency Injection: Initializes project_root in context for all commands.

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

    # Define project root relative to this file location dynamically
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    # Store in context for dependency injection
    ctx.ensure_object(dict)
    ctx.obj["project_root"] = project_root


# Register setup commands (init, migrate, setup-hooks)
app.command()(setup_commands.init)
app.command()(setup_commands.migrate)
app.command(name="setup-hooks")(setup_commands.setup_hooks)

# Register config commands (config, map)
app.command(name="config")(config_commands.config_manager)
app.command(name="map")(config_commands.project_map)

# Register knowledge commands (knowledge-scan, knowledge-sync, guardian-probe)
app.command(name="knowledge-scan")(knowledge_commands.knowledge_scan)
app.command(name="knowledge-sync")(knowledge_commands.knowledge_sync)
app.command(name="guardian-probe")(knowledge_commands.guardian_probe)

# Register docs commands (audit, generate)
app.command(name="audit")(docs_commands.audit)
app.command(name="generate")(docs_commands.generate_docs)

# Register guardian commands (guardian check)
app.command(name="guardian-check")(guardian_commands.guardian_check)


def main() -> None:
    """Entry point for the cortex CLI."""
    with trace_context():
        app()


if __name__ == "__main__":
    with trace_context():
        app()
