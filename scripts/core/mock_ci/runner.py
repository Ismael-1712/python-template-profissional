"""Orquestrador principal da integração Mock CI/CD.

Este módulo fornece a classe MockCIRunner que coordena todos os componentes
da integração CI/CD: verificação, correção, reporting e operações git.
"""

import logging
from pathlib import Path

from scripts.core.mock_ci.checker import CIChecker
from scripts.core.mock_ci.detector import detect_ci_environment
from scripts.core.mock_ci.fixer import CIFixer
from scripts.core.mock_ci.git_ops import GitOperations
from scripts.core.mock_ci.models import CIReport, FixResult
from scripts.core.mock_ci.reporter import CIReporter
from scripts.core.mock_generator import TestMockGenerator
from scripts.core.mock_validator import TestMockValidator

logger = logging.getLogger(__name__)


class MockCIRunner:
    """Orquestrador principal da integração CI/CD.

    Coordena todos os componentes (GitOperations, CIChecker, CIFixer, CIReporter)
    e fornece interface de alto nível para operações de verificação e correção.

    Attributes:
        workspace_root: Caminho raiz do workspace
        generator: Gerador de test mocks
        validator: Validador de test mocks
        git_ops: Operações git isoladas
        ci_environment: Nome do ambiente CI/CD detectado
        checker: Verificador CI/CD (read-only)
        fixer: Corretor automático (write)
        reporter: Gerador de relatórios

    Example:
        >>> from pathlib import Path
        >>> workspace = Path.cwd()
        >>> config = workspace / "scripts" / "cli" / "test_mock_config.yaml"
        >>> runner = MockCIRunner(workspace, config)
        >>> report, exit_code = runner.check(fail_on_issues=True)
        >>> print(f"Status: {report.status}, Exit Code: {exit_code}")

    """

    def __init__(self, workspace_root: Path, config_file: Path):
        """Inicializa o orquestrador CI/CD.

        Args:
            workspace_root: Caminho raiz do workspace
            config_file: Caminho do arquivo de configuração do gerador

        Raises:
            FileNotFoundError: Se workspace_root ou config_file não existirem

        """
        self.workspace_root = workspace_root.resolve()

        if not self.workspace_root.exists():
            msg = f"Workspace não encontrado: {self.workspace_root}"
            raise FileNotFoundError(msg)

        if not config_file.exists():
            msg = f"Config do gerador não encontrado: {config_file}"
            raise FileNotFoundError(msg)

        # Componentes base
        self.generator = TestMockGenerator(self.workspace_root, config_file)
        self.validator = TestMockValidator(self.workspace_root)
        self.git_ops = GitOperations(self.workspace_root)
        self.ci_environment = detect_ci_environment()

        # Estratégias especializadas
        self.checker = CIChecker(
            self.generator,
            self.validator,
            self.ci_environment,
        )
        self.fixer = CIFixer(self.generator, self.validator, self.git_ops)
        self.reporter = CIReporter(self.workspace_root)

        logger.info(
            f"MockCIRunner inicializado - Ambiente: {self.ci_environment}",
        )

    def check(self, fail_on_issues: bool = False) -> tuple[CIReport, int]:
        """Executa verificação completa e retorna relatório + exit code.

        Este método orquestra:
        1. Coleta de informações git
        2. Verificação completa (validação + sugestões)
        3. Cálculo de status e exit code

        Args:
            fail_on_issues: Se True, retorna exit code não-zero para problemas

        Returns:
            Tupla (CIReport, exit_code) onde:
                - CIReport contém todos os resultados da verificação
                - exit_code é 0 (success), 1 (warning) ou 2 (failure)

        Example:
            >>> runner = MockCIRunner(workspace, config)
            >>> report, code = runner.check(fail_on_issues=True)
            >>> if code != 0:
            ...     print(f"Problemas encontrados: {report.status}")

        """
        logger.info("Iniciando verificação CI/CD completa...")

        # Coleta informações git
        git_info = self.git_ops.get_status()

        # Executa verificação completa
        report = self.checker.run_comprehensive_check(
            git_info,
            self.workspace_root,
        )

        # Calcula exit code
        exit_code = self._calculate_exit_code(report, fail_on_issues)

        logger.info(
            f"Verificação concluída - Status: {report.status}, Exit Code: {exit_code}",
        )

        return report, exit_code

    def fix(self, commit: bool = False) -> FixResult:
        """Aplica correções automáticas e opcionalmente faz commit.

        Este método orquestra:
        1. Aplicação de correções (validação + mocks)
        2. Commit das mudanças (se solicitado e seguro)
        3. Retorno de resultado estruturado

        Args:
            commit: Se True, faz commit das correções aplicadas

        Returns:
            FixResult com detalhes das correções aplicadas

        Example:
            >>> runner = MockCIRunner(workspace, config)
            >>> result = runner.fix(commit=True)
            >>> print(f"Correções aplicadas: {result.total_fixes}")

        """
        logger.info("Iniciando aplicação de correções automáticas...")

        result = self.fixer.auto_fix(commit=commit)

        logger.info(f"Correções concluídas - Total: {result.total_fixes}")

        return result

    def generate_report(
        self,
        report: CIReport,
        output_file: Path | None = None,
    ) -> Path:
        """Gera relatório JSON a partir de CIReport.

        Args:
            report: Relatório CI/CD a ser serializado
            output_file: Caminho de saída (opcional, gera timestamp se None)

        Returns:
            Path do arquivo de relatório gerado

        Example:
            >>> runner = MockCIRunner(workspace, config)
            >>> report, _ = runner.check()
            >>> path = runner.generate_report(report)
            >>> print(f"Relatório salvo em: {path}")

        """
        return self.reporter.generate_json_report(report, output_file)

    def print_summary(self, report: CIReport) -> None:
        """Imprime resumo formatado no console.

        Args:
            report: Relatório CI/CD a ser exibido

        Example:
            >>> runner = MockCIRunner(workspace, config)
            >>> report, _ = runner.check()
            >>> runner.print_summary(report)
            # Imprime: TEST MOCK CHECK - SUCCESS

        """
        self.reporter.print_console_summary(report)

    def _calculate_exit_code(
        self,
        report: CIReport,
        fail_on_issues: bool,
    ) -> int:
        """Calcula exit code baseado no status do relatório.

        Args:
            report: Relatório CI/CD
            fail_on_issues: Se deve retornar código não-zero para problemas

        Returns:
            Exit code: 0 (success), 1 (warning), 2 (failure)

        Logic:
            - Se fail_on_issues=False: sempre retorna 0
            - Se fail_on_issues=True:
                - FAILURE → 2
                - WARNING → 1
                - SUCCESS → 0

        """
        if not fail_on_issues:
            return 0

        if report.status == "FAILURE":
            return 2
        if report.status == "WARNING":
            return 1
        return 0

    def get_environment_info(self) -> dict[str, str]:
        """Retorna informações sobre o ambiente de execução.

        Returns:
            Dicionário com informações do ambiente

        Example:
            >>> runner = MockCIRunner(workspace, config)
            >>> info = runner.get_environment_info()
            >>> print(info["ci_environment"])
            github-actions

        """
        git_info = self.git_ops.get_status()

        return {
            "ci_environment": self.ci_environment,
            "workspace": str(self.workspace_root),
            "is_git_repo": str(git_info.is_git_repo),
            "current_branch": git_info.current_branch or "unknown",
            "commit_hash": git_info.commit_hash or "unknown",
            "has_changes": str(git_info.has_changes),
        }
