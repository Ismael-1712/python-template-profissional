"""CORTEX - Documentation as Code System.

This module provides tools for managing documentation with YAML frontmatter,
validating links between docs and code, and ensuring documentation quality.

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = [
    "CodeLinkScanner",
    "DocStatus",
    "DocType",
    "DocumentMetadata",
    "KnowledgeEntry",
    "KnowledgeLink",
    "KnowledgeScanner",
    "KnowledgeSource",
    "KnowledgeSyncer",
    "LinkAnalyzer",
    "LinkCheckResult",
    "LinkType",
    "ValidationResult",
]

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
from scripts.core.cortex.knowledge_sync import KnowledgeSyncer
from scripts.core.cortex.link_analyzer import LinkAnalyzer
from scripts.core.cortex.models import (
    DocStatus,
    DocType,
    DocumentMetadata,
    KnowledgeEntry,
    KnowledgeLink,
    KnowledgeSource,
    LinkCheckResult,
    LinkType,
    ValidationResult,
)
from scripts.core.cortex.scanner import CodeLinkScanner
