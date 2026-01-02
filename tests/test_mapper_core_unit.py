"""Unit tests for CORTEX ProjectMapper class.

This module tests the ProjectMapper introspection capabilities
using mocks to isolate the class from filesystem dependencies.

Tests cover:
- Initialization with custom filesystem adapters
- Project mapping with mocked components
- CLI command scanning
- Document scanning
- Knowledge entry processing
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from scripts.core.cortex.mapper import CLICommand, Document, ProjectMapper


class TestProjectMapperInit:
    """Test suite for ProjectMapper initialization."""

    def test_init_with_default_filesystem(self) -> None:
        """Test ProjectMapper initialization with default RealFileSystem."""
        project_root = Path("/fake/project")
        mapper = ProjectMapper(project_root)

        assert mapper.project_root == project_root
        assert mapper.pyproject_path == project_root / "pyproject.toml"
        assert mapper.docs_path == project_root / "docs"
        assert mapper.scripts_cli_path == project_root / "scripts" / "cli"

    def test_init_with_custom_filesystem(self) -> None:
        """Test ProjectMapper initialization with custom FileSystemAdapter."""
        project_root = Path("/fake/project")
        mock_fs = MagicMock()
        mapper = ProjectMapper(project_root, fs=mock_fs)

        assert mapper.fs is mock_fs
        assert mapper.project_root == project_root


class TestProjectMapperMapping:
    """Test suite for ProjectMapper.map_project method."""

    @patch.object(ProjectMapper, "_load_pyproject")
    @patch.object(ProjectMapper, "_scan_cli_commands")
    @patch.object(ProjectMapper, "_scan_documents")
    @patch.object(ProjectMapper, "_scan_architecture")
    @patch.object(ProjectMapper, "_process_knowledge_entries")
    @patch.object(ProjectMapper, "_extract_knowledge_rules")
    def test_map_project_with_knowledge(
        self,
        mock_extract: Mock,
        mock_process: Mock,
        mock_arch: Mock,
        mock_docs: Mock,
        mock_cli: Mock,
        mock_load: Mock,
    ) -> None:
        """Test map_project with knowledge processing enabled."""
        # Setup mocks
        mock_load.return_value = {  # type: ignore[method-assign]
            "project": {
                "name": "test-project",
                "version": "1.0.0",
                "description": "Test project",
                "requires-python": ">=3.10",
                "dependencies": ["fastapi"],
                "optional-dependencies": {"dev": ["pytest"]},
                "scripts": {"test-cmd": "path.to:main"},
            }
        }
        mock_cli.return_value = [  # type: ignore[method-assign]
            CLICommand(
                name="test-cmd",
                script_path="scripts/cli/test_cmd.py",
                description="Test command",
            )
        ]
        mock_docs.return_value = [  # type: ignore[method-assign]
            Document(path="docs/test.md", title="Test Doc")
        ]
        mock_arch.return_value = [  # type: ignore[method-assign]
            Document(path="docs/architecture/arch.md", title="Architecture")
        ]
        mock_extract.return_value = (  # type: ignore[method-assign]
            ["golden/path/1"],
            "# Knowledge Rules\n",
        )

        # Execute
        mapper = ProjectMapper(Path("/fake/project"))
        context = mapper.map_project(include_knowledge=True)

        # Assertions
        assert context.project_name == "test-project"
        assert context.version == "1.0.0"
        assert len(context.cli_commands) == 1
        assert len(context.documents) == 1
        assert len(context.architecture_docs) == 1
        assert context.golden_paths == ["golden/path/1"]
        assert context.knowledge_rules == "# Knowledge Rules\n"

        # Verify method calls
        mock_load.assert_called_once()
        mock_cli.assert_called_once()
        mock_docs.assert_called_once()
        mock_arch.assert_called_once()
        mock_process.assert_called_once()
        mock_extract.assert_called_once()

    @patch.object(ProjectMapper, "_load_pyproject")
    @patch.object(ProjectMapper, "_scan_cli_commands")
    @patch.object(ProjectMapper, "_scan_documents")
    @patch.object(ProjectMapper, "_scan_architecture")
    @patch.object(ProjectMapper, "_process_knowledge_entries")
    def test_map_project_without_knowledge(
        self,
        mock_process: Mock,
        mock_arch: Mock,
        mock_docs: Mock,
        mock_cli: Mock,
        mock_load: Mock,
    ) -> None:
        """Test map_project with knowledge processing disabled."""
        # Setup mocks
        mock_load.return_value = {  # type: ignore[method-assign]
            "project": {
                "name": "test-project",
                "version": "1.0.0",
                "description": "Test",
                "requires-python": ">=3.10",
            }
        }
        mock_cli.return_value = []  # type: ignore[method-assign]
        mock_docs.return_value = []  # type: ignore[method-assign]
        mock_arch.return_value = []  # type: ignore[method-assign]

        # Execute
        mapper = ProjectMapper(Path("/fake/project"))
        context = mapper.map_project(include_knowledge=False)

        # Assertions
        assert context.project_name == "test-project"
        assert context.golden_paths == []
        assert context.knowledge_rules == ""


class TestProjectMapperPrivateMethods:
    """Test suite for ProjectMapper private methods."""

    def test_load_pyproject_missing_file(self) -> None:
        """Test _load_pyproject when pyproject.toml is missing."""
        mock_fs = MagicMock()
        mock_fs.exists.return_value = False

        mapper = ProjectMapper(Path("/fake/project"), fs=mock_fs)
        result = mapper._load_pyproject()

        assert result == {}
        mock_fs.exists.assert_called_once()
