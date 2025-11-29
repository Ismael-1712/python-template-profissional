#!/usr/bin/env python3
"""Sistema de Logging Padronizado para Scripts.

Fornece configuração centralizada de logging com:
- Separação correta de streams (INFO → stdout, ERROR/WARNING → stderr)
- Suporte a cores ANSI com detecção de terminal
- Configuração reutilizável para todos os scripts

Exemplo de Uso:
    >>> from scripts.utils.logger import setup_logging, get_colors
    >>>
    >>> # Configurar logger
    >>> logger = setup_logging(__name__)
    >>> logger.info("Isso vai para stdout")
    >>> logger.error("Isso vai para stderr")
    >>>
    >>> # Usar cores
    >>> colors = get_colors()
    >>> print(f"{colors.GREEN}Sucesso!{colors.RESET}")

Autor: DevOps Engineering Team
Versão: 1.0.0
"""

import logging
import os
import sys

# ============================================================
# 1. HANDLERS CUSTOMIZADOS COM SEPARAÇÃO DE STREAMS
# ============================================================


class StdoutFilter(logging.Filter):
    """Filtra apenas mensagens INFO e DEBUG para stdout.

    Este filtro garante que apenas mensagens de nível INFO ou inferior
    sejam enviadas para stdout, mantendo warnings e erros separados.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filtra mensagens baseado no nível de log.

        Args:
            record: Registro de log a ser filtrado

        Returns:
            True se a mensagem deve ser processada (INFO ou DEBUG)
        """
        return record.levelno <= logging.INFO


class InfoHandler(logging.StreamHandler):
    """Handler que envia INFO/DEBUG para stdout.

    Usa StdoutFilter para garantir que apenas mensagens informativas
    sejam enviadas para stdout, seguindo convenções POSIX.
    """

    def __init__(self) -> None:
        """Inicializa handler para stdout com filtro apropriado."""
        super().__init__(sys.stdout)
        self.addFilter(StdoutFilter())


class ErrorHandler(logging.StreamHandler):
    """Handler que envia WARNING/ERROR/CRITICAL para stderr.

    Este handler é responsável por enviar mensagens de diagnóstico
    para stderr, conforme convenções POSIX e melhores práticas.
    """

    def __init__(self) -> None:
        """Inicializa handler para stderr com nível WARNING."""
        super().__init__(sys.stderr)
        self.setLevel(logging.WARNING)


# ============================================================
# 2. SISTEMA DE CORES COM DETECÇÃO DE TERMINAL
# ============================================================


class TerminalColors:
    """Códigos ANSI para formatação de terminal com detecção automática.

    Desabilita cores automaticamente se:
    - Terminal não é interativo (sys.stdout.isatty() == False)
    - Variável NO_COLOR está definida
    - Ambiente CI sem suporte a cores

    Exemplo:
        >>> colors = TerminalColors()
        >>> print(f"{colors.RED}Erro{colors.RESET}")
        >>> # Cores desabilitadas automaticamente em pipes:
        >>> # python script.py | cat
    """

    def __init__(self, *, force_colors: bool = False) -> None:
        """Inicializa com detecção automática de suporte a cores.

        Args:
            force_colors: Força ativação de cores (útil para testes)
        """
        self._enabled = self._should_use_colors(force_colors)

    def _should_use_colors(self, force: bool) -> bool:  # noqa: FBT001
        """Determina se cores devem ser usadas.

        Args:
            force: Se True, força ativação de cores

        Returns:
            True se cores devem ser ativadas
        """
        if force:
            return True

        # Respeita NO_COLOR (https://no-color.org/)
        if os.environ.get("NO_COLOR"):
            return False

        # Verifica se stdout é um terminal interativo
        if not sys.stdout.isatty():
            return False

        # GitHub Actions suporta cores com TERM
        if os.environ.get("CI") and not os.environ.get("TERM"):
            return False

        return True

    @property
    def RED(self) -> str:  # noqa: N802
        """Retorna código ANSI para vermelho ou string vazia."""
        return "\033[91m" if self._enabled else ""

    @property
    def GREEN(self) -> str:  # noqa: N802
        """Retorna código ANSI para verde ou string vazia."""
        return "\033[92m" if self._enabled else ""

    @property
    def YELLOW(self) -> str:  # noqa: N802
        """Retorna código ANSI para amarelo ou string vazia."""
        return "\033[93m" if self._enabled else ""

    @property
    def BLUE(self) -> str:  # noqa: N802
        """Retorna código ANSI para azul ou string vazia."""
        return "\033[94m" if self._enabled else ""

    @property
    def BOLD(self) -> str:  # noqa: N802
        """Retorna código ANSI para negrito ou string vazia."""
        return "\033[1m" if self._enabled else ""

    @property
    def RESET(self) -> str:  # noqa: N802
        """Retorna código ANSI para reset ou string vazia."""
        return "\033[0m" if self._enabled else ""


# Instância global (lazy initialization)
_colors: TerminalColors | None = None


def get_colors(*, force: bool = False) -> TerminalColors:
    """Obtém instância de cores (singleton pattern).

    Args:
        force: Força ativação de cores

    Returns:
        Instância de TerminalColors

    Exemplo:
        >>> colors = get_colors()
        >>> print(f"{colors.GREEN}Sucesso{colors.RESET}")
    """
    global _colors  # noqa: PLW0603
    if _colors is None:
        _colors = TerminalColors(force_colors=force)
    return _colors


# ============================================================
# 3. FUNÇÃO DE CONFIGURAÇÃO PADRONIZADA
# ============================================================


def setup_logging(
    name: str = "__main__",
    level: int = logging.INFO,
    log_file: str | None = None,
    format_string: str | None = None,
) -> logging.Logger:
    """Configura logging com separação correta de streams.

    Esta função configura o logging seguindo as melhores práticas:
    - INFO/DEBUG → stdout (dados, progresso)
    - WARNING/ERROR/CRITICAL → stderr (diagnósticos)

    Args:
        name: Nome do logger (geralmente __name__)
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho opcional para arquivo de log
        format_string: String de formatação customizada

    Returns:
        Logger configurado

    Exemplo:
        >>> logger = setup_logging(__name__)
        >>> logger.info("Isso vai para stdout")
        >>> logger.error("Isso vai para stderr")

        >>> # Com arquivo de log
        >>> logger = setup_logging(__name__, log_file="app.log")

        >>> # Com nível DEBUG
        >>> logger = setup_logging(__name__, level=logging.DEBUG)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove handlers existentes para evitar duplicação
    logger.handlers.clear()

    # Formato padrão
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string)

    # Handler para INFO/DEBUG → stdout
    stdout_handler = InfoHandler()
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # Handler para WARNING/ERROR/CRITICAL → stderr
    stderr_handler = ErrorHandler()
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    # Handler opcional para arquivo (todos os níveis)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
