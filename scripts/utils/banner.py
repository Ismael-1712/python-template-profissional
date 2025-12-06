"""Startup Banner - Combat Tool Blindness (Cegueira de Ferramenta).

This module provides a reusable banner system to make it immediately clear
which tool is executing, preventing confusion in terminal sessions with
multiple scripts running.

Design Pattern:
    Injection at entry points (if __name__ == "__main__") to ensure
    visibility without polluting library imports.

Author: DevOps Engineering Team
License: MIT
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def print_startup_banner(
    tool_name: str,
    version: str,
    description: str,
    script_path: Path,
    width: int = 70,
) -> None:
    """Print a startup banner for CLI tools to combat tool blindness.

    This function creates a clear visual separator that indicates which tool
    is executing, helping developers track what's happening in their terminal,
    especially when multiple automation scripts are running.

    Args:
        tool_name: Name of the tool (e.g., "Dev Doctor", "Mock Generator")
        version: Version string (e.g., "2.0.0")
        description: Brief description of the tool's purpose
        script_path: Path(__file__) of the executing script
        width: Width of the banner (default: 70 characters)

    Example:
        >>> from pathlib import Path
        >>> print_startup_banner(
        ...     tool_name="Dev Doctor",
        ...     version="2.0.0",
        ...     description="Diagnóstico Preventivo de Ambiente",
        ...     script_path=Path(__file__)
        ... )
        ======================================================================
          Dev Doctor v2.0.0
          Diagnóstico Preventivo de Ambiente
        ======================================================================
          Timestamp: 2025-11-30 14:30:45
          Script:    scripts/cli/doctor.py
        ======================================================================

    Design Rationale:
        - **Visibility**: Makes it immediately clear which tool is running
        - **Context**: Provides timestamp and script location for debugging
        - **Consistency**: Uniform format across all CLI tools
        - **DevOps**: Helps trace execution in CI/CD logs and terminal multiplexers
    """
    border = "=" * width
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Try to get relative path from current working directory
    try:
        relative_path = script_path.relative_to(Path.cwd())
    except ValueError:
        # If script is outside cwd, use absolute path
        relative_path = script_path

    print(f"\n{border}")
    print(f"  {tool_name} v{version}")
    print(f"  {description}")
    print(f"{border}")
    print(f"  Timestamp: {timestamp}")
    print(f"  Script:    {relative_path}")
    print(f"{border}\n")


def print_deprecation_warning(
    old_path: str,
    new_path: str,
    removal_version: str = "3.0.0",
) -> None:
    """Print a deprecation warning for old script paths.

    Args:
        old_path: The deprecated path (e.g., "scripts/test_mock_generator.py")
        new_path: The new path (e.g., "scripts.cli.mock_generate")
        removal_version: Version when the old path will be removed

    Example:
        >>> print_deprecation_warning(
        ...     old_path="scripts/test_mock_generator.py",
        ...     new_path="scripts.cli.mock_generate"
        ... )
        ⚠️  DEPRECATION WARNING
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        This script location is deprecated and will be removed in v3.0.0

        Old (deprecated): scripts/test_mock_generator.py
        New (preferred):  python -m scripts.cli.mock_generate

        Please update your scripts and automation to use the new path.
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    width = 70
    border = "━" * width

    print("\n⚠️  DEPRECATION WARNING")
    print(border)
    print(
        f"This script location is deprecated and will be removed in v{removal_version}"
    )
    print()
    print(f"Old (deprecated): {old_path}")
    print(f"New (preferred):  python -m {new_path}")
    print()
    print("Please update your scripts and automation to use the new path.")
    print(f"{border}\n")
