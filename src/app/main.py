"""Módulo principal da aplicação FastAPI."""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Redireciona a raiz para a documentação interativa."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Endpoint de health check explícito."""
    return {"status": "ok"}


@app.get(f"{settings.API_V1_STR}/meta")
def get_meta() -> dict[str, str]:
    """Retorna metadados do projeto."""
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_v1_str": settings.API_V1_STR,
    }
