"""Mock CI - Integração de Test Mocks com Pipelines CI/CD.

Este módulo fornece ferramentas para integrar geração e validação de test mocks
em pipelines CI/CD, garantindo que todos os testes tenham mocks adequados antes
do deploy.

Exports principais:
    - MockCIRunner: Orquestrador principal da integração CI/CD
    - GitOperations: Operações git isoladas e testáveis
    - CIChecker: Lógica de verificação (read-only)
    - CIFixer: Aplicação de correções automáticas
    - CIReporter: Geração de relatórios
    - Models: GitInfo, MockSuggestion, CIReport
    - Enums: Severity, MockType, CIStatus
"""

from scripts.core.mock_ci.checker import CIChecker
from scripts.core.mock_ci.detector import detect_ci_environment
from scripts.core.mock_ci.fixer import CIFixer
from scripts.core.mock_ci.git_ops import GitOperations
from scripts.core.mock_ci.models import (
    CIReport,
    CIStatus,
    FixResult,
    GitInfo,
    MockSuggestion,
    MockSuggestions,
    MockType,
    Severity,
)
from scripts.core.mock_ci.reporter import CIReporter
from scripts.core.mock_ci.runner import MockCIRunner

__all__ = [
    # Classes principais
    "CIChecker",
    "CIFixer",
    "CIReporter",
    "GitOperations",
    "MockCIRunner",
    # Modelos (ordem alfabética)
    "CIReport",
    "CIStatus",
    "FixResult",
    "GitInfo",
    "MockSuggestion",
    "MockSuggestions",
    "MockType",
    "Severity",
    # Funções utilitárias
    "detect_ci_environment",
]

__version__ = "1.0.0"
