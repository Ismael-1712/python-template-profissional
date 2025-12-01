"""CORTEX Code Link Scanner.

Module for validating links between documentation and code files.
Verifies that referenced files exist and optionally checks for
specific symbols (classes, functions) in Python files.

Usage:
    scanner = CodeLinkScanner(workspace_root=Path('/project'))
    errors = scanner.check_python_files(['src/main.py', 'src/utils.py'])
    doc_errors = scanner.check_doc_links(['docs/guide.md'])

Author: Engineering Team
License: MIT
"""

import ast
import logging
from pathlib import Path
from typing import Any

from scripts.core.cortex.models import LinkCheckResult

logger = logging.getLogger(__name__)


class CodeLinkScanner:
    """Scanner for validating links between documentation and code.

    Verifies that files referenced in documentation frontmatter actually
    exist in the workspace, and optionally validates that Python symbols
    (classes, functions) mentioned in docs exist in the linked code.

    Attributes:
        workspace_root: Root directory of the workspace
    """

    def __init__(self, workspace_root: Path) -> None:
        """Initialize the scanner.

        Args:
            workspace_root: Root directory of the workspace
        """
        self.workspace_root = workspace_root.resolve()
        logger.debug(f"Initialized CodeLinkScanner with root: {self.workspace_root}")

    def check_python_files(self, linked_code: list[str]) -> list[str]:
        """Verify that Python files referenced in frontmatter exist.

        Args:
            linked_code: List of relative paths to Python files

        Returns:
            List of error messages for files that don't exist
        """
        errors = []

        for relative_path in linked_code:
            # Resolve path relative to workspace root
            full_path = self.workspace_root / relative_path

            # Check if file exists and is a file (not directory)
            if not full_path.exists():
                errors.append(f"Python file not found: {relative_path}")
                logger.warning(f"Missing Python file: {full_path}")
            elif not full_path.is_file():
                errors.append(f"Path is not a file: {relative_path}")
                logger.warning(f"Path is not a file: {full_path}")
            elif not relative_path.endswith(".py"):
                errors.append(f"Not a Python file: {relative_path}")
                logger.warning(f"Not a Python file: {full_path}")
            else:
                logger.debug(f"Python file exists: {relative_path}")

        return errors

    def check_doc_links(self, related_docs: list[str]) -> list[str]:
        """Verify that documentation files referenced in frontmatter exist.

        Args:
            related_docs: List of relative paths to markdown files

        Returns:
            List of error messages for files that don't exist
        """
        errors = []

        for relative_path in related_docs:
            # Resolve path relative to workspace root
            full_path = self.workspace_root / relative_path

            # Check if file exists and is a file (not directory)
            if not full_path.exists():
                errors.append(f"Documentation file not found: {relative_path}")
                logger.warning(f"Missing doc file: {full_path}")
            elif not full_path.is_file():
                errors.append(f"Path is not a file: {relative_path}")
                logger.warning(f"Path is not a file: {full_path}")
            elif not relative_path.endswith((".md", ".markdown")):
                errors.append(f"Not a Markdown file: {relative_path}")
                logger.warning(f"Not a Markdown file: {full_path}")
            else:
                logger.debug(f"Documentation file exists: {relative_path}")

        return errors

    def check_all_links(
        self,
        linked_code: list[str],
        related_docs: list[str],
        doc_file: Path,
    ) -> LinkCheckResult:
        """Check both code and documentation links for a document.

        Args:
            linked_code: List of relative paths to Python files
            related_docs: List of relative paths to markdown files
            doc_file: Path to the documentation file being checked

        Returns:
            LinkCheckResult with all broken links
        """
        # Check Python files
        code_errors = self.check_python_files(linked_code)

        # Check documentation files
        doc_errors = self.check_doc_links(related_docs)

        return LinkCheckResult(
            file=doc_file,
            broken_code_links=code_errors,
            broken_doc_links=doc_errors,
        )

    def analyze_python_exports(
        self,
        python_file: str,
        symbols: list[str] | None = None,
    ) -> dict[str, Any]:
        """Analyze Python file to extract exported symbols using AST.

        This is a bonus feature that uses Python's AST module to parse
        Python files and extract class/function definitions. Can be used
        to verify that symbols mentioned in documentation actually exist.

        Args:
            python_file: Relative path to Python file
            symbols: Optional list of symbol names to check for

        Returns:
            Dictionary with:
                - 'exists': bool (file exists and is valid Python)
                - 'classes': list of class names found
                - 'functions': list of function names found
                - 'missing_symbols': list of requested symbols not found
                - 'error': error message if parsing failed
        """
        result: dict[str, Any] = {
            "exists": False,
            "classes": [],
            "functions": [],
            "missing_symbols": [],
            "error": None,
        }

        full_path = self.workspace_root / python_file

        # Check if file exists
        if not full_path.exists():
            result["error"] = f"File not found: {python_file}"
            return result

        if not full_path.is_file():
            result["error"] = f"Path is not a file: {python_file}"
            return result

        result["exists"] = True

        try:
            # Parse Python file with AST
            with open(full_path, encoding="utf-8") as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=str(full_path))

            # Extract top-level class and function definitions
            # Only iterate through top-level nodes to avoid counting methods
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    result["classes"].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    result["functions"].append(node.name)

            # Check for specific symbols if requested
            if symbols:
                all_symbols = set(result["classes"]) | set(result["functions"])
                result["missing_symbols"] = [s for s in symbols if s not in all_symbols]

            logger.debug(
                f"Analyzed {python_file}: "
                f"{len(result['classes'])} classes, "
                f"{len(result['functions'])} functions",
            )

        except SyntaxError as e:
            result["error"] = f"Python syntax error: {e}"
            logger.error(f"Syntax error parsing {python_file}: {e}")
        except Exception as e:
            result["error"] = f"Error analyzing file: {e}"
            logger.error(f"Error analyzing {python_file}: {e}", exc_info=True)

        return result
