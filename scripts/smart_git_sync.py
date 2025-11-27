#!/usr/bin/env python3
"""Smart Git Synchronization CLI Wrapper.

A lightweight command-line interface for the Smart Git Sync orchestrator.
This script delegates all synchronization logic to the git_sync module.

Usage:
    python3 scripts/smart_git_sync.py [options]
    python3 scripts/smart_git_sync.py --dry-run
    python3 scripts/smart_git_sync.py --config custom_config.yaml

Author: DevOps Engineering Team
License: MIT
"""

import argparse
import logging
import sys
from pathlib import Path

from scripts.git_sync import SyncOrchestrator, load_config
from scripts.git_sync.exceptions import SyncError

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("smart_git_sync.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the Smart Git Sync CLI."""
    parser = argparse.ArgumentParser(
        description="Smart Git Synchronization with Preventive Audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/smart_git_sync.py           # Basic sync
  python3 scripts/smart_git_sync.py --dry-run       # Test without changes
  python3 scripts/smart_git_sync.py --config sync.yaml  # Custom config
  python3 scripts/smart_git_sync.py --no-audit      # Skip audit (not recommended)
        """,
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration YAML file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--no-audit",
        action="store_true",
        help="Skip code audit (not recommended)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = load_config(args.config)

    # Override config based on CLI arguments
    if args.no_audit:
        config["audit_enabled"] = False
        logger.warning("Code audit disabled via --no-audit flag")

    # Determine workspace root
    workspace_root = Path(__file__).parent.parent

    try:
        # Initialize and execute sync
        sync_manager = SyncOrchestrator(
            workspace_root=workspace_root,
            config=config,
            dry_run=args.dry_run,
        )

        success = sync_manager.execute_sync()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.warning("Synchronization interrupted by user")
        sys.exit(130)  # Standard SIGINT exit code
    except SyncError:
        logger.exception("Synchronization error")
        sys.exit(1)
    except Exception as e:
        logger.critical("UNEXPECTED ERROR (possible bug): %s", e, exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
