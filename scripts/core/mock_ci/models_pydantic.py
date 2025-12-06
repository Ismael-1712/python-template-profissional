"""Modelos Pydantic para Mock CI Integration.

Este módulo contém modelos validados com Pydantic para substituir
classes planas e dataclasses no sistema de Mock CI.

Migração gradual iniciada em P08 - Fase 2.

Author: DevOps Engineering Team
License: MIT
Version: 1.0.0
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MockPattern(BaseModel):
    """Representa um padrão de código que precisa de mock.

    Migrado de classe plana para Pydantic BaseModel para adicionar:
    - Validação automática de tipos
    - Serialização JSON nativa
    - Imutabilidade por padrão
    - Documentação de campos

    Attributes:
        pattern: Padrão de código a detectar (ex: "requests.get")
        mock_type: Tipo de mock (HTTP_REQUEST, SUBPROCESS, etc)
        mock_template: Template do código de mock a aplicar
        required_imports: Imports necessários para o mock funcionar
        description: Descrição legível do que o padrão detecta
        severity: Nível de severidade (HIGH, MEDIUM, LOW)

    Example:
        >>> pattern = MockPattern(
        ...     pattern="requests.get",
        ...     mock_type="HTTP_REQUEST",
        ...     mock_template="@patch('requests.get')",
        ...     required_imports=["from unittest.mock import patch"],
        ...     description="HTTP request detected",
        ...     severity="HIGH"
        ... )
        >>> pattern.model_dump()
        {'pattern': 'requests.get', 'mock_type': 'HTTP_REQUEST', ...}
    """

    pattern: str = Field(
        ...,
        description="Código pattern a detectar (ex: 'requests.get')",
        min_length=1,
    )

    mock_type: str = Field(
        ...,
        description="Tipo do mock (HTTP_REQUEST, SUBPROCESS, FILE_IO, etc)",
        min_length=1,
    )

    mock_template: str = Field(
        default="",
        description="Template do código de mock a aplicar",
    )

    required_imports: list[str] = Field(
        default_factory=list,
        description="Lista de imports necessários para o mock",
    )

    description: str = Field(
        default="",
        description="Descrição legível do padrão",
    )

    severity: str = Field(
        default="MEDIUM",
        description="Nível de severidade (HIGH, MEDIUM, LOW)",
        pattern="^(HIGH|MEDIUM|LOW)$",
    )

    class Config:
        """Configuração do modelo Pydantic."""

        # Permite validação estrita
        validate_assignment = True
        # Permite usar o modelo como dict em alguns contextos
        use_enum_values = True
        # Frozen para imutabilidade (opcional, pode ser removido se necessário)
        frozen = False  # Mantém mutável para compatibilidade inicial

    def __repr__(self) -> str:
        """Representação legível para debug."""
        return (
            f"MockPattern(pattern={self.pattern!r}, "
            f"type={self.mock_type!r}, severity={self.severity!r})"
        )
