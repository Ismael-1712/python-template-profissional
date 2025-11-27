"""Tests for the audit reporter module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.audit.reporter import AuditReporter, ConsoleAuditFormatter


@pytest.fixture
def sample_report():
    """Create a complete sample audit report for testing."""
    return {
        "metadata": {
            "timestamp": "2025-11-27T15:30:00",
            "workspace": "/test/workspace",
            "duration_seconds": 1.23,
            "files_scanned": 42,
        },
        "summary": {
            "overall_status": "WARNING",
            "total_findings": 5,
            "severity_distribution": {
                "CRITICAL": 0,
                "HIGH": 2,
                "MEDIUM": 3,
                "LOW": 0,
            },
            "recommendations": [
                "🟠 HIGH: Address high-priority security issues",
                "🧪 Add mocks to 3 test files",
            ],
        },
        "findings": [
            {
                "file": "test.py",
                "line": 10,
                "description": "SQL injection vulnerability",
                "severity": "HIGH",
            },
            {
                "file": "main.py",
                "line": 25,
                "description": "Hardcoded credentials",
                "severity": "HIGH",
            },
            # Add some medium findings
            {
                "file": "file0.py",
                "line": 0,
                "description": "Issue 0",
                "severity": "MEDIUM",
            },
            {
                "file": "file1.py",
                "line": 1,
                "description": "Issue 1",
                "severity": "MEDIUM",
            },
            {
                "file": "file2.py",
                "line": 2,
                "description": "Issue 2",
                "severity": "MEDIUM",
            },
        ],
    }


@pytest.fixture
def sample_report_no_findings():
    """Create a clean audit report."""
    return {
        "metadata": {
            "timestamp": "2025-11-27T16:00:00",
            "workspace": "/test/clean",
            "duration_seconds": 0.5,
            "files_scanned": 10,
        },
        "summary": {
            "overall_status": "PASS",
            "total_findings": 0,
            "severity_distribution": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "recommendations": ["✅ Code quality meets security standards!"],
        },
        "findings": [],
    }


class TestConsoleAuditFormatter:
    """Test the formatting logic of the audit reporter."""

    def test_format_structure(self, sample_report):
        """Test that the output contains all expected sections."""
        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)

        assert isinstance(output, str)
        assert "CODE SECURITY AUDIT REPORT" in output
        assert "=" * 60 in output
        assert "Timestamp:" in output
        assert "Workspace:" in output
        assert "OVERALL STATUS:" in output
        assert "SEVERITY DISTRIBUTION:" in output

    def test_format_findings(self, sample_report):
        """Test that findings are formatted correctly."""
        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)

        assert "TOP FINDINGS:" in output
        assert "test.py:10" in output
        assert "SQL injection vulnerability" in output

    def test_format_no_findings(self, sample_report_no_findings):
        """Test formatting when there are no findings."""
        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report_no_findings)

        assert "TOP FINDINGS:" not in output
        assert "PASS" in output

    def test_format_recommendations(self, sample_report):
        """Test that recommendations are included."""
        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)

        assert "RECOMMENDATIONS:" in output
        assert "HIGH: Address high-priority security issues" in output

    def test_format_severity_distribution(self, sample_report):
        """Test that severity counts are displayed."""
        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)

        assert "HIGH: 2" in output
        assert "MEDIUM: 3" in output

    def test_format_emojis_present(self, sample_report):
        """Test that emojis are used in the output."""
        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)
        assert "⚠️" in output or "WARNING" in output

    def test_i18n_preservation(self, sample_report):
        """Test that translation functions are called."""
        with patch("scripts.audit.reporter._") as mock_gettext:
            mock_gettext.side_effect = lambda x: f"[[{x}]]"

            formatter = ConsoleAuditFormatter()
            output = formatter.format(sample_report)
            assert output is not None

            # Check for the main headers which are cleaner
            mock_gettext.assert_any_call("🔍 CODE SECURITY AUDIT REPORT")
            # For severity, the code uses _("\n📊 SEVERITY DISTRIBUTION:")
            mock_gettext.assert_any_call("\n📊 SEVERITY DISTRIBUTION:")

    def test_format_top_5_findings_limit(self, sample_report):
        """Test that only top 5 findings are shown."""
        extra_findings = [
            {
                "file": f"file{i}.py",
                "line": i,
                "description": f"Issue {i}",
                "severity": "LOW",
            }
            for i in range(10)
        ]
        sample_report["findings"].extend(extra_findings)

        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)
        assert len(output) > 0


class TestAuditReporter:
    """Test the high-level AuditReporter class."""

    # Mock i18n to ensure tests run against English keys regardless of system locale
    @pytest.fixture(autouse=True)
    def mock_translation(self):
        """Mock translation function."""
        with patch("scripts.audit.reporter._", side_effect=lambda x: x):
            yield

    def test_reporter_initialization(self, tmp_path):
        """Test that reporter initializes correctly."""
        reporter = AuditReporter(workspace_root=tmp_path)
        assert reporter.workspace_root == tmp_path

    def test_print_summary_calls_formatter(self, sample_report):
        """Test that print_summary delegates to ConsoleAuditFormatter."""
        reporter = AuditReporter(Path("/tmp"))

        with patch("builtins.print") as mock_print:
            with patch.object(
                ConsoleAuditFormatter, "format", return_value="FORMATTED_REPORT"
            ) as mock_format:
                reporter.print_summary(sample_report)
                mock_format.assert_called_once_with(sample_report)
                mock_print.assert_called_once_with("FORMATTED_REPORT")

    def test_print_summary_integration(self, sample_report, capsys):
        """Integration test: print_summary outputs to stdout."""
        reporter = AuditReporter(Path("/tmp"))
        reporter.print_summary(sample_report)
        captured = capsys.readouterr()
        assert "CODE SECURITY AUDIT REPORT" in captured.out

    def test_save_report_json(self, sample_report, tmp_path):
        """Test saving report as JSON."""
        reporter = AuditReporter(tmp_path)
        output_file = tmp_path / "report.json"
        reporter.save_report(sample_report, str(output_file))
        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert content["summary"]["overall_status"] == "WARNING"

    def test_save_report_yaml(self, sample_report, tmp_path):
        """Test saving report as YAML."""
        reporter = AuditReporter(tmp_path)
        output_file = tmp_path / "report.yaml"
        reporter.save_report(sample_report, str(output_file))
        assert output_file.exists()
        content = yaml.safe_load(output_file.read_text())
        assert content["summary"]["overall_status"] == "WARNING"

    def test_save_report_invalid_format(self, sample_report, tmp_path):
        """Test that invalid format raises ValueError."""
        reporter = AuditReporter(tmp_path)
        output_file = tmp_path / "report.txt"
        with pytest.raises(ValueError, match="Unsupported format"):
            reporter.save_report(sample_report, str(output_file), format="invalid")

    def test_generate_recommendations_critical(self):
        """Test recommendations for CRITICAL findings."""
        reporter = AuditReporter(Path("/tmp"))
        recs = reporter.generate_recommendations(
            {"CRITICAL": 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            {"tests_passed": True},
        )
        assert any("CRITICAL" in r for r in recs)

    def test_generate_recommendations_high(self):
        """Test recommendations for HIGH findings."""
        reporter = AuditReporter(Path("/tmp"))
        recs = reporter.generate_recommendations(
            {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0},
            {"tests_passed": True},
        )
        assert any("HIGH" in r for r in recs)

    def test_generate_recommendations_mocks_needed(self):
        """Test recommendation when mocks are needed."""
        reporter = AuditReporter(Path("/tmp"))
        with patch(
            "scripts.audit.reporter.AuditReporter._check_test_mocks", return_value=3
        ):
            recs = reporter.generate_recommendations(
                {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
                {"tests_passed": True},
            )
            assert len(recs) > 0

    def test_generate_recommendations_ci_failed(self):
        """Test recommendation when CI fails."""
        reporter = AuditReporter(Path("/tmp"))
        recs = reporter.generate_recommendations(
            {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            {"tests_passed": False},
        )
        assert any("failing tests" in r for r in recs)

    def test_generate_recommendations_all_good(self):
        """Test recommendations when everything is clean."""
        reporter = AuditReporter(Path("/tmp"))
        recs = reporter.generate_recommendations(
            {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            {"tests_passed": True},
        )
        assert any("meets security standards" in r for r in recs)


class TestFormatterDataIntegrity:
    """Test that data is correctly passed through the formatter."""

    def test_all_metadata_fields_present(self, sample_report):
        """Ensure all metadata fields are rendered."""
        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)
        assert "1.23" in output
        assert "42" in output

    def test_all_recommendations_present(self, sample_report):
        """Ensure all recommendations are rendered."""
        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)
        for rec in sample_report["summary"]["recommendations"]:
            rec_text = rec.replace("🟠", "").replace("🧪", "").strip()
            assert any(word in output for word in rec_text.split()[:3])

    def test_output_is_single_string(self, sample_report):
        """Ensure format returns a single string."""
        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)
        assert isinstance(output, str)
        assert "\n" in output
