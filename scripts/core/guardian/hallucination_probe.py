"""Hallucination Probe - Needle Test (Canary) for Knowledge System.

This module implements the "Needle Test" pattern to detect hallucination
in LLM-powered systems. It injects a known "canary" knowledge entry and
verifies that the system can correctly retrieve and validate it.

The probe serves as a sanity check for the Knowledge Scanner and ensures
that the system is not fabricating or missing critical knowledge entries.

Usage:
    probe = HallucinationProbe(workspace_root=Path('/project'))
    if probe.probe():
        print("System is healthy - canary found")
    else:
        print("WARNING: System hallucination detected")

    # Detailed validation:
    result = probe.run()
    print(f"Status: {'PASS' if result.passed else 'FAIL'}")
    print(f"Details: {result.message}")

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
from scripts.core.cortex.models import DocStatus, KnowledgeEntry

logger = logging.getLogger(__name__)


@dataclass
class ProbeResult:
    """Result of a hallucination probe test.

    Contains detailed information about the probe execution,
    including success status, diagnostic message, and the
    canary entry if found.

    Attributes:
        success: True if canary was found and validated successfully
        message: Human-readable diagnostic message
        found_entry: The canary KnowledgeEntry if found, None otherwise
        total_entries_scanned: Total number of entries scanned during probe

    Example:
        >>> result = ProbeResult(
        ...     success=True,
        ...     message="Canary 'kno-001' found and validated",
        ...     found_entry=canary_entry,
        ...     total_entries_scanned=42,
        ... )
        >>> assert result.passed is True
    """

    success: bool
    message: str
    found_entry: KnowledgeEntry | None
    total_entries_scanned: int

    @property
    def passed(self) -> bool:
        """Alias for success field for semantic clarity.

        Returns:
            True if the probe test passed (canary found and valid)
        """
        return self.success


class HallucinationProbe:
    """Probe to detect hallucination in the Knowledge System.

    Implements the "Needle Test" pattern by searching for a specific
    canary knowledge entry (kno-001) and validating its properties.
    This ensures the system is not fabricating or losing knowledge.

    The probe operates in two modes:
    - Simple boolean check via probe()
    - Detailed validation via run()

    Attributes:
        workspace_root: Root directory of the workspace
        canary_id: ID of the canary knowledge entry (default: "kno-001")
        scanner: KnowledgeScanner instance for scanning knowledge entries

    Example:
        >>> probe = HallucinationProbe(workspace_root=Path('/project'))
        >>> if not probe.probe():
        ...     logger.error("Hallucination detected - canary missing!")
    """

    def __init__(
        self,
        workspace_root: Path,
        canary_id: str = "kno-001",
    ) -> None:
        """Initialize the hallucination probe.

        Args:
            workspace_root: Root directory of the workspace containing docs/
            canary_id: ID of the canary knowledge entry to search for
        """
        self.workspace_root = workspace_root
        self.canary_id = canary_id
        self.scanner = KnowledgeScanner(workspace_root=workspace_root)
        logger.debug(
            f"HallucinationProbe initialized for workspace: {workspace_root}",
        )

    def probe(self) -> bool:
        """Simple boolean check for canary existence.

        Scans the knowledge base and returns True if the canary
        is found with ACTIVE status.

        Returns:
            True if canary found and active, False otherwise
        """
        try:
            entries = self.scanner.scan()
            canary = self._find_canary(entries)
            if canary is None:
                logger.warning(f"Canary '{self.canary_id}' not found in scan")
                return False
            if canary.status != DocStatus.ACTIVE:
                logger.warning(
                    f"Canary '{self.canary_id}' found but status is "
                    f"{canary.status.value}, expected ACTIVE",
                )
                return False
            logger.info(f"Canary '{self.canary_id}' found and validated")
            return True
        except Exception as e:
            logger.error(f"Probe failed with exception: {e}")
            return False

    def run(self) -> ProbeResult:
        """Run detailed hallucination probe with full validation.

        Scans the knowledge base, searches for the canary, and
        validates all its properties. Returns a detailed result
        object with diagnostics.

        Returns:
            ProbeResult with success status, message, and found entry
        """
        try:
            entries = self.scanner.scan()
            canary = self._find_canary(entries)
            return self.validate_canary_properties(canary, len(entries))
        except Exception as e:
            logger.error(f"Probe execution failed: {e}")
            return ProbeResult(
                success=False,
                message=f"Probe failed with exception: {e}",
                found_entry=None,
                total_entries_scanned=0,
            )

    def _find_canary(
        self,
        entries: list[KnowledgeEntry],
    ) -> KnowledgeEntry | None:
        """Search for the canary entry in the scanned entries.

        Args:
            entries: List of KnowledgeEntry objects from scanner

        Returns:
            The canary KnowledgeEntry if found, None otherwise
        """
        for entry in entries:
            if entry.id == self.canary_id:
                logger.debug(f"Canary '{self.canary_id}' located in scan")
                return entry
        logger.debug(f"Canary '{self.canary_id}' not found in {len(entries)} entries")
        return None

    def validate_canary_properties(
        self,
        entry: KnowledgeEntry | None,
        count: int,
    ) -> ProbeResult:
        """Validate the canary entry properties.

        Performs strict validation of the canary entry:
        - Entry must not be None
        - Status must be ACTIVE
        - ID must match expected canary_id

        Args:
            entry: The canary KnowledgeEntry or None if not found
            count: Total number of entries scanned

        Returns:
            ProbeResult with validation outcome and diagnostics
        """
        # CRITICAL: Protect against None before accessing attributes
        if entry is None:
            return ProbeResult(
                success=False,
                message=(
                    f"Canary '{self.canary_id}' not found in {count} scanned entries"
                ),
                found_entry=None,
                total_entries_scanned=count,
            )

        # Validate status using Enum comparison (not string)
        if entry.status != DocStatus.ACTIVE:
            return ProbeResult(
                success=False,
                message=(
                    f"Canary '{self.canary_id}' found but status is "
                    f"{entry.status.value}, expected ACTIVE"
                ),
                found_entry=entry,
                total_entries_scanned=count,
            )

        # All checks passed
        logger.info(
            f"Canary '{self.canary_id}' validated successfully "
            f"(scanned {count} entries)",
        )
        return ProbeResult(
            success=True,
            message=(
                f"Canary '{self.canary_id}' found and validated "
                f"(status: ACTIVE, scanned: {count} entries)"
            ),
            found_entry=entry,
            total_entries_scanned=count,
        )
