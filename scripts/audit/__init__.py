"""Code Audit Package - Modular Security and Quality Auditor."""

from .config import load_config
from .models import AuditResult, SecurityPattern
from .scanner import scan_workspace

__version__ = "2.2.0"
__all__ = ["AuditResult", "SecurityPattern", "load_config", "scan_workspace"]
