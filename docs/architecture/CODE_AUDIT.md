---
id: code-audit
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code:
- scripts/code_audit.py
title: Code Security Auditor
---

# Code Security Auditor

Enterprise-grade security and quality auditing tool for Python projects. This tool performs static analysis to detect security vulnerabilities, external dependencies, and potential CI/CD issues before code commits.

## 🔍 Features

- **Security Pattern Detection**: Identifies dangerous patterns like `shell=True`, `os.system()`, and code injection risks
- **External Dependency Analysis**: Detects unmocked external services that can cause CI/CD failures
- **Mock Coverage Analysis**: Ensures proper mocking of external dependencies in tests
- **CI Environment Simulation**: Runs tests in CI-like conditions to catch environment-specific issues
- **Configurable Rules**: YAML-based configuration for custom security patterns and scan settings
- **Multiple Output Formats**: JSON and YAML report generation
- **Pre-commit Integration**: Seamless integration with git pre-commit hooks
- **DevOps Best Practices**: Follows enterprise security and maintainability standards

## 🚀 Quick Start

### Basic Usage

```bash
# Run basic security audit
python scripts/code_audit.py

# Use custom configuration
python scripts/code_audit.py --config scripts/audit_config.yaml

# Generate YAML report
python scripts/code_audit.py --output yaml

# Fail on medium severity issues
python scripts/code_audit.py --fail-on MEDIUM
```

## 📋 Security Patterns Detected

### Critical Severity

- `os.system()` - Command injection vulnerability
- `shell=True` - Shell injection risk in subprocess calls
- `eval()` - Code injection vulnerability
- `exec()` - Code execution vulnerability

### High Severity

- `subprocess.run()` without proper validation
- `subprocess.call()` without proper validation
- Socket connections without mocking
- `pickle.loads()` - Arbitrary code execution risk

### Medium Severity

- HTTP requests without mocking (`requests.*`, `httpx.*`, `urllib.*`)
- Network operations in tests

### Low Severity

- File operations without proper error handling

## ⚙️ Configuration

The auditor uses a YAML configuration file (`audit_config.yaml`) to customize:

- **Scan Paths**: Directories to include in the audit
- **File Patterns**: File extensions to scan
- **Exclude Paths**: Directories to skip
- **Security Patterns**: Custom patterns to detect
- **Severity Levels**: Classification of findings
- **Mock Indicators**: Patterns that indicate proper mocking

Example configuration:

```yaml
scan_paths:
  - "src/"
  - "tests/"
  - "scripts/"

file_patterns:
  - "*.py"

exclude_paths:
  - ".git/"
  - "__pycache__/"
  - ".venv/"

ci_timeout: 300
max_findings_per_file: 50

custom_patterns:
  - pattern: "eval("
    severity: "CRITICAL"
    description: "eval() usage detected - potential code injection"
    category: "injection"
```

## 📊 Report Format

The auditor generates comprehensive reports in JSON or YAML format:

```json
{
  "metadata": {
    "timestamp": "2025-10-31T10:00:00Z",
    "workspace": "/path/to/project",
    "duration_seconds": 2.5,
    "files_scanned": 42,
    "auditor_version": "2.0.0"
  },
  "findings": [
    {
      "file": "src/utils.py",
      "line": 15,
      "severity": "HIGH",
      "category": "subprocess",
      "description": "Subprocess execution detected",
      "code": "subprocess.run(user_command, shell=True)",
      "suggestion": "Use shell=False with list arguments"
    }
  ],
  "summary": {
    "total_findings": 5,
    "severity_distribution": {
      "CRITICAL": 1,
      "HIGH": 2,
      "MEDIUM": 2,
      "LOW": 0
    },
    "overall_status": "FAIL",
    "recommendations": [
      "🔴 CRITICAL: Fix security vulnerabilities before commit",
      "🧪 Add mocks to 3 test files"
    ]
  }
}
```

## 🔧 Command Line Options

```
python scripts/code_audit.py [OPTIONS]

Options:
  --config PATH         Path to configuration YAML file
  --output FORMAT       Output format: json, yaml (default: json)
  --report-file PATH    Custom report output path
  --quiet              Suppress console output
  --fail-on SEVERITY   Exit with error on severity level: CRITICAL, HIGH, MEDIUM, LOW
  --help               Show help message
```

## 🏗️ DevOps Integration

### CI/CD Pipeline Integration

Add to your `.github/workflows/ci.yml`:

```yaml
- name: Security Audit
  run: |
    python scripts/code_audit.py --fail-on HIGH --output json

- name: Upload Audit Report
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: security-audit-report
    path: audit_report_*.json
```

### Docker Integration

```dockerfile
# Add to your Dockerfile for development images
COPY scripts/code_audit.py /app/scripts/
RUN pip install pyyaml

# Run audit during build
RUN python scripts/code_audit.py --fail-on CRITICAL
```

## 🛡️ Security Best Practices

The auditor enforces these security principles:

1. **Input Validation**: Detect unsafe user input handling
2. **Command Injection Prevention**: Flag dangerous subprocess usage
3. **Dependency Isolation**: Ensure external services are properly mocked
4. **Code Injection Prevention**: Detect `eval()`, `exec()`, and similar risks
5. **Secure Defaults**: Promote `shell=False` and safe coding patterns

## 📈 Performance

- **Fast Scanning**: Processes ~1000 files/second
- **Low Memory**: Uses AST parsing for accuracy without high memory usage
- **Configurable Limits**: Prevents analysis paralysis with finding limits
- **Early Exit**: Stops on critical issues for fast feedback

## 🤝 Contributing

When extending the auditor:

1. Add new security patterns to `custom_patterns` in config
2. Follow the `SecurityPattern` class structure
3. Include severity classification and actionable suggestions
4. Add corresponding tests for new patterns
5. Update documentation with new capabilities

## 📚 Dependencies

- **Python 3.8+**: Core language features and type hints
- **PyYAML**: Configuration file parsing
- **Standard Library**: AST, subprocess, pathlib, logging

No heavy external dependencies - keeps the auditor lightweight and secure.

## 🔍 Troubleshooting

### Common Issues

**"pytest not found"**: Install pytest for CI simulation

```bash
pip install pytest pytest-timeout
```

**"Config file not found"**: Use absolute path or place config in scripts/

```bash
python scripts/code_audit.py --config /full/path/to/config.yaml
```

**"Too many findings"**: Adjust `max_findings_per_file` in config

```yaml
max_findings_per_file: 20  # Reduce from default 50
```

**"False positives"**: Add exclusion patterns or adjust severity thresholds

```yaml
exclude_paths:
  - "tests/fixtures/"  # Exclude test fixtures
  - "migrations/"      # Exclude database migrations
```

## 📞 Support

For issues, feature requests, or questions:

1. Check the configuration documentation
2. Review the troubleshooting section
3. Examine audit logs in `audit.log`
4. Create an issue with audit report attached
