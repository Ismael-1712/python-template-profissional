"""Tests for CI integrity ensuring workflows match CLI commands."""

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.cortex.cli import app


class TestCIIntegrity:
    """Garante integridade dos comandos de CI.

    Verifica se os comandos definidos nos workflows (.github/workflows)
    são válidos na versão atual do CLI.

    Filosofia Autoimune: O código não pode mudar de forma a quebrar a CI
    silenciosamente.
    """

    WORKFLOWS_DIR = Path(".github/workflows")

    def test_ci_commands_are_valid(self) -> None:
        """Valida comandos do Cortex nos workflows.

        Varre arquivos .yml, extrai 'scripts.cortex <cmd>' e testa
        se respondem ao --help usando CliRunner (in-memory execution).
        """
        if not self.WORKFLOWS_DIR.exists():
            pytest.skip("Diretório de workflows não encontrado")

        cortex_commands = []
        runner = CliRunner()

        # 1. Extrair comandos dos arquivos YAML
        # Padrão: python -m scripts.cortex <comando>
        pattern = re.compile(r"python -m scripts\.cortex\s+([a-zA-Z0-9_-]+)")

        for workflow_file in self.WORKFLOWS_DIR.glob("*.yml"):
            content = workflow_file.read_text(encoding="utf-8")
            matches = pattern.finditer(content)

            for match in matches:
                cmd = match.group(1)
                # Ignorar flags (começam com -) e capturar apenas o verbo
                if not cmd.startswith("-"):
                    cortex_commands.append((workflow_file.name, cmd))

        # 2. Validar cada comando extraído usando CliRunner
        for source_file, command in cortex_commands:
            # Executa o comando com --help em memória (sem subprocess)
            result = runner.invoke(app, [command, "--help"])

            if result.exit_code != 0:
                pytest.fail(
                    f"\n❌ ERRO CRÍTICO DE INTEGRIDADE DE CI:\n"
                    f"O workflow '{source_file}' usa comando INEXISTENTE: "
                    f"'{command}'.\n"
                    f"Isso ocorre ao renomear comandos no CLI sem atualizar a CI.\n\n"
                    f"Saída do erro:\n{result.output}\n"
                    f"Exception (if any): {result.exception}\n",
                )
