#!/usr/bin/env python3
"""Generation Orchestrator - Document Generation Business Logic.

This module implements the Thin CLI pattern by extracting all document
generation logic from the CLI layer. It orchestrates the generation of
dynamic documentation (README.md, CONTRIBUTING.md, etc.) from live data sources.

Architecture Pattern:
    Hexagonal Architecture (Ports and Adapters)
    - Port: GenerationOrchestrator (business logic)
    - Adapter: DocumentGenerator (file I/O and template rendering)
    - Adapter: CLI (presentation layer)

Responsibilities:
    - Validate generation targets (readme, contributing, all)
    - Coordinate single vs batch generation
    - Execute drift detection for CI/CD
    - Manage dry-run mode behavior
    - Return structured results for UI presentation

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import difflib
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.core.cortex.models import (
        BatchGenerationResult,
        DriftCheckResult,
        SingleGenerationResult,
    )

from scripts.core.cortex.models import (
    BatchGenerationResult,
    DriftCheckResult,
    SingleGenerationResult,
)
from scripts.core.cortex.readme_generator import DocumentGenerator
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__)


class GenerationTarget(Enum):
    """Supported document generation targets.

    Attributes:
        README: Generate README.md
        CONTRIBUTING: Generate CONTRIBUTING.md
        ALL: Generate all supported documents
    """

    README = "readme"
    CONTRIBUTING = "contributing"
    ALL = "all"


class GenerationOrchestrator:
    """Orchestrates document generation with business logic separation.

    This class encapsulates all document generation logic, providing
    a clean interface for the CLI layer while maintaining testability
    and reusability.

    Attributes:
        generator: DocumentGenerator instance for template rendering
        project_root: Root directory of the project

    Example:
        >>> orchestrator = GenerationOrchestrator()
        >>> result = orchestrator.generate_single(
        ...     target=GenerationTarget.README,
        ...     dry_run=False,
        ... )
        >>> if result.success:
        ...     print(f"Generated: {result.output_path}")
    """

    def __init__(
        self,
        project_root: Path | None = None,
        generator: DocumentGenerator | None = None,
    ) -> None:
        """Initialize the Generation Orchestrator.

        Args:
            project_root: Root directory of the project (default: cwd)
            generator: DocumentGenerator instance (injected for testing)
        """
        self.project_root = project_root or Path.cwd()
        self.generator = generator or DocumentGenerator(project_root=self.project_root)

    # =========================================================================
    # PUBLIC API - Thin CLI Pattern
    # =========================================================================

    def generate_single(
        self,
        target: GenerationTarget,
        output_path: Path | None = None,
        dry_run: bool = False,
    ) -> SingleGenerationResult:
        """Generate a single document (README or CONTRIBUTING).

        This method handles the complete generation workflow for a single
        document, including:
        - Target validation
        - Template resolution
        - Data collection
        - Content generation
        - File writing (unless dry_run=True)

        Args:
            target: Document to generate (README or CONTRIBUTING)
            output_path: Custom output path (None = use default)
            dry_run: If True, generate content without writing to disk

        Returns:
            SingleGenerationResult with status, content, and metadata

        Raises:
            ValueError: If target is GenerationTarget.ALL (use generate_batch)
            FileNotFoundError: If required template or data source is missing

        Example:
            >>> result = orchestrator.generate_single(
            ...     target=GenerationTarget.README,
            ...     output_path=Path("custom/README.md"),
            ...     dry_run=True,
            ... )
            >>> print(result.content[:100])  # Preview first 100 chars
        """
        try:
            # Validate target (cannot be ALL for single generation)
            self._validate_target(target, allow_all=False)

            # Resolve paths
            template_name = self._resolve_template_name(target)
            final_output_path = self._resolve_output_path(target, output_path)

            logger.info(
                f"Generating {target.value} document: "
                f"template={template_name}, output={final_output_path}, "
                f"dry_run={dry_run}",
            )

            # Generate content using DocumentGenerator
            content = self.generator.generate_document(
                template_name=template_name,
                output_path=None,  # Always generate in-memory first
            )

            # Write to disk if not dry-run
            was_written = False
            if not dry_run:
                final_output_path.parent.mkdir(parents=True, exist_ok=True)
                final_output_path.write_text(content, encoding="utf-8")
                was_written = True
                logger.info(f"Wrote {len(content)} bytes to {final_output_path}")

            return SingleGenerationResult(
                success=True,
                target=target.value,
                output_path=final_output_path,
                content=content,
                content_size=len(content),
                was_written=was_written,
                template_name=template_name,
            )

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return SingleGenerationResult(
                success=False,
                target=target.value,
                output_path=output_path or Path("unknown"),
                content="",
                content_size=0,
                error_message=str(e),
                template_name="",
            )
        except FileNotFoundError as e:
            logger.error(f"Template not found: {e}")
            return SingleGenerationResult(
                success=False,
                target=target.value,
                output_path=output_path or Path("unknown"),
                content="",
                content_size=0,
                error_message=f"Template not found: {e}",
                template_name="",
            )
        except Exception as e:
            logger.exception(f"Unexpected error generating {target.value}")
            return SingleGenerationResult(
                success=False,
                target=target.value,
                output_path=output_path or Path("unknown"),
                content="",
                content_size=0,
                error_message=f"Unexpected error: {e}",
                template_name="",
            )

    def generate_batch(
        self,
        dry_run: bool = False,
    ) -> BatchGenerationResult:
        """Generate all supported documents in batch mode.

        Equivalent to calling generate_single for each supported document
        type (README, CONTRIBUTING). Results are aggregated for reporting.

        This method is idempotent and safe to run multiple times.

        Args:
            dry_run: If True, generate content without writing to disk

        Returns:
            BatchGenerationResult with aggregated results and summary

        Example:
            >>> result = orchestrator.generate_batch(dry_run=False)
            >>> print(f"Generated {result.success_count} documents")
            >>> for single_result in result.results:
            ...     print(f"  - {single_result.target.value}: {single_result.success}")
        """
        logger.info("Starting batch generation (all documents)")

        # Generate all documents (README and CONTRIBUTING)
        targets = [GenerationTarget.README, GenerationTarget.CONTRIBUTING]
        results: list[SingleGenerationResult] = []

        for target in targets:
            result = self.generate_single(target=target, dry_run=dry_run)
            results.append(result)

        # Aggregate statistics
        success_count = sum(1 for r in results if r.success)
        error_count = sum(1 for r in results if not r.success)
        total_bytes = sum(r.content_size for r in results)
        targets_processed = [r.target for r in results]

        overall_success = error_count == 0

        logger.info(
            f"Batch generation complete: {success_count} succeeded, "
            f"{error_count} failed, {total_bytes} bytes total",
        )

        return BatchGenerationResult(
            success=overall_success,
            results=results,
            total_count=len(results),
            success_count=success_count,
            error_count=error_count,
            total_bytes=total_bytes,
            targets_processed=targets_processed,
        )

    def check_drift(
        self,
        target: GenerationTarget,
    ) -> DriftCheckResult:
        """Check if a document is in sync with its template (drift detection).

        Compares the current file content with what would be generated
        from the template and live data. Used for CI/CD governance to
        detect manual edits or outdated generated files.

        Args:
            target: Document to check (README or CONTRIBUTING)

        Returns:
            DriftCheckResult with drift status, diff, and metadata

        Raises:
            ValueError: If target is GenerationTarget.ALL (check each separately)
            FileNotFoundError: If target file doesn't exist

        Example:
            >>> result = orchestrator.check_drift(GenerationTarget.README)
            >>> if result.has_drift:
            ...     print("⚠️ README.md is out of sync!")
            ...     print(result.diff)
        """
        try:
            # Validate target (cannot be ALL)
            self._validate_target(target, allow_all=False)

            # Resolve paths
            template_name = self._resolve_template_name(target)
            output_path = self._resolve_output_path(target, custom_path=None)

            logger.info(f"Checking drift for {target.value}: {output_path}")

            # Generate expected content (what SHOULD be in the file)
            expected_content = self.generator.generate_document(
                template_name=template_name,
                output_path=None,  # Generate in-memory
            )

            # Read current content (what IS in the file)
            current_content = ""
            if output_path.exists():
                current_content = output_path.read_text(encoding="utf-8")
            else:
                logger.warning(f"File does not exist: {output_path}")

            # Compare contents
            has_drift = current_content != expected_content

            # Generate unified diff if there's drift
            diff = ""
            line_changes = 0
            if has_drift:
                current_lines = current_content.splitlines(keepends=True)
                expected_lines = expected_content.splitlines(keepends=True)

                diff_lines = list(
                    difflib.unified_diff(
                        current_lines,
                        expected_lines,
                        fromfile=f"current/{output_path.name}",
                        tofile=f"expected/{output_path.name}",
                        lineterm="",
                    ),
                )
                diff = "".join(diff_lines)

                # Count line changes (lines starting with + or -, excluding headers)
                line_changes = sum(
                    1
                    for line in diff_lines
                    if line.startswith(("+", "-"))
                    and not line.startswith(("+++", "---"))
                )

                logger.info(
                    f"Drift detected in {target.value}: {line_changes} line changes",
                )
            else:
                logger.info(f"No drift detected in {target.value}")

            return DriftCheckResult(
                has_drift=has_drift,
                target=target.value,
                output_path=output_path,
                diff=diff,
                current_content=current_content,
                expected_content=expected_content,
                line_changes=line_changes,
            )

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return DriftCheckResult(
                has_drift=False,
                target=target.value,
                output_path=Path("unknown"),
                error_message=str(e),
            )
        except Exception as e:
            logger.exception(f"Error checking drift for {target.value}")
            return DriftCheckResult(
                has_drift=False,
                target=target.value,
                output_path=Path("unknown"),
                error_message=f"Unexpected error: {e}",
            )

    def check_batch_drift(self) -> list[DriftCheckResult]:
        """Check drift for all supported documents.

        Convenience method that calls check_drift for each document type
        and returns aggregated results.

        Returns:
            List of DriftCheckResult, one per document type

        Example:
            >>> results = orchestrator.check_batch_drift()
            >>> drifted = [r for r in results if r.has_drift]
            >>> if drifted:
            ...     print(f"{len(drifted)} documents out of sync")
        """
        logger.info("Checking drift for all documents")

        targets = [GenerationTarget.README, GenerationTarget.CONTRIBUTING]
        results = []

        for target in targets:
            result = self.check_drift(target)
            results.append(result)

        drifted_count = sum(1 for r in results if r.has_drift)
        logger.info(f"Batch drift check complete: {drifted_count} drifted")

        return results

    # =========================================================================
    # PRIVATE HELPERS - Internal Logic
    # =========================================================================

    def _resolve_template_name(self, target: GenerationTarget) -> str:
        """Resolve template filename from target enum.

        Args:
            target: Generation target

        Returns:
            Template filename (e.g., "README.md.j2")

        Raises:
            ValueError: If target is ALL
        """
        if target == GenerationTarget.ALL:
            raise ValueError(
                "Cannot resolve template for ALL target. Use generate_batch() instead.",
            )

        template_mapping = {
            GenerationTarget.README: "README.md.j2",
            GenerationTarget.CONTRIBUTING: "CONTRIBUTING.md.j2",
        }

        return template_mapping[target]

    def _resolve_output_path(
        self,
        target: GenerationTarget,
        custom_path: Path | None,
    ) -> Path:
        """Resolve final output path for a document.

        Args:
            target: Generation target
            custom_path: Custom output path or None for default

        Returns:
            Absolute path to output file

        Raises:
            ValueError: If target is ALL
        """
        if target == GenerationTarget.ALL:
            raise ValueError(
                "Cannot resolve output path for ALL target. "
                "Use generate_batch() instead.",
            )

        # Use custom path if provided
        if custom_path:
            return custom_path.resolve()

        # Default paths based on target
        path_mapping = {
            GenerationTarget.README: self.project_root / "README.md",
            GenerationTarget.CONTRIBUTING: self.project_root / "CONTRIBUTING.md",
        }

        return path_mapping[target]

    def _validate_target(
        self,
        target: GenerationTarget,
        allow_all: bool = False,
    ) -> None:
        """Validate generation target.

        Args:
            target: Target to validate
            allow_all: If True, allow GenerationTarget.ALL

        Raises:
            ValueError: If target is invalid for the operation
        """
        if target == GenerationTarget.ALL and not allow_all:
            raise ValueError(
                "Target 'ALL' is not allowed for this operation. "
                "Expected: README or CONTRIBUTING",
            )

        # Validate target is a known enum value
        if not isinstance(target, GenerationTarget):
            raise ValueError(
                f"Invalid target type: {type(target)}. Expected GenerationTarget enum.",
            )
