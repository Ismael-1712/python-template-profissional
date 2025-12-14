"""Teste de segurança para garantir a redação de segredos nos logs."""

import logging

import pytest

from scripts.utils.logger import setup_logging


def test_secrets_are_redacted_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    """ALVO: Tarefa [002] - Blindagem de Segredos.

    Proposito:
      Garantir que padrões sensíveis (ex: API Keys) sejam substituídos
      por [REDACTED] antes de serem emitidos para stdout/stderr.

    Estado Esperado:
      SUCESSO (GREEN). O logger possui filtro SensitiveDataFilter.
    """
    # Arrange
    logger = setup_logging("test_security_logger", level=logging.INFO)
    sensitive_token = "ghp_ABC12345SECRETTOKEN"

    # Act
    # Simulamos um log acidental contendo uma credencial
    with caplog.at_level(logging.INFO):
        logger.info(f"Iniciando deploy com token {sensitive_token}")

    # Capture
    # caplog captura todos os logs emitidos
    log_output = caplog.text

    # Assert - A Auditoria
    # 1. O segredo NÃO deve estar visível
    error_leak = "CRÍTICO: O token sensível vazou no log em texto plano!"
    assert sensitive_token not in log_output, error_leak

    # 2. O placeholder de segurança DEVE estar presente
    error_mask = "O log deveria conter a tag '[REDACTED]'."
    assert "[REDACTED]" in log_output, error_mask


def test_multiple_secret_patterns_redacted(caplog: pytest.LogCaptureFixture) -> None:
    """Testa redação de múltiplos padrões de segredos.

    Valida que diferentes tipos de tokens/keys são devidamente redatados.
    """
    logger = setup_logging("test_multi_secrets", level=logging.INFO)

    # Arrange - diferentes tipos de tokens
    github_token = "ghp_1234567890abcdefGHIJKL"
    openai_key = "sk-proj-AbCdEfGh123456789"
    gitlab_token = "glpat-xyz_ABC-123"

    # Act
    with caplog.at_level(logging.INFO):
        logger.info(f"GitHub: {github_token}")
        logger.info(f"OpenAI: {openai_key}")
        logger.info(f"GitLab: {gitlab_token}")

    log_output = caplog.text

    # Assert - nenhum token deve estar visível
    assert github_token not in log_output, "GitHub token vazou!"
    assert openai_key not in log_output, "OpenAI key vazou!"
    assert gitlab_token not in log_output, "GitLab token vazou!"
    assert log_output.count("[REDACTED]") >= 3, "Tokens não foram redatados"
