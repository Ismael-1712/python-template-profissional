"""Unit tests for CORTEX Code Link Scanner.

Tests the CodeLinkScanner class which validates links between
documentation and code files.

Author: Engineering Team
License: MIT
"""

import os
from pathlib import Path

import pytest

from scripts.core.cortex.models import LinkCheckResult
from scripts.core.cortex.scanner import CodeLinkScanner


class TestCodeLinkScanner:
    """Test suite for CodeLinkScanner class."""

    @pytest.fixture
    def workspace_root(self, tmp_path: Path) -> Path:
        """Create a temporary workspace root for testing.

        Args:
            tmp_path: pytest temporary directory fixture

        Returns:
            Path to temporary workspace root
        """
        return tmp_path

    @pytest.fixture
    def scanner(self, workspace_root: Path) -> CodeLinkScanner:
        """Create a CodeLinkScanner instance for testing.

        Args:
            workspace_root: Temporary workspace root path

        Returns:
            Configured CodeLinkScanner instance
        """
        return CodeLinkScanner(workspace_root=workspace_root)

    # ===================================================================
    # Tests for check_python_files
    # ===================================================================

    def test_check_python_files_all_exist(
        self, scanner: CodeLinkScanner, workspace_root: Path
    ) -> None:
        """Test checking Python files when all files exist."""
        # Create test files
        (workspace_root / "src").mkdir()
        (workspace_root / "src" / "main.py").touch()
        (workspace_root / "src" / "utils.py").touch()

        # Check files
        errors = scanner.check_python_files(["src/main.py", "src/utils.py"])

        # Should have no errors
        assert errors == []

    def test_check_python_files_not_found(self, scanner: CodeLinkScanner) -> None:
        """Test checking Python files when some don't exist."""
        # Check non-existent files
        errors = scanner.check_python_files(["src/missing.py", "lib/absent.py"])

        # Should have errors for both files
        assert len(errors) == 2
        assert "Python file not found: src/missing.py" in errors
        assert "Python file not found: lib/absent.py" in errors

    def test_check_python_files_mixed(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking mix of existing and missing Python files."""
        # Create one file
        (workspace_root / "src").mkdir()
        (workspace_root / "src" / "exists.py").touch()

        # Check mix of files
        errors = scanner.check_python_files(["src/exists.py", "src/missing.py"])

        # Should have error only for missing file
        assert len(errors) == 1
        assert "Python file not found: src/missing.py" in errors

    def test_check_python_files_is_directory(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking when path is a directory, not a file."""
        # Create directory
        (workspace_root / "src").mkdir()

        # Check directory as if it were a file
        errors = scanner.check_python_files(["src"])

        # Should have error about not being a file
        assert len(errors) == 1
        assert "Path is not a file: src" in errors

    def test_check_python_files_not_python_extension(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking when file exists but is not a .py file."""
        # Create non-Python file
        (workspace_root / "README.md").touch()

        # Check non-Python file
        errors = scanner.check_python_files(["README.md"])

        # Should have error about not being Python file
        assert len(errors) == 1
        assert "Not a Python file: README.md" in errors

    def test_check_python_files_empty_list(self, scanner: CodeLinkScanner) -> None:
        """Test checking with empty list of files."""
        errors = scanner.check_python_files([])
        assert errors == []

    # ===================================================================
    # Tests for check_doc_links
    # ===================================================================

    def test_check_doc_links_all_exist(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking documentation files when all exist."""
        # Create test files
        (workspace_root / "docs").mkdir()
        (workspace_root / "docs" / "guide.md").touch()
        (workspace_root / "docs" / "reference.md").touch()

        # Check files
        errors = scanner.check_doc_links(["docs/guide.md", "docs/reference.md"])

        # Should have no errors
        assert errors == []

    def test_check_doc_links_not_found(self, scanner: CodeLinkScanner) -> None:
        """Test checking documentation files when some don't exist."""
        # Check non-existent files
        errors = scanner.check_doc_links(["docs/missing.md", "guides/absent.md"])

        # Should have errors for both files
        assert len(errors) == 2
        assert "Documentation file not found: docs/missing.md" in errors
        assert "Documentation file not found: guides/absent.md" in errors

    def test_check_doc_links_mixed(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking mix of existing and missing doc files."""
        # Create one file
        (workspace_root / "docs").mkdir()
        (workspace_root / "docs" / "exists.md").touch()

        # Check mix of files
        errors = scanner.check_doc_links(["docs/exists.md", "docs/missing.md"])

        # Should have error only for missing file
        assert len(errors) == 1
        assert "Documentation file not found: docs/missing.md" in errors

    def test_check_doc_links_is_directory(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking when path is a directory, not a file."""
        # Create directory
        (workspace_root / "docs").mkdir()

        # Check directory as if it were a file
        errors = scanner.check_doc_links(["docs"])

        # Should have error about not being a file
        assert len(errors) == 1
        assert "Path is not a file: docs" in errors

    def test_check_doc_links_not_markdown_extension(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking when file exists but is not markdown."""
        # Create non-markdown file
        (workspace_root / "script.py").touch()

        # Check non-markdown file
        errors = scanner.check_doc_links(["script.py"])

        # Should have error about not being markdown
        assert len(errors) == 1
        assert "Not a Markdown file: script.py" in errors

    def test_check_doc_links_markdown_extension(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test that .markdown extension is also accepted."""
        # Create file with .markdown extension
        (workspace_root / "docs").mkdir()
        (workspace_root / "docs" / "guide.markdown").touch()

        # Check file
        errors = scanner.check_doc_links(["docs/guide.markdown"])

        # Should have no errors
        assert errors == []

    def test_check_doc_links_empty_list(self, scanner: CodeLinkScanner) -> None:
        """Test checking with empty list of files."""
        errors = scanner.check_doc_links([])
        assert errors == []

    # ===================================================================
    # Tests for check_all_links
    # ===================================================================

    def test_check_all_links_no_errors(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking all links when everything exists."""
        # Create test files
        (workspace_root / "src").mkdir()
        (workspace_root / "src" / "main.py").touch()
        (workspace_root / "docs").mkdir()
        (workspace_root / "docs" / "guide.md").touch()
        doc_file = workspace_root / "docs" / "index.md"
        doc_file.touch()

        # Check all links
        result = scanner.check_all_links(
            linked_code=["src/main.py"],
            related_docs=["docs/guide.md"],
            doc_file=doc_file,
        )

        # Should be a LinkCheckResult
        assert isinstance(result, LinkCheckResult)
        assert result.file == doc_file
        assert result.broken_code_links == []
        assert result.broken_doc_links == []

    def test_check_all_links_with_errors(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking all links when some files are missing."""
        doc_file = workspace_root / "docs" / "index.md"

        # Check links to non-existent files
        result = scanner.check_all_links(
            linked_code=["src/missing.py"],
            related_docs=["docs/absent.md"],
            doc_file=doc_file,
        )

        # Should have errors for both
        assert isinstance(result, LinkCheckResult)
        assert result.file == doc_file
        total_errors = len(result.broken_code_links) + len(result.broken_doc_links)
        assert total_errors == 2
        assert any("Python file not found" in err for err in result.broken_code_links)
        assert any(
            "Documentation file not found" in err for err in result.broken_doc_links
        )

    def test_check_all_links_empty_lists(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test checking all links with empty lists."""
        doc_file = workspace_root / "docs" / "index.md"

        result = scanner.check_all_links(
            linked_code=[],
            related_docs=[],
            doc_file=doc_file,
        )

        assert isinstance(result, LinkCheckResult)
        assert result.file == doc_file
        assert result.broken_code_links == []
        assert result.broken_doc_links == []

    # ===================================================================
    # Tests for analyze_python_exports (Bonus Feature)
    # ===================================================================

    def test_analyze_python_exports_file_not_found(
        self,
        scanner: CodeLinkScanner,
    ) -> None:
        """Test analyzing non-existent Python file."""
        result = scanner.analyze_python_exports("src/missing.py")

        assert result["exists"] is False
        assert "File not found" in result["error"]
        assert result["classes"] == []
        assert result["functions"] == []

    def test_analyze_python_exports_is_directory(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test analyzing when path is a directory."""
        (workspace_root / "src").mkdir()

        result = scanner.analyze_python_exports("src")

        assert result["exists"] is False
        assert "not a file" in result["error"]

    def test_analyze_python_exports_success(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test analyzing valid Python file with classes and functions."""
        # Create Python file with classes and functions
        python_code = """
class MyClass:
    def method(self):
        pass

class AnotherClass:
    pass

def my_function():
    pass

def another_function():
    return 42
"""
        (workspace_root / "src").mkdir()
        python_file = workspace_root / "src" / "module.py"
        python_file.write_text(python_code)

        result = scanner.analyze_python_exports("src/module.py")

        assert result["exists"] is True
        assert result["error"] is None
        assert "MyClass" in result["classes"]
        assert "AnotherClass" in result["classes"]
        assert "my_function" in result["functions"]
        assert "another_function" in result["functions"]
        assert len(result["classes"]) == 2
        assert len(result["functions"]) == 2

    def test_analyze_python_exports_with_symbols(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test analyzing Python file checking for specific symbols."""
        python_code = """
class ExistingClass:
    pass

def existing_function():
    pass
"""
        (workspace_root / "src").mkdir()
        python_file = workspace_root / "src" / "module.py"
        python_file.write_text(python_code)

        # Check for some symbols that exist and some that don't
        result = scanner.analyze_python_exports(
            "src/module.py",
            symbols=[
                "ExistingClass",
                "MissingClass",
                "existing_function",
                "missing_func",
            ],
        )

        assert result["exists"] is True
        assert result["error"] is None
        assert set(result["missing_symbols"]) == {"MissingClass", "missing_func"}

    def test_analyze_python_exports_syntax_error(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test analyzing Python file with syntax errors."""
        # Create Python file with invalid syntax
        python_code = "class InvalidSyntax\n    pass"  # Missing colon
        (workspace_root / "src").mkdir()
        python_file = workspace_root / "src" / "invalid.py"
        python_file.write_text(python_code)

        result = scanner.analyze_python_exports("src/invalid.py")

        assert result["exists"] is True
        assert "syntax error" in result["error"].lower()

    def test_analyze_python_exports_empty_file(
        self,
        scanner: CodeLinkScanner,
        workspace_root: Path,
    ) -> None:
        """Test analyzing empty Python file."""
        (workspace_root / "src").mkdir()
        python_file = workspace_root / "src" / "empty.py"
        python_file.write_text("")

        result = scanner.analyze_python_exports("src/empty.py")

        assert result["exists"] is True
        assert result["error"] is None
        assert result["classes"] == []
        assert result["functions"] == []

    # ===================================================================
    # Tests for scanner initialization
    # ===================================================================

    def test_scanner_initialization(self, workspace_root: Path) -> None:
        """Test that scanner initializes correctly."""
        scanner = CodeLinkScanner(workspace_root=workspace_root)

        assert scanner.workspace_root == workspace_root.resolve()

    def test_scanner_resolves_relative_paths(self, tmp_path: Path) -> None:
        """Test that scanner resolves relative workspace paths."""
        # Create a subdirectory
        subdir = tmp_path / "project"
        subdir.mkdir()

        # Initialize scanner with relative path

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            scanner = CodeLinkScanner(workspace_root=Path("project"))
            assert scanner.workspace_root == subdir.resolve()
        finally:
            os.chdir(original_cwd)
