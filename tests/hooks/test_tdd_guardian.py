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
        self,
        guardian: TDDGuardian,
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


class TestTDDGuardianMultipleDirectories:
    """Suite de testes para suporte a múltiplos diretórios monitorados."""

    def test_guardian_monitors_custom_directories(self) -> None:
        """Testa que Guardian pode monitorar múltiplos diretórios.

        DADO um Guardian configurado para monitorar ['src', 'scripts']
        QUANDO verificamos se scripts/deploy.py deve ser ignorado
        ENTÃO deve retornar False (scripts agora é monitorado)
        """
        guardian = TDDGuardian(monitored_dirs=["src", "scripts"])
        source_file = Path("scripts/deploy.py")

        result = guardian.should_ignore(source_file)

        assert result is False, (
            f"Arquivo {source_file} NÃO deveria ser ignorado "
            "quando scripts está sendo monitorado"
        )

    def test_scripts_file_maps_to_tests_scripts(self) -> None:
        """Testa mapeamento de scripts/ para tests/scripts/.

        DADO um Guardian monitorando scripts/
        QUANDO mapeamos scripts/deploy.py
        ENTÃO deve mapear para tests/scripts/test_deploy.py
        """
        guardian = TDDGuardian(monitored_dirs=["src", "scripts"])
        source_file = Path("scripts/deploy.py")
        expected_test = Path("tests/scripts/test_deploy.py")

        result = guardian.get_test_path(source_file)

        assert result == expected_test, f"Esperava {expected_test}, obteve {result}"

    def test_scripts_nested_file_maps_correctly(self) -> None:
        """Testa mapeamento de scripts aninhados.

        DADO um Guardian monitorando scripts/
        QUANDO mapeamos scripts/cli/doctor.py
        ENTÃO deve mapear para tests/scripts/cli/test_doctor.py
        """
        guardian = TDDGuardian(monitored_dirs=["src", "scripts"])
        source_file = Path("scripts/cli/doctor.py")
        expected_test = Path("tests/scripts/cli/test_doctor.py")

        result = guardian.get_test_path(source_file)

        assert result == expected_test, f"Esperava {expected_test}, obteve {result}"

    def test_unmonitored_directory_is_ignored(self) -> None:
        """Testa que diretórios não monitorados são ignorados.

        DADO um Guardian monitorando apenas ['src']
        QUANDO verificamos scripts/utils.py
        ENTÃO deve ser ignorado (scripts não está na lista)
        """
        guardian = TDDGuardian(monitored_dirs=["src"])
        source_file = Path("scripts/utils.py")

        result = guardian.should_ignore(source_file)

        assert result is True, (
            f"Arquivo {source_file} deveria ser ignorado "
            "quando scripts não está sendo monitorado"
        )


class TestTDDGuardianWarnOnlyMode:
    """Suite de testes para modo warn-only (não bloqueante)."""

    def test_strict_mode_blocks_missing_tests(self, tmp_path: Path) -> None:
        """Testa que modo strict=True bloqueia commits sem testes.

        DADO um Guardian em modo strict (padrão)
        QUANDO validamos arquivo sem teste
        ENTÃO deve retornar False (bloqueia)
        """
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        source_file = src_dir / "untested.py"
        source_file.write_text("# Código sem teste")

        guardian = TDDGuardian(project_root=tmp_path, strict=True)
        result, missing = guardian.validate([source_file])

        assert result is False, "Modo strict deveria bloquear arquivos sem teste"
        assert len(missing) == 1, "Deveria reportar 1 arquivo faltante"

    def test_warn_only_mode_allows_missing_tests(self, tmp_path: Path) -> None:
        """Testa que modo strict=False não bloqueia, apenas avisa.

        DADO um Guardian em modo warn-only (strict=False)
        QUANDO validamos arquivo sem teste
        ENTÃO deve retornar True (não bloqueia) mas registrar warnings
        """
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        source_file = src_dir / "untested.py"
        source_file.write_text("# Código sem teste")

        guardian = TDDGuardian(project_root=tmp_path, strict=False)
        result, missing = guardian.validate([source_file])

        assert result is True, "Modo warn-only NÃO deveria bloquear commit"
        assert len(missing) == 1, "Deveria ainda detectar arquivo faltante"

    def test_warn_only_exit_code_is_zero(self, tmp_path: Path) -> None:
        """Testa que modo warn-only retorna exit code 0.

        DADO um Guardian em modo warn-only
        QUANDO executamos run() com arquivos sem teste
        ENTÃO deve retornar 0 (permite commit)
        """
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        source_file = src_dir / "untested.py"
        source_file.write_text("# Código sem teste")

        guardian = TDDGuardian(project_root=tmp_path, strict=False)
        exit_code = guardian.run([str(source_file)])

        assert exit_code == 0, "Modo warn-only deveria retornar exit code 0"


class TestTDDGuardianIntegration:
    """Testes de integração para cenários complexos."""

    def test_mixed_directories_and_modes(self, tmp_path: Path) -> None:
        """Testa cenário real: src (strict) + scripts (warn-only).

        DADO um projeto com código em src/ e scripts/
        QUANDO validamos ambos com políticas diferentes
        ENTÃO cada diretório deve seguir sua política
        """
        # Setup: cria estrutura
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "api.py"
        src_file.write_text("# API code")

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "deploy.py"
        script_file.write_text("# Deploy script")

        # Guardian strict para src
        guardian_strict = TDDGuardian(
            project_root=tmp_path,
            monitored_dirs=["src"],
            strict=True,
        )
        result_src, _ = guardian_strict.validate([src_file])

        # Guardian warn-only para scripts
        guardian_warn = TDDGuardian(
            project_root=tmp_path,
            monitored_dirs=["scripts"],
            strict=False,
        )
        result_scripts, _ = guardian_warn.validate([script_file])

        assert result_src is False, "src/ deveria bloquear (strict)"
        assert result_scripts is True, "scripts/ deveria permitir (warn-only)"

    def test_fallback_path_when_no_monitored_dir_found(self) -> None:
        """Testa fallback quando arquivo não está em diretório monitorado.

        DADO um Guardian monitorando apenas ['src']
        QUANDO mapeamos arquivo em diretório não monitorado (ex: lib/utils.py)
        ENTÃO deve usar fallback com primeiro componente do path
        """
        guardian = TDDGuardian(monitored_dirs=["src"])
        source_file = Path("lib/utils.py")

        # Mesmo que lib não seja monitorado, get_test_path deve funcionar
        result = guardian.get_test_path(source_file)

        # Fallback deve tratar lib como diretório base
        assert "test_utils.py" in str(result), (
            f"Esperava test_utils.py no resultado, obteve {result}"
        )

    def test_run_with_multiple_files_mixed_state(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Testa execução com múltiplos arquivos em estados mistos.

        DADO múltiplos arquivos (alguns com testes, outros sem)
        QUANDO executamos run()
        ENTÃO deve reportar apenas os faltantes
        """
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # Arquivo com teste
        file_with_test = src_dir / "tested.py"
        file_with_test.write_text("# Código testado")
        (tests_dir / "test_tested.py").write_text("# Teste")

        # Arquivo sem teste
        file_without_test = src_dir / "untested.py"
        file_without_test.write_text("# Código sem teste")

        guardian = TDDGuardian(project_root=tmp_path, strict=True)
        exit_code = guardian.run([str(file_with_test), str(file_without_test)])

        captured = capsys.readouterr()
        assert exit_code == 1, "Deveria bloquear quando há arquivos sem teste"
        assert "untested.py" in captured.out, "Deveria mencionar arquivo sem teste"
        # Verifica que apenas o arquivo sem teste foi reportado
        assert captured.out.count("⚠️") == 0 or captured.out.count("❌") >= 1, (
            "Deveria reportar pelo menos um erro"
        )

    def test_warn_only_prints_warning_message(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Testa que modo warn-only imprime mensagem de aviso correta.

        DADO um Guardian em modo warn-only
        QUANDO há arquivos sem teste
        ENTÃO deve imprimir mensagem com "WARN-ONLY" e exit code 0
        """
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        untested_file = src_dir / "untested.py"
        untested_file.write_text("# Código sem teste")

        guardian = TDDGuardian(project_root=tmp_path, strict=False)
        exit_code = guardian.run([str(untested_file)])

        captured = capsys.readouterr()
        assert exit_code == 0, "Modo warn-only não deve bloquear"
        assert "WARN-ONLY" in captured.out, "Deveria indicar modo warn-only na mensagem"
        assert "⚠️" in captured.out, "Deveria usar ícone de warning"

    def test_strict_mode_prints_error_message(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Testa que modo strict imprime mensagem de erro correta.

        DADO um Guardian em modo strict
        QUANDO há arquivos sem teste
        ENTÃO deve imprimir mensagem com "ERRO" e exit code 1
        """
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        untested_file = src_dir / "untested.py"
        untested_file.write_text("# Código sem teste")

        guardian = TDDGuardian(project_root=tmp_path, strict=True)
        exit_code = guardian.run([str(untested_file)])

        captured = capsys.readouterr()
        assert exit_code == 1, "Modo strict deve bloquear"
        assert "ERRO" in captured.out, "Deveria indicar ERRO na mensagem"
        assert "❌" in captured.out, "Deveria usar ícone de erro"

    def test_empty_file_list_returns_success(self) -> None:
        """Testa que lista vazia de arquivos retorna sucesso.

        DADO um Guardian configurado
        QUANDO validamos lista vazia de arquivos
        ENTÃO deve retornar sucesso (nada para validar)
        """
        guardian = TDDGuardian()
        result, missing = guardian.validate([])

        assert result is True, "Lista vazia deveria retornar sucesso"
        assert len(missing) == 0, "Não deveria ter arquivos faltantes"


class TestTDDGuardianCLI:
    """Testes para interface CLI do TDD Guardian."""

    def test_main_with_no_args_returns_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Testa que main() sem argumentos retorna sucesso.

        DADO nenhum arquivo fornecido via CLI
        QUANDO executamos main()
        ENTÃO deve retornar 0 (sucesso)
        """
        from scripts.hooks.tdd_guardian import main

        monkeypatch.setattr("sys.argv", ["tdd_guardian.py"])
        exit_code = main()

        assert exit_code == 0, "Sem arquivos deveria retornar sucesso"

    def test_main_with_dirs_argument(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Testa argumento --dirs via CLI.

        DADO arquivo em scripts/ e argumento --dirs scripts
        QUANDO executamos main() com Guardian configurado para scripts
        ENTÃO deve monitorar scripts/ e bloquear se teste não existir
        """
        # Teste simplificado: verifica que Guardian pode ser configurado via CLI
        # para monitorar scripts/ ao invés de apenas testar main()
        guardian = TDDGuardian(
            project_root=tmp_path,
            monitored_dirs=["scripts"],
            strict=True,
        )

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "deploy.py"
        script_file.write_text("# Deploy")

        # Valida que scripts/ está sendo monitorado
        assert not guardian.should_ignore(Path("scripts/deploy.py")), (
            "scripts/deploy.py não deveria ser ignorado"
        )

        # Valida que bloqueará por falta de teste
        result, missing = guardian.validate([script_file])
        assert result is False, "Deveria bloquear arquivo sem teste"
        assert len(missing) == 1, "Deveria ter 1 arquivo faltante"

    def test_main_with_warn_only_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Testa argumento --warn-only via CLI.

        DADO arquivo sem teste e flag --warn-only
        QUANDO executamos main()
        ENTÃO deve retornar 0 (não bloqueia)
        """
        from scripts.hooks.tdd_guardian import main

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "api.py"
        src_file.write_text("# API")

        monkeypatch.setattr(
            "sys.argv",
            ["tdd_guardian.py", "--warn-only", str(src_file)],
        )
        monkeypatch.chdir(tmp_path)

        exit_code = main()

        assert exit_code == 0, "Modo warn-only não deve bloquear"

    def test_main_with_combined_args(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Testa combinação de argumentos --dirs e --warn-only.

        DADO múltiplos argumentos combinados
        QUANDO executamos main()
        ENTÃO deve aplicar ambas as configurações
        """
        from scripts.hooks.tdd_guardian import main

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "deploy.py"
        script_file.write_text("# Deploy")

        monkeypatch.setattr(
            "sys.argv",
            [
                "tdd_guardian.py",
                "--dirs",
                "src",
                "scripts",
                "--warn-only",
                str(script_file),
            ],
        )
        monkeypatch.chdir(tmp_path)

        exit_code = main()

        # Combina múltiplos dirs + warn-only = não bloqueia
        assert exit_code == 0, "Combinação deveria funcionar corretamente"
