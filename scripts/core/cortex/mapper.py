#!/usr/bin/env python3
"""CORTEX Mapper - Project Introspection.

This module provides introspection capabilities for the project,
generating a comprehensive context map that can be consumed by LLMs
or other automation tools.

The mapper scans:
- CLI commands available in scripts/cli/
- Documentation in docs/
- Project configuration (pyproject.toml)
- Architecture documents

Author: Engineering Team
License: MIT
"""

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Compatibilidade com Python 3.10 (tomllib disponível apenas em 3.11+)
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

# Add project root to sys.path
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.utils.logger import setup_logging  # noqa: E402

logger = setup_logging(__name__, log_file="cortex_mapper.log")


@dataclass
class CLICommand:
    """Represents a CLI command available in the project."""

    name: str
    script_path: str
    description: str = ""


@dataclass
class Document:
    """Represents a documentation file."""

    path: str
    title: str = ""
    category: str = ""
    has_frontmatter: bool = False


@dataclass
class ProjectContext:
    """Complete project context for introspection."""

    project_name: str
    version: str
    description: str
    python_version: str
    cli_commands: list[CLICommand] = field(default_factory=list)
    documents: list[Document] = field(default_factory=list)
    architecture_docs: list[Document] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)
    scripts_available: dict[str, str] = field(default_factory=dict)


class ProjectMapper:
    """Maps the project structure and generates context."""

    def __init__(self, project_root: Path) -> None:
        """Initialize the mapper.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.pyproject_path = project_root / "pyproject.toml"
        self.docs_path = project_root / "docs"
        self.scripts_cli_path = project_root / "scripts" / "cli"

    def map_project(self) -> ProjectContext:
        """Generate a complete project context map.

        Returns:
            ProjectContext with all discovered information
        """
        logger.info("Starting project mapping...")

        # Load pyproject.toml
        config = self._load_pyproject()

        # Create base context
        context = ProjectContext(
            project_name=config.get("project", {}).get("name", "unknown"),
            version=config.get("project", {}).get("version", "0.0.0"),
            description=config.get("project", {}).get("description", ""),
            python_version=config.get("project", {}).get("requires-python", ">=3.10"),
            dependencies=config.get("project", {}).get("dependencies", []),
            dev_dependencies=config.get("project", {})
            .get("optional-dependencies", {})
            .get("dev", []),
            scripts_available=config.get("project", {}).get("scripts", {}),
        )

        # Scan CLI commands
        context.cli_commands = self._scan_cli_commands()

        # Scan documentation
        context.documents = self._scan_documents()

        # Scan architecture documents
        context.architecture_docs = self._scan_architecture()

        logger.info(
            f"Project mapping complete. Found {len(context.cli_commands)} CLI commands",
        )
        logger.info(f"Found {len(context.documents)} documents")
        logger.info(f"Found {len(context.architecture_docs)} architecture documents")

        return context

    def _load_pyproject(self) -> dict[str, Any]:
        """Load and parse pyproject.toml.

        Returns:
            Parsed TOML configuration
        """
        if not self.pyproject_path.exists():
            logger.warning("pyproject.toml not found")
            return {}

        try:
            with open(self.pyproject_path, "rb") as f:
                result: dict[str, Any] = tomllib.load(f)
                return result
        except Exception as e:
            logger.error(f"Failed to parse pyproject.toml: {e}")
            return {}

    def _scan_cli_commands(self) -> list[CLICommand]:
        """Scan scripts/cli/ directory for CLI commands.

        Returns:
            List of discovered CLI commands
        """
        commands: list[CLICommand] = []

        if not self.scripts_cli_path.exists():
            logger.warning(f"CLI directory not found: {self.scripts_cli_path}")
            return commands

        for script_file in self.scripts_cli_path.glob("*.py"):
            if script_file.name.startswith("_"):
                continue

            # Try to extract description from docstring
            description = self._extract_module_docstring(script_file)

            commands.append(
                CLICommand(
                    name=script_file.stem,
                    script_path=str(script_file.relative_to(self.project_root)),
                    description=description,
                ),
            )

        return sorted(commands, key=lambda x: x.name)

    def _scan_documents(self) -> list[Document]:
        """Scan docs/ directory for documentation files.

        Returns:
            List of discovered documents
        """
        documents: list[Document] = []

        if not self.docs_path.exists():
            logger.warning(f"Docs directory not found: {self.docs_path}")
            return documents

        for doc_file in self.docs_path.rglob("*.md"):
            # Skip architecture docs (handled separately)
            if "architecture" in doc_file.parts:
                continue

            rel_path = str(doc_file.relative_to(self.project_root))
            title = self._extract_title(doc_file)

            category = (
                doc_file.parent.name if doc_file.parent != self.docs_path else "root"
            )
            documents.append(
                Document(
                    path=rel_path,
                    title=title,
                    category=category,
                ),
            )

        return sorted(documents, key=lambda x: x.path)

    def _scan_architecture(self) -> list[Document]:
        """Scan docs/architecture/ for architecture documents.

        Returns:
            List of architecture documents
        """
        documents: list[Document] = []
        arch_path = self.docs_path / "architecture"

        if not arch_path.exists():
            logger.warning("Architecture directory not found")
            return documents

        for doc_file in arch_path.glob("*.md"):
            rel_path = str(doc_file.relative_to(self.project_root))
            title = self._extract_title(doc_file)

            documents.append(
                Document(
                    path=rel_path,
                    title=title,
                    category="architecture",
                ),
            )

        return sorted(documents, key=lambda x: x.path)

    def _extract_module_docstring(self, file_path: Path) -> str:
        """Extract the module-level docstring from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            First line of module docstring or empty string
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
                in_docstring = False
                for line in lines[:20]:  # Only check first 20 lines
                    if '"""' in line or "'''" in line:
                        if in_docstring:
                            cleaned = line.strip()
                            for delim in ['"""', "'''"]:
                                cleaned = cleaned.replace(delim, "")
                            return cleaned.strip()
                        in_docstring = True
                        # Check if single-line docstring
                        if line.count('"""') == 2 or line.count("'''") == 2:
                            cleaned = line.strip()
                            for delim in ['"""', "'''"]:
                                cleaned = cleaned.replace(delim, "")
                            return cleaned.strip()
        except Exception as e:
            logger.debug(f"Could not extract docstring from {file_path}: {e}")

        return ""

    def _extract_title(self, file_path: Path) -> str:
        """Extract title from markdown file (first # heading).

        Args:
            file_path: Path to markdown file

        Returns:
            Title or filename if not found
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# "):
                        return line[2:].strip()
        except Exception as e:
            logger.debug(f"Could not extract title from {file_path}: {e}")

        return file_path.stem

    def save_context(self, context: ProjectContext, output_path: Path) -> None:
        """Save context to JSON file.

        Args:
            context: Project context to save
            output_path: Path to output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(context), f, indent=2, ensure_ascii=False)

        logger.info(f"Context saved to {output_path}")


def generate_context_map(project_root: Path, output_path: Path) -> ProjectContext:
    """Generate and save project context map.

    Args:
        project_root: Root directory of the project
        output_path: Path to save JSON output

    Returns:
        Generated ProjectContext
    """
    mapper = ProjectMapper(project_root)
    context = mapper.map_project()
    mapper.save_context(context, output_path)
    return context
