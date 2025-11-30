#!/usr/bin/env python3
"""Mock Validator CLI - Test mock validation tool.

Command-line interface for the TestMockValidator core engine.

Usage:
    python -m scripts.cli.mock_validate
    python -m scripts.cli.mock_validate --fix-found-issues

Author: DevOps Engineering Team
License: MIT
Version: 2.0.0
"""

import argparse
import logging
import sys
from pathlib import Path

from scripts.core.mock_validator import TestMockValidator
from scripts.utils.banner import print_startup_banner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Main CLI entry point with banner injection."""
    # Inject startup banner
    print_startup_banner(
        tool_name="Mock Validator",
        version="2.0.0",
        description="Test Mock System Validation and Integrity Checker",
        script_path=Path(__file__),
    )

    parser = argparse.ArgumentParser(
        description="Test Mock Validator - Validation System",
    )

    parser.add_argument(
        "--fix-found-issues",
        action="store_true",
        help="Automatically fix found issues",
    )

    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace path (default: current directory)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Validate workspace
        workspace = args.workspace.resolve()
        if not workspace.exists():
            logger.error("Workspace not found: %s", workspace)
            return 1

        # Execute validation
        validator = TestMockValidator(workspace)

        # Fix issues if requested
        if args.fix_found_issues:
            fixed = validator.fix_common_issues()
            if fixed > 0:
                print(f"✅ {fixed} issues fixed automatically")  # noqa: T201

        # Run full validation
        results = validator.run_full_validation()

        # Display results
        print("\n🔍 VALIDATION RESULTS")  # noqa: T201
        print("=" * 40)  # noqa: T201

        for validation_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{validation_name.replace('_', ' ').title()}: {status}")  # noqa: T201

        # Summary
        success_count = sum(results.values())
        total_count = len(results)
        success_rate = success_count / total_count

        print(  # noqa: T201
            f"\n📊 SUMMARY: {success_count}/{total_count} validations passed "
            f"({success_rate:.1%})",
        )

        if validator.validation_errors:
            print(f"\n⚠️  {len(validator.validation_errors)} issues found")  # noqa: T201

            if not args.fix_found_issues:
                print("💡 Use --fix-found-issues to automatically fix")  # noqa: T201

        # Exit code
        return 0 if success_rate >= 0.8 else 1  # 80% minimum success

    except KeyboardInterrupt:
        logger.info("Validation cancelled by user")
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
