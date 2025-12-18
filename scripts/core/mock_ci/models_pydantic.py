"""Modelos Pydantic para Mock CI Integration.

Este módulo contém modelos validados com Pydantic V2 para configuração
do sistema de Mock CI.

Refatorado em Fase 02 - TDD GREEN para:
- Eliminar warnings de deprecation do Pydantic V2
- Criar Single Source of Truth via schema validado
- Permitir geração automática de documentação

Author: DevOps Engineering Team
License: MIT
Version: 2.0.0
"""

from __future__ import annotations

import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# ENUMS
# =============================================================================


class SeverityLevel(str, Enum):
    """Níveis de severidade para padrões de mock.

    Determina a prioridade de aplicação automática de correções.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class LogLevel(str, Enum):
    """Níveis de logging disponíveis."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OutputFormat(str, Enum):
    """Formatos de saída para relatórios."""

    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"


# =============================================================================
# MODELO DE PADRÃO DE MOCK
# =============================================================================


class MockPattern(BaseModel):
    """Representa um padrão de código que precisa de mock.

    Atualizado para Pydantic V2 - Sem warnings de deprecation.

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
        ...     type="HTTP_REQUEST",  # Aceita 'type' do YAML
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
        alias="type",  # Permite usar 'type' no YAML
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

    # Configuração Pydantic V2 (sem warnings)
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        frozen=False,
        populate_by_name=True,  # Permite usar 'type' ou 'mock_type'
    )

    def __repr__(self) -> str:
        """Representação legível para debug."""
        return (
            f"MockPattern(pattern={self.pattern!r}, "
            f"type={self.mock_type!r}, severity={self.severity!r})"
        )


# =============================================================================
# MODELOS DE CONFIGURAÇÃO
# =============================================================================


class MockPatternsConfig(BaseModel):
    """Configuração de padrões de mock organizados por categoria.

    Attributes:
        http_patterns: Padrões para requisições HTTP
        subprocess_patterns: Padrões para execução de processos
        filesystem_patterns: Padrões para operações de arquivo
        database_patterns: Padrões para conexões de banco de dados
    """

    http_patterns: list[MockPattern] = Field(
        default_factory=list,
        description="Padrões para requisições HTTP (httpx, requests)",
    )

    subprocess_patterns: list[MockPattern] = Field(
        default_factory=list,
        description="Padrões para execução de processos (subprocess)",
    )

    filesystem_patterns: list[MockPattern] = Field(
        default_factory=list,
        description="Padrões para operações de arquivo (open, pathlib)",
    )

    database_patterns: list[MockPattern] = Field(
        default_factory=list,
        description="Padrões para conexões de banco de dados (sqlite3, etc)",
    )

    model_config = ConfigDict(validate_assignment=True)


class ExecutionConfig(BaseModel):
    """Configuração de execução do Mock CI.

    Attributes:
        test_file_patterns: Padrões glob para localizar arquivos de teste
        exclude_patterns: Padrões glob para excluir arquivos
        min_severity_for_auto_apply: Severidade mínima para aplicação automática
        create_backups: Se deve criar backups antes de modificar arquivos
        backup_directory: Diretório para armazenar backups
    """

    test_file_patterns: list[str] = Field(
        default_factory=list,
        description="Padrões glob para localizar arquivos de teste",
    )

    exclude_patterns: list[str] = Field(
        default_factory=list,
        description="Padrões glob para excluir arquivos do processamento",
    )

    min_severity_for_auto_apply: str = Field(
        default="HIGH",
        description="Severidade mínima para aplicação automática de correções",
        pattern="^(HIGH|MEDIUM|LOW)$",
    )

    create_backups: bool = Field(
        default=True,
        description="Criar backups antes de modificar arquivos",
    )

    backup_directory: str = Field(
        default=".test_mock_backups",
        description="Diretório para armazenar backups",
    )

    model_config = ConfigDict(validate_assignment=True)


class LoggingConfig(BaseModel):
    """Configuração de logging.

    Attributes:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Formato da mensagem de log
    """

    level: str = Field(
        default="INFO",
        description="Nível de log",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )

    format: str = Field(
        default="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        description="Formato da mensagem de log",
    )

    model_config = ConfigDict(validate_assignment=True)


class ReportingConfig(BaseModel):
    """Configuração de relatórios.

    Attributes:
        include_low_priority: Incluir sugestões de baixa prioridade
        max_suggestions_display: Número máximo de sugestões a exibir
        output_format: Formato de saída (json, text, markdown)
    """

    include_low_priority: bool = Field(
        default=False,
        description="Incluir sugestões de baixa prioridade nos relatórios",
    )

    max_suggestions_display: int = Field(
        default=10,
        ge=1,
        description="Número máximo de sugestões a exibir",
    )

    output_format: str = Field(
        default="json",
        description="Formato de saída dos relatórios",
        pattern="^(json|text|markdown)$",
    )

    model_config = ConfigDict(validate_assignment=True)


# =============================================================================
# MODELO RAIZ (SINGLE SOURCE OF TRUTH)
# =============================================================================


class MockCIConfig(BaseModel):
    """Configuração raiz do Mock CI - Single Source of Truth.

    Este modelo representa a estrutura completa do arquivo
    `scripts/test_mock_config.yaml` com validação estrita.

    Attributes:
        version: Versão da configuração (formato X.Y)
        mock_patterns: Padrões de mock organizados por categoria
        execution: Configurações de execução
        logging: Configurações de logging
        reporting: Configurações de relatório

    Example:
        >>> import yaml
        >>> with open("test_mock_config.yaml") as f:
        ...     data = yaml.safe_load(f)
        >>> config = MockCIConfig(**data)
        >>> assert config.version == "1.0"
    """

    version: str = Field(
        default="1.0",
        description="Versão da configuração",
        pattern=r"^\d+\.\d+$",
    )

    mock_patterns: MockPatternsConfig = Field(
        ...,
        description="Padrões de mock organizados por categoria",
    )

    execution: ExecutionConfig = Field(
        ...,
        description="Configurações de execução do Mock CI",
    )

    logging: LoggingConfig = Field(
        ...,
        description="Configurações de logging",
    )

    reporting: ReportingConfig = Field(
        ...,
        description="Configurações de relatório",
    )

    model_config = ConfigDict(
        validate_assignment=True,
        json_schema_extra={
            "title": "Mock CI Configuration",
            "description": "Configuration schema for automated test mock generation",
        },
    )


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================


def generate_schema_json() -> str:
    """Gera o schema JSON do MockCIConfig para documentação.

    Returns:
        String JSON formatada com o schema completo.

    Example:
        >>> schema = generate_schema_json()
        >>> import json
        >>> data = json.loads(schema)
        >>> assert "title" in data
    """
    schema = MockCIConfig.model_json_schema()
    return json.dumps(schema, indent=2)
