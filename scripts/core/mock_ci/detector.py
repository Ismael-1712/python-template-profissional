"""Detecção de ambiente CI/CD.

Este módulo fornece funções para detectar automaticamente o ambiente CI/CD
onde o código está sendo executado, baseado em variáveis de ambiente.
"""

from __future__ import annotations

import os

from scripts.core.mock_ci.config import CI_ENVIRONMENT_VARS


def detect_ci_environment() -> str:
    """Detecta o ambiente CI/CD atual baseado em variáveis de ambiente.

    Verifica a presença de variáveis de ambiente específicas de diferentes
    plataformas CI/CD (GitHub Actions, GitLab CI, Jenkins, etc.) e retorna
    o nome do ambiente detectado.

    A detecção é feita na ordem definida em CI_ENVIRONMENT_VARS. O primeiro
    match determina o ambiente retornado.

    Returns:
        Nome do ambiente CI/CD detectado. Retorna "local" se nenhum ambiente
        CI/CD for detectado (execução em máquina de desenvolvedor).

    Example:
        >>> # Em ambiente GitHub Actions
        >>> detect_ci_environment()
        'github-actions'

        >>> # Em ambiente local (sem variáveis CI)
        >>> detect_ci_environment()
        'local'

    """
    for env_var, ci_name in CI_ENVIRONMENT_VARS.items():
        if os.getenv(env_var):
            return ci_name

    return "local"
