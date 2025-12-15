"""Unit tests for Link Resolver.

Tests the link resolution strategies and validation logic.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.core.cortex.link_resolver import LinkResolver, ResolutionResult
from scripts.core.cortex.models import (
    DocStatus,
    KnowledgeEntry,
    KnowledgeLink,
    LinkStatus,
    LinkType,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace for testing.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to temporary workspace
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create knowledge directory
    knowledge_dir = workspace / "docs" / "knowledge"
    knowledge_dir.mkdir(parents=True)

    # Create some test files
    (knowledge_dir / "intro.md").write_text("# Introduction")
    (knowledge_dir / "guide.md").write_text("# Guide")

    return workspace


@pytest.fixture
def sample_entries(temp_workspace: Path) -> list[KnowledgeEntry]:
    """Create sample knowledge entries for testing.

    Args:
        temp_workspace: Temporary workspace path

    Returns:
        List of sample KnowledgeEntry objects
    """
    knowledge_dir = temp_workspace / "docs" / "knowledge"

    entries = [
        KnowledgeEntry(
            id="kno-001",
            status=DocStatus.ACTIVE,
            tags=["test"],
            golden_paths=["test"],
            file_path=knowledge_dir / "intro.md",
        ),
        KnowledgeEntry(
            id="kno-002",
            status=DocStatus.ACTIVE,
            tags=["guide"],
            golden_paths=["guide"],
            file_path=knowledge_dir / "guide.md",
        ),
        KnowledgeEntry(
            id="fase-01",
            status=DocStatus.ACTIVE,
            tags=["fase"],
            golden_paths=["fase"],
            file_path=knowledge_dir / "fase01.md",
        ),
    ]

    # Create the fase01.md file
    (knowledge_dir / "fase01.md").write_text("# Fase 01")

    return entries


class TestLinkResolver:
    """Test suite for LinkResolver."""

    def test_initialization(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test resolver initialization and index building."""
        resolver = LinkResolver(sample_entries, temp_workspace)

        assert len(resolver._id_index) == 3
        assert "kno-001" in resolver._id_index
        assert "kno-002" in resolver._id_index
        assert "fase-01" in resolver._id_index

        # Path index should contain file paths
        assert len(resolver._path_to_id) > 0

    def test_resolve_by_direct_id(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test resolution by direct ID match."""
        resolver = LinkResolver(sample_entries, temp_workspace)

        # Create a link with direct ID
        link = KnowledgeLink(
            source_id="kno-001",
            target_raw="kno-002",
            type=LinkType.WIKILINK,
            line_number=1,
            context="See [[kno-002]] for more info",
        )

        result = resolver._resolve_link(link, sample_entries[0])

        assert result.target_id == "kno-002"
        assert result.status == LinkStatus.VALID
        assert result.strategy == "id"

    def test_resolve_by_path_relative(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test resolution by relative path."""
        resolver = LinkResolver(sample_entries, temp_workspace)

        # Create a link with relative path
        link = KnowledgeLink(
            source_id="kno-001",
            target_raw="./guide.md",
            type=LinkType.MARKDOWN,
            line_number=1,
            context="See [Guide](./guide.md)",
        )

        result = resolver._resolve_link(link, sample_entries[0])

        assert result.target_id == "kno-002"
        assert result.status == LinkStatus.VALID
        assert result.strategy in ["path_relative", "path_workspace"]

    def test_resolve_by_alias(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test resolution by alias (ID as alias)."""
        resolver = LinkResolver(sample_entries, temp_workspace)

        # Link using ID as alias (should work)
        link = KnowledgeLink(
            source_id="kno-001",
            target_raw="fase-01",
            type=LinkType.WIKILINK,
            line_number=1,
            context="See [[fase-01]]",
        )

        result = resolver._resolve_link(link, sample_entries[0])

        assert result.target_id == "fase-01"
        assert result.status == LinkStatus.VALID

    def test_resolve_by_fuzzy_match(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test resolution by fuzzy normalized match."""
        resolver = LinkResolver(sample_entries, temp_workspace)

        # Link with normalized ID (hyphens removed)
        link = KnowledgeLink(
            source_id="kno-001",
            target_raw="fase01",
            type=LinkType.WIKILINK,
            line_number=1,
            context="See [[fase01]]",
        )

        result = resolver._resolve_link(link, sample_entries[0])

        # Should resolve via fuzzy match
        assert result.target_id == "fase-01"
        assert result.status == LinkStatus.VALID
        assert result.strategy == "fuzzy"

    def test_resolve_broken_link(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test handling of broken (non-existent) links."""
        resolver = LinkResolver(sample_entries, temp_workspace)

        link = KnowledgeLink(
            source_id="kno-001",
            target_raw="non-existent",
            type=LinkType.WIKILINK,
            line_number=1,
            context="See [[non-existent]]",
        )

        result = resolver._resolve_link(link, sample_entries[0])

        assert result.target_id is None
        assert result.status == LinkStatus.BROKEN
        assert result.strategy == "broken"

    def test_resolve_all_links(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test batch resolution of all links."""
        # Add links to entries
        entry_with_links = sample_entries[0].model_copy(
            update={
                "links": [
                    KnowledgeLink(
                        source_id="kno-001",
                        target_raw="kno-002",
                        type=LinkType.WIKILINK,
                        line_number=1,
                        context="[[kno-002]]",
                    ),
                    KnowledgeLink(
                        source_id="kno-001",
                        target_raw="non-existent",
                        type=LinkType.WIKILINK,
                        line_number=2,
                        context="[[non-existent]]",
                    ),
                ],
            },
        )

        entries_with_links = [entry_with_links] + sample_entries[1:]

        resolver = LinkResolver(entries_with_links, temp_workspace)
        resolved_entries = resolver.resolve_all()

        # Check first entry has resolved links
        assert len(resolved_entries[0].links) == 2

        # First link should be valid
        assert resolved_entries[0].links[0].status == LinkStatus.VALID
        assert resolved_entries[0].links[0].target_id == "kno-002"
        assert resolved_entries[0].links[0].is_valid is True

        # Second link should be broken
        assert resolved_entries[0].links[1].status == LinkStatus.BROKEN
        assert resolved_entries[0].links[1].target_id is None
        assert resolved_entries[0].links[1].is_valid is False

    def test_normalize_text(self) -> None:
        """Test text normalization for fuzzy matching."""
        assert LinkResolver._normalize_text("Fase 01") == "fase01"
        assert (
            LinkResolver._normalize_text("Introduction: Part 1") == "introductionpart1"
        )
        assert LinkResolver._normalize_text("Hello-World") == "helloworld"
        assert LinkResolver._normalize_text("  Spaces  ") == "spaces"
        assert LinkResolver._normalize_text("") == ""

    def test_code_reference_resolution(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test resolution of code references."""
        # Create a code file
        scripts_dir = temp_workspace / "scripts"
        scripts_dir.mkdir(parents=True)
        test_file = scripts_dir / "test.py"
        test_file.write_text("# Test file")

        resolver = LinkResolver(sample_entries, temp_workspace)

        link = KnowledgeLink(
            source_id="kno-001",
            target_raw="code:scripts/test.py",
            type=LinkType.CODE_REFERENCE,
            line_number=1,
            context="[[code:scripts/test.py]]",
        )

        result = resolver._resolve_link(link, sample_entries[0])

        assert result.status == LinkStatus.VALID
        assert result.strategy == "code_reference"
        assert result.target_id is None  # Code refs don't have knowledge IDs
        assert result.target_resolved is not None

    def test_code_reference_with_symbol(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test code reference with symbol."""
        # Create a code file
        scripts_dir = temp_workspace / "scripts"
        scripts_dir.mkdir(parents=True)
        test_file = scripts_dir / "test.py"
        test_file.write_text("class TestClass: pass")

        resolver = LinkResolver(sample_entries, temp_workspace)

        link = KnowledgeLink(
            source_id="kno-001",
            target_raw="code:scripts/test.py::TestClass",
            type=LinkType.CODE_REFERENCE,
            line_number=1,
            context="[[code:scripts/test.py::TestClass]]",
        )

        result = resolver._resolve_link(link, sample_entries[0])

        assert result.status == LinkStatus.VALID
        assert result.strategy == "code_reference"

    def test_resolve_with_anchor(
        self,
        sample_entries: list[KnowledgeEntry],
        temp_workspace: Path,
    ) -> None:
        """Test resolution of links with anchor fragments."""
        resolver = LinkResolver(sample_entries, temp_workspace)

        # Link with anchor should still resolve
        link = KnowledgeLink(
            source_id="kno-001",
            target_raw="./guide.md#section",
            type=LinkType.MARKDOWN,
            line_number=1,
            context="[Section](./guide.md#section)",
        )

        result = resolver._resolve_link(link, sample_entries[0])

        # Should resolve by stripping anchor
        assert result.status == LinkStatus.VALID
        assert result.target_id == "kno-002"


class TestResolutionResult:
    """Test ResolutionResult dataclass."""

    def test_result_creation(self) -> None:
        """Test creating a ResolutionResult."""
        result = ResolutionResult(
            target_id="kno-001",
            target_resolved="kno-001",
            status=LinkStatus.VALID,
            strategy="id",
        )

        assert result.target_id == "kno-001"
        assert result.target_resolved == "kno-001"
        assert result.status == LinkStatus.VALID
        assert result.strategy == "id"

    def test_broken_result(self) -> None:
        """Test creating a broken link result."""
        result = ResolutionResult(
            target_id=None,
            target_resolved=None,
            status=LinkStatus.BROKEN,
            strategy="broken",
        )

        assert result.target_id is None
        assert result.target_resolved is None
        assert result.status == LinkStatus.BROKEN
