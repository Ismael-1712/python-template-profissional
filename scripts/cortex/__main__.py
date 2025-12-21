"""CORTEX - Documentation as Code CLI Entry Point.

This is the main entry point for the cortex command-line tool.
It delegates to the cli module which contains all command definitions.

Usage:
    python -m scripts.cortex [COMMAND] [ARGS]

Examples:
    python -m scripts.cortex init docs/guide.md
    python -m scripts.cortex audit
    python -m scripts.cortex map
"""

from scripts.cortex.cli import main

if __name__ == "__main__":
    main()
