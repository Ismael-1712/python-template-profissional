---
id: audit-dashboard-integration
title: Audit Dashboard Integration System
description: Architecture and integration guide for the visual audit dashboard
status: active
type: arch
version: 1.0.0
author: Ismael-1712
date: 2025-12-13
tags: [audit, dashboard, observability, cli]
linked_code: [scripts/audit_dashboard/__init__.py]
---

# Audit Dashboard Integration Guide

## Overview

O `audit_dashboard` é um sistema de métricas empresarial para rastreamento de auditorias DevOps, **totalmente integrado** ao `dev-audit` CLI para fornecer visibilidade completa sobre a efetividade das auditorias de CI/CD.

## CLI Integration (v2.0.0+)

### Uso Básico

O Dashboard agora está integrado diretamente no comando `dev-audit` através dos seguintes argumentos:

```bash
# Executar audit e exibir dashboard no console
dev-audit --dashboard

# Executar audit e exportar dashboard HTML
dev-audit --html

# Executar audit, exportar HTML e abrir no browser
dev-audit --html --open

# Combinar com outras opções
dev-audit --output yaml --dashboard --html
```

### Argumentos Disponíveis

- `--dashboard`: Exibe métricas consolidadas no console após a auditoria
- `--html`: Exporta o relatório HTML do dashboard (`audit_dashboard.html`)
- `--open`: Abre automaticamente o HTML gerado no navegador (requer `--html`)

### Integração Automática

A integração acontece automaticamente ao final de cada auditoria:

1. **Registro de Métricas**: Os resultados da auditoria são automaticamente registrados no sistema de métricas
2. **Dashboard Console**: Se `--dashboard` for usado, exibe estatísticas consolidadas
3. **Exportação HTML**: Se `--html` for usado, gera arquivo HTML com visualizações ricas
4. **Abertura Automática**: Se `--open` for usado junto com `--html`, abre o relatório no browser padrão

### Código de Integração

A integração foi implementada em `scripts/cli/audit.py`:

```python
# Imports adicionados
from scripts.audit_dashboard import AuditDashboard, AuditMetricsError
import webbrowser

# Lógica de integração (após a auditoria)
try:
    dashboard = AuditDashboard(workspace_root=workspace_root)

    # Registra automaticamente os resultados
    dashboard.record_audit(report)

    # Exibe no console se solicitado
    if args.dashboard:
        dashboard.print_console_dashboard()

    # Exporta HTML se solicitado
    if args.html:
        html_path = dashboard.export_html_dashboard()

        # Abre no browser se solicitado
        if args.open:
            webbrowser.open(f"file://{html_path.absolute()}")

except AuditMetricsError as e:
    logger.warning("Dashboard integration failed: %s", e)
    # Continua execução - dashboard é opcional
```

### 2. CI/CD Pipeline Integration

Add to your CI/CD pipeline (e.g., `.github/workflows/audit.yml`):

```yaml
steps:
  - name: Run Code Audit with Dashboard
    run: dev-audit --html

  - name: Upload Dashboard Artifact
    uses: actions/upload-artifact@v3
    with:
      name: audit-dashboard
      path: audit_dashboard.html
```

### 3. Pre-commit Hook Integration

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: audit-with-metrics
        name: Code Audit with Metrics Tracking
        entry: dev-audit --dashboard
        language: system
        pass_filenames: false
        stages: [commit]
```

## Usage Examples

### Exemplo 1: Auditoria Básica com Dashboard Console

```bash
dev-audit --dashboard
```

**Saída:**

```
📊 DASHBOARD DE AUDITORIA DEVOPS
==================================================

🎯 MÉTRICAS PRINCIPAIS:
   • Auditorias realizadas: 42
   • Falhas evitadas: 156
   • Tempo economizado: 26.0 horas
   • Taxa de sucesso: 98.5%
```

### Exemplo 2: Exportar Dashboard HTML

```bash
dev-audit --html
```

**Resultado:** Cria `audit_dashboard.html` no workspace root.

### Exemplo 3: Exportar e Abrir no Browser

```bash
dev-audit --html --open
```

**Resultado:** Exporta HTML e abre automaticamente no navegador padrão.

### Exemplo 4: Combinação Completa

```bash
dev-audit --output yaml --dashboard --html --open
```

**Resultado:**

- Gera relatório em YAML
- Exibe dashboard no console
- Exporta dashboard HTML
- Abre HTML no browser

### Standalone Dashboard Access

Se você quiser apenas visualizar o dashboard sem executar nova auditoria:

```bash
# Via módulo direto (usa dados históricos)
python scripts/audit_dashboard.py
python scripts/audit_dashboard.py --export-html
audit-dashboard --reset-stats
```

## Monitoring Integration

### Prometheus/Grafana

Export metrics to Prometheus format:

```python
def export_prometheus_metrics(dashboard: AuditDashboard) -> str:
    """Export metrics in Prometheus format."""
    metrics = dashboard.get_metrics_summary()

    prometheus_metrics = f"""
# HELP audit_total_performed Total number of audits performed
# TYPE audit_total_performed counter
audit_total_performed {metrics['audits_performed']}

# HELP audit_failures_prevented Total number of failures prevented
# TYPE audit_failures_prevented counter
audit_failures_prevented {metrics['failures_prevented']}

# HELP audit_time_saved_hours Total hours saved by audits
# TYPE audit_time_saved_hours counter
audit_time_saved_hours {metrics['time_saved_hours']}

# HELP audit_success_rate Current audit success rate percentage
# TYPE audit_success_rate gauge
audit_success_rate {metrics['success_rate']}
"""
    return prometheus_metrics
```

### Datadog Integration

```python
def send_to_datadog(dashboard: AuditDashboard):
    """Send metrics to Datadog."""
    import datadog

    metrics = dashboard.get_metrics_summary()

    datadog.api.Metric.send([
        {
            'metric': 'devops.audit.performed',
            'points': metrics['audits_performed']
        },
        {
            'metric': 'devops.audit.failures_prevented',
            'points': metrics['failures_prevented']
        }
    ])
```

## Security Considerations

1. **File Permissions**: Dashboard automatically sets secure permissions (644) on generated files
2. **HTML Sanitization**: All user data is sanitized before HTML output
3. **Atomic Writes**: Metrics file updates use atomic writes to prevent corruption
4. **Thread Safety**: All operations are thread-safe for concurrent usage

## Customization

### Configure Time Estimation

```python
dashboard = AuditDashboard(workspace_root)
# Modify configuration
dashboard._metrics["configuration"]["time_per_failure_minutes"] = 10  # Custom time estimate
```

### Custom Metrics File Location

```python
dashboard = AuditDashboard(
    workspace_root=Path("/custom/path"),
    metrics_filename="custom_metrics.json"
)
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure write permissions in workspace directory
2. **JSON Corruption**: Dashboard creates backups automatically during reset
3. **Thread Safety**: Use the provided RLock for custom modifications

### Log Analysis

Dashboard logs to both console and `audit_dashboard.log`:

```bash
tail -f audit_dashboard.log
```

## Future Enhancements

This dashboard is designed for the **main** branch of `python-template-profissional` and will work across:

- `python-template-cli`: CLI applications
- `python-template-api`: REST API services
- `python-template-lib`: Library packages

The dashboard provides universal DevOps metrics that are valuable regardless of project type.
