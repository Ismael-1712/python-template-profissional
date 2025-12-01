#!/usr/bin/env python3

"""Módulo Runner (Executor de Testes e Qualidade) SRE.

(Extraído do monólito P8.4).
"""

import logging
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from scripts.ci_recovery import executor
from scripts.ci_recovery.models import RecoveryStatus

# Inicializa o logger para este módulo
logger = logging.getLogger(__name__)


def run_code_quality_checks(
    log_step_callback: Callable[..., None],
    repository_path: Path,
    dry_run: bool,
) -> bool:
    """Executa checagens de qualidade de código (linting, etc.).

    (Função refatorada S.O.L.I.D. - dependências 'self' injetadas)
    """
    log_step_callback("Code Quality Checks", RecoveryStatus.IN_PROGRESS)

    checks = [
        # (Nota SRE: Atualizando para 'ruff'
        #  em vez dos obsoletos flake8/black/isort)
        (
            [sys.executable, "-m", "ruff", "format", "--check", "src/"],
            "Ruff Format Check",
        ),
        ([sys.executable, "-m", "ruff", "check", "src/"], "Ruff Linter Check"),
        ([sys.executable, "-m", "mypy", "src/"], "Type checking (MyPy)"),
    ]

    all_passed = True

    for command, check_name in checks:
        try:
            result = executor.run_command(
                command=command,
                repository_path=repository_path,
                dry_run=dry_run,
                timeout=120,
            )

            if result.returncode == 0:
                logger.info(f"✅ {check_name} passed")
            else:
                logger.warning(f"⚠️ {check_name} failed")
                all_passed = False

        except subprocess.TimeoutExpired:
            logger.error(f"❌ {check_name} timed out")
            all_passed = False
        except Exception as e:
            logger.error(f"❌ {check_name} error: {e}")
            all_passed = False

    status = RecoveryStatus.SUCCESS if all_passed else RecoveryStatus.PARTIAL_SUCCESS
    log_step_callback("Code Quality Checks", status)

    return all_passed


def run_tests(
    log_step_callback: Callable[..., None],
    repository_path: Path,
    dry_run: bool,
) -> bool:
    """Executa a suíte de testes (Pytest).

    (Função refatorada S.O.L.I.D. - dependências 'self' injetadas)
    """
    log_step_callback("Test Execution", RecoveryStatus.IN_PROGRESS)

    try:
        # Executa testes com pytest
        result = executor.run_command(
            command=[
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "-v",
                "--tb=short",
                "--maxfail=5",
                "--timeout=300",
            ],
            repository_path=repository_path,
            dry_run=dry_run,
            timeout=600,
        )

        if result.returncode == 0:
            log_step_callback(
                "Test Execution",
                RecoveryStatus.SUCCESS,
                details="All tests passed",
            )
            return True
        log_step_callback(
            "Test Execution",
            RecoveryStatus.FAILED,
            details=f"Tests failed with exit code {result.returncode}",
        )
        return False

    except subprocess.TimeoutExpired:
        log_step_callback(
            "Test Execution",
            RecoveryStatus.FAILED,
            details="Tests timed out",
        )
        return False
    except Exception as e:
        log_step_callback(
            "Test Execution",
            RecoveryStatus.FAILED,
            error_message=str(e),
        )
        return False
