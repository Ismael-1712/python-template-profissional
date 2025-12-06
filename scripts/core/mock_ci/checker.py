"""Verificação de testes e mocks em ambientes CI/CD (Read-Only).

Este módulo contém a lógica de verificação e análise de testes sem fazer
modificações no código.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.core.mock_ci.config import BLOCKING_MOCK_TYPES, determine_status
from scripts.core.mock_ci.models import CIReport, GitInfo, MockSuggestions
from scripts.core.mock_generator import TestMockGenerator
from scripts.core.mock_validator import TestMockValidator

logger = logging.getLogger(__name__)


class CIChecker:
    """Responsável por verificações read-only em CI/CD.

    Esta classe orquestra a verificação de testes e mocks sem fazer
    modificações, apenas analisando e reportando problemas.

    Attributes:
        generator: Gerador de mocks para análise
        validator: Validador de mocks
        ci_environment: Nome do ambiente CI/CD

    """

    def __init__(
        self,
        generator: TestMockGenerator,
        validator: TestMockValidator,
        ci_environment: str,
    ) -> None:
        """Inicializa o verificador CI/CD.

        Args:
            generator: Instância do gerador de mocks
            validator: Instância do validador de mocks
            ci_environment: Nome do ambiente CI/CD (ex: "github-actions")

        """
        self.generator = generator
        self.validator = validator
        self.ci_environment = ci_environment

    def run_comprehensive_check(
        self,
        git_info: GitInfo,
        workspace_root: Path,
    ) -> CIReport:
        """Executa verificação abrangente para CI/CD.

        Esta é a função principal que orquestra todas as verificações:
        validação de estrutura, análise de sugestões de mock e classificação
        de problemas por severidade.

        Args:
            git_info: Informações do repositório git
            workspace_root: Caminho raiz do workspace

        Returns:
            CIReport com todos os resultados da verificação

        Example:
            >>> checker = CIChecker(generator, validator, "github-actions")
            >>> report = checker.run_comprehensive_check(git_info, Path("/project"))
            >>> print(report.status)  # SUCCESS, WARNING, ou FAILURE

        """
        logger.info("Executando verificação abrangente para CI/CD...")

        # Validação básica de estrutura
        validation_results = self.validator.run_full_validation()

        # Geração de sugestões de mock
        generator_report = self.generator.scan_test_files()

        # Análise de criticidade
        critical_issues, blocking_issues = self._classify_issues(
            generator_report["suggestions"],
        )

        # Monta estrutura de sugestões
        mock_suggestions = MockSuggestions.from_suggestions_list(
            generator_report["suggestions"],
            BLOCKING_MOCK_TYPES,
        )

        # Gera recomendações
        recommendations = self._generate_recommendations(
            validation_results,
            critical_issues,
            blocking_issues,
        )

        # Determina status geral
        status = determine_status(
            validation_results,
            len(critical_issues),
            len(blocking_issues),
        )

        # Monta relatório final
        report = CIReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            environment=self.ci_environment,
            workspace=str(workspace_root),
            git_info=git_info,
            validation_results=validation_results,
            mock_suggestions=mock_suggestions,
            summary=generator_report.get("summary", {}),
            recommendations=recommendations,
            status=status,
        )

        logger.info("Verificação concluída - Status: %s", status)
        return report

    def _classify_issues(
        self,
        suggestions: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Classifica sugestões em críticas e bloqueadoras.

        Args:
            suggestions: Lista de sugestões do gerador

        Returns:
            Tupla (críticas, bloqueadoras):
                - críticas: Sugestões com severity=HIGH
                - bloqueadoras: Críticas que podem quebrar CI/CD

        Example:
            >>> critical, blocking = checker._classify_issues(suggestions)
            >>> print(f"Críticos: {len(critical)}, Bloqueadores: {len(blocking)}")

        """
        # Filtra por severidade alta
        critical_issues = [s for s in suggestions if s.get("severity") == "HIGH"]

        # Filtra bloqueadores (tipos que podem quebrar CI/CD)
        blocking_issues = [
            s for s in critical_issues if s.get("mock_type") in BLOCKING_MOCK_TYPES
        ]

        return critical_issues, blocking_issues

    def _generate_recommendations(
        self,
        validation_results: dict[str, bool],
        critical_issues: list[dict[str, Any]],
        blocking_issues: list[dict[str, Any]],
    ) -> list[str]:
        """Gera recomendações baseadas nos resultados da verificação.

        Args:
            validation_results: Resultados de validações básicas
            critical_issues: Lista de issues críticos
            blocking_issues: Lista de issues bloqueadores

        Returns:
            Lista de recomendações textuais para o usuário

        Example:
            >>> recommendations = checker._generate_recommendations(
            ...     {"has_tests": True, "has_mocks": False},
            ...     critical_issues,
            ...     blocking_issues
            ... )
            >>> for rec in recommendations:
            ...     print(f"- {rec}")

        """
        recommendations = []

        # Validações falharam
        failed_validations = [k for k, v in validation_results.items() if not v]
        if failed_validations:
            msg = f"Corrigir validações: {', '.join(failed_validations)}"
            recommendations.append(msg)

        # Issues críticos
        if critical_issues:
            num_issues = len(critical_issues)
            msg = f"Aplicar mocks para {num_issues} problemas de alta prioridade"
            recommendations.append(msg)

        # Issues bloqueadores (mais urgente)
        if blocking_issues:
            num_blocking = len(blocking_issues)
            recommendations.append(
                f"🚫 URGENTE: {num_blocking} problemas podem quebrar CI/CD",
            )
            recommendations.append(
                "Execute: python scripts/test_mock_generator.py --apply",
            )

        # Sem problemas - tudo OK!
        if not critical_issues and all(validation_results.values()):
            recommendations.append("✅ Tudo OK - prosseguir com pipeline")

        return recommendations
