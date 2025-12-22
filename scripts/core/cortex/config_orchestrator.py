"""Configuration Orchestrator for CORTEX System.

Centralized management of YAML configuration files with validation,
merging with defaults, and schema enforcement.

This module extracts I/O logic from the CLI layer to enforce separation
of concerns following SOLID principles.

Author: GEM & SRE Team
License: MIT
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from scripts.core.cortex.config import DEFAULT_CONFIG

# Configure module logger
logger = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """Raised when configuration file cannot be loaded."""


class ConfigValidationError(Exception):
    """Raised when configuration fails schema validation."""


class ConfigOrchestrator:
    """Orchestrator for YAML configuration file operations.

    Responsibilities:
    - Load YAML files with path resolution
    - Save YAML files with formatting options
    - Validate configuration against required schema
    - Merge user configuration with defaults

    Examples:
        >>> orchestrator = ConfigOrchestrator(project_root=Path("/project"))
        >>> config = orchestrator.load_yaml(Path("config.yaml"))
        >>> orchestrator.validate_config_schema(config, ["required_key"])
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize ConfigOrchestrator.

        Args:
            project_root: Root directory of the project for path resolution
        """
        self.project_root = project_root
        logger.info(f"ConfigOrchestrator initialized with root: {project_root}")

    def load_yaml(self, path: Path) -> dict[str, Any]:
        """Load and parse YAML configuration file.

        Resolves relative paths against project root, verifies file existence,
        and parses YAML content safely.

        Args:
            path: Path to YAML file (absolute or relative to project root)

        Returns:
            Parsed configuration as dictionary

        Raises:
            ConfigLoadError: If file not found or YAML parsing fails

        Examples:
            >>> config = orchestrator.load_yaml(Path("audit_config.yaml"))
            >>> print(config["scan_paths"])
        """
        # Resolve path: use absolute if provided, else resolve against project root
        config_path = path if path.is_absolute() else self.project_root / path

        # Check if file exists
        if not config_path.exists():
            error_msg = f"Configuration file not found: {config_path}"
            logger.error(error_msg)
            raise ConfigLoadError(error_msg)

        # Load and parse YAML
        try:
            logger.info(f"Loading YAML configuration from: {config_path}")
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            logger.debug(f"Successfully loaded configuration: {config_path}")
            return config_data if config_data is not None else {}
        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML syntax in {config_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigLoadError(error_msg) from e
        except OSError as e:
            error_msg = f"Error reading file {config_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigLoadError(error_msg) from e

    def save_yaml(
        self,
        data: dict[str, Any],
        path: Path,
        *,
        default_flow_style: bool = False,
        sort_keys: bool = False,
        allow_unicode: bool = True,
    ) -> None:
        """Save configuration data to YAML file with formatting.

        Creates parent directories if needed and writes formatted YAML.

        Args:
            data: Configuration data to save
            path: Destination file path
            default_flow_style: Use flow style (compact) formatting
            sort_keys: Sort dictionary keys alphabetically
            allow_unicode: Allow Unicode characters in output

        Raises:
            ConfigLoadError: If file cannot be written

        Examples:
            >>> config = {"scan_paths": ["docs/"]}
            >>> orchestrator.save_yaml(config, Path("new_config.yaml"))
        """
        try:
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Format and write YAML
            logger.info(f"Saving YAML configuration to: {path}")
            formatted_yaml = yaml.dump(
                data,
                default_flow_style=default_flow_style,
                sort_keys=sort_keys,
                allow_unicode=allow_unicode,
            )

            with path.open("w", encoding="utf-8") as f:
                f.write(formatted_yaml)

            logger.debug(f"Successfully saved configuration: {path}")
        except OSError as e:
            error_msg = f"Error writing file {path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigLoadError(error_msg) from e

    def validate_config_schema(
        self,
        config_data: dict[str, Any],
        required_keys: list[str],
    ) -> tuple[bool, list[str]]:
        """Validate configuration against required schema.

        Checks for presence of required keys and returns validation status.

        Args:
            config_data: Configuration dictionary to validate
            required_keys: List of keys that must be present

        Returns:
            Tuple of (is_valid, missing_keys)
            - is_valid: True if all required keys present
            - missing_keys: List of keys that are missing (empty if valid)

        Examples:
            >>> is_valid, missing = orchestrator.validate_config_schema(
            ...     {"scan_paths": []},
            ...     ["scan_paths", "file_patterns"]
            ... )
            >>> print(missing)  # ["file_patterns"]
        """
        # Find missing required keys
        missing_keys = [key for key in required_keys if key not in config_data]

        is_valid = len(missing_keys) == 0

        if not is_valid:
            logger.warning(
                f"Configuration validation failed. Missing keys: {missing_keys}",
            )
        else:
            logger.debug("Configuration validation passed")

        return is_valid, missing_keys

    def merge_with_defaults(
        self,
        user_config: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Merge user configuration with default values.

        User values take precedence over defaults. If defaults not provided,
        uses DEFAULT_CONFIG from config module.

        Args:
            user_config: User-provided configuration
            defaults: Default configuration (uses DEFAULT_CONFIG if None)

        Returns:
            Merged configuration dictionary

        Examples:
            >>> user = {"scan_paths": ["custom/"]}
            >>> merged = orchestrator.merge_with_defaults(user)
            >>> # merged contains user's scan_paths + default file_patterns, etc.
        """
        # Use DEFAULT_CONFIG if no defaults provided
        if defaults is None:
            defaults = DEFAULT_CONFIG.copy()
            logger.debug("Using DEFAULT_CONFIG for merge")
        else:
            # Create a copy to avoid modifying the original
            defaults = defaults.copy()

        # Merge: user config overrides defaults
        merged = defaults
        merged.update(user_config)

        logger.debug(f"Merged configuration with {len(user_config)} user overrides")
        return merged

    def load_config_with_defaults(
        self,
        config_path: Path | None = None,
        required_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Load configuration file and merge with defaults.

        Convenience method combining load, validate, and merge operations.
        If config_path is None or file doesn't exist, returns defaults.

        Args:
            config_path: Optional path to configuration file
            required_keys: Optional list of required keys for validation

        Returns:
            Merged and validated configuration

        Raises:
            ConfigValidationError: If required keys are missing

        Examples:
            >>> config = orchestrator.load_config_with_defaults(
            ...     Path("audit_config.yaml"),
            ...     ["scan_paths", "file_patterns"]
            ... )
        """
        # If no config path provided, return defaults
        if config_path is None:
            logger.info("No config path provided, using defaults")
            return DEFAULT_CONFIG.copy()

        # Try to load config file
        try:
            user_config = self.load_yaml(config_path)
        except ConfigLoadError:
            # If file doesn't exist or can't be loaded, return defaults
            logger.warning(f"Could not load {config_path}, using defaults")
            return DEFAULT_CONFIG.copy()

        # Validate user config BEFORE merging (if required keys specified)
        # This ensures the user's config file has all required keys
        if required_keys:
            is_valid, missing_keys = self.validate_config_schema(
                user_config,
                required_keys,
            )
            if not is_valid:
                error_msg = (
                    "Configuration validation failed. "
                    f"Missing required keys: {missing_keys}"
                )
                logger.error(error_msg)
                raise ConfigValidationError(error_msg)

        # Merge with defaults AFTER validation
        merged_config = self.merge_with_defaults(user_config)

        return merged_config
