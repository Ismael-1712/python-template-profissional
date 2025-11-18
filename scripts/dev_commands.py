#!/usr/bin/env python3
"""Sistema Unificado de Comandos de Desenvolvimento.

Fornece interface consistente para comandos comuns de desenvolvimento,
CI/CD e qualidade de código.

Uso: python3 scripts/dev_commands.py [command] [--options]
"""

import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CommandCategory(Enum):
    """Categorias de comandos disponíveis."""

    CODE_QUALITY = "quality"
    TESTING = "testing"
    BUILD = "build"


@dataclass
class DevCommand:
    """Definição de um comando de desenvolvimento."""

    name: str
    description: str
    category: CommandCategory
    command_template: str
    working_dir: Path | None = None
    env_vars: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 300
    capture_output: bool = True


class DevCommandsManager:
    """Gerenciador de comandos de desenvolvimento."""

    def __init__(self, workspace_root: Path) -> None:
        """Inicializa o gerenciador."""
        self.workspace_root = workspace_root.resolve()
        self.commands: dict[str, DevCommand] = {}
        self._register_default_commands()

    def _register_default_commands(self) -> None:
        """Registra comandos padrão."""
        # Quality commands
        self.register_command(
            DevCommand(
                name="lint",
                description="Executa linting com ruff",
                category=CommandCategory.CODE_QUALITY,
                command_template="{python_executable} -m ruff check {src_dir} {args}",
            ),
        )

        self.register_command(
            DevCommand(
                name="format",
                description="Formata código com ruff",
                category=CommandCategory.CODE_QUALITY,
                command_template="{python_executable} -m ruff format {src_dir} {args}",
            ),
        )

        # Testing commands
        self.register_command(
            DevCommand(
                name="test",
                description="Executa testes com pytest",
                category=CommandCategory.TESTING,
                command_template="{python_executable} -m pytest {test_dir} {args}",
            ),
        )

        # Build commands
        self.register_command(
            DevCommand(
                name="build",
                description="Constrói pacote distribuível",
                category=CommandCategory.BUILD,
                command_template="{python_executable} -m build",
            ),
        )

        self.register_command(
            DevCommand(
                name="install-dev",
                description="Compila dependências e instala projeto em desenvolvimento",
                category=CommandCategory.BUILD,
                command_template="CUSTOM_INSTALL_DEV",
            ),
        )

    def register_command(self, command: DevCommand) -> None:
        """Registra um comando de desenvolvimento."""
        self.commands[command.name] = command

    def _install_dev_explicit(self, working_dir: Path) -> subprocess.CompletedProcess:
        """Implementação explícita do comando install-dev.

        Usa subprocess.run sequencial para garantir atomicidade.
        """
        logger.info("Passo 1/3: Instalando projeto e pip-tools...")
        result1 = subprocess.run(  # noqa: subprocess
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        logger.info("Passo 2/3: Compilando dependências com pip-compile...")
        # Primeiro, vamos tentar encontrar pip-compile no PATH do ambiente virtual
        pip_compile_path = shutil.which("pip-compile")
        if not pip_compile_path:
            # Fallback: usar python -c para executar pip-compile via piptools
            result2 = subprocess.run(  # noqa: subprocess
                [
                    sys.executable,
                    "-c",
                    "import sys; from piptools.scripts import compile; "
                    "sys.argv = ['pip-compile', '--output-file', 'requirements/dev.txt', "  # noqa: E501
                    "'requirements/dev.in']; compile.cli()",
                ],
                cwd=working_dir,
                capture_output=True,
                text=True,
                check=True,
            )
        else:
            result2 = subprocess.run(  # noqa: subprocess
                [
                    pip_compile_path,
                    "--output-file",
                    "requirements/dev.txt",
                    "requirements/dev.in",
                ],
                cwd=working_dir,
                capture_output=True,
                text=True,
                check=True,
            )

        logger.info("Passo 3/3: Instalando dependências pinned...")
        result3 = subprocess.run(  # noqa: subprocess
            [sys.executable, "-m", "pip", "install", "-r", "requirements/dev.txt"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        # Retorna o último resultado, mas com stdout combinado para feedback
        combined_output = f"{result1.stdout}\n{result2.stdout}\n{result3.stdout}"
        return subprocess.CompletedProcess(
            result3.args,
            0,
            combined_output,
            "",
        )

    def _resolve_template_vars(self, template: str, **kwargs: Any) -> list[str]:
        """Resolve variáveis do template de comando de forma segura."""
        template_vars = {
            "python_executable": sys.executable,
            "src_dir": "src",
            "test_dir": "tests",
            "args": "",
        }
        template_vars.update(kwargs)
        formatted_command = template.format(**template_vars)
        return shlex.split(formatted_command)

    def execute_command(
        self,
        command_name: str,
        args: list[str] | None = None,
        dry_run: bool = False,
        **template_kwargs: Any,
    ) -> subprocess.CompletedProcess:
        """Executa um comando de desenvolvimento de forma segura."""
        if command_name not in self.commands:
            raise ValueError(f"Unknown command: {command_name}")

        command = self.commands[command_name]
        working_dir = command.working_dir or self.workspace_root

        logger.info("Executing command: %s", command_name)

        # Tratamento especial para install-dev customizado
        if command.command_template == "CUSTOM_INSTALL_DEV":
            if dry_run:
                logger.info("DRY RUN - Would execute install-dev sequence")
                return subprocess.CompletedProcess(["install-dev"], 0, "", "")
            try:
                return self._install_dev_explicit(working_dir)
            except subprocess.CalledProcessError as e:
                logger.error(
                    "install-dev failed at step with exit code %s",
                    e.returncode,
                )
                logger.error("Error output: %s", e.stderr)
                raise

        # Execução padrão para outros comandos
        template_kwargs["args"] = " ".join(args or [])
        cmd_parts = self._resolve_template_vars(
            command.command_template,
            **template_kwargs,
        )

        env = dict(os.environ)
        env.update(command.env_vars)

        if dry_run:
            logger.info("DRY RUN - Would execute: %s", " ".join(cmd_parts))
            return subprocess.CompletedProcess(cmd_parts, 0, "", "")

        try:
            result = subprocess.run(  # noqa: subprocess
                cmd_parts,
                cwd=working_dir,
                env=env,
                capture_output=command.capture_output,
                text=True,
                timeout=command.timeout_seconds,
                check=False,
            )
            return result
        except subprocess.SubprocessError as e:
            logger.error("Command %s failed: %s", command_name, e)
            raise

    def list_commands(self) -> list[DevCommand]:
        """Lista comandos disponíveis."""
        return sorted(
            self.commands.values(),
            key=lambda x: (x.category.value, x.name),
        )

    def export_vscode_tasks(self) -> dict[str, Any]:
        """Exporta comandos como tasks do VS Code."""
        tasks = {"version": "2.0.0", "tasks": []}

        for cmd in self.commands.values():
            task = {
                "label": f"dev: {cmd.name}",
                "type": "shell",
                "command": f"{sys.executable}",
                "args": ["scripts/dev_commands.py", cmd.name],
                "group": {"kind": cmd.category.value},
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared",
                },
            }
            tasks["tasks"].append(task)

        return tasks


def main() -> int:
    """Interface de linha de comando principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sistema Unificado de Comandos de Desenvolvimento",
    )

    parser.add_argument("command", nargs="?", help="Comando a executar")
    parser.add_argument("--dry-run", action="store_true", help="Dry run")
    parser.add_argument("--export-vscode", action="store_true", help="Export VS Code")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")
    parser.add_argument("args", nargs="*", help="Argumentos adicionais")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    workspace_root = Path(__file__).parent.parent
    manager = DevCommandsManager(workspace_root)

    try:
        if args.export_vscode:
            vscode_dir = workspace_root / ".vscode"
            vscode_dir.mkdir(exist_ok=True)

            tasks_file = vscode_dir / "tasks.json"
            tasks_config = manager.export_vscode_tasks()

            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks_config, f, indent=2, ensure_ascii=False)

            print(f"✅ Configuração VS Code exportada: {tasks_file}")
            return 0

        if args.command == "list" or not args.command:
            commands = manager.list_commands()
            print("📋 Comandos Disponíveis:\n")

            current_category = None
            for cmd in commands:
                if cmd.category != current_category:
                    current_category = cmd.category
                    print(f"\n🏷️ {current_category.value.upper()}:")

                print(f"  {cmd.name:<15} - {cmd.description}")

            return 0

        result = manager.execute_command(
            args.command,
            args=args.args,
            dry_run=args.dry_run,
        )

        if not args.dry_run and result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        return result.returncode

    except Exception as e:
        logger.error("Erro: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
