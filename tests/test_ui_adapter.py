"""Test suite for CORTEX UI Adapter (Presentation Layer).

This module tests the UIPresenter class to ensure all presentation logic
formats messages correctly without actually executing typer commands.

Architecture: Adapter Layer Testing (Hexagonal Architecture)
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import HttpUrl

from scripts.core.cortex.knowledge_orchestrator import SyncResult, SyncSummary
from scripts.core.cortex.migrate import MigrationResult
from scripts.core.cortex.models import (
    DocStatus,
    KnowledgeEntry,
    KnowledgeSource,
    MigrationSummary,
    SingleGenerationResult,
)
from scripts.core.guardian.hallucination_probe import ProbeResult
from scripts.core.guardian.models import ConfigFinding, ConfigType
from scripts.cortex.adapters.ui import UIPresenter


class TestUIPresenter:
    """Test suite for UIPresenter class - all presentation logic."""

    @pytest.fixture(autouse=True)
    def mock_typer(self) -> Generator[None, None, None]:
        """Patch typer.echo and typer.secho for all tests to avoid terminal output."""
        with (
            patch("scripts.cortex.adapters.ui.typer.echo") as mock_echo,
            patch("scripts.cortex.adapters.ui.typer.secho") as mock_secho,
        ):
            self.mock_echo = mock_echo
            self.mock_secho = mock_secho
            yield

    # ==================== Basic Message Display Tests ====================

    def test_show_success(self) -> None:
        """Test success message formatting."""
        """Test success message formatting."""
        UIPresenter.show_success("Operation completed")

        # Verify secho was called with correct parameters
        self.mock_secho.assert_called_once()
        call_args = self.mock_secho.call_args
        assert "✅" in call_args[0][0]
        assert "Operation completed" in call_args[0][0]
        assert call_args[1]["bold"] is False

    def test_show_success_bold(self) -> None:
        """Test success message with bold formatting."""
        UIPresenter.show_success("Important success", bold=True)

        call_args = self.mock_secho.call_args
        assert call_args[1]["bold"] is True

    def test_show_error(self) -> None:
        """Test error message formatting."""
        UIPresenter.show_error("Something went wrong")

        call_args = self.mock_secho.call_args
        assert "❌" in call_args[0][0]
        assert "Something went wrong" in call_args[0][0]
        assert call_args[1]["err"] is True

    def test_show_warning(self) -> None:
        """Test warning message formatting."""
        UIPresenter.show_warning("This is a warning")

        call_args = self.mock_secho.call_args
        assert "⚠️" in call_args[0][0]
        assert "This is a warning" in call_args[0][0]

    def test_show_info(self) -> None:
        """Test info message formatting (plain echo)."""
        UIPresenter.show_info("Information message")

        self.mock_echo.assert_called_once_with("Information message")

    def test_show_blank_line(self) -> None:
        """Test blank line display."""
        UIPresenter.show_blank_line()

        self.mock_echo.assert_called_once_with()

    def test_show_bold_no_color(self) -> None:
        """Test bold message without color."""
        UIPresenter.show_bold("Bold message")

        call_args = self.mock_secho.call_args
        assert "Bold message" in call_args[0][0]
        assert call_args[1]["bold"] is True

    def test_show_bold_with_color(self) -> None:
        """Test bold message with color."""
        import typer

        UIPresenter.show_bold("Colored bold", color=typer.colors.CYAN)

        call_args = self.mock_secho.call_args
        assert "Colored bold" in call_args[0][0]
        assert call_args[1]["bold"] is True
        assert call_args[1]["fg"] == typer.colors.CYAN

    def test_show_header(self) -> None:
        """Test header formatting with separators."""
        UIPresenter.show_header("Test Header", width=50)

        # Should have 3 echo calls: newline+separator, title, separator
        assert self.mock_echo.call_count >= 3
        calls = [str(call) for call in self.mock_echo.call_args_list]
        # Check that separator was printed
        assert any("=" * 50 in str(call) for call in calls)

    # ==================== Hooks Installation Tests ====================

    def test_display_hooks_installation(self) -> None:
        """Test Git hooks installation display."""
        installed_hooks = ["post-merge", "post-checkout", "post-rewrite"]

        UIPresenter.display_hooks_installation(installed_hooks)

        # Verify success message was shown
        success_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "✅" in str(call) and "successfully" in str(call)
        ]
        assert len(success_calls) > 0

        # Verify all hooks were listed
        all_echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        for hook in installed_hooks:
            assert any(hook in call for call in all_echo_calls)

    # ==================== Migration Summary Tests ====================

    def test_display_migration_summary_dry_run(self) -> None:
        """Test migration summary in dry-run mode."""
        summary = MigrationSummary(
            total=10,
            created=5,
            updated=3,
            errors=0,
            results=[
                MigrationResult(
                    file_path=Path("docs/test1.md"),
                    success=True,
                    action="created",
                    message="Created frontmatter",
                ),
                MigrationResult(
                    file_path=Path("docs/test2.md"),
                    success=True,
                    action="updated",
                    message="Updated frontmatter",
                ),
            ],
        )

        UIPresenter.display_migration_summary(
            summary=summary,
            path=Path("/tmp/docs"),
            dry_run=True,
        )

        # Verify dry-run banner was shown
        dry_run_calls = [
            call for call in self.mock_secho.call_args_list if "DRY-RUN" in str(call)
        ]
        assert len(dry_run_calls) > 0

        # Verify stats were printed (secho, not echo)
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        secho_calls = [str(call) for call in self.mock_secho.call_args_list]

        assert any("Total files processed: 10" in call for call in echo_calls)
        assert any("Created: 5" in call for call in secho_calls)
        assert any("Updated: 3" in call for call in secho_calls)

    def test_display_migration_summary_apply_mode(self) -> None:
        """Test migration summary in apply mode (real execution)."""
        summary = MigrationSummary(
            total=5,
            created=2,
            updated=2,
            errors=1,
            results=[],
        )

        UIPresenter.display_migration_summary(
            summary=summary,
            path=Path("/tmp/docs"),
            dry_run=False,
        )

        # Verify apply mode banner was shown
        apply_calls = [
            call for call in self.mock_secho.call_args_list if "APPLY MODE" in str(call)
        ]
        assert len(apply_calls) > 0

        # Verify error count was displayed
        error_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Errors" in str(call) and "1" in str(call)
        ]
        assert len(error_calls) > 0

    def test_display_migration_summary_no_files(self) -> None:
        """Test migration summary when no files found."""
        summary = MigrationSummary(
            total=0,
            created=0,
            updated=0,
            errors=0,
            results=[],
        )

        UIPresenter.display_migration_summary(
            summary=summary,
            path=Path("/tmp/empty"),
            dry_run=True,
        )

        # Verify "no files found" warning was shown
        warning_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "No Markdown files found" in str(call)
        ]
        assert len(warning_calls) > 0

    # ==================== Config Display Tests ====================

    def test_display_config(self) -> None:
        """Test configuration display with YAML formatting."""
        config_data = {
            "scan_paths": ["scripts/", "src/"],
            "file_patterns": ["*.py", "*.toml"],
            "exclude_paths": ["__pycache__/"],
            "custom_patterns": [r"ENV_\w+"],
        }
        config_path = Path("/tmp/config.yaml")

        UIPresenter.display_config(config_data, config_path)

        # Verify config path was shown
        path_calls = [
            call
            for call in self.mock_echo.call_args_list
            if str(config_path) in str(call)
        ]
        assert len(path_calls) > 0

        # Verify summary stats were shown
        stats_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("Scan Paths: 2" in call for call in stats_calls)
        assert any("File Patterns: 2" in call for call in stats_calls)
        assert any("Exclude Paths: 1" in call for call in stats_calls)
        assert any("Custom Patterns: 1" in call for call in stats_calls)

    # ==================== Sync Summary Tests ====================

    def test_display_sync_summary_dry_run(self) -> None:
        """Test knowledge sync summary in dry-run mode."""
        # Create mock knowledge entry
        # (KnowledgeEntry doesn't accept title/path in constructor)
        entry = KnowledgeEntry(
            id="test-entry",
            status=DocStatus.ACTIVE,
            sources=[
                KnowledgeSource(url=HttpUrl("https://example.com/doc1")),
                KnowledgeSource(url=HttpUrl("https://example.com/doc2")),
            ],
        )

        # Create mock sync result
        sync_result = SyncResult(
            entry=entry,
            status=MagicMock(value="updated"),
            error_message=None,
        )

        summary = SyncSummary(
            results=[sync_result],
            total_processed=1,
            successful_count=1,
            updated_count=0,
            not_modified_count=0,
            error_count=0,
        )

        UIPresenter.display_sync_summary(
            summary=summary,
            entry_id="test-entry",
            dry_run=True,
        )

        # Verify dry-run message was shown
        dry_run_calls = [
            call for call in self.mock_echo.call_args_list if "DRY RUN" in str(call)
        ]
        assert len(dry_run_calls) > 0

        # Verify "would sync" message was shown
        would_sync_calls = [
            call for call in self.mock_echo.call_args_list if "Would sync" in str(call)
        ]
        assert len(would_sync_calls) >= 2  # Two sources

    def test_display_sync_summary_success(self) -> None:
        """Test knowledge sync summary in success mode."""
        entry = KnowledgeEntry(
            id="test-entry",
            status=DocStatus.ACTIVE,
            sources=[],
        )

        sync_result = SyncResult(
            entry=entry,
            status=MagicMock(value="updated"),
            error_message=None,
        )

        summary = SyncSummary(
            results=[sync_result],
            total_processed=1,
            successful_count=1,
            updated_count=1,
            not_modified_count=0,
            error_count=0,
        )

        UIPresenter.display_sync_summary(
            summary=summary,
            entry_id=None,
            dry_run=False,
        )

        # Verify success message was shown
        success_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "✅ Synchronization complete" in str(call)
        ]
        assert len(success_calls) > 0

    def test_display_sync_summary_with_errors(self) -> None:
        """Test knowledge sync summary with errors."""
        entry1 = KnowledgeEntry(
            id="success-entry",
            status=DocStatus.ACTIVE,
            sources=[],
        )

        entry2 = KnowledgeEntry(
            id="error-entry",
            status=DocStatus.ACTIVE,
            sources=[],
        )

        results = [
            SyncResult(
                entry=entry1,
                status=MagicMock(value="updated"),
                error_message=None,
            ),
            SyncResult(
                entry=entry2,
                status=MagicMock(value="error"),
                error_message="Network timeout",
            ),
        ]

        summary = SyncSummary(
            results=results,
            total_processed=2,
            successful_count=1,
            updated_count=1,
            not_modified_count=0,
            error_count=1,
        )

        UIPresenter.display_sync_summary(
            summary=summary,
            entry_id=None,
            dry_run=False,
        )

        # Verify error message was shown
        error_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Failed" in str(call) and "Network timeout" in str(call)
        ]
        assert len(error_calls) > 0

        # Verify warning summary was shown
        warning_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "⚠️" in str(call) and "with errors" in str(call)
        ]
        assert len(warning_calls) > 0

    # ==================== Probe Result Tests ====================

    def test_display_probe_result_verbose_success(self) -> None:
        """Test hallucination probe display in verbose mode (success)."""
        canary_entry = KnowledgeEntry(
            id="canary-test",
            status=DocStatus.ACTIVE,
            golden_paths=["recommended-path-1"],
            tags=["canary", "test"],
        )

        probe_result = ProbeResult(
            success=True,
            message="Canary found and validated",
            found_entry=canary_entry,
            total_entries_scanned=42,
        )

        UIPresenter.display_probe_result(
            result=probe_result,
            canary_id="canary-test",
            verbose=True,
        )

        # Verify success message
        success_calls = [
            call for call in self.mock_secho.call_args_list if "✅ PASSED" in str(call)
        ]
        assert len(success_calls) > 0

        # Verify scan details were shown
        details_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("Total entries scanned: 42" in call for call in details_calls)
        assert any("Golden paths" in call for call in details_calls)
        assert any("Tags" in call for call in details_calls)

    def test_display_probe_result_verbose_failure(self) -> None:
        """Test hallucination probe display in verbose mode (failure)."""
        probe_result = ProbeResult(
            success=False,
            message="Canary not found",
            found_entry=None,
            total_entries_scanned=42,
        )

        UIPresenter.display_probe_result(
            result=probe_result,
            canary_id="missing-canary",
            verbose=True,
        )

        # Verify failure message
        failure_calls = [
            call for call in self.mock_secho.call_args_list if "❌ FAILED" in str(call)
        ]
        assert len(failure_calls) > 0

        # Verify warning about hallucination
        warning_calls = [
            call
            for call in self.mock_echo.call_args_list
            if "hallucinating" in str(call)
        ]
        assert len(warning_calls) > 0

    def test_display_probe_result_simple_success(self) -> None:
        """Test hallucination probe display in simple mode (success)."""
        probe_result = ProbeResult(
            success=True,
            message="Canary found",
            found_entry=MagicMock(),
            total_entries_scanned=10,
        )

        UIPresenter.display_probe_result(
            result=probe_result,
            canary_id="test-canary",
            verbose=False,
        )

        # Verify simple success message
        success_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "✅ System healthy" in str(call)
        ]
        assert len(success_calls) > 0

        # Verify tip about verbose mode
        tip_calls = [
            call for call in self.mock_echo.call_args_list if "--verbose" in str(call)
        ]
        assert len(tip_calls) > 0

    def test_display_probe_result_simple_failure(self) -> None:
        """Test hallucination probe display in simple mode (failure)."""
        probe_result = ProbeResult(
            success=False,
            message="Canary not found",
            found_entry=None,
            total_entries_scanned=10,
        )

        UIPresenter.display_probe_result(
            result=probe_result,
            canary_id="test-canary",
            verbose=False,
        )

        # Verify failure message
        failure_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "❌ System check failed" in str(call)
        ]
        assert len(failure_calls) > 0

        # Verify actionable hints were shown
        hints = [
            call
            for call in self.mock_echo.call_args_list
            if "Verify that docs/knowledge/" in str(call)
        ]
        assert len(hints) > 0

    # ==================== Guardian Orphans Tests ====================

    def test_display_guardian_orphans_with_findings(self) -> None:
        """Test guardian orphans display with actual orphans."""
        orphans = [
            ConfigFinding(
                key="UNKNOWN_ENV_VAR",
                config_type=ConfigType.ENV_VAR,
                source_file=Path("src/config.py"),
                line_number=42,
                context="os.getenv('UNKNOWN_ENV_VAR')",
                default_value="default_value",
            ),
            ConfigFinding(
                key="ANOTHER_ORPHAN",
                config_type=ConfigType.ENV_VAR,
                source_file=Path("src/app.py"),
                line_number=15,
                context="config.get('ANOTHER_ORPHAN')",
                default_value=None,
            ),
        ]

        UIPresenter.display_guardian_orphans(orphans=orphans, documented=None)

        # Verify orphans were listed
        orphan_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "UNKNOWN_ENV_VAR" in str(call) or "ANOTHER_ORPHAN" in str(call)
        ]
        assert len(orphan_calls) >= 2

        # Verify location information was shown
        location_calls = [
            call for call in self.mock_echo.call_args_list if "Location:" in str(call)
        ]
        assert len(location_calls) >= 2

    def test_display_guardian_orphans_with_documented(self) -> None:
        """Test guardian orphans display with documented configs."""
        orphans: list[ConfigFinding] = []
        documented = {
            "DOCUMENTED_VAR_1": [Path("docs/config.md")],
            "DOCUMENTED_VAR_2": [Path("docs/setup.md"), Path("README.md")],
        }

        UIPresenter.display_guardian_orphans(orphans=orphans, documented=documented)

        # Verify documented configs were shown
        doc_calls = [
            call
            for call in self.mock_echo.call_args_list
            if "DOCUMENTED_VAR_1" in str(call) or "DOCUMENTED_VAR_2" in str(call)
        ]
        assert len(doc_calls) >= 2

    # ==================== Generation Result Tests ====================

    def test_display_generation_result_success_dry_run(self) -> None:
        """Test generation result display in dry-run mode."""
        gen_result = SingleGenerationResult(
            target="readme",
            success=True,
            output_path=Path("README.md"),
            content="# Test README\n\nContent here...",
            content_size=1024,
            template_name="README.md.j2",
            was_written=False,
            error_message=None,
        )

        UIPresenter.display_generation_result(gen_result, dry_run=True)

        # Verify "would write" message
        would_write_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Would write to" in str(call)
        ]
        assert len(would_write_calls) > 0

        # Verify size was shown
        size_calls = [
            call
            for call in self.mock_echo.call_args_list
            if "Size: 1024 bytes" in str(call)
        ]
        assert len(size_calls) > 0

    def test_display_generation_result_success_real(self) -> None:
        """Test generation result display in apply mode."""
        gen_result = SingleGenerationResult(
            target="contributing",
            success=True,
            output_path=Path("CONTRIBUTING.md"),
            content="# Contributing Guide\n\nWelcome...",
            content_size=2048,
            template_name="CONTRIBUTING.md.j2",
            was_written=True,
            error_message=None,
        )

        UIPresenter.display_generation_result(gen_result, dry_run=False)

        # Verify "generated" message
        generated_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "✅ Generated" in str(call)
        ]
        assert len(generated_calls) > 0

    def test_display_generation_result_failure(self) -> None:
        """Test generation result display when generation fails."""
        gen_result = SingleGenerationResult(
            target="readme",
            success=False,
            output_path=Path("README.md"),
            content="",
            content_size=0,
            template_name="README.md.j2",
            was_written=False,
            error_message="Template not found",
        )

        UIPresenter.display_generation_result(gen_result, dry_run=False)

        # Verify error message
        error_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "❌ Failed" in str(call) and "Template not found" in str(call)
        ]
        assert len(error_calls) > 0

    # ==================== Knowledge Entries Display Tests ====================

    def test_display_knowledge_entries_simple_mode(self) -> None:
        """Test knowledge entries display in simple mode."""
        entries = [
            KnowledgeEntry(
                id="entry-1",
                status=DocStatus.ACTIVE,
            ),
            KnowledgeEntry(
                id="entry-2",
                status=DocStatus.DEPRECATED,
            ),
        ]

        UIPresenter.display_knowledge_entries(entries, verbose=False)

        # Verify entries were listed
        entry_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("entry-1" in call and "active" in call for call in entry_calls)
        assert any("entry-2" in call and "deprecated" in call for call in entry_calls)

    def test_display_knowledge_entries_verbose_mode(self) -> None:
        """Test knowledge entries display in verbose mode."""
        entries = [
            KnowledgeEntry(
                id="detailed-entry",
                status=DocStatus.ACTIVE,
                tags=["important", "guide"],
                golden_paths=["recommended-workflow"],
                sources=[KnowledgeSource(url=HttpUrl("https://example.com/doc"))],
                cached_content=(
                    "This is a long content preview that should be truncated..."
                ),
            ),
        ]

        UIPresenter.display_knowledge_entries(entries, verbose=True)

        # Verify verbose details were shown
        verbose_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("Tags:" in call for call in verbose_calls)
        assert any("Golden Paths:" in call for call in verbose_calls)
        assert any("Sources:" in call for call in verbose_calls)
        assert any("Content:" in call for call in verbose_calls)

    # ==================== Knowledge Scan Tests ====================

    def test_display_scan_header_sequential(self) -> None:
        """Test knowledge scan header in sequential mode."""
        UIPresenter.display_scan_header(Path("/tmp/workspace"), mode="Sequential")

        # Verify header was shown
        header_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Knowledge Base Scanner" in str(call)
        ]
        assert len(header_calls) > 0

        # Verify mode was shown
        mode_calls = [
            call for call in self.mock_echo.call_args_list if "Sequential" in str(call)
        ]
        assert len(mode_calls) > 0

    def test_display_scan_header_parallel(self) -> None:
        """Test knowledge scan header in parallel mode."""
        UIPresenter.display_scan_header(
            Path("/tmp/workspace"),
            mode="EXPERIMENTAL PARALLEL",
        )

        # Verify parallel warning was shown
        parallel_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "EXPERIMENTAL PARALLEL" in str(call)
        ]
        assert len(parallel_calls) > 0

    def test_display_scan_empty_warning(self) -> None:
        """Test warning when no knowledge entries found."""
        UIPresenter.display_scan_empty_warning()

        # Verify warning was shown
        warning_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "No knowledge entries found" in str(call)
        ]
        assert len(warning_calls) > 0

    def test_display_scan_success(self) -> None:
        """Test knowledge scan success message."""
        UIPresenter.display_scan_success(total_count=5)

        # Verify success message with count
        success_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Found 5 knowledge" in str(call)
        ]
        assert len(success_calls) > 0

    def test_display_scan_success_single(self) -> None:
        """Test knowledge scan success with singular entry."""
        UIPresenter.display_scan_success(total_count=1)

        # Verify singular form
        success_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "1 knowledge entry" in str(call)
        ]
        assert len(success_calls) > 0

    # ==================== Guardian Display Tests ====================

    def test_display_guardian_header(self) -> None:
        """Test guardian orphan detection header."""
        UIPresenter.display_guardian_header(
            Path("/tmp/src"),
            Path("/tmp/docs"),
        )

        # Verify header was shown
        header_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Visibility Guardian" in str(call)
        ]
        assert len(header_calls) > 0

        # Verify paths were shown
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("/tmp/src" in call for call in echo_calls)
        assert any("/tmp/docs" in call for call in echo_calls)

    def test_display_guardian_scan_errors(self) -> None:
        """Test guardian scan errors display."""
        errors = ["Error in file1.py", "Error in file2.py"]
        UIPresenter.display_guardian_scan_errors(errors)

        # Verify warning was shown
        warning_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Some files had errors" in str(call)
        ]
        assert len(warning_calls) > 0

        # Verify errors were listed
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("Error in file1.py" in call for call in echo_calls)
        assert any("Error in file2.py" in call for call in echo_calls)

    def test_display_guardian_findings(self) -> None:
        """Test guardian findings summary."""
        UIPresenter.display_guardian_findings(total_findings=10, files_scanned=5)

        # Verify findings were shown
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("10 configurations" in call for call in echo_calls)
        assert any("5 files" in call for call in echo_calls)

    def test_display_guardian_no_configs(self) -> None:
        """Test message when no configs found."""
        UIPresenter.display_guardian_no_configs()

        # Verify success message
        success_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "No configurations found" in str(call)
        ]
        assert len(success_calls) > 0

    def test_display_guardian_results_header(self) -> None:
        """Test guardian results header."""
        UIPresenter.display_guardian_results_header()

        # Verify header was shown (uses secho for RESULTS)
        secho_calls = [str(call) for call in self.mock_secho.call_args_list]
        assert any("RESULTS" in call for call in secho_calls)

        # Verify separators
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("=" in call for call in echo_calls)

    def test_display_guardian_success(self) -> None:
        """Test guardian success message."""
        UIPresenter.display_guardian_success(documented_count=15)

        # Verify success message
        success_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "SUCCESS" in str(call) and "documented" in str(call)
        ]
        assert len(success_calls) > 0

        # Verify count was shown
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("15 configurations" in call for call in echo_calls)

    def test_display_guardian_orphans_header(self) -> None:
        """Test orphans detected header."""
        UIPresenter.display_guardian_orphans_header(orphan_count=3)

        # Verify error message
        error_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "ORPHANS DETECTED" in str(call) and "3" in str(call)
        ]
        assert len(error_calls) > 0

    def test_display_guardian_fail_exit(self) -> None:
        """Test fail-on-error exit message."""
        UIPresenter.display_guardian_fail_exit()

        # Verify exit message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "fail-on-error" in str(call)
        ]
        assert len(secho_calls) > 0

    # ==================== Generate Command Tests ====================

    def test_display_generate_mode_header(self) -> None:
        """Test generate mode header display."""
        UIPresenter.display_generate_mode_header("CHECK MODE")

        # Verify header was shown
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Document Generator" in str(call) and "CHECK MODE" in str(call)
        ]
        assert len(secho_calls) > 0

    def test_display_generate_processing(self) -> None:
        """Test generate processing message."""
        UIPresenter.display_generate_processing("readme", dry_run=False)

        # Verify processing message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Processing" in str(call) and "README" in str(call)
        ]
        assert len(secho_calls) > 0

    def test_display_generate_processing_dry_run(self) -> None:
        """Test generate processing in dry-run mode."""
        UIPresenter.display_generate_processing("contributing", dry_run=True)

        # Verify dry-run icon
        secho_calls = [str(call) for call in self.mock_secho.call_args_list]
        assert any("📄" in call for call in secho_calls)

    def test_display_generate_dry_run_preview(self) -> None:
        """Test dry-run preview display."""
        content = "# Test Content\n\n" + "\n".join([f"Line {i}" for i in range(50)])
        UIPresenter.display_generate_dry_run_preview(content, max_lines=10)

        # Verify preview header
        secho_calls = [
            call for call in self.mock_secho.call_args_list if "DRY RUN" in str(call)
        ]
        assert len(secho_calls) > 0

        # Verify separators
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        separator_count = sum(1 for call in echo_calls if "=" * 70 in call)
        assert separator_count >= 2

    def test_display_generate_dry_run_result(self) -> None:
        """Test dry-run result message."""
        UIPresenter.display_generate_dry_run_result(
            Path("README.md"),
            content_size=2048,
        )

        # Verify would-write message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Would write to" in str(call)
        ]
        assert len(secho_calls) > 0

        # Verify size
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("2048 bytes" in call for call in echo_calls)

    def test_display_generate_success_single(self) -> None:
        """Test successful single generation display."""
        UIPresenter.display_generate_success_single(
            Path("CONTRIBUTING.md"),
            content_size=4096,
            template_name="CONTRIBUTING.md.j2",
        )

        # Verify success message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Generated" in str(call) and "CONTRIBUTING.md" in str(call)
        ]
        assert len(secho_calls) > 0

        # Verify template info
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any(
            "Template:" in call and "CONTRIBUTING.md.j2" in call for call in echo_calls
        )

    def test_display_generate_final_success(self) -> None:
        """Test final success message."""
        UIPresenter.display_generate_final_success()

        # Verify success message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "completed successfully" in str(call)
        ]
        assert len(secho_calls) > 0

    def test_display_generate_batch_summary_success(self) -> None:
        """Test batch summary for successful generation."""
        UIPresenter.display_generate_batch_summary(
            success=True,
            success_count=3,
            error_count=0,
            total_bytes=10240,
            dry_run=False,
        )

        # Verify success message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "SUCCESS" in str(call) and "3 document" in str(call)
        ]
        assert len(secho_calls) > 0

    def test_display_generate_batch_summary_with_errors(self) -> None:
        """Test batch summary with errors."""
        UIPresenter.display_generate_batch_summary(
            success=False,
            success_count=2,
            error_count=1,
            total_bytes=5120,
            dry_run=False,
        )

        # Verify warning message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "with errors" in str(call)
        ]
        assert len(secho_calls) > 0

    def test_display_generate_drift_fix_hint(self) -> None:
        """Test drift fix hint display."""
        UIPresenter.display_generate_drift_fix_hint("readme")

        # Verify drift message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "DRIFT DETECTED" in str(call)
        ]
        assert len(secho_calls) > 0

        # Verify fix hint
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("cortex generate readme" in call for call in echo_calls)

    def test_display_generate_missing_file_tips(self) -> None:
        """Test missing file tips display."""
        UIPresenter.display_generate_missing_file_tips()

        # Verify tips were shown
        echo_calls = [str(call) for call in self.mock_echo.call_args_list]
        assert any("pyproject.toml" in call for call in echo_calls)
        assert any("context.json" in call for call in echo_calls)

    # ==================== Init Command Tests ====================

    def test_display_init_file_warning(self) -> None:
        """Test init file type warning."""
        UIPresenter.display_init_file_warning(Path("test.txt"))

        # Verify warning
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "not a Markdown file" in str(call)
        ]
        assert len(secho_calls) > 0

    def test_display_init_existing_frontmatter_warning(self) -> None:
        """Test existing frontmatter warning."""
        UIPresenter.display_init_existing_frontmatter_warning("test.md")

        # Verify warning
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "already has" in str(call) and "frontmatter" in str(call)
        ]
        assert len(secho_calls) > 0

    def test_display_init_success(self) -> None:
        """Test init success display."""
        yaml_content = "id: test\ntitle: Test\n"
        UIPresenter.display_init_success(Path("test.md"), yaml_content)

        # Verify success message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "Success" in str(call) and "frontmatter" in str(call)
        ]
        assert len(secho_calls) > 0

    def test_display_init_skip_warning(self) -> None:
        """Test init skip warning."""
        UIPresenter.display_init_skip_warning("existing.md")

        # Verify skip message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if "already has frontmatter" in str(call) and "--force" in str(call)
        ]
        assert len(secho_calls) > 0

    # ==================== Hooks Installation Tests ====================

    def test_display_hooks_installing(self) -> None:
        """Test hooks installation message."""
        UIPresenter.display_hooks_installing()

        # Verify installation message
        echo_calls = [
            call
            for call in self.mock_echo.call_args_list
            if "Installing Git hooks" in str(call)
        ]
        assert len(echo_calls) > 0

    def test_display_hooks_git_error(self) -> None:
        """Test hooks Git directory error."""
        UIPresenter.display_hooks_git_error()

        # Verify error message
        secho_calls = [
            call
            for call in self.mock_secho.call_args_list
            if ".git directory not found" in str(call)
        ]
        assert len(secho_calls) > 0
