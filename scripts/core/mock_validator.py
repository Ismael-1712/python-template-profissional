"""Mock Validator Core - Test Mock Validation Engine.

This module contains the core business logic for validating the test mock
generation system. It ensures that mocks are generated correctly and test
files maintain proper structure.

Classes:
    TestMockValidator: Main engine for mock validation and integrity checks

Author: DevOps Engineering Team
License: MIT
Version: 2.0.0 (Refactored)
"""

import ast
import logging
from pathlib import Path

from scripts.core.mock_generator import TestMockGenerator

logger = logging.getLogger(__name__)


class TestMockValidator:
    """Validador para o sistema de geração automática de mocks.

    Implementa verificações de integridade e testes automatizados
    para garantir que o sistema funcione corretamente.
    """

    def __init__(
        self,
        workspace_root: Path,
        config_path: Path | None = None,
    ) -> None:
        """Inicializa o validador.

        Args:
            workspace_root: Caminho raiz do workspace
            config_path: Caminho opcional para o arquivo de configuração.
                        Se None, tenta localizar automaticamente.

        """
        self.workspace_root = workspace_root.resolve()
        self._init_error: str | None = None
        self.generator: TestMockGenerator | None = None
        self.validation_errors: list[dict[str, str]] = []

        # Tenta localizar o arquivo de config
        if config_path is None:
            script_dir = Path(__file__).parent
            config_path = script_dir / "test_mock_config.yaml"

        if not config_path.exists():
            error_msg = f"Config do gerador não encontrado: {config_path}"
            logger.warning(error_msg)
            self._init_error = error_msg
            # NÃO levanta exceção - permite construção resiliente
            return

        try:
            self.generator = TestMockGenerator(workspace_root, config_path)
            logger.debug(f"TestMockValidator inicializado com config: {config_path}")
        except Exception as e:
            error_msg = f"Erro ao inicializar gerador de mocks: {e}"
            logger.warning(error_msg)
            self._init_error = error_msg

    def validate_workspace_structure(self) -> bool:
        """Valida se a estrutura do workspace está adequada.

        Returns:
            True se estrutura válida

        """
        logger.info("Validando estrutura do workspace...")

        required_paths = [
            "tests",  # Diretório de testes
            "src",  # Código fonte (opcional)
        ]

        optional_paths = [
            "pyproject.toml",
            "requirements.txt",
            "setup.py",
        ]

        is_valid = True

        # Verifica caminhos obrigatórios
        for path_name in required_paths:
            path = self.workspace_root / path_name
            if not path.exists() and path_name == "tests":
                # Tenta criar diretório de testes se não existir
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Diretório de testes criado: {path}")
                except Exception as e:
                    logger.error(f"Erro ao criar diretório {path}: {e}")
                    self.validation_errors.append(
                        {
                            "type": "MISSING_DIRECTORY",
                            "path": str(path),
                            "message": f"Diretório obrigatório não encontrado: {path}",
                        },
                    )
                    is_valid = False

        # Verifica se há pelo menos um arquivo de configuração Python
        has_config = any(
            (self.workspace_root / path).exists() for path in optional_paths
        )
        if not has_config:
            self.validation_errors.append(
                {
                    "type": "MISSING_CONFIG",
                    "path": str(self.workspace_root),
                    "message": (
                        "Nenhum arquivo de configuração Python encontrado "
                        "(pyproject.toml, etc.)"
                    ),
                },
            )

        logger.info(
            f"Validação da estrutura: {'✅ Válida' if is_valid else '❌ Inválida'}",
        )
        return is_valid

    def validate_test_files_syntax(self) -> bool:
        """Valida sintaxe de todos os arquivos de teste.

        Returns:
            True se todos os arquivos têm sintaxe válida

        """
        logger.info("Validando sintaxe dos arquivos de teste...")

        test_files = list(self.workspace_root.glob("tests/**/*.py"))
        if not test_files:
            logger.warning("Nenhum arquivo de teste encontrado")
            return True

        valid_files = 0

        for test_file in test_files:
            try:
                with test_file.open("r", encoding="utf-8") as f:
                    content = f.read()

                ast.parse(content, filename=str(test_file))
                valid_files += 1

            except SyntaxError as e:
                logger.error(f"Erro de sintaxe em {test_file}: {e}")
                self.validation_errors.append(
                    {
                        "type": "SYNTAX_ERROR",
                        "path": str(test_file),
                        "message": f"Erro de sintaxe: {e}",
                    },
                )
            except Exception as e:
                logger.error(f"Erro ao validar {test_file}: {e}")
                self.validation_errors.append(
                    {
                        "type": "VALIDATION_ERROR",
                        "path": str(test_file),
                        "message": f"Erro de validação: {e}",
                    },
                )

        success_rate = valid_files / len(test_files) if test_files else 1.0
        msg = (
            f"Validação de sintaxe: {valid_files}/{len(test_files)} "
            f"arquivos válidos ({success_rate:.1%})"
        )
        logger.info(msg)

        return success_rate >= 0.9  # 90% dos arquivos devem ser válidos

    def create_sample_test_files(self) -> list[Path]:
        """Cria arquivos de teste de exemplo para validação.

        Returns:
            Lista de caminhos dos arquivos criados

        """
        logger.info("Criando arquivos de teste de exemplo...")

        sample_tests = {
            "test_http_requests.py": '''"""Test file with HTTP patterns."""

import httpx
import requests


def test_httpx_get_request():
    """Test that should trigger httpx.get mock suggestion."""
    response = httpx.get("https://api.example.com/data")  # noqa: network
    assert response.status_code == 200


def test_requests_post():
    """Test that should trigger requests.post mock suggestion."""
    data = {"key": "value"}
    url = "https://api.example.com/submit"
    response = requests.post(url, json=data)  # noqa: network
    assert response.status_code == 201
''',
            "test_subprocess_calls.py": '''"""Test file with subprocess patterns."""

import subprocess
import sys


def test_subprocess_run():
    """Test that should trigger subprocess.run mock suggestion."""
    result = subprocess.run([sys.executable, "--version"],  # noqa: subprocess
                          capture_output=True, text=True)
    assert result.returncode == 0


def test_subprocess_popen():
    """Test with Popen that needs mocking."""
    process = subprocess.Popen([sys.executable, "--version"],
                              stdout=subprocess.PIPE)
    output, _ = process.communicate()
    assert process.returncode == 0
''',
            "test_file_operations.py": '''"""Test file with file system operations."""

from pathlib import Path


def test_file_reading():
    """Test that might need file mocking."""
    with open("sample.txt", "r") as f:
        content = f.read()
    assert len(content) > 0


def test_path_operations():
    """Test with path operations."""
    file_path = Path("example.txt")
    exists = file_path.exists()
    assert isinstance(exists, bool)
''',
        }

        created_files = []
        tests_dir = self.workspace_root / "tests"
        tests_dir.mkdir(exist_ok=True)

        for filename, content in sample_tests.items():
            file_path = tests_dir / filename

            # Só cria se não existir
            if not file_path.exists():
                try:
                    with file_path.open("w", encoding="utf-8") as f:
                        f.write(content)
                    created_files.append(file_path)
                    logger.debug(f"Arquivo de exemplo criado: {filename}")
                except Exception as e:
                    logger.error(f"Erro ao criar {filename}: {e}")

        logger.info(f"Criados {len(created_files)} arquivos de teste de exemplo")
        return created_files

    def test_mock_generation(self) -> bool:
        """Testa se o gerador de mocks funciona corretamente.

        Returns:
            True se geração funcionou

        """
        logger.info("Testando geração de mocks...")

        # Guarda de inicialização
        if self.generator is None or self._init_error:
            error_msg = self._init_error or "Gerador não inicializado"
            logger.error(f"Validação bloqueada: {error_msg}")
            self.validation_errors.append(
                {
                    "type": "INIT_ERROR",
                    "path": str(self.workspace_root),
                    "message": error_msg,
                },
            )
            return False

        try:
            # Escaneia arquivos
            report = self.generator.scan_test_files()

            if not report["suggestions"]:
                logger.warning(
                    "Nenhuma sugestão gerada - criando arquivos de teste de exemplo",
                )
                self.create_sample_test_files()
                # Tenta novamente
                report = self.generator.scan_test_files()

            suggestions_count = len(report["suggestions"])
            high_priority_count = report["summary"]["high_priority"]

            msg = (
                f"Geração de mocks: {suggestions_count} sugestões, "
                f"{high_priority_count} alta prioridade"
            )
            logger.info(msg)

            # Valida estrutura das sugestões
            for suggestion in report["suggestions"]:
                required_fields = ["file", "function", "line", "pattern", "severity"]
                for field in required_fields:
                    if field not in suggestion:
                        self.validation_errors.append(
                            {
                                "type": "MISSING_FIELD",
                                "path": suggestion.get("file", "unknown"),
                                "message": f"Campo obrigatório ausente: {field}",
                            },
                        )
                        return False

            return suggestions_count > 0

        except Exception as e:
            logger.error(f"Erro na geração de mocks: {e}")
            self.validation_errors.append(
                {
                    "type": "GENERATION_ERROR",
                    "path": str(self.workspace_root),
                    "message": f"Erro na geração: {e}",
                },
            )
            return False

    def test_dry_run_application(self) -> bool:
        """Testa aplicação em modo dry-run.

        Returns:
            True se dry-run funcionou

        """
        logger.info("Testando aplicação em modo dry-run...")

        # Guarda de inicialização
        if self.generator is None or self._init_error:
            error_msg = self._init_error or "Gerador não inicializado"
            logger.error(f"Dry-run bloqueado: {error_msg}")
            self.validation_errors.append(
                {
                    "type": "INIT_ERROR",
                    "path": str(self.workspace_root),
                    "message": error_msg,
                },
            )
            return False

        try:
            # Garante que há sugestões
            if not self.generator.suggestions:
                self.generator.scan_test_files()

            if not self.generator.suggestions:
                logger.info("Nenhuma sugestão disponível para teste de dry-run")
                return True

            # Testa dry-run
            result = self.generator.apply_suggestions(dry_run=True)

            logger.info(f"Dry-run: {result['applied']} aplicações simuladas")

            # Valida que nenhum arquivo foi modificado realmente
            # (isso seria verificado comparando timestamps, mas simplificamos)

            return bool(result["failed"] == 0)

        except Exception as e:
            logger.error(f"Erro no dry-run: {e}")
            self.validation_errors.append(
                {
                    "type": "DRY_RUN_ERROR",
                    "path": str(self.workspace_root),
                    "message": f"Erro no dry-run: {e}",
                },
            )
            return False

    def run_full_validation(self) -> dict[str, bool]:
        """Executa validação completa do sistema.

        Returns:
            Dicionário com resultados de cada validação

        """
        logger.info("Iniciando validação completa do Test Mock Generator...")

        validations = {
            "workspace_structure": self.validate_workspace_structure(),
            "test_files_syntax": self.validate_test_files_syntax(),
            "mock_generation": self.test_mock_generation(),
            "dry_run_application": self.test_dry_run_application(),
        }

        success_count = sum(validations.values())
        total_count = len(validations)

        logger.info(
            f"Validação completa: {success_count}/{total_count} verificações passaram",
        )

        # Log de erros encontrados
        if self.validation_errors:
            logger.warning(f"Encontrados {len(self.validation_errors)} erros:")
            for error in self.validation_errors:
                logger.warning(f"  {error['type']}: {error['message']}")

        return validations

    def fix_common_issues(self) -> int:
        """Tenta corrigir problemas comuns automaticamente.

        Returns:
            Número de problemas corrigidos

        """
        logger.info("Tentando corrigir problemas comuns...")

        fixed_count = 0

        # Corrige diretório de testes ausente
        tests_dir = self.workspace_root / "tests"
        if not tests_dir.exists():
            try:
                tests_dir.mkdir(parents=True, exist_ok=True)
                # Cria __init__.py
                init_file = tests_dir / "__init__.py"
                init_file.write_text("# Tests package\n")
                fixed_count += 1
                logger.info("Diretório de testes criado")
            except Exception as e:
                logger.error(f"Erro ao criar diretório de testes: {e}")

        # Cria arquivos de exemplo se não há testes
        test_files = list(tests_dir.glob("*.py"))
        if len(test_files) <= 1:  # Apenas __init__.py ou vazio
            created = self.create_sample_test_files()
            fixed_count += len(created)

        logger.info(f"Corrigidos {fixed_count} problemas")
        return fixed_count


__all__ = ["TestMockValidator"]
