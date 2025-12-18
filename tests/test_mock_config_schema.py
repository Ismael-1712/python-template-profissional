"""Testes para validação do schema de configuração Mock CI."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

# Tenta importar o modelo que AINDA NÃO EXISTE (Isso é intencional do TDD)
try:
    from scripts.core.mock_ci.models_pydantic import MockCIConfig
except ImportError:
    MockCIConfig = None  # type: ignore[assignment, misc]


def test_config_yaml_matches_schema() -> None:
    """Verifica se o arquivo de configuração atual é validável.

    Verifica se scripts/test_mock_config.yaml é validável por um esquema
    Pydantic formal.

    Este teste FALHARÁ inicialmente porque MockCIConfig ainda não foi
    implementado. Isso serve como 'Red Test' para nossa refatoração.
    """
    # 1. Verifica se a classe foi implementada
    if MockCIConfig is None:
        pytest.fail(
            "TDD RED: O modelo 'MockCIConfig' ainda não foi "
            "implementado em models_pydantic.py",
        )

    # 2. Verifica existência do arquivo YAML
    config_path = Path("scripts/test_mock_config.yaml")
    if not config_path.exists():
        pytest.fail(
            f"Arquivo de configuração não encontrado em: {config_path.absolute()}",
        )

    # 3. Carrega o YAML
    with open(config_path) as f:
        data = yaml.safe_load(f)

    # 4. Tenta validar contra o esquema (prova que o esquema está correto)
    try:
        config = MockCIConfig(**data)
        assert config.version == "1.0"
        print("\nSucesso: O YAML é compatível com o Schema Pydantic!")
    except ValidationError as e:
        pytest.fail(f"Configuração YAML inválida segundo o esquema: {e}")
