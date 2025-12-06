#!/usr/bin/env python3
"""Testes unitários para o sistema de logging padronizado.

Testa a separação correta de streams, detecção de terminal e cores ANSI.
"""

from __future__ import annotations

# ruff: noqa: S101, PLR2004, SLF001
# S101: Use of assert (required for pytest)
# PLR2004: Magic value in comparison (test constants are acceptable)
# SLF001: Private member access (necessary for unit testing internals)
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

from scripts.utils.logger import (
    ErrorHandler,
    InfoHandler,
    StdoutFilter,
    TerminalColors,
    get_colors,
    setup_logging,
)


class TestStdoutFilter:
    """Testes para o filtro de stdout (INFO/DEBUG apenas)."""

    def test_filter_allows_info(self) -> None:
        """INFO deve passar pelo filtro."""
        filter_obj = StdoutFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert filter_obj.filter(record) is True

    def test_filter_allows_debug(self) -> None:
        """DEBUG deve passar pelo filtro."""
        filter_obj = StdoutFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert filter_obj.filter(record) is True

    def test_filter_blocks_warning(self) -> None:
        """WARNING NÃO deve passar pelo filtro."""
        filter_obj = StdoutFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert filter_obj.filter(record) is False

    def test_filter_blocks_error(self) -> None:
        """ERROR NÃO deve passar pelo filtro."""
        filter_obj = StdoutFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert filter_obj.filter(record) is False


class TestHandlers:
    """Testes para os handlers customizados."""

    def test_info_handler_has_filter(self) -> None:
        """InfoHandler deve ter o StdoutFilter aplicado."""
        handler = InfoHandler()
        assert len(handler.filters) == 1
        assert isinstance(handler.filters[0], StdoutFilter)

    def test_error_handler_level(self) -> None:
        """ErrorHandler deve ter nível WARNING."""
        handler = ErrorHandler()
        assert handler.level == logging.WARNING


class TestStreamSeparation:
    """Testes de separação de streams (stdout vs stderr)."""

    def test_info_goes_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Mensagens INFO devem ir para stdout."""
        logger = setup_logging("test_stdout")
        logger.info("Test message to stdout")

        captured = capsys.readouterr()
        assert "Test message to stdout" in captured.out
        assert "Test message to stdout" not in captured.err

    def test_warning_goes_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Mensagens WARNING devem ir para stderr."""
        logger = setup_logging("test_stderr_warn")
        logger.warning("Test warning to stderr")

        captured = capsys.readouterr()
        assert "Test warning to stderr" in captured.err
        assert "Test warning to stderr" not in captured.out

    def test_error_goes_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Mensagens ERROR devem ir para stderr."""
        logger = setup_logging("test_stderr_error")
        logger.error("Test error to stderr")

        captured = capsys.readouterr()
        assert "Test error to stderr" in captured.err
        assert "Test error to stderr" not in captured.out

    def test_critical_goes_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Mensagens CRITICAL devem ir para stderr."""
        logger = setup_logging("test_stderr_critical")
        logger.critical("Test critical to stderr")

        captured = capsys.readouterr()
        assert "Test critical to stderr" in captured.err
        assert "Test critical to stderr" not in captured.out

    def test_debug_goes_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Mensagens DEBUG devem ir para stdout."""
        logger = setup_logging("test_debug", level=logging.DEBUG)
        logger.debug("Test debug to stdout")

        captured = capsys.readouterr()
        assert "Test debug to stdout" in captured.out
        assert "Test debug to stdout" not in captured.err


class TestTerminalColors:
    """Testes para detecção de terminal e cores ANSI."""

    def test_colors_disabled_with_no_color_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Cores devem ser desabilitadas quando NO_COLOR está definida."""
        monkeypatch.setenv("NO_COLOR", "1")
        colors = TerminalColors()

        assert colors.RED == ""
        assert colors.GREEN == ""
        assert colors.RESET == ""

    def test_colors_enabled_with_force(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """force_colors=True deve forçar ativação de cores."""
        monkeypatch.setenv("NO_COLOR", "1")
        colors = TerminalColors(force_colors=True)

        assert colors.RED == "\033[91m"
        assert colors.GREEN == "\033[92m"
        assert colors.YELLOW == "\033[93m"
        assert colors.BLUE == "\033[94m"
        assert colors.BOLD == "\033[1m"
        assert colors.RESET == "\033[0m"

    def test_colors_disabled_in_ci_without_term(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Cores devem ser desabilitadas em CI sem TERM."""
        monkeypatch.setenv("CI", "true")
        monkeypatch.delenv("TERM", raising=False)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        colors = TerminalColors()
        assert colors.RED == ""

    def test_colors_enabled_in_ci_with_term(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Cores devem ser habilitadas em CI com TERM."""
        monkeypatch.setenv("CI", "true")
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        colors = TerminalColors()
        assert colors.RED == "\033[91m"

    def test_get_colors_singleton(self) -> None:
        """get_colors() deve retornar sempre a mesma instância."""
        # Limpar singleton para teste
        import scripts.utils.logger as logger_module

        logger_module._colors = None

        colors1 = get_colors()
        colors2 = get_colors()

        assert colors1 is colors2


class TestSetupLogging:
    """Testes para a função setup_logging."""

    def test_setup_logging_basic(self) -> None:
        """setup_logging deve criar logger funcional."""
        logger = setup_logging("test_basic")

        assert logger.name == "test_basic"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 2  # InfoHandler + ErrorHandler

    def test_setup_logging_with_level(self) -> None:
        """setup_logging deve aceitar nível customizado."""
        logger = setup_logging("test_level", level=logging.DEBUG)

        assert logger.level == logging.DEBUG

    def test_setup_logging_with_file(self, tmp_path: Path) -> None:
        """setup_logging deve criar handler de arquivo quando solicitado."""
        log_file = tmp_path / "test.log"
        logger = setup_logging("test_file", log_file=str(log_file))

        assert len(logger.handlers) == 3  # stdout + stderr + file

        logger.info("Test message to file")
        assert log_file.exists()
        assert "Test message to file" in log_file.read_text()

    def test_setup_logging_custom_format(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """setup_logging deve aceitar formato customizado."""
        logger = setup_logging(
            "test_format",
            format_string="%(levelname)s: %(message)s",
        )

        logger.info("Custom format test")

        captured = capsys.readouterr()
        assert "INFO: Custom format test" in captured.out

    def test_setup_logging_clears_existing_handlers(self) -> None:
        """setup_logging deve limpar handlers existentes."""
        logger = setup_logging("test_clear")
        initial_count = len(logger.handlers)

        # Chamar novamente
        logger = setup_logging("test_clear")

        assert len(logger.handlers) == initial_count


class TestIntegration:
    """Testes de integração do sistema completo."""

    def test_full_workflow(
        self,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """Teste completo: logger + cores + arquivo."""
        log_file = tmp_path / "integration.log"
        logger = setup_logging("integration", log_file=str(log_file))
        colors = get_colors(force=True)

        # Logar diferentes níveis
        logger.info(f"{colors.GREEN}Info message{colors.RESET}")
        logger.warning(f"{colors.YELLOW}Warning message{colors.RESET}")
        logger.error(f"{colors.RED}Error message{colors.RESET}")

        # Verificar streams
        captured = capsys.readouterr()
        assert "Info message" in captured.out
        assert "Warning message" in captured.err
        assert "Error message" in captured.err

        # Verificar arquivo
        log_content = log_file.read_text()
        assert "Info message" in log_content
        assert "Warning message" in log_content
        assert "Error message" in log_content

    def test_no_color_environment_integration(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Teste de integração com NO_COLOR."""
        monkeypatch.setenv("NO_COLOR", "1")

        # Resetar singleton
        import scripts.utils.logger as logger_module

        logger_module._colors = None

        logger = setup_logging("no_color_test")
        colors = get_colors()

        logger.error(f"{colors.RED}Error without colors{colors.RESET}")

        captured = capsys.readouterr()
        # Não deve conter códigos ANSI
        assert "\033[" not in captured.err
        assert "Error without colors" in captured.err
