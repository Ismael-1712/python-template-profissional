#!/usr/bin/env python3
"""Ponto de entrada principal para a API.

Este arquivo inicia o aplicativo FastAPI e define os endpoints (rotas).
"""

from fastapi import FastAPI

# Cria a instância principal do aplicativo FastAPI
app = FastAPI(
    title="Minha API (do Molde)",
    description="Este é um projeto de API gerado pelo python-template-profissional.",
    version="0.1.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Endpoint raiz (Homepage) da API.

    Retorna uma mensagem de "Praise be to God".
    """
    return {"message": "Hello World, from the API template!"}


@app.get("/health")
def read_health() -> dict[str, str]:
    """Endpoint de verificação de saúde (Health Check).

    Usado por sistemas de monitoramento (como Docker, Kubernetes)
    para verificar se a API está online e respondendo.
    """
    return {"status": "ok"}
