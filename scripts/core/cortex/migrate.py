"""CORTEX Documentation Migration Module.

Migrates existing Markdown files to CORTEX format by adding YAML frontmatter
with intelligent inference of metadata fields.

Features:
- Automatic ID generation (kebab-case from filename)
- Type inference from directory structure
- Title extraction from first heading
- Code link detection via regex
- Dry-run mode for safe preview
- Batch processing with detailed reporting

Usage:
    from scripts.core.cortex.migrate import DocumentMigrator

    migrator = DocumentMigrator(workspace_root=Path("/project"))
    results = migrator.migrate_directory(Path("docs/"), dry_run=True)

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of a single file migration operation."""

    file_path: Path
    success: bool
    action: str  # "created", "updated", "skipped", "error"
    message: str
    inferred_metadata: dict[str, Any] | None = None
    error: str | None = None


class DocumentMigrator:
    """Migrates Markdown documentation to CORTEX format.

    Intelligently adds YAML frontmatter to existing documentation files
    by inferring metadata from file structure, content, and naming.

    Attributes:
        workspace_root: Root directory of the workspace
    """

    # Regex patterns for code detection
    PYTHON_FILE_PATTERN = re.compile(
        r"(?:scripts?|src|tests?)/[a-zA-Z0-9_/]+\.py\b",
        re.IGNORECASE,
    )

    # Pattern to detect existing frontmatter
    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\n.*?\n---\s*\n",
        re.DOTALL | re.MULTILINE,
    )

    def __init__(
        self,
        workspace_root: Path,
        fs: FileSystemAdapter | None = None,
    ) -> None:
        """Initialize the migrator.

        Args:
            workspace_root: Root directory of the workspace
            fs: FileSystemAdapter for I/O operations (default: RealFileSystem)
        """
        if fs is None:
            fs = RealFileSystem()
        self.fs = fs
        self.workspace_root = workspace_root.resolve()
        logger.debug(
            "Initialized DocumentMigrator with root: %s",
            self.workspace_root,
        )

    def _generate_id(self, file_path: Path) -> str:
        """Generate a kebab-case ID from filename.

        Args:
            file_path: Path to the markdown file

        Returns:
            Kebab-case ID string
        """
        name = file_path.stem.lower()
        # Replace underscores and spaces with hyphens
        name = name.replace("_", "-").replace(" ", "-")
        # Remove non-alphanumeric characters except hyphens
        name = "".join(c for c in name if c.isalnum() or c == "-")
        # Remove consecutive hyphens
        while "--" in name:
            name = name.replace("--", "-")
        # Remove leading/trailing hyphens
        return name.strip("-")

    def _infer_type(self, file_path: Path) -> str:
        """Infer document type from directory structure.

        Args:
            file_path: Path to the markdown file

        Returns:
            Document type (arch, guide, reference, history)
        """
        path_str = str(file_path).lower()

        if "architecture" in path_str or "arch" in path_str:
            return "arch"
        if "guide" in path_str or "tutorial" in path_str:
            return "guide"
        if "reference" in path_str or "api" in path_str or "ref" in path_str:
            return "reference"
        if "history" in path_str or "changelog" in path_str:
            return "history"

        # Default to guide
        return "guide"

    def _extract_title(self, content: str) -> str | None:
        """Extract title from first # heading in content.

        Args:
            content: Markdown file content

        Returns:
            Extracted title or None if no heading found
        """
        # Remove existing frontmatter if present
        content = self.FRONTMATTER_PATTERN.sub("", content)

        # Look for first level-1 heading
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            # Clean up any emoji or extra formatting
            return re.sub(r"[🧪🔧📚🚀🎯✅🚫⚠️🟢🔴]", "", title).strip()

        return None

    def _detect_linked_code(self, content: str) -> list[str]:
        """Detect Python file references in content.

        Uses regex to find mentions of .py files in the markdown.

        Args:
            content: Markdown file content

        Returns:
            List of detected Python file paths
        """
        matches = self.PYTHON_FILE_PATTERN.findall(content)
        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                unique_matches.append(match)

        return unique_matches

    def _has_frontmatter(self, content: str) -> bool:
        """Check if content already has YAML frontmatter.

        Args:
            content: Markdown file content

        Returns:
            True if frontmatter exists
        """
        return bool(self.FRONTMATTER_PATTERN.match(content))

    def _generate_frontmatter(
        self,
        file_path: Path,
        content: str,
        *,
        force: bool = False,
    ) -> tuple[dict[str, Any], str]:
        """Generate frontmatter metadata for a file.

        Args:
            file_path: Path to the markdown file
            content: Current file content
            force: If True, generate even if frontmatter exists

        Returns:
            Tuple of (metadata_dict, action_message)
        """
        has_existing = self._has_frontmatter(content)

        if has_existing and not force:
            return {}, "skipped (has frontmatter)"

        # Generate metadata
        doc_id = self._generate_id(file_path)
        doc_type = self._infer_type(file_path)
        title = self._extract_title(content)
        linked_code = self._detect_linked_code(content)
        today = date.today().strftime("%Y-%m-%d")

        metadata = {
            "id": doc_id,
            "type": doc_type,
            "status": "active",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": today,
            "context_tags": [],
            "linked_code": linked_code,
        }

        # Add title if extracted
        if title:
            metadata["title"] = title

        action = "updated" if has_existing else "created"
        return metadata, action

    def _inject_frontmatter(self, content: str, metadata: dict[str, Any]) -> str:
        """Inject YAML frontmatter into markdown content.

        Args:
            content: Original markdown content
            metadata: Metadata dictionary to inject

        Returns:
            Content with frontmatter prepended
        """
        # Remove existing frontmatter if present
        content = self.FRONTMATTER_PATTERN.sub("", content)

        # Generate YAML frontmatter
        yaml_content = yaml.dump(
            metadata,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        # Construct final content
        final_content = f"---\n{yaml_content}---\n\n{content.lstrip()}"

        return final_content

    # TODO: Refactor God Function - extract validation, generation,
    # and writing into separate methods
    def migrate_file(
        self,
        file_path: Path,
        *,
        dry_run: bool = True,
        force: bool = False,
    ) -> MigrationResult:
        """Migrate a single markdown file to CORTEX format.

        Args:
            file_path: Path to the markdown file
            dry_run: If True, don't write changes to disk
            force: If True, overwrite existing frontmatter

        Returns:
            MigrationResult with operation details
        """
        try:
            # Validate file exists and is readable
            if not file_path.exists():
                return MigrationResult(
                    file_path=file_path,
                    success=False,
                    action="error",
                    message="File not found",
                    error="File does not exist",
                )

            if not file_path.is_file():
                return MigrationResult(
                    file_path=file_path,
                    success=False,
                    action="error",
                    message="Not a file",
                    error="Path is not a file",
                )

            # Read content
            content = self.fs.read_text(file_path)

            # Generate frontmatter
            metadata, action = self._generate_frontmatter(
                file_path,
                content,
                force=force,
            )

            # If skipped (has frontmatter and not forced)
            if not metadata:
                return MigrationResult(
                    file_path=file_path,
                    success=True,
                    action="skipped",
                    message="Already has frontmatter (use --force to overwrite)",
                    inferred_metadata=None,
                )

            # Inject frontmatter
            new_content = self._inject_frontmatter(content, metadata)

            # Write to disk if not dry-run
            if not dry_run:
                self.fs.write_text(file_path, new_content)
                logger.info("Migrated file: %s", file_path)

            return MigrationResult(
                file_path=file_path,
                success=True,
                action=action,
                message=f"Frontmatter {action}" + (" (dry-run)" if dry_run else ""),
                inferred_metadata=metadata,
            )

        except Exception as e:
            logger.exception("Error migrating %s", file_path)
            return MigrationResult(
                file_path=file_path,
                success=False,
                action="error",
                message="Migration failed",
                error=str(e),
            )

    def migrate_directory(
        self,
        directory: Path,
        *,
        dry_run: bool = True,
        force: bool = False,
        recursive: bool = True,
    ) -> list[MigrationResult]:
        """Migrate all markdown files in a directory.

        Args:
            directory: Directory containing markdown files
            dry_run: If True, don't write changes to disk
            force: If True, overwrite existing frontmatter
            recursive: If True, process subdirectories

        Returns:
            List of MigrationResult for all processed files
        """
        results = []

        # Find all markdown files
        pattern = "**/*.md" if recursive else "*.md"
        md_files = sorted(directory.glob(pattern))

        logger.info(
            "Found %d markdown files in %s",
            len(md_files),
            directory,
        )

        for md_file in md_files:
            result = self.migrate_file(md_file, dry_run=dry_run, force=force)
            results.append(result)

        return results

    def print_summary(
        self,
        results: list[MigrationResult],
        *,
        dry_run: bool = True,
    ) -> None:
        """Print a formatted summary of migration results.

        Args:
            results: List of migration results
            dry_run: Whether this was a dry-run
        """
        # Count results by action
        created = sum(1 for r in results if r.action == "created")
        updated = sum(1 for r in results if r.action == "updated")
        skipped = sum(1 for r in results if r.action == "skipped")
        errors = sum(1 for r in results if r.action == "error")

        total = len(results)

        print("\n" + "=" * 70)
        mode = "MIGRATION SUMMARY (DRY-RUN)" if dry_run else "MIGRATION SUMMARY"
        print(mode)
        print("=" * 70)
        print(f"Total files processed: {total}")
        if dry_run:
            print(f"  ✅ Would create: {created}")
            print(f"  🔄 Would update: {updated}")
        else:
            print(f"  ✅ Created: {created}")
            print(f"  🔄 Updated: {updated}")
        print(f"  ⏭️  Skipped: {skipped}")
        print(f"  ❌ Errors: {errors}")
        print("=" * 70)

        # Print details for successful migrations
        if created + updated > 0:
            section = "PLANNED CHANGES:" if dry_run else "COMPLETED CHANGES:"
            print(f"\n{section}\n")

            for result in results:
                if result.action in ("created", "updated") and result.inferred_metadata:
                    rel_path = result.file_path.relative_to(self.workspace_root)
                    print(f"📄 {rel_path}")
                    print(f"   ID: {result.inferred_metadata['id']}")
                    print(f"   Type: {result.inferred_metadata['type']}")
                    if "title" in result.inferred_metadata:
                        print(f"   Title: {result.inferred_metadata['title']}")
                    if result.inferred_metadata["linked_code"]:
                        code_list = ", ".join(result.inferred_metadata["linked_code"])
                        print(f"   Linked Code: {code_list}")
                    print()

        # Print errors if any
        if errors > 0:
            print("\n❌ ERRORS:\n")
            for result in results:
                if result.action == "error":
                    rel_path = result.file_path.relative_to(self.workspace_root)
                    print(f"  {rel_path}: {result.error}")
            print()
