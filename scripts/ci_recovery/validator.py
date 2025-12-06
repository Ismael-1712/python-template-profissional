#!/usr/bin/env python3

"""Módulo Validator (Validação de Estado SRE/Git).

(Extraído do monólito P8.6)
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from scripts.ci_recovery import executor

# Inicializa o logger para este módulo
logger = logging.getLogger(__name__)


def is_git_repository(repository_path: Path, *, dry_run: bool) -> bool:
    """Verifica se o diretório atual é um repositório git.

    (Função refatorada S.O.L.I.D. - dependências 'self' injetadas)
    """
    try:
        result = executor.run_command(
            command=["git", "rev-parse", "--git-dir"],
            repository_path=repository_path,
            dry_run=dry_run,
            cwd=repository_path,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, OSError, FileNotFoundError):
        return False
    else:
        return result.returncode == 0


def get_current_commit_hash(repository_path: Path, *, dry_run: bool) -> str:
    """Obtém o hash do commit atual.

    (Função refatorada S.O.L.I.D. - dependências 'self' injetadas)
    """
    try:
        result = executor.run_command(
            command=["git", "rev-parse", "HEAD"],
            repository_path=repository_path,
            dry_run=dry_run,
            cwd=repository_path,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, OSError, FileNotFoundError):
        logger.exception("Failed to get commit hash")
        return "unknown"
    else:
        if result.returncode == 0:
            return str(result.stdout.strip()[:8])  # Cast to ensure str type
        return "unknown"
