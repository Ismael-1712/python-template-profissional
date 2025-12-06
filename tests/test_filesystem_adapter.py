"""Test suite for FileSystem Abstraction Layer.

This module tests the FileSystemAdapter protocol and its implementations:
- MemoryFileSystem: In-memory implementation for unit testing
- RealFileSystem: Production implementation using real disk operations

Author: DevOps Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.utils.filesystem import MemoryFileSystem, RealFileSystem


class TestMemoryFileSystem:
    """Test suite for MemoryFileSystem implementation."""

    def test_write_and_read(self) -> None:
        """Test basic write and read operations."""
        fs = MemoryFileSystem()

        # Write a file
        test_file = Path("config/settings.yaml")
        content = "database:\n  host: localhost\n  port: 5432"
        fs.write_text(test_file, content)

        # Read it back
        assert fs.read_text(test_file) == content
        assert fs.exists(test_file)
        assert fs.is_file(test_file)

    def test_parent_directories_auto_creation(self) -> None:
        """Test automatic parent directory creation."""
        fs = MemoryFileSystem()

        # Writing should auto-create parent directories
        nested_file = Path("deep/nested/structure/file.txt")
        fs.write_text(nested_file, "data")

        # Verify parents exist
        assert fs.is_dir(Path("deep"))
        assert fs.is_dir(Path("deep/nested"))
        assert fs.is_dir(Path("deep/nested/structure"))
        assert fs.is_file(nested_file)

    def test_glob_pattern_matching(self) -> None:
        """Test glob pattern matching."""
        fs = MemoryFileSystem()

        # Create multiple test files
        fs.write_text(Path("tests/test_foo.py"), "# test foo")
        fs.write_text(Path("tests/test_bar.py"), "# test bar")
        fs.write_text(Path("tests/conftest.py"), "# conftest")
        fs.write_text(Path("src/main.py"), "# main")

        # Glob for test files
        test_files = fs.glob(Path("tests"), "test_*.py")

        expected_count = 2
        assert len(test_files) == expected_count
        assert Path("tests/test_foo.py") in test_files
        assert Path("tests/test_bar.py") in test_files
        assert Path("tests/conftest.py") not in test_files

    def test_rglob_recursive_search(self) -> None:
        """Test recursive glob pattern matching."""
        fs = MemoryFileSystem()

        # Create nested directory structure with multiple levels
        fs.write_text(Path("project/src/main.py"), "# main")
        fs.write_text(Path("project/src/utils/helpers.py"), "# helpers")
        fs.write_text(Path("project/tests/test_main.py"), "# test main")
        fs.write_text(Path("project/tests/unit/test_helpers.py"), "# test helpers")
        fs.write_text(Path("project/tests/integration/test_api.py"), "# test api")
        fs.write_text(Path("project/docs/readme.txt"), "# readme")
        fs.write_text(Path("project/config.yaml"), "# config")

        # Search recursively for all .py files
        py_files = fs.rglob(Path("project"), "*.py")

        # Should find all 5 Python files across all subdirectories
        expected_count = 5
        assert len(py_files) == expected_count
        assert Path("project/src/main.py") in py_files
        assert Path("project/src/utils/helpers.py") in py_files
        assert Path("project/tests/test_main.py") in py_files
        assert Path("project/tests/unit/test_helpers.py") in py_files
        assert Path("project/tests/integration/test_api.py") in py_files

        # Should not find non-.py files
        assert Path("project/docs/readme.txt") not in py_files
        assert Path("project/config.yaml") not in py_files

    def test_rglob_with_specific_pattern(self) -> None:
        """Test rglob with specific filename pattern."""
        fs = MemoryFileSystem()

        # Create test files at different levels
        fs.write_text(Path("tests/test_foo.py"), "# test foo")
        fs.write_text(Path("tests/unit/test_bar.py"), "# test bar")
        fs.write_text(Path("tests/unit/helper.py"), "# helper")
        fs.write_text(Path("tests/integration/test_baz.py"), "# test baz")

        # Search recursively only for test_*.py files
        test_files = fs.rglob(Path("tests"), "test_*.py")

        # Should find only files starting with "test_"
        expected_count = 3
        assert len(test_files) == expected_count
        assert Path("tests/test_foo.py") in test_files
        assert Path("tests/unit/test_bar.py") in test_files
        assert Path("tests/integration/test_baz.py") in test_files
        assert Path("tests/unit/helper.py") not in test_files

    def test_rglob_empty_directory(self) -> None:
        """Test rglob on empty directory structure."""
        fs = MemoryFileSystem()

        # Create empty directory structure
        fs.mkdir(Path("empty/sub1/sub2"))

        # Search should return empty list
        results = fs.rglob(Path("empty"), "*.py")
        assert len(results) == 0
        assert results == []

    def test_file_copy(self) -> None:
        """Test file copying."""
        fs = MemoryFileSystem()

        # Create source file
        src = Path("original.txt")
        content = "original content"
        fs.write_text(src, content)

        # Copy to destination
        dst = Path("backup/copy.txt")
        fs.copy(src, dst)

        # Verify both exist with same content
        assert fs.exists(dst)
        assert fs.read_text(dst) == content
        assert fs.read_text(src) == content

    def test_file_not_found_error(self) -> None:
        """Test FileNotFoundError is raised correctly."""
        fs = MemoryFileSystem()

        with pytest.raises(FileNotFoundError, match="File not found"):
            fs.read_text(Path("nonexistent.txt"))

    def test_copy_nonexistent_source(self) -> None:
        """Test copy raises FileNotFoundError for missing source."""
        fs = MemoryFileSystem()

        with pytest.raises(FileNotFoundError, match="Source file not found"):
            fs.copy(Path("nonexistent.txt"), Path("dest.txt"))

    def test_mkdir_explicit(self) -> None:
        """Test explicit directory creation."""
        fs = MemoryFileSystem()

        # Create directory explicitly
        dir_path = Path("data/cache")
        fs.mkdir(dir_path, parents=True, exist_ok=True)

        assert fs.exists(dir_path)
        assert fs.is_dir(dir_path)
        assert not fs.is_file(dir_path)

        # Creating again with exist_ok=True should not raise
        fs.mkdir(dir_path, parents=True, exist_ok=True)

        # Creating with exist_ok=False should raise
        with pytest.raises(FileExistsError, match="already exists"):
            fs.mkdir(dir_path, parents=True, exist_ok=False)

    def test_isolation_between_instances(self) -> None:
        """Test that different instances are isolated."""
        fs1 = MemoryFileSystem()
        fs2 = MemoryFileSystem()

        # Write to fs1
        fs1.write_text(Path("file.txt"), "fs1 data")

        # fs2 should not see it
        assert fs1.exists(Path("file.txt"))
        assert not fs2.exists(Path("file.txt"))

    def test_encoding_parameter(self) -> None:
        """Test encoding parameter is accepted (though ignored in memory)."""
        fs = MemoryFileSystem()

        # Write with custom encoding
        test_file = Path("encoded.txt")
        content = "Olá, Mundo! 你好世界"
        fs.write_text(test_file, content, encoding="utf-8")

        # Read with custom encoding
        result = fs.read_text(test_file, encoding="utf-8")
        assert result == content


class TestRealFileSystem:
    """Test suite for RealFileSystem implementation."""

    def test_write_and_read(self, tmp_path: Path) -> None:
        """Test basic write and read operations on real filesystem."""
        fs = RealFileSystem()

        # Write a file
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        fs.write_text(test_file, content)

        # Read it back
        assert fs.read_text(test_file) == content
        assert fs.exists(test_file)
        assert fs.is_file(test_file)

    def test_parent_directories_auto_creation(self, tmp_path: Path) -> None:
        """Test automatic parent directory creation on real filesystem."""
        fs = RealFileSystem()

        # Writing should auto-create parent directories
        nested_file = tmp_path / "deep/nested/structure/file.txt"
        fs.write_text(nested_file, "data")

        # Verify parents exist
        assert fs.is_dir(tmp_path / "deep")
        assert fs.is_dir(tmp_path / "deep/nested")
        assert fs.is_dir(tmp_path / "deep/nested/structure")
        assert fs.is_file(nested_file)

    def test_glob_pattern_matching(self, tmp_path: Path) -> None:
        """Test glob pattern matching on real filesystem."""
        fs = RealFileSystem()

        # Create test directory
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        # Create multiple test files
        fs.write_text(test_dir / "test_foo.py", "# test foo")
        fs.write_text(test_dir / "test_bar.py", "# test bar")
        fs.write_text(test_dir / "conftest.py", "# conftest")

        # Glob for test files
        test_files = fs.glob(test_dir, "test_*.py")

        expected_count = 2
        assert len(test_files) == expected_count
        assert test_dir / "test_foo.py" in test_files
        assert test_dir / "test_bar.py" in test_files
        assert test_dir / "conftest.py" not in test_files

    def test_rglob_recursive_search(self, tmp_path: Path) -> None:
        """Test recursive glob pattern matching on real filesystem."""
        fs = RealFileSystem()

        # Create nested directory structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create files at multiple levels
        fs.write_text(project_dir / "main.py", "# main")
        fs.write_text(project_dir / "src/utils.py", "# utils")
        fs.write_text(project_dir / "src/core/engine.py", "# engine")
        fs.write_text(project_dir / "tests/test_main.py", "# test main")
        fs.write_text(project_dir / "tests/unit/test_utils.py", "# test utils")
        fs.write_text(project_dir / "docs/readme.txt", "# readme")

        # Search recursively for all .py files
        py_files = fs.rglob(project_dir, "*.py")

        # Should find all 5 Python files
        expected_count = 5
        assert len(py_files) == expected_count
        assert project_dir / "main.py" in py_files
        assert project_dir / "src/utils.py" in py_files
        assert project_dir / "src/core/engine.py" in py_files
        assert project_dir / "tests/test_main.py" in py_files
        assert project_dir / "tests/unit/test_utils.py" in py_files

        # Should not find non-.py files
        assert project_dir / "docs/readme.txt" not in py_files

    def test_rglob_with_specific_pattern(self, tmp_path: Path) -> None:
        """Test rglob with specific filename pattern on real filesystem."""
        fs = RealFileSystem()

        # Create test directory structure
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # Create test files at different levels
        fs.write_text(tests_dir / "test_foo.py", "# test foo")
        fs.write_text(tests_dir / "unit/test_bar.py", "# test bar")
        fs.write_text(tests_dir / "unit/helper.py", "# helper")
        fs.write_text(tests_dir / "integration/test_baz.py", "# test baz")

        # Search recursively only for test_*.py files
        test_files = fs.rglob(tests_dir, "test_*.py")

        # Should find only files starting with "test_"
        expected_count = 3
        assert len(test_files) == expected_count
        assert tests_dir / "test_foo.py" in test_files
        assert tests_dir / "unit/test_bar.py" in test_files
        assert tests_dir / "integration/test_baz.py" in test_files
        assert tests_dir / "unit/helper.py" not in test_files

    def test_file_copy(self, tmp_path: Path) -> None:
        """Test file copying on real filesystem."""
        fs = RealFileSystem()

        # Create source file
        src = tmp_path / "original.txt"
        content = "original content"
        fs.write_text(src, content)

        # Copy to destination
        dst = tmp_path / "backup/copy.txt"
        fs.copy(src, dst)

        # Verify both exist with same content
        assert fs.exists(dst)
        assert fs.read_text(dst) == content
        assert fs.read_text(src) == content

    def test_mkdir_explicit(self, tmp_path: Path) -> None:
        """Test explicit directory creation on real filesystem."""
        fs = RealFileSystem()

        # Create directory explicitly
        dir_path = tmp_path / "data/cache"
        fs.mkdir(dir_path, parents=True, exist_ok=True)

        assert fs.exists(dir_path)
        assert fs.is_dir(dir_path)
        assert not fs.is_file(dir_path)

        # Creating again with exist_ok=True should not raise
        fs.mkdir(dir_path, parents=True, exist_ok=True)


class TestIntegrationScenarios:
    """Integration tests demonstrating real-world usage patterns."""

    def test_config_loader_with_memory_fs(self) -> None:
        """Test config loader pattern with MemoryFileSystem."""

        def load_config(fs, config_path: Path) -> dict:
            """Load YAML config from filesystem."""
            import yaml

            if not fs.exists(config_path):
                return {}

            content = fs.read_text(config_path)
            return yaml.safe_load(content)

        # Test with MemoryFileSystem (no disk I/O!)
        fs = MemoryFileSystem()
        config_path = Path("config.yaml")

        # Test missing file case
        assert load_config(fs, config_path) == {}

        # Test existing file case
        fs.write_text(config_path, "debug: true\nport: 8080")
        config = load_config(fs, config_path)
        assert config["debug"] is True
        port_number = 8080
        assert config["port"] == port_number

    def test_backup_creation_pattern(self) -> None:
        """Test backup creation pattern common in DevOps tools."""
        fs = MemoryFileSystem()

        # Original file
        original = Path("important.conf")
        fs.write_text(original, "version: 1.0")

        # Create backup
        backup = Path("backups/important.conf.backup")
        fs.copy(original, backup)

        # Modify original
        fs.write_text(original, "version: 2.0")

        # Verify backup preserved old version
        assert fs.read_text(backup) == "version: 1.0"
        assert fs.read_text(original) == "version: 2.0"

    def test_file_scanner_pattern(self) -> None:
        """Test file discovery pattern used in code analysis tools."""
        fs = MemoryFileSystem()

        # Create project structure
        fs.write_text(Path("src/main.py"), "# main")
        fs.write_text(Path("src/utils.py"), "# utils")
        fs.write_text(Path("tests/test_main.py"), "# test main")
        fs.write_text(Path("tests/test_utils.py"), "# test utils")

        # Discover Python files
        src_files = fs.glob(Path("src"), "*.py")
        test_files = fs.glob(Path("tests"), "test_*.py")

        expected_src_count = 2
        expected_test_count = 2
        assert len(src_files) == expected_src_count
        assert len(test_files) == expected_test_count


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
