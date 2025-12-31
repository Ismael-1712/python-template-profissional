#!/usr/bin/env python3
"""Mock Generator CLI - Test mock generation tool.

Command-line interface for the TestMockGenerator core engine.

Usage:
    python -m scripts.cli.mock_generate --scan
    python -m scripts.cli.mock_generate --apply --dry-run

Author: DevOps Engineering Team
License: MIT
Version: 2.0.0
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from scripts.core.mock_ci.models_pydantic import MockCIConfig
from scripts.core.mock_generator import TestMockGenerator
from scripts.utils.banner import print_startup_banner
from scripts.utils.context import trace_context
from scripts.utils.logger import setup_logging

# Configure structured logging
logger = setup_logging(__name__)


# TODO: Refactor God Function - split CLI parsing from generation logic
def main() -> int:  # noqa: C901
    """Main CLI entry point with banner injection."""
    # Inject startup banner
    print_startup_banner(
        tool_name="Mock Generator",
        version="2.0.0",
        description="Test Mock Generation and Auto-Correction System",
        script_path=Path(__file__),
    )

    parser = argparse.ArgumentParser(
        description="Test Mock Generator - Auto-Correction System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --scan                 # Scan and show suggestions
  %(prog)s --apply --dry-run      # Preview corrections
  %(prog)s --apply                # Apply corrections
  %(prog)s --scan --report report.json  # Generate JSON report
        """,
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan test files for problematic patterns",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply high-priority corrections automatically",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate application without modifying files (use with --apply)",
    )

    parser.add_argument(
        "--report",
        type=Path,
        help="Generate JSON report at specified file",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace path (default: current directory)",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if not args.scan and not args.apply:
        parser.error("Specify --scan or --apply")

    if args.dry_run and not args.apply:
        parser.error("--dry-run can only be used with --apply")

    try:
        # Initialize generator
        workspace = args.workspace.resolve()
        if not workspace.exists():
            logger.error("Workspace not found: %s", workspace)
            return 1

        # Locate config file
        script_dir = Path(__file__).parent.parent  # Go up to scripts/
        config_file = script_dir / "test_mock_config.yaml"

        if not config_file.exists():
            logger.error("Config file not found: %s", config_file)
            logger.error("Ensure 'test_mock_config.yaml' is in scripts/ directory")
            return 1

        # Load and validate config with Pydantic (Top-Down Injection)
        try:
            with config_file.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Automatic validation via Pydantic
            config = MockCIConfig.model_validate(config_data)
            logger.info("✅ YAML configuration validated successfully")

        except ValidationError as e:
            logger.error("❌ Validation error in YAML configuration:")
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                logger.error(f"  [{loc}]: {error['msg']}")
            return 1
        except Exception as e:
            logger.error(f"❌ Error loading configuration: {e}")
            return 1

        generator = TestMockGenerator(workspace, config)

        # Execute requested actions
        if args.scan:
            _report = generator.scan_test_files()
            generator.print_summary()

            if args.report:
                generator.generate_report(args.report)

        if args.apply:
            if not generator.suggestions:
                generator.scan_test_files()

            result = generator.apply_suggestions(dry_run=args.dry_run)

            if result["applied"] > 0 and not args.dry_run:
                print(f"\n✅ {result['applied']} corrections applied successfully!")  # noqa: T201
                print("💡 Recommended: Run tests to validate corrections:")  # noqa: T201
                print("   python3 -m pytest tests/")  # noqa: T201

        return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    with trace_context():
        sys.exit(main())
