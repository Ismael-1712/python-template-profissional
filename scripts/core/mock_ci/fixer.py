"""Aplicação de correções automáticas em testes e mocks.

Este módulo contém a lógica para aplicar correções automaticamente,
incluindo geração de mocks e commits.
"""

import logging
from datetime import datetime, timezone

from scripts.core.mock_ci.git_ops import GitOperations
from scripts.core.mock_ci.models import FixResult, GitInfo
from scripts.core.mock_generator import TestMockGenerator
from scripts.core.mock_validator import TestMockValidator

logger = logging.getLogger(__name__)


class CIFixer:
    """Responsável por aplicar correções automáticas.

    Esta classe encapsula toda a lógica de modificação: aplicar mocks,
    corrigir problemas de validação e criar commits automáticos.

    Attributes:
        generator: Gerador de mocks
        validator: Validador de mocks
        git_ops: Operações git

    """

    def __init__(
        self,
        generator: TestMockGenerator,
        validator: TestMockValidator,
        git_ops: GitOperations,
    ) -> None:
        """Inicializa o aplicador de correções.

        Args:
            generator: Instância do gerador de mocks
            validator: Instância do validador de mocks
            git_ops: Instância de operações git

        """
        self.generator = generator
        self.validator = validator
        self.git_ops = git_ops

    def auto_fix(self, commit: bool = False) -> FixResult:
        """Aplica correções automáticas para problemas encontrados.

        Executa a sequência completa de correções:
        1. Valida ambiente (git repo)
        2. Corrige problemas de validação
        3. Aplica sugestões de mock
        4. Opcionalmente faz commit das mudanças

        Args:
            commit: Se True, faz commit das correções

        Returns:
            FixResult com detalhes de todas as correções aplicadas

        Example:
            >>> fixer = CIFixer(generator, validator, git_ops)
            >>> result = fixer.auto_fix(commit=True)
            >>> print(f"Total de correções: {result.total_fixes}")
            >>> if result.commit_created:
            ...     print(f"Commit: {result.commit_message}")

        """
        logger.info("Aplicando correções automáticas...")

        # Verifica status do git
        git_info = self.git_ops.get_status()

        # Valida se é safe fazer commit
        should_commit = self._should_commit(commit, git_info)
        if commit and not should_commit:
            logger.warning("Commit desabilitado - não é repositório git")

        # 1. Corrige problemas de validação
        validation_fixes = self.validator.fix_common_issues()
        logger.info("Correções de validação aplicadas: %s", validation_fixes)

        # 2. Aplica sugestões de mock
        mock_result = self.generator.apply_suggestions(dry_run=False)
        mock_fixes_applied = mock_result.get("applied", 0)
        logger.info("Correções de mock aplicadas: %s", mock_fixes_applied)

        # 3. Consolida resultado
        timestamp = datetime.now(timezone.utc).isoformat()
        total_fixes = validation_fixes + mock_fixes_applied

        result = FixResult(
            timestamp=timestamp,
            validation_fixes=validation_fixes,
            mock_fixes_applied=mock_fixes_applied,
            mock_fixes_details=mock_result,
            total_fixes=total_fixes,
            commit_created=False,
            commit_message=None,
        )

        # 4. Faz commit se solicitado e há correções
        if should_commit and total_fixes > 0:
            commit_success = self.git_ops.commit_fixes(
                mock_fixes=mock_fixes_applied,
                validation_fixes=validation_fixes,
            )

            if commit_success:
                result.commit_created = True
                # Captura mensagem de commit do último commit
                success, message = self.git_ops.run_command(
                    ["git", "log", "-1", "--pretty=%B"],
                )
                if success:
                    result.commit_message = message

        logger.info("Correções aplicadas: %s total", total_fixes)
        return result

    def _should_commit(self, commit: bool, git_info: GitInfo) -> bool:
        """Verifica se é seguro fazer commit.

        Args:
            commit: Flag de commit solicitado pelo usuário
            git_info: Informações do repositório

        Returns:
            True se deve fazer commit (safe to commit)

        Example:
            >>> should = fixer._should_commit(True, git_info)
            >>> if should:
            ...     print("Safe to commit")

        """
        # Usuário não solicitou commit ou não é repositório git
        return commit and git_info.is_git_repo
