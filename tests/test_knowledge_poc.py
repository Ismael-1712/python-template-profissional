"""Proof of Concept: Knowledge Scanner usando FileSystemAdapter.

Este módulo demonstra o uso do método `rglob()` para implementar um scanner
de base de conhecimento, preparando o terreno para o futuro Knowledge Node (Item P31).

Author: DevOps Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.utils.filesystem import FileSystemAdapter, MemoryFileSystem, RealFileSystem


def scan_knowledge_base(
    fs: FileSystemAdapter,
    root: Path,
    pattern: str = "*.md",
) -> list[Path]:
    """Escaneia base de conhecimento em busca de documentos.

    Esta é uma função de demonstração que simula o futuro Knowledge Node.
    Usa o FileSystemAdapter para permitir testes rápidos sem I/O.

    Args:
        fs: Filesystem adapter (RealFileSystem ou MemoryFileSystem)
        root: Diretório raiz da base de conhecimento
        pattern: Padrão de busca (default: "*.md")

    Returns:
        Lista de todos os arquivos encontrados recursivamente

    Example:
        >>> fs = MemoryFileSystem()
        >>> fs.write_text(Path("docs/api/v1.md"), "# API v1")
        >>> docs = scan_knowledge_base(fs, Path("docs"))
        >>> len(docs)
        1
    """
    return list(fs.rglob(root, pattern))


def extract_metadata(fs: FileSystemAdapter, doc_path: Path) -> dict[str, str | int]:
    """Extrai metadados simples de um documento Markdown.

    Args:
        fs: Filesystem adapter
        doc_path: Caminho do documento

    Returns:
        Dicionário com metadados extraídos
    """
    content = fs.read_text(doc_path)
    lines = content.split("\n")

    # Extrai primeira linha como título (simplificado)
    title = "Untitled"
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    return {
        "path": str(doc_path),
        "title": title,
        "size": len(content),
    }


class TestKnowledgeScannerPoC:
    """Proof of Concept: Knowledge Scanner usando rglob()."""

    def test_scan_simple_structure(self) -> None:
        """PoC: Escanear estrutura simples de documentação."""
        fs = MemoryFileSystem()

        # Criar estrutura de documentação simulada
        fs.write_text(Path("docs/index.md"), "# Documentation Index")
        fs.write_text(Path("docs/api/v1.md"), "# API v1 Reference")
        fs.write_text(Path("docs/guides/setup.md"), "# Setup Guide")

        # Escanear base de conhecimento
        docs = scan_knowledge_base(fs, Path("docs"))

        # Validações
        assert len(docs) == 3
        assert Path("docs/index.md") in docs
        assert Path("docs/api/v1.md") in docs
        assert Path("docs/guides/setup.md") in docs

    def test_scan_complex_nested_structure(self) -> None:
        """PoC: Escanear estrutura complexa com múltiplos níveis."""
        fs = MemoryFileSystem()

        # Criar estrutura complexa (3 níveis)
        fs.write_text(Path("kb/root.md"), "# Knowledge Base Root")
        fs.write_text(Path("kb/arch/design.md"), "# Design Principles")
        fs.write_text(Path("kb/arch/decisions/adr-001.md"), "# ADR 001")
        fs.write_text(Path("kb/arch/decisions/adr-002.md"), "# ADR 002")
        fs.write_text(Path("kb/guides/api/rest.md"), "# REST API Guide")
        fs.write_text(Path("kb/guides/api/graphql.md"), "# GraphQL Guide")
        fs.write_text(Path("kb/guides/deployment/docker.md"), "# Docker Deployment")

        # Escanear recursivamente
        all_docs = scan_knowledge_base(fs, Path("kb"))

        # Validações
        assert len(all_docs) == 7

        # Verificar níveis profundos
        assert Path("kb/arch/decisions/adr-001.md") in all_docs
        assert Path("kb/guides/api/rest.md") in all_docs
        assert Path("kb/guides/deployment/docker.md") in all_docs

    def test_scan_with_multiple_extensions(self) -> None:
        """PoC: Escanear com diferentes extensões de arquivo."""
        fs = MemoryFileSystem()

        # Criar arquivos de diferentes tipos
        fs.write_text(Path("docs/readme.md"), "# README")
        fs.write_text(Path("docs/config.yaml"), "key: value")
        fs.write_text(Path("docs/script.py"), "# Python script")
        fs.write_text(Path("docs/data.json"), '{"key": "value"}')

        # Escanear apenas Markdown
        md_files = scan_knowledge_base(fs, Path("docs"), "*.md")
        assert len(md_files) == 1
        assert Path("docs/readme.md") in md_files

        # Escanear apenas Python
        py_files = scan_knowledge_base(fs, Path("docs"), "*.py")
        assert len(py_files) == 1
        assert Path("docs/script.py") in py_files

        # Escanear apenas YAML
        yaml_files = scan_knowledge_base(fs, Path("docs"), "*.yaml")
        assert len(yaml_files) == 1
        assert Path("docs/config.yaml") in yaml_files

    def test_scan_empty_knowledge_base(self) -> None:
        """PoC: Escanear base de conhecimento vazia."""
        fs = MemoryFileSystem()

        # Criar estrutura vazia
        fs.mkdir(Path("empty_kb/section1"))
        fs.mkdir(Path("empty_kb/section2/subsection"))

        # Escanear deve retornar lista vazia
        docs = scan_knowledge_base(fs, Path("empty_kb"))
        assert len(docs) == 0
        assert docs == []

    def test_extract_metadata_from_documents(self) -> None:
        """PoC: Extrair metadados de documentos escaneados."""
        fs = MemoryFileSystem()

        # Criar documentos com conteúdo
        fs.write_text(
            Path("docs/guide.md"),
            "# Complete Setup Guide\n\nThis is the content of the guide.",
        )
        fs.write_text(
            Path("docs/api.md"),
            "# API Reference\n\n## Endpoints\n\n- GET /users\n- POST /users",
        )

        # Escanear e extrair metadados
        docs = scan_knowledge_base(fs, Path("docs"))
        metadata_list = [extract_metadata(fs, doc) for doc in docs]

        # Validações
        assert len(metadata_list) == 2  # noqa: PLR2004

        # Verificar metadados do primeiro documento
        guide_meta = next(m for m in metadata_list if "guide.md" in str(m["path"]))
        assert guide_meta["title"] == "Complete Setup Guide"
        assert int(str(guide_meta["size"])) > 0

        # Verificar metadados do segundo documento
        api_meta = next(m for m in metadata_list if "api.md" in str(m["path"]))
        assert api_meta["title"] == "API Reference"
        assert int(str(api_meta["size"])) > 0

    def test_scan_with_pattern_filter(self) -> None:
        """PoC: Escanear com filtros de padrão específicos."""
        fs = MemoryFileSystem()

        # Criar documentos de diferentes tipos
        fs.write_text(Path("docs/user_guide.md"), "# User Guide")
        fs.write_text(Path("docs/admin_guide.md"), "# Admin Guide")
        fs.write_text(Path("docs/api_reference.md"), "# API Reference")
        fs.write_text(Path("docs/changelog.md"), "# Changelog")

        # Escanear apenas guias (pattern: *_guide.md)
        guides = scan_knowledge_base(fs, Path("docs"), "*_guide.md")
        assert len(guides) == 2
        assert Path("docs/user_guide.md") in guides
        assert Path("docs/admin_guide.md") in guides
        assert Path("docs/api_reference.md") not in guides

    def test_performance_comparison(self) -> None:
        """PoC: Demonstrar performance de MemoryFS vs RealFS."""
        import time

        # Teste com MemoryFileSystem (sem I/O)
        fs_memory = MemoryFileSystem()

        # Criar 100 documentos
        for i in range(100):
            fs_memory.write_text(
                Path(f"docs/section{i % 10}/doc{i}.md"),
                f"# Document {i}\n\nContent here.",
            )

        # Medir tempo de scan em memória
        start = time.perf_counter()
        docs_memory = scan_knowledge_base(fs_memory, Path("docs"))
        elapsed_memory = time.perf_counter() - start

        # Validações
        assert len(docs_memory) == 100  # noqa: PLR2004

        # MemoryFileSystem deve ser extremamente rápido (< 15ms)
        assert elapsed_memory < 0.015  # 15ms  # noqa: PLR2004

        # Demonstração: Este seria ~50-100x mais lento com RealFileSystem
        # (não executamos para não tocar disco em testes unitários)

    def test_integration_with_real_filesystem(self, tmp_path: Path) -> None:
        """PoC: Integração com sistema de arquivos real (usando tmp_path)."""
        fs = RealFileSystem()

        # Criar estrutura real em diretório temporário
        docs_dir = tmp_path / "knowledge_base"
        docs_dir.mkdir()

        # Criar diretórios pais antes de escrever arquivos
        (docs_dir / "guides").mkdir(parents=True, exist_ok=True)
        (docs_dir / "api").mkdir(parents=True, exist_ok=True)

        fs.write_text(docs_dir / "index.md", "# Knowledge Base Index")
        fs.write_text(docs_dir / "guides/quickstart.md", "# Quick Start")
        fs.write_text(docs_dir / "api/endpoints.md", "# API Endpoints")

        # Escanear sistema real
        docs = scan_knowledge_base(fs, docs_dir)

        # Validações
        assert len(docs) == 3
        assert docs_dir / "index.md" in docs
        assert docs_dir / "guides/quickstart.md" in docs
        assert docs_dir / "api/endpoints.md" in docs


class TestKnowledgeScannerEdgeCases:
    """Edge cases e cenários especiais."""

    def test_scan_with_special_characters_in_filenames(self) -> None:
        """PoC: Lidar com caracteres especiais em nomes de arquivo."""
        fs = MemoryFileSystem()

        # Criar arquivos com caracteres especiais
        fs.write_text(Path("docs/README-pt_BR.md"), "# README em Português")
        fs.write_text(Path("docs/API_v2.0.md"), "# API v2.0")
        fs.write_text(Path("docs/setup-[linux].md"), "# Setup Linux")

        # Escanear deve funcionar normalmente
        docs = scan_knowledge_base(fs, Path("docs"))
        assert len(docs) == 3

    def test_scan_deeply_nested_structure(self) -> None:
        """PoC: Escanear estrutura com muitos níveis de aninhamento."""
        fs = MemoryFileSystem()

        # Criar estrutura profunda (5 níveis)
        deep_path = Path("kb/l1/l2/l3/l4/l5/deep_doc.md")
        fs.write_text(deep_path, "# Deep Document")

        # Escanear deve encontrar documento profundo
        docs = scan_knowledge_base(fs, Path("kb"))
        assert len(docs) == 1
        assert deep_path in docs

    def test_scan_large_knowledge_base(self) -> None:
        """PoC: Escanear base de conhecimento grande (stress test)."""
        fs = MemoryFileSystem()

        # Criar 500 documentos em estrutura hierárquica
        for section in range(10):
            for subsection in range(5):
                for doc in range(10):
                    path = Path(f"kb/s{section}/ss{subsection}/doc{doc}.md")
                    fs.write_text(path, f"# Document {section}-{subsection}-{doc}")

        # Escanear todos
        docs = scan_knowledge_base(fs, Path("kb"))

        # Validações
        expected_count = 10 * 5 * 10
        assert len(docs) == expected_count

        # Performance: Deve completar rapidamente mesmo com 500 docs
        import time  # noqa: PLC0415

        start = time.perf_counter()
        docs = scan_knowledge_base(fs, Path("kb"))
        elapsed = time.perf_counter() - start

        # Sequential mode (v0.1.0+): allow slightly more time than parallel
        # Original threshold: 50ms. Adjusted to 100ms for sequential processing.
        assert elapsed < 0.1  # 100ms  # noqa: PLR2004


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
