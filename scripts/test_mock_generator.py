#!/usr/bin/env python3
"""[DEPRECATED] Test Mock Generator - Compatibility Wrapper.

⚠️  This script location is deprecated!

New location: python -m scripts.cli.mock_generate

This wrapper will be removed in version 3.0.0.
Please update your scripts and automation.
"""

import sys
import warnings
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.cli.mock_generate import main  # noqa: E402
from scripts.utils.banner import print_deprecation_warning  # noqa: E402

if __name__ == "__main__":
    print_deprecation_warning(
        old_path="scripts/test_mock_generator.py",
        new_path="scripts.cli.mock_generate",
        removal_version="3.0.0",
    )

    warnings.warn(
        "scripts/test_mock_generator.py is deprecated. "
        "Use 'python -m scripts.cli.mock_generate' instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    sys.exit(main())
