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

from scripts.core.cortex.mapper import generate_context_map  # noqa: E402
from scripts.core.cortex.metadata import (  # noqa: E402
    FrontmatterParseError,
    FrontmatterParser,
)
from scripts.core.cortex.migrate import DocumentMigrator  # noqa: E402
from scripts.core.cortex.scanner import CodeLinkScanner  # noqa: E402
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

        # Initialize migrator
        migrator = DocumentMigrator(workspace_root=workspace_root)

        # Perform migration
        typer.echo(f"📂 Scanning {path} for Markdown files...\n")

        results = migrator.migrate_directory(
            directory=path,
            dry_run=dry_run,
            force=force,
            recursive=recursive,
        )

        # Print summary
        migrator.print_summary(results, dry_run=dry_run)

        # Count results
        created = sum(1 for r in results if r.action == "created")
        updated = sum(1 for r in results if r.action == "updated")
        errors = sum(1 for r in results if r.action == "error")

        # Provide next steps
        if dry_run and (created + updated > 0):
            typer.echo("\n" + "=" * 70)
            typer.secho(
                "\n💡 To apply these changes, run:\n",
                fg=typer.colors.CYAN,
                bold=True,
            )
            typer.secho(f"   cortex migrate {path} --apply", fg=typer.colors.WHITE)
            typer.echo()

        if errors > 0:
            logger.warning("Migration completed with %d error(s)", errors)
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
) -> None:
    """Audit documentation files for metadata and link integrity.

    Scans Markdown files to verify:
    - Valid YAML frontmatter
    - Required metadata fields
    - Links to code files exist
    - Links to other docs exist

    Examples:
        cortex audit                    # Audit all docs in docs/
        cortex audit docs/guides/       # Audit specific directory
        cortex audit docs/guide.md      # Audit single file
        cortex audit --fail-on-error    # Exit 1 if errors found (CI mode)
    """
    try:
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

        # Initialize parser and scanner
        parser = FrontmatterParser()
        scanner = CodeLinkScanner(workspace_root=workspace_root)

        # ============================================================
        # ROOT LOCKDOWN: Check for unauthorized .md files in root
        # ============================================================
        typer.echo("🔒 Checking Root Lockdown policy...")
        root_violations = scanner.check_root_markdown_files()

        if root_violations:
            typer.secho(
                f"  ❌ {len(root_violations)} violation(s):",
                fg=typer.colors.RED,
            )
            for violation in root_violations:
                typer.secho(f"     • {violation}", fg=typer.colors.RED)
            typer.echo()
        else:
            typer.secho("  ✅ Root Lockdown: OK", fg=typer.colors.GREEN)
            typer.echo()

        # Track errors and warnings
        total_errors = len(root_violations)  # Start with root violations
        total_warnings = 0
        files_with_errors = []

        # Add root violations to error tracking
        if root_violations:
            files_with_errors.append(Path("PROJECT_ROOT"))

        # Audit each file
        for md_file in md_files:
            relative_path = md_file.relative_to(workspace_root)
            typer.echo(f"🔍 Auditing {relative_path}...")

            file_errors = []
            file_warnings = []

            # 1. Parse and validate frontmatter
            try:
                # parse_file already validates and returns DocumentMetadata
                metadata = parser.parse_file(md_file)
                # No errors if we got here

            except (FrontmatterParseError, ValueError, TypeError) as e:
                file_errors.append(f"Frontmatter error: {e}")
                metadata = None

            # 2. Check code and documentation links
            if metadata:
                link_result = scanner.check_all_links(
                    linked_code=metadata.linked_code or [],
                    related_docs=metadata.related_docs or [],
                    doc_file=md_file,
                    metadata=metadata,
                )

                if link_result.broken_code_links:
                    file_errors.extend(link_result.broken_code_links)

                if link_result.broken_doc_links:
                    file_errors.extend(link_result.broken_doc_links)

            # Report results for this file
            if file_errors:
                typer.secho(f"  ❌ {len(file_errors)} error(s):", fg=typer.colors.RED)
                for error in file_errors:
                    typer.secho(f"     • {error}", fg=typer.colors.RED)
                files_with_errors.append(relative_path)
                total_errors += len(file_errors)

            if file_warnings:
                typer.secho(
                    f"  ⚠️  {len(file_warnings)} warning(s):",
                    fg=typer.colors.YELLOW,
                )
                for warning in file_warnings:
                    typer.secho(f"     • {warning}", fg=typer.colors.YELLOW)
                total_warnings += len(file_warnings)

            if not file_errors and not file_warnings:
                typer.secho("  ✅ No issues found", fg=typer.colors.GREEN)

            typer.echo()  # Blank line between files

        # Print summary
        typer.echo("=" * 70)
        typer.echo("\n📊 Audit Summary\n")
        typer.echo(f"Files scanned: {len(md_files)}")

        if total_errors > 0:
            typer.secho(
                f"Total errors: {total_errors} (in {len(files_with_errors)} file(s))",
                fg=typer.colors.RED,
            )

        if total_warnings > 0:
            typer.secho(f"Total warnings: {total_warnings}", fg=typer.colors.YELLOW)

        if total_errors == 0 and total_warnings == 0:
            typer.secho("\n✅ All checks passed!", fg=typer.colors.GREEN, bold=True)
        elif total_errors == 0:
            typer.secho(
                "\n✅ No errors found (only warnings)",
                fg=typer.colors.GREEN,
            )
        else:
            msg = (
                f"\n❌ Found {total_errors} error(s) in "
                f"{len(files_with_errors)} file(s)"
            )
            typer.secho(msg, fg=typer.colors.RED, bold=True)

        logger.info(
            f"Audit complete: {total_errors} errors, {total_warnings} warnings",
        )

        # Exit with error code if requested and errors found
        if fail_on_error and total_errors > 0:
            raise typer.Exit(code=1)

    except typer.Exit:
        # Re-raise Exit exceptions
        raise

    except Exception as e:
        logger.error(f"Error during audit: {e}", exc_info=True)
        typer.secho(f"❌ Audit failed: {e}", fg=typer.colors.RED, err=True)
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
) -> None:
    """Generate project context map for introspection.

    Scans the project structure and generates a comprehensive context map
    containing information about CLI commands, documentation, dependencies,
    and architecture. This map can be used by LLMs or automation tools.

    The output is saved to .cortex/context.json by default.

    Example:
        cortex map                          # Generate context map
        cortex map --verbose               # Show detailed information
        cortex map -o custom/path.json     # Custom output location
    """
    try:
        logger.info("Generating project context map...")

        if verbose:
            typer.echo("🔍 Scanning project structure...")

        # Generate context map
        project_root = _project_root
        context = generate_context_map(project_root, output)

        # Display summary
        typer.secho("✓ Context map generated successfully!", fg=typer.colors.GREEN)
        typer.echo(f"📍 Output: {output}")
        typer.echo()
        typer.echo(f"📦 Project: {context.project_name} v{context.version}")
        typer.echo(f"🐍 Python: {context.python_version}")
        typer.echo(f"🔧 CLI Commands: {len(context.cli_commands)}")
        typer.echo(f"📄 Documents: {len(context.documents)}")
        typer.echo(f"🏗️  Architecture Docs: {len(context.architecture_docs)}")
        typer.echo(f"📦 Dependencies: {len(context.dependencies)}")
        typer.echo(f"🛠️  Dev Dependencies: {len(context.dev_dependencies)}")

        if verbose:
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

        logger.info(f"Context map saved to {output}")

    except Exception as e:
        logger.error(f"Error generating context map: {e}", exc_info=True)
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
