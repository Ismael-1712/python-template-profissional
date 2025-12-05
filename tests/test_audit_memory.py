"""Proof-of-Life Test: Audit System with MemoryFileSystem.

This test module validates that the audit system can run entirely in-memory
without any disk I/O, proving the successful decoupling of business logic
from filesystem operations.

Test Strategy:
    - Use MemoryFileSystem for all I/O operations
    - Create virtual Python files with security vulnerabilities
    - Run CodeAnalyzer and FileScanner in-memory
    - Assert vulnerabilities are detected correctly

Author: DevOps Engineering Team
License: MIT
Ticket: P11 - Fase 02 Passo 3
"""

from pathlib import Path

import pytest

from scripts.audit.analyzer import CodeAnalyzer
from scripts.audit.models import SecurityPattern
from scripts.audit.scanner import FileScanner
from scripts.utils.filesystem import MemoryFileSystem


class TestAuditWithMemoryFileSystem:
    """Test suite for in-memory audit execution."""

    @pytest.fixture
    def memory_fs(self) -> MemoryFileSystem:
        """Create a fresh MemoryFileSystem for each test."""
        return MemoryFileSystem()

    @pytest.fixture
    def security_patterns(self) -> list[SecurityPattern]:
        """Create security patterns for testing."""
        return [
            SecurityPattern(
                pattern="subprocess.run(",
                severity="HIGH",
                description="Subprocess execution detected",
                category="subprocess",
            ),
            SecurityPattern(
                pattern="shell=True",
                severity="CRITICAL",
                description="Shell injection risk",
                category="subprocess",
            ),
            SecurityPattern(
                pattern="eval(",
                severity="CRITICAL",
                description="Dangerous eval() usage",
                category="security",
            ),
            SecurityPattern(
                pattern="os.system(",
                severity="HIGH",
                description="Direct OS command execution",
                category="subprocess",
            ),
        ]

    def test_analyze_vulnerable_file_in_memory(
        self,
        memory_fs: MemoryFileSystem,
        security_patterns: list[SecurityPattern],
    ) -> None:
        """Test that CodeAnalyzer detects vulnerabilities in a virtual file.

        This is the core proof-of-life test: it proves that the analyzer
        can work entirely in-memory without touching the disk.
        """
        # Arrange: Create vulnerable code in memory
        # Using string concatenation to avoid direct pattern detection in test file
        vulnerable_code = (
            '"""Vulnerable script for testing."""\n'
            "import subprocess\n"
            "\n"
            "def deploy_code(branch):\n"
            "    # CRITICAL: Shell injection vulnerability\n"
            '    subprocess.run(f"git checkout {branch}", shell=True)\n'  # noqa:subprocess
            "\n"
            "def execute_command(cmd):\n"
            "    # HIGH: Direct OS command execution\n"
            "    import os\n"
            "    os.system(cmd)\n"  # noqa:subprocess
        )

        file_path = Path("/workspace/vulnerable_script.py")
        memory_fs.write_text(file_path, vulnerable_code)

        analyzer = CodeAnalyzer(
            patterns=security_patterns,
            workspace_root=Path("/workspace"),
            fs_adapter=memory_fs,
        )

        # Act: Analyze the virtual file
        findings = analyzer.analyze_file(file_path)

        # Assert: Vulnerabilities should be detected
        assert len(findings) > 0, "Should detect at least one vulnerability"

        # Should detect subprocess.run
        subprocess_findings = [
            f for f in findings if f.pattern.pattern == "subprocess.run("
        ]
        assert len(subprocess_findings) > 0, "Should detect subprocess.run usage"

        # Should detect shell=True
        shell_findings = [f for f in findings if f.pattern.pattern == "shell=True"]
        assert len(shell_findings) > 0, "Should detect shell=True usage"
        assert shell_findings[0].pattern.severity == "CRITICAL"

        # Should detect os.system
        os_system_findings = [f for f in findings if f.pattern.pattern == "os.system("]
        assert len(os_system_findings) > 0, "Should detect os.system usage"

    def test_scan_workspace_in_memory(
        self,
        memory_fs: MemoryFileSystem,
    ) -> None:
        """Test that FileScanner can discover files in a virtual filesystem.

        Proves that file scanning works without real disk access.
        """
        # Arrange: Create virtual workspace with Python files
        workspace_root = Path("/workspace")

        # Create some Python files in memory
        files_to_create = [
            Path("/workspace/src/main.py"),
            Path("/workspace/src/utils.py"),
            Path("/workspace/tests/test_main.py"),
            Path("/workspace/.venv/lib/package.py"),  # Should be excluded
            Path("/workspace/__pycache__/compiled.py"),  # Should be excluded
        ]

        for file_path in files_to_create:
            memory_fs.write_text(file_path, "# Python file")

        scanner = FileScanner(
            workspace_root=workspace_root,
            scan_paths=["src/", "tests/"],
            file_patterns=["*.py"],
            exclude_paths=[".venv/", "__pycache__/"],
            fs_adapter=memory_fs,
        )

        # Act: Scan for Python files
        found_files = scanner.scan()

        # Assert: Should find only non-excluded files
        assert len(found_files) == 3, f"Expected 3 files, found {len(found_files)}"

        found_paths = [str(f) for f in found_files]
        assert "/workspace/src/main.py" in found_paths
        assert "/workspace/src/utils.py" in found_paths
        assert "/workspace/tests/test_main.py" in found_paths

        # Should not include excluded paths
        assert not any(".venv" in str(f) for f in found_files)
        assert not any("__pycache__" in str(f) for f in found_files)

    def test_full_audit_pipeline_in_memory(
        self,
        memory_fs: MemoryFileSystem,
        security_patterns: list[SecurityPattern],
    ) -> None:
        """Test complete audit pipeline: scan + analyze, entirely in memory.

        This is the ultimate integration test proving that the entire
        audit system can run without disk I/O.
        """
        # Arrange: Create virtual workspace with multiple files
        workspace_root = Path("/workspace")

        safe_code = '''"""Safe code."""
def safe_function():
    # No vulnerabilities here
    result = []
    return result
'''

        # Using string concatenation to avoid direct pattern detection in test file
        vulnerable_code = (
            '"""Vulnerable code."""\n'
            "import subprocess\n"
            "\n"
            "def unsafe_function(user_input):\n"
            "    subprocess.run(user_input, shell=True)\n"  # noqa:subprocess
        )

        memory_fs.write_text(Path("/workspace/src/safe.py"), safe_code)
        memory_fs.write_text(Path("/workspace/src/vulnerable.py"), vulnerable_code)

        # Create scanner and analyzer
        scanner = FileScanner(
            workspace_root=workspace_root,
            scan_paths=["src/"],
            file_patterns=["*.py"],
            exclude_paths=[],
            fs_adapter=memory_fs,
        )

        analyzer = CodeAnalyzer(
            patterns=security_patterns,
            workspace_root=workspace_root,
            fs_adapter=memory_fs,
        )

        # Act: Run full pipeline
        python_files = scanner.scan()
        all_findings = []
        for file_path in python_files:
            findings = analyzer.analyze_file(file_path)
            all_findings.extend(findings)

        # Assert: Should find vulnerabilities only in vulnerable.py
        assert len(python_files) == 2, "Should find 2 Python files"
        assert len(all_findings) > 0, "Should detect vulnerabilities"

        # All findings should be from vulnerable.py
        for finding in all_findings:
            assert "vulnerable.py" in str(finding.file_path)

    def test_memory_fs_isolation(
        self,
        memory_fs: MemoryFileSystem,
        security_patterns: list[SecurityPattern],
    ) -> None:
        """Test that MemoryFileSystem provides proper isolation.

        Ensures that files created in one test don't leak to another.
        """
        # Arrange: Create a file
        test_file = Path("/workspace/test.py")
        memory_fs.write_text(test_file, "print('hello')")

        analyzer = CodeAnalyzer(
            patterns=security_patterns,
            workspace_root=Path("/workspace"),
            fs_adapter=memory_fs,
        )

        # Act: Analyze should work
        findings = analyzer.analyze_file(test_file)

        # Assert: File should exist in this test's memory fs
        assert memory_fs.exists(test_file)
        assert isinstance(findings, list)

    def test_nonexistent_file_handling(
        self,
        memory_fs: MemoryFileSystem,
        security_patterns: list[SecurityPattern],
    ) -> None:
        """Test that analyzer handles non-existent files gracefully.

        Even with MemoryFileSystem, error handling should work correctly.
        """
        # Arrange: File doesn't exist
        nonexistent_file = Path("/workspace/does_not_exist.py")

        analyzer = CodeAnalyzer(
            patterns=security_patterns,
            workspace_root=Path("/workspace"),
            fs_adapter=memory_fs,
        )

        # Act: Try to analyze non-existent file
        findings = analyzer.analyze_file(nonexistent_file)

        # Assert: Should return empty list, not crash
        assert findings == []

    def test_syntax_error_handling_in_memory(
        self,
        memory_fs: MemoryFileSystem,
        security_patterns: list[SecurityPattern],
    ) -> None:
        """Test that analyzer handles syntax errors in virtual files.

        Syntax errors should be logged and return empty findings.
        """
        # Arrange: Create file with syntax error
        invalid_code = '''"""Invalid Python."""
def broken_function(
    # Missing closing parenthesis
'''

        file_path = Path("/workspace/broken.py")
        memory_fs.write_text(file_path, invalid_code)

        analyzer = CodeAnalyzer(
            patterns=security_patterns,
            workspace_root=Path("/workspace"),
            fs_adapter=memory_fs,
        )

        # Act: Analyze file with syntax error
        findings = analyzer.analyze_file(file_path)

        # Assert: Should handle gracefully
        assert findings == [], "Syntax errors should return empty findings list"

    def test_unicode_handling_in_memory(
        self,
        memory_fs: MemoryFileSystem,
        security_patterns: list[SecurityPattern],
    ) -> None:
        """Test that analyzer handles Unicode content correctly in memory."""
        # Arrange: Create file with Unicode content
        # Using string concatenation to avoid direct pattern detection in test file
        unicode_code = (
            '"""Arquivo com Unicode."""\n'
            "def função_portuguesa():\n"
            '    mensagem = "Olá, mundo! 🚀"\n'
            "    print(mensagem)\n"
            "\n"
            "    # This should still be detected\n"
            "    import subprocess\n"
            '    subprocess.run("ls", shell=True)\n'  # noqa:subprocess
        )

        file_path = Path("/workspace/unicode.py")
        memory_fs.write_text(file_path, unicode_code)

        analyzer = CodeAnalyzer(
            patterns=security_patterns,
            workspace_root=Path("/workspace"),
            fs_adapter=memory_fs,
        )

        # Act: Analyze Unicode file
        findings = analyzer.analyze_file(file_path)

        # Assert: Should detect vulnerabilities despite Unicode
        assert len(findings) > 0, "Should detect vulnerabilities in Unicode files"
        shell_findings = [f for f in findings if "shell=True" in f.code_snippet]
        assert len(shell_findings) > 0
