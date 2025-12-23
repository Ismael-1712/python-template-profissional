"""Unit tests for AuditOrchestrator.

Tests the orchestration logic for audit operations, including metadata
validation and Knowledge Graph health checks.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from scripts.core.cortex.audit_orchestrator import AuditOrchestrator
from scripts.core.cortex.models import (
    FullAuditResult,
    KnowledgeAuditResult,
    MetadataAuditResult,
)


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """Create temporary workspace root for testing."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    knowledge_dir = docs_dir / "knowledge"
    knowledge_dir.mkdir()
    return tmp_path


@pytest.fixture
def sample_md_files(workspace_root: Path) -> list[Path]:
    """Create sample Markdown files for testing."""
    docs_dir = workspace_root / "docs"

    # Create some test files
    files = []
    for i in range(3):
        file_path = docs_dir / f"test{i}.md"
        file_path.write_text(f"# Test Document {i}\n\nContent here.")
        files.append(file_path)

    return files


@pytest.fixture
def orchestrator(workspace_root: Path) -> AuditOrchestrator:
    """Create AuditOrchestrator instance for testing."""
    return AuditOrchestrator(workspace_root=workspace_root)


class TestAuditOrchestratorInit:
    """Test AuditOrchestrator initialization."""

    def test_init_with_defaults(self, workspace_root: Path) -> None:
        """Test initialization with default parameters."""
        orchestrator = AuditOrchestrator(workspace_root=workspace_root)

        assert orchestrator.workspace_root == workspace_root.resolve()
        assert orchestrator.knowledge_dir == workspace_root / "docs/knowledge"
        assert orchestrator.fs is not None
        assert orchestrator.parser is not None

    def test_init_with_custom_knowledge_dir(self, workspace_root: Path) -> None:
        """Test initialization with custom knowledge directory."""
        custom_dir = workspace_root / "custom/knowledge"
        orchestrator = AuditOrchestrator(
            workspace_root=workspace_root,
            knowledge_dir=custom_dir,
        )

        assert orchestrator.knowledge_dir == custom_dir


class TestCollectMarkdownFiles:
    """Test collect_markdown_files method."""

    def test_collect_from_directory(
        self,
        orchestrator: AuditOrchestrator,
        sample_md_files: list[Path],
    ) -> None:
        """Test collecting Markdown files from directory."""
        docs_dir = orchestrator.workspace_root / "docs"
        files = orchestrator.collect_markdown_files(docs_dir)

        assert len(files) >= 3
        assert all(f.suffix == ".md" for f in files)

    def test_collect_single_file(
        self,
        orchestrator: AuditOrchestrator,
        sample_md_files: list[Path],
    ) -> None:
        """Test collecting single Markdown file."""
        target_file = sample_md_files[0]
        files = orchestrator.collect_markdown_files(target_file)

        assert len(files) == 1
        assert files[0] == target_file

    def test_collect_nonexistent_path(
        self,
        orchestrator: AuditOrchestrator,
    ) -> None:
        """Test error when path doesn't exist."""
        nonexistent = orchestrator.workspace_root / "nonexistent"

        with pytest.raises(FileNotFoundError, match="does not exist"):
            orchestrator.collect_markdown_files(nonexistent)

    def test_collect_non_markdown_file(
        self,
        orchestrator: AuditOrchestrator,
        workspace_root: Path,
    ) -> None:
        """Test error when file is not Markdown."""
        txt_file = workspace_root / "test.txt"
        txt_file.write_text("Not markdown")

        with pytest.raises(ValueError, match="not a Markdown file"):
            orchestrator.collect_markdown_files(txt_file)


class TestRunMetadataAudit:
    """Test run_metadata_audit method."""

    @patch("scripts.core.cortex.audit_orchestrator.MetadataAuditor")
    def test_metadata_audit_success(
        self,
        mock_auditor_class: Mock,
        orchestrator: AuditOrchestrator,
        sample_md_files: list[Path],
    ) -> None:
        """Test successful metadata audit."""
        # Setup mock
        mock_auditor = MagicMock()
        mock_auditor_class.return_value = mock_auditor

        mock_report = MagicMock()
        mock_report.total_errors = 0
        mock_report.total_warnings = 2
        mock_report.root_violations = []
        mock_report.is_successful = True
        mock_auditor.audit.return_value = mock_report

        # Execute
        result = orchestrator.run_metadata_audit(
            path=orchestrator.workspace_root / "docs",
            fail_on_error=False,
        )

        # Verify
        assert isinstance(result, MetadataAuditResult)
        assert result.should_fail is False
        assert result.report == mock_report
        assert len(result.files_audited) >= 3
        mock_auditor.audit.assert_called_once()

    @patch("scripts.core.cortex.audit_orchestrator.MetadataAuditor")
    def test_metadata_audit_with_errors(
        self,
        mock_auditor_class: Mock,
        orchestrator: AuditOrchestrator,
    ) -> None:
        """Test metadata audit with errors and fail_on_error=True."""
        # Setup mock
        mock_auditor = MagicMock()
        mock_auditor_class.return_value = mock_auditor

        mock_report = MagicMock()
        mock_report.total_errors = 5
        mock_report.total_warnings = 0
        mock_report.root_violations = ["README.md"]
        mock_report.is_successful = False
        mock_auditor.audit.return_value = mock_report

        # Execute
        result = orchestrator.run_metadata_audit(
            path=orchestrator.workspace_root / "docs",
            fail_on_error=True,
        )

        # Verify
        assert result.should_fail is True
        assert len(result.root_violations) == 1

    @patch("scripts.core.cortex.audit_orchestrator.MetadataAuditor")
    def test_metadata_audit_default_path(
        self,
        mock_auditor_class: Mock,
        orchestrator: AuditOrchestrator,
        sample_md_files: list[Path],
    ) -> None:
        """Test metadata audit with default path (docs/)."""
        # Setup mock
        mock_auditor = MagicMock()
        mock_auditor_class.return_value = mock_auditor
        mock_report = MagicMock()
        mock_report.total_errors = 0
        mock_report.total_warnings = 0
        mock_report.root_violations = []
        mock_auditor.audit.return_value = mock_report

        # Execute with path=None (should default to docs/)
        result = orchestrator.run_metadata_audit()

        # Verify default path was used
        assert isinstance(result, MetadataAuditResult)


class TestRunKnowledgeAudit:
    """Test run_knowledge_audit method."""

    @patch("scripts.core.cortex.audit_orchestrator.KnowledgeAuditor")
    def test_knowledge_audit_success(
        self,
        mock_auditor_class: Mock,
        orchestrator: AuditOrchestrator,
    ) -> None:
        """Test successful Knowledge Graph audit."""
        # Setup mock
        mock_auditor = MagicMock()
        mock_auditor_class.return_value = mock_auditor

        mock_validation_report = MagicMock()
        mock_validation_report.is_healthy = True
        mock_validation_report.metrics.health_score = 0.95

        mock_entry = MagicMock()
        mock_entry.links = [
            MagicMock(status=MagicMock(value="valid")),
            MagicMock(status=MagicMock(value="valid")),
        ]

        mock_auditor.validate.return_value = (
            mock_validation_report,
            [mock_entry],
        )

        # Execute
        result = orchestrator.run_knowledge_audit(strict=False)

        # Verify
        assert isinstance(result, KnowledgeAuditResult)
        assert result.num_entries == 1
        assert result.total_links == 2
        assert result.valid_links == 2
        assert result.broken_links == 0
        assert result.should_fail is False
        mock_auditor.save_report.assert_called_once()

    @patch("scripts.core.cortex.audit_orchestrator.KnowledgeAuditor")
    def test_knowledge_audit_with_broken_links_strict(
        self,
        mock_auditor_class: Mock,
        orchestrator: AuditOrchestrator,
    ) -> None:
        """Test Knowledge Graph audit with broken links in strict mode."""
        # Setup mock
        mock_auditor = MagicMock()
        mock_auditor_class.return_value = mock_auditor

        mock_validation_report = MagicMock()
        mock_validation_report.is_healthy = False

        mock_entry = MagicMock()
        mock_entry.links = [
            MagicMock(status=MagicMock(value="valid")),
            MagicMock(status=MagicMock(value="broken")),
            MagicMock(status=MagicMock(value="broken")),
        ]

        mock_auditor.validate.return_value = (
            mock_validation_report,
            [mock_entry],
        )

        # Execute with strict=True
        result = orchestrator.run_knowledge_audit(strict=True)

        # Verify
        assert result.broken_links == 2
        assert result.should_fail is True

    @patch("scripts.core.cortex.audit_orchestrator.KnowledgeAuditor")
    def test_knowledge_audit_custom_output_path(
        self,
        mock_auditor_class: Mock,
        orchestrator: AuditOrchestrator,
        workspace_root: Path,
    ) -> None:
        """Test Knowledge Graph audit with custom output path."""
        # Setup mock
        mock_auditor = MagicMock()
        mock_auditor_class.return_value = mock_auditor
        mock_validation_report = MagicMock()
        mock_auditor.validate.return_value = (mock_validation_report, [])

        # Execute with custom output path
        custom_path = workspace_root / "custom/report.md"
        result = orchestrator.run_knowledge_audit(output_path=custom_path)

        # Verify
        assert result.output_path == custom_path


class TestRunFullAudit:
    """Test run_full_audit method."""

    @patch("scripts.core.cortex.audit_orchestrator.KnowledgeAuditor")
    @patch("scripts.core.cortex.audit_orchestrator.MetadataAuditor")
    def test_full_audit_metadata_only(
        self,
        mock_metadata_class: Mock,
        mock_knowledge_class: Mock,
        orchestrator: AuditOrchestrator,
        sample_md_files: list[Path],
    ) -> None:
        """Test full audit with only metadata check (check_links=False)."""
        # Setup metadata mock
        mock_metadata = MagicMock()
        mock_metadata_class.return_value = mock_metadata
        mock_report = MagicMock()
        mock_report.total_errors = 0
        mock_report.total_warnings = 0
        mock_report.root_violations = []
        mock_metadata.audit.return_value = mock_report

        # Execute
        result = orchestrator.run_full_audit(
            path=orchestrator.workspace_root / "docs",
            check_links=False,
        )

        # Verify
        assert isinstance(result, FullAuditResult)
        assert result.metadata_result is not None
        assert result.knowledge_result is None
        assert result.should_fail is False

    @patch("scripts.core.cortex.audit_orchestrator.KnowledgeAuditor")
    @patch("scripts.core.cortex.audit_orchestrator.MetadataAuditor")
    def test_full_audit_with_knowledge_check(
        self,
        mock_metadata_class: Mock,
        mock_knowledge_class: Mock,
        orchestrator: AuditOrchestrator,
        sample_md_files: list[Path],
    ) -> None:
        """Test full audit with both metadata and Knowledge Graph checks."""
        # Setup metadata mock
        mock_metadata = MagicMock()
        mock_metadata_class.return_value = mock_metadata
        mock_metadata_report = MagicMock()
        mock_metadata_report.total_errors = 0
        mock_metadata_report.root_violations = []
        mock_metadata.audit.return_value = mock_metadata_report

        # Setup knowledge mock
        mock_knowledge = MagicMock()
        mock_knowledge_class.return_value = mock_knowledge
        mock_validation_report = MagicMock()
        mock_validation_report.is_healthy = True
        mock_knowledge.validate.return_value = (mock_validation_report, [])

        # Execute
        result = orchestrator.run_full_audit(
            path=orchestrator.workspace_root / "docs",
            check_links=True,
        )

        # Verify
        assert result.metadata_result is not None
        assert result.knowledge_result is not None
        assert result.should_fail is False

    @patch("scripts.core.cortex.audit_orchestrator.KnowledgeAuditor")
    @patch("scripts.core.cortex.audit_orchestrator.MetadataAuditor")
    def test_full_audit_aggregates_failures(
        self,
        mock_metadata_class: Mock,
        mock_knowledge_class: Mock,
        orchestrator: AuditOrchestrator,
        sample_md_files: list[Path],
    ) -> None:
        """Test that full audit aggregates failure status from both audits."""
        # Setup metadata mock with errors
        mock_metadata = MagicMock()
        mock_metadata_class.return_value = mock_metadata
        mock_metadata_report = MagicMock()
        mock_metadata_report.total_errors = 3
        mock_metadata_report.root_violations = []
        mock_metadata.audit.return_value = mock_metadata_report

        # Setup knowledge mock with broken links
        mock_knowledge = MagicMock()
        mock_knowledge_class.return_value = mock_knowledge
        mock_validation_report = MagicMock()
        mock_entry = MagicMock()
        mock_entry.links = [MagicMock(status=MagicMock(value="broken"))]
        mock_knowledge.validate.return_value = (mock_validation_report, [mock_entry])

        # Execute with both fail flags AND path to ensure metadata runs
        result = orchestrator.run_full_audit(
            path=orchestrator.workspace_root / "docs",
            check_links=True,
            fail_on_error=True,
            strict=True,
        )

        # Verify both failures are detected
        assert result.metadata_result is not None
        assert result.knowledge_result is not None
        assert result.should_fail is True


class TestSaveKnowledgeReport:
    """Test save_knowledge_report method."""

    @patch("scripts.core.cortex.audit_orchestrator.KnowledgeAuditor")
    def test_save_report_creates_directory(
        self,
        mock_auditor_class: Mock,
        orchestrator: AuditOrchestrator,
        workspace_root: Path,
    ) -> None:
        """Test that save_knowledge_report creates output directory."""
        # Setup mock
        mock_auditor = MagicMock()
        mock_auditor_class.return_value = mock_auditor

        mock_validation_report = MagicMock()
        output_path = workspace_root / "new/nested/report.md"

        # Execute
        orchestrator.save_knowledge_report(mock_validation_report, output_path)

        # Verify directory was created
        assert output_path.parent.exists()
        mock_auditor.save_report.assert_called_once_with(
            mock_validation_report,
            output_path,
        )
