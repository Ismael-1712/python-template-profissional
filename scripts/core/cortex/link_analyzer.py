"""Link Analyzer for CORTEX Knowledge Graph.

Module for extracting and analyzing semantic links between Knowledge Nodes.
Supports Markdown links, Wikilinks, and code references.

Usage:
    analyzer = LinkAnalyzer()
    links = analyzer.extract_links(content, source_id="kno-001")

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from scripts.core.cortex.models import KnowledgeLink, LinkType

# ============================================================================
# REGEX PATTERNS
# ============================================================================

# Links Markdown padrão: [Label](target)
MARKDOWN_LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\(([^)]+)\)",
    re.MULTILINE,
)

# Wikilinks: [[target]] ou [[target|alias]]
WIKILINK_PATTERN = re.compile(
    r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
    re.MULTILINE,
)

# Code References: [[code:path/to/file.py]] ou [[code:path::Symbol]]
CODE_REFERENCE_PATTERN = re.compile(
    r"\[\[code:([^\]]+?)(?:::([^\]]+))?\]\]",
    re.MULTILINE,
)


# ============================================================================
# LINK ANALYZER (Core Component)
# ============================================================================


@dataclass
class LinkExtractionResult:
    """Resultado intermediário da extração de links (antes da resolução).

    Attributes:
        target_raw: String original do link
        line_number: Linha onde foi encontrado (1-indexed)
        context: Snippet de contexto ao redor do link
        type: Tipo do link
    """

    target_raw: str
    line_number: int
    context: str
    type: LinkType


class LinkAnalyzer:
    """Analisa conteúdo textual e extrai links semânticos.

    Este componente é stateless e thread-safe. Não mantém estado interno,
    todas as operações são puras (dado o mesmo input, sempre retorna o mesmo output).

    Example:
        >>> analyzer = LinkAnalyzer()
        >>> content = "Veja [[Fase 01]] e [Guia](docs/guide.md)"
        >>> raw_links = analyzer.extract_links(content, source_id="kno-001")
        >>> len(raw_links)
        2
    """

    def __init__(self) -> None:
        """Initialize the LinkAnalyzer."""

    def extract_links(
        self,
        content: str,
        source_id: str,
    ) -> list[KnowledgeLink]:
        """Extrai todos os links do conteúdo textual.

        Args:
            content: Texto completo do documento (cached_content)
            source_id: ID do documento de origem

        Returns:
            Lista de KnowledgeLink com links extraídos (não resolvidos)
        """
        if not content:
            return []

        raw_results: list[LinkExtractionResult] = []

        # Extrair cada tipo de link
        raw_results.extend(self._parse_markdown_links(content))
        raw_results.extend(self._parse_wikilinks(content))
        raw_results.extend(self._parse_code_references(content))

        # Converter para KnowledgeLink
        links = [
            KnowledgeLink(
                source_id=source_id,
                target_raw=result.target_raw,
                target_resolved=None,  # Será resolvido posteriormente
                type=result.type,
                line_number=result.line_number,
                context=result.context,
                is_valid=False,  # Será validado posteriormente
            )
            for result in raw_results
        ]

        return links

    def _parse_markdown_links(self, content: str) -> list[LinkExtractionResult]:
        """Extrai links Markdown padrão [label](target)."""
        links = []

        for line_num, line in enumerate(content.splitlines(), start=1):
            for match in MARKDOWN_LINK_PATTERN.finditer(line):
                label, target = match.groups()

                # Ignorar URLs externas (HTTP/HTTPS)
                if target.startswith(("http://", "https://")):
                    continue

                links.append(
                    LinkExtractionResult(
                        target_raw=target,
                        line_number=line_num,
                        context=self._extract_context(line, match.start()),
                        type=LinkType.MARKDOWN,
                    ),
                )

        return links

    def _parse_wikilinks(self, content: str) -> list[LinkExtractionResult]:
        """Extrai Wikilinks [[target]] ou [[target|alias]]."""
        links = []

        for line_num, line in enumerate(content.splitlines(), start=1):
            for match in WIKILINK_PATTERN.finditer(line):
                target = match.group(1).strip()
                alias = match.group(2).strip() if match.group(2) else None

                link_type = LinkType.WIKILINK_ALIASED if alias else LinkType.WIKILINK

                links.append(
                    LinkExtractionResult(
                        target_raw=target,
                        line_number=line_num,
                        context=self._extract_context(line, match.start()),
                        type=link_type,
                    ),
                )

        return links

    def _parse_code_references(self, content: str) -> list[LinkExtractionResult]:
        """Extrai referências a código [[code:path]] ou [[code:path::Symbol]]."""
        links = []

        for line_num, line in enumerate(content.splitlines(), start=1):
            for match in CODE_REFERENCE_PATTERN.finditer(line):
                file_path = match.group(1).strip()
                symbol = match.group(2).strip() if match.group(2) else None

                target_raw = f"code:{file_path}"
                if symbol:
                    target_raw += f"::{symbol}"

                links.append(
                    LinkExtractionResult(
                        target_raw=target_raw,
                        line_number=line_num,
                        context=self._extract_context(line, match.start()),
                        type=LinkType.CODE_REFERENCE,
                    ),
                )

        return links

    def _extract_context(
        self,
        line: str,
        match_pos: int,
        window: int = 50,
    ) -> str:
        """Extrai snippet de contexto ao redor do match.

        Args:
            line: Linha completa onde o match foi encontrado
            match_pos: Posição inicial do match na linha
            window: Número de caracteres antes/depois (padrão: 50)

        Returns:
            String de contexto com elipses se truncado
        """
        start = max(0, match_pos - window)
        end = min(len(line), match_pos + window)

        snippet = line[start:end]

        # Adicionar elipses se truncado
        if start > 0:
            snippet = "..." + snippet
        if end < len(line):
            snippet = snippet + "..."

        return snippet.strip()
