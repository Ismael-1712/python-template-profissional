"""Testes unitários para o Visibility Guardian Scanner."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from scripts.core.guardian.models import ConfigType
from scripts.core.guardian.scanner import ConfigScanner, EnvVarVisitor

# Código Python de exemplo para testes
SAMPLE_CODE_WITH_ENVVARS = '''
import os

def get_database_config():
    """Função que lê configurações do ambiente."""
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD", "secret")
    database = os.environ["DB_NAME"]
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
    }

def get_api_key():
    """Função que lê API key."""
    return os.getenv("API_KEY")
'''

SAMPLE_CODE_WITHOUT_ENVVARS = '''
def calculate_sum(a, b):
    """Função simples sem configurações."""
    return a + b
'''

SAMPLE_CODE_WITH_SYNTAX_ERROR = '''
def broken_function(
    """Função com erro de sintaxe."""
    return "broken"
'''


class TestEnvVarVisitor:
    """Testes para o EnvVarVisitor."""

    def test_visitor_detects_os_getenv(self, tmp_path: Path) -> None:
        """Testa detecção de os.getenv()."""
        code = 'import os\nvalue = os.getenv("TEST_VAR")'
        tree = ast.parse(code)

        visitor = EnvVarVisitor(tmp_path / "test.py")
        visitor.visit(tree)

        assert len(visitor.findings) == 1
        finding = visitor.findings[0]
        assert finding.key == "TEST_VAR"
        assert finding.config_type == ConfigType.ENV_VAR
        assert finding.required is True
        assert finding.default_value is None

    def test_visitor_detects_os_getenv_with_default(
        self,
        tmp_path: Path,
    ) -> None:
        """Testa detecção de os.getenv() com valor padrão."""
        code = 'import os\nvalue = os.getenv("TEST_VAR", "default_value")'
        tree = ast.parse(code)

        visitor = EnvVarVisitor(tmp_path / "test.py")
        visitor.visit(tree)

        assert len(visitor.findings) == 1
        finding = visitor.findings[0]
        assert finding.key == "TEST_VAR"
        assert finding.required is False
        assert finding.default_value == "default_value"

    def test_visitor_detects_environ_get(self, tmp_path: Path) -> None:
        """Testa detecção de os.environ.get()."""
        code = 'import os\nvalue = os.environ.get("TEST_VAR")'
        tree = ast.parse(code)

        visitor = EnvVarVisitor(tmp_path / "test.py")
        visitor.visit(tree)

        assert len(visitor.findings) == 1
        finding = visitor.findings[0]
        assert finding.key == "TEST_VAR"
        assert finding.config_type == ConfigType.ENV_VAR
        assert finding.required is True

    def test_visitor_detects_environ_subscript(
        self,
        tmp_path: Path,
    ) -> None:
        """Testa detecção de os.environ["VAR"]."""
        code = 'import os\nvalue = os.environ["TEST_VAR"]'
        tree = ast.parse(code)

        visitor = EnvVarVisitor(tmp_path / "test.py")
        visitor.visit(tree)

        assert len(visitor.findings) == 1
        finding = visitor.findings[0]
        assert finding.key == "TEST_VAR"
        assert finding.config_type == ConfigType.ENV_VAR
        assert finding.required is True  # Subscript sempre é required

    def test_visitor_tracks_function_context(self, tmp_path: Path) -> None:
        """Testa rastreamento de contexto da função."""
        code = """
import os

def my_function():
    value = os.getenv("TEST_VAR")
    return value
"""
        tree = ast.parse(code)

        visitor = EnvVarVisitor(tmp_path / "test.py")
        visitor.visit(tree)

        assert len(visitor.findings) == 1
        assert visitor.findings[0].context == "my_function"

    def test_visitor_finds_multiple_vars(self, tmp_path: Path) -> None:
        """Testa detecção de múltiplas variáveis."""
        tree = ast.parse(SAMPLE_CODE_WITH_ENVVARS)

        visitor = EnvVarVisitor(tmp_path / "test.py")
        visitor.visit(tree)

        # Deve encontrar: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, API_KEY  # noqa: E501
        assert len(visitor.findings) == 6

        var_names = {f.key for f in visitor.findings}
        expected_vars = {
            "DB_HOST",
            "DB_PORT",
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME",
            "API_KEY",
        }
        assert var_names == expected_vars


class TestConfigScanner:
    """Testes para o ConfigScanner."""

    def test_scan_file_with_envvars(self, tmp_path: Path) -> None:
        """Testa scan de arquivo com variáveis de ambiente."""
        test_file = tmp_path / "config.py"
        test_file.write_text(SAMPLE_CODE_WITH_ENVVARS)

        scanner = ConfigScanner()
        findings = scanner.scan_file(test_file)

        assert len(findings) == 6

        # Verifica se todas as variáveis foram encontradas
        var_names = {f.key for f in findings}
        assert "DB_HOST" in var_names
        assert "DB_PORT" in var_names
        assert "API_KEY" in var_names

    def test_scan_file_without_envvars(self, tmp_path: Path) -> None:
        """Testa scan de arquivo sem variáveis de ambiente."""
        test_file = tmp_path / "simple.py"
        test_file.write_text(SAMPLE_CODE_WITHOUT_ENVVARS)

        scanner = ConfigScanner()
        findings = scanner.scan_file(test_file)

        assert len(findings) == 0

    def test_scan_file_with_syntax_error(self, tmp_path: Path) -> None:
        """Testa comportamento com arquivo com erro de sintaxe."""
        test_file = tmp_path / "broken.py"
        test_file.write_text(SAMPLE_CODE_WITH_SYNTAX_ERROR)

        scanner = ConfigScanner()

        with pytest.raises(SyntaxError):
            scanner.scan_file(test_file)

    def test_scan_file_not_found(self) -> None:
        """Testa comportamento com arquivo inexistente."""
        scanner = ConfigScanner()

        with pytest.raises(FileNotFoundError):
            scanner.scan_file(Path("/nonexistent/file.py"))

    def test_scan_project(self, tmp_path: Path) -> None:
        """Testa scan de projeto inteiro."""
        # Cria estrutura de diretórios
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        # Cria arquivos de teste
        (tmp_path / "src" / "config.py").write_text(
            SAMPLE_CODE_WITH_ENVVARS,
        )
        (tmp_path / "src" / "utils.py").write_text(
            SAMPLE_CODE_WITHOUT_ENVVARS,
        )
        (tmp_path / "tests" / "test_config.py").write_text(
            'import os\ntest_var = os.getenv("TEST_ENV")',
        )

        scanner = ConfigScanner()
        result = scanner.scan_project(tmp_path)

        assert result.files_scanned == 3
        assert result.total_findings == 7  # 6 do config.py + 1 do test_config.py
        assert result.scan_duration_ms > 0
        assert not result.has_errors()

    def test_scan_project_ignores_pycache(self, tmp_path: Path) -> None:
        """Testa que __pycache__ é ignorado."""
        # Cria diretório __pycache__
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()

        # Cria arquivo em __pycache__ (não deve ser escaneado)
        (pycache / "cached.py").write_text(
            'import os\nos.getenv("SHOULD_BE_IGNORED")',
        )

        # Cria arquivo normal
        (tmp_path / "normal.py").write_text(
            'import os\nos.getenv("SHOULD_BE_FOUND")',
        )

        scanner = ConfigScanner()
        result = scanner.scan_project(tmp_path)

        # Deve encontrar apenas o arquivo normal
        assert result.files_scanned == 1
        assert result.total_findings == 1
        assert result.findings[0].key == "SHOULD_BE_FOUND"

    def test_scan_result_properties(self, tmp_path: Path) -> None:
        """Testa propriedades de ScanResult."""
        test_file = tmp_path / "config.py"
        test_file.write_text(SAMPLE_CODE_WITH_ENVVARS)

        scanner = ConfigScanner()
        result = scanner.scan_project(tmp_path)

        assert result.total_findings == 6
        assert len(result.env_vars) == 6
        assert len(result.cli_args) == 0

        summary = result.summary()
        assert "6 configurações" in summary
        assert "1 arquivos" in summary

    def test_scan_handles_errors_gracefully(self, tmp_path: Path) -> None:
        """Testa que erros são capturados e não param o scan."""
        # Cria arquivo válido
        (tmp_path / "valid.py").write_text(
            'import os\nos.getenv("VALID_VAR")',
        )

        # Cria arquivo com erro de sintaxe
        (tmp_path / "broken.py").write_text(SAMPLE_CODE_WITH_SYNTAX_ERROR)

        scanner = ConfigScanner()
        result = scanner.scan_project(tmp_path)

        # Deve ter escaneado o arquivo válido
        assert result.files_scanned == 1
        assert result.total_findings == 1

        # Deve ter registrado o erro
        assert result.has_errors()
        assert len(result.errors) == 1
        assert "broken.py" in result.errors[0]


class TestConfigFindingModel:
    """Testes para o modelo ConfigFinding."""

    def test_config_finding_str_representation(self, tmp_path: Path) -> None:
        """Testa representação string de ConfigFinding."""
        from scripts.core.guardian.models import ConfigFinding

        finding = ConfigFinding(
            key="DB_HOST",
            config_type=ConfigType.ENV_VAR,
            source_file=tmp_path / "config.py",
            line_number=10,
            default_value="localhost",
            required=False,
        )

        str_repr = str(finding)
        assert "DB_HOST" in str_repr
        assert "config.py:10" in str_repr
        assert "localhost" in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
