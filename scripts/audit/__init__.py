"""Code Audit Package - Modular Security and Quality Auditor."""

from .analyzer import CodeAnalyzer
from .config import load_config
from .models import AuditResult, SecurityPattern
from .plugins import check_mock_coverage, simulate_ci
from .reporter import AuditReporter
from .scanner import scan_workspace

__version__ = "2.2.0"
__all__ = [
    "AuditReporter",
    "AuditResult",
    "CodeAnalyzer",
    "SecurityPattern",
    "check_mock_coverage",
    "load_config",
    "scan_workspace",
    "simulate_ci",
]
