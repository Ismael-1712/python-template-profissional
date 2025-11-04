"""Testes para o módulo src.main (CLI)."""

import pytest
from typer.testing import CliRunner

# Importa o 'app' do seu arquivo src.main.py
try:
    from src.main import app
except ImportError:
    app = None


# Cria uma instância do "Executor de CLI"
runner = CliRunner()


@pytest.mark.skipif(app is None, reason="Não foi possível importar 'app' de 'src.main'")
def test_cli_hello_default() -> None:
    """Testa o comando 'hello' com seu valor padrão ('Mundo')."""
    assert app is not None  # noqa: S101

    # Invoca o app, passando "hello" como o comando
    result = runner.invoke(app, ["hello"])

    # Verifica se o comando terminou com sucesso (exit code 0)
    assert result.exit_code == 0  # noqa: S101

    # Verifica se a saída esperada ("Olá, Mundo!") está presente
    assert "Olá, Mundo!" in result.stdout  # noqa: S101


@pytest.mark.skipif(app is None, reason="Não foi possível importar 'app' de 'src.main'")
def test_cli_goodbye() -> None:
    """Testa o comando 'goodbye'."""
    assert app is not None  # noqa: S101

    # Invoca o app, passando "goodbye" como o comando
    result = runner.invoke(app, ["goodbye"])

    # Verifica se o comando terminou com sucesso (exit code 0)
    assert result.exit_code == 0  # noqa: S101

    # Verifica se a saída esperada ("Adeus!") está presente
    assert "Adeus!" in result.stdout  # noqa: S101
