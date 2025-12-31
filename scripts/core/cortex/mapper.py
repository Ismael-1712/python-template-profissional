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

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

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

from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem  # noqa: E402
from scripts.utils.logger import setup_logging  # noqa: E402

logger = setup_logging(__name__, log_file="cortex_mapper.log")

# Import Knowledge components
try:
    from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
    from scripts.core.cortex.link_resolver import LinkResolver
    from scripts.core.cortex.models import KnowledgeEntry

    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False
    logger.debug("Knowledge components not available")


class CLICommand(BaseModel):
    """Represents a CLI command available in the project."""

    name: str
    script_path: str
    description: str = ""


class Document(BaseModel):
    """Represents a documentation file."""

    path: str
    title: str = ""
    category: str = ""
    has_frontmatter: bool = False


class ProjectContext(BaseModel):
    """Complete project context for introspection."""

    project_name: str
    version: str
    description: str
    python_version: str
    cli_commands: list[CLICommand] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)
    architecture_docs: list[Document] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    dev_dependencies: list[str] = Field(default_factory=list)
    scripts_available: dict[str, str] = Field(default_factory=dict)
    knowledge_entries_count: int = 0
    knowledge_links_valid: int = 0
    knowledge_links_broken: int = 0
    golden_paths: list[str] = Field(
        default_factory=list,
        description="Project-specific golden paths extracted from Knowledge Node",
    )
    knowledge_rules: str = Field(
        default="",
        description="Formatted Markdown with project rules and patterns for LLMs",
    )


class ProjectMapper:
    """Maps the project structure and generates context."""

    def __init__(
        self,
        project_root: Path,
        fs: FileSystemAdapter | None = None,
    ) -> None:
        """Initialize the mapper.

        Args:
            project_root: Root directory of the project
            fs: FileSystemAdapter for I/O operations (default: RealFileSystem)
        """
        if fs is None:
            fs = RealFileSystem()
        self.fs = fs
        self.project_root = project_root
        self.pyproject_path = project_root / "pyproject.toml"
        self.docs_path = project_root / "docs"
        self.scripts_cli_path = project_root / "scripts" / "cli"
        self._knowledge_scanner: KnowledgeScanner | None = None

    def map_project(self, include_knowledge: bool = True) -> ProjectContext:
        """Generate a complete project context map.

        Args:
            include_knowledge: Whether to include Knowledge Node rules and golden paths
                              (default: True for rich LLM context)

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

        # Process knowledge entries (scan + resolve links)
        if KNOWLEDGE_AVAILABLE:
            self._process_knowledge_entries(context)

            # Extract golden paths and rules for LLM context
            if include_knowledge:
                golden_paths, knowledge_rules = self._extract_knowledge_rules()
                context.golden_paths = golden_paths
                context.knowledge_rules = knowledge_rules

        logger.info(
            f"Project mapping complete. Found {len(context.cli_commands)} CLI commands",
        )
        logger.info(f"Found {len(context.documents)} documents")
        logger.info(f"Found {len(context.architecture_docs)} architecture documents")
        if include_knowledge:
            logger.info(f"Extracted {len(context.golden_paths)} golden paths")

        return context

    def _load_pyproject(self) -> dict[str, Any]:
        """Load and parse pyproject.toml.

        Returns:
            Parsed TOML configuration
        """
        if not self.fs.exists(self.pyproject_path):
            logger.warning("pyproject.toml not found")
            return {}

        try:
            # tomllib.loads espera string, então read_text é suficiente
            content = self.fs.read_text(self.pyproject_path)
            result: dict[str, Any] = tomllib.loads(content)
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
            content = self.fs.read_text(file_path)
            lines = content.splitlines(keepends=True)
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
            content = self.fs.read_text(file_path)
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()
        except Exception as e:
            logger.debug(f"Could not extract title from {file_path}: {e}")

        return file_path.stem

    def _process_knowledge_entries(self, context: ProjectContext) -> None:
        """Process knowledge entries: scan and resolve links.

        Updates the context with knowledge statistics.

        Args:
            context: ProjectContext to update with knowledge stats
        """
        try:
            # Scan knowledge entries
            scanner = KnowledgeScanner(workspace_root=self.project_root, fs=self.fs)
            entries = scanner.scan()

            if not entries:
                logger.debug("No knowledge entries found")
                return

            # Resolve links
            resolver = LinkResolver(entries, workspace_root=self.project_root)
            resolved_entries = resolver.resolve_all()

            # Calculate statistics
            from scripts.core.cortex.models import LinkStatus

            total_valid = sum(
                sum(1 for link in entry.links if link.status == LinkStatus.VALID)
                for entry in resolved_entries
            )
            total_broken = sum(
                sum(1 for link in entry.links if link.status == LinkStatus.BROKEN)
                for entry in resolved_entries
            )

            # Update context
            context.knowledge_entries_count = len(resolved_entries)
            context.knowledge_links_valid = total_valid
            context.knowledge_links_broken = total_broken

            # Save knowledge entries to separate file
            self._save_knowledge_entries(resolved_entries)

            logger.info(
                f"Processed {len(resolved_entries)} knowledge entries: "
                f"{total_valid} valid links, {total_broken} broken links",
            )

        except Exception as e:
            logger.warning(f"Failed to process knowledge entries: {e}")

    def _save_knowledge_entries(self, entries: list[KnowledgeEntry]) -> None:
        """Save knowledge entries to JSON file.

        Args:
            entries: List of KnowledgeEntry objects
        """
        try:
            import json

            output_path = self.project_root / ".cortex" / "knowledge.json"
            self.fs.mkdir(output_path.parent, parents=True, exist_ok=True)

            # Convert Pydantic models to dict
            entries_data = [entry.model_dump(mode="json") for entry in entries]

            json_content = json.dumps(
                {"entries": entries_data, "count": len(entries)},
                indent=2,
                ensure_ascii=False,
            )
            self.fs.write_text(output_path, json_content)

            logger.debug(f"Knowledge entries saved to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save knowledge entries: {e}")

    def _extract_knowledge_rules(self) -> tuple[list[str], str]:
        """Extract golden paths and format rules from Knowledge Node.

        Returns:
            Tuple of (golden_paths, knowledge_rules_markdown)
                - golden_paths: List of all golden path strings
                - knowledge_rules_markdown: Formatted Markdown for LLMs
        """
        try:
            # Initialize scanner if not cached
            if self._knowledge_scanner is None:
                self._knowledge_scanner = KnowledgeScanner(
                    workspace_root=self.project_root,
                    fs=self.fs,
                )

            # Scan knowledge entries
            entries = self._knowledge_scanner.scan()

            if not entries:
                logger.debug("No knowledge entries found for rule extraction")
                return [], ""

            # Filter out deprecated entries (keep active and draft)
            from scripts.core.cortex.models import DocStatus

            active_entries = [
                entry for entry in entries if entry.status != DocStatus.DEPRECATED
            ]

            if not active_entries:
                logger.debug("No active knowledge entries found")
                return [], ""

            # Extract all golden paths (flatten lists)
            all_golden_paths: list[str] = []
            for entry in active_entries:
                all_golden_paths.extend(entry.golden_paths)

            # Remove duplicates while preserving order
            unique_paths = list(dict.fromkeys(all_golden_paths))

            # Format as Markdown for LLMs
            markdown_rules = self._format_knowledge_markdown(active_entries)

            logger.info(
                f"Extracted {len(unique_paths)} golden paths from "
                f"{len(active_entries)} knowledge entries",
            )

            return unique_paths, markdown_rules

        except Exception as e:
            logger.warning(f"Failed to extract knowledge rules: {e}")
            return [], ""

    # TODO: Refactor God Function - break down markdown formatting into sections
    def _format_knowledge_markdown(self, entries: list[KnowledgeEntry]) -> str:  # noqa: C901
        """Format knowledge entries as LLM-friendly Markdown.

        Args:
            entries: List of KnowledgeEntry objects (active/draft only)

        Returns:
            Formatted Markdown string
        """
        if not entries:
            return ""

        lines = [
            "# Project Rules & Golden Paths",
            "",
            "This section contains project-specific rules, patterns, and golden paths "
            "extracted from the Knowledge Node.",
            "",
            "## Active Rules",
            "",
        ]

        for entry in entries:
            # Rule header with ID and status
            status_badge = "[DRAFT]" if entry.status.value == "draft" else "[ACTIVE]"
            lines.append(f"### {entry.id} {status_badge}")
            lines.append("")

            # Tags
            if entry.tags:
                tags_str = ", ".join(f"`{tag}`" for tag in entry.tags)
                lines.append(f"**Tags:** {tags_str}")
                lines.append("")

            # Golden Paths
            if entry.golden_paths:
                lines.append("**Golden Paths:**")
                for path in entry.golden_paths:
                    lines.append(f"- `{path}`")
                lines.append("")

            # Content excerpt (first 3 lines of cached content)
            if entry.cached_content:
                content_lines = entry.cached_content.strip().split("\n")
                # Skip markdown headings and get first meaningful content
                content_preview = []
                for line in content_lines:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        content_preview.append(stripped)
                    if len(content_preview) >= 2:
                        break

                if content_preview:
                    lines.append("**Rule Summary:**")
                    for preview_line in content_preview:
                        lines.append(f"> {preview_line}")
                    lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def save_context(self, context: ProjectContext, output_path: Path) -> None:
        """Save context to JSON file.

        Args:
            context: Project context to save
            output_path: Path to output JSON file
        """
        self.fs.mkdir(output_path.parent, parents=True, exist_ok=True)

        json_content = json.dumps(
            context.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        self.fs.write_text(output_path, json_content)

        logger.info(f"Context saved to {output_path}")


def generate_context_map(
    project_root: Path,
    output_path: Path,
    include_knowledge: bool = True,
) -> ProjectContext:
    """Generate and save project context map.

    Args:
        project_root: Root directory of the project
        output_path: Path to save JSON output
        include_knowledge: Whether to include Knowledge Node rules (default: True)

    Returns:
        Generated ProjectContext
    """
    mapper = ProjectMapper(project_root)
    context = mapper.map_project(include_knowledge=include_knowledge)
    mapper.save_context(context, output_path)
    return context
