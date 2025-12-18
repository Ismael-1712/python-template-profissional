"""TOML Merger - Fusionista de TOML.

Intelligent TOML file merger that preserves comments, formatting, and structure.
Uses tomlkit for style-preserving parsing and serialization.

Key Features:
- Comment preservation (critical requirement)
- Smart merge strategies (template/user/smart)
- List union with deduplication
- Recursive dictionary merge
- Version conflict resolution
- Automatic backup creation

Author: Engineering Team
License: MIT
"""

# mypy: disable-error-code="arg-type,return-value"
# Justification: tomlkit has incomplete type stubs; types are validated at runtime

from __future__ import annotations

import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.items import Array, Table

# Type alias for conflict resolution decisions
ConflictDecision = Literal["template", "user", "both", "skip"]


# ======================================================================
# ENUMS AND DATA CLASSES
# ======================================================================
class MergeStrategy(Enum):
    """Strategies for resolving conflicts during merge.

    Attributes:
        TEMPLATE_PRIORITY: Template values overwrite user values
        USER_PRIORITY: User values take precedence over template
        SMART: Intelligent merge (union lists, recursive dicts)
        INTERACTIVE: Delegate conflict resolution to external callback
    """

    TEMPLATE_PRIORITY = "template"
    USER_PRIORITY = "user"
    SMART = "smart"
    INTERACTIVE = "interactive"


@dataclass
class MergeResult:
    """Result of a TOML merge operation.

    Attributes:
        success: Whether merge completed successfully
        conflicts: List of conflict descriptions (if any)
        diff: Unified diff of changes (populated in dry_run)
        backup_path: Path to backup file (if created)
    """

    success: bool
    conflicts: list[str] = field(default_factory=list)
    diff: str = ""
    backup_path: Path | None = None


# ======================================================================
# TOML MERGER CLASS
# ======================================================================
class TOMLMerger:
    """Intelligent TOML file merger with comment preservation.

    This class handles merging two TOML files while preserving:
    - Comments (both section and inline)
    - Formatting (indentation, spacing)
    - Quote styles
    - Custom user configurations

    Example:
        >>> merger = TOMLMerger(strategy=MergeStrategy.SMART)
        >>> result = merger.merge(source_path, target_path)
        >>> if result.success:
        ...     print("Merge successful!")
    """

    def __init__(
        self,
        strategy: MergeStrategy = MergeStrategy.SMART,
        conflict_resolver: Callable[[str, Any, Any], ConflictDecision] | None = None,
    ) -> None:
        """Initialize TOMLMerger.

        Args:
            strategy: Merge strategy to use
            conflict_resolver: Optional callback for INTERACTIVE mode.
                Called with (key, user_value, template_value) and should
                return "template", "user", "both", or "skip".
        """
        self.strategy = strategy
        self.conflict_resolver = conflict_resolver

    def merge(
        self,
        source_path: Path,
        target_path: Path,
        output_path: Path | None = None,
        dry_run: bool = False,
        backup: bool = True,
    ) -> MergeResult:
        """Merge source TOML into target TOML.

        Args:
            source_path: Path to template/source TOML file
            target_path: Path to project/target TOML file
            output_path: Optional output path (defaults to target_path)
            dry_run: If True, don't write changes (return diff only)
            backup: If True, create .bak file before overwrite

        Returns:
            MergeResult with success status, conflicts, diff, and backup path

        Example:
            >>> merger = TOMLMerger(MergeStrategy.SMART)
            >>> result = merger.merge(
            ...     Path("template/pyproject.toml"),
            ...     Path("pyproject.toml"),
            ...     dry_run=True
            ... )
            >>> print(result.diff)
        """
        # Validate inputs
        if not source_path.exists():
            return MergeResult(
                success=False,
                conflicts=[f"Source file not found: {source_path}"],
            )

        if not target_path.exists():
            return MergeResult(
                success=False,
                conflicts=[f"Target file not found: {target_path}"],
            )

        # Parse both files
        try:
            source_doc = tomlkit.parse(source_path.read_text(encoding="utf-8"))
            target_doc = tomlkit.parse(target_path.read_text(encoding="utf-8"))
        except Exception as e:
            return MergeResult(
                success=False,
                conflicts=[f"Failed to parse TOML: {e}"],
            )

        # Perform merge based on strategy
        try:
            merged_doc = self._merge_documents(source_doc, target_doc)
        except Exception as e:
            return MergeResult(
                success=False,
                conflicts=[f"Merge failed: {e}"],
            )

        # Generate output
        merged_content = tomlkit.dumps(merged_doc)

        # Handle dry run
        if dry_run:
            original_content = target_path.read_text(encoding="utf-8")
            diff = self._generate_diff(original_content, merged_content)
            return MergeResult(
                success=True,
                diff=diff,
            )

        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = self._create_backup(target_path)

        # Write merged content
        output = output_path or target_path
        try:
            output.write_text(merged_content, encoding="utf-8")
        except Exception as e:
            return MergeResult(
                success=False,
                conflicts=[f"Failed to write output: {e}"],
                backup_path=backup_path,
            )

        return MergeResult(
            success=True,
            backup_path=backup_path,
        )

    def _merge_documents(
        self,
        source: TOMLDocument,
        target: TOMLDocument,
    ) -> TOMLDocument:
        """Merge source document into target document.

        Args:
            source: Template TOML document
            target: Project TOML document (will be modified)

        Returns:
            Merged TOMLDocument
        """
        if self.strategy == MergeStrategy.TEMPLATE_PRIORITY:
            return self._merge_template_priority(source, target)
        if self.strategy == MergeStrategy.USER_PRIORITY:
            return self._merge_user_priority(source, target)
        if self.strategy == MergeStrategy.INTERACTIVE:
            return self._merge_interactive(source, target)
        # SMART
        return self._merge_smart(source, target)

    def _merge_template_priority(
        self,
        source: TOMLDocument,
        target: TOMLDocument,
    ) -> TOMLDocument:
        """Merge with template values taking priority.

        Args:
            source: Template document
            target: Target document

        Returns:
            Merged document (source overwrites target)
        """
        # Deep copy target to preserve comments
        result = tomlkit.parse(tomlkit.dumps(target))

        # Recursively update with source values
        self._deep_update(result, source, prioritize_overlay=True)

        return result

    def _merge_user_priority(
        self,
        source: TOMLDocument,
        target: TOMLDocument,
    ) -> TOMLDocument:
        """Merge with user values taking priority.

        Args:
            source: Template document
            target: Target document

        Returns:
            Merged document (target preserved, source fills gaps)
        """
        # Deep copy target to preserve comments
        result = tomlkit.parse(tomlkit.dumps(target))

        # Recursively update (only add new keys from source)
        self._deep_update(result, source, prioritize_overlay=False)

        return result

    def _merge_smart(
        self,
        source: TOMLDocument,
        target: TOMLDocument,
    ) -> TOMLDocument:
        """Smart merge: union lists, recursive dicts.

        Args:
            source: Template document
            target: Target document

        Returns:
            Intelligently merged document
        """
        # Deep copy target to preserve comments
        result = tomlkit.parse(tomlkit.dumps(target))

        # Smart recursive merge
        self._smart_merge_recursive(result, source)

        return result

    def _merge_interactive(
        self,
        source: TOMLDocument,
        target: TOMLDocument,
    ) -> TOMLDocument:
        """Interactive merge with callback-driven conflict resolution.

        Args:
            source: Template document
            target: Target document

        Returns:
            Merged document with conflicts resolved by callback
        """
        # Deep copy target to preserve comments
        result = tomlkit.parse(tomlkit.dumps(target))

        # Interactive recursive merge
        self._interactive_merge_recursive(result, source)

        return result

    def _interactive_merge_recursive(
        self,
        base: dict[str, Any] | Table,
        overlay: dict[str, Any] | Table,
    ) -> None:
        """Recursive merge with callback for conflict resolution.

        Args:
            base: Base dictionary (modified in place)
            overlay: Overlay dictionary
        """
        for key, value in overlay.items():
            if key not in base:
                # New key from template - add it
                base[key] = value
            elif isinstance(value, (dict, Table)) and isinstance(
                base[key],
                (dict, Table),
            ):
                # Both are dicts - recurse
                self._interactive_merge_recursive(base[key], value)
            elif isinstance(value, (list, Array)) and isinstance(
                base[key],
                (list, Array),
            ):
                # Both are lists - use SMART merge (union)
                # TODO: Could add callback for list conflicts in future
                base[key] = self._merge_lists(base[key], value)
            # SCALAR CONFLICT - delegate to callback
            elif self.conflict_resolver:
                decision = self.conflict_resolver(key, base[key], value)

                if decision == "template":
                    base[key] = value
                elif decision == "user":
                    # Keep base[key] unchanged
                    pass
                elif decision == "both":
                    # For scalars, "both" falls back to template
                    base[key] = value
                # "skip" -> no change
            else:
                # No callback provided - fallback to template wins
                base[key] = value

    def _deep_update(
        self,
        base: dict[str, Any] | Table,
        overlay: dict[str, Any] | Table,
        prioritize_overlay: bool,
    ) -> None:
        """Recursively update base dict with overlay.

        Args:
            base: Base dictionary (modified in place)
            overlay: Overlay dictionary
            prioritize_overlay: If True, overlay wins; else base preserved
        """
        for key, value in overlay.items():
            if key not in base:
                # New key - always add
                base[key] = value
            elif isinstance(value, (dict, Table)) and isinstance(
                base[key],
                (dict, Table),
            ):
                # Both are dicts - recurse
                self._deep_update(base[key], value, prioritize_overlay)
            elif prioritize_overlay:
                # Overlay wins
                base[key] = value
            # else: base preserved (user priority)

    def _smart_merge_recursive(
        self,
        base: dict[str, Any] | Table,
        overlay: dict[str, Any] | Table,
    ) -> None:
        """Smart recursive merge with list union.

        Args:
            base: Base dictionary (modified in place)
            overlay: Overlay dictionary
        """
        for key, value in overlay.items():
            if key not in base:
                # New key from template - add it
                base[key] = value
            elif isinstance(value, (dict, Table)) and isinstance(
                base[key],
                (dict, Table),
            ):
                # Both are dicts - recurse
                self._smart_merge_recursive(base[key], value)
            elif isinstance(value, (list, Array)) and isinstance(
                base[key],
                (list, Array),
            ):
                # Both are lists - union with deduplication
                base[key] = self._merge_lists(base[key], value)
            else:
                # Scalar values - template wins in SMART mode
                base[key] = value

    def _merge_lists(
        self,
        base_list: list[Any] | Array,
        overlay_list: list[Any] | Array,
    ) -> Array:
        """Merge two lists with union and deduplication.

        Handles version conflicts in dependencies (e.g., pydantic>=2.0 vs >=2.5).
        CRITICAL: Preserves inline comments from base list by modifying in place.

        Strategy:
        1. Parse packages from both lists
        2. Update existing packages with newer versions
        3. Append new packages from template
        4. NO SORTING - preserves original order and comments

        Args:
            base_list: User's list (with potential inline comments)
            overlay_list: Template's list

        Returns:
            Merged tomlkit Array with preserved comments
        """
        # Parse package names from both lists
        base_packages: dict[str, tuple[int, str]] = {}  # pkg -> (index, spec)
        overlay_packages = self._parse_dependencies(overlay_list)

        # Map base packages to their indices (to preserve order/comments)
        for idx, item in enumerate(base_list):
            item_str = str(item).strip()
            match = re.match(r"^([a-zA-Z0-9\-_]+)", item_str)
            if match:
                pkg_name = match.group(1).lower()
                base_packages[pkg_name] = (idx, item_str)

        # Update existing packages if newer version in template
        for pkg, overlay_spec in overlay_packages.items():
            if pkg in base_packages:
                idx, base_spec = base_packages[pkg]
                resolved = self._resolve_version(base_spec, overlay_spec)

                # If version changed, update in place
                if resolved != base_spec:
                    base_list[idx] = resolved

        # Add new packages from template (not in base)
        for pkg, spec in overlay_packages.items():
            if pkg not in base_packages:
                base_list.append(spec)

        return base_list

    def _parse_dependencies(
        self,
        dep_list: list[Any] | Array,
    ) -> dict[str, str]:
        """Parse dependency list into {package: specification} dict.

        Args:
            dep_list: List of dependency strings

        Returns:
            Dict mapping package names to full specifications

        Example:
            >>> deps = ["fastapi>=0.100.0", "pydantic>=2.0"]
            >>> _parse_dependencies(deps)
            {'fastapi': 'fastapi>=0.100.0', 'pydantic': 'pydantic>=2.0'}
        """
        packages: dict[str, str] = {}

        for dep in dep_list:
            dep_str = str(dep).strip()

            # Extract package name (before version specifier or [extra])
            # Handles: "package", "package>=1.0", "package[extra]",
            # "package[extra]>=1.0"
            match = re.match(r"^([a-zA-Z0-9\-_]+)", dep_str)
            if match:
                pkg_name = match.group(1).lower()
                packages[pkg_name] = dep_str

        return packages

    def _resolve_version(self, spec1: str, spec2: str) -> str:
        """Resolve version conflict between two dependency specifications.

        Strategy: Choose the more restrictive version.

        Args:
            spec1: First specification (e.g., "pydantic>=2.0.0")
            spec2: Second specification (e.g., "pydantic>=2.5.0")

        Returns:
            More restrictive specification

        Example:
            >>> _resolve_version("pydantic>=2.0", "pydantic>=2.5")
            'pydantic>=2.5'
        """
        # Extract version numbers using regex
        version_pattern = r"([0-9]+(?:\.[0-9]+)*)"

        match1 = re.search(version_pattern, spec1)
        match2 = re.search(version_pattern, spec2)

        if not match1:
            return spec2
        if not match2:
            return spec1

        v1 = match1.group(1)
        v2 = match2.group(1)

        # Simple version comparison (split by dots and compare)
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]

        # Pad to same length
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))

        # Compare and return higher version
        if parts2 > parts1:
            return spec2
        return spec1

    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of file before modification.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file

        Example:
            >>> backup = _create_backup(Path("pyproject.toml"))
            >>> print(backup)
            PosixPath('pyproject.toml.bak.20251218_143022')
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".bak.{timestamp}")

        shutil.copy2(file_path, backup_path)

        return backup_path

    def _generate_diff(self, original: str, modified: str) -> str:
        """Generate unified diff between original and modified content.

        Args:
            original: Original file content
            modified: Modified file content

        Returns:
            Unified diff string
        """
        import difflib

        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile="original",
            tofile="modified",
        )

        return "".join(diff)


# ======================================================================
# HELPER FUNCTION
# ======================================================================
def merge_toml(
    source_path: Path,
    target_path: Path,
    output_path: Path | None = None,
    strategy: MergeStrategy = MergeStrategy.SMART,
    dry_run: bool = False,
    backup: bool = True,
    conflict_resolver: Callable[[str, Any, Any], ConflictDecision] | None = None,
) -> MergeResult:
    """Standalone helper function for merging TOML files.

    Convenience wrapper around TOMLMerger class.

    Args:
        source_path: Template TOML file
        target_path: Project TOML file
        output_path: Optional output path
        strategy: Merge strategy
        dry_run: Preview mode (no writes)
        backup: Create backup before overwrite
        conflict_resolver: Optional callback for INTERACTIVE mode

    Returns:
        MergeResult with operation details

    Example:
        >>> result = merge_toml(
        ...     Path("template/pyproject.toml"),
        ...     Path("pyproject.toml"),
        ...     dry_run=True
        ... )
        >>> if result.success:
        ...     print(result.diff)
    """
    merger = TOMLMerger(strategy=strategy, conflict_resolver=conflict_resolver)
    return merger.merge(
        source_path=source_path,
        target_path=target_path,
        output_path=output_path,
        dry_run=dry_run,
        backup=backup,
    )
