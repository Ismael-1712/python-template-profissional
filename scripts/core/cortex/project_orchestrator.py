"""CORTEX Project Orchestrator.

Facade for project lifecycle operations including file initialization and
batch migration. Provides a high-level interface for managing CORTEX
documentation across entire projects.

Features:
- Single file initialization with frontmatter injection
- Batch project migration with aggregated reporting
- Force mode for overwriting existing frontmatter
- Dry-run mode for safe previewing
- Integration with DocumentMigrator for delegation

Usage:
    from scripts.core.cortex.project_orchestrator import ProjectOrchestrator

    orchestrator = ProjectOrchestrator(workspace_root=Path("/project"))

    # Initialize single file
    result = orchestrator.initialize_file(Path("docs/guide.md"))

    # Migrate entire directory
    summary = orchestrator.migrate_project(
        directory=Path("docs/"),
        dry_run=False,
        force=False,
        recursive=True
    )

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from scripts.core.cortex.metadata import FrontmatterParser
from scripts.core.cortex.migrate import DocumentMigrator, MigrationResult
from scripts.core.cortex.models import InitResult, MigrationSummary
from scripts.cortex.core.frontmatter_helpers import generate_default_frontmatter
from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem

logger = logging.getLogger(__name__)


class ProjectOrchestrator:
    """Orchestrates CORTEX project lifecycle operations.

    Provides a unified interface for initializing individual files and
    migrating entire projects to CORTEX format. Acts as a Facade over
    DocumentMigrator and other core components.

    Attributes:
        workspace_root: Root directory of the workspace
        migrator: DocumentMigrator instance for delegation
        fs: FileSystemAdapter for I/O operations
        parser: FrontmatterParser for detecting existing frontmatter
    """

    # Regex pattern for detecting existing frontmatter
    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\n.*?\n---\s*\n",
        re.DOTALL | re.MULTILINE,
    )

    def __init__(
        self,
        workspace_root: Path,
        fs: FileSystemAdapter | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            workspace_root: Root directory of the workspace
            fs: FileSystemAdapter for I/O operations (default: RealFileSystem)
        """
        if fs is None:
            fs = RealFileSystem()

        self.workspace_root = workspace_root.resolve()
        self.fs = fs
        self.migrator = DocumentMigrator(workspace_root=workspace_root, fs=fs)
        self.parser = FrontmatterParser(fs=fs)

        logger.debug(
            "Initialized ProjectOrchestrator with root: %s",
            self.workspace_root,
        )

    def _has_frontmatter(self, content: str) -> bool:
        """Check if content already has YAML frontmatter.

        Args:
            content: Markdown file content

        Returns:
            True if frontmatter exists
        """
        return bool(self.FRONTMATTER_PATTERN.match(content))

    def _extract_existing_frontmatter(
        self,
        content: str,
    ) -> dict[str, Any] | None:
        """Extract existing frontmatter from content.

        Args:
            content: Markdown file content

        Returns:
            Dictionary of frontmatter metadata or None if not found
        """
        if not self._has_frontmatter(content):
            return None

        try:
            import frontmatter as fm

            post = fm.loads(content)
            return dict(post.metadata) if post.metadata else None
        except Exception as e:
            logger.warning("Failed to parse existing frontmatter: %s", e)
            return None

    def initialize_file(
        self,
        path: Path,
        force: bool = False,
    ) -> InitResult:
        """Initialize a single file with CORTEX frontmatter.

        Adds YAML frontmatter to a markdown file with intelligent metadata
        inference. If the file already has frontmatter, returns status 'skipped'
        unless force=True.

        Args:
            path: Path to the markdown file to initialize
            force: If True, overwrite existing frontmatter (default: False)

        Returns:
            InitResult containing operation status and metadata

        Example:
            >>> orchestrator = ProjectOrchestrator(Path("/project"))
            >>> result = orchestrator.initialize_file(Path("docs/guide.md"))
            >>> assert result.status in ["success", "skipped", "error"]
        """
        logger.info("Initializing file: %s (force=%s)", path, force)

        # Validate file exists
        if not self.fs.exists(path):
            return InitResult(
                path=path,
                status="error",
                old_frontmatter=None,
                new_frontmatter={},
                error=f"File does not exist: {path}",
            )

        if not self.fs.is_file(path):
            return InitResult(
                path=path,
                status="error",
                old_frontmatter=None,
                new_frontmatter={},
                error=f"Path is not a file: {path}",
            )

        try:
            # Read current content
            content = self.fs.read_text(path)

            # Check for existing frontmatter
            old_frontmatter = self._extract_existing_frontmatter(content)
            has_existing = old_frontmatter is not None

            # If has frontmatter and not force, skip
            if has_existing and not force:
                logger.debug(
                    "File %s already has frontmatter, skipping (force=False)",
                    path,
                )
                # old_frontmatter is guaranteed to be dict here (not None)
                # because has_existing is True
                return InitResult(
                    path=path,
                    status="skipped",
                    old_frontmatter=old_frontmatter,
                    new_frontmatter=old_frontmatter or {},
                )

            # Generate new frontmatter using helper
            frontmatter_block = generate_default_frontmatter(path)

            # Parse the generated frontmatter to extract metadata dict
            import frontmatter as fm

            temp_doc = fm.loads(frontmatter_block + "\nTemp content")
            new_frontmatter = dict(temp_doc.metadata)

            # Remove old frontmatter from content if exists
            clean_content = self.FRONTMATTER_PATTERN.sub("", content)

            # Construct new content with frontmatter
            new_content = frontmatter_block + clean_content.lstrip()

            # Write back to file (not dry-run, this is actual initialization)
            self.fs.write_text(path, new_content)

            logger.info(
                "Successfully initialized %s (old_frontmatter=%s)",
                path,
                "exists" if has_existing else "none",
            )

            return InitResult(
                path=path,
                status="success",
                old_frontmatter=old_frontmatter,
                new_frontmatter=new_frontmatter,
            )

        except Exception as e:
            logger.exception("Failed to initialize file %s", path)
            return InitResult(
                path=path,
                status="error",
                old_frontmatter=None,
                new_frontmatter={},
                error=str(e),
            )

    def migrate_project(
        self,
        directory: Path,
        dry_run: bool = True,
        force: bool = False,
        recursive: bool = True,
    ) -> MigrationSummary:
        """Migrate an entire project directory to CORTEX format.

        Processes all markdown files in the given directory, adding CORTEX
        frontmatter with intelligent metadata inference. Aggregates results
        into a summary report.

        Args:
            directory: Directory containing markdown files to migrate
            dry_run: If True, preview changes without writing (default: True)
            force: If True, overwrite existing frontmatter (default: False)
            recursive: If True, process subdirectories (default: True)

        Returns:
            MigrationSummary with aggregated statistics and detailed results

        Example:
            >>> orchestrator = ProjectOrchestrator(Path("/project"))
            >>> summary = orchestrator.migrate_project(
            ...     directory=Path("docs/"),
            ...     dry_run=True,
            ...     recursive=True,
            ... )
            >>> assert summary.total >= 0
        """
        logger.info(
            "Migrating project: %s (dry_run=%s, force=%s, recursive=%s)",
            directory,
            dry_run,
            force,
            recursive,
        )

        # Validate directory exists
        if not self.fs.exists(directory):
            logger.warning("Directory does not exist: %s", directory)
            return MigrationSummary(
                total=0,
                created=0,
                updated=0,
                errors=0,
                results=[],
            )

        if not self.fs.is_dir(directory):
            logger.warning("Path is not a directory: %s", directory)
            return MigrationSummary(
                total=0,
                created=0,
                updated=0,
                errors=0,
                results=[],
            )

        # Delegate to DocumentMigrator
        results: list[MigrationResult] = self.migrator.migrate_directory(
            directory=directory,
            dry_run=dry_run,
            force=force,
            recursive=recursive,
        )

        # Aggregate statistics
        total = len(results)
        created = sum(1 for r in results if r.action == "created")
        updated = sum(1 for r in results if r.action == "updated")
        errors = sum(1 for r in results if r.action == "error")

        logger.info(
            "Migration complete: %d total, %d created, %d updated, %d errors",
            total,
            created,
            updated,
            errors,
        )

        return MigrationSummary(
            total=total,
            created=created,
            updated=updated,
            errors=errors,
            results=results,
        )
