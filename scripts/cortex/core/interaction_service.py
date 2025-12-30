"""Interaction Service - Handles user interactions and confirmations.

This module provides a clean interface for interactive CLI operations,
separating user interaction logic from command orchestration.

Extracted from cli.py as part of the Hexagonal Architecture refactoring.

Architecture: Core Layer (Application Services)
"""

from __future__ import annotations

import typer


class InteractionService:
    """Handles interactive user confirmations and prompts.

    This service encapsulates all user interaction logic, making it
    testable and reusable across different CLI commands.

    Usage:
        InteractionService.confirm_action(
            "Do you want to overwrite?",
            abort_message="Aborted. No changes made."
        )
    """

    @staticmethod
    def confirm_action(
        message: str,
        abort_message: str = "Aborted. No changes made.",
    ) -> None:
        """Prompt user for confirmation and abort if declined.

        Args:
            message: The confirmation question to display.
            abort_message: Message to show if user declines (default: "Aborted...").

        Raises:
            typer.Abort: If user declines the confirmation.

        Example:
            >>> InteractionService.confirm_action("Delete all files?")
            # If user types 'n', raises typer.Abort
        """
        if not typer.confirm(message):
            typer.secho(
                f"✋ {abort_message}",
                fg=typer.colors.BLUE,
            )
            raise typer.Abort()

    @staticmethod
    def confirm_with_preview(
        message: str,
        preview_lines: list[str],
        abort_message: str = "Aborted. No changes made.",
    ) -> None:
        """Show preview content and prompt for confirmation.

        Args:
            message: The confirmation question to display.
            preview_lines: Lines of content to preview before confirmation.
            abort_message: Message to show if user declines.

        Raises:
            typer.Abort: If user declines the confirmation.

        Example:
            >>> InteractionService.confirm_with_preview(
            ...     "Overwrite frontmatter?",
            ...     ["---", "title: Test", "---"]
            ... )
        """
        # Display preview
        for line in preview_lines:
            typer.echo(line)

        # Ask for confirmation
        InteractionService.confirm_action(message, abort_message)
