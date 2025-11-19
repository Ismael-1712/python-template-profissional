"""Configuration Management for Code Audit System.

This module handles loading and validation of audit configuration from
YAML files with intelligent fallback to sensible defaults.

Functions:
    load_config: Load configuration from YAML file with defaults

Author: DevOps Engineering Team
License: MIT
"""

import logging
from pathlib import Path
from typing import Any

import yaml

# Configure module logger
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG: dict[str, Any] = {
    "scan_paths": ["src/", "tests/", "scripts/", ".github/"],
    "file_patterns": ["*.py"],
    "exclude_paths": [".git/", "__pycache__/", ".venv/", "venv/"],
    "ci_timeout": 300,
    "simulate_ci": True,
    "max_findings_per_file": 50,
    "severity_levels": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
}


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from YAML file with fallback defaults.

    Attempts to load user configuration from a YAML file and merges it
    with default values. If the file doesn't exist or fails to parse,
    returns the default configuration with a warning.

    Args:
        config_path: Optional path to YAML configuration file

    Returns:
        Dictionary containing merged configuration values

    Example:
        >>> config = load_config(Path("audit_config.yaml"))
        >>> print(config["scan_paths"])
        ['src/', 'tests/', 'scripts/']
    """
    # Start with a copy of defaults
    config = DEFAULT_CONFIG.copy()

    if config_path and config_path.exists():
        try:
            with config_path.open(encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    config.update(user_config)
                    logger.info("Loaded configuration from %s", config_path)
        except yaml.YAMLError as e:
            logger.warning("Failed to parse YAML config from %s: %s", config_path, e)
        except OSError as e:
            logger.warning("Failed to read config file %s: %s", config_path, e)
    elif config_path:
        logger.warning("Config file not found: %s - using defaults", config_path)

    return config
