"""Unit Tests for Code Analysis Engine.

This test module provides comprehensive coverage for the CodeAnalyzer class,
focusing on security pattern detection, suppression handling, and configuration
respect.

Test Coverage:
    - Positive Detection: Unsafe patterns are correctly identified
    - Negative Detection: Safe code is not flagged
    - Suppression Logic: noqa comments work correctly
    - Configuration: max_findings_per_file is respected
    - Edge Cases: Syntax errors, string literals, comments

Author: DevOps Engineering Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from scripts.audit.analyzer import CodeAnalyzer
from scripts.audit.models import SecurityPattern, SecuritySeverity


@pytest.fixture
def workspace_root() -> Path:
    """Fixture providing fake workspace root path."""
    return Path("/fake/workspace")


@pytest.fixture
def security_patterns() -> list[SecurityPattern]:
    """Fixture providing common security patterns for testing."""
    return [
        SecurityPattern(
            pattern="shell=True",
            severity=SecuritySeverity.CRITICAL,
            description="Shell injection vulnerability",
            category="subprocess",
        ),
        SecurityPattern(
            pattern="os.system(",
            severity=SecuritySeverity.HIGH,
            description="Unsafe system command execution",
            category="subprocess",
        ),
        SecurityPattern(
            pattern="requests.get(",
            severity=SecuritySeverity.MEDIUM,
            description="Network request without mocking",
            category="network",
        ),
    ]


@pytest.fixture
def analyzer(
    security_patterns: list[SecurityPattern],
    workspace_root: Path,
) -> CodeAnalyzer:
    """Fixture providing configured CodeAnalyzer instance."""
    return CodeAnalyzer(
        patterns=security_patterns,
        workspace_root=workspace_root,
        max_findings_per_file=50,
    )


def test_detect_unsafe_subprocess_shell_true(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test positive detection: subprocess.run with shell=True is flagged."""
    unsafe_code = """\
import subprocess

def deploy():
    # CRITICAL: This is vulnerable to shell injection
    subprocess.run("rm -rf /tmp/*", shell=True)
    return True
"""

    mock_file_path = workspace_root / "unsafe_deploy.py"

    with patch("pathlib.Path.open", mock_open(read_data=unsafe_code)):
        findings = analyzer.analyze_file(mock_file_path)

    # Should detect exactly one CRITICAL finding
    assert len(findings) == 1

    finding = findings[0]
    assert finding.pattern.severity == "CRITICAL"
    assert finding.pattern.category == "subprocess"
    assert finding.line_number == 5
    assert "shell=True" in finding.code_snippet
    assert finding.suggestion is not None
    assert "shell=False" in finding.suggestion


def test_detect_multiple_unsafe_patterns(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test detection of multiple different unsafe patterns in one file."""
    unsafe_code = """\
import subprocess
import os
import requests

def bad_operations():
    os.system("echo test")  # HIGH severity
    subprocess.run("ls", shell=True)  # CRITICAL severity
    requests.get("http://api.example.com")  # MEDIUM severity
"""

    mock_file_path = workspace_root / "multiple_issues.py"

    with patch("pathlib.Path.open", mock_open(read_data=unsafe_code)):
        findings = analyzer.analyze_file(mock_file_path)

    # Should detect all three issues
    assert len(findings) == 3

    # Verify severities
    severities = {f.pattern.severity for f in findings}
    assert severities == {"HIGH", "CRITICAL", "MEDIUM"}

    # Verify line numbers are different
    line_numbers = [f.line_number for f in findings]
    assert len(line_numbers) == len(set(line_numbers))


def test_ignore_safe_code(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test negative detection: Safe code is not flagged."""
    safe_code = """\
import subprocess

def safe_deploy():
    # This is safe: shell=False is the default
    subprocess.run(["ls", "-la"], check=True)

    # This is safe: shell explicitly False
    subprocess.run(["echo", "hello"], shell=False)

    return True
"""

    mock_file_path = workspace_root / "safe_deploy.py"

    with patch("pathlib.Path.open", mock_open(read_data=safe_code)):
        findings = analyzer.analyze_file(mock_file_path)

    # Should not detect any issues in safe code
    assert len(findings) == 0


def test_suppression_with_noqa_subprocess(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test suppression logic: noqa:subprocess suppresses subprocess warnings."""
    suppressed_code = """\
import subprocess

def legacy_deploy():
    # This is suppressed - legacy code with documented risk
    subprocess.run("legacy-command", shell=True)  # noqa: subprocess

    # This should still be detected (not suppressed)
    subprocess.run("another-command", shell=True)
"""

    mock_file_path = workspace_root / "suppressed.py"

    with patch("pathlib.Path.open", mock_open(read_data=suppressed_code)):
        findings = analyzer.analyze_file(mock_file_path)

    # Should detect only the non-suppressed violation
    assert len(findings) == 1
    assert findings[0].line_number == 8
    assert "noqa" not in findings[0].code_snippet


def test_suppression_with_noqa_multiple_categories(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test suppression with multiple categories: noqa:subprocess,network."""
    suppressed_code = """\
import subprocess
import requests

def multi_suppressed():
    subprocess.run("cmd", shell=True)  # noqa: subprocess,network
    requests.get("http://example.com")  # noqa: network
"""

    mock_file_path = workspace_root / "multi_suppressed.py"

    with patch("pathlib.Path.open", mock_open(read_data=suppressed_code)):
        findings = analyzer.analyze_file(mock_file_path)

    # Both should be suppressed
    assert len(findings) == 0


def test_suppression_case_insensitive(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that suppression is case-insensitive."""
    suppressed_code = """\
import subprocess

def case_test():
    subprocess.run("cmd", shell=True)  # noqa: SUBPROCESS
    subprocess.run("cmd", shell=True)  # noqa: SubProcess
"""

    mock_file_path = workspace_root / "case_suppressed.py"

    with patch("pathlib.Path.open", mock_open(read_data=suppressed_code)):
        findings = analyzer.analyze_file(mock_file_path)

    # Both should be suppressed regardless of case
    assert len(findings) == 0


def test_max_findings_per_file_respected(
    security_patterns: list[SecurityPattern],
    workspace_root: Path,
) -> None:
    """Test configuration: max_findings_per_file limit is enforced."""
    # Create analyzer with low limit
    limited_analyzer = CodeAnalyzer(
        patterns=security_patterns,
        workspace_root=workspace_root,
        max_findings_per_file=3,
    )

    # Code with many violations
    many_violations = "\n".join(
        [
            "import subprocess",
            *[f"subprocess.run('cmd{i}', shell=True)" for i in range(10)],
        ],
    )

    mock_file_path = workspace_root / "many_issues.py"

    with patch("pathlib.Path.open", mock_open(read_data=many_violations)):
        findings = limited_analyzer.analyze_file(mock_file_path)

    # Should stop at max_findings_per_file
    assert len(findings) == 3


def test_ignore_patterns_in_comments(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that patterns in comments are ignored."""
    code_with_comments = """\
import subprocess

def documented():
    # Don't use shell=True - it's dangerous!
    # Example of bad code: subprocess.run("cmd", shell=True)

    # This is the actual violation
    subprocess.run("real-cmd", shell=True)
"""

    mock_file_path = workspace_root / "commented.py"

    with patch("pathlib.Path.open", mock_open(read_data=code_with_comments)):
        findings = analyzer.analyze_file(mock_file_path)

    # Should detect only the actual code, not comments
    assert len(findings) == 1
    assert findings[0].line_number == 8


def test_ignore_patterns_in_string_literals(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that patterns inside string literals are ignored."""
    code_with_strings = """\
import subprocess

def with_strings():
    help_text = "Don't use shell=True in production"
    example = 'subprocess.run("cmd", shell=True)'

    # This is the actual violation (not in string)
    subprocess.run("real-cmd", shell=True)
"""

    mock_file_path = workspace_root / "strings.py"

    with patch("pathlib.Path.open", mock_open(read_data=code_with_strings)):
        findings = analyzer.analyze_file(mock_file_path)

    # Should detect only the actual code, not string literals
    assert len(findings) == 1
    assert findings[0].line_number == 8


def test_syntax_error_returns_empty_list(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that files with syntax errors return empty findings list."""
    invalid_code = """\
import subprocess

def broken(:  # Syntax error
    subprocess.run("cmd", shell=True)
"""

    mock_file_path = workspace_root / "broken.py"

    with patch("pathlib.Path.open", mock_open(read_data=invalid_code)):
        findings = analyzer.analyze_file(mock_file_path)

    # Should return empty list for syntax errors
    assert len(findings) == 0


def test_file_read_error_returns_empty_list(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that file read errors return empty findings list."""
    mock_file_path = workspace_root / "unreadable.py"

    with patch("pathlib.Path.open", side_effect=OSError("Permission denied")):
        findings = analyzer.analyze_file(mock_file_path)

    # Should return empty list for read errors
    assert len(findings) == 0


def test_unicode_decode_error_returns_empty_list(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that Unicode decode errors return empty findings list."""
    mock_file_path = workspace_root / "binary.py"

    with patch(
        "pathlib.Path.open",
        side_effect=UnicodeDecodeError(
            "utf-8",
            b"\x80\x81",
            0,
            1,
            "invalid start byte",
        ),
    ):
        findings = analyzer.analyze_file(mock_file_path)

    # Should return empty list for decode errors
    assert len(findings) == 0


def test_relative_path_conversion(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that file paths are converted to relative paths."""
    unsafe_code = 'subprocess.run("cmd", shell=True)'

    # Absolute path within workspace
    mock_file_path = workspace_root / "src" / "module.py"

    with patch("pathlib.Path.open", mock_open(read_data=unsafe_code)):
        findings = analyzer.analyze_file(mock_file_path)

    assert len(findings) == 1

    # Path should be relative to workspace root
    finding_path = findings[0].file_path
    path_str = str(finding_path)
    assert not path_str.startswith("/fake/workspace")


def test_suggestion_generation_for_shell_true(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that appropriate suggestions are generated for shell=True."""
    unsafe_code = 'subprocess.run("cmd", shell=True)'
    mock_file_path = workspace_root / "test.py"

    with patch("pathlib.Path.open", mock_open(read_data=unsafe_code)):
        findings = analyzer.analyze_file(mock_file_path)

    assert len(findings) == 1
    suggestion = findings[0].suggestion

    assert suggestion is not None
    assert "shell=False" in suggestion
    assert "list arguments" in suggestion


def test_suggestion_generation_for_os_system(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that appropriate suggestions are generated for os.system."""
    unsafe_code = 'os.system("rm -rf /tmp")'
    mock_file_path = workspace_root / "test.py"

    with patch("pathlib.Path.open", mock_open(read_data=unsafe_code)):
        findings = analyzer.analyze_file(mock_file_path)

    assert len(findings) == 1
    suggestion = findings[0].suggestion

    assert suggestion is not None
    assert "subprocess.run()" in suggestion


def test_suggestion_generation_for_requests(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that appropriate suggestions are generated for network requests."""
    unsafe_code = 'requests.get("http://example.com")'
    mock_file_path = workspace_root / "test.py"

    with patch("pathlib.Path.open", mock_open(read_data=unsafe_code)):
        findings = analyzer.analyze_file(mock_file_path)

    assert len(findings) == 1
    suggestion = findings[0].suggestion

    assert suggestion is not None
    assert "mock" in suggestion.lower()


def test_empty_file_returns_empty_list(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that empty files return no findings."""
    empty_code = ""
    mock_file_path = workspace_root / "empty.py"

    with patch("pathlib.Path.open", mock_open(read_data=empty_code)):
        findings = analyzer.analyze_file(mock_file_path)

    assert len(findings) == 0


def test_no_patterns_returns_empty_list(workspace_root: Path) -> None:
    """Test that analyzer with no patterns returns no findings."""
    analyzer_no_patterns = CodeAnalyzer(
        patterns=[],
        workspace_root=workspace_root,
        max_findings_per_file=50,
    )

    unsafe_code = 'subprocess.run("cmd", shell=True)'
    mock_file_path = workspace_root / "test.py"

    with patch("pathlib.Path.open", mock_open(read_data=unsafe_code)):
        findings = analyzer_no_patterns.analyze_file(mock_file_path)

    assert len(findings) == 0


def test_audit_result_contains_all_metadata(
    analyzer: CodeAnalyzer,
    workspace_root: Path,
) -> None:
    """Test that AuditResult contains all required metadata."""
    unsafe_code = 'subprocess.run("cmd", shell=True)'
    mock_file_path = workspace_root / "metadata_test.py"

    with patch("pathlib.Path.open", mock_open(read_data=unsafe_code)):
        findings = analyzer.analyze_file(mock_file_path)

    assert len(findings) == 1
    finding = findings[0]

    # Verify all metadata is present
    assert finding.file_path is not None
    assert isinstance(finding.line_number, int)
    assert finding.line_number > 0
    assert finding.pattern is not None
    assert isinstance(finding.code_snippet, str)
    assert len(finding.code_snippet) > 0
    assert finding.suggestion is not None
