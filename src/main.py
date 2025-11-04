#!/usr/bin/env python3
"""Ponto de entrada principal para a aplicação CLI.

Este arquivo inicia o aplicativo Typer.
"""

import typer

# Cria a instância principal do aplicativo Typer
app = typer.Typer(
    name="meu_projeto_placeholder",
    help="Uma aplicação CLI incrível gerada pelo molde profissional.",
    add_completion=False,  # Desativa a autocompletação por padrão
)


@app.command()
def hello(
    name: str = typer.Option("Mundo", "--name", "-n", help="O nome para saudar."),
) -> None:
    """Envia uma saudação "Olá, [nome]!" no console."""
    typer.echo(f"Olá, {name}!")


@app.command()
def goodbye() -> None:
    """Envia uma despedida."""
    typer.echo("Adeus!")


if __name__ == "__main__":
    """
    Permite que o script seja executado diretamente (ex: python3 src/main.py).

    Isso é útil para desenvolvimento local rápido, sem precisar
    instalar o pacote com 'pip install .'.
    """
    app()
