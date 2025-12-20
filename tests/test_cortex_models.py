"""Testes unitários para modelos CORTEX Knowledge Node.

Este módulo testa os modelos Pydantic KnowledgeSource e KnowledgeEntry,
validando schemas, imutabilidade e serialização.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import HttpUrl, ValidationError

from scripts.core.cortex.models import (
    DocStatus,
    KnowledgeEntry,
    KnowledgeSource,
)


class TestKnowledgeSource:
    """Testes para o modelo KnowledgeSource."""

    def test_valid_url_http(self) -> None:
        """Testa criação com URL HTTP válida."""
        source = KnowledgeSource(url="http://example.com/doc.md")  # type: ignore[arg-type]
        assert str(source.url) == "http://example.com/doc.md"
        assert source.last_synced is None
        assert source.etag is None

    def test_valid_url_https(self) -> None:
        """Testa criação com URL HTTPS válida."""
        source = KnowledgeSource(url="https://example.com/guide.md")  # type: ignore[arg-type]
        assert str(source.url) == "https://example.com/guide.md"

    def test_invalid_url_no_scheme(self) -> None:
        """Testa rejeição de URL sem esquema (http/https)."""
        with pytest.raises(ValidationError) as exc_info:
            KnowledgeSource(url="example.com/doc.md")  # type: ignore[arg-type]

        assert "url" in str(exc_info.value).lower()

    def test_invalid_url_wrong_scheme(self) -> None:
        """Testa rejeição de URL com esquema inválido."""
        with pytest.raises(ValidationError) as exc_info:
            KnowledgeSource(url="ftp://example.com/doc.md")  # type: ignore[arg-type]

        assert "url" in str(exc_info.value).lower()

    def test_optional_last_synced(self) -> None:
        """Testa campo opcional last_synced."""
        now = datetime(2025, 12, 20, 10, 30, 0)
        source = KnowledgeSource(
            url="https://example.com/doc.md",  # type: ignore[arg-type]
            last_synced=now,
        )
        assert source.last_synced == now

    def test_optional_etag(self) -> None:
        """Testa campo opcional etag."""
        source = KnowledgeSource(
            url="https://example.com/doc.md",  # type: ignore[arg-type]
            etag='"abc123"',
        )
        assert source.etag == '"abc123"'

    def test_all_fields_populated(self) -> None:
        """Testa criação com todos os campos."""
        now = datetime(2025, 12, 20, 10, 30, 0)
        source = KnowledgeSource(
            url="https://api.github.com/repos/owner/repo/readme",  # type: ignore[arg-type]
            last_synced=now,
            etag='"W/abc123"',
        )
        assert str(source.url) == "https://api.github.com/repos/owner/repo/readme"
        assert source.last_synced == now
        assert source.etag == '"W/abc123"'

    def test_immutability_frozen(self) -> None:
        """Testa que o modelo é imutável (frozen=True)."""
        source = KnowledgeSource(url="https://example.com/doc.md")  # type: ignore[arg-type]

        with pytest.raises((ValidationError, AttributeError)):
            source.url = "https://evil.com/malware.md"  # type: ignore[assignment]

    def test_serialization_model_dump(self) -> None:
        """Testa serialização com model_dump()."""
        now = datetime(2025, 12, 20, 10, 30, 0)
        source = KnowledgeSource(
            url="https://example.com/doc.md",  # type: ignore[arg-type]
            last_synced=now,
            etag='"abc"',
        )

        dumped = source.model_dump()
        assert isinstance(dumped["url"], (str, HttpUrl))
        assert dumped["last_synced"] == now
        assert dumped["etag"] == '"abc"'

    def test_serialization_model_dump_json(self) -> None:
        """Testa serialização JSON."""
        source = KnowledgeSource(
            url="https://example.com/doc.md",  # type: ignore[arg-type]
            last_synced=datetime(2025, 12, 20, 10, 30, 0),
        )

        json_str = source.model_dump_json()
        assert "https://example.com/doc.md" in json_str
        assert "2025-12-20T10:30:00" in json_str


class TestKnowledgeEntry:
    """Testes para o modelo KnowledgeEntry."""

    def test_minimal_creation(self) -> None:
        """Testa criação com campos mínimos obrigatórios."""
        entry = KnowledgeEntry(
            id="kno-001",
            status=DocStatus.ACTIVE,
        )

        assert entry.id == "kno-001"
        assert entry.type == "knowledge"  # literal default
        assert entry.status == DocStatus.ACTIVE
        assert entry.tags == []  # default_factory
        assert entry.golden_paths == []
        assert entry.sources == []
        assert entry.cached_content is None
        assert entry.links == []
        assert entry.inbound_links == []

    def test_type_literal_fixed(self) -> None:
        """Testa que o campo type é sempre 'knowledge'."""
        entry = KnowledgeEntry(id="kno-002", status=DocStatus.DRAFT)
        assert entry.type == "knowledge"

    def test_with_tags(self) -> None:
        """Testa criação com tags."""
        entry = KnowledgeEntry(
            id="kno-003",
            status=DocStatus.ACTIVE,
            tags=["api", "authentication", "jwt"],
        )
        assert len(entry.tags) == 3
        assert "jwt" in entry.tags

    def test_with_golden_paths(self) -> None:
        """Testa criação com golden paths."""
        entry = KnowledgeEntry(
            id="kno-004",
            status=DocStatus.ACTIVE,
            golden_paths=["auth/jwt.py -> docs/auth.md"],
        )
        assert len(entry.golden_paths) == 1

    def test_with_knowledge_sources(self) -> None:
        """Testa criação com sources (composição)."""
        source = KnowledgeSource(url="https://example.com/api-guide.md")  # type: ignore[arg-type]
        entry = KnowledgeEntry(
            id="kno-005",
            status=DocStatus.ACTIVE,
            sources=[source],
        )
        assert len(entry.sources) == 1
        assert str(entry.sources[0].url) == "https://example.com/api-guide.md"

    def test_with_cached_content(self) -> None:
        """Testa criação com cached_content."""
        content = "# API Guide\n\nThis is the authentication guide..."
        entry = KnowledgeEntry(
            id="kno-006",
            status=DocStatus.ACTIVE,
            cached_content=content,
        )
        assert entry.cached_content == content

    def test_immutability_frozen(self) -> None:
        """Testa que o modelo é imutável (frozen=True)."""
        entry = KnowledgeEntry(id="kno-007", status=DocStatus.ACTIVE)

        with pytest.raises((ValidationError, AttributeError)):
            entry.id = "kno-999"

    def test_serialization_excludes_file_path(self) -> None:
        """Testa que file_path é excluído na serialização."""
        from pathlib import Path

        entry = KnowledgeEntry(
            id="kno-008",
            status=DocStatus.ACTIVE,
            file_path=Path("/tmp/knowledge/kno-008.md"),
        )

        dumped = entry.model_dump()
        assert "file_path" not in dumped

    def test_serialization_model_dump(self) -> None:
        """Testa serialização completa com model_dump()."""
        source = KnowledgeSource(url="https://example.com/guide.md")  # type: ignore[arg-type]
        entry = KnowledgeEntry(
            id="kno-009",
            status=DocStatus.ACTIVE,
            tags=["testing"],
            sources=[source],
        )

        dumped = entry.model_dump()
        assert dumped["id"] == "kno-009"
        assert dumped["type"] == "knowledge"
        assert dumped["status"] == DocStatus.ACTIVE
        assert len(dumped["sources"]) == 1

    def test_serialization_model_dump_json(self) -> None:
        """Testa serialização JSON completa."""
        entry = KnowledgeEntry(
            id="kno-010",
            status=DocStatus.ACTIVE,
            tags=["json", "serialization"],
        )

        json_str = entry.model_dump_json()
        assert "kno-010" in json_str
        assert "knowledge" in json_str
        assert "active" in json_str.lower()

    def test_default_factory_independence(self) -> None:
        """Testa que default_factory cria listas independentes."""
        entry1 = KnowledgeEntry(id="kno-011", status=DocStatus.ACTIVE)
        entry2 = KnowledgeEntry(id="kno-012", status=DocStatus.ACTIVE)

        # Modificar lista não afeta outras instâncias (antes de frozen)
        assert entry1.tags is not entry2.tags

    def test_status_enum_validation(self) -> None:
        """Testa validação do enum DocStatus."""
        # Valid statuses
        valid_statuses = [
            DocStatus.DRAFT,
            DocStatus.ACTIVE,
            DocStatus.DEPRECATED,
            DocStatus.ARCHIVED,
        ]
        for status in valid_statuses:
            entry = KnowledgeEntry(id=f"kno-{status.value}", status=status)
            assert entry.status == status

    def test_invalid_status_rejected(self) -> None:
        """Testa rejeição de status inválido."""
        with pytest.raises(ValidationError) as exc_info:
            KnowledgeEntry(
                id="kno-invalid",
                status="INVALID_STATUS",  # type: ignore[arg-type]
            )

        assert "status" in str(exc_info.value).lower()
