"""Modelos de dados para Mock CI Integration.

Este módulo define as estruturas de dados usadas para representar informações
de git, sugestões de mock, relatórios CI e status de verificação.

Usa dataclasses padrão do Python para manter consistência com o restante do
projeto até a migração global para Pydantic (P16).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Nível de severidade de uma sugestão de mock."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MockType(str, Enum):
    """Tipo de mock sugerido."""

    HTTP_REQUEST = "HTTP_REQUEST"
    SUBPROCESS = "SUBPROCESS"
    FILE_IO = "FILE_IO"
    DATABASE = "DATABASE"
    DATETIME = "DATETIME"
    RANDOM = "RANDOM"
    ENVIRONMENT = "ENVIRONMENT"
    NETWORK = "NETWORK"
    EXTERNAL_API = "EXTERNAL_API"


class CIStatus(str, Enum):
    """Status geral da verificação CI/CD."""

    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILURE = "FAILURE"


@dataclass
class GitInfo:
    """Informações sobre o repositório git.

    Attributes:
        is_git_repo: Se o diretório é um repositório git válido
        has_changes: Se há mudanças não commitadas
        current_branch: Nome da branch atual (None se não detectado)
        commit_hash: Hash curto do commit atual (None se não detectado)

    """

    is_git_repo: bool = False
    has_changes: bool = False
    current_branch: str | None = None
    commit_hash: str | None = None


@dataclass
class MockSuggestion:
    """Sugestão de mock para um teste.

    Attributes:
        severity: Nível de severidade (HIGH, MEDIUM, LOW)
        mock_type: Tipo de mock sugerido
        file_path: Caminho do arquivo de teste
        line_number: Número da linha onde aplicar o mock
        reason: Explicação da sugestão
        pattern: Padrão detectado (opcional)

    """

    severity: str  # Mantém como str para compatibilidade com código existente
    mock_type: str  # Mantém como str para compatibilidade
    file_path: str
    line_number: int
    reason: str
    pattern: str | None = None

    @property
    def severity_enum(self) -> Severity:
        """Converte severity string para enum."""
        return Severity(self.severity)

    @property
    def mock_type_enum(self) -> MockType:
        """Converte mock_type string para enum."""
        return MockType(self.mock_type)


@dataclass
class MockSuggestions:
    """Agregação de sugestões de mock.

    Attributes:
        total: Total de sugestões
        high_priority: Número de sugestões de alta prioridade
        blocking: Número de sugestões bloqueadoras
        details: Lista de sugestões detalhadas

    """

    total: int
    high_priority: int
    blocking: int
    details: list[MockSuggestion] = field(default_factory=list)

    @classmethod
    def from_suggestions_list(
        cls,
        suggestions: list[dict[str, Any]],
        blocking_mock_types: set[str],
    ) -> "MockSuggestions":
        """Cria MockSuggestions a partir de lista de dicionários.

        Args:
            suggestions: Lista de sugestões (dicts do gerador)
            blocking_mock_types: Set de tipos considerados bloqueadores

        Returns:
            Instância de MockSuggestions

        """
        mock_suggestions = [
            MockSuggestion(
                severity=s.get("severity", "MEDIUM"),
                mock_type=s.get("mock_type", "UNKNOWN"),
                file_path=s.get("file_path", ""),
                line_number=s.get("line_number", 0),
                reason=s.get("reason", ""),
                pattern=s.get("pattern"),
            )
            for s in suggestions
        ]

        high_priority = [s for s in mock_suggestions if s.severity == "HIGH"]
        blocking = [s for s in high_priority if s.mock_type in blocking_mock_types]

        return cls(
            total=len(mock_suggestions),
            high_priority=len(high_priority),
            blocking=len(blocking),
            details=mock_suggestions,
        )


@dataclass
class CIReport:
    """Relatório completo de verificação CI/CD.

    Attributes:
        timestamp: Timestamp da execução
        environment: Nome do ambiente CI/CD
        workspace: Caminho do workspace
        git_info: Informações do repositório git
        validation_results: Resultados de validação (nome -> sucesso)
        mock_suggestions: Sugestões de mock agregadas
        summary: Resumo geral (dict livre)
        recommendations: Lista de recomendações textuais
        status: Status geral (SUCCESS, WARNING, FAILURE)

    """

    timestamp: str
    environment: str
    workspace: str
    git_info: GitInfo
    validation_results: dict[str, bool]
    mock_suggestions: MockSuggestions
    summary: dict[str, Any]
    recommendations: list[str]
    status: str  # Mantém como str para compatibilidade com JSON

    @property
    def status_enum(self) -> CIStatus:
        """Converte status string para enum."""
        return CIStatus(self.status)

    def to_dict(self) -> dict[str, Any]:
        """Serializa relatório para dicionário (compatível com JSON).

        Returns:
            Dicionário com todos os campos do relatório

        """
        return {
            "timestamp": self.timestamp,
            "environment": self.environment,
            "workspace": self.workspace,
            "git_info": {
                "is_git_repo": self.git_info.is_git_repo,
                "has_changes": self.git_info.has_changes,
                "current_branch": self.git_info.current_branch,
                "commit_hash": self.git_info.commit_hash,
            },
            "validation_results": self.validation_results,
            "mock_suggestions": {
                "total": self.mock_suggestions.total,
                "high_priority": self.mock_suggestions.high_priority,
                "blocking": self.mock_suggestions.blocking,
                "details": [
                    {
                        "severity": s.severity,
                        "mock_type": s.mock_type,
                        "file_path": s.file_path,
                        "line_number": s.line_number,
                        "reason": s.reason,
                        "pattern": s.pattern,
                    }
                    for s in self.mock_suggestions.details
                ],
            },
            "summary": self.summary,
            "recommendations": self.recommendations,
            "status": self.status,
        }


@dataclass
class FixResult:
    """Resultado de aplicação de correções automáticas.

    Attributes:
        timestamp: Timestamp da execução
        validation_fixes: Número de correções de validação aplicadas
        mock_fixes_applied: Número de correções de mock aplicadas
        mock_fixes_details: Detalhes das correções (dict do gerador)
        total_fixes: Total de correções aplicadas
        commit_created: Se um commit foi criado
        commit_message: Mensagem do commit (se criado)

    """

    timestamp: str
    validation_fixes: int
    mock_fixes_applied: int
    mock_fixes_details: dict[str, Any]
    total_fixes: int
    commit_created: bool = False
    commit_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serializa resultado para dicionário.

        Returns:
            Dicionário com todos os campos

        """
        return {
            "timestamp": self.timestamp,
            "validation_fixes": self.validation_fixes,
            "mock_fixes": {
                "applied": self.mock_fixes_applied,
                "details": self.mock_fixes_details,
            },
            "total_fixes": self.total_fixes,
            "commit_created": self.commit_created,
            "commit_message": self.commit_message,
        }
