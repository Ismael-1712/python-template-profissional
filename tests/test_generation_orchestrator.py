"""Tests for GenerationOrchestrator.

This module tests the document generation orchestrator using mocks
to isolate business logic from I/O dependencies.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.core.cortex.generation_orchestrator import (
    GenerationOrchestrator,
    GenerationTarget,
)
from scripts.core.cortex.models import (
    BatchGenerationResult,
    DriftCheckResult,
    SingleGenerationResult,
)


@pytest.fixture
def mock_generator() -> Mock:
    """Mock DocumentGenerator for testing."""
    generator = Mock()
    generator.generate_document = Mock(return_value="# Generated Content\n\nTest")
    return generator


@pytest.fixture
def orchestrator(mock_generator: Mock, tmp_path: Path) -> GenerationOrchestrator:
    """Create orchestrator with mocked generator."""
    return GenerationOrchestrator(
        project_root=tmp_path,
        generator=mock_generator,
    )


class TestGenerationTarget:
    """Test GenerationTarget enum."""

    def test_enum_values(self) -> None:
        """Test enum has expected values."""
        assert GenerationTarget.README.value == "readme"
        assert GenerationTarget.CONTRIBUTING.value == "contributing"
        assert GenerationTarget.ALL.value == "all"


class TestGenerateSingle:
    """Test generate_single method."""

    def test_generate_readme_success(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful README generation."""
        result = orchestrator.generate_single(
            target=GenerationTarget.README,
            dry_run=False,
        )

        # Verify result structure
        assert isinstance(result, SingleGenerationResult)
        assert result.success is True
        assert result.target == "readme"
        assert result.content == "# Generated Content\n\nTest"
        assert result.content_size == len("# Generated Content\n\nTest")
        assert result.was_written is True
        assert result.template_name == "README.md.j2"
        assert result.output_path == tmp_path / "README.md"
        assert result.error_message is None

        # Verify generator was called
        mock_generator.generate_document.assert_called_once_with(
            template_name="README.md.j2",
            output_path=None,
        )

        # Verify file was written
        assert (tmp_path / "README.md").exists()
        assert (tmp_path / "README.md").read_text() == "# Generated Content\n\nTest"

    def test_generate_contributing_success(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
    ) -> None:
        """Test successful CONTRIBUTING generation."""
        result = orchestrator.generate_single(
            target=GenerationTarget.CONTRIBUTING,
            dry_run=False,
        )

        assert result.success is True
        assert result.target == "contributing"
        assert result.template_name == "CONTRIBUTING.md.j2"

    def test_generate_dry_run(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
        tmp_path: Path,
    ) -> None:
        """Test dry-run mode (no file writing)."""
        result = orchestrator.generate_single(
            target=GenerationTarget.README,
            dry_run=True,
        )

        # Should generate content but not write to disk
        assert result.success is True
        assert result.content == "# Generated Content\n\nTest"
        assert result.was_written is False

        # File should NOT exist
        assert not (tmp_path / "README.md").exists()

    def test_generate_custom_output_path(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
        tmp_path: Path,
    ) -> None:
        """Test generation with custom output path."""
        custom_path = tmp_path / "custom" / "MY_README.md"

        result = orchestrator.generate_single(
            target=GenerationTarget.README,
            output_path=custom_path,
            dry_run=False,
        )

        assert result.success is True
        assert result.output_path == custom_path.resolve()
        assert custom_path.exists()

    def test_generate_all_target_raises_error(
        self,
        orchestrator: GenerationOrchestrator,
    ) -> None:
        """Test that ALL target raises ValueError."""
        result = orchestrator.generate_single(
            target=GenerationTarget.ALL,
            dry_run=True,
        )

        assert result.success is False
        assert result.error_message and "ALL" in result.error_message
        assert result.content == ""

    def test_generate_template_not_found(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
    ) -> None:
        """Test handling of missing template."""
        mock_generator.generate_document.side_effect = FileNotFoundError(
            "Template not found",
        )

        result = orchestrator.generate_single(
            target=GenerationTarget.README,
            dry_run=True,
        )

        assert result.success is False
        assert result.error_message and "Template not found" in result.error_message

    def test_generate_unexpected_error(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
    ) -> None:
        """Test handling of unexpected errors."""
        mock_generator.generate_document.side_effect = RuntimeError("Unexpected error")

        result = orchestrator.generate_single(
            target=GenerationTarget.README,
            dry_run=True,
        )

        assert result.success is False
        assert result.error_message and "Unexpected error" in result.error_message


class TestGenerateBatch:
    """Test generate_batch method."""

    def test_batch_generation_success(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful batch generation of all documents."""
        result = orchestrator.generate_batch(dry_run=False)

        # Verify result structure
        assert isinstance(result, BatchGenerationResult)
        assert result.success is True
        assert result.total_count == 2
        assert result.success_count == 2
        assert result.error_count == 0
        assert result.total_bytes > 0
        assert len(result.results) == 2

        # Verify individual results
        assert result.results[0].target == "readme"
        assert result.results[1].target == "contributing"

        # Verify files were created
        assert (tmp_path / "README.md").exists()
        assert (tmp_path / "CONTRIBUTING.md").exists()

        # Verify generator was called twice
        assert mock_generator.generate_document.call_count == 2

    def test_batch_generation_dry_run(
        self,
        orchestrator: GenerationOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test batch generation in dry-run mode."""
        result = orchestrator.generate_batch(dry_run=True)

        assert result.success is True
        assert result.total_count == 2
        assert result.success_count == 2

        # Verify no files were written
        assert not (tmp_path / "README.md").exists()
        assert not (tmp_path / "CONTRIBUTING.md").exists()

    def test_batch_generation_partial_failure(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
    ) -> None:
        """Test batch generation with one failure."""
        # First call succeeds, second fails
        mock_generator.generate_document.side_effect = [
            "# README Content",
            FileNotFoundError("Template not found"),
        ]

        result = orchestrator.generate_batch(dry_run=False)

        assert result.success is False  # Overall failure
        assert result.total_count == 2
        assert result.success_count == 1
        assert result.error_count == 1
        assert result.has_errors is True
        assert result.all_succeeded is False

    def test_batch_properties(self, orchestrator: GenerationOrchestrator) -> None:
        """Test BatchGenerationResult properties."""
        result = orchestrator.generate_batch(dry_run=True)

        assert result.has_errors is False
        assert result.all_succeeded is True


class TestCheckDrift:
    """Test check_drift method."""

    def test_no_drift_file_matches_template(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
        tmp_path: Path,
    ) -> None:
        """Test drift check when file matches expected content."""
        # Create file with expected content
        readme_path = tmp_path / "README.md"
        expected_content = "# Generated Content\n\nTest"
        readme_path.write_text(expected_content)

        result = orchestrator.check_drift(GenerationTarget.README)

        assert isinstance(result, DriftCheckResult)
        assert result.has_drift is False
        assert result.target == "readme"
        assert result.output_path == readme_path
        assert result.diff == ""
        assert result.line_changes == 0
        assert result.current_content == expected_content
        assert result.expected_content == expected_content
        assert result.error_message is None

    def test_drift_detected(
        self,
        orchestrator: GenerationOrchestrator,
        mock_generator: Mock,
        tmp_path: Path,
    ) -> None:
        """Test drift detection when file differs from template."""
        # Create file with different content
        readme_path = tmp_path / "README.md"
        readme_path.write_text("# Old Content\n\nOutdated")

        result = orchestrator.check_drift(GenerationTarget.README)

        assert result.has_drift is True
        assert result.target == "readme"
        assert len(result.diff) > 0
        assert result.line_changes > 0
        assert result.current_content == "# Old Content\n\nOutdated"
        assert result.expected_content == "# Generated Content\n\nTest"

        # Verify diff contains markers
        assert "---" in result.diff or "+++" in result.diff

    def test_drift_file_missing(
        self,
        orchestrator: GenerationOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test drift check when file doesn't exist."""
        result = orchestrator.check_drift(GenerationTarget.README)

        # File missing is considered drift
        assert result.has_drift is True
        assert result.current_content == ""
        assert result.expected_content == "# Generated Content\n\nTest"

    def test_drift_all_target_raises_error(
        self,
        orchestrator: GenerationOrchestrator,
    ) -> None:
        """Test that ALL target raises ValueError."""
        result = orchestrator.check_drift(GenerationTarget.ALL)

        assert result.has_drift is False  # Error state
        assert result.error_message and "ALL" in result.error_message

    def test_drift_contributing(
        self,
        orchestrator: GenerationOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test drift check for CONTRIBUTING.md."""
        contrib_path = tmp_path / "CONTRIBUTING.md"
        contrib_path.write_text("# Generated Content\n\nTest")

        result = orchestrator.check_drift(GenerationTarget.CONTRIBUTING)

        assert result.has_drift is False
        assert result.target == "contributing"
        assert result.output_path == contrib_path


class TestCheckBatchDrift:
    """Test check_batch_drift method."""

    def test_batch_drift_all_in_sync(
        self,
        orchestrator: GenerationOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test batch drift check when all files are in sync."""
        # Create both files with expected content
        (tmp_path / "README.md").write_text("# Generated Content\n\nTest")
        (tmp_path / "CONTRIBUTING.md").write_text("# Generated Content\n\nTest")

        results = orchestrator.check_batch_drift()

        assert len(results) == 2
        assert all(not r.has_drift for r in results)
        assert results[0].target == "readme"
        assert results[1].target == "contributing"

    def test_batch_drift_some_drifted(
        self,
        orchestrator: GenerationOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test batch drift check with some drifted files."""
        # README in sync, CONTRIBUTING drifted
        (tmp_path / "README.md").write_text("# Generated Content\n\nTest")
        (tmp_path / "CONTRIBUTING.md").write_text("# Old Content")

        results = orchestrator.check_batch_drift()

        assert len(results) == 2
        assert results[0].has_drift is False  # README
        assert results[1].has_drift is True  # CONTRIBUTING


class TestPrivateHelpers:
    """Test private helper methods."""

    def test_resolve_template_name_readme(
        self,
        orchestrator: GenerationOrchestrator,
    ) -> None:
        """Test template name resolution for README."""
        template = orchestrator._resolve_template_name(GenerationTarget.README)
        assert template == "README.md.j2"

    def test_resolve_template_name_contributing(
        self,
        orchestrator: GenerationOrchestrator,
    ) -> None:
        """Test template name resolution for CONTRIBUTING."""
        template = orchestrator._resolve_template_name(GenerationTarget.CONTRIBUTING)
        assert template == "CONTRIBUTING.md.j2"

    def test_resolve_template_name_all_raises_error(
        self,
        orchestrator: GenerationOrchestrator,
    ) -> None:
        """Test that ALL target raises ValueError."""
        with pytest.raises(ValueError, match="ALL"):
            orchestrator._resolve_template_name(GenerationTarget.ALL)

    def test_resolve_output_path_default(
        self,
        orchestrator: GenerationOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test default output path resolution."""
        path = orchestrator._resolve_output_path(GenerationTarget.README, None)
        assert path == tmp_path / "README.md"

    def test_resolve_output_path_custom(
        self,
        orchestrator: GenerationOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test custom output path resolution."""
        custom = tmp_path / "custom.md"
        path = orchestrator._resolve_output_path(GenerationTarget.README, custom)
        assert path == custom.resolve()

    def test_resolve_output_path_all_raises_error(
        self,
        orchestrator: GenerationOrchestrator,
    ) -> None:
        """Test that ALL target raises ValueError."""
        with pytest.raises(ValueError, match="ALL"):
            orchestrator._resolve_output_path(GenerationTarget.ALL, None)

    def test_validate_target_readme_ok(
        self,
        orchestrator: GenerationOrchestrator,
    ) -> None:
        """Test validation accepts README."""
        # Should not raise
        orchestrator._validate_target(GenerationTarget.README, allow_all=False)

    def test_validate_target_all_disallowed(
        self,
        orchestrator: GenerationOrchestrator,
    ) -> None:
        """Test validation rejects ALL when not allowed."""
        with pytest.raises(ValueError, match="ALL"):
            orchestrator._validate_target(GenerationTarget.ALL, allow_all=False)

    def test_validate_target_all_allowed(
        self,
        orchestrator: GenerationOrchestrator,
    ) -> None:
        """Test validation accepts ALL when explicitly allowed."""
        # Should not raise
        orchestrator._validate_target(GenerationTarget.ALL, allow_all=True)


class TestIntegrationScenarios:
    """Test realistic end-to-end scenarios."""

    def test_full_workflow_generate_then_check(
        self,
        orchestrator: GenerationOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test generating a document then checking for drift."""
        # Step 1: Generate document
        gen_result = orchestrator.generate_single(
            target=GenerationTarget.README,
            dry_run=False,
        )
        assert gen_result.success is True

        # Step 2: Check drift (should be none)
        drift_result = orchestrator.check_drift(GenerationTarget.README)
        assert drift_result.has_drift is False

        # Step 3: Modify file manually
        (tmp_path / "README.md").write_text("# Modified by user")

        # Step 4: Check drift again (should detect changes)
        drift_result2 = orchestrator.check_drift(GenerationTarget.README)
        assert drift_result2.has_drift is True
        assert drift_result2.line_changes > 0

    def test_ci_cd_drift_detection_workflow(
        self,
        orchestrator: GenerationOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Simulate CI/CD drift detection workflow."""
        # Setup: Files were previously generated
        (tmp_path / "README.md").write_text("# Old README")
        (tmp_path / "CONTRIBUTING.md").write_text("# Generated Content\n\nTest")

        # CI runs batch drift check
        results = orchestrator.check_batch_drift()

        # Verify one file drifted
        drifted = [r for r in results if r.has_drift]
        assert len(drifted) == 1
        assert drifted[0].target == "readme"

        # CI would fail based on this result
        assert any(r.has_drift for r in results)
