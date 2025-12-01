"""Testes End-to-End para MockCIRunner.

Nota: Estes testes validam apenas a estrutura e imports do runner.
Testes funcionais completos requerem correção prévia do TestMockValidator
para aceitar config_file como parâmetro.
"""

from scripts.core.mock_ci import MockCIRunner


class TestMockCIRunnerStructure:
    """Testes de estrutura do MockCIRunner."""

    def test_runner_class_exists_and_is_importable(self) -> None:
        """Verifica que MockCIRunner pode ser importado."""
        assert MockCIRunner is not None
        assert MockCIRunner.__doc__ is not None

    def test_runner_has_expected_methods(self) -> None:
        """Verifica que MockCIRunner tem os métodos esperados."""
        assert hasattr(MockCIRunner, "check")
        assert hasattr(MockCIRunner, "fix")
        assert hasattr(MockCIRunner, "generate_report")
        assert hasattr(MockCIRunner, "print_summary")
        assert hasattr(MockCIRunner, "get_environment_info")

    def test_runner_init_signature(self) -> None:
        """Verifica assinatura do __init__."""
        import inspect

        sig = inspect.signature(MockCIRunner.__init__)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "workspace_root" in params
        assert "config_file" in params
