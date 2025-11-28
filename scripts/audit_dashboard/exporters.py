"""Export functionality for audit metrics.

This module provides exporters for different output formats:
HTML dashboards, JSON exports, and console reports.
"""

import gettext
import html
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

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


class HTMLExporter:
    """Export audit metrics as HTML dashboard."""

    def __init__(self, template_path: Path | None = None) -> None:
        """Initialize HTML exporter.

        Args:
            template_path: Path to HTML template file (defaults to bundled template)

        """
        if template_path is None:
            template_path = Path(__file__).parent / "templates" / "dashboard.html"
        self.template_path = template_path

    def export(self, metrics: dict[str, Any]) -> str:
        """Generate HTML dashboard from metrics.

        Args:
            metrics: Metrics dictionary

        Returns:
            Complete HTML string

        """
        template_data = self._prepare_template_data(metrics)
        return self._render_html_template(template_data)

    def _prepare_template_data(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Prepare sanitized data for HTML template.

        Args:
            metrics: Raw metrics dictionary

        Returns:
            Dictionary with sanitized data for template

        """
        # Sanitize all string data for HTML output
        sanitized_patterns = []
        for pattern, data in sorted(
            metrics["pattern_statistics"].items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )[:10]:
            severity_class = (
                "severity-high"
                if data["severity_distribution"]["HIGH"] > 0
                else "severity-medium"
            )
            sanitized_patterns.append(
                {
                    "pattern": html.escape(str(pattern)),
                    "count": data["count"],
                    "files_count": len(data["files_affected"]),
                    "severity_class": severity_class,
                },
            )

        sanitized_monthly = []
        for month, data in sorted(metrics["monthly_stats"].items(), reverse=True)[:6]:
            sanitized_monthly.append(
                {
                    "month": html.escape(str(month)),
                    "audits": data["audits"],
                    "failures_prevented": data["failures_prevented"],
                },
            )

        sanitized_history = []
        for audit in metrics["audit_history"][-10:]:
            try:
                timestamp = datetime.fromisoformat(audit["timestamp"]).strftime(
                    "%d/%m %H:%M",
                )
            except (ValueError, TypeError) as e:
                logger.debug(
                    "Invalid timestamp format for %s: %s",
                    audit.get("timestamp"),
                    e,
                )
                timestamp = "N/A"

            sanitized_history.append(
                {
                    "timestamp": html.escape(timestamp),
                    "status_emoji": "✅"
                    if audit.get("ci_simulation_passed", True)
                    else "❌",
                    "failures_prevented": audit["failures_prevented"],
                    "time_saved": audit["time_saved"],
                },
            )

        return {
            "last_update": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "audits_performed": metrics["audits_performed"],
            "failures_prevented": metrics["failures_prevented"],
            "time_saved_hours": metrics["time_saved_minutes"] / 60,
            "success_rate": metrics["success_rate"],
            "patterns": sanitized_patterns,
            "monthly": sanitized_monthly,
            "history": sanitized_history,
            "generation_time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }

    def _render_html_template(self, data: dict[str, Any]) -> str:
        """Render HTML template with provided data.

        Args:
            data: Template data dictionary

        Returns:
            Rendered HTML string

        """
        # Build HTML lists for dynamic content
        pattern_stats_html = "".join(
            [
                """
                <li class="pattern-item">
                    <span class="{severity_class}">
                        🔍 {pattern}
                    </span>
                    <span>
                        {count_text}
                    </span>
                </li>
            """.format(
                    severity_class=pattern["severity_class"],
                    pattern=pattern["pattern"][:15],
                    count_text=_("{count} em {files} arquivos").format(
                        count=pattern["count"],
                        files=pattern["files_count"],
                    ),
                )
                for pattern in data["patterns"]
            ],
        )

        monthly_stats_html = "".join(
            [
                """
                <li class="pattern-item">
                    <span>📅 {month}</span>
                    <span>
                        {stats_text}
                    </span>
                </li>
            """.format(
                    month=month["month"],
                    stats_text=_("{audits} auditorias, {failures} err").format(
                        audits=month["audits"],
                        failures=month["failures_prevented"],
                    ),
                )
                for month in data["monthly"]
            ],
        )

        audit_history_html = "".join(
            [
                """
                <li class="pattern-item">
                    <span>{emoji} {timestamp}</span>
                    <span>
                        {history_text}
                    </span>
                </li>
            """.format(
                    emoji=audit["status_emoji"],
                    timestamp=audit["timestamp"],
                    history_text=_("{failures} falhas, {time}min").format(
                        failures=audit["failures_prevented"],
                        time=audit["time_saved"],
                    ),
                )
                for audit in data["history"]
            ],
        )

        # Load template from file
        with self.template_path.open(encoding="utf-8") as f:
            html_template = f.read()

        # Render template with data
        return html_template.format(
            page_title=_("📊 Dashboard - Auditoria DevOps"),
            header_title=_("📊 Dashboard de Auditoria DevOps"),
            header_subtitle=_(
                "Monitoramento de falhas evitadas e métricas de produtividade CI/CD",
            ),
            last_update_label=_("Última atualização"),
            last_update=data["last_update"],
            audits_performed=data["audits_performed"],
            audits_label=_("Auditorias Realizadas"),
            failures_prevented=data["failures_prevented"],
            failures_label=_("Falhas Evitadas"),
            time_saved=data["time_saved_hours"],
            time_label=_("Tempo Economizado"),
            success_rate=data["success_rate"],
            success_label=_("Taxa de Sucesso"),
            patterns_title=_("🔍 Padrões Mais Detectados"),
            pattern_stats_html=pattern_stats_html,
            monthly_title=_("📈 Estatísticas Mensais"),
            monthly_stats_html=monthly_stats_html,
            history_title=_("📋 Histórico Recente (Últimas 10 Auditorias)"),
            audit_history_html=audit_history_html,
            footer_text=_("🤖 Sistema de Auditoria Preventiva DevOps"),
            generated_label=_("Gerado automaticamente em"),
            generation_time=data["generation_time"],
        )


class JSONExporter:
    """Export audit metrics as JSON."""

    @staticmethod
    def export(metrics: dict[str, Any]) -> str:
        """Export metrics as formatted JSON string.

        Args:
            metrics: Metrics dictionary

        Returns:
            JSON formatted string

        """
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "metrics": metrics.copy(),
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)


class ConsoleReporter:
    """Print formatted dashboard to console."""

    @staticmethod
    def print_dashboard(metrics: dict[str, Any]) -> None:
        """Print formatted dashboard to console.

        Args:
            metrics: Metrics dictionary

        """
        print(_("📊 DASHBOARD DE AUDITORIA DEVOPS"))
        print("=" * 50)

        print(_("\n🎯 MÉTRICAS PRINCIPAIS:"))
        print(
            _("   • Auditorias realizadas: {count}").format(
                count=metrics["audits_performed"],
            ),
        )
        print(
            _("   • Falhas evitadas: {count}").format(
                count=metrics["failures_prevented"],
            ),
        )
        time_hours = metrics["time_saved_minutes"] / 60
        print(
            _("   • Tempo economizado: {hours:.1f} horas").format(hours=time_hours),
        )
        print(
            _("   • Taxa de sucesso: {rate:.1f}%").format(
                rate=metrics["success_rate"],
            ),
        )

        if metrics["pattern_statistics"]:
            print(_("\n🔍 PADRÕES MAIS DETECTADOS:"))
            for pattern, data in sorted(
                metrics["pattern_statistics"].items(),
                key=lambda x: x[1]["count"],
                reverse=True,
            )[:5]:
                severity = "🔴" if data["severity_distribution"]["HIGH"] > 0 else "🟡"
                print(
                    _("   {severity} {pattern}: {count} ocorrências").format(
                        severity=severity,
                        pattern=pattern,
                        count=data["count"],
                    ),
                )

        if metrics["audit_history"]:
            print(_("\n📈 ÚLTIMAS AUDITORIAS:"))
            for audit in metrics["audit_history"][-5:]:
                try:
                    timestamp = datetime.fromisoformat(audit["timestamp"]).strftime(
                        "%d/%m %H:%M",
                    )
                except (ValueError, TypeError) as e:
                    logger.debug(
                        "Invalid timestamp format for %s: %s",
                        audit.get("timestamp"),
                        e,
                    )
                    timestamp = "N/A"

                status = "✅" if audit.get("ci_simulation_passed", True) else "❌"
                failures = audit["failures_prevented"]
                print(
                    _("   {status} {timestamp}: {failures} falhas evitadas").format(
                        status=status,
                        timestamp=timestamp,
                        failures=failures,
                    ),
                )
