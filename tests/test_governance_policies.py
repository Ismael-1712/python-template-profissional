"""Suite de testes de Política como Código (Policy as Code).

Garante que regras fundamentais de governança (status, tipos, metadados)
sejam validadas em tempo de execução de teste.
"""

import re
from pathlib import Path

import pytest
import yaml

from scripts.core.cortex.link_analyzer import LinkAnalyzer
from scripts.core.cortex.metadata import (
    ALLOWED_STATUSES,
    ALLOWED_TYPES,
    REQUIRED_FIELDS,
)
from scripts.utils.filesystem import MemoryFileSystem


@pytest.fixture
def mock_filesystem() -> MemoryFileSystem:
    """Simula um sistema de arquivos para não tocar no disco real."""
    return MemoryFileSystem()


class TestStatusGovernance:
    """Valida as regras de transição e permissão de status."""

    def test_status_list_integrity(self) -> None:
        """A lista de status permitidos deve ser exata e controlada."""
        expected = {"draft", "active", "deprecated", "archived"}
        assert set(ALLOWED_STATUSES) == expected, (
            "A lista de status permitidos foi alterada sem autorização."
        )

    def test_status_stable_is_explicitly_rejected(self) -> None:
        """Status 'stable' NÃO é válido e deve falhar explicitamente."""
        assert "stable" not in ALLOWED_STATUSES, (
            "Status 'stable' não existe no CORTEX. "
            "Use 'active' para documentos estáveis e publicados."
        )


class TestTypeGovernance:
    """Valida os tipos de documentos permitidos."""

    def test_allowed_types_integrity(self) -> None:
        """Novos tipos exigem aprovação de arquitetura."""
        expected = {"guide", "arch", "reference", "history", "knowledge"}
        assert set(ALLOWED_TYPES) == expected, (
            "Novos tipos de documento exigem aprovação de arquitetura."
        )


class TestLinkGovernance:
    """Valida a integridade de referências."""

    def test_link_extraction_context(self) -> None:
        """Links extraídos devem fornecer contexto para debugging."""
        analyzer = LinkAnalyzer()
        content = (
            "Consulte a documentação completa em [Guia](docs/guide.md) para instruções."
        )
        links = analyzer.extract_links(content, source_id="test")

        assert len(links) == 1
        assert links[0].target_raw == "docs/guide.md"


class TestMetadataGovernance:
    """Valida campos obrigatórios."""

    def test_mandatory_fields_presence(self) -> None:
        """Campos obrigatórios devem estar presentes."""
        expected = {"id", "type", "status", "version", "author", "date"}
        assert set(REQUIRED_FIELDS) == expected


class TestRealFilesGovernance:
    """Valida que arquivos reais do projeto obedeçam às políticas de governança.

    Esta suite varre o projeto inteiro (não apenas docs/) para garantir que
    nenhum arquivo Markdown escape das regras de Frontmatter.
    """

    # Arquivos de infraestrutura que são isentos das regras de Frontmatter
    EXEMPT_FILES = {
        "README.md",  # README da raiz do projeto (documentação de entrada)
        "CONTRIBUTING.md",  # Guia de contribuição (pode ter formato próprio)
        "CODE_OF_CONDUCT.md",  # Código de conduta padrão
        "SECURITY.md",  # Política de segurança
        "CHANGELOG.md",  # Registro de mudanças (formato específico)
        "LICENSE.md",  # Licença (não aplicável)
        # Templates e documentação do GitHub/projeto
        "PR_CORTEX_ORCHESTRATOR.md",
        "PR_DESCRIPTION.md",
        "PULL_REQUEST_TEMPLATE.md",
        "copilot-instructions.md",
        "PR_CORTEX_MODULARIZATION.md",
    }

    # Diretórios que devem ser completamente ignorados na varredura
    EXCLUDED_DIRS = {
        ".venv",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        "__pycache__",
        "dist",
        "build",
        ".tox",
        "node_modules",
        ".cortex",
        "locales",
        "tests",  # Fixtures de teste não precisam de governança
    }

    def test_project_wide_markdown_compliance(self) -> None:
        """Todos os arquivos Markdown do projeto devem ter Frontmatter válido.

        Este teste varre a raiz completa do projeto (`.`), excluindo apenas
        diretórios de infraestrutura e arquivos explicitamente isentos.

        Falhas neste teste indicam arquivos Markdown sem governança.
        """
        project_root = Path()
        all_md_files = list(project_root.rglob("*.md"))

        # Filtrar arquivos que estão em diretórios excluídos
        filtered_files = []
        for md_file in all_md_files:
            parts = md_file.parts
            if not any(excluded_dir in parts for excluded_dir in self.EXCLUDED_DIRS):
                filtered_files.append(md_file)

        # Separar arquivos isentos vs arquivos que devem ser validados
        files_to_validate = []
        exempt_found = []

        for md_file in filtered_files:
            if md_file.name in self.EXEMPT_FILES:
                exempt_found.append(md_file)
            else:
                files_to_validate.append(md_file)

        # Validar cada arquivo não-isento
        files_without_frontmatter = []
        files_with_invalid_frontmatter = []

        for md_file in files_to_validate:
            content = md_file.read_text(encoding="utf-8")

            # Extrair Frontmatter YAML (delimitado por ---)
            frontmatter_pattern = re.compile(
                r"^---\s*\n(.*?)\n---\s*\n",
                re.DOTALL | re.MULTILINE,
            )
            match = frontmatter_pattern.match(content)

            if not match:
                files_without_frontmatter.append(str(md_file))
                continue

            # Validar YAML
            try:
                frontmatter_raw = match.group(1)
                metadata = yaml.safe_load(frontmatter_raw)

                # Verificar campos obrigatórios (baseado no padrão do projeto)
                # Aceita ambos os padrões: type/status OU doc_type/doc_status
                # Title é obrigatório, mas pode estar em 'title' ou 'id' (fallback)
                if metadata is None or not isinstance(metadata, dict):
                    files_with_invalid_frontmatter.append(
                        (
                            str(md_file),
                            "Frontmatter não é um dicionário YAML válido",
                        ),
                    )
                    continue

                # Deve ter (title OU id) E (type OU doc_type) E (status OU doc_status)
                has_title_or_id = ("title" in metadata) or ("id" in metadata)
                has_type = ("type" in metadata) or ("doc_type" in metadata)
                has_status = ("status" in metadata) or ("doc_status" in metadata)

                missing = []
                if not has_title_or_id:
                    missing.append("title ou id")
                if not has_type:
                    missing.append("type ou doc_type")
                if not has_status:
                    missing.append("status ou doc_status")

                if missing:
                    files_with_invalid_frontmatter.append(
                        (str(md_file), f"Faltam campos: {', '.join(missing)}"),
                    )

            except yaml.YAMLError as e:
                files_with_invalid_frontmatter.append(
                    (str(md_file), f"Erro de parse YAML: {e}"),
                )

        # Construir relatório de falhas
        error_messages = []

        if files_without_frontmatter:
            error_messages.append(
                f"\n❌ {len(files_without_frontmatter)} arquivo(s) "
                f"sem Frontmatter:\n"
                + "\n".join(f"  - {f}" for f in files_without_frontmatter),
            )

        if files_with_invalid_frontmatter:
            error_messages.append(
                f"\n❌ {len(files_with_invalid_frontmatter)} arquivo(s) "
                f"com Frontmatter inválido:\n"
                + "\n".join(
                    f"  - {f}: {reason}" for f, reason in files_with_invalid_frontmatter
                ),
            )

        # Relatório de sucesso (para visibilidade)
        if not error_messages:
            print(
                f"\n✅ Governança Project-Wide: "
                f"{len(files_to_validate)} arquivos validados com sucesso",
            )
            exempt_names = [f.name for f in exempt_found]
            print(f"ℹ️  {len(exempt_found)} arquivo(s) isentos: {exempt_names}")

        # Falhar se houver violações
        assert not error_messages, "\n".join(error_messages)
