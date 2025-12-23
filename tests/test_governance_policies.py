"""Suite de testes de Política como Código (Policy as Code).

Garante que regras fundamentais de governança (status, tipos, metadados)
sejam validadas em tempo de execução de teste.
"""

import pytest

from scripts.core.cortex.link_analyzer import LinkAnalyzer
from scripts.core.cortex.metadata import (
    ALLOWED_STATUSES,
    ALLOWED_TYPES,
    MANDATORY_FIELDS,
)


@pytest.fixture
def mock_filesystem():
    """Simula um sistema de arquivos para não tocar no disco real."""
    from scripts.utils.filesystem import MemoryFileSystem

    return MemoryFileSystem()


class TestStatusGovernance:
    """Valida as regras de transição e permissão de status."""

    def test_status_list_integrity(self):
        """A lista de status permitidos deve ser exata e controlada."""
        expected = {"draft", "active", "deprecated", "archived"}
        assert set(ALLOWED_STATUSES) == expected, (
            "A lista de status permitidos foi alterada sem autorização."
        )

    def test_status_stable_is_explicitly_rejected(self):
        """Status 'stable' NÃO é válido e deve falhar explicitamente."""
        assert "stable" not in ALLOWED_STATUSES, (
            "Status 'stable' não existe no CORTEX. "
            "Use 'active' para documentos estáveis e publicados."
        )


class TestTypeGovernance:
    """Valida os tipos de documentos permitidos."""

    def test_allowed_types_integrity(self):
        """Novos tipos exigem aprovação de arquitetura."""
        expected = {"guide", "arch", "reference", "history", "knowledge"}
        assert set(ALLOWED_TYPES) == expected, (
            "Novos tipos de documento exigem aprovação de arquitetura."
        )


class TestLinkGovernance:
    """Valida a integridade de referências."""

    def test_link_extraction_context(self):
        """Links extraídos devem fornecer contexto para debugging."""
        analyzer = LinkAnalyzer()
        content = (
            "Consulte a documentação completa em [Guia](docs/guide.md) para instruções."
        )
        links = analyzer.extract_links(content, source_id="test")

        assert len(links) == 1
        assert links[0].target == "docs/guide.md"


class TestMetadataGovernance:
    """Valida campos obrigatórios."""

    def test_mandatory_fields_presence(self):
        """Campos obrigatórios devem estar presentes."""
        expected = {"id", "type", "status", "version", "author", "date"}
        assert set(MANDATORY_FIELDS) == expected
