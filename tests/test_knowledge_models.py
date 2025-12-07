"""Unit tests for CORTEX Knowledge Node models.

This module tests the Pydantic models introduced for the Knowledge Node system,
including validation, serialization, immutability, and error handling.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from scripts.core.cortex import DocStatus, KnowledgeEntry, KnowledgeSource


class TestKnowledgeSource:
    """Test suite for KnowledgeSource model."""

    def test_valid_instantiation(self) -> None:
        """Test creating a valid KnowledgeSource instance."""
        source = KnowledgeSource(
            url="https://example.com/docs/guide.md",
            last_synced=datetime(2025, 12, 7, 10, 30, 0),
            etag='"abc123"',
        )

        assert str(source.url) == "https://example.com/docs/guide.md"
        assert source.last_synced == datetime(2025, 12, 7, 10, 30, 0)
        assert source.etag == '"abc123"'

    def test_valid_instantiation_minimal(self) -> None:
        """Test creating KnowledgeSource with only required fields."""
        source = KnowledgeSource(url="https://example.com")

        assert str(source.url) == "https://example.com/"
        assert source.last_synced is None
        assert source.etag is None

    def test_invalid_url(self) -> None:
        """Test that invalid URLs raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KnowledgeSource(url="not-a-valid-url")

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert errors[0]["type"] == "url_parsing"
        assert "url" in errors[0]["loc"]

    def test_invalid_url_scheme(self) -> None:
        """Test that non-HTTP(S) schemes raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KnowledgeSource(url="ftp://example.com/file.txt")

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert "url" in str(errors[0]["loc"])

    def test_immutability(self) -> None:
        """Test that KnowledgeSource is immutable (frozen=True)."""
        source = KnowledgeSource(url="https://example.com")

        with pytest.raises(ValidationError) as exc_info:
            source.url = "https://other.com"  # type: ignore[misc]

        errors = exc_info.value.errors()
        assert errors[0]["type"] == "frozen_instance"

    def test_serialization_model_dump(self) -> None:
        """Test serialization with model_dump()."""
        source = KnowledgeSource(
            url="https://example.com/docs",
            last_synced=datetime(2025, 12, 7, 15, 45, 30),
            etag='"xyz789"',
        )

        data = source.model_dump()

        # model_dump() preserves HttpUrl type, use str() to convert
        assert str(data["url"]) == "https://example.com/docs"
        assert isinstance(data["last_synced"], datetime)
        assert data["etag"] == '"xyz789"'

    def test_serialization_model_dump_json(self) -> None:
        """Test JSON serialization with model_dump_json()."""
        source = KnowledgeSource(
            url="https://example.com/api",
            last_synced=datetime(2025, 12, 7, 12, 0, 0),
        )

        json_str = source.model_dump_json()
        data = json.loads(json_str)

        assert data["url"] == "https://example.com/api"
        assert "2025-12-07T12:00:00" in data["last_synced"]
        assert data["etag"] is None

    def test_deserialization_round_trip(self) -> None:
        """Test JSON round-trip (serialize -> deserialize -> serialize)."""
        original = KnowledgeSource(
            url="https://example.com/resource",
            last_synced=datetime(2025, 12, 7, 9, 15, 0),
            etag='"tag123"',
        )

        # Serialize to JSON
        json_str = original.model_dump_json()

        # Deserialize back to object
        restored = KnowledgeSource.model_validate_json(json_str)

        # Verify equality
        assert str(restored.url) == str(original.url)
        assert restored.last_synced == original.last_synced
        assert restored.etag == original.etag

        # Serialize again and compare
        assert restored.model_dump_json() == original.model_dump_json()


class TestKnowledgeEntry:
    """Test suite for KnowledgeEntry model."""

    def test_valid_instantiation(self) -> None:
        """Test creating a valid KnowledgeEntry instance."""
        source = KnowledgeSource(url="https://example.com/docs/auth.md")
        entry = KnowledgeEntry(
            id="kno-001",
            status=DocStatus.ACTIVE,
            tags=["api", "authentication"],
            golden_paths="auth/jwt.py -> docs/auth.md",
            sources=[source],
            cached_content="# Authentication Guide\n...",
        )

        assert entry.id == "kno-001"
        assert entry.type == "knowledge"
        assert entry.status == DocStatus.ACTIVE
        assert entry.tags == ["api", "authentication"]
        assert entry.golden_paths == "auth/jwt.py -> docs/auth.md"
        assert len(entry.sources) == 1
        assert entry.cached_content is not None

    def test_valid_instantiation_minimal(self) -> None:
        """Test creating KnowledgeEntry with only required fields."""
        entry = KnowledgeEntry(
            id="kno-002",
            status=DocStatus.DRAFT,
            golden_paths="test/path.py",
        )

        assert entry.id == "kno-002"
        assert entry.type == "knowledge"
        assert entry.status == DocStatus.DRAFT
        assert entry.tags == []
        assert entry.sources == []
        assert entry.cached_content is None

    def test_type_literal_default(self) -> None:
        """Test that type field defaults to 'knowledge'."""
        entry = KnowledgeEntry(
            id="kno-test",
            status=DocStatus.ACTIVE,
            golden_paths="test/path",
        )

        assert entry.type == "knowledge"

    def test_enum_status_values(self) -> None:
        """Test all DocStatus enum values work correctly."""
        for status in DocStatus:
            entry = KnowledgeEntry(
                id=f"kno-{status.value}",
                status=status,
                golden_paths="test/path",
            )
            assert entry.status == status

    def test_empty_tags_and_sources(self) -> None:
        """Test that empty lists are handled correctly."""
        entry = KnowledgeEntry(
            id="kno-empty",
            status=DocStatus.ACTIVE,
            tags=[],
            golden_paths="path",
            sources=[],
        )

        assert entry.tags == []
        assert entry.sources == []

    def test_multiple_sources(self) -> None:
        """Test KnowledgeEntry with multiple sources."""
        sources = [
            KnowledgeSource(url="https://example.com/doc1.md"),
            KnowledgeSource(url="https://example.com/doc2.md"),
            KnowledgeSource(url="https://example.com/doc3.md"),
        ]

        entry = KnowledgeEntry(
            id="kno-multi",
            status=DocStatus.ACTIVE,
            golden_paths="multi/path",
            sources=sources,
        )

        assert len(entry.sources) == 3
        assert all(isinstance(s, KnowledgeSource) for s in entry.sources)

    def test_immutability(self) -> None:
        """Test that KnowledgeEntry is immutable (frozen=True)."""
        entry = KnowledgeEntry(
            id="kno-frozen",
            status=DocStatus.ACTIVE,
            golden_paths="frozen/path",
        )

        with pytest.raises(ValidationError) as exc_info:
            entry.id = "kno-modified"  # type: ignore[misc]

        errors = exc_info.value.errors()
        assert errors[0]["type"] == "frozen_instance"

    def test_serialization_model_dump(self) -> None:
        """Test serialization with model_dump()."""
        source = KnowledgeSource(url="https://example.com/docs")
        entry = KnowledgeEntry(
            id="kno-serialize",
            status=DocStatus.ACTIVE,
            tags=["test", "serialization"],
            golden_paths="test/serialize.py",
            sources=[source],
        )

        data = entry.model_dump()

        assert data["id"] == "kno-serialize"
        assert data["type"] == "knowledge"
        assert data["status"] == DocStatus.ACTIVE
        assert data["tags"] == ["test", "serialization"]
        assert len(data["sources"]) == 1

    def test_serialization_model_dump_json(self) -> None:
        """Test JSON serialization with model_dump_json()."""
        source = KnowledgeSource(
            url="https://example.com/api",
            etag='"abc"',
        )
        entry = KnowledgeEntry(
            id="kno-json",
            status=DocStatus.DEPRECATED,
            tags=["json"],
            golden_paths="json/path",
            sources=[source],
            cached_content="cached data",
        )

        json_str = entry.model_dump_json()
        data = json.loads(json_str)

        assert data["id"] == "kno-json"
        assert data["type"] == "knowledge"
        assert data["status"] == "deprecated"  # Enum serialized to string
        assert data["tags"] == ["json"]
        assert data["cached_content"] == "cached data"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["url"] == "https://example.com/api"

    def test_deserialization_round_trip(self) -> None:
        """Test JSON round-trip with nested KnowledgeSource objects."""
        sources = [
            KnowledgeSource(
                url="https://example.com/doc1",
                last_synced=datetime(2025, 12, 7, 10, 0, 0),
                etag='"tag1"',
            ),
            KnowledgeSource(url="https://example.com/doc2"),
        ]

        original = KnowledgeEntry(
            id="kno-roundtrip",
            status=DocStatus.ACTIVE,
            tags=["roundtrip", "test"],
            golden_paths="test/roundtrip.py",
            sources=sources,
            cached_content="test content",
        )

        # Serialize to JSON
        json_str = original.model_dump_json()

        # Deserialize back to object
        restored = KnowledgeEntry.model_validate_json(json_str)

        # Verify equality
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.status == original.status
        assert restored.tags == original.tags
        assert restored.golden_paths == original.golden_paths
        assert len(restored.sources) == len(original.sources)
        assert restored.cached_content == original.cached_content

        # Verify nested sources
        for orig_src, rest_src in zip(original.sources, restored.sources, strict=True):
            assert str(rest_src.url) == str(orig_src.url)
            assert rest_src.last_synced == orig_src.last_synced
            assert rest_src.etag == orig_src.etag

    def test_deserialization_from_dict(self) -> None:
        """Test deserialization from dictionary (model_validate)."""
        data = {
            "id": "kno-dict",
            "status": "active",
            "tags": ["dict", "test"],
            "golden_paths": "dict/path",
            "sources": [
                {"url": "https://example.com/doc"},
            ],
        }

        entry = KnowledgeEntry.model_validate(data)

        assert entry.id == "kno-dict"
        assert entry.status == DocStatus.ACTIVE
        assert len(entry.sources) == 1
        assert str(entry.sources[0].url) == "https://example.com/doc"

    def test_invalid_status_value(self) -> None:
        """Test that invalid status values raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KnowledgeEntry.model_validate(
                {
                    "id": "kno-invalid",
                    "status": "invalid_status",
                    "golden_paths": "test/path",
                }
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        # Should error on status field
        assert any("status" in str(e["loc"]) for e in errors)

    def test_nested_source_validation(self) -> None:
        """Test that nested KnowledgeSource validation works."""
        with pytest.raises(ValidationError) as exc_info:
            KnowledgeEntry.model_validate(
                {
                    "id": "kno-nested-invalid",
                    "status": "active",
                    "golden_paths": "test/path",
                    "sources": [
                        {"url": "not-a-valid-url"},
                    ],
                }
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        # Should error on nested url field
        assert any("url" in str(e["loc"]) for e in errors)
