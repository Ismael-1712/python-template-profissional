"""Audit Dashboard - Modular DevOps Metrics Tracking.

This package provides enterprise-grade audit metrics tracking,
dashboard generation, and reporting capabilities.
"""

from __future__ import annotations

from scripts.audit_dashboard.dashboard import AuditDashboard
from scripts.audit_dashboard.models import (
    AuditHistoryRecord,
    AuditMetricsError,
    MetricsConfiguration,
    MonthlyStatistics,
    PatternStatistics,
)

__version__ = "2.0.0"
__all__ = [
    "AuditDashboard",
    "AuditHistoryRecord",
    "AuditMetricsError",
    "MetricsConfiguration",
    "MonthlyStatistics",
    "PatternStatistics",
]
