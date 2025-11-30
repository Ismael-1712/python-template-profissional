#!/usr/bin/env python3
"""DEPRECATED: Backward compatibility wrapper for Version Governor.

This file will be removed in v3.0.0.
Please update your scripts to use the new location.
"""

import sys
import warnings
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.banner import print_deprecation_warning  # noqa: E402

print_deprecation_warning(
    old_path="scripts/maintain_versions.py",
    new_path="scripts.cli.upgrade_python",
    removal_version="3.0.0",
)

warnings.warn(
    "scripts/maintain_versions.py is deprecated and will be removed in v3.0.0. "
    "Use 'python -m scripts.cli.upgrade_python' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Delegate to new CLI
from scripts.cli.upgrade_python import main  # noqa: E402

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nErro inesperado: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
