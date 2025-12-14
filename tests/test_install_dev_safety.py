"""Teste de segurança e hardening para scripts de instalação."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.install_dev import install_dev_environment


@pytest.mark.unit
def test_subprocess_calls_must_have_timeout() -> None:
    """ALVO: Tarefa [001] - Hardening do install_dev.py.

    Proposito:
      Verificar se TODAS as chamadas de sistema (pip install, pip-compile)
      possuem um limite de tempo (timeout) definido.

    Estado Esperado:
      FALHA (RED). O código atual não implementa timeout.
    """
    # Arrange
    mock_workspace = Path("/tmp/mock_workspace")

    # Mockamos dependências externas para o teste não rodar de verdade
    with (
        patch("scripts.install_dev.subprocess.run") as mock_run,
        patch("scripts.install_dev.shutil.which") as mock_which,
        patch("scripts.install_dev._setup_direnv"),
        patch("scripts.install_dev._display_success_panel"),
        patch("scripts.install_dev.safe_pip_compile") as mock_safe_pip,
    ):
        # Configura o mock para simular sucesso (returncode 0)
        mock_run.return_value = MagicMock(returncode=0, stdout="success")
        # Simula que pip-compile existe no PATH para testar o caminho feliz
        mock_which.return_value = "/usr/bin/pip-compile"
        mock_safe_pip.return_value = MagicMock(stdout="compiled")

        # Act
        install_dev_environment(mock_workspace)

        # Assert - A Auditoria
        # Verificamos se o subprocess.run foi chamado
        msg_call = "O subprocess.run deveria ter sido chamado."
        assert mock_run.call_count > 0, msg_call

        # Verificamos CADA chamada feita ao sistema
        for i, call in enumerate(mock_run.call_args_list):
            args, kwargs = call
            command_str = str(args[0]) if args else "unknown"

            # A REGRA DE OURO: Sem timeout = Falha
            error_msg = (
                f"CRÍTICO: A chamada #{i + 1} ({command_str}) "
                "não possui 'timeout' definido!"
            )
            assert "timeout" in kwargs, error_msg

            # A REGRA DE VALOR: Timeout deve ser seguro (ex: 300s)
            assert kwargs["timeout"] >= 300, (
                f"O timeout da chamada #{i + 1} é muito curto."
            )
