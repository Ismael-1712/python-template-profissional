#!/usr/bin/env python3
"""CORTEX CLI - Backward Compatibility Wrapper.

This file maintains backward compatibility for existing workflows that call:
    python scripts/cli/cortex.py [COMMAND]

It simply forwards to the new modular package structure:
    python -m scripts.cortex [COMMAND]

The actual CLI implementation has been refactored into scripts/cortex/
following Single Responsibility Principle and modular architecture.

Migration: scripts/cli/cortex.py (2113 lines) → scripts/cortex/ (package)
Protocol: docs/guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md
"""

from scripts.cortex.cli import main

if __name__ == "__main__":
    main()
