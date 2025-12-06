#!/usr/bin/env python3
"""DEPRECATED: Backward compatibility wrapper for Dev Doctor.

This file will be removed in v3.0.0.
Please update your scripts to use the new location.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.banner import print_deprecation_warning  # noqa: E402

print_deprecation_warning(
    old_path="scripts/doctor.py",
    new_path="scripts.cli.doctor",
    removal_version="3.0.0",
)

warnings.warn(
    "scripts/doctor.py is deprecated and will be removed in v3.0.0. "
    "Use 'python -m scripts.cli.doctor' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Delegate to new CLI
from scripts.cli.doctor import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
