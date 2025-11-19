"""Code Audit Package - Modular Security and Quality Auditor.

This package provides a refactored, modular implementation of the code
audit system. It separates concerns into distinct modules for better
maintainability, testability, and extensibility.

Modules:
    models: Data models for audit results and patterns
    (Future modules: config, scanner, analyzer, reporters, plugins)

Author: DevOps Engineering Team
License: MIT
Version: 2.2.0
"""

from .models import AuditResult, SecurityPattern

__version__ = "2.2.0"
__all__ = ["AuditResult", "SecurityPattern"]
