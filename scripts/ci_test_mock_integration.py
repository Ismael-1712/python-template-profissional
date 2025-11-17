#!/usr/bin/env python3
"""CI/CD Test Mock Integration - Integração com Pipelines CI/CD
============================================================

Script para integrar o Test Mock Generator em pipelines de CI/CD,
garantindo que todos os testes tenham mocks adequados antes do deploy.

Este script é idempotente e pode ser executado em qualquer ambiente CI/CD.

Uso em CI/CD:
    # No pipeline (GitHub Actions, GitLab CI, etc.)
    python scripts/ci_test_mock_integration.py --check --fail-on-issues

    # Para aplicar correções automaticamente
    python scripts/ci_test_mock_integration.py --auto-fix --commit

Autor: DevOps Template Generator
Versão: 1.0.0
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from test_mock_generator import TestMockGenerator
from validate_test_mocks import TestMockValidator

# Configuração de logging para CI/CD
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ci_test_mock_integration")


class CITestMockIntegration:
    """Integração do Test Mock Generator com pipelines CI/CD.

    Implementa verificações automáticas e correções para garantir
    que todos os testes tenham mocks adequados em ambiente CI/CD.
    """

    def __init__(self, workspace_root: Path):
        """Inicializa a integração CI/CD.

        Args:
            workspace_root: Caminho raiz do workspace

        """
        self.workspace_root = workspace_root.resolve()

        # --- INÍCIO DA CORREÇÃO ---
        # Localiza o arquivo de config, que está no mesmo diretório deste script
        script_dir = Path(__file__).parent
        config_file = script_dir / "test_mock_config.yaml"

        if not config_file.exists():
            logger.error(f"Config do gerador não encontrado: {config_file}")
            raise FileNotFoundError(f"Config do gerador não encontrado: {config_file}")

        self.generator = TestMockGenerator(workspace_root, config_file)  # <-- CORRIGIDO
        self.validator = TestMockValidator(
            workspace_root,
        )  # <-- OK (Corrigido na Etapa 31)
        # --- FIM DA CORREÇÃO ---

        self.ci_environment = self._detect_ci_environment()

        logger.info(f"CI/CD Integration iniciada - Ambiente: {self.ci_environment}")

    def _detect_ci_environment(self) -> str:
        """Detecta o ambiente CI/CD atual.

        Returns:
            Nome do ambiente CI/CD detectado

        """
        ci_environments = {
            "GITHUB_ACTIONS": "github-actions",
            "GITLAB_CI": "gitlab-ci",
            "JENKINS_URL": "jenkins",
            "TRAVIS": "travis-ci",
            "CIRCLECI": "circle-ci",
            "AZURE_DEVOPS": "azure-devops",
            "CI": "generic-ci",
        }

        for env_var, ci_name in ci_environments.items():
            if os.getenv(env_var):
                return ci_name

        return "local"

    def _run_git_command(self, command: list[str]) -> tuple[bool, str]:
        """Executa comando git de forma segura.

        Args:
            command: Lista com comando git

        Returns:
            Tupla (sucesso, output)

        """
        try:
            result = subprocess.run(  # noqa: subprocess
                command,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=False,
            )

            return result.returncode == 0, result.stdout.strip()

        except Exception as e:
            logger.error(f"Erro ao executar comando git: {e}")
            return False, str(e)

    def check_git_status(self) -> dict[str, any]:
        """Verifica status do repositório git.

        Returns:
            Dicionário com informações do git

        """
        info = {
            "is_git_repo": False,
            "has_changes": False,
            "current_branch": None,
            "commit_hash": None,
        }

        # Verifica se é repositório git
        success, _ = self._run_git_command(["git", "status", "--porcelain"])
        if not success:
            return info

        info["is_git_repo"] = True

        # Verifica mudanças pendentes
        success, output = self._run_git_command(["git", "status", "--porcelain"])
        if success:
            info["has_changes"] = bool(output.strip())

        # Branch atual
        success, branch = self._run_git_command(["git", "branch", "--show-current"])
        if success:
            info["current_branch"] = branch

        # Hash do commit atual
        success, commit = self._run_git_command(["git", "rev-parse", "HEAD"])
        if success:
            info["commit_hash"] = commit[:8]

        return info

    def run_comprehensive_check(self) -> dict[str, any]:
        """Executa verificação abrangente para CI/CD.

        Returns:
            Relatório completo das verificações

        """
        logger.info("Executando verificação abrangente para CI/CD...")

        # Informações do ambiente
        git_info = self.check_git_status()

        # Validação básica
        validation_results = self.validator.run_full_validation()

        # Geração de sugestões
        report = self.generator.scan_test_files()

        # Análise de criticidade
        critical_issues = [s for s in report["suggestions"] if s["severity"] == "HIGH"]

        blocking_issues = [
            s
            for s in critical_issues
            if s["mock_type"] in ["HTTP_REQUEST", "SUBPROCESS"]
        ]

        # Relatório final
        ci_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": self.ci_environment,
            "workspace": str(self.workspace_root),
            "git_info": git_info,
            "validation_results": validation_results,
            "mock_suggestions": {
                "total": len(report["suggestions"]),
                "high_priority": len(critical_issues),
                "blocking": len(blocking_issues),
                "details": report["suggestions"],
            },
            "summary": report["summary"],
            "recommendations": self._generate_recommendations(
                validation_results,
                critical_issues,
                blocking_issues,
            ),
            "status": self._determine_overall_status(
                validation_results,
                critical_issues,
                blocking_issues,
            ),
        }

        logger.info(f"Verificação concluída - Status: {ci_report['status']}")

        return ci_report

    def _generate_recommendations(
        self,
        validation_results: dict[str, bool],
        critical_issues: list[dict],
        blocking_issues: list[dict],
    ) -> list[str]:
        """Gera recomendações baseadas nos resultados.

        Returns:
            Lista de recomendações

        """
        recommendations = []

        # Validações falharam
        failed_validations = [k for k, v in validation_results.items() if not v]
        if failed_validations:
            recommendations.append(
                f"Corrigir validações falharam: {', '.join(failed_validations)}",
            )

        # Issues críticos
        if critical_issues:
            num_issues = len(critical_issues)
            msg = f"Aplicar mocks para {num_issues} problemas de alta prioridade"
            recommendations.append(msg)

        # Issues bloqueadores
        if blocking_issues:
            recommendations.append(
                f"URGENTE: {len(blocking_issues)} problemas podem quebrar CI/CD",
            )
            recommendations.append(
                "Execute: python scripts/test_mock_generator.py --apply",
            )

        # Sem problemas
        if not critical_issues and all(validation_results.values()):
            recommendations.append("✅ Tudo OK - prosseguir com pipeline")

        return recommendations

    def _determine_overall_status(
        self,
        validation_results: dict[str, bool],
        critical_issues: list[dict],
        blocking_issues: list[dict],
    ) -> str:
        """Determina status geral da verificação.

        Returns:
            Status: SUCCESS, WARNING, ou FAILURE

        """
        # Falha se validações básicas falharam
        if not all(validation_results.values()):
            return "FAILURE"

        # Falha se há problemas bloqueadores
        if blocking_issues:
            return "FAILURE"

        # Warning se há problemas críticos
        if critical_issues:
            return "WARNING"

        return "SUCCESS"

    def auto_fix_issues(self, commit: bool = False) -> dict[str, any]:
        """Aplica correções automáticas para problemas encontrados.

        Args:
            commit: Se True, faz commit das correções

        Returns:
            Relatório das correções aplicadas

        """
        logger.info("Aplicando correções automáticas...")

        # Verifica se é safe aplicar correções
        git_info = self.check_git_status()
        if not git_info["is_git_repo"] and commit:
            logger.warning("Não é repositório git - commit desabilitado")
            commit = False

        # Corrige problemas básicos
        validation_fixes = self.validator.fix_common_issues()

        # Aplica sugestões de mock
        mock_result = self.generator.apply_suggestions(dry_run=False)

        # Resultado consolidado
        fix_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_fixes": validation_fixes,
            "mock_fixes": mock_result,
            "total_fixes": validation_fixes + mock_result["applied"],
            "commit_created": False,
        }

        # Commit das mudanças se solicitado
        if commit and git_info["is_git_repo"] and fix_result["total_fixes"] > 0:
            commit_success = self._commit_fixes(fix_result)
            fix_result["commit_created"] = commit_success

        logger.info(f"Correções aplicadas: {fix_result['total_fixes']} total")

        return fix_result

    def _commit_fixes(self, fix_result: dict[str, any]) -> bool:
        """Faz commit das correções aplicadas.

        Args:
            fix_result: Resultado das correções

        Returns:
            True se commit foi bem-sucedido

        """
        try:
            # Adiciona arquivos modificados
            success, _ = self._run_git_command(["git", "add", "."])
            if not success:
                logger.error("Erro ao adicionar arquivos ao git")
                return False

            # Cria commit
            commit_message = (
                f"feat(tests): Auto-fix test mocks via CI/CD\n\n"
                f"- Applied {fix_result['mock_fixes']['applied']} mock fixes\n"
                f"- Fixed {fix_result['validation_fixes']} validation issues\n"
                f"- Generated by: CI Test Mock Integration"
            )

            success, _ = self._run_git_command(["git", "commit", "-m", commit_message])

            if success:
                logger.info("Commit de correções criado com sucesso")
                return True
            logger.warning("Nenhuma mudança para commit")
            return False

        except Exception as e:
            logger.error(f"Erro ao fazer commit: {e}")
            return False

    def generate_ci_report(
        self,
        report_data: dict[str, any],
        output_file: Path | None = None,
    ) -> Path:
        """Gera relatório formatado para CI/CD.

        Args:
            report_data: Dados do relatório
            output_file: Arquivo de saída (opcional)

        Returns:
            Caminho do arquivo de relatório

        """
        if output_file is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = self.workspace_root / f"ci_test_mock_report_{timestamp}.json"

        # Salva relatório JSON
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        # Gera resumo para logs do CI
        self._print_ci_summary(report_data)

        logger.info(f"Relatório CI/CD gerado: {output_file}")
        return output_file

    def _print_ci_summary(self, report_data: dict[str, any]) -> None:
        """Imprime resumo formatado para logs do CI/CD.

        Args:
            report_data: Dados do relatório

        """
        status = report_data["status"]

        # Header baseado no status
        if status == "SUCCESS":
            header = "✅ TEST MOCK CHECK - SUCCESS"
        elif status == "WARNING":
            header = "⚠️  TEST MOCK CHECK - WARNING"
        else:
            header = "❌ TEST MOCK CHECK - FAILURE"

        print(f"\n{header}")
        print("=" * len(header))

        # Estatísticas
        mock_stats = report_data["mock_suggestions"]
        total = mock_stats["total"]
        high_priority = mock_stats["high_priority"]
        print(f"📊 Mock Suggestions: {total} total, {high_priority} high priority")

        if mock_stats["blocking"]:
            print(f"🚫 Blocking Issues: {mock_stats['blocking']} (may break CI/CD)")

        # Recomendações
        if report_data["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in report_data["recommendations"]:
                print(f"   • {rec}")

        # Set exit code baseado no status
        if status == "FAILURE":
            print("\n❌ Pipeline should FAIL - critical issues found")
        elif status == "WARNING":
            print("\n⚠️  Pipeline can continue with warnings")
        else:
            print("\n✅ Pipeline can continue - no issues found")


def main() -> int:
    """Função principal CLI para integração CI/CD.

    Returns:
        Código de saída (0 = sucesso, 1 = warning, 2 = failure)

    """
    parser = argparse.ArgumentParser(
        description="CI/CD Test Mock Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso em CI/CD:
  %(prog)s --check --fail-on-issues      # Verificar e falhar se problemas
  %(prog)s --auto-fix --commit           # Aplicar correções e commitar
  %(prog)s --check --report ci-report.json  # Gerar relatório JSON
        """,
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Executar verificação abrangente",
    )

    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Aplicar correções automáticas",
    )

    parser.add_argument(
        "--commit",
        action="store_true",
        help="Fazer commit das correções (usar com --auto-fix)",
    )

    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Falhar pipeline se problemas críticos encontrados",
    )

    parser.add_argument(
        "--report",
        type=Path,
        help="Gerar relatório JSON no arquivo especificado",
    )

    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Caminho do workspace (padrão: diretório atual)",
    )

    args = parser.parse_args()

    try:
        # Inicializa integração
        workspace = args.workspace.resolve()
        if not workspace.exists():
            logger.error(f"Workspace não encontrado: {workspace}")
            return 2

        integration = CITestMockIntegration(workspace)

        # Executa ações solicitadas
        if args.check:
            report = integration.run_comprehensive_check()

            # Gera relatório se solicitado
            if args.report:
                integration.generate_ci_report(report, args.report)
            else:
                integration.generate_ci_report(report)

            # Determina código de saída
            if args.fail_on_issues:
                if report["status"] == "FAILURE":
                    return 2
                if report["status"] == "WARNING":
                    return 1

        if args.auto_fix:
            fix_result = integration.auto_fix_issues(commit=args.commit)

            if fix_result["total_fixes"] > 0:
                fixes = fix_result["total_fixes"]
                print(f"✅ {fixes} problemas corrigidos automaticamente")
            else:
                print("ℹ️  Nenhuma correção necessária")

        return 0

    except KeyboardInterrupt:
        logger.info("Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
