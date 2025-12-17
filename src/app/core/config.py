"""Configurações da aplicação."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações globais da aplicação."""

    PROJECT_NAME: str = "Meu Projeto Profissional"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
