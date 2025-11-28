"""Command-line interface for the Audit Dashboard.

This module provides the CLI entry point and argument parsing.
"""

import argparse
import gettext
import logging
import os
import sys
from pathlib import Path

from scripts.audit_dashboard.dashboard import AuditDashboard
from scripts.audit_dashboard.models import AuditMetricsError

# i18n setup
_locale_dir = Path(__file__).parent.parent.parent / "locales"
try:
    _translation = gettext.translation(
        "messages",
        localedir=str(_locale_dir),
        languages=[os.getenv("LANGUAGE", "pt_BR")],
        fallback=True,
    )
    _ = _translation.gettext
except Exception:
    # Fallback if translations not found
    def _(message: str) -> str:
        return message


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("audit_dashboard.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser.

    Returns:
        Configured argument parser

    """
    parser = argparse.ArgumentParser(
        description="DevOps Audit Metrics Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Show console dashboard
  %(prog)s --export-html            Export HTML dashboard
  %(prog)s --export-json metrics.json  Export metrics as JSON
  %(prog)s --reset-stats            Reset all statistics
        """,
    )

    parser.add_argument(
        "--export-html",
        action="store_true",
        help="Export dashboard as HTML file",
    )

    parser.add_argument(
        "--export-json",
        type=str,
        metavar="FILE",
        help="Export metrics as JSON to specified file",
    )

    parser.add_argument(
        "--reset-stats",
        action="store_true",
        help="Reset all statistics (creates backup)",
    )

    parser.add_argument(
        "--workspace",
        type=Path,
        help="Workspace root directory (default: current directory)",
    )

    parser.add_argument(
        "--metrics-file",
        type=str,
        default="audit_metrics.json",
        help="Metrics file name (default: audit_metrics.json)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser


def main() -> int:
    """Main entry point with comprehensive error handling.

    Returns:
        Exit code (0 for success, non-zero for errors)

    """
    parser = create_argument_parser()
    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize dashboard
        workspace_root = args.workspace or Path.cwd()
        dashboard = AuditDashboard(workspace_root, args.metrics_file)

        # Execute requested action
        if args.export_html:
            html_file = dashboard.export_html_dashboard()
            print(_("📄 Dashboard HTML exportado para: {file}").format(file=html_file))

        elif args.export_json:
            json_file = dashboard.export_json_metrics(Path(args.export_json))
            print(_("📊 Métricas exportadas para: {file}").format(file=json_file))

        elif args.reset_stats:
            dashboard.reset_metrics()
            print(_("🔄 Estatísticas resetadas com backup criado"))

        else:
            dashboard.print_console_dashboard()
            # Mostrar dica sobre exportação HTML (exceto em modo verbose)
            if not args.verbose:
                tip_msg = (
                    "\n💡 Dica: Gere um relatório HTML interativo com: "
                    "python scripts/audit_dashboard.py --export-html"
                )
                print(tip_msg)  # noqa: T201

        return 0

    except AuditMetricsError as e:
        logger.error("Dashboard error: %s", e)
        print(_("❌ Erro: {error}").format(error=e), file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print(_("\n⚠️  Operação cancelada pelo usuário"))
        return 130

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        print(_("💥 Erro inesperado: {error}").format(error=e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
