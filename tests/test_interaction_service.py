"""Tests for InteractionService - User interaction handling.

Validates the behavior of interactive confirmation logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import typer

from scripts.cortex.core.interaction_service import InteractionService


class TestInteractionService:
    """Test suite for InteractionService."""

    @patch("typer.confirm")
    @patch("typer.secho")
    def test_confirm_action_accepted(
        self,
        mock_secho: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test that confirm_action succeeds when user confirms."""
        # Arrange
        mock_confirm.return_value = True

        # Act - should not raise
        InteractionService.confirm_action("Continue?")

        # Assert
        mock_confirm.assert_called_once_with("Continue?")
        mock_secho.assert_not_called()

    @patch("typer.confirm")
    @patch("typer.secho")
    def test_confirm_action_rejected(
        self,
        mock_secho: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test that confirm_action raises Abort when user declines."""
        # Arrange
        mock_confirm.return_value = False

        # Act & Assert
        with pytest.raises(typer.Abort):
            InteractionService.confirm_action("Continue?")

        # Verify abort message was shown
        mock_secho.assert_called_once()
        assert "Aborted" in str(mock_secho.call_args)

    @patch("typer.confirm")
    @patch("typer.secho")
    def test_confirm_action_custom_abort_message(
        self,
        mock_secho: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test custom abort message is displayed."""
        # Arrange
        mock_confirm.return_value = False
        custom_message = "Operation cancelled by user"

        # Act & Assert
        with pytest.raises(typer.Abort):
            InteractionService.confirm_action(
                "Continue?",
                abort_message=custom_message,
            )

        # Verify custom message was used
        call_args = mock_secho.call_args[0][0]
        assert custom_message in call_args

    @patch("typer.confirm")
    @patch("typer.echo")
    @patch("typer.secho")
    def test_confirm_with_preview_accepted(
        self,
        mock_secho: MagicMock,
        mock_echo: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test confirm_with_preview shows content before confirmation."""
        # Arrange
        mock_confirm.return_value = True
        preview = ["Line 1", "Line 2", "Line 3"]

        # Act
        InteractionService.confirm_with_preview("Continue?", preview)

        # Assert - preview was displayed
        assert mock_echo.call_count == len(preview)
        for i, line in enumerate(preview):
            assert mock_echo.call_args_list[i][0][0] == line

        # Assert - confirmation was requested
        mock_confirm.assert_called_once_with("Continue?")

    @patch("typer.confirm")
    @patch("typer.echo")
    @patch("typer.secho")
    def test_confirm_with_preview_rejected(
        self,
        mock_secho: MagicMock,
        mock_echo: MagicMock,
        mock_confirm: MagicMock,
    ) -> None:
        """Test confirm_with_preview aborts when user declines."""
        # Arrange
        mock_confirm.return_value = False
        preview = ["Preview line"]

        # Act & Assert
        with pytest.raises(typer.Abort):
            InteractionService.confirm_with_preview("Continue?", preview)

        # Verify preview was shown before abort
        assert mock_echo.call_count == len(preview)

    @patch("typer.confirm")
    def test_confirm_action_message_passed_correctly(
        self,
        mock_confirm: MagicMock,
    ) -> None:
        """Test that confirmation message is passed verbatim."""
        # Arrange
        mock_confirm.return_value = True
        message = "Do you want to delete all files? (y/n)"

        # Act
        InteractionService.confirm_action(message)

        # Assert
        mock_confirm.assert_called_once_with(message)
