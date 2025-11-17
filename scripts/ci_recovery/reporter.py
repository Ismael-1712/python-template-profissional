#!/usr/bin/env python3

"""Módulo Reporter (Geração e Persistência de Relatórios) SRE.

(Extraído do monólito P8.5)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from scripts.ci_recovery.models import RecoveryReport, RiskLevel

# Inicializa o logger para este módulo
logger = logging.getLogger(__name__)


def generate_recovery_suggestions(report: RecoveryReport) -> list[str]:
    """Gera sugestões de recuperação acionáveis com base na análise.

    (Função refatorada S.O.L.I.D. - dependência 'self' injetada)
    """
    suggestions = []

    if not report.file_analysis:
        return ["Run file analysis first"]

    risk = report.file_analysis.overall_risk

    if risk == RiskLevel.CRITICAL:
        suggestions.extend(
            [
                "Review critical infrastructure changes carefully",
                "Test in isolated environment before deployment",
                "Consider rolling back changes if CI continues to fail",
            ],
        )

    if risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        suggestions.extend(
            [
                "Run full test suite locally before pushing",
                "Check for missing dependencies or configuration",
                "Verify environment variables are set correctly",
            ],
        )

    # Adiciona sugestões específicas com base nos tipos de arquivo
    if report.file_analysis.high_risk:
        test_files = [f for f in report.file_analysis.high_risk if "test" in f.lower()]
        if test_files:
            suggestions.append(
                "Review test changes - ensure mocks and fixtures are correct",
            )

    if not suggestions:
        suggestions.append(
            "No specific issues detected - CI failure may be transient",
        )

    return suggestions


def save_report(
    report: RecoveryReport,
    repository_path: Path,
    commit_hash: str,
) -> Path:
    """Salva o relatório de recuperação em um arquivo JSON.

    (Função refatorada S.O.L.I.D. - dependências 'self' injetadas)
    """
    report_file = (
        repository_path / f"ci_recovery_report_{commit_hash}_"
        f"{int(datetime.now(timezone.utc).timestamp())}.json"
    )

    try:
        # Converte dataclass para dict para serialização JSON
        report_dict = {
            "timestamp": report.timestamp.isoformat(),
            "commit_hash": report.commit_hash,
            "repository_path": str(report.repository_path),
            "steps": [
                {
                    "name": step.name,
                    "status": step.status.value,
                    "timestamp": step.timestamp.isoformat(),
                    "details": step.details,
                    "error_message": step.error_message,
                    "duration_seconds": step.duration_seconds,
                }
                for step in report.steps
            ],
            "file_analysis": {
                "low_risk": report.file_analysis.low_risk
                if report.file_analysis
                else [],
                "medium_risk": report.file_analysis.medium_risk
                if report.file_analysis
                else [],
                "high_risk": report.file_analysis.high_risk
                if report.file_analysis
                else [],
                "critical_risk": report.file_analysis.critical_risk
                if report.file_analysis
                else [],
                "overall_risk": report.file_analysis.overall_risk.value
                if report.file_analysis
                else "low",
            }
            if report.file_analysis
            else None,
            "fixes_applied": report.fixes_applied,
            "final_status": report.final_status.value,
            "total_duration_seconds": report.total_duration_seconds,
            "metadata": report.metadata,
        }

        with report_file.open("w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

    except Exception:
        logger.exception("Failed to save recovery report")
        raise
    else:
        logger.info("Recovery report saved to: %s", report_file)
        return report_file
