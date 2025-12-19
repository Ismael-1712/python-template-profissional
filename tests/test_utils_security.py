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
        sanitized, blocked = sanitize_env(env)

        assert "MY_TOKEN" not in sanitized
        assert "GITHUB_TOKEN" not in sanitized
        assert "AUTH_TOKEN" not in sanitized

        # Verify blocked list contains sensitive variables
        assert "MY_TOKEN" in blocked
        assert "GITHUB_TOKEN" in blocked
        assert "AUTH_TOKEN" in blocked

    def test_blocks_key_patterns(self) -> None:
        """Test that KEY patterns are blocked."""
        env = {
            "API_KEY": "ak-123",
            "SECRET_KEY": "sk-456",
            "PRIVATE_KEY": "pk-789",
        }
        sanitized, blocked = sanitize_env(env)

        assert "API_KEY" not in sanitized
        assert "SECRET_KEY" not in sanitized
        assert "PRIVATE_KEY" not in sanitized

        # Verify blocked list
        assert "API_KEY" in blocked
        assert "SECRET_KEY" in blocked
        assert "PRIVATE_KEY" in blocked

    def test_blocks_secret_patterns(self) -> None:
        """Test that SECRET patterns are blocked."""
        env = {
            "MY_SECRET": "sensitive",
            "DATABASE_SECRET": "db_pass",
        }
        sanitized, blocked = sanitize_env(env)

        assert "MY_SECRET" not in sanitized
        assert "DATABASE_SECRET" not in sanitized

        assert "MY_SECRET" in blocked
        assert "DATABASE_SECRET" in blocked

    def test_blocks_password_patterns(self) -> None:
        """Test that PASSWORD patterns are blocked."""
        env = {
            "DB_PASSWORD": "pass123",
            "USER_PASSWORD": "secret456",
        }
        sanitized, blocked = sanitize_env(env)

        assert "DB_PASSWORD" not in sanitized
        assert "USER_PASSWORD" not in sanitized

        assert "DB_PASSWORD" in blocked
        assert "USER_PASSWORD" in blocked

    def test_blocks_credential_patterns(self) -> None:
        """Test that CREDENTIAL patterns are blocked."""
        env = {
            "AWS_CREDENTIALS": "creds",
            "SERVICE_CREDENTIAL": "token",
        }
        sanitized, blocked = sanitize_env(env)

        assert "AWS_CREDENTIALS" not in sanitized
        assert "SERVICE_CREDENTIAL" not in sanitized

        assert "AWS_CREDENTIALS" in blocked
        assert "SERVICE_CREDENTIAL" in blocked

    def test_blocks_api_patterns(self) -> None:
        """Test that API patterns are blocked."""
        env = {
            "OPENAI_API": "sk-xxx",
            "REST_API": "endpoint",
        }
        sanitized, blocked = sanitize_env(env)

        assert "OPENAI_API" not in sanitized
        assert "REST_API" not in sanitized

        assert "OPENAI_API" in blocked
        assert "REST_API" in blocked

    def test_blocks_case_insensitive(self) -> None:
        """Test that blocking is case-insensitive."""
        env = {
            "my_token": "lower",
            "My_Token": "mixed",
            "MY_TOKEN": "upper",
            "api_key": "lower_key",
        }
        sanitized, blocked = sanitize_env(env)

        assert "my_token" not in sanitized
        assert "My_Token" not in sanitized
        assert "MY_TOKEN" not in sanitized
        assert "api_key" not in sanitized

        assert len(blocked) == 4

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
        sanitized, blocked = sanitize_env(env)

        assert sanitized["PATH"] == "/usr/bin:/usr/local/bin"
        assert sanitized["HOME"] == "/home/user"
        assert sanitized["LANG"] == "en_US.UTF-8"
        assert sanitized["LC_ALL"] == "en_US.UTF-8"
        assert sanitized["TZ"] == "UTC"
        assert sanitized["USER"] == "testuser"
        assert sanitized["TMPDIR"] == "/tmp"
        assert sanitized["TEMP"] == "/tmp"
        assert sanitized["TMP"] == "/tmp"

        # No variables should be blocked
        assert len(blocked) == 0

    def test_allows_pythonpath(self) -> None:
        """Test that PYTHONPATH is allowed (in whitelist)."""
        env = {"PYTHONPATH": "/app:/lib"}
        sanitized, blocked = sanitize_env(env)

        assert sanitized["PYTHONPATH"] == "/app:/lib"
        assert len(blocked) == 0

    def test_allows_virtual_env(self) -> None:
        """Test that VIRTUAL_ENV is allowed."""
        env = {"VIRTUAL_ENV": "/home/user/.venv"}
        sanitized, blocked = sanitize_env(env)

        assert sanitized["VIRTUAL_ENV"] == "/home/user/.venv"
        assert len(blocked) == 0

    def test_hardening_allows_safe_python_vars(self) -> None:
        """Test that only explicitly safe PYTHON* variables are allowed."""
        safe_vars = {
            "PYTHONPATH": "/app",
            "PYTHONUNBUFFERED": "1",
            "PYTHONHASHSEED": "random",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
        }
        sanitized, blocked = sanitize_env(safe_vars)

        # All safe vars should pass
        assert sanitized["PYTHONPATH"] == "/app"
        assert sanitized["PYTHONUNBUFFERED"] == "1"
        assert sanitized["PYTHONHASHSEED"] == "random"
        assert sanitized["PYTHONDONTWRITEBYTECODE"] == "1"
        assert sanitized["PYTHONIOENCODING"] == "utf-8"

        assert len(blocked) == 0

    def test_hardening_blocks_dangerous_python_vars(self) -> None:
        """Test that dangerous PYTHON* variables are blocked (HARDENED)."""
        dangerous_vars = {
            "PYTHONSTARTUP": "/tmp/evil.py",
            "PYTHONHOME": "/malicious",
            "PYTHONINSPECT": "1",
        }
        sanitized, blocked = sanitize_env(dangerous_vars)

        # All dangerous vars should be blocked
        assert "PYTHONSTARTUP" not in sanitized
        assert "PYTHONHOME" not in sanitized
        assert "PYTHONINSPECT" not in sanitized

        # These are filtered (not sensitive), so not in blocked list
        assert len(blocked) == 0

    def test_allows_pytest_vars(self) -> None:
        """Test that PY* prefix vars (like PYTEST_*) are allowed."""
        env = {
            "PYTEST_TIMEOUT": "30",
            "PYTEST_CURRENT_TEST": "test_security.py::test_foo",
            "PY_COLORS": "1",
        }
        sanitized, blocked = sanitize_env(env)

        assert sanitized["PYTEST_TIMEOUT"] == "30"
        assert sanitized["PYTEST_CURRENT_TEST"] == "test_security.py::test_foo"
        assert sanitized["PY_COLORS"] == "1"

        assert len(blocked) == 0

    def test_blocks_unlisted_variables(self) -> None:
        """Test that non-whitelisted variables are blocked (Least Privilege)."""
        env = {
            "RANDOM_VAR": "value",
            "CUSTOM_CONFIG": "data",
            "MY_APP_SETTING": "setting",
        }
        sanitized, blocked = sanitize_env(env)

        assert "RANDOM_VAR" not in sanitized
        assert "CUSTOM_CONFIG" not in sanitized
        assert "MY_APP_SETTING" not in sanitized

        # These are filtered (not in allowed list), not in blocked list
        assert len(blocked) == 0

    def test_empty_environment(self) -> None:
        """Test that empty environment returns empty result."""
        sanitized, blocked = sanitize_env({})
        assert sanitized == {}
        assert blocked == []

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
        sanitized, blocked = sanitize_env(env)

        # Safe vars should pass
        assert "PATH" in sanitized
        assert "HOME" in sanitized
        assert "PYTHONPATH" in sanitized
        assert "PYTEST_TIMEOUT" in sanitized

        # Sensitive and dangerous vars should be blocked
        assert "MY_TOKEN" not in sanitized
        assert "API_KEY" not in sanitized
        assert "RANDOM_VAR" not in sanitized
        assert "PYTHONSTARTUP" not in sanitized

        # Verify blocked list contains only sensitive patterns
        assert "MY_TOKEN" in blocked
        assert "API_KEY" in blocked
        # RANDOM_VAR and PYTHONSTARTUP are filtered (not sensitive), not in blocked

    def test_preserves_values_unchanged(self) -> None:
        """Test that allowed values are not modified."""
        special_value = "/usr/bin:$HOME/.local/bin"
        env = {"PATH": special_value}
        sanitized, blocked = sanitize_env(env)

        assert sanitized["PATH"] == special_value
        assert len(blocked) == 0

    def test_regression_python_startswith_not_safe(self) -> None:
        """Regression test: ensure PYTHON* doesn't blanket allow all vars."""
        # This was the old vulnerable behavior - should NOT pass anymore
        env = {
            "PYTHONSTARTUP": "/tmp/evil.py",
            "PYTHONWARNINGS": "ignore",
        }
        sanitized, blocked = sanitize_env(env)

        # PYTHONSTARTUP should be blocked (dangerous)
        assert "PYTHONSTARTUP" not in sanitized
        # PYTHONWARNINGS is not in safe list, should be blocked
        assert "PYTHONWARNINGS" not in sanitized

        # These are filtered (not in allowed list), not in blocked list
        assert len(blocked) == 0
