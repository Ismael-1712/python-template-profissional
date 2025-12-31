"""Tests for CI integrity ensuring workflows match CLI commands."""

import re
import subprocess  # nosec B404
from pathlib import Path

import pytest


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
        se respondem ao --help.
        """
        if not self.WORKFLOWS_DIR.exists():
            pytest.skip("Diretório de workflows não encontrado")

        cortex_commands = []

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

        # 2. Validar cada comando extraído
        for source_file, command in cortex_commands:
            # Executa o comando com --help para verificar existência
            # nosec B603, B607: Uso controlado de subprocess para testes internos
            result = subprocess.run(  # nosec B603
                ["python", "-m", "scripts.cortex", command, "--help"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                pytest.fail(
                    f"\n❌ ERRO CRÍTICO DE INTEGRIDADE DE CI:\n"
                    f"O workflow '{source_file}' usa comando INEXISTENTE: "
                    f"'{command}'.\n"
                    f"Isso ocorre ao renomear comandos no CLI sem atualizar a CI.\n\n"
                    f"Saída do erro:\n{result.stderr}\n"
                )
