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

import json
import logging
import os
import sys
from datetime import datetime, timezone

try:
    from scripts.utils.context import get_trace_id
except ImportError:
    # Fallback if context module is not available
    def get_trace_id() -> str:
        """Fallback trace ID when context module is unavailable."""
        return "no-trace-id"

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


class InfoHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """Handler que envia INFO/DEBUG para stdout.

    Usa StdoutFilter para garantir que apenas mensagens informativas
    sejam enviadas para stdout, seguindo convenções POSIX.
    """

    def __init__(self) -> None:
        """Inicializa handler para stdout com filtro apropriado."""
        super().__init__(sys.stdout)
        self.addFilter(StdoutFilter())


class ErrorHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """Handler que envia WARNING/ERROR/CRITICAL para stderr.

    Este handler é responsável por enviar mensagens de diagnóstico
    para stderr, conforme convenções POSIX e melhores práticas.
    """

    def __init__(self) -> None:
        """Inicializa handler para stderr com nível WARNING."""
        super().__init__(sys.stderr)
        self.setLevel(logging.WARNING)


# ============================================================
# 2.5. TRACE ID FILTER
# ============================================================


class TraceIDFilter(logging.Filter):
    """Injects Trace ID into log records for distributed tracing.

    This filter automatically adds a 'trace_id' attribute to every
    log record, enabling correlation of logs across operations.

    The Trace ID is retrieved from the context management system,
    which uses contextvars for thread-safe and async-safe storage.

    Example:
        >>> handler.addFilter(TraceIDFilter())
        >>> logger.info("This log will include trace_id")
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add trace_id attribute to log record.

        Args:
            record: Log record to enhance

        Returns:
            Always True (record is always processed)
        """
        setattr(record, "trace_id", get_trace_id())  # noqa: B010
        return True


# ============================================================
# 2.6. JSON FORMATTER
# ============================================================


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging.

    This formatter outputs logs in JSON format, making them easy to
    parse, index, and analyze with modern observability tools like
    ELK Stack, Splunk, or Datadog.

    Output fields:
        - timestamp: ISO8601 formatted timestamp with timezone
        - level: Log level (INFO, ERROR, etc.)
        - logger: Logger name (usually module path)
        - message: Formatted log message
        - trace_id: Distributed tracing identifier
        - location: File and line number
        - extra: Any additional context fields

    Example Output:
        {
            "timestamp": "2025-12-03T21:45:00.123456Z",
            "level": "INFO",
            "logger": "scripts.cli.audit",
            "message": "Starting audit",
            "trace_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "location": "audit.py:195"
        }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Build base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", "no-trace-id"),
            "location": f"{record.filename}:{record.lineno}",
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields (custom context)
        extra = getattr(record, "extra", None)
        if extra:
            log_entry["extra"] = extra

        return json.dumps(log_entry, ensure_ascii=False)


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
        return not (os.environ.get("CI") and not os.environ.get("TERM"))

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
    *,
    use_json: bool | None = None,
) -> logging.Logger:
    """Configura logging com separação correta de streams e Trace ID.

    Esta função configura o logging seguindo as melhores práticas:
    - INFO/DEBUG → stdout (dados, progresso)
    - WARNING/ERROR/CRITICAL → stderr (diagnósticos)
    - Trace ID automático para correlação de logs
    - Suporte a JSON structured logging

    Args:
        name: Nome do logger (geralmente __name__)
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho opcional para arquivo de log
        format_string: String de formatação customizada
        use_json: Force JSON format. If None, uses LOG_FORMAT env var

    Returns:
        Logger configurado

    Environment Variables:
        LOG_FORMAT: "json" para JSON logs, "text" para formato texto (padrão)
        LOG_LEVEL: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Exemplo:
        >>> logger = setup_logging(__name__)
        >>> logger.info("Isso vai para stdout")
        >>> logger.error("Isso vai para stderr")

        >>> # Com JSON logging
        >>> logger = setup_logging(__name__, use_json=True)

        >>> # Via environment variable
        >>> # export LOG_FORMAT=json
        >>> logger = setup_logging(__name__)
    """
    logger = logging.getLogger(name)

    # Check environment variable for log level override
    env_level = os.environ.get("LOG_LEVEL", "").upper()
    if env_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        level = getattr(logging, env_level)

    logger.setLevel(level)

    # Remove handlers existentes para evitar duplicação
    logger.handlers.clear()

    # Determine format (JSON or text)
    if use_json is None:
        log_format = os.environ.get("LOG_FORMAT", "text").lower()
        use_json = log_format == "json"

    # Create formatter
    if use_json:
        formatter: logging.Formatter = JSONFormatter()
    else:
        # Formato padrão com Trace ID
        if format_string is None:
            format_string = (
                "%(asctime)s - [%(trace_id)s] - %(name)s - %(levelname)s - %(message)s"
            )
        formatter = logging.Formatter(format_string)

    # Create Trace ID filter
    trace_filter = TraceIDFilter()

    # Handler para INFO/DEBUG → stdout
    stdout_handler = InfoHandler()
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(trace_filter)
    logger.addHandler(stdout_handler)

    # Handler para WARNING/ERROR/CRITICAL → stderr
    stderr_handler = ErrorHandler()
    stderr_handler.setFormatter(formatter)
    stderr_handler.addFilter(trace_filter)
    logger.addHandler(stderr_handler)

    # Handler opcional para arquivo (todos os níveis)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(trace_filter)
        logger.addHandler(file_handler)

    return logger
