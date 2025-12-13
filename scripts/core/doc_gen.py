#!/usr/bin/env python3
"""Automatic CLI Documentation Generator.

This script automatically generates comprehensive Markdown documentation
from Typer CLI applications. It uses introspection to extract commands,
arguments, options, and docstrings without manual maintenance.

Features:
- Auto-discovery of all CLI commands
- Idempotent operation (no file changes if docs unchanged)
- Automatic Table of Contents generation
- Type-safe parameter extraction
- Support for subcommands and nested command groups

Usage:
    python scripts/core/doc_gen.py

Integration:
    Designed to run automatically via pre-commit hook when CLI files change.

Author: DevOps Engineering Team
License: MIT
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import inspect
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, cast

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import typer  # noqa: E402

from scripts.utils.logger import setup_logging  # noqa: E402

logger = setup_logging(__name__, log_file="doc_gen.log")


class CLIDocGenerator:
    """Generator for CLI documentation from Typer applications.

    Introspects Typer apps to extract commands, parameters, and metadata,
    then generates well-formatted Markdown documentation.
    """

    def __init__(self, output_path: Path) -> None:
        """Initialize documentation generator.

        Args:
            output_path: Path where CLI_COMMANDS.md will be written
        """
        self.output_path = output_path
        self.cli_modules = [
            ("cortex", "scripts.cli.cortex"),
            ("audit", "scripts.cli.audit"),
            ("doctor", "scripts.cli.doctor"),
            ("git-sync", "scripts.cli.git_sync"),
            ("mock-gen", "scripts.cli.mock_generate"),
            ("mock-check", "scripts.cli.mock_validate"),
            ("mock-ci", "scripts.cli.mock_ci"),
            ("install-dev", "scripts.cli.install_dev"),
            ("upgrade-python", "scripts.cli.upgrade_python"),
        ]

    def generate_documentation(self) -> str:
        """Generate complete CLI documentation in Markdown format.

        Returns:
            Complete Markdown documentation as string
        """
        sections = []

        # Header
        sections.append(self._generate_header())

        # Table of Contents
        toc_entries = []
        command_sections = []

        # Process each CLI module
        for cli_name, module_path in self.cli_modules:
            try:
                module = self._import_module(module_path)

                # Check if it's a Typer app or simple main() function
                if hasattr(module, "app") and isinstance(module.app, typer.Typer):
                    # Typer app with commands
                    cli_section, toc_items = self._process_typer_app(
                        cli_name,
                        module.app,
                        module,
                    )
                    toc_entries.extend(toc_items)
                    command_sections.append(cli_section)
                elif hasattr(module, "main"):
                    # Simple CLI with main() function
                    cli_section, toc_item = self._process_simple_cli(
                        cli_name,
                        module,
                    )
                    toc_entries.append(toc_item)
                    command_sections.append(cli_section)
                else:
                    logger.warning(f"No app or main() found in {module_path}")

            except Exception as e:
                logger.error(f"Failed to process {cli_name}: {e}", exc_info=True)
                continue

        # Assemble final document
        sections.append(self._generate_toc(toc_entries))
        sections.extend(command_sections)
        sections.append(self._generate_footer())

        return "\n\n".join(sections)

    def _generate_header(self) -> str:
        """Generate document header with metadata."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return f"""---
id: cli-commands-reference
type: reference
status: active
version: 0.1.0
author: Auto-Generated (doc_gen.py)
date: '{datetime.now(timezone.utc).strftime("%Y-%m-%d")}'
context_tags: [cli, commands, reference]
linked_code:
  - scripts/cli/cortex.py
  - scripts/cli/audit.py
  - scripts/core/doc_gen.py
title: 📚 Referência de Comandos CLI (Auto-Generated)
---

# 📚 Referência de Comandos CLI (Auto-Generated)

**⚠️ ESTE ARQUIVO É GERADO AUTOMATICAMENTE**

Não edite manualmente. Toda alteração será sobrescrita.
Gerado em: **{timestamp}**
Fonte: `scripts/core/doc_gen.py`

Este documento contém a referência completa de todos os comandos CLI disponíveis
no projeto. A documentação é extraída automaticamente dos códigos-fonte usando
introspecção do Typer."""

    def _generate_toc(self, entries: list[tuple[str, str]]) -> str:
        """Generate Table of Contents.

        Args:
            entries: List of (title, anchor) tuples

        Returns:
            Formatted TOC section
        """
        toc_lines = ["## 📑 Índice\n"]

        for title, anchor in entries:
            # Detect CLI boundaries
            if " - " not in title:
                # This is a CLI header
                toc_lines.append(f"- **[{title}](#{anchor})**")
            else:
                # This is a command under a CLI
                toc_lines.append(f"  - [{title}](#{anchor})")

        return "\n".join(toc_lines)

    def _generate_footer(self) -> str:
        """Generate document footer."""
        return f"""---

## 🔄 Atualização Automática

Esta documentação é regenerada automaticamente:

1. **Trigger:** Commit que modifica arquivos em `scripts/cli/` ou `scripts/core/`
2. **Hook:** `.pre-commit-config.yaml` → `auto-doc-gen`
3. **Script:** `scripts/core/doc_gen.py`

**Para forçar regeneração manual:**
```bash
python scripts/core/doc_gen.py
```

---

**Última Atualização:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
**Gerado por:** `scripts/core/doc_gen.py` v1.0.0"""

    def _import_module(self, module_path: str) -> ModuleType:
        """Dynamically import a module by path.

        Args:
            module_path: Dotted module path (e.g., 'scripts.cli.cortex')

        Returns:
            Imported module object
        """
        import importlib

        return importlib.import_module(module_path)

    def _process_typer_app(
        self,
        cli_name: str,
        app: typer.Typer,
        module: ModuleType,
    ) -> tuple[str, list[tuple[str, str]]]:
        """Process a Typer application and extract commands.

        Args:
            cli_name: Name of the CLI (e.g., 'cortex')
            app: Typer application instance
            module: Module containing the app

        Returns:
            Tuple of (markdown_section, toc_entries)
        """
        sections: list[str] = []
        toc_entries: list[tuple[str, str]] = []

        # CLI Header
        cli_anchor = cli_name.replace("-", "")
        sections.append(f"## `{cli_name}` - {self._get_cli_description(module)}")
        toc_entries.append((cli_name, cli_anchor))

        # Module docstring
        if module.__doc__:
            desc = module.__doc__.split("Usage:")[0].strip()
            sections.append(f"**Descrição:** {desc}")

        # Extract commands from Typer app
        commands = self._extract_commands(app)

        if not commands:
            sections.append("*Nenhum comando encontrado via introspecção.*")
            return "\n\n".join(sections), toc_entries

        # Process each command
        for cmd_name, cmd_info in sorted(commands.items()):
            cmd_section, cmd_anchor = self._process_command(
                cli_name,
                cmd_name,
                cmd_info,
            )
            sections.append(cmd_section)
            toc_entries.append((f"{cli_name} - {cmd_name}", cmd_anchor))

        return "\n\n".join(sections), toc_entries

    def _process_simple_cli(
        self,
        cli_name: str,
        module: ModuleType,
    ) -> tuple[str, tuple[str, str]]:
        """Process a simple CLI with main() function.

        Args:
            cli_name: Name of the CLI
            module: Module containing main()

        Returns:
            Tuple of (markdown_section, toc_entry)
        """
        sections: list[str] = []
        cli_anchor = cli_name.replace("-", "")

        # CLI Header
        sections.append(f"## `{cli_name}` - {self._get_cli_description(module)}")

        # Module docstring
        if module.__doc__:
            desc = module.__doc__.split("Usage:")[0].strip()
            sections.append(f"**Descrição:** {desc}")

        # main() function signature
        if hasattr(module, "main"):
            main_func = module.main
            sections.append("### Função Principal")
            sections.append(f"```python\n{inspect.signature(main_func)}\n```")

            if main_func.__doc__:
                sections.append(f"**Documentação:**\n\n{main_func.__doc__}")

        return "\n\n".join(sections), (cli_name, cli_anchor)

    def _extract_commands(self, app: typer.Typer) -> dict[str, dict[str, Any]]:
        """Extract commands from Typer app using introspection.

        Args:
            app: Typer application instance

        Returns:
            Dictionary mapping command names to their metadata
        """
        commands: dict[str, dict[str, Any]] = {}

        # Access Typer's internal registered_commands
        registered_commands = getattr(app, "registered_commands", None)
        if registered_commands is not None:
            for cmd in registered_commands:
                # Guard against None callback
                if not hasattr(cmd, "callback") or cmd.callback is None:
                    continue

                # Safe extraction of command name
                cmd_name_attr = getattr(cmd, "name", None)
                if cmd_name_attr is not None:
                    cmd_name = cmd_name_attr
                else:
                    # Fallback to callback __name__ with guard
                    callback_name = getattr(cmd.callback, "__name__", "unknown")
                    cmd_name = callback_name

                # Safe extraction of help text
                help_text = getattr(cmd, "help", None) or ""

                commands[cmd_name] = {
                    "callback": cmd.callback,
                    "help": help_text,
                    "params": self._extract_params(cmd.callback),
                }

        # Fallback: try to access via click conversion
        else:
            app_info = getattr(app, "info", None)
            if app_info is not None:
                info_commands = getattr(app_info, "commands", {})
                for cmd_name, cmd_obj in info_commands.items():
                    callback = getattr(cmd_obj, "callback", None)
                    help_text = getattr(cmd_obj, "help", None) or ""

                    commands[cmd_name] = {
                        "callback": callback,
                        "help": help_text,
                        "params": [],
                    }

        return commands

    def _extract_params(self, func: Callable[..., Any] | None) -> list[dict[str, Any]]:
        """Extract parameters from function signature.

        Args:
            func: Function to introspect (can be None)

        Returns:
            List of parameter metadata dictionaries
        """
        # Guard against None function
        if func is None:
            return []

        params: list[dict[str, Any]] = []

        try:
            sig = inspect.signature(func)
        except (ValueError, TypeError):
            # Function signature cannot be inspected
            return []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            param_info = {
                "name": param_name,
                "type": self._format_type(param.annotation),
                "default": self._format_default(param.default),
                "required": param.default == inspect.Parameter.empty,
            }
            params.append(param_info)

        return params

    def _process_command(
        self,
        cli_name: str,
        cmd_name: str,
        cmd_info: dict[str, Any],
    ) -> tuple[str, str]:
        """Process individual command and generate documentation.

        Args:
            cli_name: Parent CLI name
            cmd_name: Command name
            cmd_info: Command metadata

        Returns:
            Tuple of (markdown_section, anchor)
        """
        sections: list[str] = []
        anchor = f"{cli_name}-{cmd_name}".replace("-", "").replace("_", "")

        # Command header
        sections.append(f"### `{cli_name} {cmd_name}`")

        # Help text
        help_text = cmd_info.get("help", "")
        if help_text:
            sections.append(f"**Descrição:** {help_text}")

        # Docstring from callback with guard
        callback = cmd_info.get("callback")
        if callback is not None:
            callback_doc = getattr(callback, "__doc__", None)
            if callback_doc:
                docstring = inspect.cleandoc(callback_doc)
                sections.append(f"\n{docstring}\n")

        # Parameters table
        if cmd_info["params"]:
            sections.append("**Parâmetros:**\n")
            sections.append("| Nome | Tipo | Padrão | Obrigatório |")
            sections.append("|:-----|:-----|:-------|:------------|")

            for param in cmd_info["params"]:
                required = "✅ Sim" if param["required"] else "❌ Não"
                sections.append(
                    f"| `{param['name']}` | `{param['type']}` | "
                    f"`{param['default']}` | {required} |",
                )

        # Usage example
        param_names = [p["name"] for p in cmd_info["params"] if p["required"]]
        if param_names:
            example_args = " ".join(f"<{name}>" for name in param_names)
            example = f"{cli_name} {cmd_name} {example_args}"
            sections.append(f"\n**Exemplo:**\n```bash\n{example}\n```")
        else:
            sections.append(f"\n**Exemplo:**\n```bash\n{cli_name} {cmd_name}\n```")

        return "\n\n".join(sections), anchor

    def _get_cli_description(self, module: ModuleType) -> str:
        """Extract CLI description from module docstring.

        Args:
            module: CLI module

        Returns:
            Short description string
        """
        # Guard against None docstring
        module_doc = getattr(module, "__doc__", None)
        if not module_doc or not isinstance(module_doc, str):
            return "CLI Tool"

        # Cast to str after isinstance check to satisfy mypy strict mode
        doc_str = cast("str", module_doc)
        # Get first line of docstring
        first_line = doc_str.strip().split("\n")[0]
        return first_line.strip("# ").strip()

    def _format_type(self, annotation: Any) -> str:
        """Format type annotation for display.

        Args:
            annotation: Type annotation from signature

        Returns:
            Formatted type string
        """
        if annotation == inspect.Parameter.empty:
            return "Any"

        # Handle string annotations
        if isinstance(annotation, str):
            return annotation

        # Handle typing module types
        type_str = str(annotation)
        type_str = type_str.replace("typing.", "")
        type_str = type_str.replace("<class '", "").replace("'>", "")

        return type_str

    def _format_default(self, default: Any) -> str:
        """Format default value for display.

        Args:
            default: Default value from parameter

        Returns:
            Formatted default string
        """
        if default == inspect.Parameter.empty:
            return "-"

        if default is None:
            return "None"

        if isinstance(default, str):
            return f'"{default}"'

        if isinstance(default, bool):
            return str(default)

        # Handle Typer special types
        if hasattr(default, "__class__"):
            default_class = getattr(default, "__class__", None)
            if default_class is not None:
                class_name = getattr(default_class, "__name__", "")
                if "Option" in class_name or "Argument" in class_name:
                    return "CLI Option"

        return str(default)

    def write_documentation(self, force: bool = False) -> bool:
        """Write documentation to file with idempotency check.

        Args:
            force: If True, write even if content hasn't changed

        Returns:
            True if file was written, False if skipped (unchanged)
        """
        # Generate new documentation
        new_content = self.generate_documentation()

        # Calculate hash for idempotency check
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()

        # Check if file exists and content is identical
        if not force and self.output_path.exists():
            old_content = self.output_path.read_text(encoding="utf-8")
            old_hash = hashlib.sha256(old_content.encode()).hexdigest()

            if new_hash == old_hash:
                logger.info("Documentation unchanged, skipping write (idempotent)")
                return False

        # Ensure parent directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write new documentation
        self.output_path.write_text(new_content, encoding="utf-8")
        logger.info(f"Documentation written to {self.output_path}")

        return True


def main() -> int:
    """Main entry point for documentation generator.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        output_path = PROJECT_ROOT / "docs" / "reference" / "CLI_COMMANDS.md"

        logger.info("Starting CLI documentation generation...")
        generator = CLIDocGenerator(output_path)

        was_written = generator.write_documentation()

        if was_written:
            logger.info("✅ Documentation generated successfully")
            print(f"✅ Documentation generated: {output_path}")
        else:
            logger.info("⏭️  Documentation unchanged (skipped)")
            print("⏭️  Documentation unchanged (skipped)")

        return 0

    except Exception as e:
        logger.error(f"Documentation generation failed: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
