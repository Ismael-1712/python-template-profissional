"""Modelos de dados para o Visibility Guardian.

Define as estruturas para armazenar resultados do scanner AST.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ConfigType(str, Enum):
    """Tipos de configurações detectadas."""

    ENV_VAR = "env_var"
    CLI_ARG = "cli_arg"
    FEATURE_FLAG = "feature_flag"


class ConfigFinding(BaseModel):
    """Representa uma configuração encontrada no código.

    Attributes:
        key: Nome da variável/configuração (ex: "DB_HOST")
        config_type: Tipo da configuração (ENV_VAR, CLI_ARG, etc)
        source_file: Caminho do arquivo onde foi encontrada
        line_number: Número da linha no arquivo
        default_value: Valor padrão, se especificado
        required: Se a configuração é obrigatória
        context: Contexto adicional (nome da função, classe, etc)
    """

    model_config = ConfigDict(frozen=True)

    key: str
    config_type: ConfigType
    source_file: Path
    line_number: int = Field(gt=0)
    default_value: str | None = None
    required: bool = False
    context: str = ""

    def __str__(self) -> str:
        """Representação legível."""
        location = f"{self.source_file}:{self.line_number}"
        required_str = " (required)" if self.required else ""
        default_str = f" [default: {self.default_value}]" if self.default_value else ""
        return f"{self.key}{required_str}{default_str} @ {location}"


class ScanResult(BaseModel):
    """Resultado completo de um scan.

    Attributes:
        findings: Lista de configurações encontradas
        files_scanned: Número de arquivos analisados
        errors: Lista de erros encontrados durante o scan
        scan_duration_ms: Duração do scan em milissegundos
    """

    findings: list[ConfigFinding] = Field(default_factory=list)
    files_scanned: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)
    scan_duration_ms: float = Field(default=0.0, ge=0.0)

    @property
    def total_findings(self) -> int:
        """Total de configurações encontradas."""
        return len(self.findings)

    @property
    def env_vars(self) -> list[ConfigFinding]:
        """Apenas variáveis de ambiente."""
        return [f for f in self.findings if f.config_type == ConfigType.ENV_VAR]

    @property
    def cli_args(self) -> list[ConfigFinding]:
        """Apenas argumentos CLI."""
        return [f for f in self.findings if f.config_type == ConfigType.CLI_ARG]

    def has_errors(self) -> bool:
        """Verifica se houve erros durante o scan."""
        return len(self.errors) > 0

    def summary(self) -> str:
        """Resumo do scan."""
        return (
            f"Scan completo: {self.total_findings} configurações "
            f"em {self.files_scanned} arquivos "
            f"({len(self.env_vars)} env vars, {len(self.cli_args)} CLI args)"
        )
