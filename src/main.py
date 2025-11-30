#!/usr/bin/env python3
"""Ponto de entrada principal para a API (Molde API).

Este arquivo inicia o aplicativo FastAPI.
"""

from fastapi import FastAPI

# Cria a instância principal do aplicativo FastAPI
app = FastAPI(
    title="Minha API (do Molde)",
    description="Uma API incrível gerada pelo molde profissional.",
    version="0.1.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Endpoint raiz (Health Check)."""
    return {"message": "API está online. Praise be to God."}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Endpoint de health check explícito."""
    return {"status": "ok"}


if __name__ == "__main__":
    """
    Permite que o script seja executado diretamente (ex: python3 src/main.py).

    Isso é útil para desenvolvimento local rápido, mas para produção,
    use 'uvicorn src.main:app --host 0.0.0.0 --port 8000'.
    """
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
