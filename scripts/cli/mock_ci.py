#!/usr/bin/env python3
"""CI/CD Test Mock Integration - Integração com Pipelines CI/CD.

============================================================

Script para integrar o Test Mock Generator em pipelines de CI/CD,
garantindo que todos os testes tenham mocks adequados antes do deploy.

Este script é idempotente e pode ser executado em qualquer ambiente CI/CD.

Uso em CI/CD:
    # No pipeline (GitHub Actions, GitLab CI, etc.)
    python scripts/cli/mock_ci.py --check --fail-on-issues

    # Para aplicar correções automaticamente
    python scripts/cli/mock_ci.py --auto-fix --commit

Autor: DevOps Template Generator
Versão: 2.0.0 (Refatorado)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao sys.path para permitir imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.core.mock_ci import MockCIRunner  # noqa: E402
from scripts.utils.banner import print_startup_banner  # noqa: E402

# Configuração de logging para CI/CD
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ci_test_mock_integration")


def main() -> int:
    """Função principal CLI para integração CI/CD.

    Returns:
        Código de saída (0 = sucesso, 1 = warning, 2 = failure)

    """
    # Banner de inicialização
    print_startup_banner(
        tool_name="CI/CD Mock Integration",
        version="2.0.0",
        description="Test Mock Validation and Auto-Fix for CI/CD Pipelines",
        script_path=Path(__file__),
    )

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
        # Valida workspace
        workspace = args.workspace.resolve()
        if not workspace.exists():
            logger.error("Workspace não encontrado: %s", workspace)
            return 2

        # Localiza arquivo de configuração
        config_file = workspace / "scripts" / "test_mock_config.yaml"
        if not config_file.exists():
            logger.error("Config do gerador não encontrado: %s", config_file)
            return 2

        # Inicializa runner
        runner = MockCIRunner(workspace, config_file)

        # Código de saída padrão
        exit_code = 0

        # Executa verificação se solicitado
        if args.check:
            report, exit_code = runner.check(fail_on_issues=args.fail_on_issues)

            # Gera relatório se solicitado
            if args.report:
                runner.generate_report(report, args.report)
            else:
                runner.generate_report(report)

            # Imprime resumo no console
            runner.print_summary(report)

        # Executa correção se solicitado
        if args.auto_fix:
            fix_result = runner.fix(commit=args.commit)

            if fix_result.total_fixes > 0:
                print(f"✅ {fix_result.total_fixes} problemas corrigidos")
            else:
                print("ℹ️  Nenhuma correção necessária")

        return exit_code

    except KeyboardInterrupt:
        logger.info("Operação cancelada pelo usuário")
        return 1
    except FileNotFoundError as e:
        logger.error("Arquivo não encontrado: %s", e)
        return 2
    except Exception as e:
        logger.exception("Erro inesperado: %s", e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
