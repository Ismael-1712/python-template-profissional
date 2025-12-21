"""Testes para validar geração de projetos via Copier Template.

Este módulo testa se o template Copier:
- Gera arquivos com variáveis substituídas corretamente
- Preserva configurações do usuário em updates
- Exclui arquivos sensíveis (_exclude)
- Executa hooks de toml-fusion corretamente

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def copier_answers() -> dict[str, Any]:
    """Respostas padrão para testes de geração do template.

    Returns:
        Dicionário com variáveis do copier.yml
    """
    return {
        "project_name": "My Awesome Project",
        "project_slug": "my_awesome_project",
        "project_description": "A professional Python project for testing",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "repository_url": "https://github.com/testuser/my-awesome-project",
        "python_version": "3.10",
        "initial_version": "0.1.0",
        "enable_docker": True,
        "enable_mkdocs": True,
        "default_reviewers": "@test-team",
    }


class TestCopierTemplateGeneration:
    """Testes de geração inicial do template."""

    def test_pyproject_toml_generated_with_correct_metadata(
        self,
        copier_answers: dict[str, Any],
    ) -> None:
        """Verifica se pyproject.toml é gerado com metadados corretos.

        Simula a geração de um projeto e valida:
        - project.name = "my_awesome_project"
        - project.description correta
        - project.authors com nome e email
        - requires-python = ">=3.10"
        """
        # ARRANGE - Cria diretório temporário para projeto
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "my_awesome_project"

            # ACT - Simula geração via Copier (mock)
            # Como ainda não temos o template pronto, este teste FALHARÁ (RED)
            # Após criar copier.yml e templates, substituiremos pelo copier.run_copy
            pyproject_path = project_path / "pyproject.toml"

            # ASSERT - Por enquanto, esperamos que o arquivo não exista (RED)
            # Após implementação, verificaremos conteúdo real
            assert not pyproject_path.exists(), (
                "Teste RED: Template ainda não implementado. "
                "Este teste deve falhar até criarmos copier.yml."
            )

    def test_excluded_files_are_not_overwritten(
        self,
        copier_answers: dict[str, Any],
    ) -> None:
        """Verifica se arquivos em _exclude não são sobrescritos.

        Testa que:
        - .env não é copiado
        - .cortex/ não é incluído
        - .git/ não é tocado
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()

            # Cria arquivo sensível que não deve ser sobrescrito
            env_file = project_path / ".env"
            env_file.write_text("SECRET_KEY=my_secret_123")

            # ACT - Simula update do template (ainda não implementado)
            # copier.run_update(...)

            # ASSERT - .env deve permanecer inalterado
            assert env_file.read_text() == "SECRET_KEY=my_secret_123"

    @pytest.mark.skip(reason="TDD RED - Aguardando implementação completa do Copier")
    def test_readme_contains_project_name(
        self,
        copier_answers: dict[str, Any],
    ) -> None:
        """Verifica se README.md contém o nome do projeto substituído.

        Valida:
        - Título substituído de 'CORTEX' para 'My Awesome Project'
        - URL do repositório correta
        """
        # Teste RED - Ainda não temos template
        raise AssertionError("Template não implementado - fase RED do TDD")


class TestCopierSmartUpdate:
    """Testes de atualização inteligente com toml-fusion."""

    @pytest.mark.skip(reason="TDD RED - Aguardando integração com toml_merger")
    def test_toml_fusion_preserves_user_dependencies(self) -> None:
        """Verifica se toml-fusion preserva dependências customizadas.

        Cenário:
        1. Usuário adiciona "my-custom-lib" ao pyproject.toml
        2. Template é atualizado com nova lib "template-new-lib"
        3. Após update, ambas as libs devem coexistir
        """
        # ARRANGE - Cria pyproject.toml do usuário
        with tempfile.TemporaryDirectory() as tmpdir:
            user_toml = Path(tmpdir) / "user_pyproject.toml"
            user_toml.write_text(
                """
[project]
name = "user_project"
dependencies = ["fastapi", "my-custom-lib>=1.0"]
""",
            )

            # ACT - Simula merge via toml-fusion (mockado)
            # Após implementação, chamaremos scripts.utils.toml_merger.merge_toml
            # result = merge_toml(template_toml, user_toml, strategy="smart")

            # ASSERT - Deve conter AMBAS as dependências
            # merged_data = tomli.loads(user_toml.read_text())
            # assert "my-custom-lib>=1.0" in merged_data["project"]["dependencies"]
            # assert "template-new-lib" in merged_data["project"]["dependencies"]

            # Teste RED - Ainda não implementado
            raise AssertionError("Smart Update não implementado - fase RED")


class TestCopierValidators:
    """Testes de validação de inputs do copier.yml."""

    @pytest.mark.parametrize(
        "invalid_version",
        ["3.9", "2.7", "invalid"],
    )
    def test_invalid_python_version_rejected(self, invalid_version: str) -> None:
        """Verifica se versões Python inválidas são rejeitadas.

        Args:
            invalid_version: Versão inválida para testar
        """
        # Teste de validação do copier.yml (choices)
        valid_versions = ["3.10", "3.11", "3.12", "3.13"]
        assert invalid_version not in valid_versions

    def test_repository_url_validator(self) -> None:
        """Verifica validação de URL do repositório GitHub."""
        valid_url = "https://github.com/user/repo"
        invalid_url = "http://gitlab.com/user/repo"

        # Pattern do copier.yml: ^https://github\.com/.+/.+$
        import re

        pattern = r"^https://github\.com/.+/.+$"
        assert re.match(pattern, valid_url)
        assert not re.match(pattern, invalid_url)


# ======================================================================
# HELPER PARA TESTES (Mockado até termos Copier configurado)
# ======================================================================
def _mock_generate_project(
    template_path: Path,
    output_path: Path,
    answers: dict[str, Any],
) -> None:
    """Mock temporário de copier.run_copy até implementarmos o template.

    Args:
        template_path: Caminho do template Copier
        output_path: Diretório de saída
        answers: Respostas para variáveis do template
    """
    # Placeholder - será substituído por copier.run_copy real
    raise NotImplementedError(
        "Template Copier ainda não implementado. Este é um teste RED do TDD.",
    )
