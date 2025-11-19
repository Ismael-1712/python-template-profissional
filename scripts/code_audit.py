#!/usr/bin/env python3
"""Pre-commit Code Security and Quality Auditor.

A DevOps-grade auditing tool that performs static analysis to detect
security vulnerabilities, external dependencies, and CI/CD risks before commits.

Usage:
    python scripts/code_audit.py [--config CONFIG_FILE] [--output FORMAT] [--fix]
    python scripts/code_audit.py [FILE1_PATH] [FILE2_PATH] ...

Author: DevOps Engineering Team
License: MIT
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Import models from the audit package (relative import)
from audit.analyzer import CodeAnalyzer
from audit.config import load_config
from audit.models import AuditResult, SecurityPattern
from audit.scanner import scan_workspace

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("audit.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


class CodeAuditor:
    """Enterprise-grade code auditor for Python projects.

    Performs static analysis to detect security vulnerabilities,
    external dependencies, and potential CI/CD issues.
    """

    def __init__(self, workspace_root: Path, config_path: Path | None = None) -> None:
        """Inicializa a instância."""
        self.workspace_root = workspace_root.resolve()
        self.config = self._load_config(config_path)
        self.findings: list[AuditResult] = []
        self.patterns = self._load_security_patterns()

        # Initialize analyzer with loaded patterns and config
        self.analyzer = CodeAnalyzer(
            patterns=self.patterns,
            workspace_root=self.workspace_root,
            max_findings_per_file=self.config["max_findings_per_file"],
        )

        logger.info("Initialized auditor for workspace: %s", self.workspace_root)

    def _load_config(self, config_path: Path | None) -> dict[str, Any]:
        """Load configuration from YAML file with fallback defaults."""
        return load_config(config_path)

    def _load_security_patterns(self) -> list[SecurityPattern]:
        """Load security patterns to detect in code."""
        return [
            # Subprocess security risks
            SecurityPattern(
                "subprocess.run(",
                "HIGH",
                (
                    "Subprocess execution detected - ensure shell=False "
                    "and validate inputs"
                ),
                "subprocess",
            ),
            SecurityPattern(
                "subprocess.call(",
                "HIGH",
                ("Subprocess call detected - ensure shell=False and validate inputs"),
                "subprocess",
            ),
            SecurityPattern(
                "os.system(",
                "CRITICAL",
                "os.system() is dangerous - use subprocess with shell=False instead",
                "subprocess",
            ),
            SecurityPattern(
                "shell=True",
                "CRITICAL",
                "shell=True is a security risk - use shell=False with list arguments",
                "subprocess",
            ),
            # Network requests without mocking
            SecurityPattern(
                "requests.get(",
                "MEDIUM",
                "HTTP request detected - ensure proper mocking in tests",
                "network",
            ),
            SecurityPattern(
                "requests.post(",
                "MEDIUM",
                "HTTP request detected - ensure proper mocking in tests",
                "network",
            ),
            SecurityPattern(
                "httpx.get(",
                "MEDIUM",
                "HTTP request detected - ensure proper mocking in tests",
                "network",
            ),
            SecurityPattern(
                "urllib.request",
                "MEDIUM",
                "URL request detected - ensure proper mocking in tests",
                "network",
            ),
            # File system operations
            SecurityPattern(
                "open(",
                "LOW",
                "File operation detected - ensure proper error handling and encoding",
                "filesystem",
            ),
            # External service dependencies
            SecurityPattern(
                "socket.connect",
                "HIGH",
                "Socket connection detected - ensure proper mocking in tests",
                "network",
            ),
        ]

    def _get_python_files(self) -> list[Path]:
        """Get all Python files to audit based on configuration."""
        return scan_workspace(
            workspace_root=self.workspace_root,
            scan_paths=self.config["scan_paths"],
            file_patterns=self.config["file_patterns"],
            exclude_paths=self.config["exclude_paths"],
        )

    def _analyze_file(self, file_path: Path) -> list[AuditResult]:
        """Analyze a single Python file for security patterns.

        This is a wrapper method that delegates to CodeAnalyzer.analyze_file().
        """
        return self.analyzer.analyze_file(file_path)

    def _check_mock_coverage(self) -> dict[str, Any]:
        """Analyze test files for proper mocking of external dependencies."""
        test_files = []
        for scan_path in self.config["scan_paths"]:
            if "test" in scan_path.lower():
                test_dir = self.workspace_root / scan_path
                if test_dir.exists():
                    test_files.extend(test_dir.rglob("test_*.py"))
                    test_files.extend(test_dir.rglob("*_test.py"))

        mock_coverage = {
            "total_test_files": len(test_files),
            "files_with_mocks": 0,
            "files_needing_mocks": [],
        }

        mock_indicators = [
            "@patch",
            "Mock()",
            "mocker.patch",
            "mock_",
            "pytest-httpx",
            "httpx_mock",
        ]
        external_indicators = ["requests.", "httpx.", "subprocess.", "socket."]

        for test_file in test_files:
            try:
                with open(test_file, encoding="utf-8") as f:
                    content = f.read()

                has_external = any(
                    indicator in content for indicator in external_indicators
                )
                has_mock = any(indicator in content for indicator in mock_indicators)

                if has_external and has_mock:
                    mock_coverage["files_with_mocks"] += 1
                elif has_external and not has_mock:
                    mock_coverage["files_needing_mocks"].append(
                        str(test_file.relative_to(self.workspace_root)),
                    )

            except Exception as e:
                logger.error(f"Error analyzing test file {test_file}: {e}")

        return mock_coverage

    def _simulate_ci_environment(self) -> dict[str, Any]:
        """Simulate CI environment by running critical tests."""
        logger.info("Simulating CI environment...")

        # Set CI-like environment variables
        ci_env = {
            **dict(os.environ),
            "CI": "true",
            "PYTEST_TIMEOUT": str(self.config["ci_timeout"]),
        }

        try:
            # Run pytest with CI-appropriate flags
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "--tb=short",
                "--maxfail=5",
                "--timeout=60",
                "--quiet",
                "tests/",
            ]

            result = subprocess.run(  # noqa: subprocess
                cmd,
                check=False,
                env=ci_env,
                capture_output=True,
                text=True,
                timeout=self.config["ci_timeout"],
                cwd=self.workspace_root,
            )

            return {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": "within_timeout",
            }

        except subprocess.TimeoutExpired:
            logger.error(f"CI simulation timed out after {self.config['ci_timeout']}s")
            return {
                "exit_code": -1,
                "passed": False,
                "stdout": "",
                "stderr": f"Tests exceeded {self.config['ci_timeout']}s timeout",
                "duration": "timeout",
            }
        except FileNotFoundError:
            logger.warning("pytest not found - skipping CI simulation")
            return {
                "exit_code": -2,
                "passed": None,
                "stdout": "",
                "stderr": "pytest not available",
                "duration": "skipped",
            }
        except Exception as e:
            logger.error(f"CI simulation failed: {e}")
            return {
                "exit_code": -3,
                "passed": False,
                "stdout": "",
                "stderr": str(e),
                "duration": "error",
            }

    def run_audit(self, files_to_audit: list[Path] | None = None) -> dict[str, Any]:
        """Run complete security and quality audit."""
        logger.info("Starting comprehensive code audit...")
        start_time = datetime.now(timezone.utc)

        # SE uma lista de arquivos for passada (pelo pre-commit),
        # use-a. SENÃO, faça o scan completo (comportamento antigo).
        if files_to_audit:
            logger.info(
                f"Auditing specific file list (Delta Audit): "
                f"{len(files_to_audit)} files",
            )
            python_files = files_to_audit
        else:
            logger.info("No specific files provided, scanning paths from config...")
            # Scan all Python files (Comportamento antigo)
            python_files = self._get_python_files()

        for file_path in python_files:
            file_findings = self._analyze_file(file_path)
            self.findings.extend(file_findings)

        # Check mock coverage
        mock_coverage = self._check_mock_coverage()

        # Simulate CI environment
        ci_simulation = {"passed": True, "status": "SKIPPED"}  # Padrão: Passa se pulado
        if self.config.get("simulate_ci"):
            ci_simulation = self._simulate_ci_environment()
        else:
            logger.info("Skipping CI simulation (as 'simulate_ci' is false in config).")

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Calculate severity distribution
        severity_counts = {}
        for severity in self.config["severity_levels"]:
            severity_counts[severity] = len(
                [f for f in self.findings if f.pattern.severity == severity],
            )

        # Determine overall status
        critical_issues = severity_counts.get("CRITICAL", 0)
        high_issues = severity_counts.get("HIGH", 0)
        ci_passed = ci_simulation.get("passed", False)

        overall_status = "PASS"
        if critical_issues > 0:
            overall_status = "CRITICAL"
        elif high_issues > 0 or not ci_passed:
            overall_status = "FAIL"
        elif severity_counts.get("MEDIUM", 0) > 10:
            overall_status = "WARNING"

        report = {
            "metadata": {
                "timestamp": start_time.isoformat(),
                "workspace": str(self.workspace_root),
                "duration_seconds": duration,
                "files_scanned": len(python_files),
                "auditor_version": "2.1.2-delta",  # Versão atualizada
            },
            "findings": [finding.to_dict() for finding in self.findings],
            "mock_coverage": mock_coverage,
            "ci_simulation": ci_simulation,
            "summary": {
                "total_findings": len(self.findings),
                "severity_distribution": severity_counts,
                "overall_status": overall_status,
                "recommendations": self._generate_recommendations(
                    severity_counts,
                    mock_coverage,
                    ci_simulation,
                ),
            },
        }

        logger.info(f"Audit completed in {duration:.2f}s - Status: {overall_status}")
        return report

    def _generate_recommendations(
        self,
        severity_counts: dict[str, int],
        mock_coverage: dict[str, Any],
        ci_simulation: dict[str, Any],
    ) -> list[str]:
        """Generate actionable recommendations based on audit results."""
        recommendations = []

        if severity_counts.get("CRITICAL", 0) > 0:
            recommendations.append(
                "🔴 CRITICAL: Fix security vulnerabilities before commit",
            )

        if severity_counts.get("HIGH", 0) > 0:
            recommendations.append("🟠 HIGH: Address high-priority security issues")

        if mock_coverage["files_needing_mocks"]:
            recommendations.append(
                f"🧪 Add mocks to {len(mock_coverage['files_needing_mocks'])} "
                "test files",
            )

        if not ci_simulation.get("passed", True):
            recommendations.append("⚠️ Fix failing tests before CI/CD pipeline")

        if not recommendations:
            recommendations.append("✅ Code quality meets security standards!")

        return recommendations


def save_report(
    report: dict[str, Any],
    output_path: Path,
    format_type: str = "json",
) -> None:
    """Save audit report in specified format."""
    if format_type.lower() == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    elif format_type.lower() == "yaml":
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(report, f, default_flow_style=False, allow_unicode=True)
    else:
        raise ValueError(f"Unsupported format: {format_type}")

    logger.info(f"Report saved to {output_path}")


def print_summary(report: dict[str, Any]) -> None:
    """Print executive summary of audit results."""
    metadata = report["metadata"]
    summary = report["summary"]

    print(f"\n{'=' * 60}")
    print("🔍 CODE SECURITY AUDIT REPORT")
    print(f"{'=' * 60}")
    print(f"📅 Timestamp: {metadata['timestamp']}")
    print(f"📁 Workspace: {metadata['workspace']}")
    print(f"⏱️  Duration: {metadata['duration_seconds']:.2f}s")
    print(f"📄 Files Scanned: {metadata['files_scanned']}")

    status = summary["overall_status"]
    status_emoji = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌", "CRITICAL": "🔴"}
    print(f"\n{status_emoji.get(status, '❓')} OVERALL STATUS: {status}")

    print("\n📊 SEVERITY DISTRIBUTION:")
    for severity, count in summary["severity_distribution"].items():
        if count > 0:
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(
                severity,
                "⚪",
            )
            print(f"  {emoji} {severity}: {count}")

    if report["findings"]:
        print("\n🔍 TOP FINDINGS:")
        for finding in report["findings"][:5]:  # Show top 5
            print(f"  • {finding['file']}:{finding['line']} - {finding['description']}")

    print("\n💡 RECOMMENDATIONS:")
    for rec in summary["recommendations"]:
        print(f"  {rec}")

    print(f"\n{'=' * 60}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enterprise code security and quality auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/code_audit.py                     # Basic audit
  python scripts/code_audit.py --output yaml       # YAML output
  python scripts/code_audit.py --config audit_yaml   # Custom config
  python scripts/code_audit.py file1.py file2.py   # Delta audit (pre-commit)
        """,
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration YAML file",
    )
    parser.add_argument(
        "--output",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        help="Custom report output path",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output",
    )
    parser.add_argument(
        "--fail-on",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default="HIGH",
        help="Exit with error on this severity level or higher",
    )

    parser.add_argument(
        "files",
        nargs="*",  # "Zero ou mais" - se nenhum for passado, a lista será vazia.
        type=Path,
        help="Optional list of files to audit (overrides config scan_paths)",
    )

    args = parser.parse_args()

    # Configure logging based on quiet flag
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    # Determine workspace root
    workspace_root = Path(__file__).parent.parent

    # Initialize auditor
    auditor = CodeAuditor(workspace_root, args.config)

    # Run audit
    report = auditor.run_audit(files_to_audit=args.files)

    # Determine output file
    if args.report_file:
        output_file = args.report_file
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = workspace_root / f"audit_report_{timestamp}.{args.output}"

    # Save report
    save_report(report, output_file, args.output)

    # Print summary unless quiet
    if not args.quiet:
        print_summary(report)

    # Determine exit code based on severity threshold
    severity_hierarchy = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    fail_threshold = severity_hierarchy[args.fail_on]

    for finding in auditor.findings:
        finding_level = severity_hierarchy.get(finding.pattern.severity, 0)
        if finding_level >= fail_threshold:
            logger.error(
                f"Audit failed due to {finding.pattern.severity} severity findings",
            )
            sys.exit(1)

    # Check CI simulation if it ran
    ci_result = report.get("ci_simulation", {})
    if ci_result.get("passed") is False:
        logger.error("Audit failed due to CI simulation failures")
        sys.exit(1)

    logger.info("Audit completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
