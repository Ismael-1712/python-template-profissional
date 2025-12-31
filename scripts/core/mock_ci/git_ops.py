"""Operações Git isoladas e testáveis.

Este módulo encapsula todas as operações relacionadas ao Git em uma classe
dedicada, facilitando testes e manutenção.
"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path
from subprocess import TimeoutExpired

from scripts.core.mock_ci.config import format_commit_message
from scripts.core.mock_ci.models import GitInfo

logger = logging.getLogger(__name__)

# Constantes para timeout e retry
DEFAULT_TIMEOUT = 30  # segundos
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5


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

    # TODO: Refactor God Function - split retry logic and error handling
    def run_command(self, command: list[str]) -> tuple[bool, str]:  # noqa: C901
        """Executa comando git de forma segura com timeout e retry.

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
            - Timeout de 30s para prevenir travamentos
            - Retry automático com backoff exponencial

        """
        # Security check: comando deve começar com "git"
        if not command or command[0] != "git":
            logger.error("Comando inválido: deve começar com 'git'")
            return False, ""

        sleep_time = 1.0  # Tempo inicial de espera entre tentativas
        last_error = ""

        for attempt in range(MAX_RETRIES):
            try:
                result = subprocess.run(  # nosec # noqa: S603
                    command,
                    cwd=self.workspace_root,
                    shell=False,  # Security: prevent shell injection
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=DEFAULT_TIMEOUT,  # Previne travamentos
                )

                success = result.returncode == 0
                output = result.stdout.strip() if success else ""

                if not success and result.stderr:
                    last_error = result.stderr.strip()
                    logger.debug(
                        "Git command stderr (attempt %d/%d): %s",
                        attempt + 1,
                        MAX_RETRIES,
                        last_error,
                    )

                # Se sucesso, retorna imediatamente
                if success:
                    if attempt > 0:
                        logger.info(
                            "Git command succeeded on attempt %d/%d",
                            attempt + 1,
                            MAX_RETRIES,
                        )
                    return True, output

                # Se falhou mas não é a última tentativa, espera e tenta de novo
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        "Git command failed (attempt %d/%d), retrying in %.1fs...",
                        attempt + 1,
                        MAX_RETRIES,
                        sleep_time,
                    )
                    time.sleep(sleep_time)
                    sleep_time *= BACKOFF_FACTOR

            except TimeoutExpired:
                logger.warning(
                    "Git command timeout after %ds (attempt %d/%d): %s",
                    DEFAULT_TIMEOUT,
                    attempt + 1,
                    MAX_RETRIES,
                    " ".join(command),
                )

                # Se não é a última tentativa, espera e tenta de novo
                if attempt < MAX_RETRIES - 1:
                    logger.info("Retrying in %.1fs...", sleep_time)
                    time.sleep(sleep_time)
                    sleep_time *= BACKOFF_FACTOR
                else:
                    logger.error(
                        "Git command failed permanently after %d timeouts",
                        MAX_RETRIES,
                    )
                    return False, ""

            except OSError as e:
                # Erros de sistema (arquivo não encontrado, permissões, etc.)
                logger.error(
                    "System error executing git command: %s",
                    str(e),
                    exc_info=True,
                )
                return False, ""

            except Exception as e:
                # Outras exceções inesperadas
                logger.error(
                    "Unexpected error executing git command: %s",
                    str(e),
                    exc_info=True,
                )
                return False, ""

        # Se chegou aqui, esgotou todas as tentativas
        logger.error(
            "Git command failed after %d attempts. Last error: %s",
            MAX_RETRIES,
            last_error,
        )
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
        # Verifica se é repositório git
        success, _ = self.run_command(["git", "status", "--porcelain"])
        if not success:
            # Não é um repositório git válido
            return GitInfo()

        # Coleta todas as informações antes de instanciar (GitInfo é imutável)
        is_git_repo = True
        has_changes = False
        current_branch = None
        commit_hash = None

        # Verifica mudanças pendentes
        success, output = self.run_command(["git", "status", "--porcelain"])
        if success:
            has_changes = bool(output.strip())

        # Branch atual
        success, branch = self.run_command(["git", "branch", "--show-current"])
        if success and branch:
            current_branch = branch

        # Hash do commit atual (8 primeiros caracteres)
        success, commit = self.run_command(["git", "rev-parse", "HEAD"])
        if success and commit:
            commit_hash = commit[:8]

        # Instancia GitInfo uma única vez com todos os valores coletados
        return GitInfo(
            is_git_repo=is_git_repo,
            has_changes=has_changes,
            current_branch=current_branch,
            commit_hash=commit_hash,
        )

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
