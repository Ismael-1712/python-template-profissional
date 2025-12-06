#!/usr/bin/env python3
"""Test Suite for Smart Git Sync CLI Wrapper.

Smoke tests to validate the CLI entry point functionality.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from scripts.git_sync.exceptions import SyncError


class TestSmartGitSyncCLI(unittest.TestCase):
    """Test cases for the CLI wrapper main() function."""

    @patch("scripts.cli.git_sync.SyncOrchestrator")
    @patch("scripts.cli.git_sync.load_config")
    @patch("sys.argv", ["git_sync.py"])
    def test_main_basic_execution(
        self,
        mock_load_config: MagicMock,
        mock_orchestrator_cls: MagicMock,
    ) -> None:
        """Test basic CLI execution without arguments."""
        # Mock configuration
        mock_config = {"audit_enabled": True}
        mock_load_config.return_value = mock_config

        # Mock orchestrator instance
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_sync.return_value = True
        mock_orchestrator_cls.return_value = mock_orchestrator

        # Import and run main
        from scripts.cli.git_sync import main

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 0)
        mock_orchestrator.execute_sync.assert_called_once()

    @patch("scripts.cli.git_sync.SyncOrchestrator")
    @patch("scripts.cli.git_sync.load_config")
    @patch("sys.argv", ["git_sync.py", "--dry-run"])
    def test_main_dry_run_flag(
        self,
        mock_load_config: MagicMock,
        mock_orchestrator_cls: MagicMock,
    ) -> None:
        """Test CLI with --dry-run flag."""
        mock_config = {"audit_enabled": True}
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_sync.return_value = True
        mock_orchestrator_cls.return_value = mock_orchestrator

        from scripts.cli.git_sync import main

        with self.assertRaises(SystemExit) as cm:
            main()

        # Verify dry_run=True was passed
        mock_orchestrator_cls.assert_called_once()
        call_kwargs = mock_orchestrator_cls.call_args.kwargs
        self.assertTrue(call_kwargs["dry_run"])
        self.assertEqual(cm.exception.code, 0)

    @patch("scripts.cli.git_sync.SyncOrchestrator")
    @patch("scripts.cli.git_sync.load_config")
    @patch("sys.argv", ["git_sync.py", "--no-audit"])
    def test_main_no_audit_flag(
        self,
        mock_load_config: MagicMock,
        mock_orchestrator_cls: MagicMock,
    ) -> None:
        """Test CLI with --no-audit flag."""
        mock_config = {"audit_enabled": True}
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_sync.return_value = True
        mock_orchestrator_cls.return_value = mock_orchestrator

        from scripts.cli.git_sync import main

        with self.assertRaises(SystemExit) as cm:
            main()

        # Verify audit was disabled
        self.assertFalse(mock_config["audit_enabled"])
        self.assertEqual(cm.exception.code, 0)

    @patch("scripts.cli.git_sync.SyncOrchestrator")
    @patch("scripts.cli.git_sync.load_config")
    @patch("sys.argv", ["git_sync.py"])
    def test_main_sync_failure(
        self,
        mock_load_config: MagicMock,
        mock_orchestrator_cls: MagicMock,
    ) -> None:
        """Test CLI when sync fails."""
        mock_config = {"audit_enabled": True}
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_sync.return_value = False
        mock_orchestrator_cls.return_value = mock_orchestrator

        from scripts.cli.git_sync import main

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)

    @patch("scripts.cli.git_sync.SyncOrchestrator")
    @patch("scripts.cli.git_sync.load_config")
    @patch("sys.argv", ["git_sync.py"])
    def test_main_keyboard_interrupt(
        self,
        mock_load_config: MagicMock,
        mock_orchestrator_cls: MagicMock,
    ) -> None:
        """Test CLI handles KeyboardInterrupt gracefully."""
        mock_config = {"audit_enabled": True}
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_sync.side_effect = KeyboardInterrupt()
        mock_orchestrator_cls.return_value = mock_orchestrator

        from scripts.cli.git_sync import main

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 130)

    @patch("scripts.cli.git_sync.SyncOrchestrator")
    @patch("scripts.cli.git_sync.load_config")
    @patch("sys.argv", ["git_sync.py"])
    def test_main_sync_error(
        self,
        mock_load_config: MagicMock,
        mock_orchestrator_cls: MagicMock,
    ) -> None:
        """Test CLI handles SyncError properly."""
        mock_config = {"audit_enabled": True}
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_sync.side_effect = SyncError("Test error")
        mock_orchestrator_cls.return_value = mock_orchestrator

        from scripts.cli.git_sync import main

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)

    @patch("scripts.cli.git_sync.SyncOrchestrator")
    @patch("scripts.cli.git_sync.load_config")
    @patch("sys.argv", ["git_sync.py"])
    def test_main_unexpected_exception(
        self,
        mock_load_config: MagicMock,
        mock_orchestrator_cls: MagicMock,
    ) -> None:
        """Test CLI handles unexpected exceptions."""
        mock_config = {"audit_enabled": True}
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_sync.side_effect = RuntimeError("Unexpected!")
        mock_orchestrator_cls.return_value = mock_orchestrator

        from scripts.cli.git_sync import main

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 2)

    @patch("scripts.cli.git_sync.SyncOrchestrator")
    @patch("scripts.cli.git_sync.load_config")
    @patch("sys.argv", ["git_sync.py", "--config", "/tmp/test.yaml"])
    def test_main_with_config_file(
        self,
        mock_load_config: MagicMock,
        mock_orchestrator_cls: MagicMock,
    ) -> None:
        """Test CLI with custom config file."""
        mock_config = {"audit_enabled": True}
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_sync.return_value = True
        mock_orchestrator_cls.return_value = mock_orchestrator

        from scripts.cli.git_sync import main

        with self.assertRaises(SystemExit) as cm:
            main()

        # Verify config was loaded with correct path
        mock_load_config.assert_called_once()
        config_arg = mock_load_config.call_args.args[0]
        self.assertEqual(str(config_arg), "/tmp/test.yaml")
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
