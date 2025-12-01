"""Testes unitários para modelos de Mock CI Integration.

Valida que as dataclasses, enums e funções de configuração funcionam
corretamente e mantêm tipagem estrita.
"""

from datetime import datetime, timezone
from pathlib import Path

from scripts.core.mock_ci.config import (
    BLOCKING_MOCK_TYPES,
    CI_ENVIRONMENT_VARS,
    COMMIT_MESSAGE_TEMPLATE,
    determine_status,
    format_commit_message,
    get_report_filename,
)
from scripts.core.mock_ci.models import (
    CIReport,
    CIStatus,
    FixResult,
    GitInfo,
    MockSuggestion,
    MockSuggestions,
    MockType,
    Severity,
)


class TestEnums:
    """Testes para os enums do sistema."""

    def test_severity_enum_values(self) -> None:
        """Testa que Severity contém os valores esperados."""
        assert Severity.HIGH.value == "HIGH"
        assert Severity.MEDIUM.value == "MEDIUM"
        assert Severity.LOW.value == "LOW"

    def test_mock_type_enum_values(self) -> None:
        """Testa alguns valores de MockType."""
        assert MockType.HTTP_REQUEST.value == "HTTP_REQUEST"
        assert MockType.SUBPROCESS.value == "SUBPROCESS"
        assert MockType.FILE_IO.value == "FILE_IO"

    def test_ci_status_enum_values(self) -> None:
        """Testa valores de CIStatus."""
        assert CIStatus.SUCCESS.value == "SUCCESS"
        assert CIStatus.WARNING.value == "WARNING"
        assert CIStatus.FAILURE.value == "FAILURE"


class TestGitInfo:
    """Testes para dataclass GitInfo."""

    def test_git_info_default_values(self) -> None:
        """Testa valores padrão de GitInfo."""
        info = GitInfo()
        assert info.is_git_repo is False
        assert info.has_changes is False
        assert info.current_branch is None
        assert info.commit_hash is None

    def test_git_info_with_values(self) -> None:
        """Testa instanciação com valores."""
        info = GitInfo(
            is_git_repo=True,
            has_changes=True,
            current_branch="main",
            commit_hash="abc123",
        )
        assert info.is_git_repo is True
        assert info.has_changes is True
        assert info.current_branch == "main"
        assert info.commit_hash == "abc123"


class TestMockSuggestion:
    """Testes para dataclass MockSuggestion."""

    def test_mock_suggestion_creation(self) -> None:
        """Testa criação de MockSuggestion."""
        suggestion = MockSuggestion(
            severity="HIGH",
            mock_type="HTTP_REQUEST",
            file_path="tests/test_api.py",
            line_number=42,
            reason="Chamada HTTP não mockada",
        )

        assert suggestion.severity == "HIGH"
        assert suggestion.mock_type == "HTTP_REQUEST"
        assert suggestion.file_path == "tests/test_api.py"
        assert suggestion.line_number == 42
        assert suggestion.reason == "Chamada HTTP não mockada"
        assert suggestion.pattern is None

    def test_mock_suggestion_enum_properties(self) -> None:
        """Testa conversão para enums."""
        suggestion = MockSuggestion(
            severity="HIGH",
            mock_type="SUBPROCESS",
            file_path="test.py",
            line_number=1,
            reason="Test",
        )

        assert suggestion.severity_enum == Severity.HIGH
        assert suggestion.mock_type_enum == MockType.SUBPROCESS


class TestMockSuggestions:
    """Testes para agregação MockSuggestions."""

    def test_mock_suggestions_creation(self) -> None:
        """Testa criação direta de MockSuggestions."""
        suggestions = MockSuggestions(
            total=10,
            high_priority=3,
            blocking=1,
            details=[],
        )

        assert suggestions.total == 10
        assert suggestions.high_priority == 3
        assert suggestions.blocking == 1
        assert len(suggestions.details) == 0

    def test_mock_suggestions_from_list(self) -> None:
        """Testa criação a partir de lista de dicts."""
        raw_suggestions = [
            {
                "severity": "HIGH",
                "mock_type": "HTTP_REQUEST",
                "file_path": "test1.py",
                "line_number": 10,
                "reason": "HTTP call",
            },
            {
                "severity": "HIGH",
                "mock_type": "SUBPROCESS",
                "file_path": "test2.py",
                "line_number": 20,
                "reason": "Subprocess call",
            },
            {
                "severity": "MEDIUM",
                "mock_type": "FILE_IO",
                "file_path": "test3.py",
                "line_number": 30,
                "reason": "File access",
            },
        ]

        suggestions = MockSuggestions.from_suggestions_list(
            raw_suggestions,
            BLOCKING_MOCK_TYPES,
        )

        assert suggestions.total == 3
        assert suggestions.high_priority == 2
        assert suggestions.blocking == 2  # HTTP_REQUEST e SUBPROCESS
        assert len(suggestions.details) == 3


class TestCIReport:
    """Testes para dataclass CIReport."""

    def test_ci_report_creation(self) -> None:
        """Testa criação de CIReport."""
        git_info = GitInfo(is_git_repo=True, current_branch="main")
        mock_suggestions = MockSuggestions(
            total=5,
            high_priority=2,
            blocking=1,
            details=[],
        )

        report = CIReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            environment="github-actions",
            workspace="/project",
            git_info=git_info,
            validation_results={"has_tests": True},
            mock_suggestions=mock_suggestions,
            summary={"files_scanned": 10},
            recommendations=["Apply mocks"],
            status="SUCCESS",
        )

        assert report.environment == "github-actions"
        assert report.git_info.current_branch == "main"
        assert report.mock_suggestions.total == 5
        assert report.status_enum == CIStatus.SUCCESS

    def test_ci_report_to_dict(self) -> None:
        """Testa serialização para dict."""
        git_info = GitInfo(is_git_repo=True)
        mock_suggestions = MockSuggestions(
            total=2,
            high_priority=1,
            blocking=0,
            details=[],
        )

        report = CIReport(
            timestamp="2025-06-01T14:30:00Z",
            environment="local",
            workspace="/project",
            git_info=git_info,
            validation_results={},
            mock_suggestions=mock_suggestions,
            summary={},
            recommendations=[],
            status="SUCCESS",
        )

        data = report.to_dict()

        assert data["timestamp"] == "2025-06-01T14:30:00Z"
        assert data["environment"] == "local"
        assert data["git_info"]["is_git_repo"] is True
        assert data["mock_suggestions"]["total"] == 2
        assert data["status"] == "SUCCESS"


class TestFixResult:
    """Testes para dataclass FixResult."""

    def test_fix_result_creation(self) -> None:
        """Testa criação de FixResult."""
        result = FixResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            validation_fixes=2,
            mock_fixes_applied=5,
            mock_fixes_details={"applied": 5},
            total_fixes=7,
            commit_created=True,
            commit_message="fix: auto-fix mocks",
        )

        assert result.validation_fixes == 2
        assert result.mock_fixes_applied == 5
        assert result.total_fixes == 7
        assert result.commit_created is True

    def test_fix_result_to_dict(self) -> None:
        """Testa serialização para dict."""
        result = FixResult(
            timestamp="2025-06-01T14:30:00Z",
            validation_fixes=1,
            mock_fixes_applied=3,
            mock_fixes_details={"details": "test"},
            total_fixes=4,
        )

        data = result.to_dict()

        assert data["validation_fixes"] == 1
        assert data["mock_fixes"]["applied"] == 3
        assert data["total_fixes"] == 4
        assert data["commit_created"] is False


class TestConfig:
    """Testes para módulo de configuração."""

    def test_ci_environment_vars_constant(self) -> None:
        """Testa que CI_ENVIRONMENT_VARS está definido."""
        assert "GITHUB_ACTIONS" in CI_ENVIRONMENT_VARS
        assert CI_ENVIRONMENT_VARS["GITHUB_ACTIONS"] == "github-actions"
        assert "GITLAB_CI" in CI_ENVIRONMENT_VARS
        assert len(CI_ENVIRONMENT_VARS) >= 7

    def test_blocking_mock_types_constant(self) -> None:
        """Testa que BLOCKING_MOCK_TYPES está definido."""
        assert "HTTP_REQUEST" in BLOCKING_MOCK_TYPES
        assert "SUBPROCESS" in BLOCKING_MOCK_TYPES
        assert len(BLOCKING_MOCK_TYPES) >= 2

    def test_commit_message_template_constant(self) -> None:
        """Testa que COMMIT_MESSAGE_TEMPLATE está definido."""
        assert "feat(tests)" in COMMIT_MESSAGE_TEMPLATE
        assert "{mock_fixes}" in COMMIT_MESSAGE_TEMPLATE
        assert "{validation_fixes}" in COMMIT_MESSAGE_TEMPLATE

    def test_format_commit_message(self) -> None:
        """Testa formatação de mensagem de commit."""
        msg = format_commit_message(mock_fixes=5, validation_fixes=2)

        assert "Applied 5 mock fixes" in msg
        assert "Fixed 2 validation issues" in msg
        assert "feat(tests)" in msg

    def test_get_report_filename(self) -> None:
        """Testa geração de nome de arquivo de relatório."""
        workspace = Path("/project")
        timestamp = "20250601_143052"

        filename = get_report_filename(workspace, timestamp)

        assert filename.parent == workspace
        assert "ci_test_mock_report" in filename.name
        assert "20250601_143052" in filename.name
        assert filename.suffix == ".json"

    def test_determine_status_success(self) -> None:
        """Testa determinação de status SUCCESS."""
        status = determine_status(
            validation_results={"test1": True, "test2": True},
            critical_count=1,
            blocking_count=0,
        )
        assert status == "SUCCESS"

    def test_determine_status_warning(self) -> None:
        """Testa determinação de status WARNING."""
        status = determine_status(
            validation_results={"test1": True, "test2": True},
            critical_count=5,  # Acima do threshold
            blocking_count=0,
        )
        assert status == "WARNING"

    def test_determine_status_failure_validation(self) -> None:
        """Testa determinação de status FAILURE (validação falhou)."""
        status = determine_status(
            validation_results={"test1": True, "test2": False},
            critical_count=0,
            blocking_count=0,
        )
        assert status == "FAILURE"

    def test_determine_status_failure_blocking(self) -> None:
        """Testa determinação de status FAILURE (issues bloqueadores)."""
        status = determine_status(
            validation_results={"test1": True, "test2": True},
            critical_count=0,
            blocking_count=2,  # Acima do threshold
        )
        assert status == "FAILURE"
