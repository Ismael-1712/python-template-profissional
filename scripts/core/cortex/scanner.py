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

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

from scripts.core.cortex.models import DocStatus, DocumentMetadata, LinkCheckResult

logger = logging.getLogger(__name__)

# Allowlist de arquivos Markdown permitidos na raiz do projeto
ALLOWED_ROOT_MARKDOWN_FILES = frozenset(
    [
        "README.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "LICENSE",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
    ],
)


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

    def _should_ignore_broken_links(
        self,
        doc_file: Path,
        metadata: DocumentMetadata | None = None,
    ) -> bool:
        """Determine if broken links should be ignored for a document.

        Links are ignored if:
        - Document status is 'archived' or 'deprecated'
        - Document is in docs/history/ directory

        Args:
            doc_file: Path to the documentation file
            metadata: Optional parsed metadata for the document

        Returns:
            True if broken links should be ignored, False otherwise
        """
        # Check metadata status
        if metadata and metadata.status in (DocStatus.ARCHIVED, DocStatus.DEPRECATED):
            logger.debug(
                "Ignoring broken links for %s (status: %s)",
                doc_file,
                metadata.status.value,
            )
            return True

        # Check if file is in history directory
        try:
            relative_path = doc_file.relative_to(self.workspace_root)
            path_parts = relative_path.parts
            if "history" in path_parts:
                logger.debug(
                    "Ignoring broken links for %s (in history directory)",
                    doc_file,
                )
                return True
        except ValueError:
            # File is not relative to workspace_root (Security/Logic anomaly)
            logger.warning(
                "⚠️  PATH ANOMALY: File '%s' is outside workspace root '%s'. "
                "Skipping link check.",
                doc_file,
                self.workspace_root,
            )
            return False

        return False

    def check_python_files(
        self,
        linked_code: list[str],
        doc_file: Path | None = None,
        metadata: DocumentMetadata | None = None,
    ) -> list[str]:
        """Verify that Python files referenced in frontmatter exist.

        Args:
            linked_code: List of relative paths to Python files
            doc_file: Path to the documentation file being checked
            metadata: Optional parsed metadata for the document

        Returns:
            List of error messages for files that don't exist
        """
        # Check if we should ignore broken links for archived/deprecated docs
        if doc_file and self._should_ignore_broken_links(doc_file, metadata):
            logger.debug(
                "Skipping Python file validation for archived/deprecated document: %s",
                doc_file,
            )
            return []

        errors = []

        for relative_path in linked_code:
            # Resolve path relative to workspace root
            full_path = self.workspace_root / relative_path

            # Check if file exists and is a file (not directory)
            if not full_path.exists():
                errors.append(f"Python file not found: {relative_path}")
                logger.warning("Missing Python file: %s", full_path)
            elif not full_path.is_file():
                errors.append(f"Path is not a file: {relative_path}")
                logger.warning("Path is not a file: %s", full_path)
            elif not relative_path.endswith(".py"):
                errors.append(f"Not a Python file: {relative_path}")
                logger.warning("Not a Python file: %s", full_path)
            else:
                logger.debug("Python file exists: %s", relative_path)

        return errors

    def check_doc_links(
        self,
        related_docs: list[str],
        doc_file: Path | None = None,
        metadata: DocumentMetadata | None = None,
    ) -> list[str]:
        """Verify that documentation files referenced in frontmatter exist.

        Args:
            related_docs: List of relative paths to markdown files
            doc_file: Path to the documentation file being checked
            metadata: Optional parsed metadata for the document

        Returns:
            List of error messages for files that don't exist
        """
        # Check if we should ignore broken links for archived/deprecated docs
        if doc_file and self._should_ignore_broken_links(doc_file, metadata):
            logger.debug(
                "Skipping doc link validation for archived/deprecated document: %s",
                doc_file,
            )
            return []

        errors = []

        for relative_path in related_docs:
            # Resolve path relative to workspace root
            full_path = self.workspace_root / relative_path

            # Check if file exists and is a file (not directory)
            if not full_path.exists():
                errors.append(f"Documentation file not found: {relative_path}")
                logger.warning("Missing doc file: %s", full_path)
            elif not full_path.is_file():
                errors.append(f"Path is not a file: {relative_path}")
                logger.warning("Path is not a file: %s", full_path)
            elif not relative_path.endswith((".md", ".markdown")):
                errors.append(f"Not a Markdown file: {relative_path}")
                logger.warning("Not a Markdown file: %s", full_path)
            else:
                logger.debug("Documentation file exists: %s", relative_path)

        return errors

    def check_all_links(
        self,
        linked_code: list[str],
        related_docs: list[str],
        doc_file: Path,
        metadata: DocumentMetadata | None = None,
    ) -> LinkCheckResult:
        """Check both code and documentation links for a document.

        Args:
            linked_code: List of relative paths to Python files
            related_docs: List of relative paths to markdown files
            doc_file: Path to the documentation file being checked
            metadata: Optional parsed metadata for the document

        Returns:
            LinkCheckResult with all broken links
        """
        # Check Python files
        code_errors = self.check_python_files(
            linked_code,
            doc_file=doc_file,
            metadata=metadata,
        )

        # Check documentation files
        doc_errors = self.check_doc_links(
            related_docs,
            doc_file=doc_file,
            metadata=metadata,
        )

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

    def check_root_markdown_files(self) -> list[str]:
        """Validate that only approved Markdown files exist in project root.

        This implements the "Root Lockdown" policy - only specific documentation
        files are allowed in the project root. All other documentation must
        reside in the docs/ directory.

        Returns:
            List of error messages for unauthorized .md files in root
        """
        errors = []

        # Get all .md files in root (non-recursive)
        root_md_files = [
            f
            for f in self.workspace_root.iterdir()
            if f.is_file() and f.suffix.lower() in (".md", ".markdown")
        ]

        for md_file in root_md_files:
            filename = md_file.name

            if filename not in ALLOWED_ROOT_MARKDOWN_FILES:
                allowed_files = ", ".join(sorted(ALLOWED_ROOT_MARKDOWN_FILES))
                error_msg = (
                    f"File placement violation: '{filename}' found in project root. "
                    "Documentation must reside in docs/, not project root. "
                    f"Allowed root files: {allowed_files}"
                )
                errors.append(error_msg)
                logger.warning("Root Lockdown violation: %s", filename)
            else:
                logger.debug("Approved root markdown file: %s", filename)

        if errors:
            logger.warning(
                "Found %d unauthorized markdown file(s) in project root",
                len(errors),
            )
        else:
            logger.debug("Root Lockdown check passed: All root .md files are approved")

        return errors
