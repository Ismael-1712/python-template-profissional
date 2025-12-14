"""Integration Tests for Link Analyzer with Knowledge Scanner.

Tests the full integration of LinkAnalyzer with KnowledgeScanner,
ensuring links are extracted during the scan process.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
from scripts.core.cortex.models import LinkType
from scripts.utils.filesystem import MemoryFileSystem


@pytest.fixture
def in_memory_fs() -> MemoryFileSystem:
    """Cria um filesystem in-memory com arquivos de teste."""
    fs = MemoryFileSystem()

    # Criar diretórios
    fs.mkdir(Path("/project/docs/knowledge"))

    # Arquivo 1: Knowledge Node com links variados
    content_1 = dedent("""
        ---
        id: kno-001
        status: active
        golden_paths: scripts/core/cortex/
        tags:
          - phase3
          - link-analyzer
        ---

        # Link Analyzer Design

        Este documento descreve a arquitetura do Link Analyzer.

        ## Referências

        - Veja [[Fase 01]] para contexto histórico
        - Consulte [Design](docs/architecture/CORTEX_FASE03_DESIGN.md)
        - Implementação em [[code:scripts/core/cortex/link_analyzer.py::LinkAnalyzer]]

        ## Conceitos Relacionados

        [[Knowledge Graph|Grafo de Conhecimento]] é central para a arquitetura.
    """).strip()

    fs.write_text(Path("/project/docs/knowledge/kno-001.md"), content_1)

    # Arquivo 2: Knowledge Node sem links
    content_2 = dedent("""
        ---
        id: kno-002
        status: active
        golden_paths: tests/
        tags:
          - testing
        ---

        # Testing Guide

        Sem links aqui.
    """).strip()

    fs.write_text(Path("/project/docs/knowledge/kno-002.md"), content_2)

    return fs


def test_knowledge_scanner_extracts_links(in_memory_fs: MemoryFileSystem) -> None:
    """Testa se o KnowledgeScanner extrai links durante o scan."""
    scanner = KnowledgeScanner(
        workspace_root=Path("/project"),
        fs=in_memory_fs,
    )

    entries = scanner.scan()

    # Deve encontrar 2 entries
    assert len(entries) == 2

    # Entry kno-001 deve ter pelo menos 4 links (pode detectar duplicados)
    entry_001 = next(e for e in entries if e.id == "kno-001")
    assert len(entry_001.links) >= 4

    # Verificar tipos de links
    link_types = {link.type for link in entry_001.links}
    assert LinkType.WIKILINK in link_types
    assert LinkType.MARKDOWN in link_types
    assert LinkType.CODE_REFERENCE in link_types
    assert LinkType.WIKILINK_ALIASED in link_types

    # Verificar targets específicos
    targets = {link.target_raw for link in entry_001.links}
    assert "Fase 01" in targets
    assert "docs/architecture/CORTEX_FASE03_DESIGN.md" in targets
    assert "code:scripts/core/cortex/link_analyzer.py::LinkAnalyzer" in targets
    assert "Knowledge Graph" in targets


def test_knowledge_scanner_handles_no_links(in_memory_fs: MemoryFileSystem) -> None:
    """Testa que entries sem links têm lista vazia."""
    scanner = KnowledgeScanner(
        workspace_root=Path("/project"),
        fs=in_memory_fs,
    )

    entries = scanner.scan()

    # Entry kno-002 não deve ter links
    entry_002 = next(e for e in entries if e.id == "kno-002")
    assert len(entry_002.links) == 0
    assert entry_002.links == []


def test_link_source_id_matches_entry_id(in_memory_fs: MemoryFileSystem) -> None:
    """Testa que source_id dos links corresponde ao entry.id."""
    scanner = KnowledgeScanner(
        workspace_root=Path("/project"),
        fs=in_memory_fs,
    )

    entries = scanner.scan()
    entry_001 = next(e for e in entries if e.id == "kno-001")

    # Todos os links devem ter source_id = "kno-001"
    for link in entry_001.links:
        assert link.source_id == "kno-001"


def test_links_have_correct_line_numbers(in_memory_fs: MemoryFileSystem) -> None:
    """Testa que os links têm números de linha corretos."""
    scanner = KnowledgeScanner(
        workspace_root=Path("/project"),
        fs=in_memory_fs,
    )

    entries = scanner.scan()
    entry_001 = next(e for e in entries if e.id == "kno-001")

    # Todos os links devem ter line_number > 0
    for link in entry_001.links:
        assert link.line_number > 0

    # Links devem estar em linhas diferentes (exceto se houver múltiplos na mesma linha)
    line_numbers = [link.line_number for link in entry_001.links]
    assert len(set(line_numbers)) >= 3  # Pelo menos 3 linhas diferentes
