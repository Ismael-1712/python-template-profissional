"""Suite de Testes de Governança - Policy as Code.

Este módulo contém testes que documentam e aplicam as regras fundamentais
do projeto CORTEX. Qualquer violação das políticas de governança deve falhar
instantaneamente no `make validate`.

**Filosofia: "Leis como Testes"**
- Cada regra de governança é um teste explícito
- Mudanças nas regras requerem mudanças nos testes (revisão consciente)
- Nenhuma validação manual - tudo automatizado

**Categorias de Governança:**
1. Enumerações de Status e Tipos (valores permitidos)
2. Campos Obrigatórios no Frontmatter
3. Integridade de Links (detecção de links quebrados)
4. Formatos de ID, Versão e Data

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.core.cortex.config import (
    ALLOWED_STATUSES,
    ALLOWED_TYPES,
    DATE_PATTERN,
    ERROR_MESSAGES,
    ID_PATTERN,
    REQUIRED_FIELDS,
    VERSION_PATTERN,
)
from scripts.core.cortex.link_analyzer import LinkAnalyzer
from scripts.core.cortex.metadata import FrontmatterParseError, FrontmatterParser
from scripts.core.cortex.models import LinkType
from scripts.utils.filesystem import MemoryFileSystem

# ============================================================================
# GOVERNANÇA: STATUS PERMITIDOS (ENUMERAÇÃO)
# ============================================================================


class TestStatusGovernance:
    """Valida que apenas status explicitamente permitidos são aceitos.

    **Contexto do Incidente:**
    Um documento foi criado com `status: stable`, que não existe no sistema.
    Isso só foi detectado tardiamente, causando retrabalho.

    **Política Aplicada:**
    Apenas os status definidos em ALLOWED_STATUSES são válidos.
    """

    def test_status_draft_is_valid(self) -> None:
        """Status 'draft' deve ser aceito pelo sistema."""
        assert "draft" in ALLOWED_STATUSES

    def test_status_active_is_valid(self) -> None:
        """Status 'active' deve ser aceito pelo sistema."""
        assert "active" in ALLOWED_STATUSES

    def test_status_deprecated_is_valid(self) -> None:
        """Status 'deprecated' deve ser aceito pelo sistema."""
        assert "deprecated" in ALLOWED_STATUSES

    def test_status_archived_is_valid(self) -> None:
        """Status 'archived' deve ser aceito pelo sistema."""
        assert "archived" in ALLOWED_STATUSES

    def test_status_stable_is_explicitly_rejected(self) -> None:
        """Status 'stable' NÃO é válido e deve falhar explicitamente.

        Este é o teste que teria evitado o incidente. Se alguém tentar
        adicionar 'stable' como status, este teste falha imediatamente.
        """
        assert "stable" not in ALLOWED_STATUSES, (
            "Status 'stable' não existe no CORTEX. "
            "Use 'active' para documentos estáveis e publicados."
        )

    def test_only_four_statuses_are_allowed(self) -> None:
        """Garante que a lista de status permitidos não cresça sem revisão."""
        assert len(ALLOWED_STATUSES) == 4, (
            f"Esperado 4 status, encontrado {len(ALLOWED_STATUSES)}. "
            f"Lista atual: {ALLOWED_STATUSES}. "
            "Se você adicionou um novo status, revise este teste e a documentação."
        )

    def test_frontmatter_validation_rejects_invalid_status(self) -> None:
        """Validador deve rejeitar status inválido em documento real."""
        parser = FrontmatterParser()

        invalid_metadata = {
            "id": "test-doc",
            "type": "guide",
            "status": "stable",  # ❌ Status inválido
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-12-23",
        }

        result = parser.validate_metadata(invalid_metadata)

        assert not result.is_valid, "Validação deveria ter falhado para status 'stable'"
        assert any("status" in error.lower() for error in result.errors), (
            f"Erro esperado sobre 'status', mas recebeu: {result.errors}"
        )


# ============================================================================
# GOVERNANÇA: TIPOS DE DOCUMENTOS (ENUMERAÇÃO)
# ============================================================================


class TestDocTypeGovernance:
    """Valida que apenas tipos de documento explicitamente permitidos são aceitos."""

    def test_type_guide_is_valid(self) -> None:
        """Tipo 'guide' deve ser aceito pelo sistema."""
        assert "guide" in ALLOWED_TYPES

    def test_type_arch_is_valid(self) -> None:
        """Tipo 'arch' deve ser aceito pelo sistema."""
        assert "arch" in ALLOWED_TYPES

    def test_type_reference_is_valid(self) -> None:
        """Tipo 'reference' deve ser aceito pelo sistema."""
        assert "reference" in ALLOWED_TYPES

    def test_type_history_is_valid(self) -> None:
        """Tipo 'history' deve ser aceito pelo sistema."""
        assert "history" in ALLOWED_TYPES

    def test_type_knowledge_is_valid(self) -> None:
        """Tipo 'knowledge' deve ser aceito pelo sistema."""
        assert "knowledge" in ALLOWED_TYPES

    def test_type_tutorial_is_explicitly_rejected(self) -> None:
        """Tipo 'tutorial' não existe - use 'guide' ao invés."""
        assert "tutorial" not in ALLOWED_TYPES

    def test_type_api_is_explicitly_rejected(self) -> None:
        """Tipo 'api' não existe - use 'reference' ao invés."""
        assert "api" not in ALLOWED_TYPES

    def test_frontmatter_validation_rejects_invalid_type(self) -> None:
        """Validador deve rejeitar tipo inválido em documento real."""
        parser = FrontmatterParser()

        invalid_metadata = {
            "id": "test-doc",
            "type": "tutorial",  # ❌ Tipo inválido
            "status": "active",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-12-23",
        }

        result = parser.validate_metadata(invalid_metadata)

        assert not result.is_valid
        assert any("type" in error.lower() for error in result.errors)


# ============================================================================
# GOVERNANÇA: CAMPOS OBRIGATÓRIOS (FRONTMATTER)
# ============================================================================


class TestRequiredFieldsGovernance:
    """Valida que todos os campos obrigatórios estão presentes e corretos.

    **Política Aplicada:**
    Todo documento CORTEX deve ter os campos definidos em REQUIRED_FIELDS.
    Sem exceções. Sem metadados vazios.
    """

    def test_required_fields_are_exactly_six(self) -> None:
        """Garante que a lista de campos obrigatórios não mude sem revisão."""
        assert len(REQUIRED_FIELDS) == 6, (
            f"Esperado 6 campos obrigatórios, encontrado {len(REQUIRED_FIELDS)}. "
            f"Lista atual: {REQUIRED_FIELDS}"
        )

    def test_required_field_id_is_mandatory(self) -> None:
        """Campo 'id' é obrigatório."""
        assert "id" in REQUIRED_FIELDS

    def test_required_field_type_is_mandatory(self) -> None:
        """Campo 'type' é obrigatório."""
        assert "type" in REQUIRED_FIELDS

    def test_required_field_status_is_mandatory(self) -> None:
        """Campo 'status' é obrigatório."""
        assert "status" in REQUIRED_FIELDS

    def test_required_field_version_is_mandatory(self) -> None:
        """Campo 'version' é obrigatório."""
        assert "version" in REQUIRED_FIELDS

    def test_required_field_author_is_mandatory(self) -> None:
        """Campo 'author' é obrigatório."""
        assert "author" in REQUIRED_FIELDS

    def test_required_field_date_is_mandatory(self) -> None:
        """Campo 'date' é obrigatório."""
        assert "date" in REQUIRED_FIELDS

    def test_document_without_frontmatter_fails_parsing(self) -> None:
        """Documento sem frontmatter YAML deve falhar ao ser parseado."""
        fs = MemoryFileSystem()
        fs.write_text(
            Path("test.md"),
            "# Just a heading\n\nNo frontmatter here.",
        )

        parser = FrontmatterParser(fs=fs)

        with pytest.raises(
            FrontmatterParseError,
            match="No YAML frontmatter found",
        ):
            parser.parse_file(Path("test.md"))

    def test_document_missing_required_field_fails_validation(self) -> None:
        """Documento sem campo obrigatório deve falhar na validação."""
        parser = FrontmatterParser()

        incomplete_metadata = {
            "id": "test-doc",
            "type": "guide",
            "status": "active",
            # ❌ Faltando: version, author, date
        }

        result = parser.validate_metadata(incomplete_metadata)

        assert not result.is_valid
        assert len(result.errors) >= 3  # Pelo menos 3 campos faltando

    def test_document_with_null_required_field_fails_validation(self) -> None:
        """Campo obrigatório com valor None deve falhar."""
        parser = FrontmatterParser()

        metadata_with_null = {
            "id": "test-doc",
            "type": "guide",
            "status": "active",
            "version": None,  # ❌ Valor nulo em campo obrigatório
            "author": "Team",
            "date": "2025-12-23",
        }

        result = parser.validate_metadata(metadata_with_null)

        assert not result.is_valid
        assert any("version" in error.lower() for error in result.errors)


# ============================================================================
# GOVERNANÇA: FORMATOS DE ID, VERSÃO E DATA
# ============================================================================


class TestFormatGovernance:
    """Valida que formatos de ID, versão e data seguem padrões rígidos.

    **Política Aplicada:**
    - ID: kebab-case (ex: 'testing-guide')
    - Versão: semver (ex: '1.0.0')
    - Data: ISO 8601 (ex: '2025-12-23')
    """

    # --- Testes de ID (kebab-case) ---

    def test_id_kebab_case_is_valid(self) -> None:
        """ID em kebab-case válido deve passar."""
        assert ID_PATTERN.match("testing-guide")
        assert ID_PATTERN.match("api-v2")
        assert ID_PATTERN.match("sprint-1-summary")

    def test_id_camel_case_is_rejected(self) -> None:
        """ID em CamelCase deve ser rejeitado."""
        assert not ID_PATTERN.match("TestingGuide")
        assert not ID_PATTERN.match("apiV2")

    def test_id_snake_case_is_rejected(self) -> None:
        """ID em snake_case deve ser rejeitado."""
        assert not ID_PATTERN.match("testing_guide")
        assert not ID_PATTERN.match("api_v2")

    def test_id_with_spaces_is_rejected(self) -> None:
        """ID com espaços deve ser rejeitado."""
        assert not ID_PATTERN.match("testing guide")

    # --- Testes de Versão (semver) ---

    def test_version_semver_is_valid(self) -> None:
        """Versão semver válida deve passar."""
        assert VERSION_PATTERN.match("1.0.0")
        assert VERSION_PATTERN.match("2.3.1")
        assert VERSION_PATTERN.match("10.20.30")

    def test_version_without_patch_is_rejected(self) -> None:
        """Versão sem patch (ex: '1.0') deve ser rejeitada."""
        assert not VERSION_PATTERN.match("1.0")
        assert not VERSION_PATTERN.match("2.3")

    def test_version_with_prefix_is_rejected(self) -> None:
        """Versão com prefixo 'v' deve ser rejeitada."""
        assert not VERSION_PATTERN.match("v1.0.0")

    def test_version_with_suffix_is_rejected(self) -> None:
        """Versão com sufixo (ex: '1.0.0-beta') deve ser rejeitada."""
        assert not VERSION_PATTERN.match("1.0.0-beta")
        assert not VERSION_PATTERN.match("1.0.0-rc1")

    # --- Testes de Data (ISO 8601) ---

    def test_date_iso_8601_is_valid(self) -> None:
        """Data ISO 8601 válida deve passar."""
        assert DATE_PATTERN.match("2025-12-23")
        assert DATE_PATTERN.match("2024-01-15")

    def test_date_european_format_is_rejected(self) -> None:
        """Data no formato europeu (DD/MM/YYYY) deve ser rejeitada."""
        assert not DATE_PATTERN.match("23/12/2025")
        assert not DATE_PATTERN.match("15-01-2024")

    def test_date_american_format_is_rejected(self) -> None:
        """Data no formato americano (MM/DD/YYYY) deve ser rejeitada."""
        assert not DATE_PATTERN.match("12/23/2025")

    def test_date_with_time_is_rejected(self) -> None:
        """Data com timestamp deve ser rejeitada."""
        assert not DATE_PATTERN.match("2025-12-23T10:00:00")
        assert not DATE_PATTERN.match("2025-12-23 10:00:00")


# ============================================================================
# GOVERNANÇA: INTEGRIDADE DE LINKS
# ============================================================================


class TestLinkIntegrityGovernance:
    """Valida que links quebrados são detectados corretamente.

    **Política Aplicada:**
    Todo link para documentação ou código deve apontar para um arquivo existente.
    Links quebrados = falha imediata.
    """

    def test_link_analyzer_extracts_markdown_links(self) -> None:
        """LinkAnalyzer deve extrair links Markdown padrão."""
        analyzer = LinkAnalyzer()
        content = "Veja o [Guia de Testes](docs/testing.md) para detalhes."

        links = analyzer.extract_links(content, source_id="test-doc")

        assert len(links) == 1
        assert links[0].target_raw == "docs/testing.md"
        assert links[0].type == LinkType.MARKDOWN

    def test_link_analyzer_extracts_wikilinks(self) -> None:
        """LinkAnalyzer deve extrair wikilinks [[target]]."""
        analyzer = LinkAnalyzer()
        content = "Consulte [[Fase 01]] e [[Fase 02|Fase Dois]]."

        links = analyzer.extract_links(content, source_id="test-doc")

        assert len(links) == 2
        assert links[0].target_raw == "Fase 01"
        assert links[0].type == LinkType.WIKILINK
        assert links[1].target_raw == "Fase 02"
        assert links[1].type == LinkType.WIKILINK_ALIASED

    def test_link_analyzer_extracts_code_references(self) -> None:
        """LinkAnalyzer deve extrair referências a código [[code:path]]."""
        analyzer = LinkAnalyzer()
        content = "Veja [[code:scripts/cortex/metadata.py::FrontmatterParser]]."

        links = analyzer.extract_links(content, source_id="test-doc")

        # Pode extrair como CODE_REFERENCE ou também como WIKILINK
        # O importante é que a referência de código seja capturada
        assert len(links) >= 1
        code_links = [link for link in links if "code:" in link.target_raw]
        assert len(code_links) >= 1
        assert "code:scripts/cortex/metadata.py" in code_links[0].target_raw

    def test_link_analyzer_ignores_external_urls(self) -> None:
        """LinkAnalyzer deve ignorar URLs externas (http/https)."""
        analyzer = LinkAnalyzer()
        content = "Acesse [Google](https://google.com) e [GitHub](http://github.com)."

        links = analyzer.extract_links(content, source_id="test-doc")

        assert len(links) == 0, "URLs externas devem ser ignoradas"

    def test_broken_link_detection_scenario(self) -> None:
        """Simula detecção de link quebrado em documento.

        Este teste documenta como um link quebrado deve ser tratado:
        1. Link é extraído pelo analyzer
        2. Link é marcado como não-válido inicialmente (is_valid=False)
        3. Posteriormente, um resolver verificaria se o target existe
        """
        analyzer = LinkAnalyzer()

        # Documento com link para arquivo inexistente
        content = "Consulte [Documentação Perdida](docs/inexistente.md)."

        links = analyzer.extract_links(content, source_id="policy-test")

        assert len(links) == 1
        broken_link = links[0]

        # Link é extraído corretamente
        assert broken_link.target_raw == "docs/inexistente.md"
        assert broken_link.source_id == "policy-test"

        # Link começa como não-válido (precisa de resolução)
        assert not broken_link.is_valid, (
            "Links extraídos devem começar como is_valid=False. "
            "A validação real ocorre na fase de resolução."
        )

    def test_link_provides_context_for_debugging(self) -> None:
        """Links extraídos devem fornecer contexto para debugging."""
        analyzer = LinkAnalyzer()
        content = (
            "Consulte a documentação completa em [Guia](docs/guide.md) para instruções."
        )

        links = analyzer.extract_links(content, source_id="test")

        assert len(links) == 1
        link = links[0]

        # Link deve ter número de linha
        assert link.line_number == 1

        # Link deve ter contexto (snippet ao redor)
        assert link.context is not None
        assert len(link.context) > 0


# ============================================================================
# GOVERNANÇA: MENSAGENS DE ERRO (CONTRATO DE INTERFACE)
# ============================================================================


class TestErrorMessagesGovernance:
    """Valida que mensagens de erro estão padronizadas e completas.

    **Política Aplicada:**
    Toda categoria de erro deve ter uma mensagem template definida.
    Isso garante consistência na experiência do usuário.
    """

    def test_error_message_for_missing_field_exists(self) -> None:
        """Mensagem de erro para campo faltando deve estar definida."""
        assert "missing_field" in ERROR_MESSAGES
        assert "{field}" in ERROR_MESSAGES["missing_field"]

    def test_error_message_for_invalid_id_exists(self) -> None:
        """Mensagem de erro para ID inválido deve estar definida."""
        assert "invalid_id" in ERROR_MESSAGES

    def test_error_message_for_invalid_status_exists(self) -> None:
        """Mensagem de erro para status inválido deve estar definida."""
        assert "invalid_status" in ERROR_MESSAGES
        assert "{allowed}" in ERROR_MESSAGES["invalid_status"]

    def test_error_message_for_invalid_type_exists(self) -> None:
        """Mensagem de erro para tipo inválido deve estar definida."""
        assert "invalid_type" in ERROR_MESSAGES
        assert "{allowed}" in ERROR_MESSAGES["invalid_type"]

    def test_error_message_for_broken_link_exists(self) -> None:
        """Mensagem de erro para link quebrado deve estar definida."""
        assert "broken_doc_link" in ERROR_MESSAGES
        assert "{path}" in ERROR_MESSAGES["broken_doc_link"]


# ============================================================================
# GOVERNANÇA: INTEGRAÇÃO COMPLETA (END-TO-END)
# ============================================================================


class TestEndToEndGovernance:
    """Testes end-to-end que validam o fluxo completo de governança."""

    def test_valid_document_passes_all_governance_checks(self) -> None:
        """Documento completamente válido deve passar em todas as verificações."""
        fs = MemoryFileSystem()

        valid_frontmatter = """---
id: testing-guide
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 2025-12-23
context_tags:
  - testing
  - automation
linked_code:
  - scripts/core/cortex/metadata.py
---

# Testing Guide

Este é um documento válido.
"""

        fs.write_text(Path("docs/testing-guide.md"), valid_frontmatter)
        parser = FrontmatterParser(fs=fs)

        # Parsing deve ser bem-sucedido
        metadata = parser.parse_file(Path("docs/testing-guide.md"))

        assert metadata.id == "testing-guide"
        assert metadata.type.value == "guide"
        assert metadata.status.value == "active"
        assert metadata.version == "1.0.0"

    def test_invalid_document_fails_with_clear_errors(self) -> None:
        """Documento inválido deve falhar com erros claros e acionáveis."""
        fs = MemoryFileSystem()

        invalid_frontmatter = """---
id: InvalidID  # ❌ Não é kebab-case
type: tutorial  # ❌ Tipo não existe
status: stable  # ❌ Status não existe
version: "1.0"  # ❌ Não é semver completo
author: TE  # ❌ Muito curto (< 3 chars)
date: 23/12/2025  # ❌ Não é ISO 8601
---

# Invalid Document
"""

        fs.write_text(Path("docs/invalid.md"), invalid_frontmatter)
        parser = FrontmatterParser(fs=fs)

        # Parsing deve falhar
        with pytest.raises(ValueError) as exc_info:
            parser.parse_file(Path("docs/invalid.md"))

        error_message = str(exc_info.value)

        # Deve mencionar múltiplos erros
        assert "validation failed" in error_message.lower()


# ============================================================================
# DOCUMENTAÇÃO DOS TESTES
# ============================================================================

"""
**Como Usar Esta Suite de Governança:**

1. Execute via pytest:
   ```bash
   pytest tests/test_governance_policies.py -v
   ```

2. Execute via make (integrado ao CI):
   ```bash
   make validate
   ```

3. Se um teste falhar:
   - LEIA A MENSAGEM DE ERRO cuidadosamente
   - Identifique qual regra de governança foi violada
   - Corrija o código/configuração OU atualize a regra consciente

**Quando Modificar Estes Testes:**

✅ Quando adicionar uma nova regra de governança
✅ Quando mudar intencionalmente um status/tipo permitido
✅ Quando atualizar formatos de validação

❌ Apenas para "fazer o CI passar" sem entender o problema
❌ Para contornar validações sem revisão da equipe

**Princípio Fundamental:**
Estes testes são a FONTE DA VERDADE sobre o que é permitido no projeto.
Mudá-los é uma decisão arquitetural, não uma correção trivial.
"""
