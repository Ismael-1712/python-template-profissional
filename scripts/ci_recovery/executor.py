#!/usr/bin/env python3

"""Módulo Executor de Subprocesso (Utilitário SRE).

(Extraído do monólito P8.2).
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from pathlib import Path

# Inicializa o logger para este módulo
logger = logging.getLogger(__name__)


def run_command(
    command: list[str],
    repository_path: Path,  # <-- Dependência 'self' removida
    dry_run: bool,  # <-- Dependência 'self' removida
    cwd: Path | None = None,
    capture_output: bool = True,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    """Executa um comando de forma segura usando subprocess.

    Args:
        command: Comando como lista de strings (para execução segura)
        repository_path: Caminho do repositório (para 'cwd' padrão)
        dry_run: Se True, simula a execução
        cwd: Diretório de trabalho
        capture_output: Se captura stdout/stderr
        timeout: Timeout em segundos

    Returns:
        Instância de CompletedProcess

    Raises:
        subprocess.TimeoutExpired: Se o comando expirar
        subprocess.SubprocessError: Em erros de subprocesso
        ValueError: Se o comando for inválido ou inseguro

    """
    # Validação de segurança do comando
    if not command or not isinstance(command, list):
        raise ValueError("Comando deve ser uma lista não vazia")

    # Validação de segurança adicional - previne path traversal
    if any("/../" in str(arg) or str(arg).startswith("/") for arg in command):
        raise ValueError("Comando contém caminhos potencialmente inseguros")

    # Sanitize command arguments (para logging)
    sanitized_command = [
        shlex.quote(str(arg)) if " " in str(arg) else str(arg) for arg in command
    ]

    logger.debug(f"Executando comando: {' '.join(sanitized_command)}")

    if dry_run:  # <-- 'self.' removido
        logger.info(f"DRY RUN: Executaria: {' '.join(sanitized_command)}")
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    try:
        result = subprocess.run(  # noqa: subprocess
            command,  # Usa o comando original, não sanitizado
            cwd=cwd or repository_path,  # <-- 'self.' removido
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=False,  # Não levanta exceção em exit code não-zero
            shell=False,  # Security: prevent shell injection
        )

        if result.returncode != 0:
            logger.warning(
                f"Comando falhou com exit code {result.returncode}: "
                f"{' '.join(sanitized_command)}",
            )
            if result.stderr:
                logger.warning(f"STDERR: {result.stderr}")

        return result

    except subprocess.TimeoutExpired:
        logger.error(
            f"Comando expirou após {timeout}s: {' '.join(sanitized_command)}",
        )
        raise
    except Exception as e:
        logger.error(f"Execução do comando falhou: {e}")
        raise
