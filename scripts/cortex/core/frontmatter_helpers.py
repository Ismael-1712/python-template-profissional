"""Frontmatter Helpers - Pure business logic for YAML frontmatter generation.

This module contains helper functions for generating YAML frontmatter in
Markdown documentation files. These functions were extracted from the monolithic
cortex.py CLI script to follow the Single Responsibility Principle.

Functions:
    infer_doc_type: Infer document type from file path
    generate_id_from_filename: Generate kebab-case ID from filename
    generate_default_frontmatter: Generate complete YAML frontmatter string

Usage:
    from scripts.cortex.core.frontmatter_helpers import (
        infer_doc_type,
        generate_default_frontmatter
    )

    frontmatter = generate_default_frontmatter(Path("docs/guide.md"))
"""

from datetime import date
from pathlib import Path


def infer_doc_type(file_path: Path) -> str:
    """Infer document type from file path.

    Analyzes the file path to determine the appropriate document type
    based on directory structure and naming conventions.

    Args:
        file_path: Path to the markdown file

    Returns:
        Inferred document type (guide, arch, reference, or history)

    Examples:
        >>> infer_doc_type(Path("docs/architecture/design.md"))
        'arch'
        >>> infer_doc_type(Path("docs/guides/tutorial.md"))
        'guide'
        >>> infer_doc_type(Path("docs/api/reference.md"))
        'reference'
    """
    path_str = str(file_path).lower()

    if "architecture" in path_str or "arch" in path_str:
        return "arch"
    if "guide" in path_str or "tutorial" in path_str:
        return "guide"
    if "reference" in path_str or "api" in path_str or "ref" in path_str:
        return "reference"
    if "history" in path_str or "changelog" in path_str:
        return "history"
    # Default to guide for general documentation
    return "guide"


def generate_id_from_filename(file_path: Path) -> str:
    """Generate a kebab-case ID from filename.

    Converts a filename to a normalized kebab-case identifier suitable
    for use in YAML frontmatter. Handles spaces, underscores, and special
    characters.

    Args:
        file_path: Path to the markdown file

    Returns:
        Kebab-case ID string

    Examples:
        >>> generate_id_from_filename(Path("My Cool Guide.md"))
        'my-cool-guide'
        >>> generate_id_from_filename(Path("setup_instructions__v2.md"))
        'setup-instructions-v2'
    """
    # Get filename without extension
    name = file_path.stem

    # Convert to lowercase
    name = name.lower()

    # Replace underscores and spaces with hyphens
    name = name.replace("_", "-").replace(" ", "-")

    # Remove any characters that aren't alphanumeric or hyphens
    name = "".join(c for c in name if c.isalnum() or c == "-")

    # Remove consecutive hyphens
    while "--" in name:
        name = name.replace("--", "-")

    # Remove leading/trailing hyphens
    name = name.strip("-")

    return name


def generate_default_frontmatter(file_path: Path) -> str:
    """Generate default YAML frontmatter for a file.

    Creates a complete YAML frontmatter block with default values based on
    the file path and current date. Includes standard CORTEX metadata fields.

    Args:
        file_path: Path to the markdown file

    Returns:
        YAML frontmatter string (including --- delimiters)

    Examples:
        >>> frontmatter = generate_default_frontmatter(Path("docs/guide.md"))
        >>> print(frontmatter)
        ---
        id: guide
        type: guide
        status: draft
        version: 1.0.0
        author: Engineering Team
        date: 2025-12-21
        context_tags: []
        linked_code: []
        ---
        <BLANKLINE>
    """
    doc_id = generate_id_from_filename(file_path)
    doc_type = infer_doc_type(file_path)
    today = date.today().strftime("%Y-%m-%d")

    frontmatter = f"""---
id: {doc_id}
type: {doc_type}
status: draft
version: 1.0.0
author: Engineering Team
date: {today}
context_tags: []
linked_code: []
---

"""
    return frontmatter
