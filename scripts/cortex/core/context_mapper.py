"""Context Mapper - Generates project introspection context.

This module contains the business logic for mapping the project structure,
generating context maps, and synchronizing configuration files.

Extracted from cli.py as part of Iteration 4: God Function Elimination.

Architecture: Core Domain Logic (Hexagonal Architecture)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.core.cortex.mapper import (
    ProjectContext,
    generate_context_map,
)
from scripts.utils.toml_merger import MergeResult, MergeStrategy, merge_toml


@dataclass(frozen=True)
class MappingResult:
    """Result of project context mapping operation."""

    context: ProjectContext
    """The generated project context."""

    config_sync_result: MergeResult | None = None
    """Optional result of configuration synchronization."""

    @property
    def is_successful(self) -> bool:
        """Check if mapping was successful."""
        return self.context is not None

    @property
    def config_sync_successful(self) -> bool:
        """Check if config sync was successful (if performed)."""
        if self.config_sync_result is None:
            return True  # Not performed, so no failure
        return self.config_sync_result.success


class ContextMapper:
    """Maps project structure and generates introspection context.

    This class encapsulates the business logic for:
    - Scanning project structure (CLI commands, docs, dependencies)
    - Generating context maps for LLM introspection
    - Synchronizing configuration files from templates

    Usage:
        mapper = ContextMapper(project_root=Path.cwd())
        result = mapper.map_project(
            output=Path(".cortex/context.json"),
            include_knowledge=True,
        )

        if result.is_successful:
            print(f"Mapped {result.context.project_name}")
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the context mapper.

        Args:
            project_root: Root directory of the project.
        """
        self.project_root = project_root

    def map_project(
        self,
        output: Path,
        include_knowledge: bool = True,
    ) -> MappingResult:
        """Generate project context map.

        This is the main entry point for context mapping.

        Args:
            output: Path where to save the context JSON.
            include_knowledge: Whether to include Knowledge Node golden paths.

        Returns:
            MappingResult containing the project context.

        Raises:
            ValueError: If mapping fails.
            FileNotFoundError: If required directories don't exist.
        """
        context = generate_context_map(
            self.project_root,
            output,
            include_knowledge=include_knowledge,
        )

        return MappingResult(context=context)

    def map_and_sync_config(
        self,
        output: Path,
        include_knowledge: bool = True,
        template_path: Path | None = None,
    ) -> MappingResult:
        """Generate context map and synchronize configuration from template.

        Args:
            output: Path where to save the context JSON.
            include_knowledge: Whether to include Knowledge Node golden paths.
            template_path: Path to template TOML file
                (default: project_root/templates/pyproject.toml).

        Returns:
            MappingResult with both context and config sync result.
        """
        # First, generate context map
        context = generate_context_map(
            self.project_root,
            output,
            include_knowledge=include_knowledge,
        )

        # Then, sync configuration
        template = template_path or (self.project_root / "templates/pyproject.toml")
        target = self.project_root / "pyproject.toml"

        if not template.exists():
            # Return result without config sync (template not found)
            return MappingResult(context=context, config_sync_result=None)

        # Perform merge
        merge_result = merge_toml(
            source_path=template,
            target_path=target,
            strategy=MergeStrategy.SMART,
            dry_run=False,
            backup=True,
        )

        return MappingResult(
            context=context,
            config_sync_result=merge_result,
        )

    def get_template_path(self, custom_template: Path | None = None) -> Path:
        """Get the template path, with fallback to default.

        Args:
            custom_template: Optional custom template path.

        Returns:
            Path to the template file.
        """
        return custom_template or (self.project_root / "templates/pyproject.toml")
