"""Testes de integração para Mock CI - valida imports e estrutura."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from scripts.core.mock_ci import (
    CIStatus,
    GitInfo,
    MockType,
    Severity,
)
from scripts.core.mock_ci.checker import CIChecker
from scripts.core.mock_ci.config import (
    BLOCKING_MOCK_TYPES,
    CI_ENVIRONMENT_VARS,
    determine_status,
)
from scripts.core.mock_ci.detector import detect_ci_environment
from scripts.core.mock_ci.fixer import CIFixer
from scripts.core.mock_ci.git_ops import GitOperations
from scripts.core.mock_ci.reporter import CIReporter


class TestImportsAndStructure:
    """Testes básicos de imports e estrutura."""

    def test_all_enums_importable(self) -> None:
        """Verifica que todos os enums podem ser importados."""
        assert Severity.HIGH
        assert MockType.HTTP_REQUEST
        assert CIStatus.SUCCESS

    def test_all_models_importable(self) -> None:
        """Verifica que todos os modelos podem ser importados."""
        info = GitInfo()
        assert info.is_git_repo is False

    def test_all_config_importable(self) -> None:
        """Verifica que todas as configurações podem ser importadas."""
        assert "GITHUB_ACTIONS" in CI_ENVIRONMENT_VARS
        assert "HTTP_REQUEST" in BLOCKING_MOCK_TYPES

    def test_detector_module(self) -> None:
        """Verifica que o módulo detector funciona."""
        # Limpa variáveis de ambiente CI para garantir resultado 'local'
        with patch.dict(os.environ, {}, clear=True):
            env = detect_ci_environment()
            # Em ambiente local (sem variáveis CI), deve retornar 'local'
            assert isinstance(env, str)
            assert env == "local"

    def test_git_ops_class_instantiable(self) -> None:
        """Verifica que GitOperations pode ser instanciada."""
        workspace = Path.cwd()
        git_ops = GitOperations(workspace)
        assert git_ops.workspace_root == workspace

    def test_git_ops_get_status(self) -> None:
        """Verifica que GitOperations.get_status retorna GitInfo."""
        workspace = Path.cwd()
        git_ops = GitOperations(workspace)
        git_info = git_ops.get_status()

        assert isinstance(git_info, GitInfo)
        # Se estivermos em um repo git, deve detectar
        assert isinstance(git_info.is_git_repo, bool)

    def test_reporter_class_instantiable(self) -> None:
        """Verifica que CIReporter pode ser instanciada."""
        workspace = Path.cwd()
        reporter = CIReporter(workspace)
        assert reporter.workspace_root == workspace

    def test_config_determine_status(self) -> None:
        """Verifica que determine_status funciona."""
        # Caso SUCCESS
        status = determine_status(
            validation_results={"test1": True, "test2": True},
            critical_count=1,
            blocking_count=0,
        )
        assert status == "SUCCESS"

        # Caso FAILURE
        status = determine_status(
            validation_results={"test1": True, "test2": False},
            critical_count=0,
            blocking_count=0,
        )
        assert status == "FAILURE"


class TestClassesCanBeInstantiated:
    """Testes de instanciação das classes principais."""

    def test_checker_requires_dependencies(self) -> None:
        """Verifica que CIChecker pode ser instanciada com mocks."""
        # Nota: CIChecker requer TestMockGenerator e TestMockValidator
        # Aqui apenas verificamos que a classe existe
        assert CIChecker is not None

    def test_fixer_requires_dependencies(self) -> None:
        """Verifica que CIFixer pode ser instanciada com mocks."""
        # Nota: CIFixer requer TestMockGenerator e TestMockValidator
        # Aqui apenas verificamos que a classe existe
        assert CIFixer is not None

    def test_all_classes_have_docstrings(self) -> None:
        """Verifica que todas as classes têm docstrings."""
        assert GitOperations.__doc__ is not None
        assert CIChecker.__doc__ is not None
        assert CIFixer.__doc__ is not None
        assert CIReporter.__doc__ is not None
