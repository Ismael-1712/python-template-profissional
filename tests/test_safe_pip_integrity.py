"""Teste de integridade e segurança para compilação de pacotes."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.utils.safe_pip import safe_pip_compile


@pytest.mark.unit
@pytest.mark.xfail(
    reason="Feature de segurança (hashes) planejada para próxima sprint",
    strict=True,
)
def test_pip_compile_enforces_hashes() -> None:
    """ALVO: Tarefa [003] - Integrity Validation.

    Proposito:
      Garantir que a compilação de dependências SEMPRE gere hashes
      para proteção contra Supply Chain Attacks (CWE-494).

    Estado Esperado:
      FALHA (RED). O código atual não injeta a flag '--generate-hashes'.
    """
    # Arrange
    input_file = Path("requirements.in")
    output_file = Path("requirements.txt")
    pip_path = "/usr/bin/pip-compile"

    # Mockamos todo o IO para não tocar no disco nem rodar processos reais
    with (
        patch("scripts.utils.safe_pip.subprocess.run") as mock_run,
        patch("scripts.utils.safe_pip.Path.mkdir"),
        patch("scripts.utils.safe_pip.Path.exists", return_value=True),
        patch("scripts.utils.safe_pip.Path.stat") as mock_stat,
        patch("scripts.utils.safe_pip.Path.read_text", return_value="# Header"),
        patch("scripts.utils.safe_pip.Path.replace"),
    ):
        # Configura mock para simular sucesso (arquivo criado e não vazio)
        mock_run.return_value = MagicMock(returncode=0)
        mock_stat.return_value.st_size = 100

        # Act
        safe_pip_compile(input_file, output_file, pip_path)

        # Assert - A Auditoria
        args, _ = mock_run.call_args
        command_list = args[0]

        # A REGRA DE OURO: Sem hash = Inseguro
        error_msg = (
            "CRÍTICO: A compilação deve gerar hashes ('--generate-hashes') "
            "para garantir a integridade dos pacotes."
        )
        assert "--generate-hashes" in command_list, error_msg
