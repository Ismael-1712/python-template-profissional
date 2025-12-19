"""Testes End-to-End para MockCIRunner.

Nota: Estes testes validam apenas a estrutura e imports do runner.
Testes funcionais completos requerem correção prévia do TestMockValidator
para aceitar config_file como parâmetro.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.core.mock_ci import MockCIRunner


class TestMockCIRunnerStructure:
    """Testes de estrutura do MockCIRunner."""

    def test_runner_class_exists_and_is_importable(self) -> None:
        """Verifica que MockCIRunner pode ser importado."""
        assert MockCIRunner is not None
        assert MockCIRunner.__doc__ is not None

    def test_runner_has_expected_methods(self) -> None:
        """Verifica que MockCIRunner tem os métodos esperados."""
        assert hasattr(MockCIRunner, "check")
        assert hasattr(MockCIRunner, "fix")
        assert hasattr(MockCIRunner, "generate_report")
        assert hasattr(MockCIRunner, "print_summary")
        assert hasattr(MockCIRunner, "get_environment_info")

    def test_runner_init_signature(self) -> None:
        """Verifica assinatura do __init__."""
        import inspect

        sig = inspect.signature(MockCIRunner.__init__)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "workspace_root" in params
        # BREAKING CHANGE: config_file -> config (MockCIConfig)
        assert "config" in params


class TestMockCIInitCommand:
    """Testes do comando init do Mock CI CLI."""

    def test_init_command_creates_config_file(self, tmp_path: Path) -> None:
        """Verifica que o comando init cria o arquivo de configuração."""
        output_file = tmp_path / "test_mock_config.yaml"

        # Executa o comando init
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.cli.mock_ci",
                "init",
                "--output",
                str(output_file),
                "--workspace",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            check=False,
        )

        # Verifica que o comando foi executado com sucesso
        assert result.returncode == 0, (
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

        # Verifica que o arquivo foi criado
        assert output_file.exists(), "Arquivo de configuração não foi criado"

        # Verifica que o arquivo tem conteúdo
        content = output_file.read_text(encoding="utf-8")
        assert len(content) > 0, "Arquivo de configuração está vazio"

        # Verifica que o arquivo tem comentários explicativos
        assert "# ====" in content, "Arquivo não tem comentários de cabeçalho"
        assert "Mock CI Configuration" in content, "Arquivo não tem título correto"
        assert "mock_patterns:" in content, "Arquivo não tem seção de padrões"
        assert "execution:" in content, "Arquivo não tem seção de execução"

    def test_init_command_with_existing_file_fails_without_force(
        self,
        tmp_path: Path,
    ) -> None:
        """Verifica que init falha se arquivo já existe e --force não foi usado."""
        output_file = tmp_path / "test_mock_config.yaml"
        output_file.write_text("existing content", encoding="utf-8")

        # Executa o comando init sem --force
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.cli.mock_ci",
                "init",
                "--output",
                str(output_file),
                "--workspace",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            check=False,
        )

        # Verifica que o comando falhou
        assert result.returncode == 1, (
            "Comando deveria ter falhado com arquivo existente"
        )

        # Verifica que a mensagem de erro está presente
        output = result.stdout + result.stderr
        assert "já existe" in output or "already exists" in output.lower()

    def test_init_command_with_force_overwrites(self, tmp_path: Path) -> None:
        """Verifica que init com --force sobrescreve arquivo existente."""
        output_file = tmp_path / "test_mock_config.yaml"
        output_file.write_text("old content", encoding="utf-8")

        # Executa o comando init com --force
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.cli.mock_ci",
                "init",
                "--output",
                str(output_file),
                "--workspace",
                str(tmp_path),
                "--force",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            check=False,
        )

        # Verifica que o comando foi executado com sucesso
        assert result.returncode == 0

        # Verifica que o arquivo foi sobrescrito
        content = output_file.read_text(encoding="utf-8")
        assert "old content" not in content
        assert "Mock CI Configuration" in content
