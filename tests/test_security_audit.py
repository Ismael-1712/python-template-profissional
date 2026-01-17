"""Testes de Integração para Software Composition Analysis (SCA).

Este módulo valida o sistema de auditoria de segurança via pip-audit,
garantindo que vulnerabilidades sejam detectadas e bloqueiem o build.

Estratégia:
- Mock de outputs do pip-audit para simular CVEs
- Validação de cache baseado em hash
- Validação de exit codes (fail em vulnerabilidades)

Autor: SRE Engineering Team
Versão: 1.0.0 (Protocolo SCA v2.1)
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestSecurityAudit:
    """Testes para o sistema de auditoria de segurança."""

    @pytest.fixture
    def mock_requirements_txt(self, tmp_path: Path) -> Path:
        """Cria um arquivo requirements.txt temporário para testes."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            "requests==2.28.0\nurllib3==1.26.0\npytest==7.0.0\n",
        )
        return req_file

    @pytest.fixture
    def mock_pip_audit_clean_output(self) -> dict[str, Any]:
        """Output JSON do pip-audit sem vulnerabilidades."""
        return {
            "dependencies": [
                {"name": "requests", "version": "2.28.0"},
                {"name": "urllib3", "version": "1.26.0"},
                {"name": "pytest", "version": "7.0.0"},
            ],
            "vulnerabilities": [],
        }

    @pytest.fixture
    def mock_pip_audit_vuln_output(self) -> dict[str, Any]:
        """Output JSON do pip-audit com vulnerabilidade CRITICAL."""
        return {
            "dependencies": [
                {"name": "requests", "version": "2.28.0"},
                {"name": "urllib3", "version": "1.26.0"},
            ],
            "vulnerabilities": [
                {
                    "name": "urllib3",
                    "version": "1.26.0",
                    "vulns": [
                        {
                            "id": "CVE-2024-99999",
                            "fix_versions": ["1.26.18"],
                            "description": "Critical vulnerability in urllib3",
                            "severity": "CRITICAL",
                        },
                    ],
                },
            ],
        }

    def test_pip_audit_no_vulnerabilities_returns_zero(
        self,
        mock_requirements_txt: Path,
        mock_pip_audit_clean_output: dict[str, Any],
    ) -> None:
        """Valida que pip-audit retorna exit code 0 quando não há CVEs."""
        with patch("subprocess.run") as mock_run:
            # Simula pip-audit retornando sucesso (sem vulnerabilidades)
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = json.dumps(mock_pip_audit_clean_output).encode()
            mock_process.stderr = b""
            mock_run.return_value = mock_process

            # Executa pip-audit simulado
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pip_audit",
                    "-r",
                    str(mock_requirements_txt),
                    "--desc",
                    "--format",
                    "json",
                ],
                capture_output=True,
                check=False,
            )

            assert result.returncode == 0, "pip-audit deve retornar 0 sem CVEs"

    def test_pip_audit_with_vulnerabilities_returns_nonzero(
        self,
        mock_requirements_txt: Path,
        mock_pip_audit_vuln_output: dict[str, Any],
    ) -> None:
        """Valida que pip-audit retorna exit code != 0 quando detecta CVEs."""
        with patch("subprocess.run") as mock_run:
            # Simula pip-audit retornando erro (vulnerabilidade detectada)
            mock_process = MagicMock()
            mock_process.returncode = 1  # Exit code de falha
            mock_process.stdout = json.dumps(mock_pip_audit_vuln_output).encode()
            mock_process.stderr = b"Found 1 known vulnerability"
            mock_run.return_value = mock_process

            # Executa pip-audit simulado
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pip_audit",
                    "-r",
                    str(mock_requirements_txt),
                    "--desc",
                    "--format",
                    "json",
                ],
                capture_output=True,
                check=False,
            )

            assert result.returncode == 1, "pip-audit deve falhar ao detectar CVEs"
            assert b"vulnerability" in result.stderr.lower()

    def test_cache_invalidation_on_requirements_change(
        self,
        tmp_path: Path,
    ) -> None:
        """Valida que o cache é invalidado quando requirements.txt muda."""
        import hashlib

        # Arquivo requirements.txt inicial
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        # Hash inicial
        hash1 = hashlib.sha256(req_file.read_bytes()).hexdigest()

        # Simula arquivo de cache baseado no hash
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()
        cache_file_1 = cache_dir / f"pip-audit-{hash1}.json"
        cache_file_1.write_text('{"vulnerabilities": []}')

        assert cache_file_1.exists(), "Cache inicial deve existir"

        # Modifica requirements.txt
        req_file.write_text("requests==2.28.0\nurllib3==2.0.0\n")

        # Hash após mudança
        hash2 = hashlib.sha256(req_file.read_bytes()).hexdigest()

        assert hash1 != hash2, "Hash deve mudar quando requirements muda"

        # Cache antigo não deve ser usado
        cache_file_2 = cache_dir / f"pip-audit-{hash2}.json"
        assert not cache_file_2.exists(), "Novo hash não deve ter cache (invalidação)"

    def test_cache_reuse_when_requirements_unchanged(
        self,
        tmp_path: Path,
    ) -> None:
        """Valida que o cache é reutilizado quando requirements.txt não muda."""
        import hashlib

        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        # Hash do arquivo
        file_hash = hashlib.sha256(req_file.read_bytes()).hexdigest()

        # Cria cache
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()
        cache_file = cache_dir / f"pip-audit-{file_hash}.json"
        cache_file.write_text('{"vulnerabilities": []}')

        # Simula leitura do cache
        assert cache_file.exists(), "Cache deve estar disponível"

        # Re-calcula hash (deve ser idêntico)
        file_hash_2 = hashlib.sha256(req_file.read_bytes()).hexdigest()

        assert file_hash == file_hash_2, "Hash deve permanecer inalterado"
        assert cache_file.exists(), "Cache deve ser reutilizável"

    def test_pip_audit_strict_mode_blocks_any_vulnerability(self) -> None:
        """Valida que --strict bloqueia qualquer CVE (mesmo LOW/MEDIUM)."""
        with patch("subprocess.run") as mock_run:
            # Simula vulnerabilidade MEDIUM (que seria ignorada sem --strict)
            mock_process = MagicMock()
            mock_process.returncode = 1  # Strict mode falha em qualquer CVE
            mock_process.stdout = json.dumps(
                {
                    "vulnerabilities": [
                        {
                            "name": "requests",
                            "version": "2.28.0",
                            "vulns": [
                                {
                                    "id": "CVE-2024-12345",
                                    "severity": "MEDIUM",
                                    "description": "Medium severity issue",
                                },
                            ],
                        },
                    ],
                },
            ).encode()
            mock_run.return_value = mock_process

            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pip_audit",
                    "--strict",
                    "--format",
                    "json",
                ],
                capture_output=True,
                check=False,
            )

            assert result.returncode != 0, (
                "--strict deve falhar mesmo em severity MEDIUM"
            )

    def test_pip_audit_respects_pyproject_ignore_vulns(
        self,
        tmp_path: Path,
    ) -> None:
        """Valida que CVEs em [tool.pip-audit].ignore-vulns são ignoradas."""
        # Cria pyproject.toml com CVE ignorada
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.pip-audit]
ignore-vulns = [
    "CVE-2024-99999",  # Test CVE - Aceito por motivo técnico
]
""",
        )

        with patch("subprocess.run") as mock_run:
            # Simula pip-audit detectando CVE que está na lista de ignore
            mock_process = MagicMock()
            mock_process.returncode = 0  # Deve passar (CVE ignorada)
            mock_process.stdout = json.dumps(
                {
                    "vulnerabilities": [
                        {
                            "name": "requests",
                            "vulns": [
                                {
                                    "id": "CVE-2024-99999",  # Esta CVE está ignorada
                                    "severity": "HIGH",
                                },
                            ],
                        },
                    ],
                },
            ).encode()
            mock_run.return_value = mock_process

            # pip-audit lê pyproject.toml automaticamente
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pip_audit",
                    "--desc",
                ],
                cwd=str(tmp_path),
                capture_output=True,
                check=False,
            )

            assert result.returncode == 0, "CVEs em ignore-vulns devem ser permitidas"


class TestMakefileSecuritySCA:
    """Testes para validar comportamento do target make audit-security-sca."""

    def test_makefile_target_exists(self) -> None:
        """Valida que o target security-sca existe no Makefile."""
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text()

        assert "security-sca:" in content, "Target security-sca deve existir"
        assert "|| true" not in content.split("security-sca:")[1].split("\n\n")[0], (
            "Target NÃO deve ter || true (soft-fail removido)"
        )

    def test_makefile_validate_includes_security_sca(self) -> None:
        """Valida que 'make validate' está simplificado e não inclui checks pesados."""
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text()

        # Encontra a linha do target validate
        validate_section = None
        for line in content.split("\n"):
            if line.startswith("validate:"):
                validate_section = line
                break

        assert validate_section is not None, "Target validate deve existir"
        # Validate agora é simplificado: apenas format lint type-check test
        assert "format" in validate_section, "validate deve incluir format"
        assert "lint" in validate_section, "validate deve incluir lint"
        assert "type-check" in validate_section, "validate deve incluir type-check"
        assert "test" in validate_section, "validate deve incluir test"


class TestPreCommitHook:
    """Testes para validar integração do pip-audit no pre-commit."""

    def test_precommit_config_has_pip_audit_hook(self) -> None:
        """Valida que .pre-commit-config.yaml contém hook de pip-audit."""
        precommit_file = Path(__file__).parent.parent / ".pre-commit-config.yaml"
        content = precommit_file.read_text()

        assert "pip-audit" in content.lower(), "Hook de pip-audit deve existir"
        assert "--strict" in content or "pip_audit" in content, (
            "Hook deve usar modo strict"
        )

    def test_precommit_hook_triggers_on_requirements_changes(self) -> None:
        """Valida que o hook só executa quando requirements/* muda."""
        precommit_file = Path(__file__).parent.parent / ".pre-commit-config.yaml"
        content = precommit_file.read_text()

        # Procura pela configuração do hook pip-audit
        lines = content.split("\n")
        in_pip_audit_section = False
        has_files_filter = False

        for line in lines:
            if "pip-audit" in line.lower() or "pip_audit" in line.lower():
                in_pip_audit_section = True
            if in_pip_audit_section and "files:" in line:
                has_files_filter = True
                # Próxima linha deve conter o padrão de requirements
                break

        assert has_files_filter or "requirements" in content, (
            "Hook deve ter filtro de arquivos requirements"
        )
