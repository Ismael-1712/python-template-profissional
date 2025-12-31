"""Comandos de configuração e mapeamento do CORTEX.

Este módulo contém comandos relacionados à gestão de configurações
e geração de mapas de contexto do projeto.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from scripts.cortex.adapters.ui import UIPresenter
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__, log_file="cortex.log")


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
