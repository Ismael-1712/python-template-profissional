"""Unit tests for CORTEX frontmatter parser.

Tests the FrontmatterParser class using mocks to avoid real filesystem I/O,
following the SRE Standard testing guidelines.

Author: Engineering Team
License: MIT
"""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from scripts.core.cortex.metadata import FrontmatterParseError, FrontmatterParser
from scripts.core.cortex.models import DocStatus, DocType, DocumentMetadata

# ============================================================================
# TEST FIXTURES (Markdown content as strings)
# ============================================================================

VALID_FRONTMATTER = """---
id: test-guide
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 2025-11-30
context_tags:
  - testing
  - pytest
linked_code:
  - scripts/core/cortex/metadata.py
---

# Test Guide

This is test content.
"""

MINIMAL_VALID_FRONTMATTER = """---
id: minimal-doc
type: arch
status: draft
version: 2.0.0
author: Test Author
date: 2025-01-01
---

# Minimal Document
"""

NO_FRONTMATTER = """# Document Without Frontmatter

This file has no YAML header.
"""

MISSING_ID_FRONTMATTER = """---
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 2025-11-30
---

# Missing ID
"""

INVALID_ID_FRONTMATTER = """---
id: Invalid_ID_With_Underscores
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 2025-11-30
---

# Invalid ID Format
"""

INVALID_VERSION_FRONTMATTER = """---
id: test-doc
type: guide
status: active
version: 1.0
author: Engineering Team
date: 2025-11-30
---

# Invalid Version
"""

INVALID_DATE_FRONTMATTER = """---
id: test-doc
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 30/11/2025
---

# Invalid Date Format
"""

INVALID_TYPE_FRONTMATTER = """---
id: test-doc
type: invalid-type
status: active
version: 1.0.0
author: Engineering Team
date: 2025-11-30
---

# Invalid Type
"""

SHORT_AUTHOR_FRONTMATTER = """---
id: test-doc
type: guide
status: active
version: 1.0.0
author: AB
date: 2025-11-30
---

# Short Author Name
"""

INVALID_TAG_FRONTMATTER = """---
id: test-doc
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 2025-11-30
context_tags:
  - Valid_Tag_With_Underscores
---

# Invalid Tag Format
"""


# ============================================================================
# TEST CLASS
# ============================================================================


class TestFrontmatterParser:
    """Tests for FrontmatterParser class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.parser = FrontmatterParser()
        self.test_path = Path("test.md")

    # ------------------------------------------------------------------------
    # Tests for parse_file() - Success Cases
    # ------------------------------------------------------------------------

    @patch("builtins.open", new_callable=mock_open, read_data=VALID_FRONTMATTER)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_parse_valid_frontmatter(
        self,
        mock_is_file: MagicMock,
        mock_exists: MagicMock,
        mock_file: MagicMock,
    ) -> None:
        """Test parsing a file with valid frontmatter."""
        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True

        # Execute
        metadata = self.parser.parse_file(self.test_path)

        # Assert
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.id == "test-guide"
        assert metadata.type == DocType.GUIDE
        assert metadata.status == DocStatus.ACTIVE
        assert metadata.version == "1.0.0"
        assert metadata.author == "Engineering Team"
        assert metadata.date == date(2025, 11, 30)
        assert "testing" in metadata.context_tags
        assert "pytest" in metadata.context_tags
        assert "scripts/core/cortex/metadata.py" in metadata.linked_code
        assert metadata.source_file == self.test_path

    @patch("builtins.open", new_callable=mock_open, read_data=MINIMAL_VALID_FRONTMATTER)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_parse_minimal_frontmatter(
        self,
        mock_is_file: MagicMock,
        mock_exists: MagicMock,
        mock_file: MagicMock,
    ) -> None:
        """Test parsing with only required fields (no optional fields)."""
        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True

        # Execute (should emit warnings but succeed)
        metadata = self.parser.parse_file(self.test_path)

        # Assert
        assert metadata.id == "minimal-doc"
        assert metadata.type == DocType.ARCH
        assert metadata.status == DocStatus.DRAFT
        assert metadata.context_tags == []  # Empty but valid
        assert metadata.linked_code == []  # Empty but valid

    # ------------------------------------------------------------------------
    # Tests for parse_file() - Error Cases
    # ------------------------------------------------------------------------

    @patch("pathlib.Path.exists")
    def test_parse_file_not_found(self, mock_exists: MagicMock) -> None:
        """Test parsing a file that doesn't exist."""
        # Setup
        mock_exists.return_value = False

        # Execute & Assert
        with pytest.raises(FrontmatterParseError, match="does not exist"):
            self.parser.parse_file(self.test_path)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_parse_path_is_directory(
        self,
        mock_is_file: MagicMock,
        mock_exists: MagicMock,
    ) -> None:
        """Test parsing when path is a directory, not a file."""
        # Setup
        mock_exists.return_value = True
        mock_is_file.return_value = False

        # Execute & Assert
        with pytest.raises(FrontmatterParseError, match="not a file"):
            self.parser.parse_file(self.test_path)

    @patch("builtins.open", new_callable=mock_open, read_data=NO_FRONTMATTER)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_parse_no_frontmatter(
        self,
        mock_is_file: MagicMock,
        mock_exists: MagicMock,
        mock_file: MagicMock,
    ) -> None:
        """Test parsing a file without YAML frontmatter."""
        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True

        # Execute & Assert
        with pytest.raises(FrontmatterParseError, match="No YAML frontmatter"):
            self.parser.parse_file(self.test_path)

    @patch("builtins.open", new_callable=mock_open, read_data=MISSING_ID_FRONTMATTER)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_parse_missing_required_field(
        self,
        mock_is_file: MagicMock,
        mock_exists: MagicMock,
        mock_file: MagicMock,
    ) -> None:
        """Test parsing frontmatter missing a required field."""
        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True

        # Execute & Assert
        with pytest.raises(ValueError, match="validation failed"):
            self.parser.parse_file(self.test_path)

    # ------------------------------------------------------------------------
    # Tests for validate_metadata() - Format Validation
    # ------------------------------------------------------------------------

    def test_validate_invalid_id_format(self) -> None:
        """Test validation with invalid ID format (not kebab-case)."""
        # Setup
        metadata = {
            "id": "Invalid_ID",
            "type": "guide",
            "status": "active",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-11-30",
        }

        # Execute
        result = self.parser.validate_metadata(metadata)

        # Assert
        assert not result.is_valid
        assert any("kebab-case" in error for error in result.errors)

    def test_validate_invalid_version_format(self) -> None:
        """Test validation with invalid semver format."""
        # Setup
        metadata = {
            "id": "test-doc",
            "type": "guide",
            "status": "active",
            "version": "1.0",  # Missing patch number
            "author": "Engineering Team",
            "date": "2025-11-30",
        }

        # Execute
        result = self.parser.validate_metadata(metadata)

        # Assert
        assert not result.is_valid
        assert any("semver" in error for error in result.errors)

    def test_validate_invalid_date_format(self) -> None:
        """Test validation with invalid date format."""
        # Setup
        metadata = {
            "id": "test-doc",
            "type": "guide",
            "status": "active",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "30/11/2025",  # Wrong format
        }

        # Execute
        result = self.parser.validate_metadata(metadata)

        # Assert
        assert not result.is_valid
        assert any("ISO 8601" in error for error in result.errors)

    def test_validate_invalid_type(self) -> None:
        """Test validation with invalid document type."""
        # Setup
        metadata = {
            "id": "test-doc",
            "type": "invalid-type",
            "status": "active",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-11-30",
        }

        # Execute
        result = self.parser.validate_metadata(metadata)

        # Assert
        assert not result.is_valid
        assert any("type" in error.lower() for error in result.errors)

    def test_validate_invalid_status(self) -> None:
        """Test validation with invalid document status."""
        # Setup
        metadata = {
            "id": "test-doc",
            "type": "guide",
            "status": "invalid-status",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-11-30",
        }

        # Execute
        result = self.parser.validate_metadata(metadata)

        # Assert
        assert not result.is_valid
        assert any("status" in error.lower() for error in result.errors)

    def test_validate_short_author(self) -> None:
        """Test validation with author name too short."""
        # Setup
        metadata = {
            "id": "test-doc",
            "type": "guide",
            "status": "active",
            "version": "1.0.0",
            "author": "AB",  # Less than MIN_AUTHOR_LENGTH
            "date": "2025-11-30",
        }

        # Execute
        result = self.parser.validate_metadata(metadata)

        # Assert
        assert not result.is_valid
        assert any("author" in error.lower() for error in result.errors)

    def test_validate_invalid_tag_format(self) -> None:
        """Test validation with invalid tag format (not kebab-case)."""
        # Setup
        metadata = {
            "id": "test-doc",
            "type": "guide",
            "status": "active",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-11-30",
            "context_tags": ["Valid_Tag"],  # Underscore not allowed
        }

        # Execute
        result = self.parser.validate_metadata(metadata)

        # Assert
        assert not result.is_valid
        assert any("tag" in error.lower() for error in result.errors)

    # ------------------------------------------------------------------------
    # Tests for validate_metadata() - Success Cases
    # ------------------------------------------------------------------------

    def test_validate_complete_valid_metadata(self) -> None:
        """Test validation with all fields valid."""
        # Setup
        metadata = {
            "id": "test-guide",
            "type": "guide",
            "status": "active",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-11-30",
            "context_tags": ["testing", "pytest"],
            "linked_code": ["tests/test_cortex.py"],
        }

        # Execute
        result = self.parser.validate_metadata(metadata)

        # Assert
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_minimal_valid_metadata(self) -> None:
        """Test validation with only required fields."""
        # Setup
        metadata = {
            "id": "minimal-doc",
            "type": "arch",
            "status": "draft",
            "version": "2.0.0",
            "author": "Test Author",
            "date": "2025-01-01",
        }

        # Execute
        result = self.parser.validate_metadata(metadata)

        # Assert
        assert result.is_valid
        assert len(result.errors) == 0
        # Should have warnings for missing recommended fields
        assert len(result.warnings) > 0

    def test_validate_all_document_types(self) -> None:
        """Test validation accepts all valid document types."""
        # Setup base metadata
        base = {
            "id": "test-doc",
            "status": "active",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-11-30",
        }

        # Test each valid type
        for doc_type in ["guide", "arch", "reference", "history"]:
            metadata = {**base, "type": doc_type}
            result = self.parser.validate_metadata(metadata)
            assert result.is_valid, f"Type '{doc_type}' should be valid"

    def test_validate_all_document_statuses(self) -> None:
        """Test validation accepts all valid document statuses."""
        # Setup base metadata
        base = {
            "id": "test-doc",
            "type": "guide",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-11-30",
        }

        # Test each valid status
        for status in ["draft", "active", "deprecated", "archived"]:
            metadata = {**base, "status": status}
            result = self.parser.validate_metadata(metadata)
            assert result.is_valid, f"Status '{status}' should be valid"

    # ------------------------------------------------------------------------
    # Tests for extract_missing_fields()
    # ------------------------------------------------------------------------

    def test_extract_missing_fields_none(self) -> None:
        """Test extracting missing fields when all are present."""
        # Setup
        metadata = {
            "id": "test-doc",
            "type": "guide",
            "status": "active",
            "version": "1.0.0",
            "author": "Engineering Team",
            "date": "2025-11-30",
        }

        # Execute
        missing = self.parser.extract_missing_fields(metadata)

        # Assert
        assert len(missing) == 0

    def test_extract_missing_fields_multiple(self) -> None:
        """Test extracting multiple missing fields."""
        # Setup
        metadata = {
            "id": "test-doc",
            "type": "guide",
            # Missing: status, version, author, date
        }

        # Execute
        missing = self.parser.extract_missing_fields(metadata)

        # Assert
        assert "status" in missing
        assert "version" in missing
        assert "author" in missing
        assert "date" in missing

    def test_extract_missing_fields_all(self) -> None:
        """Test extracting when all required fields are missing."""
        # Setup
        metadata = {}  # Empty metadata

        # Execute
        missing = self.parser.extract_missing_fields(metadata)

        # Assert
        assert len(missing) == 6  # All required fields
        assert "id" in missing
        assert "type" in missing
        assert "status" in missing
        assert "version" in missing
        assert "author" in missing
        assert "date" in missing
