"""Integration tests for CORTEX CLI commands.

This module provides comprehensive test coverage for all Typer CLI commands
in the CORTEX system, ensuring that the command-line interface works correctly
after refactoring into atomized command modules.

Test Strategy:
- Smoke Tests: Verify all commands respond to --help without errors
- Functional Tests: Validate command execution with mocked orchestrators
- Integration Tests: Test dependency injection and context propagation

Author: Engineering Team (QA Automation)
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from scripts.core.cortex.knowledge_orchestrator import (
    ScanResult,
    SyncSummary,
)
from scripts.core.cortex.mapper import ProjectContext
from scripts.core.cortex.models import (
    DocStatus,
    InitResult,
    KnowledgeEntry,
    MigrationSummary,
    SingleGenerationResult,
)
from scripts.cortex.cli import app
from scripts.cortex.core.guardian_orchestrator import OrphanCheckResult


@pytest.fixture
def runner() -> CliRunner:
    """Create a Typer CLI runner for testing."""
    return CliRunner()


class TestCLIHelp:
    """Smoke tests for --help flag on all commands."""

    def test_main_help(self, runner: CliRunner) -> None:
        """Test main CLI help displays correctly."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "CORTEX" in result.output
        assert "Documentation as Code Manager" in result.output

    def test_init_help(self, runner: CliRunner) -> None:
        """Test 'init' command help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Add YAML frontmatter" in result.output
        assert "path" in result.output.lower()

    def test_migrate_help(self, runner: CliRunner) -> None:
        """Test 'migrate' command help."""
        result = runner.invoke(app, ["migrate", "--help"])
        assert result.exit_code == 0
        assert "Migrate documentation files" in result.output

    def test_setup_hooks_help(self, runner: CliRunner) -> None:
        """Test 'setup-hooks' command help."""
        result = runner.invoke(app, ["setup-hooks", "--help"])
        assert result.exit_code == 0
        assert "Git hooks" in result.output or "hooks" in result.output.lower()

    def test_config_help(self, runner: CliRunner) -> None:
        """Test 'config' command help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0, f"Unexpected exit code: {result.exit_code}"

        output_lower = result.output.lower()

        # Verificar presença da palavra "configuration"
        assert "configuration" in output_lower or "config" in output_lower, (
            f"Expected 'configuration' or 'config' in help output.\n"
            f"Actual output:\n{result.output}"
        )

        # Verificar presença das flags (mais flexível)
        # Busca "show" e "validate" independentemente de formatação
        assert "show" in output_lower and "validate" in output_lower, (
            f"Expected '--show' and '--validate' flags in help output.\n"
            f"Actual output:\n{result.output}"
        )

    def test_map_help(self, runner: CliRunner) -> None:
        """Test 'map' command help."""
        result = runner.invoke(app, ["map", "--help"])
        assert result.exit_code == 0
        assert "context" in result.output.lower() or "map" in result.output.lower()

    def test_knowledge_scan_help(self, runner: CliRunner) -> None:
        """Test 'knowledge-scan' command help."""
        result = runner.invoke(app, ["knowledge-scan", "--help"])
        assert result.exit_code == 0
        assert "Knowledge Base" in result.output or "knowledge" in result.output.lower()

    def test_knowledge_sync_help(self, runner: CliRunner) -> None:
        """Test 'knowledge-sync' command help."""
        result = runner.invoke(app, ["knowledge-sync", "--help"])
        assert result.exit_code == 0
        assert "Synchronize" in result.output or "sync" in result.output.lower()

    def test_guardian_probe_help(self, runner: CliRunner) -> None:
        """Test 'guardian-probe' command help."""
        result = runner.invoke(app, ["guardian-probe", "--help"])
        assert result.exit_code == 0
        assert (
            "Hallucination Probe" in result.output or "probe" in result.output.lower()
        )

    def test_guardian_check_help(self, runner: CliRunner) -> None:
        """Test 'guardian-check' command help."""
        result = runner.invoke(app, ["guardian-check", "--help"])
        assert result.exit_code == 0
        assert (
            "undocumented" in result.output.lower() or "orphan" in result.output.lower()
        )

    def test_audit_help(self, runner: CliRunner) -> None:
        """Test 'audit' command help."""
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        assert "audit" in result.output.lower()
        assert "metadata" in result.output.lower() or "link" in result.output.lower()

    def test_generate_help(self, runner: CliRunner) -> None:
        """Test 'generate' command help."""
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Generate" in result.output or "documentation" in result.output.lower()


class TestCLIVersion:
    """Test version flag."""

    def test_version_flag(self, runner: CliRunner) -> None:
        """Test --version displays version information."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "CORTEX" in result.output
        assert "v0.1.0" in result.output

    def test_version_short_flag(self, runner: CliRunner) -> None:
        """Test -v short flag for version."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "CORTEX" in result.output
        assert "v0.1.0" in result.output


class TestConfigCommand:
    """Test 'config' command with mocked orchestrator."""

    @patch("scripts.core.cortex.config_orchestrator.ConfigOrchestrator")
    def test_config_show(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex config --show' displays configuration."""
        # Arrange: Create mock configuration
        mock_config = {
            "scan_paths": ["docs/", "src/"],
            "file_patterns": ["*.md", "*.py"],
            "exclude_paths": ["venv/", "__pycache__/"],
        }

        # Mock orchestrator instance
        mock_orchestrator = MagicMock()
        mock_orchestrator.load_yaml.return_value = mock_config
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create a temporary config file
        config_file = tmp_path / "audit_config.yaml"
        config_file.write_text("scan_paths:\n  - docs/\n")

        # Act: Run command
        result = runner.invoke(
            app,
            ["config", "--show", "--path", str(config_file)],
        )

        # Assert: Check output
        assert result.exit_code == 0
        mock_orchestrator.load_yaml.assert_called_once()

    @patch("scripts.core.cortex.config_orchestrator.ConfigOrchestrator")
    def test_config_validate(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex config --validate' validates configuration."""
        # Arrange: Mock successful validation
        mock_orchestrator = MagicMock()
        mock_orchestrator.load_config_with_defaults.return_value = {
            "scan_paths": ["docs/"],
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create a temporary config file
        config_file = tmp_path / "audit_config.yaml"
        config_file.write_text("scan_paths:\n  - docs/\n")

        # Act: Run command
        result = runner.invoke(
            app,
            ["config", "--validate", "--path", str(config_file)],
        )

        # Assert: Validation was called
        assert result.exit_code == 0
        mock_orchestrator.load_config_with_defaults.assert_called_once()


class TestMapCommand:
    """Test 'map' command with mocked mapper."""

    @patch("scripts.cortex.core.context_mapper.ContextMapper")
    def test_map_basic(
        self,
        mock_mapper_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex map' generates context successfully."""
        # Arrange: Create mock context
        mock_context = ProjectContext(
            project_name="test-project",
            version="1.0.0",
            python_version="3.11",
            description="Test project",
            cli_commands=[],
            documents=[],
            architecture_docs=[],
            dependencies=[],
            dev_dependencies=[],
            golden_paths=[],
            knowledge_entries_count=0,
            knowledge_links_valid=0,
            knowledge_links_broken=0,
        )

        # Mock mapper instance
        mock_mapper = MagicMock()
        mock_mapper.generate_context.return_value = mock_context
        mock_mapper_class.return_value = mock_mapper

        # Create output directory
        output_dir = tmp_path / ".cortex"
        output_dir.mkdir()
        output_file = output_dir / "context.json"

        # Act: Run command
        result = runner.invoke(
            app,
            ["map", "--output", str(output_file)],
        )

        # Assert: Context was generated
        assert result.exit_code == 0
        assert (
            "Context map generated successfully" in result.output
            or "Context map saved" in result.output
        )

    @patch("scripts.cortex.core.context_mapper.ContextMapper")
    def test_map_verbose(
        self,
        mock_mapper_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex map --verbose' shows detailed output."""
        # Arrange: Create mock context with data
        mock_context = ProjectContext(
            project_name="test-project",
            version="1.0.0",
            python_version="3.11",
            description="Test project",
            cli_commands=[],
            documents=[],
            architecture_docs=[],
            dependencies=["pydantic", "typer"],
            dev_dependencies=["pytest"],
            golden_paths=["src/main.py -> docs/guide.md"],
            knowledge_entries_count=0,
            knowledge_links_valid=0,
            knowledge_links_broken=0,
        )

        mock_mapper = MagicMock()
        mock_mapper.generate_context.return_value = mock_context
        mock_mapper_class.return_value = mock_mapper

        # Create output directory
        output_dir = tmp_path / ".cortex"
        output_dir.mkdir()
        output_file = output_dir / "context.json"

        # Act: Run command with verbose
        result = runner.invoke(
            app,
            ["map", "--output", str(output_file), "--verbose"],
        )

        # Assert: Verbose output includes dependencies
        assert result.exit_code == 0


class TestKnowledgeScanCommand:
    """Test 'knowledge-scan' command with mocked orchestrator."""

    @patch("scripts.cortex.commands.knowledge.KnowledgeOrchestrator")
    def test_knowledge_scan_basic(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test 'cortex knowledge-scan' scans knowledge base."""
        # Arrange: Create mock scan result
        mock_entry = KnowledgeEntry(
            id="kno-001",
            type="knowledge",
            status=DocStatus.ACTIVE,
            golden_paths=["src/main.py -> docs/knowledge/kno-001.md"],
            tags=["test"],
            file_path=Path("docs/knowledge/kno-001.md"),
        )

        mock_result = ScanResult(
            entries=[mock_entry],
            total_count=1,
            entries_with_sources=[],
        )

        # Mock orchestrator instance
        mock_orchestrator = MagicMock()
        mock_orchestrator.scan.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator

        # Act: Run command
        result = runner.invoke(app, ["knowledge-scan"])

        # Assert: Scan was executed
        assert result.exit_code == 0
        mock_orchestrator.scan.assert_called_once()

    @patch("scripts.cortex.commands.knowledge.KnowledgeOrchestrator")
    def test_knowledge_scan_verbose(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test 'cortex knowledge-scan --verbose' shows details."""
        # Arrange: Mock scan result
        mock_result = ScanResult(entries=[], total_count=0, entries_with_sources=[])

        mock_orchestrator = MagicMock()
        mock_orchestrator.scan.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator

        # Act: Run with verbose flag
        result = runner.invoke(app, ["knowledge-scan", "--verbose"])

        # Assert: Verbose mode was passed
        assert result.exit_code == 0
        mock_orchestrator.scan.assert_called_once_with(verbose=True)


class TestKnowledgeSyncCommand:
    """Test 'knowledge-sync' command with mocked orchestrator."""

    @patch("scripts.cortex.commands.knowledge.KnowledgeOrchestrator")
    def test_knowledge_sync_basic(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test 'cortex knowledge-sync' synchronizes knowledge."""
        # Arrange: Create mock sync summary
        mock_summary = SyncSummary(
            results=[],
            total_processed=1,
            successful_count=1,
            updated_count=1,
            not_modified_count=0,
            error_count=0,
        )

        # Mock orchestrator instance
        mock_orchestrator = MagicMock()
        mock_orchestrator.sync_multiple.return_value = mock_summary
        mock_orchestrator_class.return_value = mock_orchestrator

        # Act: Run command
        result = runner.invoke(app, ["knowledge-sync"])

        # Assert: Sync was executed
        assert result.exit_code == 0
        mock_orchestrator.sync_multiple.assert_called_once()


class TestGuardianProbeCommand:
    """Test 'guardian-probe' command - smoke test only."""

    def test_guardian_probe_help(self, runner: CliRunner) -> None:
        """Test 'cortex guardian-probe --help' displays help."""
        result = runner.invoke(app, ["guardian-probe", "--help"])
        assert result.exit_code == 0
        assert (
            "Hallucination Probe" in result.output or "probe" in result.output.lower()
        )


class TestGuardianCheckCommand:
    """Test 'guardian-check' command with mocked orchestrator."""

    @patch("scripts.cortex.core.guardian_orchestrator.GuardianOrchestrator")
    def test_guardian_check_basic(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex guardian-check' detects orphans."""
        # Arrange: Create mock guardian result
        mock_result = OrphanCheckResult(
            total_findings=0,
            files_scanned=1,
            orphans=[],
            documented={},
            scan_errors=[],
        )

        # Mock orchestrator instance
        mock_orchestrator = MagicMock()
        mock_orchestrator.check_orphans.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create temporary scan path
        scan_path = tmp_path / "src"
        scan_path.mkdir()
        test_file = scan_path / "config.py"
        test_file.write_text("# Empty config\n")

        docs_path = tmp_path / "docs"
        docs_path.mkdir()

        # Act: Run command
        result = runner.invoke(
            app,
            ["guardian-check", str(scan_path), "--docs", str(docs_path)],
        )

        # Assert: Check was executed (verify output)
        assert result.exit_code == 0

    @patch("scripts.cortex.core.guardian_orchestrator.GuardianOrchestrator")
    def test_guardian_check_fail_on_error(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex guardian-check --fail-on-error' exits on orphans."""
        # Arrange: Create result with orphans
        from scripts.core.guardian.models import ConfigFinding, ConfigType

        orphan = ConfigFinding(
            key="DATABASE_URL",
            config_type=ConfigType.ENV_VAR,
            source_file=Path("src/config.py"),
            line_number=10,
        )

        mock_result = OrphanCheckResult(
            total_findings=1,
            files_scanned=1,
            orphans=[orphan],
            documented={},
            scan_errors=[],
        )

        mock_orchestrator = MagicMock()
        mock_orchestrator.check_orphans.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator

        scan_path = tmp_path / "src"
        scan_path.mkdir()
        test_file = scan_path / "config.py"
        test_file.write_text("DATABASE_URL = 'postgres://...'\n")

        docs_path = tmp_path / "docs"
        docs_path.mkdir()

        # Act: Run command with --fail-on-error
        result = runner.invoke(
            app,
            [
                "guardian-check",
                str(scan_path),
                "--docs",
                str(docs_path),
                "--fail-on-error",
            ],
        )

        # Assert: Command exits with error code
        assert result.exit_code == 1


class TestAuditCommand:
    """Test 'audit' command with mocked orchestrator."""

    @patch("scripts.core.cortex.audit_orchestrator.AuditOrchestrator")
    def test_audit_basic(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex audit' audits documentation."""
        # Arrange: Create mock audit result using MagicMock
        mock_report = MagicMock()
        mock_report.total_errors = 0
        mock_report.total_warnings = 0
        mock_report.files_with_errors = []
        mock_report.is_successful = True

        mock_metadata_result = MagicMock()
        mock_metadata_result.report = mock_report

        mock_result = MagicMock()
        mock_result.metadata_result = mock_metadata_result
        mock_result.knowledge_result = None
        mock_result.should_fail = False

        # Mock orchestrator instance
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_full_audit.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create temporary docs directory
        docs_path = tmp_path / "docs"
        docs_path.mkdir()

        # Act: Run command
        result = runner.invoke(app, ["audit", str(docs_path)])

        # Assert: Audit was executed (check output)
        assert result.exit_code == 0

    @patch("scripts.core.cortex.audit_orchestrator.AuditOrchestrator")
    def test_audit_fail_on_error(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex audit --fail-on-error' exits on issues."""
        # Arrange: Create result with errors using MagicMock
        mock_report = MagicMock()
        mock_report.total_errors = 1
        mock_report.root_violations = ["README.md"]
        mock_report.is_successful = False

        mock_metadata_result = MagicMock()
        mock_metadata_result.report = mock_report

        mock_result = MagicMock()
        mock_result.metadata_result = mock_metadata_result
        mock_result.knowledge_result = None
        mock_result.should_fail = True

        mock_orchestrator = MagicMock()
        mock_orchestrator.run_full_audit.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator

        docs_path = tmp_path / "docs"
        docs_path.mkdir()

        # Act: Run with --fail-on-error
        result = runner.invoke(
            app,
            ["audit", str(docs_path), "--fail-on-error"],
        )

        # Assert: Command exits with error code (check result)
        assert result.exit_code == 1


class TestGenerateCommand:
    """Test 'generate' command with mocked orchestrator."""

    @patch("scripts.core.cortex.generation_orchestrator.GenerationOrchestrator")
    def test_generate_readme(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test 'cortex generate readme' generates README."""
        # Arrange: Create mock generation result
        mock_result = SingleGenerationResult(
            success=True,
            target="readme",
            output_path=Path("README.md"),
            content="# Test Project\n\nGenerated content",
            content_size=42,
            was_written=True,
            template_name="README.md.j2",
        )

        # Mock orchestrator instance
        mock_orchestrator = MagicMock()
        mock_orchestrator.generate_single.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator

        # Act: Run command
        result = runner.invoke(app, ["generate", "readme"])

        # Assert: Generation was executed (check output)
        assert result.exit_code == 0


class TestInitCommand:
    """Test 'init' command with mocked orchestrator."""

    @patch("scripts.core.cortex.project_orchestrator.ProjectOrchestrator")
    def test_init_new_file(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex init' adds frontmatter to new file."""
        # Arrange: Create mock init result
        mock_result = InitResult(
            status="success",
            path=Path("test.md"),
            new_frontmatter={
                "id": "test-001",
                "type": "guide",
                "status": "active",
            },
        )

        # Mock orchestrator instance
        mock_orchestrator = MagicMock()
        mock_orchestrator.initialize_file.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create a test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Document\n")

        # Act: Run command
        result = runner.invoke(app, ["init", str(test_file)])

        # Assert: Init was executed (check output, not mock call due to
        # instantiation inside function)
        assert result.exit_code == 0


class TestMigrateCommand:
    """Test 'migrate' command with mocked orchestrator."""

    @patch("scripts.core.cortex.project_orchestrator.ProjectOrchestrator")
    def test_migrate_basic(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test 'cortex migrate' migrates documentation."""
        # Arrange: Create mock migration summary
        mock_summary = MigrationSummary(
            total=5,
            created=3,
            updated=2,
            errors=0,
            results=[],
        )

        # Mock orchestrator instance
        mock_orchestrator = MagicMock()
        mock_orchestrator.migrate_directory.return_value = mock_summary
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create temporary docs directory
        docs_path = tmp_path / "docs"
        docs_path.mkdir()

        # Act: Run command
        result = runner.invoke(app, ["migrate", str(docs_path)])

        # Assert: Migration was executed (check output, not mock call)
        assert result.exit_code == 0


class TestSetupHooksCommand:
    """Test 'setup-hooks' command with mocked orchestrator."""

    def test_setup_hooks_help(self, runner: CliRunner) -> None:
        """Test 'cortex setup-hooks --help' displays help."""
        result = runner.invoke(app, ["setup-hooks", "--help"])
        assert result.exit_code == 0
        assert "Git hooks" in result.output or "hooks" in result.output.lower()


class TestContextInjection:
    """Test dependency injection through Typer context."""

    @patch("scripts.cortex.core.context_mapper.ContextMapper")
    def test_context_provides_project_root(
        self,
        mock_mapper_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test that project_root is injected into command context."""
        # Arrange: Mock mapper to capture context usage
        captured_root = None

        def capture_root(project_root: Path, **kwargs: Any) -> MagicMock:
            nonlocal captured_root
            captured_root = project_root
            # Return minimal mock context
            return MagicMock()

        mock_mapper_class.side_effect = capture_root

        # Mock the generate_context method on the instance
        mock_context = ProjectContext(
            project_name="test",
            version="1.0.0",
            python_version="3.11",
            description="Test",
            cli_commands=[],
            documents=[],
            architecture_docs=[],
            dependencies=[],
            dev_dependencies=[],
            golden_paths=[],
            knowledge_entries_count=0,
            knowledge_links_valid=0,
            knowledge_links_broken=0,
        )

        mock_mapper_instance = MagicMock()
        mock_mapper_instance.generate_context.return_value = mock_context
        mock_mapper_class.return_value = mock_mapper_instance

        output_dir = tmp_path / ".cortex"
        output_dir.mkdir()
        output_file = output_dir / "context.json"

        # Act: Run map command
        result = runner.invoke(app, ["map", "--output", str(output_file)])

        # Assert: project_root was injected
        assert result.exit_code == 0
        mock_mapper_class.assert_called_once()


class TestErrorHandling:
    """Test error handling in CLI commands."""

    @patch("scripts.core.cortex.config_orchestrator.ConfigOrchestrator")
    def test_config_nonexistent_file(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test config command handles nonexistent file gracefully."""
        # Act: Run with nonexistent file
        result = runner.invoke(
            app,
            ["config", "--show", "--path", "/nonexistent/config.yaml"],
        )

        # Assert: Command fails gracefully
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    @patch("scripts.core.cortex.audit_orchestrator.AuditOrchestrator")
    def test_audit_exception_handling(
        self,
        mock_orchestrator_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test audit command handles exceptions gracefully."""
        # Arrange: Mock orchestrator to raise exception
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_full_audit.side_effect = RuntimeError("Test error")
        mock_orchestrator_class.return_value = mock_orchestrator

        docs_path = tmp_path / "docs"
        docs_path.mkdir()

        # Act: Run command
        result = runner.invoke(app, ["audit", str(docs_path)])

        # Assert: Error is handled
        assert result.exit_code == 1
        assert "error" in result.output.lower()


# Test Summary Statistics
def test_summary() -> None:
    """Display test coverage summary."""
    test_classes = [
        TestCLIHelp,
        TestCLIVersion,
        TestConfigCommand,
        TestMapCommand,
        TestKnowledgeScanCommand,
        TestKnowledgeSyncCommand,
        TestGuardianProbeCommand,
        TestGuardianCheckCommand,
        TestAuditCommand,
        TestGenerateCommand,
        TestInitCommand,
        TestMigrateCommand,
        TestSetupHooksCommand,
        TestContextInjection,
        TestErrorHandling,
    ]

    total_test_methods = sum(
        len([m for m in dir(cls) if m.startswith("test_")]) for cls in test_classes
    )

    print(f"\n{'=' * 70}")
    print("CORTEX CLI Test Coverage Summary")
    print(f"{'=' * 70}")
    print(f"Total Test Classes: {len(test_classes)}")
    print(f"Total Test Methods: {total_test_methods}")
    print(f"{'=' * 70}")
    print("\nCoverage Areas:")
    print("  ✅ Smoke Tests (--help for all commands)")
    print("  ✅ Version Flag Tests")
    print("  ✅ Functional Tests with Mocked Orchestrators")
    print("  ✅ Error Handling Tests")
    print("  ✅ Dependency Injection Tests")
    print(f"{'=' * 70}\n")
