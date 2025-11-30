"""Módulo principal para a aplicação CLI."""

import typer

# Cria a instância principal do Typer
app = typer.Typer()


@app.command()
def hello(name: str = "Mundo"):
    """Diz Olá para NAME."""
    print(f"Olá, {name}!")


@app.command()
def goodbye():
    """Diz Adeus."""
    print("Adeus!")


if __name__ == "__main__":
    app()
