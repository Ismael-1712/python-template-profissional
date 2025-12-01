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

import sys
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

# Add project root to sys.path
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.core.cortex.metadata import (  # noqa: E402
    FrontmatterParseError,
    FrontmatterParser,
)
from scripts.utils.banner import print_startup_banner  # noqa: E402
from scripts.utils.logger import setup_logging  # noqa: E402

# Configure logging
logger = setup_logging(__name__, log_file="cortex.log")

# Create Typer app
app = typer.Typer(
    name="cortex",
    help="CORTEX - Documentation as Code Manager",
    add_completion=False,
)


def _infer_doc_type(file_path: Path) -> str:
    """Infer document type from file path.

    Args:
        file_path: Path to the markdown file

    Returns:
        Inferred document type (guide, arch, reference, or history)
    """
    path_str = str(file_path).lower()

    if "architecture" in path_str or "arch" in path_str:
        return "arch"
    if "guide" in path_str or "tutorial" in path_str:
        return "guide"
    if "reference" in path_str or "api" in path_str or "ref" in path_str:
        return "reference"
    if "history" in path_str or "changelog" in path_str:
        return "history"
    # Default to guide for general documentation
    return "guide"


def _generate_id_from_filename(file_path: Path) -> str:
    """Generate a kebab-case ID from filename.

    Args:
        file_path: Path to the markdown file

    Returns:
        Kebab-case ID string
    """
    # Get filename without extension
    name = file_path.stem

    # Convert to lowercase
    name = name.lower()

    # Replace underscores and spaces with hyphens
    name = name.replace("_", "-").replace(" ", "-")

    # Remove any characters that aren't alphanumeric or hyphens
    name = "".join(c for c in name if c.isalnum() or c == "-")

    # Remove consecutive hyphens
    while "--" in name:
        name = name.replace("--", "-")

    # Remove leading/trailing hyphens
    name = name.strip("-")

    return name


def _generate_default_frontmatter(file_path: Path) -> str:
    """Generate default YAML frontmatter for a file.

    Args:
        file_path: Path to the markdown file

    Returns:
        YAML frontmatter string (including --- delimiters)
    """
    doc_id = _generate_id_from_filename(file_path)
    doc_type = _infer_doc_type(file_path)
    today = date.today().strftime("%Y-%m-%d")

    frontmatter = f"""---
id: {doc_id}
type: {doc_type}
status: draft
version: 1.0.0
author: Engineering Team
date: {today}
context_tags: []
linked_code: []
---

"""
    return frontmatter


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

        # Read existing file content
        with open(path, encoding="utf-8") as f:
            content = f.read()

        # Check if frontmatter already exists
        parser = FrontmatterParser()
        has_frontmatter = False

        try:
            # Try to parse existing frontmatter
            parser.parse_file(path)
            has_frontmatter = True
            logger.info("File already has frontmatter")

        except FrontmatterParseError:
            # No frontmatter found, this is expected
            logger.info("No existing frontmatter found")
            has_frontmatter = False

        # Handle existing frontmatter
        if has_frontmatter and not force:
            typer.secho(
                f"⚠️  File {path.name} already has YAML frontmatter.",
                fg=typer.colors.YELLOW,
            )
            typer.echo("Current frontmatter:")
            typer.echo("---")

            # Show first few lines of existing frontmatter
            lines = content.split("\n")
            if lines[0].strip() == "---":
                for _i, line in enumerate(lines[1:], 1):
                    if line.strip() == "---":
                        break
                    typer.echo(f"  {line}")
            typer.echo("---")

            if not typer.confirm(
                "\nDo you want to overwrite it? (Use --force to skip this prompt)",
            ):
                typer.secho("✋ Aborted. No changes made.", fg=typer.colors.BLUE)
                logger.info("User aborted overwrite")
                raise typer.Abort()

            logger.info("User confirmed overwrite")

        # Generate frontmatter
        frontmatter = _generate_default_frontmatter(path)

        # Remove existing frontmatter if present
        new_content = content
        if content.strip().startswith("---"):
            lines = content.split("\n")
            # Find the closing ---
            end_idx = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    end_idx = i
                    break

            if end_idx is not None:
                # Remove old frontmatter (including both --- lines)
                new_content = "\n".join(lines[end_idx + 1 :])
                # Remove leading blank lines
                new_content = new_content.lstrip("\n")

        # Add new frontmatter
        final_content = frontmatter + new_content

        # Write back to file
        with open(path, "w", encoding="utf-8") as f:
            f.write(final_content)

        typer.secho(f"✅ Success! Added frontmatter to {path}", fg=typer.colors.GREEN)
        typer.echo()
        typer.echo("Generated frontmatter:")
        typer.echo(frontmatter.rstrip())

        logger.info(f"Successfully added frontmatter to {path}")

    except typer.Abort:
        # User cancelled, exit gracefully
        raise

    except Exception as e:
        logger.error(f"Error initializing frontmatter: {e}", exc_info=True)
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
    app()


if __name__ == "__main__":
    app()
