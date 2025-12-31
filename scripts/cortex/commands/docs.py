"""Comandos de auditoria e geração de documentação do CORTEX.

Este módulo contém comandos para:
- Auditoria de metadados e links em documentação Markdown
- Geração de documentos padrão (README, CONTRIBUTING, etc.)
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from scripts.cortex.adapters.ui import UIPresenter
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__, log_file="cortex.log")


def audit(
    ctx: typer.Context,
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to audit (file or directory). Defaults to docs/",
            exists=True,
            resolve_path=True,
        ),
    ] = Path("docs"),
    fail_on_error: Annotated[
        bool,
        typer.Option(
            "--fail-on-error",
            "-f",
            help="Exit with error code if any issues are found",
        ),
    ] = False,
    links: Annotated[
        bool,
        typer.Option(
            "--links/--no-links",
            "-l",
            help="Validate Knowledge Graph links in documents (slower)",
        ),
    ] = True,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            "-s",
            help="Enable strict mode: warn on missing optional fields",
        ),
    ] = False,
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            help="Export results to JSON file (optional)",
        ),
    ] = None,
) -> None:
    """Audit Markdown files for metadata and link integrity.

    Scans documents for:
    - Valid YAML frontmatter with required fields
    - Proper link relationships (requires → provides)
    - Optional: Knowledge Graph validation (when --links is enabled)

    Examples:
        cortex audit docs/
        cortex audit docs/architecture/ --strict --fail-on-error
        cortex audit . --no-links --output results.json
    """
    try:
        from scripts.core.cortex.audit_orchestrator import AuditOrchestrator

        project_root = ctx.obj["project_root"]
        ui = UIPresenter()

        # Display audit header
        ui.display_audit_header()

        # Execute audit - use correct parameter name and method
        orchestrator = AuditOrchestrator(workspace_root=project_root)
        results = orchestrator.run_full_audit(
            path=path,
            check_links=links,
            fail_on_error=fail_on_error,
            strict=strict,
        )

        # Export results if requested
        if output and results.metadata_result:
            output_path = Path(output)
            results.metadata_result.report.export_to_json(output_path)
            ui.show_info(f"Results exported to: {output_path}")

        # Display results using existing UIPresenter method
        if results.metadata_result:
            ui.display_audit_results(results.metadata_result.report)

        # Final status check for fail-on-error
        if fail_on_error and results.should_fail:
            ui.show_error("Audit failed with errors. Exiting with code 1.")
            raise typer.Exit(code=1)

        ui.show_blank_line()

    except Exception as e:
        logger.error("Error during audit: %s", e, exc_info=True)
        ui = UIPresenter()
        ui.show_error(f"Audit error: {e}")
        raise typer.Exit(code=1) from e


def generate_docs(
    ctx: typer.Context,
    target: Annotated[
        str,
        typer.Argument(
            help=("Document type to generate: 'readme', 'contributing', or 'all'"),
        ),
    ] = "all",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help=(
                "Output directory (defaults to project root for README, "
                "docs/ for CONTRIBUTING)"
            ),
        ),
    ] = None,
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            "-c",
            help="Check mode: detect drift without regenerating",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be generated without writing files",
        ),
    ] = False,
) -> None:
    """Generate standard project documentation from templates.

    Supports generation of:
    - README.md: Project overview with auto-collected metadata
    - CONTRIBUTING.md: Contribution guidelines
    - Both documents (--all)

    Includes drift detection to compare existing vs. generated content.

    Examples:
        cortex generate readme
        cortex generate contributing --output docs/
        cortex generate all --check
        cortex generate readme --dry-run
    """
    try:
        from scripts.core.cortex.generation_orchestrator import (
            GenerationOrchestrator,
            GenerationTarget,
        )

        project_root = ctx.obj["project_root"]
        ui = UIPresenter()

        # Normalize target string to enum
        target_enum: GenerationTarget
        if target.lower() == "readme":
            target_enum = GenerationTarget.README
        elif target.lower() == "contributing":
            target_enum = GenerationTarget.CONTRIBUTING
        else:
            target_enum = GenerationTarget.ALL

        # Show processing mode
        if check:
            ui.display_generate_mode_header("CHECK")
        elif dry_run:
            ui.display_generate_mode_header("DRY-RUN")
        else:
            ui.display_generate_mode_header("GENERATE")

        # Determine output paths
        if output:
            output_dir = output
        else:
            # Default: README at root, CONTRIBUTING in docs/
            output_dir = (
                project_root
                if target_enum == GenerationTarget.README
                else project_root / "docs"
            )

        # Execute generation
        orchestrator = GenerationOrchestrator(project_root=project_root)

        targets_to_generate = []
        if target_enum == GenerationTarget.ALL:
            targets_to_generate = [
                GenerationTarget.README,
                GenerationTarget.CONTRIBUTING,
            ]
        else:
            targets_to_generate = [target_enum]

        for gen_target in targets_to_generate:
            # Show processing
            ui.display_generate_processing(target=gen_target.value, dry_run=dry_run)

            # Determine file path
            if gen_target == GenerationTarget.README:
                file_path = output_dir / "README.md"
            else:  # CONTRIBUTING
                file_path = output_dir / "CONTRIBUTING.md"

            # Check mode: detect drift only
            if check:
                drift_result = orchestrator.check_drift(target=gen_target)

                # Display drift result
                ui.display_drift_result(
                    drift_result=drift_result,
                    target_name=gen_target.value.upper(),
                )

                continue  # Skip generation in check mode

            # Dry-run mode: show preview without writing
            if dry_run:
                result = orchestrator.generate_single(
                    target=gen_target,
                    output_path=file_path,
                    dry_run=True,
                )
                ui.display_generation_result(gen_result=result, dry_run=True)
                continue  # Skip actual write

            # Normal mode: generate and write
            result = orchestrator.generate_single(
                target=gen_target,
                output_path=file_path,
                dry_run=False,
            )

            # Display result
            ui.display_generation_result(
                gen_result=result,
                dry_run=False,
            )

        # Final summary
        if not check and not dry_run:
            ui.display_generate_final_success()

        ui.show_blank_line()

    except Exception as e:
        logger.error("Error during document generation: %s", e, exc_info=True)
        ui = UIPresenter()
        ui.show_error(f"Generation error: {e}")
        raise typer.Exit(code=1) from e
