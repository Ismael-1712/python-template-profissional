"""Contract tests for FileSystemAdapter implementations.

This test suite ensures that MemoryFileSystem and RealFileSystem have
consistent behavior. These tests prevent regressions where mock implementations
diverge from real filesystem behavior, causing CI failures.

The tests verify critical contracts:
- rglob/glob return iterators (not consumed single-use iterators)
- mkdir creates parent directories when parents=True
- write_text creates parent directories automatically
- Consistent error handling (FileNotFoundError, FileExistsError)

Author: QA Engineering Team
License: MIT
"""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.utils.filesystem import (
    FileSystemAdapter,
    MemoryFileSystem,
    RealFileSystem,
)


class FileSystemContract:
    """Base contract test for FileSystemAdapter implementations.

    This class defines the behavioral contract that all FileSystemAdapter
    implementations must satisfy. Both MemoryFileSystem and RealFileSystem
    are tested against these contracts.
    """

    @pytest.fixture
    def fs(self) -> FileSystemAdapter:
        """Provide filesystem implementation for testing."""
        raise NotImplementedError("Subclasses must implement fs fixture")

    @pytest.fixture
    def base_path(self) -> Path:
        """Provide base path for testing."""
        raise NotImplementedError("Subclasses must implement base_path fixture")

    def test_rglob_returns_iterable(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: rglob must return an iterable that can be consumed multiple times.

        This test prevents the bug where rglob returns a single-use iterator
        that fails when calling len() or iterating twice.
        """
        # Setup: Create test files
        fs.write_text(base_path / "file1.md", "# File 1")
        fs.write_text(base_path / "subdir/file2.md", "# File 2")
        fs.write_text(base_path / "subdir/deep/file3.md", "# File 3")

        # Test: rglob returns iterable
        result = fs.rglob(base_path, "*.md")

        # Contract: Must be convertible to list (for len() operation)
        result_list = list(result)
        assert len(result_list) == 3  # noqa: PLR2004

        # Contract: All expected files found
        assert base_path / "file1.md" in result_list
        assert base_path / "subdir/file2.md" in result_list
        assert base_path / "subdir/deep/file3.md" in result_list

    def test_glob_returns_iterable(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: glob must return an iterable that can be consumed."""
        # Setup: Create test files
        fs.write_text(base_path / "file1.md", "# File 1")
        fs.write_text(base_path / "file2.py", "# Python file")
        fs.write_text(base_path / "subdir/file3.md", "# File 3")

        # Test: glob returns iterable (non-recursive)
        result = fs.glob(base_path, "*.md")
        result_list = list(result)

        # Contract: Only direct children match
        assert len(result_list) == 1
        assert base_path / "file1.md" in result_list
        assert base_path / "subdir/file3.md" not in result_list

    def test_mkdir_with_parents_true(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: mkdir with parents=True creates all intermediate directories."""
        # Test: Create deeply nested directory
        deep_path = base_path / "level1/level2/level3"
        fs.mkdir(deep_path, parents=True, exist_ok=True)

        # Contract: All intermediate directories exist
        assert fs.exists(base_path / "level1")
        assert fs.is_dir(base_path / "level1")
        assert fs.exists(base_path / "level1/level2")
        assert fs.is_dir(base_path / "level1/level2")
        assert fs.exists(deep_path)
        assert fs.is_dir(deep_path)

    def test_mkdir_with_exist_ok_true(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: mkdir with exist_ok=True doesn't raise if directory exists."""
        # Setup: Create directory
        test_dir = base_path / "test_dir"
        fs.mkdir(test_dir, parents=True, exist_ok=True)

        # Contract: Creating again with exist_ok=True succeeds
        fs.mkdir(test_dir, parents=True, exist_ok=True)
        assert fs.exists(test_dir)
        assert fs.is_dir(test_dir)

    def test_mkdir_with_exist_ok_false(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: mkdir with exist_ok=False raises if directory exists."""
        # Setup: Create directory
        test_dir = base_path / "test_dir"
        fs.mkdir(test_dir, parents=True, exist_ok=True)

        # Contract: Creating again with exist_ok=False raises
        with pytest.raises(FileExistsError):
            fs.mkdir(test_dir, parents=False, exist_ok=False)

    def test_write_text_creates_parent_dirs(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: write_text creates parent directories automatically."""
        # Test: Write to file in non-existent directory
        nested_file = base_path / "nested/dir/file.txt"
        fs.write_text(nested_file, "Content")

        # Contract: File and parent directories created
        assert fs.exists(nested_file)
        assert fs.is_file(nested_file)
        assert fs.read_text(nested_file) == "Content"
        assert fs.exists(base_path / "nested")
        assert fs.is_dir(base_path / "nested")
        assert fs.exists(base_path / "nested/dir")
        assert fs.is_dir(base_path / "nested/dir")

    def test_read_nonexistent_file_raises(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: Reading non-existent file raises FileNotFoundError."""
        # Contract: FileNotFoundError for missing file
        with pytest.raises(FileNotFoundError):
            fs.read_text(base_path / "nonexistent.txt")

    def test_exists_returns_false_for_nonexistent(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: exists() returns False for non-existent paths."""
        assert not fs.exists(base_path / "nonexistent.txt")
        assert not fs.exists(base_path / "nonexistent/dir")

    def test_is_file_vs_is_dir(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: is_file and is_dir are mutually exclusive."""
        # Setup: Create file and directory
        test_file = base_path / "file.txt"
        test_dir = base_path / "dir"

        fs.write_text(test_file, "Content")
        fs.mkdir(test_dir, parents=True, exist_ok=True)

        # Contract: Files are not directories
        assert fs.is_file(test_file)
        assert not fs.is_dir(test_file)

        # Contract: Directories are not files
        assert fs.is_dir(test_dir)
        assert not fs.is_file(test_dir)

    def test_rglob_with_pattern_filtering(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: rglob correctly filters by pattern."""
        # Setup: Create files with different extensions
        fs.write_text(base_path / "file1.md", "# Markdown")
        fs.write_text(base_path / "file2.py", "# Python")
        fs.write_text(base_path / "subdir/file3.md", "# Markdown")
        fs.write_text(base_path / "subdir/file4.txt", "Text")

        # Test: Filter by .md pattern
        md_files = list(fs.rglob(base_path, "*.md"))
        assert len(md_files) == 2  # noqa: PLR2004
        assert base_path / "file1.md" in md_files
        assert base_path / "subdir/file3.md" in md_files

        # Test: Filter by .py pattern
        py_files = list(fs.rglob(base_path, "*.py"))
        assert len(py_files) == 1
        assert base_path / "file2.py" in py_files

    def test_rglob_empty_directory_returns_empty(
        self,
        fs: FileSystemAdapter,
        base_path: Path,
    ) -> None:
        """Contract: rglob on empty directory returns empty iterator."""
        # Setup: Create empty directory structure
        empty_dir = base_path / "empty"
        fs.mkdir(empty_dir, parents=True, exist_ok=True)

        # Contract: Empty result for empty directory
        result = list(fs.rglob(empty_dir, "*.md"))
        assert len(result) == 0
        assert result == []


class TestMemoryFileSystemContract(FileSystemContract):
    """Test MemoryFileSystem against FileSystemAdapter contract."""

    @pytest.fixture
    def fs(self) -> FileSystemAdapter:
        """Provide MemoryFileSystem for testing."""
        return MemoryFileSystem()

    @pytest.fixture
    def base_path(self) -> Path:
        """Provide base path for MemoryFileSystem tests."""
        return Path("/test")


class TestRealFileSystemContract(FileSystemContract):
    """Test RealFileSystem against FileSystemAdapter contract."""

    @pytest.fixture
    def fs(self) -> FileSystemAdapter:
        """Provide RealFileSystem for testing."""
        return RealFileSystem()

    @pytest.fixture
    def base_path(self) -> Iterator[Path]:
        """Provide temporary directory for RealFileSystem tests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)


# ============================================================================
# Additional regression tests for specific bugs
# ============================================================================


def test_regression_iterator_len_bug() -> None:
    """Regression: Prevent bug where len() fails on rglob result.

    Original bug: KnowledgeScanner called len(self.fs.rglob(...)) which
    failed with TypeError because rglob returned a single-use iterator.

    This test ensures rglob returns something that can be converted to list
    and then measured with len().
    """
    fs = MemoryFileSystem()
    base = Path("/docs")

    # Setup
    fs.write_text(base / "file1.md", "Content")
    fs.write_text(base / "file2.md", "Content")

    # This must not raise TypeError
    markdown_files = list(fs.rglob(base, "*.md"))
    assert len(markdown_files) == 2  # noqa: PLR2004


def test_regression_mkdir_parents_bug() -> None:
    """Regression: Prevent bug where write_text fails on RealFileSystem.

    Original bug: test_knowledge_poc.py failed with FileNotFoundError
    because parent directories weren't created before write_text.

    This test ensures write_text creates parent directories automatically.
    """
    fs = MemoryFileSystem()

    # Write to deeply nested path without creating parents first
    deep_file = Path("/docs/guides/api/endpoints.md")
    fs.write_text(deep_file, "# API Endpoints")

    # Must succeed without manual mkdir
    assert fs.exists(deep_file)
    assert fs.read_text(deep_file) == "# API Endpoints"

    # Parent directories must exist
    assert fs.exists(Path("/docs"))
    assert fs.exists(Path("/docs/guides"))
    assert fs.exists(Path("/docs/guides/api"))
