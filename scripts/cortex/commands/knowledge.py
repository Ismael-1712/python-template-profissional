"""Comandos de Knowledge Base e Guardian do CORTEX.

Este módulo contém comandos relacionados à gestão da base de conhecimento
e validação de integridade através do Guardian Probe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from scripts.core.cortex.knowledge_orchestrator import KnowledgeOrchestrator
from scripts.core.guardian.hallucination_probe import HallucinationProbe
from scripts.cortex.adapters.ui import UIPresenter
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__, log_file="cortex.log")


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
