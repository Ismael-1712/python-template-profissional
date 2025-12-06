"""Geração de relatórios CI/CD em múltiplos formatos.

Este módulo fornece funcionalidades para gerar relatórios de verificação
em formato JSON (para parsing) e console (para visualização humana).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from scripts.core.mock_ci.config import REPORT_INDENT, get_report_filename
from scripts.core.mock_ci.models import CIReport

logger = logging.getLogger(__name__)


class CIReporter:
    """Gera relatórios em diferentes formatos.

    Esta classe centraliza toda a lógica de geração de relatórios,
    tanto para arquivos JSON quanto para output de console formatado.

    Attributes:
        workspace_root: Diretório raiz do workspace

    """

    def __init__(self, workspace_root: Path) -> None:
        """Inicializa o gerador de relatórios.

        Args:
            workspace_root: Caminho raiz do workspace

        """
        self.workspace_root = workspace_root.resolve()

    def generate_json_report(
        self,
        report: CIReport,
        output_file: Path | None = None,
    ) -> Path:
        """Gera relatório formatado em JSON.

        Salva o relatório completo em formato JSON, adequado para parsing
        por ferramentas de CI/CD ou análise posterior.

        Args:
            report: Relatório a ser serializado
            output_file: Caminho do arquivo de saída (opcional)

        Returns:
            Path do arquivo criado

        Example:
            >>> reporter = CIReporter(Path("/project"))
            >>> report_path = reporter.generate_json_report(report)
            >>> print(f"Relatório salvo em: {report_path}")

        """
        # Gera nome de arquivo se não fornecido
        if output_file is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = get_report_filename(self.workspace_root, timestamp)

        # Serializa relatório
        report_data = report.to_dict()

        # Salva arquivo JSON
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=REPORT_INDENT, ensure_ascii=False)

        logger.info("Relatório CI/CD gerado: %s", output_file)
        return output_file

    def print_console_summary(self, report: CIReport) -> None:
        """Imprime resumo formatado para logs do CI/CD.

        Gera output colorido e formatado para visualização direta nos logs
        de pipelines CI/CD (GitHub Actions, GitLab CI, etc.).

        Args:
            report: Relatório a ser exibido

        Example:
            >>> reporter = CIReporter(Path("/project"))
            >>> reporter.print_console_summary(report)
            ✅ TEST MOCK CHECK - SUCCESS
            ========================================
            📊 Mock Suggestions: 5 total, 2 high priority
            💡 Recommendations:
               • Apply mocks for 2 high priority issues

        """
        status = report.status

        # Header baseado no status
        if status == "SUCCESS":
            header = "✅ TEST MOCK CHECK - SUCCESS"
        elif status == "WARNING":
            header = "⚠️  TEST MOCK CHECK - WARNING"
        else:
            header = "❌ TEST MOCK CHECK - FAILURE"

        print(f"\n{header}")
        print("=" * len(header))

        # Estatísticas de mock suggestions
        mock_stats = report.mock_suggestions
        print(
            f"📊 Mock Suggestions: {mock_stats.total} total, "
            f"{mock_stats.high_priority} high priority",
        )

        if mock_stats.blocking > 0:
            print(
                f"🚫 Blocking Issues: {mock_stats.blocking} (may break CI/CD)",
            )

        # Recomendações
        if report.recommendations:
            print("\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"   • {rec}")

        # Mensagem final baseada no status
        print()
        if status == "FAILURE":
            print("❌ Pipeline should FAIL - critical issues found")
        elif status == "WARNING":
            print("⚠️  Pipeline can continue with warnings")
        else:
            print("✅ Pipeline can continue - no issues found")

    def print_fix_summary(
        self,
        total_fixes: int,
        commit_created: bool = False,
    ) -> None:
        """Imprime resumo de correções aplicadas.

        Args:
            total_fixes: Número total de correções aplicadas
            commit_created: Se um commit foi criado

        Example:
            >>> reporter = CIReporter(Path("/project"))
            >>> reporter.print_fix_summary(7, commit_created=True)
            ✅ 7 problemas corrigidos automaticamente
            📝 Commit criado com as correções

        """
        if total_fixes > 0:
            print(f"✅ {total_fixes} problemas corrigidos automaticamente")
            if commit_created:
                print("📝 Commit criado com as correções")
        else:
            print("ℹ️  Nenhuma correção necessária")
