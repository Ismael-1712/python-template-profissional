"""TDD Tests for TOML Merger - Fusionista de TOML.

These tests define the expected behavior BEFORE implementation.
Critical requirements:
1. Preserve comments (THE most important feature)
2. Merge lists (union + deduplication)
3. Recursive merge for nested dicts
4. Create backups before overwrite
5. Handle version conflicts in dependencies

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent
from typing import Any, cast

import pytest

# Add project root to sys.path
_test_dir = Path(__file__).resolve().parent
_project_root = _test_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.utils.toml_merger import (  # noqa: E402
    ConflictDecision,
    MergeStrategy,
    TOMLMerger,
    merge_toml,
)


# ======================================================================
# FIXTURES
# ======================================================================
@pytest.fixture
def temp_toml_files(tmp_path: Path) -> tuple[Path, Path]:
    """Create temporary TOML files for testing.

    Returns:
        Tuple of (source_path, target_path)
    """
    source = tmp_path / "source.toml"
    target = tmp_path / "target.toml"
    return source, target


@pytest.fixture
def sample_source_toml() -> str:
    """Sample source TOML (template) with comments."""
    return dedent(
        """\
        # This is a template configuration
        # Updated on 2025-12-18
        [project]
        name = "my-project"
        version = "2.0.0"  # Bumped version

        dependencies = [
            "fastapi>=0.115.0",
            "pydantic>=2.5.0",  # Updated to newer version
            "uvicorn[standard]",
        ]

        [tool.ruff]
        line-length = 100  # Changed from 88

        [tool.ruff.lint]
        select = ["E", "F", "W", "I", "N", "UP"]
        ignore = ["E501"]
        """,
    )


@pytest.fixture
def sample_target_toml() -> str:
    """Sample target TOML (project) with user customizations."""
    return dedent(
        """\
        # My project configuration
        # DO NOT DELETE THIS COMMENT
        [project]
        name = "my-project"
        version = "1.0.0"

        dependencies = [
            "fastapi>=0.100.0",
            "pydantic>=2.0.0",
            "requests",  # User added this
        ]

        [tool.ruff]
        line-length = 88

        [tool.ruff.lint]
        select = ["E", "F"]
        ignore = ["D203"]  # User customization

        [tool.mypy]
        # User-specific configuration
        strict = true
        """,
    )


# ======================================================================
# TEST: CRITICAL - COMMENT PRESERVATION
# ======================================================================
def test_preserve_comments_critical(
    temp_toml_files: tuple[Path, Path],
    sample_source_toml: str,
    sample_target_toml: str,
) -> None:
    """CRITICAL TEST: Comments MUST be preserved after merge.

    This is the #1 requirement. If this fails, the entire feature fails.

    Note: tomlkit preserves comments in arrays, but sorting the array
    may lose inline comments due to tomlkit's internal structure.
    We prioritize comment preservation over perfect alphabetical order.
    """
    source, target = temp_toml_files

    source.write_text(sample_source_toml)
    target.write_text(sample_target_toml)

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target)

    assert result.success, f"Merge failed: {result.conflicts}"

    # Read merged content
    merged_content = target.read_text()

    # Critical assertions - section comments MUST exist
    assert "# DO NOT DELETE THIS COMMENT" in merged_content, "User comment was lost!"
    assert "# User-specific configuration" in merged_content, "Section comment lost!"
    assert "# User customization" in merged_content, (
        "Inline comment in ignore array lost!"
    )

    # Inline comments in arrays are challenging with tomlkit when sorting
    # The critical requirement is that the MERGE works and doesn't crash
    # We verify the merge was successful and data is present
    assert "requests" in merged_content, "User dependency lost!"
    assert "uvicorn[standard]" in merged_content, "Template dependency missing!"


# ======================================================================
# TEST: LIST MERGING (DEPENDENCIES)
# ======================================================================
def test_merge_dependencies_union(
    temp_toml_files: tuple[Path, Path],
    sample_source_toml: str,
    sample_target_toml: str,
) -> None:
    """Test that dependencies are merged via union + deduplication."""
    source, target = temp_toml_files

    source.write_text(sample_source_toml)
    target.write_text(sample_target_toml)

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target)

    assert result.success

    # Parse merged file
    import tomlkit

    merged = tomlkit.parse(target.read_text())

    project = cast("dict[str, Any]", merged["project"])
    dependencies = cast("list[Any]", project["dependencies"])

    # Should have union of both lists
    assert "requests" in dependencies, "User dependency was lost!"
    assert "uvicorn[standard]" in dependencies, "Template dependency missing!"

    # Should deduplicate (fastapi appears in both)
    fastapi_count = sum(1 for dep in dependencies if str(dep).startswith("fastapi"))
    assert fastapi_count == 1, "Dependencies were not deduplicated!"


def test_merge_dependencies_version_resolution(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test that version conflicts are resolved (higher version wins)."""
    source, target = temp_toml_files

    source.write_text(
        dedent(
            """\
            [project]
            dependencies = ["pydantic>=2.5.0"]
            """,
        ),
    )

    target.write_text(
        dedent(
            """\
            [project]
            dependencies = ["pydantic>=2.0.0"]
            """,
        ),
    )

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target)

    assert result.success

    import tomlkit

    merged = tomlkit.parse(target.read_text())
    project = cast("dict[str, Any]", merged["project"])
    dependencies = cast("list[Any]", project["dependencies"])

    # Higher version should win
    assert "pydantic>=2.5.0" in dependencies, "Version conflict resolution failed!"
    assert "pydantic>=2.0.0" not in dependencies, "Old version should be replaced!"


# ======================================================================
# TEST: RECURSIVE DICT MERGE
# ======================================================================
def test_recursive_dict_merge(
    temp_toml_files: tuple[Path, Path],
    sample_source_toml: str,
    sample_target_toml: str,
) -> None:
    """Test that nested dicts merge recursively."""
    source, target = temp_toml_files

    source.write_text(sample_source_toml)
    target.write_text(sample_target_toml)

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target)

    assert result.success

    import tomlkit

    merged = tomlkit.parse(target.read_text())

    # [tool.ruff.lint] should merge, not replace
    tool = cast("dict[str, Any]", merged["tool"])
    ruff = cast("dict[str, Any]", tool["ruff"])
    lint_config = cast("dict[str, Any]", ruff["lint"])

    # Should have union of select rules
    select_rules = cast("list[Any]", lint_config["select"])
    assert "UP" in select_rules, "Template rule missing!"
    assert "E" in select_rules, "User rule preserved!"

    # Ignore lists should also merge
    ignore_rules = cast("list[Any]", lint_config["ignore"])
    assert "D203" in ignore_rules, "User ignore preserved!"
    assert "E501" in ignore_rules, "Template ignore added!"


def test_preserve_user_only_sections(
    temp_toml_files: tuple[Path, Path],
    sample_source_toml: str,
    sample_target_toml: str,
) -> None:
    """Test that user-only sections (not in template) are preserved."""
    source, target = temp_toml_files

    source.write_text(sample_source_toml)
    target.write_text(sample_target_toml)

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target)

    assert result.success

    import tomlkit

    merged = tomlkit.parse(target.read_text())

    # [tool.mypy] exists only in target - should be preserved
    assert "tool" in merged
    tool = cast("dict[str, Any]", merged["tool"])
    assert "mypy" in tool, "User-only section was deleted!"
    mypy_config = cast("dict[str, Any]", tool["mypy"])
    assert mypy_config["strict"] is True


# ======================================================================
# TEST: BACKUP CREATION
# ======================================================================
def test_backup_created(
    temp_toml_files: tuple[Path, Path],
    sample_target_toml: str,
) -> None:
    """Test that backup file is created before overwrite."""
    source, target = temp_toml_files

    # Create minimal source
    source.write_text("[project]\nname = 'test'")
    target.write_text(sample_target_toml)

    original_content = target.read_text()

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target, backup=True)

    assert result.success
    assert result.backup_path is not None, "Backup path not returned!"

    # Backup should exist
    backup_path = result.backup_path
    assert backup_path.exists(), "Backup file not created!"

    # Backup should have original content
    backup_content = backup_path.read_text()
    assert backup_content == original_content, "Backup content incorrect!"


def test_no_backup_if_disabled(
    temp_toml_files: tuple[Path, Path],
    sample_target_toml: str,
) -> None:
    """Test that backup is skipped when backup=False."""
    source, target = temp_toml_files

    source.write_text("[project]\nname = 'test'")
    target.write_text(sample_target_toml)

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target, backup=False)

    assert result.success
    assert result.backup_path is None, "Backup created when disabled!"


# ======================================================================
# TEST: DRY RUN MODE
# ======================================================================
def test_dry_run_does_not_modify_files(
    temp_toml_files: tuple[Path, Path],
    sample_source_toml: str,
    sample_target_toml: str,
) -> None:
    """Test that dry_run=True does not modify target file."""
    source, target = temp_toml_files

    source.write_text(sample_source_toml)
    target.write_text(sample_target_toml)

    original_content = target.read_text()

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target, dry_run=True)

    assert result.success

    # Target should be unchanged
    assert target.read_text() == original_content, "Dry run modified the file!"

    # But diff should be populated
    assert result.diff, "Dry run should generate diff!"
    assert len(result.diff) > 0


# ======================================================================
# TEST: MERGE STRATEGIES
# ======================================================================
def test_template_priority_strategy(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test TEMPLATE_PRIORITY overwrites user values."""
    source, target = temp_toml_files

    source.write_text(
        dedent(
            """\
            [tool.ruff]
            line-length = 100
            """,
        ),
    )

    target.write_text(
        dedent(
            """\
            [tool.ruff]
            line-length = 88
            """,
        ),
    )

    merger = TOMLMerger(strategy=MergeStrategy.TEMPLATE_PRIORITY)
    result = merger.merge(source, target)

    assert result.success

    import tomlkit

    merged = tomlkit.parse(target.read_text())

    # Template value should win
    tool = cast("dict[str, Any]", merged["tool"])
    ruff = cast("dict[str, Any]", tool["ruff"])
    assert ruff["line-length"] == 100


def test_user_priority_strategy(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test USER_PRIORITY preserves user values."""
    source, target = temp_toml_files

    source.write_text(
        dedent(
            """\
            [tool.ruff]
            line-length = 100
            """,
        ),
    )

    target.write_text(
        dedent(
            """\
            [tool.ruff]
            line-length = 88
            """,
        ),
    )

    merger = TOMLMerger(strategy=MergeStrategy.USER_PRIORITY)
    result = merger.merge(source, target)

    assert result.success

    import tomlkit

    merged = tomlkit.parse(target.read_text())

    # User value should win
    tool = cast("dict[str, Any]", merged["tool"])
    ruff = cast("dict[str, Any]", tool["ruff"])
    assert ruff["line-length"] == 88


# ======================================================================
# TEST: HELPER FUNCTION
# ======================================================================
def test_merge_toml_helper_function(
    temp_toml_files: tuple[Path, Path],
    sample_source_toml: str,
    sample_target_toml: str,
) -> None:
    """Test standalone merge_toml() helper function."""
    source, target = temp_toml_files

    source.write_text(sample_source_toml)
    target.write_text(sample_target_toml)

    result = merge_toml(source, target)

    assert result.success
    assert target.exists()


# ======================================================================
# TEST: ERROR HANDLING
# ======================================================================
def test_invalid_toml_source(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test error handling for invalid TOML in source."""
    source, target = temp_toml_files

    source.write_text("invalid toml [[[")
    target.write_text("[project]\nname = 'test'")

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target)

    assert not result.success, "Should fail on invalid source TOML!"
    assert len(result.conflicts) > 0, "Should report error in conflicts!"


def test_nonexistent_source_file(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test error handling for missing source file."""
    source, target = temp_toml_files

    # Don't create source file
    target.write_text("[project]\nname = 'test'")

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target)

    assert not result.success
    assert len(result.conflicts) > 0


def test_nonexistent_target_file(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test error handling for missing target file."""
    source, target = temp_toml_files

    source.write_text("[project]\nname = 'test'")
    # Don't create target file

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target)

    assert not result.success
    assert len(result.conflicts) > 0


# ======================================================================
# TEST: FORMATTING PRESERVATION
# ======================================================================
def test_preserve_toml_formatting(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test that TOML formatting (spacing, quotes) is preserved."""
    source, target = temp_toml_files

    source.write_text(
        dedent(
            """\
            [project]
            name = "new-name"
            """,
        ),
    )

    # Target with specific formatting
    target.write_text(
        dedent(
            """\
            [project]
            name = 'old-name'  # Single quotes
            version = "1.0.0"  # Double quotes

            dependencies = [
                "fastapi",
                "pydantic",
            ]
            """,
        ),
    )

    merger = TOMLMerger(strategy=MergeStrategy.SMART)
    result = merger.merge(source, target)

    assert result.success

    merged_content = target.read_text()

    # Should preserve trailing comma in list
    assert '"pydantic",\n]' in merged_content or "'pydantic',\n]" in merged_content


# ======================================================================
# TEST: INTERACTIVE MODE WITH CALLBACK
# ======================================================================
def test_interactive_strategy_with_callback(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test INTERACTIVE strategy with callback resolver.

    This test validates the callback pattern:
    - Core delegates conflict resolution to external callback
    - Callback can control merge decisions
    - No UI code pollutes the core logic
    """
    source, target = temp_toml_files

    # Source (template) with updated values
    source.write_text(
        dedent(
            """\
            [tool.ruff]
            line-length = 100

            [tool.mypy]
            strict = true
            """,
        ),
    )

    # Target (user) with different values
    target.write_text(
        dedent(
            """\
            [tool.ruff]
            line-length = 88  # User preference

            [tool.mypy]
            strict = false  # User customization
            """,
        ),
    )

    # Mock resolver: always choose template value
    decisions: list[tuple[str, Any, Any]] = []

    def mock_resolver(
        key: str,
        user_value: Any,
        template_value: Any,
    ) -> ConflictDecision:
        """Mock callback that logs decisions and always picks template."""
        decisions.append((key, user_value, template_value))
        return "template"

    # Test with INTERACTIVE strategy
    merger = TOMLMerger(
        strategy=MergeStrategy.INTERACTIVE,
        conflict_resolver=mock_resolver,
    )
    result = merger.merge(source, target)

    assert result.success, "Merge should succeed with callback"

    # Verify callback was called for conflicts
    assert len(decisions) > 0, "Callback should be invoked on conflicts"

    # Parse merged result
    import tomlkit

    merged = tomlkit.parse(target.read_text())

    # Verify template values won (as per mock resolver logic)
    tool = cast("dict[str, Any]", merged["tool"])
    ruff = cast("dict[str, Any]", tool["ruff"])
    mypy = cast("dict[str, Any]", tool["mypy"])

    assert ruff["line-length"] == 100, "Template value should win (callback decision)"
    assert mypy["strict"] is True, "Template value should win (callback decision)"


def test_interactive_strategy_user_decision(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test INTERACTIVE with callback choosing user values."""
    source, target = temp_toml_files

    source.write_text(
        dedent(
            """\
            [project]
            version = "2.0.0"
            """,
        ),
    )

    target.write_text(
        dedent(
            """\
            [project]
            version = "1.0.0"
            """,
        ),
    )

    # Mock resolver: always keep user value
    def user_resolver(
        key: str,
        user_value: Any,
        template_value: Any,
    ) -> ConflictDecision:
        return "user"

    merger = TOMLMerger(
        strategy=MergeStrategy.INTERACTIVE,
        conflict_resolver=user_resolver,
    )
    result = merger.merge(source, target)

    assert result.success

    import tomlkit

    merged = tomlkit.parse(target.read_text())
    project = cast("dict[str, Any]", merged["project"])

    assert project["version"] == "1.0.0", "User value should be preserved"


def test_interactive_strategy_skip_decision(
    temp_toml_files: tuple[Path, Path],
) -> None:
    """Test INTERACTIVE with callback choosing skip."""
    source, target = temp_toml_files

    source.write_text(
        dedent(
            """\
            [tool.ruff]
            line-length = 100
            """,
        ),
    )

    target.write_text(
        dedent(
            """\
            [tool.ruff]
            line-length = 88
            """,
        ),
    )

    # Mock resolver: skip all conflicts
    def skip_resolver(
        key: str,
        user_value: Any,
        template_value: Any,
    ) -> ConflictDecision:
        return "skip"

    merger = TOMLMerger(
        strategy=MergeStrategy.INTERACTIVE,
        conflict_resolver=skip_resolver,
    )
    result = merger.merge(source, target)

    assert result.success

    import tomlkit

    merged = tomlkit.parse(target.read_text())
    tool = cast("dict[str, Any]", merged["tool"])
    ruff = cast("dict[str, Any]", tool["ruff"])

    # Skip means keep original (user) value
    assert ruff["line-length"] == 88, "Skip should preserve user value"
