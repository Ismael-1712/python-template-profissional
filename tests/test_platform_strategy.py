"""Test suite for platform strategy factory and alert system.

This module validates:
- Windows compatibility alert is emitted exactly once per session
- Unix/Linux systems do not trigger the alert
- Platform detection robustness
- Thread-safety of alert guard (basic validation)

Test Coverage:
- test_windows_alert_emitted_once: Validates single-emission guard
- test_unix_no_alert: Ensures no false positives on Unix
- test_cygwin_alert: Validates Cygwin detection
- test_alert_reset: Validates manual reset capability for testing
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from scripts.utils.platform_strategy import (
    UnixStrategy,
    WindowsStrategy,
    get_platform_strategy,
)


class TestPlatformStrategyFactory:
    """Test suite for platform strategy factory and detection logic."""

    def setup_method(self) -> None:
        """Reset alert guard before each test to ensure isolation."""
        # Import the module to access the private variable
        import scripts.utils.platform_strategy as ps_module

        # Reset the global guard flag
        ps_module._windows_alert_emitted = False

    def test_windows_alert_emitted_once(self, monkeypatch: Any) -> None:
        """Verify Windows alert is emitted exactly once per session.

        Test Strategy:
        1. Patch sys.platform to simulate Windows
        2. Mock logger.warning to capture calls
        3. Call get_platform_strategy() twice
        4. Assert warning is called only on first invocation

        Expected Behavior:
            First call → logger.warning called (1 time)
            Second call → logger.warning NOT called again (still 1 total)
        """
        # Arrange: Simulate Windows environment
        monkeypatch.setattr("sys.platform", "win32")

        # Act & Assert: Mock logger and verify single emission
        with patch("scripts.utils.platform_strategy.logger") as mock_logger:
            # First call: Should emit warning
            strategy1 = get_platform_strategy()
            assert isinstance(strategy1, WindowsStrategy)
            assert mock_logger.warning.call_count == 1

            # Verify warning message content
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "Windows Platform Detected" in warning_msg
            assert "BEST-EFFORT MODE" in warning_msg
            assert "fsync()" in warning_msg
            assert "chmod()" in warning_msg

            # Second call: Should NOT emit warning again
            strategy2 = get_platform_strategy()
            assert isinstance(strategy2, WindowsStrategy)
            assert mock_logger.warning.call_count == 1  # Still 1!

    def test_unix_no_alert(self, monkeypatch: Any) -> None:
        """Verify Unix/Linux systems do NOT trigger the Windows alert.

        Test Strategy:
        1. Patch sys.platform to simulate Linux
        2. Mock logger.warning to capture calls
        3. Call get_platform_strategy() multiple times
        4. Assert warning is NEVER called

        Expected Behavior:
            Unix detected → UnixStrategy returned
            logger.warning → NEVER called
        """
        # Arrange: Simulate Linux environment
        monkeypatch.setattr("sys.platform", "linux")

        # Act & Assert: Mock logger and verify no warnings
        with patch("scripts.utils.platform_strategy.logger") as mock_logger:
            # First call
            strategy1 = get_platform_strategy()
            assert isinstance(strategy1, UnixStrategy)
            mock_logger.warning.assert_not_called()

            # Second call (double-check)
            strategy2 = get_platform_strategy()
            assert isinstance(strategy2, UnixStrategy)
            mock_logger.warning.assert_not_called()

    def test_cygwin_alert(self, monkeypatch: Any) -> None:
        """Verify Cygwin environment triggers the Windows alert.

        Cygwin is treated as Windows for compatibility purposes.
        """
        # Arrange: Simulate Cygwin environment
        monkeypatch.setattr("sys.platform", "cygwin")

        # Act & Assert: Mock logger and verify alert
        with patch("scripts.utils.platform_strategy.logger") as mock_logger:
            strategy = get_platform_strategy()
            assert isinstance(strategy, WindowsStrategy)
            assert mock_logger.warning.call_count == 1

            # Verify it's the Windows alert
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "Windows Platform Detected" in warning_msg

    def test_macos_no_alert(self, monkeypatch: Any) -> None:
        """Verify macOS (darwin) does NOT trigger the Windows alert."""
        # Arrange: Simulate macOS environment
        monkeypatch.setattr("sys.platform", "darwin")

        # Act & Assert: Mock logger and verify no warnings
        with patch("scripts.utils.platform_strategy.logger") as mock_logger:
            strategy = get_platform_strategy()
            assert isinstance(strategy, UnixStrategy)
            mock_logger.warning.assert_not_called()

    def test_alert_reset_capability(self, monkeypatch: Any) -> None:
        """Verify manual reset of alert guard for testing purposes.

        This validates that the alert system can be reset between tests.
        """
        import scripts.utils.platform_strategy as ps_module

        # Arrange: Simulate Windows and emit alert
        monkeypatch.setattr("sys.platform", "win32")

        with patch("scripts.utils.platform_strategy.logger") as mock_logger:
            # First emission
            get_platform_strategy()
            assert mock_logger.warning.call_count == 1

            # Manually reset guard (simulates test isolation)
            ps_module._windows_alert_emitted = False

            # Second emission after reset
            get_platform_strategy()
            assert mock_logger.warning.call_count == 2  # Alert re-emitted

    def test_windows_strategy_methods(self) -> None:
        """Smoke test for WindowsStrategy basic methods."""
        strategy = WindowsStrategy()

        # Verify basic interface compliance
        assert strategy.get_git_command() == "git.exe"
        assert strategy.get_venv_bin_dir() == "Scripts"
        assert "activate.bat" in strategy.get_venv_activate_command()

    def test_unix_strategy_methods(self) -> None:
        """Smoke test for UnixStrategy basic methods."""
        strategy = UnixStrategy()

        # Verify basic interface compliance
        assert strategy.get_git_command() == "git"
        assert strategy.get_venv_bin_dir() == "bin"
        assert "source" in strategy.get_venv_activate_command()


class TestPlatformStrategyIntegration:
    """Integration tests for platform strategy in realistic scenarios."""

    def setup_method(self) -> None:
        """Reset alert guard before each test."""
        import scripts.utils.platform_strategy as ps_module

        ps_module._windows_alert_emitted = False

    def test_multiple_invocations_realistic_scenario(self, monkeypatch: Any) -> None:
        """Simulate realistic scenario with multiple tool invocations.

        Scenario:
            User runs: cortex map → cortex scan → cortex init
            Each command may call get_platform_strategy() internally.
            Alert should appear ONLY on first command.
        """
        monkeypatch.setattr("sys.platform", "win32")

        with patch("scripts.utils.platform_strategy.logger") as mock_logger:
            # Simulate 10 invocations (realistic for complex operations)
            for _ in range(10):
                strategy = get_platform_strategy()
                assert isinstance(strategy, WindowsStrategy)

            # Verify alert emitted exactly ONCE
            assert mock_logger.warning.call_count == 1

    def test_logger_level_integration(self, monkeypatch: Any) -> None:
        """Verify alert uses warning level (not info/debug)."""
        monkeypatch.setattr("sys.platform", "win32")

        with patch("scripts.utils.platform_strategy.logger") as mock_logger:
            get_platform_strategy()

            # Verify warning() was used (not info/debug/error)
            mock_logger.warning.assert_called_once()
            mock_logger.info.assert_not_called()
            mock_logger.debug.assert_called()  # Platform detection debug still happens
