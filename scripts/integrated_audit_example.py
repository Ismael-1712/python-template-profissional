#!/usr/bin/env python3
"""Integration example showing how to connect audit_dashboard.py with code_audit.py.

This example demonstrates enterprise-grade integration patterns for
tracking audit metrics in DevOps pipelines.
"""

import logging
import sys
from pathlib import Path

# Add the scripts directory to the path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

# Now we can safely import the local modules after modifying sys.path
from audit_dashboard import AuditDashboard, AuditMetricsError  # noqa: E402
from code_audit import CodeAuditor, print_summary, save_report  # noqa: E402

logger = logging.getLogger(__name__)


def run_integrated_audit(workspace_root: Path, config_path: Path = None) -> int:
    """Run code audit with dashboard metrics integration.

    Args:
        workspace_root: Root directory of the project
        config_path: Optional path to audit configuration

    Returns:
        Exit code (0 for success, >0 for failure)

    """
    try:
        # Initialize auditor
        auditor = CodeAuditor(workspace_root, config_path)

        # Run the audit
        logger.info("Starting integrated audit with dashboard tracking...")
        audit_report = auditor.run_audit()

        # Transform audit report for dashboard consumption
        dashboard_data = transform_audit_for_dashboard(audit_report)

        # Record metrics in dashboard
        try:
            dashboard = AuditDashboard(workspace_root)
            dashboard.record_audit(dashboard_data)
            logger.info("✅ Audit metrics recorded in dashboard")

            # Print dashboard summary
            print("\n" + "=" * 60)
            print("📊 DASHBOARD METRICS UPDATED")
            print("=" * 60)
            dashboard.print_console_dashboard()

        except AuditMetricsError as e:
            logger.warning(f"Failed to record dashboard metrics: {e}")
            # Don't fail the audit if dashboard recording fails

        # Save the audit report
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = workspace_root / f"audit_report_{timestamp}.json"
        save_report(audit_report, report_file, "json")

        # Print audit summary
        print_summary(audit_report)

        # Determine exit code based on audit results
        overall_status = audit_report["summary"]["overall_status"]
        if overall_status in ["CRITICAL", "FAIL"]:
            logger.error(f"Audit failed with status: {overall_status}")
            return 1
        if overall_status == "WARNING":
            logger.warning(f"Audit completed with warnings: {overall_status}")
            return 0  # Warnings don't fail the build
        logger.info(f"Audit passed with status: {overall_status}")
        return 0

    except Exception as e:
        logger.exception(f"Integrated audit failed: {e}")
        return 1


def transform_audit_for_dashboard(audit_report: dict) -> dict:
    """Transform code_audit.py report format to audit_dashboard.py expected format.

    Args:
        audit_report: Report from CodeAuditor.run_audit()

    Returns:
        Dictionary in format expected by AuditDashboard.record_audit()

    """
    # Extract external dependencies from findings
    external_dependencies = []

    for finding in audit_report.get("findings", []):
        # Map audit findings to dashboard dependencies format
        dependency = {
            "pattern": finding.get("category", "unknown"),
            "severity": finding.get("severity", "MEDIUM"),
            "file": finding.get("file", ""),
            "description": finding.get("description", ""),
            "line": finding.get("line", 0),
        }
        external_dependencies.append(dependency)

    # Format CI simulation results
    ci_simulation = audit_report.get("ci_simulation", {})
    formatted_ci_simulation = {
        "tests_passed": ci_simulation.get("passed", True),
        "exit_code": ci_simulation.get("exit_code", 0),
        "duration": ci_simulation.get("duration", "unknown"),
        "output": ci_simulation.get("stdout", ""),
    }

    # Return dashboard-compatible format
    return {
        "external_dependencies": external_dependencies,
        "ci_simulation": formatted_ci_simulation,
        "metadata": audit_report.get("metadata", {}),
        "mock_coverage": audit_report.get("mock_coverage", {}),
        "summary": audit_report.get("summary", {}),
    }


def main():
    """Main entry point for integrated audit."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Integrated code audit with dashboard metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to audit configuration YAML file",
    )

    parser.add_argument(
        "--workspace",
        type=Path,
        help="Workspace root directory (default: parent of this script)",
    )

    parser.add_argument(
        "--export-dashboard",
        action="store_true",
        help="Export HTML dashboard after audit",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Determine workspace root
    workspace_root = args.workspace or Path(__file__).parent.parent

    # --- INÍCIO DA CORREÇÃO ---
    # Define o caminho do config (relativo ao script)
    config_file = args.config  # Usa o config do usuário se fornecido
    if not config_file:
        # Se não, usa o padrão do nosso molde
        script_dir = Path(__file__).parent
        config_file = script_dir / "audit_config.yaml"

    if not config_file.exists():
        logger.error(
            f"Arquivo de configuração de auditoria não encontrado: {config_file}",
        )
        return 1

    # Run integrated audit
    exit_code = run_integrated_audit(
        workspace_root,
        config_file,
    )  # Passa o config_file corrigido
    # --- FIM DA CORREÇÃO ---

    # Export dashboard if requested
    if args.export_dashboard:
        try:
            dashboard = AuditDashboard(workspace_root)
            html_file = dashboard.export_html_dashboard()
            print(f"\n📄 Dashboard HTML exported to: {html_file}")
        except Exception as e:
            logger.warning(f"Failed to export dashboard: {e}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
