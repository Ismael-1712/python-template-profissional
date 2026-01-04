"""Testes para o TDD Guardian - Garante que código novo tenha testes correspondentes.

Este módulo testa o mecanismo que impõe a presença de testes para qualquer
arquivo Python adicionado em src/. Segue a filosofia TDD: testes primeiro.
"""

from pathlib import Path

import pytest

from scripts.hooks.tdd_guardian import TDDGuardian


class TestTDDGuardian:
    """Suite de testes para o TDD Guardian."""

    @pytest.fixture
    def guardian(self) -> TDDGuardian:
        """Fixture que retorna uma instância do TDDGuardian."""
        return TDDGuardian()

    def test_src_main_requires_test_main(self, guardian: TDDGuardian) -> None:
        """Testa o mapeamento de src/main.py para tests/test_main.py.

        DADO um arquivo src/main.py
        QUANDO verificamos a existência do teste correspondente
        ENTÃO deve mapear para tests/test_main.py
        """
        source_file = Path("src/main.py")
        expected_test = Path("tests/test_main.py")

        result = guardian.get_test_path(source_file)

        assert result == expected_test, f"Esperava {expected_test}, obteve {result}"

    def test_src_core_utils_requires_test_core_utils(
        self, guardian: TDDGuardian
    ) -> None:
        """Testa o mapeamento de módulos aninhados.

        DADO um arquivo src/core/utils.py
        QUANDO verificamos a existência do teste correspondente
        ENTÃO deve mapear para tests/core/test_utils.py
        """
        source_file = Path("src/core/utils.py")
        expected_test = Path("tests/core/test_utils.py")

        result = guardian.get_test_path(source_file)

        assert result == expected_test, f"Esperava {expected_test}, obteve {result}"

    def test_src_init_should_be_ignored(self, guardian: TDDGuardian) -> None:
        """Testa que arquivos __init__.py são ignorados automaticamente.

        DADO um arquivo src/__init__.py
        QUANDO verificamos se deve ser ignorado
        ENTÃO deve retornar True (arquivos __init__.py são ignorados)
        """
        source_file = Path("src/__init__.py")

        result = guardian.should_ignore(source_file)

        assert result is True, f"Arquivo {source_file} deveria ser ignorado"

    def test_readme_should_be_ignored(self, guardian: TDDGuardian) -> None:
        """Testa que arquivos não-Python são ignorados.

        DADO um arquivo README.md
        QUANDO verificamos se deve ser ignorado
        ENTÃO deve retornar True (arquivos não-Python são ignorados)
        """
        source_file = Path("README.md")

        result = guardian.should_ignore(source_file)

        assert result is True, f"Arquivo {source_file} deveria ser ignorado"

    def test_src_nested_module_requires_test(self, guardian: TDDGuardian) -> None:
        """Testa o mapeamento de módulos profundamente aninhados.

        DADO um arquivo src/app/services/auth.py
        QUANDO verificamos a existência do teste correspondente
        ENTÃO deve mapear para tests/app/services/test_auth.py
        """
        source_file = Path("src/app/services/auth.py")
        expected_test = Path("tests/app/services/test_auth.py")

        result = guardian.get_test_path(source_file)

        assert result == expected_test, f"Esperava {expected_test}, obteve {result}"

    def test_non_src_file_should_be_ignored(self, guardian: TDDGuardian) -> None:
        """Testa que arquivos fora de src/ são ignorados.

        DADO um arquivo fora de src/ (ex: scripts/utils.py)
        QUANDO verificamos se deve ser ignorado
        ENTÃO deve retornar True (apenas src/ requer testes)
        """
        source_file = Path("scripts/utils.py")

        result = guardian.should_ignore(source_file)

        assert result is True, f"Arquivo {source_file} deveria ser ignorado"

    def test_validation_fails_when_test_missing(
        self,
        guardian: TDDGuardian,
        tmp_path: Path,
    ) -> None:
        """Testa que validação falha quando teste está faltando.

        DADO um arquivo src/new_module.py sem teste correspondente
        QUANDO executamos a validação
        ENTÃO deve retornar False e listar o arquivo faltante
        """
        # Cria um arquivo temporário em src/
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        source_file = src_dir / "new_module.py"
        source_file.write_text("# New module")

        # Cria instância com project_root correto
        temp_guardian = TDDGuardian(project_root=tmp_path)

        # Executa validação
        result, missing = temp_guardian.validate([source_file])

        assert result is False, "Validação deveria falhar quando teste está faltando"
        assert len(missing) == 1, "Deveria ter exatamente 1 arquivo sem teste"
        assert source_file in missing, (
            f"{source_file} deveria estar na lista de faltantes"
        )

    def test_validation_succeeds_when_test_exists(
        self,
        guardian: TDDGuardian,
        tmp_path: Path,
    ) -> None:
        """Testa que validação passa quando teste existe.

        DADO um arquivo src/existing.py com teste correspondente
        QUANDO executamos a validação
        ENTÃO deve retornar True (sem arquivos faltantes)
        """
        # Cria estrutura src/ e tests/
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        source_file = src_dir / "existing.py"
        source_file.write_text("# Existing module")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_existing.py"
        test_file.write_text("# Test for existing module")

        # Cria instância com project_root correto
        temp_guardian = TDDGuardian(project_root=tmp_path)

        # Executa validação
        result, missing = temp_guardian.validate([source_file])

        assert result is True, "Validação deveria passar quando teste existe"
        assert len(missing) == 0, "Não deveria ter arquivos faltantes"

    def test_validation_ignores_init_files(
        self,
        guardian: TDDGuardian,
        tmp_path: Path,
    ) -> None:
        """Testa que validação ignora arquivos __init__.py.

        DADO um arquivo src/__init__.py sem teste
        QUANDO executamos a validação
        ENTÃO deve retornar True (arquivos __init__.py são ignorados)
        """
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        init_file = src_dir / "__init__.py"
        init_file.write_text("# Init file")

        # Cria instância com project_root correto
        temp_guardian = TDDGuardian(project_root=tmp_path)

        result, missing = temp_guardian.validate([init_file])

        assert result is True, "Validação deveria passar para __init__.py"
        assert len(missing) == 0, "__init__.py não deveria requerer teste"
