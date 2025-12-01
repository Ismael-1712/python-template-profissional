#!/usr/bin/env python3

"""SRE Risk Analysis Module.

(Extracted from P8.3 monolith).
"""

import logging
from collections.abc import Callable
from pathlib import Path

from scripts.ci_recovery import executor
from scripts.ci_recovery.models import (
    FileRiskAnalysis,
    RecoveryReport,
    RecoveryStatus,
    RiskLevel,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)


def _assess_file_risk(file_path: str) -> RiskLevel:
    """Assess the CI failure risk of a single file.

    (Pure function extracted from monolith)

    Args:
        file_path: Path to the file

    Returns:
        Risk level for the file

    """
    file_path_lower = file_path.lower()

    # Arquivos de risco crítico
    critical_patterns = [
        "dockerfile",
        "docker-compose",
        ".github/workflows",
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "makefile",
        ".gitignore",
    ]

    if any(pattern in file_path_lower for pattern in critical_patterns):
        return RiskLevel.CRITICAL

    # Arquivos de alto risco
    high_risk_patterns = [
        "test_",
        "_test.py",
        "/tests/",
        "conftest.py",
        "tox.ini",
        ".pre-commit",
        "pytest.ini",
    ]

    if any(pattern in file_path_lower for pattern in high_risk_patterns):
        return RiskLevel.HIGH

    # Arquivos de risco médio
    medium_risk_patterns = [
        "src/",
        "lib/",
        "__init__.py",
        "config",
        "settings",
    ]

    if any(pattern in file_path_lower for pattern in medium_risk_patterns):
        return RiskLevel.MEDIUM

    # The rest is low risk
    return RiskLevel.LOW


def analyze_changed_files(
    report: RecoveryReport,
    log_step_callback: Callable[..., None],
    commit_hash: str,
    repository_path: Path,
    dry_run: bool,
) -> FileRiskAnalysis:
    """Analyze changed files in commit for CI failure risk.

    (S.O.L.I.D. refactored function - 'self' dependencies injected)
    """
    log_step_callback("File Risk Analysis", RecoveryStatus.IN_PROGRESS)

    try:
        # Obtém arquivos alterados
        result = executor.run_command(
            command=[
                "git",
                "show",
                "--name-only",
                "--format=",
                commit_hash,
            ],
            repository_path=repository_path,
            dry_run=dry_run,
        )

        if result.returncode != 0:
            log_step_callback(
                "File Risk Analysis",
                RecoveryStatus.FAILED,
                error_message="Failed to get changed files",
            )
            return FileRiskAnalysis()

        changed_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
        analysis = FileRiskAnalysis()

        for file_path in changed_files:
            risk = _assess_file_risk(file_path)  # Calls local function

            if risk == RiskLevel.CRITICAL:
                analysis.critical_risk.append(file_path)
            elif risk == RiskLevel.HIGH:
                analysis.high_risk.append(file_path)
            elif risk == RiskLevel.MEDIUM:
                analysis.medium_risk.append(file_path)
            else:
                analysis.low_risk.append(file_path)

        # Determina o risco geral
        if analysis.critical_risk:
            analysis.overall_risk = RiskLevel.CRITICAL
        elif analysis.high_risk:
            analysis.overall_risk = RiskLevel.HIGH
        elif analysis.medium_risk:
            analysis.overall_risk = RiskLevel.MEDIUM
        else:
            analysis.overall_risk = RiskLevel.LOW

        report.file_analysis = analysis  # Mutates 'report' object

        log_step_callback(
            "File Risk Analysis",
            RecoveryStatus.SUCCESS,
            details=(
                f"Analyzed {len(changed_files)} files - "
                f"Overall risk: {analysis.overall_risk.value}"
            ),
        )

        return analysis

    except Exception as e:
        log_step_callback(
            "File Risk Analysis",
            RecoveryStatus.FAILED,
            error_message=str(e),
        )
        return FileRiskAnalysis()
