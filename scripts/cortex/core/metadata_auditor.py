"""Metadata Auditor - Validates documentation frontmatter and links.

This module contains the business logic for auditing Markdown documentation
files. It validates YAML frontmatter, checks required metadata fields, and
verifies that linked code/documentation files exist.

Extracted from cli.py as part of Iteration 3: God Function Elimination.

Architecture: Core Domain Logic (Hexagonal Architecture)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.core.cortex.metadata import FrontmatterParseError, FrontmatterParser
from scripts.core.cortex.models import DocumentMetadata
from scripts.core.cortex.scanner import CodeLinkScanner


@dataclass(frozen=True)
class FileAuditResult:
    """Result of auditing a single file."""

    file_path: Path
    """The file that was audited (relative to workspace root)."""

    errors: list[str]
    """List of error messages found in this file."""

    warnings: list[str]
    """List of warning messages found in this file."""

    metadata: DocumentMetadata | None
    """Parsed metadata if successful, None if parsing failed."""

    @property
    def has_errors(self) -> bool:
        """Check if this file has any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if this file has any warnings."""
        return len(self.warnings) > 0

    @property
    def is_clean(self) -> bool:
        """Check if this file passed all checks."""
        return not self.has_errors and not self.has_warnings


@dataclass(frozen=True)
class AuditReport:
    """Complete audit report for all files."""

    files_scanned: int
    """Total number of files scanned."""

    file_results: list[FileAuditResult]
    """Individual results for each file."""

    root_violations: list[str]
    """Files in project root that violate Root Lockdown policy."""

    @property
    def total_errors(self) -> int:
        """Calculate total number of errors across all files."""
        file_errors = sum(len(r.errors) for r in self.file_results)
        return file_errors + len(self.root_violations)

    @property
    def total_warnings(self) -> int:
        """Calculate total number of warnings across all files."""
        return sum(len(r.warnings) for r in self.file_results)

    @property
    def files_with_errors(self) -> list[Path]:
        """Get list of files that have errors."""
        result = []
        if self.root_violations:
            result.append(Path("PROJECT_ROOT"))
        result.extend(r.file_path for r in self.file_results if r.has_errors)
        return result

    @property
    def is_successful(self) -> bool:
        """Check if audit passed (no errors)."""
        return self.total_errors == 0


class MetadataAuditor:
    """Auditor for documentation metadata and links.

    This class encapsulates the business logic for auditing Markdown files.
    It validates YAML frontmatter, checks required fields, verifies code links,
    and enforces the Root Lockdown policy.

    Usage:
        auditor = MetadataAuditor(workspace_root=Path.cwd())
        report = auditor.audit(md_files)

        if not report.is_successful:
            print(f"Found {report.total_errors} errors")
    """

    def __init__(self, workspace_root: Path) -> None:
        """Initialize the auditor.

        Args:
            workspace_root: Root directory of the workspace/project.
        """
        self.workspace_root = workspace_root
        self.parser = FrontmatterParser()
        self.code_scanner = CodeLinkScanner(workspace_root=workspace_root)

    def check_root_lockdown(self) -> list[str]:
        """Check for unauthorized .md files in project root.

        Returns:
            List of violations (file paths that violate Root Lockdown policy).
        """
        return self.code_scanner.check_root_markdown_files()

    def audit_single_file(self, md_file: Path) -> FileAuditResult:
        """Audit a single Markdown file.

        Args:
            md_file: Path to the Markdown file to audit.

        Returns:
            FileAuditResult containing errors, warnings, and metadata.
        """
        relative_path = md_file.resolve().relative_to(self.workspace_root.resolve())
        errors: list[str] = []
        warnings: list[str] = []
        metadata: DocumentMetadata | None = None

        # 1. Parse and validate frontmatter
        try:
            metadata = self.parser.parse_file(md_file)
        except (FrontmatterParseError, ValueError, TypeError) as e:
            errors.append(f"Frontmatter error: {e}")

        # 2. Check code and documentation links
        if metadata:
            link_result = self.code_scanner.check_all_links(
                linked_code=metadata.linked_code or [],
                related_docs=metadata.related_docs or [],
                doc_file=md_file,
                metadata=metadata,
            )

            if link_result.broken_code_links:
                errors.extend(link_result.broken_code_links)

            if link_result.broken_doc_links:
                errors.extend(link_result.broken_doc_links)

        return FileAuditResult(
            file_path=relative_path,
            errors=errors,
            warnings=warnings,
            metadata=metadata,
        )

    def audit(self, md_files: list[Path]) -> AuditReport:
        """Audit multiple Markdown files.

        This is the main entry point for metadata auditing.

        Args:
            md_files: List of Markdown files to audit.

        Returns:
            AuditReport containing results for all files.
        """
        # Check Root Lockdown violations
        root_violations = self.check_root_lockdown()

        # Audit each file
        file_results = [self.audit_single_file(md_file) for md_file in md_files]

        return AuditReport(
            files_scanned=len(md_files),
            file_results=file_results,
            root_violations=root_violations,
        )
