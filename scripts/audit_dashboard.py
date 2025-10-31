#!/usr/bin/env python3
"""
DevOps Audit Metrics Dashboard.

Enterprise-grade dashboard for tracking CI/CD audit metrics, prevented failures,
and productivity improvements across development workflows.

This tool provides:
- Real-time audit metrics tracking
- HTML dashboard generation with security sanitization
- Thread-safe metrics persistence
- Configurable reporting intervals
- Export capabilities for external monitoring systems

Usage:
    python scripts/audit_dashboard.py [options]
    python scripts/audit_dashboard.py --export-html
    python scripts/audit_dashboard.py --reset-stats
    python scripts/audit_dashboard.py --export-json metrics.json

Author: DevOps Engineering Team
License: MIT
"""

import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import argparse
import html

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("audit_dashboard.log", mode="a"),
    ]
)
logger = logging.getLogger(__name__)


class AuditMetricsError(Exception):
    """Custom exception for audit metrics operations."""
    pass


class AuditDashboard:
    """
    Thread-safe dashboard for DevOps audit metrics tracking.
    
    Provides comprehensive metrics collection, persistence, and reporting
    for CI/CD audit operations with enterprise-grade reliability.
    """

    # Configuration constants
    DEFAULT_TIME_PER_FAILURE_MINUTES = 7
    MAX_HISTORY_RECORDS = 50
    METRICS_FILE_PERMISSIONS = 0o644
    
    def __init__(
        self, 
        workspace_root: Optional[Path] = None,
        metrics_filename: str = "audit_metrics.json"
    ) -> None:
        """
        Initialize audit dashboard with thread-safe operations.
        
        Args:
            workspace_root: Root directory for metrics storage
            metrics_filename: Name of the metrics file
        """
        self.workspace_root = workspace_root or Path.cwd()
        self.metrics_file = self.workspace_root / metrics_filename
        self._lock = threading.RLock()
        self._metrics: Dict[str, Any] = {}
        
        # Ensure workspace directory exists
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        
        self._load_metrics()

    def _load_metrics(self) -> None:
        """Load metrics from persistent storage with error handling."""
        with self._lock:
            try:
                if self.metrics_file.exists():
                    with open(self.metrics_file, 'r', encoding='utf-8') as f:
                        self._metrics = json.load(f)
                    logger.info(f"Loaded metrics from {self.metrics_file}")
                else:
                    self._metrics = self._get_default_metrics()
                    logger.info("Initialized default metrics")
                    
                # Validate and migrate metrics structure
                self._validate_metrics_structure()
                
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load metrics: {e}")
                logger.info("Initializing with default metrics")
                self._metrics = self._get_default_metrics()

    def _get_default_metrics(self) -> Dict[str, Any]:
        """Return default metrics structure."""
        return {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "audits_performed": 0,
            "failures_prevented": 0,
            "time_saved_minutes": 0,
            "last_audit": None,
            "audit_history": [],
            "pattern_statistics": {},
            "monthly_stats": {},
            "success_rate": 100.0,
            "configuration": {
                "time_per_failure_minutes": self.DEFAULT_TIME_PER_FAILURE_MINUTES,
                "max_history_records": self.MAX_HISTORY_RECORDS
            }
        }

    def _validate_metrics_structure(self) -> None:
        """Validate and migrate metrics structure if needed."""
        required_keys = [
            "audits_performed", "failures_prevented", "time_saved_minutes",
            "audit_history", "pattern_statistics", "monthly_stats", "success_rate"
        ]
        
        for key in required_keys:
            if key not in self._metrics:
                logger.warning(f"Missing metric key '{key}', initializing with default")
                if key in ["audits_performed", "failures_prevented", "time_saved_minutes"]:
                    self._metrics[key] = 0
                elif key == "success_rate":
                    self._metrics[key] = 100.0
                else:
                    self._metrics[key] = {}

        # Ensure configuration exists
        if "configuration" not in self._metrics:
            self._metrics["configuration"] = {
                "time_per_failure_minutes": self.DEFAULT_TIME_PER_FAILURE_MINUTES,
                "max_history_records": self.MAX_HISTORY_RECORDS
            }

    def _save_metrics(self) -> None:
        """Save metrics to persistent storage with atomic write."""
        try:
            # Atomic write using temporary file
            temp_file = self.metrics_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._metrics, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(self.metrics_file)
            
            # Set proper permissions
            os.chmod(self.metrics_file, self.METRICS_FILE_PERMISSIONS)
            
            logger.debug(f"Metrics saved to {self.metrics_file}")
            
        except IOError as e:
            logger.error(f"Failed to save metrics: {e}")
            raise AuditMetricsError(f"Cannot save metrics: {e}") from e

    def record_audit(self, audit_result: Dict[str, Any]) -> None:
        """
        Record audit results with comprehensive validation.
        
        Args:
            audit_result: Dictionary containing audit results with structure:
                {
                    "external_dependencies": [{"severity": str, "pattern": str, "file": str}, ...],
                    "ci_simulation": {"tests_passed": bool},
                    ...
                }
        """
        if not isinstance(audit_result, dict):
            raise ValueError("audit_result must be a dictionary")

        with self._lock:
            try:
                now = datetime.now(timezone.utc).isoformat()
                
                self._metrics["audits_performed"] += 1
                self._metrics["last_audit"] = now

                # Process external dependencies
                dependencies = audit_result.get("external_dependencies", [])
                if not isinstance(dependencies, list):
                    logger.warning("external_dependencies is not a list, treating as empty")
                    dependencies = []

                failures_prevented = len(dependencies)
                high_severity_count = sum(
                    1 for dep in dependencies 
                    if isinstance(dep, dict) and dep.get("severity") == "HIGH"
                )

                self._metrics["failures_prevented"] += failures_prevented

                # Calculate time saved with configurable rate
                time_per_failure = self._metrics["configuration"]["time_per_failure_minutes"]
                time_saved = failures_prevented * time_per_failure
                self._metrics["time_saved_minutes"] += time_saved

                # Update pattern statistics
                self._update_pattern_statistics(dependencies)

                # Update monthly statistics
                self._update_monthly_statistics(failures_prevented, time_saved)

                # Record audit history
                self._record_audit_history(
                    now, failures_prevented, high_severity_count, 
                    time_saved, audit_result
                )

                # Update success rate
                self._update_success_rate()

                # Persist changes
                self._save_metrics()
                
                logger.info(
                    f"Audit recorded: {failures_prevented} failures prevented, "
                    f"{time_saved} minutes saved"
                )

            except Exception as e:
                logger.error(f"Failed to record audit: {e}")
                raise AuditMetricsError(f"Cannot record audit: {e}") from e

    def _update_pattern_statistics(self, dependencies: List[Dict[str, Any]]) -> None:
        """Update pattern detection statistics."""
        for dep in dependencies:
            if not isinstance(dep, dict):
                continue
                
            pattern = dep.get("pattern", "unknown")
            file_path = dep.get("file", "")
            severity = dep.get("severity", "MEDIUM")

            if pattern not in self._metrics["pattern_statistics"]:
                self._metrics["pattern_statistics"][pattern] = {
                    "count": 0,
                    "files_affected": [],
                    "severity_distribution": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
                }

            pattern_stats = self._metrics["pattern_statistics"][pattern]
            pattern_stats["count"] += 1
            
            if file_path and file_path not in pattern_stats["files_affected"]:
                pattern_stats["files_affected"].append(file_path)
            
            if severity in pattern_stats["severity_distribution"]:
                pattern_stats["severity_distribution"][severity] += 1

    def _update_monthly_statistics(self, failures_prevented: int, time_saved: int) -> None:
        """Update monthly aggregated statistics."""
        month_key = datetime.now().strftime("%Y-%m")
        
        if month_key not in self._metrics["monthly_stats"]:
            self._metrics["monthly_stats"][month_key] = {
                "audits": 0,
                "failures_prevented": 0, 
                "time_saved": 0
            }

        monthly = self._metrics["monthly_stats"][month_key]
        monthly["audits"] += 1
        monthly["failures_prevented"] += failures_prevented
        monthly["time_saved"] += time_saved

    def _record_audit_history(
        self, 
        timestamp: str, 
        failures_prevented: int,
        high_severity_count: int, 
        time_saved: int, 
        audit_result: Dict[str, Any]
    ) -> None:
        """Record individual audit in history with size management."""
        audit_record = {
            "timestamp": timestamp,
            "failures_prevented": failures_prevented,
            "high_severity": high_severity_count,
            "time_saved": time_saved,
            "ci_simulation_passed": (
                audit_result.get("ci_simulation", {}).get("tests_passed", True)
            )
        }

        self._metrics["audit_history"].append(audit_record)
        
        # Maintain history size limit
        max_records = self._metrics["configuration"]["max_history_records"]
        if len(self._metrics["audit_history"]) > max_records:
            self._metrics["audit_history"] = self._metrics["audit_history"][-max_records:]

    def _update_success_rate(self) -> None:
        """Calculate and update success rate based on CI simulation results."""
        if not self._metrics["audit_history"]:
            self._metrics["success_rate"] = 100.0
            return

        successful_audits = sum(
            1 for audit in self._metrics["audit_history"]
            if audit.get("ci_simulation_passed", True)
        )
        
        total_audits = len(self._metrics["audit_history"])
        self._metrics["success_rate"] = (successful_audits / total_audits) * 100

    def generate_html_dashboard(self) -> str:
        """
        Generate secure HTML dashboard with sanitized content.
        
        Returns:
            HTML string with complete dashboard
        """
        with self._lock:
            template_data = self._prepare_template_data()
            return self._render_html_template(template_data)

    def _prepare_template_data(self) -> Dict[str, Any]:
        """Prepare sanitized data for HTML template."""
        # Sanitize all string data for HTML output
        sanitized_patterns = []
        for pattern, data in sorted(
            self._metrics["pattern_statistics"].items(), 
            key=lambda x: x[1]["count"], 
            reverse=True
        )[:10]:
            severity_class = (
                "severity-high" if data["severity_distribution"]["HIGH"] > 0 
                else "severity-medium"
            )
            sanitized_patterns.append({
                "pattern": html.escape(str(pattern)),
                "count": data["count"],
                "files_count": len(data["files_affected"]),
                "severity_class": severity_class
            })

        sanitized_monthly = []
        for month, data in sorted(self._metrics["monthly_stats"].items(), reverse=True)[:6]:
            sanitized_monthly.append({
                "month": html.escape(str(month)),
                "audits": data["audits"],
                "failures_prevented": data["failures_prevented"]
            })

        sanitized_history = []
        for audit in self._metrics["audit_history"][-10:]:
            try:
                timestamp = datetime.fromisoformat(audit["timestamp"]).strftime("%d/%m %H:%M")
            except (ValueError, TypeError):
                timestamp = "N/A"
            
            sanitized_history.append({
                "timestamp": html.escape(timestamp),
                "status_emoji": "✅" if audit.get("ci_simulation_passed", True) else "❌",
                "failures_prevented": audit["failures_prevented"],
                "time_saved": audit["time_saved"]
            })

        return {
            "last_update": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "audits_performed": self._metrics["audits_performed"],
            "failures_prevented": self._metrics["failures_prevented"],
            "time_saved_hours": self._metrics["time_saved_minutes"] / 60,
            "success_rate": self._metrics["success_rate"],
            "patterns": sanitized_patterns,
            "monthly": sanitized_monthly,
            "history": sanitized_history,
            "generation_time": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

    def _render_html_template(self, data: Dict[str, Any]) -> str:
        """Render HTML template with provided data."""
        pattern_stats_html = "".join([
            f'''
                <li class="pattern-item">
                    <span class="{pattern['severity_class']}">🔍 {pattern['pattern']}</span>
                    <span>{pattern['count']} ocorrências em {pattern['files_count']} arquivos</span>
                </li>
            ''' for pattern in data["patterns"]
        ])

        monthly_stats_html = "".join([
            f'''
                <li class="pattern-item">
                    <span>📅 {month['month']}</span>
                    <span>{month['audits']} auditorias, {month['failures_prevented']} falhas evitadas</span>
                </li>
            ''' for month in data["monthly"]
        ])

        audit_history_html = "".join([
            f'''
                <li class="pattern-item">
                    <span>{audit['status_emoji']} {audit['timestamp']}</span>
                    <span>{audit['failures_prevented']} falhas evitadas, {audit['time_saved']}min economizados</span>
                </li>
            ''' for audit in data["history"]
        ])

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="DevOps Audit Dashboard">
    <title>📊 Dashboard - Auditoria DevOps</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #1976d2, #42a5f5);
            color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 20px;
        }}
        .stat-card {{
            background: white; padding: 20px; border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }}
        .stat-card:hover {{ transform: translateY(-2px); }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; color: #1976d2; }}
        .stat-label {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        .chart-container {{
            background: white; padding: 20px; border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;
        }}
        .pattern-list {{ list-style: none; padding: 0; }}
        .pattern-item {{ 
            display: flex; justify-content: space-between; 
            padding: 10px; border-bottom: 1px solid #eee;
            transition: background-color 0.2s ease;
        }}
        .pattern-item:hover {{ background-color: #f9f9f9; }}
        .severity-high {{ color: #f44336; font-weight: bold; }}
        .severity-medium {{ color: #ff9800; }}
        .severity-low {{ color: #4caf50; }}
        .footer {{ text-align: center; color: #666; margin-top: 40px; }}
        .footer small {{ font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Dashboard de Auditoria DevOps</h1>
            <p>Monitoramento de falhas evitadas e métricas de produtividade CI/CD</p>
            <p><small>Última atualização: {data["last_update"]}</small></p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{data["audits_performed"]}</div>
                <div class="stat-label">Auditorias Realizadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{data["failures_prevented"]}</div>
                <div class="stat-label">Falhas Evitadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{data["time_saved_hours"]:.1f}h</div>
                <div class="stat-label">Tempo Economizado</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{data["success_rate"]:.1f}%</div>
                <div class="stat-label">Taxa de Sucesso</div>
            </div>
        </div>

        <div class="chart-container">
            <h3>🔍 Padrões Mais Detectados</h3>
            <ul class="pattern-list">
                {pattern_stats_html}
            </ul>
        </div>

        <div class="chart-container">
            <h3>📈 Estatísticas Mensais</h3>
            <ul class="pattern-list">
                {monthly_stats_html}
            </ul>
        </div>

        <div class="chart-container">
            <h3>📋 Histórico Recente (Últimas 10 Auditorias)</h3>
            <ul class="pattern-list">
                {audit_history_html}
            </ul>
        </div>

        <div class="footer">
            <p>🤖 Sistema de Auditoria Preventiva DevOps</p>
            <p><small>Gerado automaticamente em {data["generation_time"]}</small></p>
        </div>
    </div>
</body>
</html>'''

    def print_console_dashboard(self) -> None:
        """Print formatted dashboard to console."""
        with self._lock:
            print("📊 DASHBOARD DE AUDITORIA DEVOPS")
            print("=" * 50)

            print("\n🎯 MÉTRICAS PRINCIPAIS:")
            print(f"   • Auditorias realizadas: {self._metrics['audits_performed']}")
            print(f"   • Falhas evitadas: {self._metrics['failures_prevented']}")
            print(f"   • Tempo economizado: {self._metrics['time_saved_minutes'] / 60:.1f} horas")
            print(f"   • Taxa de sucesso: {self._metrics['success_rate']:.1f}%")

            if self._metrics["pattern_statistics"]:
                print("\n🔍 PADRÕES MAIS DETECTADOS:")
                for pattern, data in sorted(
                    self._metrics["pattern_statistics"].items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )[:5]:
                    severity = "🔴" if data["severity_distribution"]["HIGH"] > 0 else "🟡"
                    print(f"   {severity} {pattern}: {data['count']} ocorrências")

            if self._metrics["audit_history"]:
                print("\n📈 ÚLTIMAS AUDITORIAS:")
                for audit in self._metrics["audit_history"][-5:]:
                    try:
                        timestamp = datetime.fromisoformat(audit["timestamp"]).strftime("%d/%m %H:%M")
                    except (ValueError, TypeError):
                        timestamp = "N/A"
                    
                    status = "✅" if audit.get("ci_simulation_passed", True) else "❌"
                    print(f"   {status} {timestamp}: {audit['failures_prevented']} falhas evitadas")

    def export_html_dashboard(self) -> Path:
        """
        Export dashboard as HTML file.
        
        Returns:
            Path to generated HTML file
        """
        try:
            html_content = self.generate_html_dashboard()
            html_file = self.workspace_root / "audit_dashboard.html"

            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            os.chmod(html_file, self.METRICS_FILE_PERMISSIONS)
            logger.info(f"HTML dashboard exported to {html_file}")
            return html_file
            
        except IOError as e:
            raise AuditMetricsError(f"Cannot export HTML dashboard: {e}") from e

    def export_json_metrics(self, output_file: Optional[Path] = None) -> Path:
        """
        Export metrics as JSON for external monitoring systems.
        
        Args:
            output_file: Optional custom output file path
            
        Returns:
            Path to exported JSON file
        """
        with self._lock:
            try:
                if output_file is None:
                    output_file = self.workspace_root / "audit_metrics_export.json"

                export_data = {
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "metrics": self._metrics.copy()
                }

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                os.chmod(output_file, self.METRICS_FILE_PERMISSIONS)
                logger.info(f"Metrics exported to {output_file}")
                return output_file
                
            except IOError as e:
                raise AuditMetricsError(f"Cannot export JSON metrics: {e}") from e

    def reset_metrics(self) -> None:
        """Reset all metrics to default state."""
        with self._lock:
            try:
                # Backup current metrics
                if self.metrics_file.exists():
                    backup_file = self.metrics_file.with_suffix('.backup')
                    self.metrics_file.rename(backup_file)
                    logger.info(f"Metrics backed up to {backup_file}")

                self._metrics = self._get_default_metrics()
                self._save_metrics()
                logger.info("Metrics reset to default state")
                
            except IOError as e:
                raise AuditMetricsError(f"Cannot reset metrics: {e}") from e

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get current metrics summary for programmatic access.
        
        Returns:
            Dictionary with current metrics
        """
        with self._lock:
            return {
                "audits_performed": self._metrics["audits_performed"],
                "failures_prevented": self._metrics["failures_prevented"],
                "time_saved_hours": self._metrics["time_saved_minutes"] / 60,
                "success_rate": self._metrics["success_rate"],
                "last_audit": self._metrics.get("last_audit"),
                "pattern_count": len(self._metrics["pattern_statistics"]),
                "history_count": len(self._metrics["audit_history"])
            }


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="DevOps Audit Metrics Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Show console dashboard
  %(prog)s --export-html            Export HTML dashboard
  %(prog)s --export-json metrics.json  Export metrics as JSON
  %(prog)s --reset-stats            Reset all statistics
        """
    )
    
    parser.add_argument(
        "--export-html",
        action="store_true",
        help="Export dashboard as HTML file"
    )
    
    parser.add_argument(
        "--export-json",
        type=str,
        metavar="FILE",
        help="Export metrics as JSON to specified file"
    )
    
    parser.add_argument(
        "--reset-stats",
        action="store_true",
        help="Reset all statistics (creates backup)"
    )
    
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Workspace root directory (default: current directory)"
    )
    
    parser.add_argument(
        "--metrics-file",
        type=str,
        default="audit_metrics.json",
        help="Metrics file name (default: audit_metrics.json)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def main() -> int:
    """Main entry point with comprehensive error handling."""
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
            print(f"📄 Dashboard HTML exportado para: {html_file}")
            
        elif args.export_json:
            json_file = dashboard.export_json_metrics(Path(args.export_json))
            print(f"📊 Métricas exportadas para: {json_file}")
            
        elif args.reset_stats:
            dashboard.reset_metrics()
            print("🔄 Estatísticas resetadas com backup criado")
            
        else:
            dashboard.print_console_dashboard()
        
        return 0
        
    except AuditMetricsError as e:
        logger.error(f"Dashboard error: {e}")
        print(f"❌ Erro: {e}", file=sys.stderr)
        return 1
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\n⚠️  Operação cancelada pelo usuário")
        return 130
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"💥 Erro inesperado: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())