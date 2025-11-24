"""Pytest configuration and fixtures.

This conftest.py file is automatically loaded by pytest before running tests.
It configures the Python path to ensure that the 'scripts' package is importable.
"""

import sys
from pathlib import Path

# Add project root to sys.path so that 'scripts' is importable
# This runs before test collection
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
