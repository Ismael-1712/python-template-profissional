"""Operações Git isoladas e testáveis.

Este módulo encapsula todas as operações relacionadas ao Git em uma classe
dedicada, facilitando testes e manutenção.
"""

import logging
import subprocess
from pathlib import Path

from scripts.core.mock_ci.config import format_commit_message
from scripts.core.mock_ci.models import GitInfo

logger = logging.getLogger(__name__)


class GitOperations:
    """Encapsula operações git de forma segura e testável.

    Esta classe fornece uma interface limpa para operações git comuns,
    com tratamento de erros e logging apropriado.

    Attributes:
        workspace_root: Diretório raiz do workspace/repositório

    """

    def __init__(self, workspace_root: Path):
        """Inicializa as operações Git.

        Args:
            workspace_root: Caminho raiz do workspace

        """
        self.workspace_root = workspace_root.resolve()

    def run_command(self, command: list[str]) -> tuple[bool, str]:
        """Executa comando git de forma segura.

        Args:
            command: Lista com comando git e argumentos

        Returns:
            Tupla (sucesso, output):
                - sucesso: True se comando executou sem erros
                - output: Saída stdout do comando (vazia em caso de erro)

        Example:
            >>> git_ops = GitOperations(Path("/project"))
            >>> success, branch = git_ops.run_command(
            ...     ["git", "branch", "--show-current"]
            ... )
            >>> if success:
            ...     print(f"Branch atual: {branch}")

        Security:
            - Usa shell=False para prevenir shell injection
            - Valida que comando inicia com "git"

        """
        # Security check: comando deve começar com "git"
        if not command or command[0] != "git":
            logger.error("Comando inválido: deve começar com 'git'")
            return False, ""

        try:
            result = subprocess.run(  # nosec # noqa: subprocess
                command,
                cwd=self.workspace_root,
                shell=False,  # Security: prevent shell injection
                capture_output=True,
                text=True,
                check=False,
            )

            success = result.returncode == 0
            output = result.stdout.strip() if success else ""

            if not success and result.stderr:
                logger.debug(f"Git command stderr: {result.stderr.strip()}")

            return success, output

        except Exception as e:
            logger.error(f"Erro ao executar comando git: {e}")
            return False, ""

    def get_status(self) -> GitInfo:
        """Coleta informações completas do repositório git.

        Verifica se o diretório é um repositório git válido e coleta
        informações sobre o estado atual: branch, commit hash, mudanças
        pendentes, etc.

        Returns:
            GitInfo com todas as informações coletadas. Se não for um
            repositório git, retorna GitInfo com is_git_repo=False.

        Example:
            >>> git_ops = GitOperations(Path("/project"))
            >>> info = git_ops.get_status()
            >>> if info.is_git_repo:
            ...     print(f"Branch: {info.current_branch}")
            ...     print(f"Commit: {info.commit_hash}")

        """
        info = GitInfo()

        # Verifica se é repositório git
        success, _ = self.run_command(["git", "status", "--porcelain"])
        if not success:
            return info

        info.is_git_repo = True

        # Verifica mudanças pendentes
        success, output = self.run_command(["git", "status", "--porcelain"])
        if success:
            info.has_changes = bool(output.strip())

        # Branch atual
        success, branch = self.run_command(["git", "branch", "--show-current"])
        if success and branch:
            info.current_branch = branch

        # Hash do commit atual (8 primeiros caracteres)
        success, commit = self.run_command(["git", "rev-parse", "HEAD"])
        if success and commit:
            info.commit_hash = commit[:8]

        return info

    def add_all(self) -> bool:
        """Adiciona todos os arquivos modificados ao staging.

        Returns:
            True se arquivos foram adicionados com sucesso

        Example:
            >>> git_ops = GitOperations(Path("/project"))
            >>> if git_ops.add_all():
            ...     print("Arquivos adicionados ao staging")

        """
        success, _ = self.run_command(["git", "add", "."])
        if not success:
            logger.error("Erro ao adicionar arquivos ao git")
        return success

    def commit(
        self,
        message: str,
        allow_empty: bool = False,
    ) -> bool:
        """Cria commit com mensagem fornecida.

        Args:
            message: Mensagem do commit
            allow_empty: Se True, permite commits sem mudanças

        Returns:
            True se commit foi criado com sucesso

        Example:
            >>> git_ops = GitOperations(Path("/project"))
            >>> if git_ops.commit("fix: correct typo"):
            ...     print("Commit criado")

        """
        command = ["git", "commit", "-m", message]
        if allow_empty:
            command.append("--allow-empty")

        success, _ = self.run_command(command)

        if success:
            logger.info("Commit criado com sucesso")
            return True

        logger.warning("Nenhuma mudança para commit ou erro ao commitar")
        return False

    def commit_fixes(
        self,
        mock_fixes: int,
        validation_fixes: int,
    ) -> bool:
        """Faz commit de correções automáticas com mensagem formatada.

        Args:
            mock_fixes: Número de correções de mock aplicadas
            validation_fixes: Número de correções de validação

        Returns:
            True se commit foi criado com sucesso

        Example:
            >>> git_ops = GitOperations(Path("/project"))
            >>> git_ops.add_all()
            >>> git_ops.commit_fixes(mock_fixes=5, validation_fixes=2)
            True

        """
        # Primeiro, adiciona todos os arquivos
        if not self.add_all():
            return False

        # Gera mensagem de commit formatada
        commit_message = format_commit_message(mock_fixes, validation_fixes)

        # Cria commit
        return self.commit(commit_message)

    def has_uncommitted_changes(self) -> bool:
        """Verifica se há mudanças não commitadas.

        Returns:
            True se há arquivos modificados não commitados

        Example:
            >>> git_ops = GitOperations(Path("/project"))
            >>> if git_ops.has_uncommitted_changes():
            ...     print("Há mudanças pendentes")

        """
        info = self.get_status()
        return info.is_git_repo and info.has_changes
