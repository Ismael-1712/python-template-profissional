#!/usr/bin/env python3
"""DevOps Audit Metrics Dashboard - Compatibility Wrapper.

⚠️  DEPRECATION NOTICE:
This file is now a compatibility wrapper for backward compatibility.
The actual implementation has been refactored into a modular package:
    scripts/audit_dashboard/ (package)

New code should import from:
    from audit_dashboard import AuditDashboard
    from audit_dashboard.cli import main

For CLI usage, you can still run this file directly:
    python3 scripts/audit_dashboard.py [options]

This wrapper will be maintained for one release cycle and then removed.

Enterprise-grade dashboard for tracking CI/CD audit metrics, prevented failures,
and productivity improvements across development workflows.

This tool provides:
- Real-time audit metrics tracking
- HTML dashboard generation with security sanitization
- Thread-safe metrics persistence
- Configurable reporting intervals
- Export capabilities for external monitoring systems

Usage:
    python3 scripts/audit_dashboard.py [options]
    python3 scripts/audit_dashboard.py --export-html
    python3 scripts/audit_dashboard.py --reset-stats
    python3 scripts/audit_dashboard.py --export-json metrics.json

Author: DevOps Engineering Team
License: MIT
Version: 2.0.0 (Refactored)
"""

import sys

# Re-export main classes for backward compatibility
from audit_dashboard import AuditDashboard, AuditMetricsError
from audit_dashboard.cli import main

__all__ = ["AuditDashboard", "AuditMetricsError", "main"]


if __name__ == "__main__":
    # Execute the new modular CLI
    sys.exit(main())
