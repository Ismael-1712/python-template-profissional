"""Comandos Guardian do CORTEX para detectar configurações órfãs.

Este módulo contém comandos relacionados ao Guardian - sistema de detecção
de configurações não documentadas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from scripts.cortex.adapters.ui import UIPresenter
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__, log_file="cortex.log")


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
        from scripts.core.cortex.guardian_orchestrator import GuardianOrchestrator

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
