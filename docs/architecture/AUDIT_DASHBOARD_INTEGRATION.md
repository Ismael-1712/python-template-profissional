---
id: audit-dashboard-integration
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
last_updated: '2025-12-01'
context_tags: []
linked_code:
- scripts/code_audit.py
- scripts/audit_dashboard.py
title: Audit Dashboard Integration Guide
---

# Audit Dashboard Integration Guide

## Overview

O `audit_dashboard.py` é um sistema de métricas empresarial para rastreamento de auditorias DevOps, integrado com o `code_audit.py` para fornecer visibilidade completa sobre a efetividade das auditorias de CI/CD.

## Integration Points

### 1. With `code_audit.py`

O dashboard pode ser integrado ao sistema de auditoria principal adicionando estas linhas ao final do `code_audit.py`:

```python
# Add to code_audit.py imports
from scripts.audit_dashboard import AuditDashboard

# Add to the end of your audit process
def integrate_dashboard_recording(audit_results: dict, workspace_root: Path):
    """Record audit results in dashboard metrics."""
    try:
        dashboard = AuditDashboard(workspace_root)
        dashboard.record_audit(audit_results)
        logger.info("Audit metrics recorded successfully")
    except Exception as e:
        logger.warning(f"Failed to record audit metrics: {e}")
        # Don't fail the audit if dashboard recording fails
```

### 2. CI/CD Pipeline Integration

Add to your CI/CD pipeline (e.g., `.github/workflows/audit.yml`):

```yaml
steps:
  - name: Run Code Audit
    run: dev-audit --output json --config scripts/audit_config.yaml

  - name: Update Dashboard Metrics
    run: audit-dashboard

  - name: Export Dashboard
    run: audit-dashboard --export-html

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
      - id: audit-dashboard-update
        name: Update Audit Dashboard
        entry: audit-dashboard
        language: system
        pass_filenames: false
        stages: [post-commit]
```

## Usage Examples

### Console Dashboard

```bash
audit-dashboard
```

### HTML Export

```bash
audit-dashboard --export-html
```

### JSON Export for Monitoring

```bash
audit-dashboard --export-json monitoring_metrics.json
```

### Reset Statistics

```bash
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
