"""Tests for security utilities module.

Validates sanitization of environment variables to prevent
data leakage in subprocess execution.
"""

from __future__ import annotations

from scripts.utils.security import sanitize_env


class TestSanitizeEnv:
    """Test suite for sanitize_env function."""

    def test_blocks_token_patterns(self) -> None:
        """Test that TOKEN patterns are blocked."""
        env = {
            "MY_TOKEN": "secret123",
            "GITHUB_TOKEN": "ghp_xxx",
            "AUTH_TOKEN": "bearer_xxx",
        }
        result = sanitize_env(env)

        assert "MY_TOKEN" not in result
        assert "GITHUB_TOKEN" not in result
        assert "AUTH_TOKEN" not in result

    def test_blocks_key_patterns(self) -> None:
        """Test that KEY patterns are blocked."""
        env = {
            "API_KEY": "ak-123",
            "SECRET_KEY": "sk-456",
            "PRIVATE_KEY": "pk-789",
        }
        result = sanitize_env(env)

        assert "API_KEY" not in result
        assert "SECRET_KEY" not in result
        assert "PRIVATE_KEY" not in result

    def test_blocks_secret_patterns(self) -> None:
        """Test that SECRET patterns are blocked."""
        env = {
            "MY_SECRET": "sensitive",
            "DATABASE_SECRET": "db_pass",
        }
        result = sanitize_env(env)

        assert "MY_SECRET" not in result
        assert "DATABASE_SECRET" not in result

    def test_blocks_password_patterns(self) -> None:
        """Test that PASSWORD patterns are blocked."""
        env = {
            "DB_PASSWORD": "pass123",
            "USER_PASSWORD": "secret456",
        }
        result = sanitize_env(env)

        assert "DB_PASSWORD" not in result
        assert "USER_PASSWORD" not in result

    def test_blocks_credential_patterns(self) -> None:
        """Test that CREDENTIAL patterns are blocked."""
        env = {
            "AWS_CREDENTIALS": "creds",
            "SERVICE_CREDENTIAL": "token",
        }
        result = sanitize_env(env)

        assert "AWS_CREDENTIALS" not in result
        assert "SERVICE_CREDENTIAL" not in result

    def test_blocks_api_patterns(self) -> None:
        """Test that API patterns are blocked."""
        env = {
            "OPENAI_API": "sk-xxx",
            "REST_API": "endpoint",
        }
        result = sanitize_env(env)

        assert "OPENAI_API" not in result
        assert "REST_API" not in result

    def test_blocks_case_insensitive(self) -> None:
        """Test that blocking is case-insensitive."""
        env = {
            "my_token": "lower",
            "My_Token": "mixed",
            "MY_TOKEN": "upper",
            "api_key": "lower_key",
        }
        result = sanitize_env(env)

        assert "my_token" not in result
        assert "My_Token" not in result
        assert "MY_TOKEN" not in result
        assert "api_key" not in result

    def test_allows_whitelisted_system_vars(self) -> None:
        """Test that whitelisted system variables pass through."""
        env = {
            "PATH": "/usr/bin:/usr/local/bin",
            "HOME": "/home/user",
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8",
            "TZ": "UTC",
            "USER": "testuser",
            "TMPDIR": "/tmp",
            "TEMP": "/tmp",
            "TMP": "/tmp",
        }
        result = sanitize_env(env)

        assert result["PATH"] == "/usr/bin:/usr/local/bin"
        assert result["HOME"] == "/home/user"
        assert result["LANG"] == "en_US.UTF-8"
        assert result["LC_ALL"] == "en_US.UTF-8"
        assert result["TZ"] == "UTC"
        assert result["USER"] == "testuser"
        assert result["TMPDIR"] == "/tmp"
        assert result["TEMP"] == "/tmp"
        assert result["TMP"] == "/tmp"

    def test_allows_pythonpath(self) -> None:
        """Test that PYTHONPATH is allowed (in whitelist)."""
        env = {"PYTHONPATH": "/app:/lib"}
        result = sanitize_env(env)

        assert result["PYTHONPATH"] == "/app:/lib"

    def test_allows_virtual_env(self) -> None:
        """Test that VIRTUAL_ENV is allowed."""
        env = {"VIRTUAL_ENV": "/home/user/.venv"}
        result = sanitize_env(env)

        assert result["VIRTUAL_ENV"] == "/home/user/.venv"

    def test_hardening_allows_safe_python_vars(self) -> None:
        """Test that only explicitly safe PYTHON* variables are allowed."""
        safe_vars = {
            "PYTHONPATH": "/app",
            "PYTHONUNBUFFERED": "1",
            "PYTHONHASHSEED": "random",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
        }
        result = sanitize_env(safe_vars)

        # All safe vars should pass
        assert result["PYTHONPATH"] == "/app"
        assert result["PYTHONUNBUFFERED"] == "1"
        assert result["PYTHONHASHSEED"] == "random"
        assert result["PYTHONDONTWRITEBYTECODE"] == "1"
        assert result["PYTHONIOENCODING"] == "utf-8"

    def test_hardening_blocks_dangerous_python_vars(self) -> None:
        """Test that dangerous PYTHON* variables are blocked (HARDENED)."""
        dangerous_vars = {
            "PYTHONSTARTUP": "/tmp/evil.py",
            "PYTHONHOME": "/malicious",
            "PYTHONINSPECT": "1",
        }
        result = sanitize_env(dangerous_vars)

        # All dangerous vars should be blocked
        assert "PYTHONSTARTUP" not in result
        assert "PYTHONHOME" not in result
        assert "PYTHONINSPECT" not in result

    def test_allows_pytest_vars(self) -> None:
        """Test that PY* prefix vars (like PYTEST_*) are allowed."""
        env = {
            "PYTEST_TIMEOUT": "30",
            "PYTEST_CURRENT_TEST": "test_security.py::test_foo",
            "PY_COLORS": "1",
        }
        result = sanitize_env(env)

        assert result["PYTEST_TIMEOUT"] == "30"
        assert result["PYTEST_CURRENT_TEST"] == "test_security.py::test_foo"
        assert result["PY_COLORS"] == "1"

    def test_blocks_unlisted_variables(self) -> None:
        """Test that non-whitelisted variables are blocked (Least Privilege)."""
        env = {
            "RANDOM_VAR": "value",
            "CUSTOM_CONFIG": "data",
            "MY_APP_SETTING": "setting",
        }
        result = sanitize_env(env)

        assert "RANDOM_VAR" not in result
        assert "CUSTOM_CONFIG" not in result
        assert "MY_APP_SETTING" not in result

    def test_empty_environment(self) -> None:
        """Test that empty environment returns empty result."""
        result = sanitize_env({})
        assert result == {}

    def test_mixed_environment(self) -> None:
        """Test realistic mixed environment with safe and sensitive vars."""
        env = {
            "PATH": "/usr/bin",
            "HOME": "/home/user",
            "MY_TOKEN": "secret",
            "PYTHONPATH": "/app",
            "API_KEY": "dangerous",
            "PYTEST_TIMEOUT": "30",
            "RANDOM_VAR": "blocked",
            "PYTHONSTARTUP": "/tmp/evil.py",
        }
        result = sanitize_env(env)

        # Safe vars should pass
        assert "PATH" in result
        assert "HOME" in result
        assert "PYTHONPATH" in result
        assert "PYTEST_TIMEOUT" in result

        # Sensitive and dangerous vars should be blocked
        assert "MY_TOKEN" not in result
        assert "API_KEY" not in result
        assert "RANDOM_VAR" not in result
        assert "PYTHONSTARTUP" not in result

    def test_preserves_values_unchanged(self) -> None:
        """Test that allowed values are not modified."""
        special_value = "/usr/bin:$HOME/.local/bin"
        env = {"PATH": special_value}
        result = sanitize_env(env)

        assert result["PATH"] == special_value

    def test_regression_python_startswith_not_safe(self) -> None:
        """Regression test: ensure PYTHON* doesn't blanket allow all vars."""
        # This was the old vulnerable behavior - should NOT pass anymore
        env = {
            "PYTHONSTARTUP": "/tmp/evil.py",
            "PYTHONWARNINGS": "ignore",
        }
        result = sanitize_env(env)

        # PYTHONSTARTUP should be blocked (dangerous)
        assert "PYTHONSTARTUP" not in result
        # PYTHONWARNINGS is not in safe list, should be blocked
        assert "PYTHONWARNINGS" not in result
