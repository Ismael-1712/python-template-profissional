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

import yaml
from pydantic import ValidationError

# Adiciona o diretório raiz do projeto ao sys.path para permitir imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.core.mock_ci import MockCIRunner  # noqa: E402
from scripts.core.mock_ci.models_pydantic import MockCIConfig  # noqa: E402
from scripts.utils.banner import print_startup_banner  # noqa: E402
from scripts.utils.logger import setup_logging  # noqa: E402

# Configurar logging centralizado para CI/CD
logger = setup_logging("ci_test_mock_integration", level=logging.INFO)


def _generate_config_template() -> str:
    """Gera template de configuração com comentários explicativos.

    Returns:
        String YAML com configuração comentada

    """
    return '''# ====================================================================
# Mock CI Configuration - Test Mock Generator
# ====================================================================
# Este arquivo configura o gerador de mocks para testes CI/CD.
# Ele detecta padrões de código que precisam de mocks e sugere/aplica
# correções automaticamente.
#
# Documentação completa: docs/guides/mock-ci-setup.md
# ====================================================================

# Versão da configuração
version: "1.0"

# ====================================================================
# PADRÕES DE MOCK DETECTÁVEIS
# ====================================================================
# Organize seus padrões por categoria para melhor manutenção.
# Cada padrão especifica:
#   - pattern: String a detectar no código (ex: "requests.get(")
#   - type: Categoria do mock (HTTP_REQUEST, SUBPROCESS, FILE_SYSTEM, DATABASE)
#   - severity: Prioridade (HIGH, MEDIUM, LOW)
#   - description: Descrição do que é detectado
#   - mock_template: Template do código de mock a aplicar
#   - required_imports: Imports necessários para o mock funcionar

mock_patterns:
  # ----------------------------------------------------------------
  # Requisições HTTP
  # ----------------------------------------------------------------
  http_patterns:
    - pattern: "requests.get("
      type: "HTTP_REQUEST"
      severity: "HIGH"
      description: "HTTP GET request - precisa de mock para estabilidade em CI"
      mock_template: |
        @patch("requests.get")
        def {func_name}(self, mock_get, *args, **kwargs):
            """Test com HTTP GET mockado."""
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "mocked"}
            mock_get.return_value = mock_response

            # Sua lógica de teste aqui
      required_imports:
        - "from unittest.mock import Mock, patch"

    - pattern: "requests.post("
      type: "HTTP_REQUEST"
      severity: "HIGH"
      description: "HTTP POST request - precisa de mock para estabilidade em CI"
      mock_template: |
        @patch("requests.post")
        def {func_name}(self, mock_post, *args, **kwargs):
            """Test com HTTP POST mockado."""
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "created"}
            mock_post.return_value = mock_response

            # Sua lógica de teste aqui
      required_imports:
        - "from unittest.mock import Mock, patch"

  # ----------------------------------------------------------------
  # Execução de Processos
  # ----------------------------------------------------------------
  subprocess_patterns:
    - pattern: "subprocess.run("
      type: "SUBPROCESS"
      severity: "HIGH"
      description: "Execução de subprocess - precisa de mock para portabilidade em CI"
      mock_template: |
        @patch("subprocess.run")
        def {func_name}(self, mock_subprocess_run, *args, **kwargs):
            """Test com subprocess mockado."""
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "mocked output"
            mock_result.stderr = ""
            mock_subprocess_run.return_value = mock_result

            # Sua lógica de teste aqui
      required_imports:
        - "from unittest.mock import Mock, patch"

  # ----------------------------------------------------------------
  # Sistema de Arquivos
  # ----------------------------------------------------------------
  filesystem_patterns:
    - pattern: "open("
      type: "FILE_SYSTEM"
      severity: "MEDIUM"
      description: "Operação de arquivo - considere mockar para isolamento de teste"
      mock_template: |
        @patch("builtins.open", new_callable=mock_open, read_data="mocked file content")
        def {func_name}(self, mock_file, *args, **kwargs):
            """Test com operações de arquivo mockadas."""
            # Sua lógica de teste aqui
      required_imports:
        - "from unittest.mock import Mock, patch, mock_open"

  # ----------------------------------------------------------------
  # Banco de Dados
  # ----------------------------------------------------------------
  database_patterns:
    - pattern: "sqlite3.connect("
      type: "DATABASE"
      severity: "HIGH"
      description: "Conexão SQLite - precisa de mock para isolamento de teste"
      mock_template: |
        @patch("sqlite3.connect")
        def {func_name}(self, mock_connect, *args, **kwargs):
            """Test com conexão SQLite mockada."""
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            mock_connect.return_value = mock_conn

            # Sua lógica de teste aqui
      required_imports:
        - "from unittest.mock import Mock, patch"

# ====================================================================
# CONFIGURAÇÕES DE EXECUÇÃO
# ====================================================================
execution:
  # Padrões glob para localizar arquivos de teste
  test_file_patterns:
    - "tests/**/*.py"
    - "test_*.py"
    - "*_test.py"

  # Padrões glob para EXCLUIR arquivos do processamento
  exclude_patterns:
    - "**/__init__.py"
    - "**/conftest.py"
    - "**/.venv/**"
    - "**/venv/**"
    - "**/.pytest_cache/**"

  # Severidade mínima para aplicar correções automáticas
  # Valores: HIGH, MEDIUM, LOW
  min_severity_for_auto_apply: "HIGH"

  # Criar backup antes de modificar arquivos?
  create_backups: true

  # Diretório para backups
  backup_directory: ".test_mock_backups"

# ====================================================================
# CONFIGURAÇÕES DE LOGGING
# ====================================================================
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# ====================================================================
# CONFIGURAÇÕES DE RELATÓRIO
# ====================================================================
reporting:
  # Incluir sugestões de baixa prioridade nos relatórios?
  include_low_priority: false

  # Máximo de sugestões a exibir no console
  max_suggestions_display: 10

  # Formato de saída: json, text, markdown
  output_format: "json"
'''


def handle_init_command(args: argparse.Namespace) -> int:
    """Manipula o comando init para scaffolding de configuração.

    Args:
        args: Argumentos parseados do CLI

    Returns:
        Código de saída (0 = sucesso, 1 = warning, 2 = erro)

    """
    workspace = args.workspace.resolve()

    # Determina caminho do arquivo de saída
    if args.output:
        output_path = args.output.resolve()
    else:
        output_path = workspace / "test_mock_config.yaml"

    # Verifica se arquivo já existe
    if output_path.exists() and not args.force:
        logger.error(
            "❌ Arquivo já existe: %s\n   Use --force para sobrescrever",
            output_path,
        )
        return 1

    # Gera configuração
    try:
        config_content = _generate_config_template()

        # Cria diretório pai se necessário
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Escreve arquivo
        with output_path.open("w", encoding="utf-8") as f:
            f.write(config_content)

        logger.info("✅ Configuração gerada com sucesso!")
        logger.info("📄 Arquivo: %s", output_path)
        logger.info("")
        logger.info("Próximos passos:")
        logger.info("  1. Revise e personalize %s", output_path.name)
        logger.info("  2. Execute: mock-ci --check")
        logger.info("  3. Aplique correções: mock-ci --auto-fix")

        return 0

    except OSError as e:
        logger.error("❌ Erro ao criar arquivo: %s", e)
        return 2
    except Exception as e:
        logger.exception("❌ Erro inesperado: %s", e)
        return 2


# TODO: Refactor God Function - split CLI logic from orchestration
def main() -> int:  # noqa: C901
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

    # Subcomandos para melhor UX
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando init
    init_parser = subparsers.add_parser(
        "init",
        help="Gerar arquivo de configuração inicial (test_mock_config.yaml)",
    )
    init_parser.add_argument(
        "--output",
        type=Path,
        help="Caminho do arquivo de saída (padrão: test_mock_config.yaml no workspace)",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescrever arquivo existente",
    )
    init_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Caminho do workspace (padrão: diretório atual)",
    )

    args = parser.parse_args()

    # Comando init - scaffolding de configuração
    if args.command == "init":
        return handle_init_command(args)

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

        # Carrega e valida configuração com Pydantic (Top-Down Injection)
        try:
            with config_file.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Validação automática via Pydantic
            config = MockCIConfig.model_validate(config_data)
            logger.info("✅ Configuração YAML validada com sucesso")

        except ValidationError as e:
            logger.error("❌ Erro de validação na configuração YAML:")
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                logger.error(f"  [{loc}]: {error['msg']}")
            return 2
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configuração: {e}")
            return 2

        # Inicializa runner com config validado
        runner = MockCIRunner(workspace, config)

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
