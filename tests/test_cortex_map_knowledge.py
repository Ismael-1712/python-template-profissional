"""Tests for Cortex Map Knowledge Integration.

Tests the integration between ProjectMapper and KnowledgeScanner to ensure
that the cortex map command properly includes Project Rules & Golden Paths
from the Knowledge Node.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.core.cortex.mapper import ProjectMapper
from scripts.utils.filesystem import MemoryFileSystem


@pytest.fixture
def mock_fs_with_knowledge() -> MemoryFileSystem:
    """Create a mock filesystem with knowledge entries and project files."""
    fs = MemoryFileSystem()

    # Create pyproject.toml
    pyproject_content = """
[project]
name = "test-project"
version = "1.0.0"
description = "Test project with knowledge"
requires-python = ">=3.10"
dependencies = ["pydantic>=2.0.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]

[project.scripts]
test-cli = "scripts.cli.test:main"
"""
    fs.write_text(Path("pyproject.toml"), pyproject_content)

    # Create knowledge entries directory
    knowledge_dir = Path("docs/knowledge")
    fs.mkdir(knowledge_dir, parents=True, exist_ok=True)

    # Knowledge entry 1: Authentication rules (active)
    auth_knowledge = """---
id: kno-auth-001
status: active
tags: [authentication, security, api]
golden_paths:
  - "src/app/auth/jwt.py -> docs/guides/authentication.md"
  - "src/app/auth/middleware.py -> docs/architecture/security.md"
sources:
  - url: "https://example.com/auth-docs"
    type: documentation
    priority: high
---

# Authentication Golden Paths

## JWT Implementation
All JWT authentication must use the centralized handler in `src/app/auth/jwt.py`.

## Middleware Pattern
Authentication middleware MUST be applied to all protected routes.
"""
    fs.write_text(knowledge_dir / "authentication.md", auth_knowledge)

    # Knowledge entry 2: Database patterns (active)
    db_knowledge = """---
id: kno-db-001
status: active
tags: [database, orm, patterns]
golden_paths:
  - "src/app/models/*.py -> docs/guides/database.md"
  - "migrations/*.py -> docs/architecture/data-model.md"
sources:
  - url: "https://example.com/db-patterns"
    type: documentation
    priority: medium
---

# Database Golden Paths

## ORM Models
All database models must inherit from BaseModel and follow naming conventions.
"""
    fs.write_text(knowledge_dir / "database.md", db_knowledge)

    # Knowledge entry 3: Deprecated rule (should be excluded)
    deprecated_knowledge = """---
id: kno-old-001
status: deprecated
tags: [legacy]
golden_paths:
  - "legacy/old_auth.py -> nowhere"
---

# Old Authentication (DEPRECATED)
This rule is deprecated and should be ignored.
"""
    fs.write_text(knowledge_dir / "deprecated.md", deprecated_knowledge)

    # Knowledge entry 4: Draft rule (should be included)
    draft_knowledge = """---
id: kno-draft-001
status: draft
tags: [testing, wip]
golden_paths:
  - "tests/fixtures/*.py -> docs/guides/testing.md"
---

# Testing Patterns (DRAFT)
Work in progress testing standards.
"""
    fs.write_text(knowledge_dir / "testing-draft.md", draft_knowledge)

    # Create some docs for completeness
    fs.mkdir(Path("docs/guides"), parents=True, exist_ok=True)
    fs.write_text(Path("docs/guides/README.md"), "# Guides")

    fs.mkdir(Path("docs/architecture"), parents=True, exist_ok=True)
    fs.write_text(Path("docs/architecture/README.md"), "# Architecture")

    # Create scripts/cli directory
    fs.mkdir(Path("scripts/cli"), parents=True, exist_ok=True)
    fs.write_text(
        Path("scripts/cli/test.py"),
        '"""Test CLI"""\ndef main():\n    pass\n',
    )

    return fs


class TestCortexMapKnowledgeIntegration:
    """Test suite for Knowledge Node integration in cortex map."""

    def test_map_includes_knowledge_by_default(
        self,
        mock_fs_with_knowledge: MemoryFileSystem,
    ) -> None:
        """Test that cortex map includes knowledge by default."""
        # Arrange
        project_root = Path()
        mapper = ProjectMapper(project_root, fs=mock_fs_with_knowledge)

        # Act
        context = mapper.map_project(include_knowledge=True)

        # Assert - Check that golden_paths field exists
        assert hasattr(context, "golden_paths"), "ProjectContext missing golden_paths"

        # Assert - Check that golden_paths contains expected paths
        assert isinstance(context.golden_paths, list), "golden_paths should be a list"
        assert len(context.golden_paths) > 0, "Should have found golden paths"

        # Check for specific paths from active entries
        expected_paths = [
            "src/app/auth/jwt.py -> docs/guides/authentication.md",
            "src/app/auth/middleware.py -> docs/architecture/security.md",
            "src/app/models/*.py -> docs/guides/database.md",
            "migrations/*.py -> docs/architecture/data-model.md",
            "tests/fixtures/*.py -> docs/guides/testing.md",  # Draft should be included
        ]

        for expected_path in expected_paths:
            assert expected_path in context.golden_paths, (
                f"Missing expected path: {expected_path}"
            )

    def test_map_excludes_deprecated_knowledge(
        self,
        mock_fs_with_knowledge: MemoryFileSystem,
    ) -> None:
        """Test that deprecated knowledge entries are excluded."""
        # Arrange
        project_root = Path()
        mapper = ProjectMapper(project_root, fs=mock_fs_with_knowledge)

        # Act
        context = mapper.map_project(include_knowledge=True)

        # Assert - Deprecated paths should NOT be included
        deprecated_path = "legacy/old_auth.py -> nowhere"
        assert deprecated_path not in context.golden_paths, (
            "Deprecated paths should be excluded"
        )

    def test_map_includes_knowledge_rules_markdown(
        self,
        mock_fs_with_knowledge: MemoryFileSystem,
    ) -> None:
        """Test that knowledge_rules field contains formatted Markdown."""
        # Arrange
        project_root = Path()
        mapper = ProjectMapper(project_root, fs=mock_fs_with_knowledge)

        # Act
        context = mapper.map_project(include_knowledge=True)

        # Assert - Check that knowledge_rules field exists
        assert hasattr(
            context,
            "knowledge_rules",
        ), "ProjectContext missing knowledge_rules"

        # Assert - Check that knowledge_rules is a non-empty string
        assert isinstance(context.knowledge_rules, str), "knowledge_rules should be str"
        assert len(context.knowledge_rules) > 0, "knowledge_rules should not be empty"

        # Assert - Check for expected Markdown structure
        rules = context.knowledge_rules
        assert "# Project Rules & Golden Paths" in rules, "Missing main heading"
        assert "kno-auth-001" in rules, "Missing authentication rule ID"
        assert "kno-db-001" in rules, "Missing database rule ID"
        assert "kno-draft-001" in rules, "Draft rules should be included"
        assert "kno-old-001" not in rules, "Deprecated rules should be excluded"

        # Check for tags
        assert "authentication" in rules or "security" in rules, "Missing tags"

    def test_map_without_knowledge_flag(
        self,
        mock_fs_with_knowledge: MemoryFileSystem,
    ) -> None:
        """Test that knowledge can be disabled with include_knowledge=False."""
        # Arrange
        project_root = Path()
        mapper = ProjectMapper(project_root, fs=mock_fs_with_knowledge)

        # Act
        context = mapper.map_project(include_knowledge=False)

        # Assert - Should have empty golden_paths and knowledge_rules
        assert context.golden_paths == [], "golden_paths should be empty when disabled"
        assert context.knowledge_rules == "", (
            "knowledge_rules should be empty when disabled"
        )

    def test_map_resilience_no_knowledge_directory(self) -> None:
        """Test that mapper is resilient when docs/knowledge doesn't exist."""
        # Arrange
        fs = MemoryFileSystem()

        # Create minimal project structure without knowledge directory
        pyproject_content = """
[project]
name = "test-project"
version = "1.0.0"
description = "Test project without knowledge"
requires-python = ">=3.10"
"""
        fs.write_text(Path("pyproject.toml"), pyproject_content)

        project_root = Path()
        mapper = ProjectMapper(project_root, fs=fs)

        # Act - Should not raise exception
        context = mapper.map_project(include_knowledge=True)

        # Assert - Should have empty knowledge fields
        assert context.golden_paths == [], "Should return empty list"
        assert (
            context.knowledge_rules == "" or "unavailable" in context.knowledge_rules
        ), "Should indicate knowledge unavailable"

    def test_map_resilience_malformed_knowledge(self) -> None:
        """Test that mapper handles malformed knowledge files gracefully."""
        # Arrange
        fs = MemoryFileSystem()

        pyproject_content = """
[project]
name = "test-project"
version = "1.0.0"
"""
        fs.write_text(Path("pyproject.toml"), pyproject_content)

        # Create knowledge directory with malformed file
        knowledge_dir = Path("docs/knowledge")
        fs.mkdir(knowledge_dir, parents=True, exist_ok=True)

        # Malformed YAML (missing required 'id' field)
        malformed_knowledge = """---
status: active
tags: [broken]
---

# Malformed Knowledge
This entry is missing the required 'id' field.
"""
        fs.write_text(knowledge_dir / "malformed.md", malformed_knowledge)

        project_root = Path()
        mapper = ProjectMapper(project_root, fs=fs)

        # Act - Should not raise exception
        context = mapper.map_project(include_knowledge=True)

        # Assert - Should handle gracefully
        assert isinstance(context.golden_paths, list), "Should return valid list"
        assert isinstance(context.knowledge_rules, str), "Should return valid string"

    def test_knowledge_rules_markdown_format(
        self,
        mock_fs_with_knowledge: MemoryFileSystem,
    ) -> None:
        """Test that knowledge_rules follows expected Markdown format."""
        # Arrange
        project_root = Path()
        mapper = ProjectMapper(project_root, fs=mock_fs_with_knowledge)

        # Act
        context = mapper.map_project(include_knowledge=True)

        # Assert - Verify Markdown structure
        rules = context.knowledge_rules
        lines = rules.split("\n")

        # Should start with main heading
        assert lines[0].strip() == "# Project Rules & Golden Paths"

        # Should contain section headers
        assert any("## Active Rules" in line for line in lines)

        # Should contain rule IDs as bullet points or subsections
        assert any("kno-auth-001" in line for line in lines)
        assert any("kno-db-001" in line for line in lines)

    def test_golden_paths_unique_and_sorted(
        self,
        mock_fs_with_knowledge: MemoryFileSystem,
    ) -> None:
        """Test that golden_paths are unique and optionally sorted."""
        # Arrange
        project_root = Path()
        mapper = ProjectMapper(project_root, fs=mock_fs_with_knowledge)

        # Act
        context = mapper.map_project(include_knowledge=True)

        # Assert - Check uniqueness
        assert len(context.golden_paths) == len(
            set(context.golden_paths),
        ), "Golden paths should be unique"

        # Assert - All paths should be non-empty strings
        assert all(
            isinstance(path, str) and len(path) > 0 for path in context.golden_paths
        ), "All paths should be non-empty strings"
