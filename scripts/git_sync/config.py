"""Configuration management for the Git synchronization system."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration with sensible defaults."""
    default_config = {
        "audit_enabled": True,
        "audit_timeout": 300,
        "audit_fail_threshold": "HIGH",
        "strict_audit": True,
        "auto_fix_enabled": True,
        "lint_timeout": 180,
        "cleanup_enabled": True,
        "git_timeout": 120,
        # Deep Clean: Merged Branches Pruning
        "prune_local_merged": True,
        "prune_base_branch": "main",
        "prune_force_delete": False,
        "prune_delete_remote": False,
        "protected_branches": ["main", "master", "develop", "staging", "production"],
        "protect_remote_tracking": True,
    }

    if config_path and config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
                logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")

    return default_config
