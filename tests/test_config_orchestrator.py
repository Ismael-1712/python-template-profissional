"""Unit tests for ConfigOrchestrator.

Tests configuration file I/O, validation, and merging operations.
Following TDD approach - these tests will FAIL initially (RED phase).

Author: GEM & SRE Team
License: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.core.cortex.config_orchestrator import (
    ConfigLoadError,
    ConfigOrchestrator,
    ConfigValidationError,
)


class TestConfigOrchestratorInit:
    """Test ConfigOrchestrator initialization."""

    def test_init_with_valid_path(self, tmp_path: Path) -> None:
        """ConfigOrchestrator should initialize with valid project root."""
        orchestrator = ConfigOrchestrator(project_root=tmp_path)
        assert orchestrator.project_root == tmp_path

    def test_init_stores_project_root(self, tmp_path: Path) -> None:
        """ConfigOrchestrator should store project root for path resolution."""
        orchestrator = ConfigOrchestrator(project_root=tmp_path)
        assert orchestrator.project_root.exists()
        assert orchestrator.project_root.is_dir()


class TestLoadYAML:
    """Test YAML file loading functionality."""

    def test_load_yaml_with_valid_file(self, tmp_path: Path) -> None:
        """load_yaml() should successfully load valid YAML file."""
        # Arrange
        config_file = tmp_path / "test_config.yaml"
        config_data = {"scan_paths": ["docs/"], "file_patterns": ["*.md"]}
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        orchestrator = ConfigOrchestrator(project_root=tmp_path)

        # Act
        result = orchestrator.load_yaml(config_file)

        # Assert
        assert result == config_data
        assert result["scan_paths"] == ["docs/"]

    def test_load_yaml_with_relative_path(self, tmp_path: Path) -> None:
        """load_yaml() should resolve relative paths against project root."""
        # Arrange
        config_file = tmp_path / "configs" / "test.yaml"
        config_file.parent.mkdir(parents=True)
        config_data = {"test_key": "test_value"}
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        orchestrator = ConfigOrchestrator(project_root=tmp_path)

        # Act
        result = orchestrator.load_yaml(Path("configs/test.yaml"))

        # Assert
        assert result["test_key"] == "test_value"

    def test_load_yaml_with_absolute_path(self, tmp_path: Path) -> None:
        """load_yaml() should handle absolute paths correctly."""
        # Arrange
        config_file = tmp_path / "absolute_config.yaml"
        config_data = {"absolute": True}
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        orchestrator = ConfigOrchestrator(project_root=tmp_path / "other")

        # Act
        result = orchestrator.load_yaml(config_file)

        # Assert
        assert result["absolute"] is True

    def test_load_yaml_file_not_found(self, tmp_path: Path) -> None:
        """load_yaml() should raise ConfigLoadError if file doesn't exist."""
        orchestrator = ConfigOrchestrator(project_root=tmp_path)

        with pytest.raises(ConfigLoadError, match="not found|does not exist"):
            orchestrator.load_yaml(Path("nonexistent.yaml"))

    def test_load_yaml_invalid_syntax(self, tmp_path: Path) -> None:
        """load_yaml() should raise ConfigLoadError on invalid YAML."""
        # Arrange
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: syntax: [", encoding="utf-8")

        orchestrator = ConfigOrchestrator(project_root=tmp_path)

        # Act & Assert
        with pytest.raises(ConfigLoadError, match="YAML|syntax|parse"):
            orchestrator.load_yaml(config_file)

    def test_load_yaml_empty_file(self, tmp_path: Path) -> None:
        """load_yaml() should handle empty YAML files gracefully."""
        # Arrange
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("", encoding="utf-8")

        orchestrator = ConfigOrchestrator(project_root=tmp_path)

        # Act
        result = orchestrator.load_yaml(config_file)

        # Assert
        assert result is None or result == {}


class TestSaveYAML:
    """Test YAML file saving functionality."""

    def test_save_yaml_creates_file(self, tmp_path: Path) -> None:
        """save_yaml() should create new YAML file."""
        # Arrange
        config_data = {"test": "data", "number": 42}
        output_file = tmp_path / "output.yaml"
        orchestrator = ConfigOrchestrator(project_root=tmp_path)

        # Act
        orchestrator.save_yaml(config_data, output_file)

        # Assert
        assert output_file.exists()
        loaded = yaml.safe_load(output_file.read_text(encoding="utf-8"))
        assert loaded == config_data

    def test_save_yaml_creates_parent_directories(self, tmp_path: Path) -> None:
        """save_yaml() should create parent directories if needed."""
        # Arrange
        config_data = {"nested": "config"}
        output_file = tmp_path / "deep" / "nested" / "config.yaml"
        orchestrator = ConfigOrchestrator(project_root=tmp_path)

        # Act
        orchestrator.save_yaml(config_data, output_file)

        # Assert
        assert output_file.exists()
        assert output_file.parent.exists()

    def test_save_yaml_formatting_options(self, tmp_path: Path) -> None:
        """save_yaml() should respect formatting options."""
        # Arrange
        config_data = {"key1": "value1", "key2": "value2"}
        output_file = tmp_path / "formatted.yaml"
        orchestrator = ConfigOrchestrator(project_root=tmp_path)

        # Act
        orchestrator.save_yaml(
            config_data,
            output_file,
            default_flow_style=False,
            sort_keys=True,
        )

        # Assert
        content = output_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        # With sort_keys=True, key1 should come before key2
        assert "key1" in lines[0]
        assert "key2" in lines[1]


class TestValidateConfigSchema:
    """Test configuration schema validation."""

    def test_validate_config_schema_all_keys_present(self) -> None:
        """validate_config_schema() should return (True, []) when all keys present."""
        # Arrange
        config: dict[str, list[str]] = {
            "scan_paths": [],
            "file_patterns": [],
            "exclude_paths": [],
        }
        required = ["scan_paths", "file_patterns", "exclude_paths"]
        orchestrator = ConfigOrchestrator(project_root=Path("/tmp"))

        # Act
        is_valid, missing = orchestrator.validate_config_schema(config, required)

        # Assert
        assert is_valid is True
        assert missing == []

    def test_validate_config_schema_missing_keys(self) -> None:
        """validate_config_schema() should detect missing required keys."""
        # Arrange
        config: dict[str, list[str]] = {"scan_paths": []}
        required = ["scan_paths", "file_patterns", "exclude_paths"]
        orchestrator = ConfigOrchestrator(project_root=Path("/tmp"))

        # Act
        is_valid, missing = orchestrator.validate_config_schema(config, required)

        # Assert
        assert is_valid is False
        assert "file_patterns" in missing
        assert "exclude_paths" in missing
        assert len(missing) == 2

    def test_validate_config_schema_empty_config(self) -> None:
        """validate_config_schema() should handle empty config."""
        # Arrange
        config: dict[str, object] = {}
        required = ["key1", "key2"]
        orchestrator = ConfigOrchestrator(project_root=Path("/tmp"))

        # Act
        is_valid, missing = orchestrator.validate_config_schema(config, required)

        # Assert
        assert is_valid is False
        assert set(missing) == {"key1", "key2"}


class TestMergeWithDefaults:
    """Test merging user config with defaults."""

    def test_merge_with_defaults_user_overrides(self) -> None:
        """merge_with_defaults() should prefer user values over defaults."""
        # Arrange
        user_config = {"scan_paths": ["custom/"]}
        defaults = {"scan_paths": ["docs/"], "file_patterns": ["*.md"]}
        orchestrator = ConfigOrchestrator(project_root=Path("/tmp"))

        # Act
        result = orchestrator.merge_with_defaults(user_config, defaults)

        # Assert
        assert result["scan_paths"] == ["custom/"]  # User value
        assert result["file_patterns"] == ["*.md"]  # Default value

    def test_merge_with_defaults_uses_default_config(self) -> None:
        """merge_with_defaults() should use DEFAULT_CONFIG when defaults=None."""
        # Arrange
        user_config = {"scan_paths": ["custom/"]}
        orchestrator = ConfigOrchestrator(project_root=Path("/tmp"))

        # Act
        result = orchestrator.merge_with_defaults(user_config, defaults=None)

        # Assert
        assert result["scan_paths"] == ["custom/"]
        # Should have other keys from DEFAULT_CONFIG
        assert "file_patterns" in result
        assert "exclude_paths" in result

    def test_merge_with_defaults_empty_user_config(self) -> None:
        """merge_with_defaults() should return defaults when user config empty."""
        # Arrange
        user_config: dict[str, str] = {}
        defaults = {"key1": "value1", "key2": "value2"}
        orchestrator = ConfigOrchestrator(project_root=Path("/tmp"))

        # Act
        result = orchestrator.merge_with_defaults(user_config, defaults)

        # Assert
        assert result == defaults


class TestLoadConfigWithDefaults:
    """Test integrated config loading with defaults."""

    def test_load_config_with_defaults_success(self, tmp_path: Path) -> None:
        """load_config_with_defaults() should load, validate, and merge."""
        # Arrange
        config_file = tmp_path / "config.yaml"
        user_config = {"scan_paths": ["custom/"], "file_patterns": ["*.md"]}
        config_file.write_text(yaml.dump(user_config), encoding="utf-8")

        orchestrator = ConfigOrchestrator(project_root=tmp_path)
        required = ["scan_paths", "file_patterns"]

        # Act
        result = orchestrator.load_config_with_defaults(config_file, required)

        # Assert
        assert result["scan_paths"] == ["custom/"]
        assert result["file_patterns"] == ["*.md"]

    def test_load_config_with_defaults_validation_fails(self, tmp_path: Path) -> None:
        """load_config_with_defaults() should raise on validation failure."""
        # Arrange
        config_file = tmp_path / "incomplete.yaml"
        user_config: dict[str, list[str]] = {"scan_paths": []}  # Missing file_patterns
        config_file.write_text(yaml.dump(user_config), encoding="utf-8")

        orchestrator = ConfigOrchestrator(project_root=tmp_path)
        required = ["scan_paths", "file_patterns"]

        # Act & Assert
        with pytest.raises(ConfigValidationError, match="file_patterns"):
            orchestrator.load_config_with_defaults(config_file, required)

    def test_load_config_with_defaults_no_file_returns_defaults(
        self,
        tmp_path: Path,
    ) -> None:
        """load_config_with_defaults() should return defaults when file missing."""
        # Arrange
        orchestrator = ConfigOrchestrator(project_root=tmp_path)

        # Act
        result = orchestrator.load_config_with_defaults(config_path=None)

        # Assert
        # Should return DEFAULT_CONFIG
        assert "scan_paths" in result
        assert "file_patterns" in result
