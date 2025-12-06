"""CLI Tools - Command-line interfaces for development automation.

This package contains executable command-line tools for development workflows:
- audit: Code security and quality auditing
- doctor: Development environment diagnostics
- git_sync: Smart Git synchronization
- install_dev: Development environment installation
- mock_ci: CI/CD mock integration
- mock_generate: Test mock generator
- mock_validate: Test mock validator
- upgrade_python: Python version manager

Usage:
    python -m scripts.cli.doctor
    python -m scripts.cli.audit
    python -m scripts.cli.mock_generate --scan

Author: DevOps Engineering Team
License: MIT
"""

from __future__ import annotations

__all__ = [
    "audit",
    "doctor",
    "git_sync",
    "install_dev",
    "mock_ci",
    "mock_generate",
    "mock_validate",
    "upgrade_python",
]
