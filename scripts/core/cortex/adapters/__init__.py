"""CORTEX Adapters Layer.

This package contains output adapters (Ports & Adapters pattern) for
presenting and persisting Knowledge Graph validation results.

Adapters handle infrastructure concerns like file I/O and formatting,
keeping the core domain logic clean and testable.
"""

from scripts.core.cortex.adapters.reporters import (
    FileReportWriter,
    MarkdownReporter,
)

__all__ = [
    "FileReportWriter",
    "MarkdownReporter",
]
