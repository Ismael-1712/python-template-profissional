"""Link Resolver for CORTEX Knowledge Graph.

Module for resolving and validating semantic links between Knowledge Nodes.
Implements multiple resolution strategies with fallback logic.

Usage:
    resolver = LinkResolver(entries, workspace_root)
    resolved_entries = resolver.resolve_all()

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from scripts.core.cortex.models import (
    KnowledgeEntry,
    KnowledgeLink,
    LinkStatus,
    LinkType,
)

logger = logging.getLogger(__name__)


@dataclass
class ResolutionResult:
    """Result of a link resolution attempt.

    Attributes:
        target_id: Resolved Knowledge Node ID (None if not resolved)
        target_resolved: Resolved path or ID string
        status: LinkStatus indicating resolution outcome
        strategy: Name of strategy that succeeded ("id", "path", "alias", etc)
    """

    target_id: str | None
    target_resolved: str | None
    status: LinkStatus
    strategy: str


class LinkResolver:
    """Resolves raw link targets to validated Knowledge Node IDs.

    Implements a multi-strategy resolution pipeline:
    1. Direct ID match
    2. File path resolution (relative/absolute)
    3. Alias/title exact match
    4. Fuzzy normalized match

    Attributes:
        entries: List of all KnowledgeEntry objects
        workspace_root: Root directory of the workspace
        _id_index: Direct ID -> Entry mapping
        _path_to_id: Absolute Path -> ID mapping
        _alias_to_ids: Alias/Title -> [IDs] mapping
        _title_normalized: Normalized title -> ID mapping
    """

    def __init__(
        self,
        entries: list[KnowledgeEntry],
        workspace_root: Path,
    ) -> None:
        """Initialize the LinkResolver with a list of entries.

        Args:
            entries: List of KnowledgeEntry objects to build indices from
            workspace_root: Root directory of the workspace
        """
        self.entries = entries
        self.workspace_root = workspace_root

        # Primary index
        self._id_index: dict[str, KnowledgeEntry] = {}

        # Reverse indices
        self._path_to_id: dict[Path, str] = {}
        self._alias_to_ids: dict[str, list[str]] = {}
        self._title_normalized: dict[str, str] = {}

        # Build all indices
        self._build_indices()

        logger.debug(
            f"LinkResolver initialized with {len(entries)} entries, "
            f"{len(self._path_to_id)} paths, "
            f"{len(self._alias_to_ids)} aliases",
        )

    def _build_indices(self) -> None:
        """Build all reverse index structures from entries."""
        for entry in self.entries:
            # Primary ID index
            self._id_index[entry.id] = entry

            # Path index (absolute paths)
            if entry.file_path:
                abs_path = entry.file_path.resolve()
                self._path_to_id[abs_path] = entry.id

                # Also index workspace-relative path
                try:
                    rel_path = abs_path.relative_to(self.workspace_root)
                    # Store as absolute to avoid ambiguity
                    self._path_to_id[self.workspace_root / rel_path] = entry.id
                except ValueError:
                    # Path is outside workspace
                    pass

            # Alias index (extract from frontmatter if available)
            # For now, we'll use the entry ID as an alias
            # TODO: Extract actual aliases from frontmatter when available
            if entry.id not in self._alias_to_ids:
                self._alias_to_ids[entry.id] = []
            self._alias_to_ids[entry.id].append(entry.id)

            # Title normalization index
            # Use ID as title for now (can be enhanced with actual titles)
            normalized = self._normalize_text(entry.id)
            if normalized and normalized not in self._title_normalized:
                self._title_normalized[normalized] = entry.id

    def resolve_all(self) -> list[KnowledgeEntry]:
        """Resolve all links in all entries.

        Returns:
            List of new KnowledgeEntry instances with resolved links
            (Pydantic models are frozen, so we create new instances)
        """
        resolved_entries = []

        for entry in self.entries:
            if not entry.links:
                # No links to resolve, keep as is
                resolved_entries.append(entry)
                continue

            # Resolve each link
            resolved_links = []
            for link in entry.links:
                result = self._resolve_link(link, entry)

                # Create new link with resolved fields
                resolved_link = link.model_copy(
                    update={
                        "target_id": result.target_id,
                        "target_resolved": result.target_resolved,
                        "status": result.status,
                        "is_valid": result.status == LinkStatus.VALID,
                    },
                )
                resolved_links.append(resolved_link)

            # Create new entry with resolved links
            resolved_entry = entry.model_copy(update={"links": resolved_links})
            resolved_entries.append(resolved_entry)

        # Log summary
        total_links = sum(len(e.links) for e in resolved_entries)
        valid_links = sum(
            sum(1 for link in e.links if link.status == LinkStatus.VALID)
            for e in resolved_entries
        )
        broken_links = sum(
            sum(1 for link in e.links if link.status == LinkStatus.BROKEN)
            for e in resolved_entries
        )

        logger.info(
            f"Resolved {total_links} links: {valid_links} valid, {broken_links} broken",
        )

        return resolved_entries

    def _resolve_link(
        self,
        link: KnowledgeLink,
        source_entry: KnowledgeEntry,
    ) -> ResolutionResult:
        """Resolve a single link using the strategy pipeline.

        Args:
            link: The link to resolve
            source_entry: The entry containing this link

        Returns:
            ResolutionResult with resolved information
        """
        target_raw = link.target_raw

        # STRATEGY 1: Direct ID Match
        if target_raw in self._id_index:
            logger.debug(f"Resolved '{target_raw}' via ID strategy")
            return ResolutionResult(
                target_id=target_raw,
                target_resolved=target_raw,
                status=LinkStatus.VALID,
                strategy="id",
            )

        # STRATEGY 2: File Path Resolution
        if link.type in [LinkType.MARKDOWN, LinkType.WIKILINK]:
            path_result = self._resolve_by_path(target_raw, source_entry)
            if path_result:
                logger.debug(f"Resolved '{target_raw}' via path strategy")
                return path_result

        # STRATEGY 3: Alias/Title Exact Match
        if link.type in [LinkType.WIKILINK, LinkType.WIKILINK_ALIASED]:
            alias_result = self._resolve_by_alias(target_raw)
            if alias_result:
                logger.debug(f"Resolved '{target_raw}' via alias strategy")
                return alias_result

        # STRATEGY 4: Fuzzy Normalized Match
        fuzzy_result = self._resolve_by_fuzzy(target_raw)
        if fuzzy_result:
            logger.debug(f"Resolved '{target_raw}' via fuzzy strategy")
            return fuzzy_result

        # STRATEGY 5: Code Reference (Special Case)
        if link.type == LinkType.CODE_REFERENCE:
            code_result = self._resolve_code_reference(target_raw, source_entry)
            if code_result:
                return code_result

        # FAILED: Link is broken
        logger.debug(f"Failed to resolve link: '{target_raw}' from {source_entry.id}")
        return ResolutionResult(
            target_id=None,
            target_resolved=None,
            status=LinkStatus.BROKEN,
            strategy="broken",
        )

    def _resolve_by_path(
        self,
        target_raw: str,
        source_entry: KnowledgeEntry,
    ) -> ResolutionResult | None:
        """Resolve link by file path (relative or absolute).

        Args:
            target_raw: Raw target string (may be a path)
            source_entry: Source entry (for relative path resolution)

        Returns:
            ResolutionResult if successful, None otherwise
        """
        if not source_entry.file_path:
            return None

        # Remove anchor fragments (#section)
        target_clean = target_raw.split("#")[0].strip()
        if not target_clean:
            return None

        # Try relative to source file's directory
        if target_clean.startswith(("./", "../")):
            resolved = (source_entry.file_path.parent / target_clean).resolve()
            if resolved in self._path_to_id:
                target_id = self._path_to_id[resolved]
                return ResolutionResult(
                    target_id=target_id,
                    target_resolved=str(resolved),
                    status=LinkStatus.VALID,
                    strategy="path_relative",
                )

        # Try relative to workspace root
        workspace_relative = (self.workspace_root / target_clean).resolve()
        if workspace_relative in self._path_to_id:
            target_id = self._path_to_id[workspace_relative]
            return ResolutionResult(
                target_id=target_id,
                target_resolved=str(workspace_relative),
                status=LinkStatus.VALID,
                strategy="path_workspace",
            )

        # Try as absolute path
        try:
            absolute_path = Path(target_clean).resolve()
            if absolute_path.exists() and absolute_path in self._path_to_id:
                target_id = self._path_to_id[absolute_path]
                return ResolutionResult(
                    target_id=target_id,
                    target_resolved=str(absolute_path),
                    status=LinkStatus.VALID,
                    strategy="path_absolute",
                )
        except (ValueError, OSError):
            pass

        return None

    def _resolve_by_alias(self, target_raw: str) -> ResolutionResult | None:
        """Resolve link by alias or title exact match.

        Args:
            target_raw: Raw target string (should be an alias/title)

        Returns:
            ResolutionResult if successful, None otherwise
        """
        matching_ids = self._alias_to_ids.get(target_raw, [])

        if len(matching_ids) == 1:
            # Unambiguous match
            target_id = matching_ids[0]
            return ResolutionResult(
                target_id=target_id,
                target_resolved=target_id,
                status=LinkStatus.VALID,
                strategy="alias",
            )
        if len(matching_ids) > 1:
            # Ambiguous match
            logger.warning(
                f"Ambiguous alias '{target_raw}' matches {len(matching_ids)} entries: "
                f"{matching_ids}",
            )
            return ResolutionResult(
                target_id=None,
                target_resolved=None,
                status=LinkStatus.AMBIGUOUS,
                strategy="alias_ambiguous",
            )

        return None

    def _resolve_by_fuzzy(self, target_raw: str) -> ResolutionResult | None:
        """Resolve link by fuzzy normalized text match.

        Args:
            target_raw: Raw target string

        Returns:
            ResolutionResult if successful, None otherwise
        """
        normalized = self._normalize_text(target_raw)
        if not normalized:
            return None

        target_id = self._title_normalized.get(normalized)
        if target_id:
            return ResolutionResult(
                target_id=target_id,
                target_resolved=target_id,
                status=LinkStatus.VALID,
                strategy="fuzzy",
            )

        return None

    def _resolve_code_reference(
        self,
        target_raw: str,
        source_entry: KnowledgeEntry,
    ) -> ResolutionResult | None:
        """Resolve code reference links.

        Format: "code:path/to/file.py" or "code:path/to/file.py::ClassName"

        Args:
            target_raw: Raw target string (should start with "code:")
            source_entry: Source entry (for relative path resolution)

        Returns:
            ResolutionResult if successful, None otherwise
        """
        if not target_raw.startswith("code:"):
            return None

        # Extract path after "code:" prefix
        path_part = target_raw[5:]
        file_path, _, symbol = path_part.partition("::")

        # Resolve file path
        if not source_entry.file_path:
            return None

        # Try relative to source
        resolved_file = (source_entry.file_path.parent / file_path).resolve()
        if not resolved_file.exists():
            # Try relative to workspace
            resolved_file = (self.workspace_root / file_path).resolve()

        if resolved_file.exists():
            # For code refs, target_resolved is the file path (not an ID)
            return ResolutionResult(
                target_id=None,  # Code files don't have Knowledge IDs
                target_resolved=str(resolved_file),
                status=LinkStatus.VALID,
                strategy="code_reference",
            )

        return ResolutionResult(
            target_id=None,
            target_resolved=None,
            status=LinkStatus.BROKEN,
            strategy="code_file_not_found",
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for fuzzy matching.

        Rules:
        - Convert to lowercase
        - Remove all punctuation (including hyphens)
        - Collapse multiple spaces to single space
        - Strip leading/trailing whitespace

        Args:
            text: Text to normalize

        Returns:
            Normalized text string

        Examples:
            >>> LinkResolver._normalize_text("Fase 01")
            'fase01'
            >>> LinkResolver._normalize_text("Introduction: Part 1")
            'introductionpart1'
            >>> LinkResolver._normalize_text("Hello-World")
            'helloworld'
        """
        if not text:
            return ""

        normalized = text.lower()
        # Remove all punctuation and spaces
        normalized = re.sub(r"[^\w]", "", normalized)
        return normalized.strip()
