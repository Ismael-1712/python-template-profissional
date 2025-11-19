"""Code Audit Package - Modular Security and Quality Auditor."""

from .config import load_config
from .models import AuditResult, SecurityPattern

__version__ = "2.2.0"
__all__ = ["AuditResult", "SecurityPattern", "load_config"]
