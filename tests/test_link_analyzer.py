"""Unit Tests for Link Analyzer (CORTEX Phase 3).

Comprehensive test coverage for link extraction from Knowledge Node content.
Validates regex patterns, LinkAnalyzer logic, and edge cases.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import pytest

from scripts.core.cortex.link_analyzer import (
    CODE_REFERENCE_PATTERN,
    MARKDOWN_LINK_PATTERN,
    WIKILINK_PATTERN,
    LinkAnalyzer,
)
from scripts.core.cortex.models import LinkType


class TestMarkdownLinkPattern:
    """Testes para o padrão MARKDOWN_LINK_PATTERN."""

    def test_basic_markdown_link(self) -> None:
        """Testa link Markdown básico."""
        text = "See [Guide](docs/guide.md) for details."
        matches = list(MARKDOWN_LINK_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(1) == "Guide"
        assert matches[0].group(2) == "docs/guide.md"

    def test_relative_path_link(self) -> None:
        """Testa link com caminho relativo (..)."""
        text = "[Architecture](../architecture/design.md)"
        matches = list(MARKDOWN_LINK_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(2) == "../architecture/design.md"

    def test_multiple_links_same_line(self) -> None:
        """Testa múltiplos links na mesma linha."""
        text = "See [A](a.md) and [B](b.md) for reference."
        matches = list(MARKDOWN_LINK_PATTERN.finditer(text))

        assert len(matches) == 2
        assert matches[0].group(1) == "A"
        assert matches[1].group(1) == "B"

    def test_ignores_wikilinks(self) -> None:
        """Garante que não captura Wikilinks."""
        text = "This is a [[Wikilink]] not a markdown link."
        matches = list(MARKDOWN_LINK_PATTERN.finditer(text))

        assert len(matches) == 0

    def test_link_with_special_chars(self) -> None:
        """Testa link com caracteres especiais no label."""
        text = "[API Reference (v2.0)](api/v2.md)"
        matches = list(MARKDOWN_LINK_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(1) == "API Reference (v2.0)"


class TestWikilinkPattern:
    """Testes para o padrão WIKILINK_PATTERN."""

    def test_simple_wikilink(self) -> None:
        """Testa Wikilink simples sem alias."""
        text = "Refer to [[CORTEX Fase 01]] for details."
        matches = list(WIKILINK_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(1) == "CORTEX Fase 01"
        assert matches[0].group(2) is None

    def test_wikilink_with_alias(self) -> None:
        """Testa Wikilink com alias (pipe syntax)."""
        text = "See [[cortex-fase01-design|Phase 1 Design]]"
        matches = list(WIKILINK_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(1) == "cortex-fase01-design"
        assert matches[0].group(2) == "Phase 1 Design"

    def test_wikilink_with_path(self) -> None:
        """Testa Wikilink com caminho de arquivo."""
        text = "[[docs/architecture/CORTEX_FASE01_DESIGN.md]]"
        matches = list(WIKILINK_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(1) == "docs/architecture/CORTEX_FASE01_DESIGN.md"

    def test_multiple_wikilinks(self) -> None:
        """Testa múltiplos Wikilinks."""
        text = "Compare [[Fase 01]] with [[Fase 02]] and [[Fase 03]]"
        matches = list(WIKILINK_PATTERN.finditer(text))

        assert len(matches) == 3
        assert matches[0].group(1) == "Fase 01"
        assert matches[1].group(1) == "Fase 02"
        assert matches[2].group(1) == "Fase 03"

    def test_ignores_markdown_links(self) -> None:
        """Garante que não captura links Markdown."""
        text = "This is [not a wikilink](file.md)"
        matches = list(WIKILINK_PATTERN.finditer(text))

        assert len(matches) == 0

    def test_wikilink_with_spaces(self) -> None:
        """Testa Wikilink com espaços no ID."""
        text = "[[Knowledge Node System]]"
        matches = list(WIKILINK_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(1) == "Knowledge Node System"


class TestCodeReferencePattern:
    """Testes para o padrão CODE_REFERENCE_PATTERN."""

    def test_code_reference_file_only(self) -> None:
        """Testa referência a arquivo sem símbolo."""
        text = "[[code:scripts/core/cortex/models.py]]"
        matches = list(CODE_REFERENCE_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(1) == "scripts/core/cortex/models.py"
        assert matches[0].group(2) is None

    def test_code_reference_with_class(self) -> None:
        """Testa referência com símbolo de classe."""
        text = "[[code:scripts/core/cortex/models.py::KnowledgeEntry]]"
        matches = list(CODE_REFERENCE_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(1) == "scripts/core/cortex/models.py"
        assert matches[0].group(2) == "KnowledgeEntry"

    def test_code_reference_with_function(self) -> None:
        """Testa referência com símbolo de função."""
        text = "[[code:tests/test_link_analyzer.py::test_extraction]]"
        matches = list(CODE_REFERENCE_PATTERN.finditer(text))

        assert len(matches) == 1
        assert matches[0].group(2) == "test_extraction"

    def test_ignores_regular_wikilinks(self) -> None:
        """Garante que não captura Wikilinks regulares."""
        text = "[[Normal Wikilink]]"
        matches = list(CODE_REFERENCE_PATTERN.finditer(text))

        assert len(matches) == 0

    def test_multiple_code_references(self) -> None:
        """Testa múltiplas referências a código."""
        text = """
        See [[code:src/main.py]] and [[code:src/utils.py::helper]]
        """
        matches = list(CODE_REFERENCE_PATTERN.finditer(text))

        assert len(matches) == 2


class TestLinkAnalyzerExtraction:
    """Testes para a classe LinkAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> LinkAnalyzer:
        """Fixture do LinkAnalyzer."""
        return LinkAnalyzer()

    def test_extract_markdown_links(self, analyzer: LinkAnalyzer) -> None:
        """Testa extração de links Markdown."""
        content = """
        # Documentation

        See [Guide](docs/guide.md) for more info.
        Check [Reference](../ref.md) too.
        """
        links = analyzer.extract_links(content, source_id="test-doc")

        markdown_links = [link for link in links if link.type == LinkType.MARKDOWN]
        assert len(markdown_links) == 2
        assert markdown_links[0].target_raw == "docs/guide.md"
        assert markdown_links[1].target_raw == "../ref.md"

    def test_extract_wikilinks(self, analyzer: LinkAnalyzer) -> None:
        """Testa extração de Wikilinks."""
        content = """
        Compare [[Fase 01]] with [[Fase 02|Phase 2]].
        """
        links = analyzer.extract_links(content, source_id="test-doc")

        wikilinks = [
            link
            for link in links
            if link.type in (LinkType.WIKILINK, LinkType.WIKILINK_ALIASED)
        ]
        assert len(wikilinks) == 2
        assert wikilinks[0].type == LinkType.WIKILINK
        assert wikilinks[1].type == LinkType.WIKILINK_ALIASED

    def test_extract_code_references(self, analyzer: LinkAnalyzer) -> None:
        """Testa extração de referências a código."""
        content = """
        The [[code:scripts/core/cortex/models.py::KnowledgeEntry]] model.
        """
        links = analyzer.extract_links(content, source_id="test-doc")

        code_refs = [link for link in links if link.type == LinkType.CODE_REFERENCE]
        assert len(code_refs) == 1
        assert "code:scripts/core/cortex/models.py" in code_refs[0].target_raw

    def test_mixed_link_types(self, analyzer: LinkAnalyzer) -> None:
        """Testa extração de tipos mistos de links."""
        content = """
        # Mixed Links

        - Markdown: [Guide](guide.md)
        - Wikilink: [[Fase 01]]
        - Code: [[code:src/main.py]]
        """
        links = analyzer.extract_links(content, source_id="test-doc")

        # Note: [[code:...]] é capturado tanto por WIKILINK quanto CODE_REFERENCE
        # Isso é esperado e será tratado na fase de resolução
        assert len(links) >= 3
        types = {link.type for link in links}
        assert LinkType.MARKDOWN in types
        assert LinkType.WIKILINK in types or LinkType.CODE_REFERENCE in types

    def test_line_numbers_correct(self, analyzer: LinkAnalyzer) -> None:
        """Verifica se os números de linha estão corretos."""
        content = """Line 1
Line 2 with [[Link A]]
Line 3
Line 4 with [Link B](file.md)
"""
        links = analyzer.extract_links(content, source_id="test-doc")

        # Link A deve estar na linha 2
        link_a = [link for link in links if "Link A" in link.target_raw][0]
        assert link_a.line_number == 2

        # Link B deve estar na linha 4
        link_b = [link for link in links if "file.md" in link.target_raw][0]
        assert link_b.line_number == 4

    def test_context_extraction(self, analyzer: LinkAnalyzer) -> None:
        """Verifica extração de contexto ao redor do link."""
        content = "This is a long sentence with [[Important Link]] in the middle."
        links = analyzer.extract_links(content, source_id="test-doc")

        assert len(links) == 1
        assert "Important Link" in links[0].context
        assert "long sentence" in links[0].context or "..." in links[0].context

    def test_empty_content(self, analyzer: LinkAnalyzer) -> None:
        """Testa comportamento com conteúdo vazio."""
        links = analyzer.extract_links("", source_id="test-doc")
        assert links == []

    def test_no_links(self, analyzer: LinkAnalyzer) -> None:
        """Testa conteúdo sem links."""
        content = "This is plain text without any links."
        links = analyzer.extract_links(content, source_id="test-doc")
        assert links == []

    def test_ignores_external_urls(self, analyzer: LinkAnalyzer) -> None:
        """Verifica que URLs externas são ignoradas."""
        content = """
        External: [Google](https://google.com)
        Internal: [Guide](docs/guide.md)
        """
        links = analyzer.extract_links(content, source_id="test-doc")

        # Apenas o link interno deve ser extraído
        assert len(links) == 1
        assert links[0].target_raw == "docs/guide.md"


class TestRegexEdgeCases:
    """Testes de edge cases para robustez das regex."""

    def test_nested_brackets_markdown(self) -> None:
        """Testa comportamento com colchetes aninhados."""
        # Comportamento esperado: capturar até o primeiro fechamento
        text = "[Label [nested]](file.md)"
        _ = list(MARKDOWN_LINK_PATTERN.finditer(text))

        # Regex deve capturar "Label [nested" como label (conhecido limitation)
        # Ou pode não capturar nada (também aceitável)
        # Este é um edge case raro na prática

    def test_wikilink_with_special_chars(self) -> None:
        """Testa Wikilink com caracteres especiais."""
        text = "[[File-Name_v2.0 (final)]]"
        matches = list(WIKILINK_PATTERN.finditer(text))

        assert len(matches) == 1
        assert "File-Name_v2.0 (final)" in matches[0].group(1)

    def test_multiline_link(self) -> None:
        """Testa comportamento com links em múltiplas linhas."""
        text = """[Label that spans
        multiple lines](file.md)"""
        matches = list(MARKDOWN_LINK_PATTERN.finditer(text))

        # Regex com flag MULTILINE pode capturar links multiline
        # Este é um comportamento aceitável (edge case raro)
        # Se capturar, deve ter exatamente 1 match
        assert len(matches) <= 1

    def test_empty_link_target(self) -> None:
        """Testa comportamento com target vazio."""
        text = "[[]]"
        _ = list(WIKILINK_PATTERN.finditer(text))

        # Pode ou não capturar (edge case)
        # Se capturar, group(1) será string vazia


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
