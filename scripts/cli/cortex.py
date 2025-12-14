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
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

# Add project root to sys.path
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner  # noqa: E402
from scripts.core.cortex.knowledge_sync import KnowledgeSyncer  # noqa: E402
from scripts.core.cortex.mapper import generate_context_map  # noqa: E402
from scripts.core.cortex.metadata import (  # noqa: E402
    FrontmatterParseError,
    FrontmatterParser,
)
from scripts.core.cortex.migrate import DocumentMigrator  # noqa: E402
from scripts.core.cortex.scanner import CodeLinkScanner  # noqa: E402
from scripts.core.guardian.hallucination_probe import HallucinationProbe  # noqa: E402
from scripts.core.guardian.matcher import DocumentationMatcher  # noqa: E402
from scripts.core.guardian.models import ScanResult  # noqa: E402
from scripts.core.guardian.scanner import ConfigScanner  # noqa: E402
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

            file_errors: list[str] = []
            file_warnings: list[str] = []

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
        cortex knowledge-scan              # Scan knowledge base
        cortex knowledge-scan --verbose    # Show detailed info
    """
    try:
        workspace_root = Path.cwd()
        logger.info("Scanning Knowledge Base...")

        typer.secho("\n🧠 Knowledge Base Scanner", bold=True, fg=typer.colors.CYAN)
        typer.echo(f"Workspace: {workspace_root}")
        typer.echo("Knowledge Directory: docs/knowledge/\n")

        # Instantiate scanner and scan
        scanner = KnowledgeScanner(workspace_root=workspace_root)
        entries = scanner.scan()

        # Display results
        if not entries:
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
        entry_word = "entry" if len(entries) == 1 else "entries"
        typer.secho(
            f"✅ Found {len(entries)} knowledge {entry_word}",
            fg=typer.colors.GREEN,
            bold=True,
        )
        typer.echo()

        # List entries
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

        logger.info(f"Knowledge scan completed: {len(entries)} entries found")

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

        # Step 1: Scan for knowledge entries
        scanner = KnowledgeScanner(workspace_root=workspace_root)
        all_entries = scanner.scan()

        if not all_entries:
            typer.secho(
                "⚠️  No knowledge entries found",
                fg=typer.colors.YELLOW,
            )
            typer.echo(
                "\nTip: Create knowledge entries in docs/knowledge/ "
                "with valid YAML frontmatter.",
            )
            return

        # Step 2: Filter entries if specific ID requested
        if entry_id:
            entries_to_sync = [e for e in all_entries if e.id == entry_id]
            if not entries_to_sync:
                typer.secho(
                    f"❌ Entry '{entry_id}' not found",
                    fg=typer.colors.RED,
                )
                typer.echo(
                    f"\nAvailable entries: {', '.join(e.id for e in all_entries)}",
                )
                raise typer.Exit(code=1)
        else:
            entries_to_sync = all_entries

        # Step 3: Filter entries that have sources
        entries_with_sources = [e for e in entries_to_sync if e.sources]

        if not entries_with_sources:
            if entry_id:
                typer.secho(
                    f"⚠️  Entry '{entry_id}' has no external sources",
                    fg=typer.colors.YELLOW,
                )
            else:
                typer.secho(
                    "⚠️  No entries with external sources found",
                    fg=typer.colors.YELLOW,
                )
            return

        # Step 4: Synchronize entries
        syncer = KnowledgeSyncer()
        sync_count = 0
        error_count = 0

        typer.echo(f"Processing {len(entries_with_sources)} entries...\n")

        for entry in entries_with_sources:
            # Verify file_path is available
            if not entry.file_path:
                typer.secho(
                    f"⚠️  {entry.id}: Missing file path (internal error)",
                    fg=typer.colors.YELLOW,
                )
                error_count += 1
                continue

            typer.echo(f"📄 {entry.id} ({len(entry.sources)} source(s))")

            if dry_run:
                # Dry run mode: just log what would be synced
                for source in entry.sources:
                    typer.echo(f"   Would sync: {source.url}")
                sync_count += 1
            else:
                # Real sync mode
                try:
                    updated_entry = syncer.sync_entry(entry, entry.file_path)
                    # Check if any source was updated
                    was_updated = any(
                        new.last_synced != old.last_synced
                        for old, new in zip(
                            entry.sources,
                            updated_entry.sources,
                            strict=True,
                        )
                    )
                    if was_updated:
                        typer.secho("   ✅ Synchronized", fg=typer.colors.GREEN)
                        sync_count += 1
                    else:
                        typer.echo("   ℹ️  No changes (304 Not Modified)")
                        sync_count += 1
                except Exception as e:
                    typer.secho(
                        f"   ❌ Failed: {e}",
                        fg=typer.colors.RED,
                    )
                    logger.error(
                        f"Error syncing entry {entry.id}: {e}",
                        exc_info=True,
                    )
                    error_count += 1

        # Step 5: Summary
        typer.echo()
        if dry_run:
            typer.secho(
                f"🔍 Dry run complete: {sync_count} entries would be synced",
                fg=typer.colors.BLUE,
                bold=True,
            )
        elif error_count == 0:
            typer.secho(
                f"✅ Synchronization complete: {sync_count} entries processed",
                fg=typer.colors.GREEN,
                bold=True,
            )
        else:
            typer.secho(
                f"⚠️  Synchronization complete with errors: "
                f"{sync_count} succeeded, {error_count} failed",
                fg=typer.colors.YELLOW,
                bold=True,
            )

        logger.info(
            f"Knowledge sync completed: {sync_count} succeeded, {error_count} failed",
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


# ============================================================================
# Guardian Commands - Visibility Guardian for orphaned configs
# ============================================================================

guardian_app = typer.Typer(
    name="guardian",
    help="Visibility Guardian - Detect undocumented configurations",
)
app.add_typer(guardian_app, name="guardian")


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
        typer.secho("\n🔍 Visibility Guardian - Orphan Detection", bold=True)
        typer.echo(f"Scanning: {path}")
        typer.echo(f"Documentation: {docs_path}\n")

        # Step 1: Scan código
        typer.echo("📝 Step 1: Scanning code for configurations...")
        # Passa project_root para carregar whitelist
        project_root = Path.cwd()
        scanner = ConfigScanner(project_root=project_root)

        # Determina se é arquivo ou diretório
        if path.is_file():
            # Scan de arquivo único
            try:
                findings = scanner.scan_file(path)
                scan_result = ScanResult(
                    findings=findings,
                    files_scanned=1,
                )
            except Exception as e:
                typer.secho(
                    f"❌ Error scanning file: {e}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=1) from e
        else:
            # Scan de diretório
            scan_result = scanner.scan_project(path)

        if scan_result.has_errors():
            typer.secho(
                "⚠️  Some files had errors during scanning:",
                fg=typer.colors.YELLOW,
            )
            for error in scan_result.errors:
                typer.echo(f"   • {error}")

        findings_msg = (
            f"   Found {scan_result.total_findings} configurations in "
            f"{scan_result.files_scanned} files"
        )
        typer.echo(findings_msg)

        if scan_result.total_findings == 0:
            typer.secho(
                "✅ No configurations found - nothing to check!",
                fg=typer.colors.GREEN,
            )
            return

        # Step 2: Match com documentação
        typer.echo("\n📚 Step 2: Checking documentation...")
        matcher = DocumentationMatcher(docs_path)
        orphans, documented = matcher.find_orphans(scan_result.findings)

        # Step 3: Report
        typer.echo("\n" + "=" * 70)
        typer.secho("📊 RESULTS", bold=True)
        typer.echo("=" * 70)

        if not orphans:
            typer.secho(
                "\n✅ SUCCESS: All configurations are documented!",
                fg=typer.colors.GREEN,
                bold=True,
            )
            typer.echo(f"   {len(documented)} configurations found in documentation")
        else:
            typer.secho(
                f"\n❌ ORPHANS DETECTED: {len(orphans)} undocumented configurations",
                fg=typer.colors.RED,
                bold=True,
            )
            typer.echo()

            for orphan in orphans:
                typer.secho(f"  • {orphan.key}", fg=typer.colors.RED, bold=True)
                typer.echo(f"    Location: {orphan.source_file}:{orphan.line_number}")
                if orphan.context:
                    typer.echo(f"    Context: {orphan.context}")
                if orphan.default_value:
                    typer.echo(f"    Default: {orphan.default_value}")
                typer.echo()

            if documented:
                typer.echo(f"✅ {len(documented)} configurations ARE documented:")
                for key, files in documented.items():
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
