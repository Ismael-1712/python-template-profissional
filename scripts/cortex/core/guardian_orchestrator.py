"""Guardian Orchestrator - Orchestrates configuration visibility checks.

This module handles the Guardian feature, which scans code for configurations
(environment variables, etc.) and checks if they are properly documented.
It identifies "orphans" - configurations that exist in code but not in docs.

Architecture:
    - Core Layer: Business logic for orphan detection
    - Depends on: ConfigScanner, DocumentationMatcher
    - Used by: CLI command (guardian check)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from scripts.core.guardian.matcher import DocumentationMatcher
from scripts.core.guardian.models import ConfigFinding, ScanResult
from scripts.core.guardian.scanner import ConfigScanner


@dataclass
class OrphanCheckResult:
    """Result of orphan detection check."""

    orphans: list[ConfigFinding]
    documented: dict[str, list[Path]]
    total_findings: int
    files_scanned: int
    scan_errors: list[str] = field(default_factory=list)

    @property
    def has_orphans(self) -> bool:
        """Check if orphans were found."""
        return len(self.orphans) > 0

    @property
    def success(self) -> bool:
        """Check if all configurations are documented."""
        return not self.has_orphans


class GuardianOrchestrator:
    """Orchestrates configuration visibility checks."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize the orchestrator.

        Args:
            project_root: Root directory of the project (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()

    def check_orphans(
        self,
        scan_path: Path,
        docs_path: Path,
    ) -> OrphanCheckResult:
        """Check for undocumented configurations (orphans).

        Scans Python code for environment variables and other configurations,
        then checks if they are documented. Reports any "orphans".

        Args:
            scan_path: Path to scan (file or directory)
            docs_path: Path to documentation directory

        Returns:
            OrphanCheckResult with orphan detection results
        """
        try:
            # Step 1: Scan code for configurations
            scanner = ConfigScanner(project_root=self.project_root)

            if scan_path.is_file():
                # Scan single file
                findings = scanner.scan_file(scan_path)
                scan_result = ScanResult(
                    findings=findings,
                    files_scanned=1,
                )
            else:
                # Scan directory
                scan_result = scanner.scan_project(scan_path)

            # Step 2: Match with documentation
            matcher = DocumentationMatcher(docs_path)
            orphans, documented = matcher.find_orphans(scan_result.findings)

            return OrphanCheckResult(
                orphans=orphans,
                documented=documented,
                total_findings=scan_result.total_findings,
                files_scanned=scan_result.files_scanned,
                scan_errors=scan_result.errors,
            )

        except Exception as e:  # noqa: BLE001
            # Return error result
            return OrphanCheckResult(
                orphans=[],
                documented={},
                total_findings=0,
                files_scanned=0,
                scan_errors=[str(e)],
            )
