"""Tests for CI documentation validator."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ci.check_docs import (  # noqa: E402
    normalize_content,
    validate_documentation,
)


class TestNormalizeContent:
    """Test suite for content normalization."""

    def test_removes_timestamp_gerado_em(self) -> None:
        """Test that 'Gerado em:' timestamps are normalized."""
        content = "Gerado em: **2024-12-13 20:30 UTC**"
        expected = "Gerado em: **TIMESTAMP**"
        assert normalize_content(content) == expected

    def test_removes_timestamp_ultima_atualizacao(self) -> None:
        """Test that 'Última Atualização:' timestamps are normalized."""
        content = "**Última Atualização:** 2024-12-13 20:30 UTC"
        expected = "**Última Atualização:** TIMESTAMP"
        assert normalize_content(content) == expected

    def test_removes_timestamp_generated_at(self) -> None:
        """Test that 'Generated at:' timestamps are normalized."""
        content = "> Generated at: 2024-12-13 20:30 UTC"
        expected = "> Generated at: TIMESTAMP"
        assert normalize_content(content) == expected

    def test_removes_timestamp_last_update(self) -> None:
        """Test that 'Last update:' timestamps are normalized."""
        content = "Last update: 2024-12-13 20:30"
        expected = "Last update: TIMESTAMP"
        assert normalize_content(content) == expected

    def test_preserves_other_content(self) -> None:
        """Test that non-timestamp content is preserved."""
        content = """# Title

Some regular content here.
With multiple lines.
And no timestamps."""
        assert normalize_content(content) == content

    def test_normalizes_multiple_timestamps(self) -> None:
        """Test normalization of content with multiple timestamps."""
        content = """# Documentation
Gerado em: **2024-12-13 20:30 UTC**

Some content here.

**Última Atualização:** 2024-12-13 21:45 UTC"""

        result = normalize_content(content)

        assert "2024-12-13 20:30 UTC" not in result
        assert "2024-12-13 21:45 UTC" not in result
        assert "TIMESTAMP" in result

    def test_case_insensitive_matching(self) -> None:
        """Test that pattern matching is case-insensitive."""
        content = "GERADO EM: 2024-12-13 20:30 UTC"
        result = normalize_content(content)
        assert "TIMESTAMP" in result

    def test_handles_empty_content(self) -> None:
        """Test handling of empty content."""
        assert normalize_content("") == ""

    def test_handles_multiline_content(self) -> None:
        """Test proper handling of multiline content."""
        content = """Line 1
Gerado em: **2024-12-13 20:30 UTC**
Line 3
**Última Atualização:** 2024-12-13 21:45 UTC
Line 5"""

        result = normalize_content(content)
        lines = result.split("\n")

        assert len(lines) == 5
        assert "Line 1" in lines[0]
        assert "TIMESTAMP" in lines[1]
        assert "Line 3" in lines[2]
        assert "TIMESTAMP" in lines[3]
        assert "Line 5" in lines[4]


class TestValidateDocumentation:
    """Test suite for documentation validation."""

    @patch("scripts.ci.check_docs.CLIDocGenerator")
    def test_validation_succeeds_when_content_matches(
        self,
        mock_generator_class: MagicMock,
    ) -> None:
        """Test validation succeeds when content matches."""
        # Mock the generator
        mock_generator = MagicMock()
        mock_generator.generate_documentation.return_value = (
            "Gerado em: **2024-12-13 20:30 UTC**\nContent"
        )
        mock_generator_class.return_value = mock_generator

        # Mock the file read
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.read_text",
                return_value="Gerado em: **2024-01-01 10:00 UTC**\nContent",
            ),
        ):
            result = validate_documentation()

        assert result == 0

    @patch("scripts.ci.check_docs.CLIDocGenerator")
    def test_validation_fails_when_content_differs(
        self,
        mock_generator_class: MagicMock,
    ) -> None:
        """Test validation fails when content differs."""
        # Mock the generator with different content
        mock_generator = MagicMock()
        mock_generator.generate_documentation.return_value = (
            "Gerado em: **2024-12-13 20:30 UTC**\nNew Content"
        )
        mock_generator_class.return_value = mock_generator

        # Mock the file read with old content
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.read_text",
                return_value="Gerado em: **2024-01-01 10:00 UTC**\nOld Content",
            ),
            patch("builtins.print"),
        ):  # Suppress output
            result = validate_documentation()

        assert result == 1

    def test_validation_fails_when_file_not_found(self) -> None:
        """Test validation fails when documentation file doesn't exist."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            patch(
                "builtins.print",
            ),
        ):  # Suppress output
            result = validate_documentation()

        assert result == 1

    @patch("scripts.ci.check_docs.CLIDocGenerator")
    def test_validation_handles_import_error(
        self,
        mock_generator_class: MagicMock,
    ) -> None:
        """Test validation handles import errors gracefully."""
        # Make the generator raise ImportError
        mock_generator_class.side_effect = ImportError("Module not found")

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "builtins.print",
            ),
        ):  # Suppress output
            result = validate_documentation()

        assert result == 1

    @patch("scripts.ci.check_docs.CLIDocGenerator")
    def test_validation_handles_generic_exception(
        self,
        mock_generator_class: MagicMock,
    ) -> None:
        """Test validation handles generic exceptions gracefully."""
        # Make the generator raise a generic exception
        mock_generator_class.side_effect = RuntimeError("Something went wrong")

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "builtins.print",
            ),
        ):  # Suppress output
            result = validate_documentation()

        assert result == 1


class TestIntegration:
    """Integration tests (require actual files)."""

    def test_normalize_content_preserves_structure(self) -> None:
        """Test that normalization preserves document structure."""
        content = """---
title: Documentation
---

# Header

Gerado em: **2024-12-13 20:30 UTC**

## Section

Content here.

**Última Atualização:** 2024-12-13 21:45 UTC

### Subsection

More content.
"""

        result = normalize_content(content)

        # Structure should be preserved
        assert "---" in result
        assert "title: Documentation" in result
        assert "# Header" in result
        assert "## Section" in result
        assert "### Subsection" in result

        # Timestamps should be normalized
        assert "2024-12-13" not in result
        assert result.count("TIMESTAMP") == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
