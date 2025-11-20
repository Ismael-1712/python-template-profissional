"""Configuration management for Smart Git Sync.

This module handles loading, validation, and defaults for the git_sync
configuration system.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Default configuration with sensible values
DEFAULT_CONFIG: dict[str, Any] = {
    # Audit settings
    "audit_enabled": True,
    "audit_timeout": 300,  # seconds
    "audit_fail_threshold": "HIGH",  # CRITICAL, HIGH, MEDIUM, LOW
    "strict_audit": True,  # Fail sync if audit fails
    # Automated fix settings
    "auto_fix_enabled": True,
    "lint_timeout": 180,  # seconds
    # Git settings
    "git_timeout": 120,  # seconds
    "cleanup_enabled": True,
    # Branch protection settings
    "branch_protection": {
        "protected_branches": ["main", "master", "develop", "release/*"],
        "allow_direct_push": False,
        "require_pr": True,
    },
    # Pull Request settings
    "pull_request": {
        "provider": "github",  # github or gitlab
        "api_token_env": "GITHUB_TOKEN",
        "default_reviewers": [],
        "auto_assign": True,
        "labels": ["automated-sync", "needs-review"],
    },
    # Feature branch settings
    "feature_branch": {
        "prefix": "sync",
        "include_timestamp": True,
        "include_user": False,
        "format": "{prefix}/{timestamp}",
    },
    # Rollback settings
    "rollback": {
        "enabled": True,
        "preserve_commits": True,
        "create_backup_branch": False,
    },
}


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration with sensible defaults.

    This function loads configuration from a YAML file and merges it with
    default values. If no config file is provided or the file doesn't exist,
    returns the default configuration.

    Args:
        config_path: Optional path to YAML configuration file.
                    If None, looks for smart_git_sync_config.yaml in the
                    scripts directory.

    Returns:
        Dictionary containing merged configuration (defaults + user overrides)

    Example:
        >>> config = load_config(Path("custom_config.yaml"))
        >>> print(config["audit_enabled"])
        True
    """
    # Start with defaults
    config = DEFAULT_CONFIG.copy()

    # Determine config file location
    if config_path is None:
        # Default to smart_git_sync_config.yaml in scripts directory
        scripts_dir = Path(__file__).parent.parent
        config_path = scripts_dir / "smart_git_sync_config.yaml"

    # Load user configuration if exists
    if config_path and config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                user_config = yaml.safe_load(f)

            if user_config:
                # Deep merge for nested dictionaries
                _deep_merge(config, user_config)
                logger.info(f"Loaded configuration from {config_path}")
            else:
                logger.warning(f"Config file {config_path} is empty, using defaults")

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config {config_path}: {e}")
            logger.warning("Using default configuration")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            logger.warning("Using default configuration")
    else:
        logger.info("No configuration file found, using defaults")

    return config


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Deep merge override dictionary into base dictionary.

    This modifies the base dictionary in-place. For nested dictionaries,
    it merges recursively instead of replacing.

    Args:
        base: Base dictionary to merge into (modified in-place)
        override: Override dictionary with new values
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            _deep_merge(base[key], value)
        else:
            # Override value
            base[key] = value


def get_protected_branches(config: dict[str, Any]) -> list[str]:
    """Extract list of protected branches from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        List of protected branch names/patterns

    Example:
        >>> config = load_config()
        >>> branches = get_protected_branches(config)
        >>> print(branches)
        ['main', 'master', 'develop', 'release/*']
    """
    return config.get("branch_protection", {}).get(
        "protected_branches",
        ["main", "master"],
    )


def is_direct_push_allowed(config: dict[str, Any]) -> bool:
    """Check if direct push to protected branches is allowed.

    Args:
        config: Configuration dictionary

    Returns:
        True if direct push is allowed, False otherwise
    """
    return config.get("branch_protection", {}).get("allow_direct_push", False)


def is_pr_required(config: dict[str, Any]) -> bool:
    """Check if Pull Request is required for protected branches.

    Args:
        config: Configuration dictionary

    Returns:
        True if PR is required, False otherwise
    """
    return config.get("branch_protection", {}).get("require_pr", True)
