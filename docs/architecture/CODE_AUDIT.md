---
id: code-audit
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
last_updated: '2025-12-01'
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
dev-audit

# Use custom configuration
dev-audit --config scripts/audit_config.yaml

# Generate YAML report
dev-audit --output yaml

# Fail on medium severity issues
dev-audit --fail-on MEDIUM
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
dev-audit [OPTIONS]

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
    dev-audit --fail-on HIGH --output json

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
RUN dev-audit --fail-on CRITICAL
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

---

## 🔐 Itens Auditados e Resolvidos

Esta seção documenta vulnerabilidades identificadas e suas resoluções.

### [P00.2] Atomicidade do Pip Install

**Status:** ✅ Concluído (v8.0)
**Data:** 2025-12-06
**Tipo:** Estabilidade / SRE
**Severidade:** 🔴 Alta (corrupção de ambiente de desenvolvimento)

**Problema Original:**

O script `scripts/cli/install_dev.py` realizava operações críticas (`pip-compile`, `pip install`) sem garantia de atomicidade. Se o processo falhasse no meio, o arquivo `requirements/dev.txt` poderia ficar corrompido ou inconsistente, quebrando o ambiente para todos os desenvolvedores.

**Vulnerabilidades Identificadas:**

1. **V1 - Ausência de Rollback (ALTA)**: Se `pip install` falhasse após `pip-compile`, o ambiente ficava em estado inconsistente
2. **V2 - Inconsistência no Fallback (MÉDIA)**: Modo fallback não usava mesmas validações do modo PATH
3. **V3 - Arquivos Temporários Órfãos (BAIXA)**: Cleanup incompleto em caso de exceção

**Solução Implementada:**

1. **Backup Preemptivo**: Cópia de segurança com preservação de metadados (`shutil.copy2`) antes da compilação

   ```python
   backup_file = target_file.with_suffix(".txt.bak")
   shutil.copy2(target_file, backup_file)
   ```

2. **Atomicidade**: Uso de arquivos temporários validados para o `pip-compile`
   - Validação de existência do arquivo
   - Validação de tamanho (não vazio)
   - Validação de sintaxe (header com comentário)
   - Atomic replace usando `Path.replace()` (garantia POSIX)

3. **Rollback Automático**: Bloco `try/except` que restaura o backup se a instalação falhar

   ```python
   try:
       subprocess.run(["pip", "install", "-r", "dev.txt"], check=True)
   except subprocess.CalledProcessError:
       backup_file.replace(target_file)  # Restaura versão anterior
       raise
   ```

4. **UX Melhorada**: Mensagem de erro refatorada para focar na proteção
   - **Antes**: `"⚠️ Installation failed. Rolled back: /path/to/dev.txt"`
   - **Depois**: `"🛡️ ROLLBACK ATIVADO: A instalação falhou, mas seu ambiente foi restaurado com segurança para a versão anterior (dev.txt). Nenhuma alteração foi aplicada."`

5. **Cleanup Garantido**: Remoção de arquivos temporários após sucesso

   ```python
   if backup_file and backup_file.exists():
       backup_file.unlink()  # Remove .bak após sucesso
   ```

**Impacto:**

- ✅ Ambiente sempre em estado consistente
- ✅ Rollback automático transparente
- ✅ Redução de ansiedade do desenvolvedor
- ✅ Menor necessidade de intervenção manual
- ✅ Zero downtime em caso de falha

**Arquivos Modificados:**

- `scripts/cli/install_dev.py` (~95 linhas de mudança)

**Referências:**

- Relatório de Auditoria (Fase 01)
- Relatório de Implementação (Fase 02)
- Relatório de Refinamento de UX (Fase 03)

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
dev-audit --config /full/path/to/config.yaml
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

---

## 📋 Histórico de Melhorias

### [P29] Hardening de Dados com Enums

**Status:** ✅ Concluído (v8.0)
**Data:** 2025-12-06
**Tipo:** Arquitetura / Segurança

**Problema Original:**

Modelos usavam strings soltas ("magic strings") para definir severidade e status. Erros de digitação passavam despercebidos até o runtime.

Exemplo do problema:

```python
# ❌ ANTES: Strings soltas permitiam erros silenciosos
class SecurityIssue(BaseModel):
    severity: str  # "HIHG" (typo) seria aceito!
    category: str

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        # 30+ linhas de boilerplate para cada campo
        if v not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            raise ValueError(f"Invalid severity: {v}")
        return v
```

**Solução Implementada:**

1. **Conversão de Campos para Enums**: Todos os campos de domínio finito foram convertidos para `Enum` (herdando de `str` para compatibilidade JSON).

2. **Criação de Enums Específicos**:
   - `SecurityCategory`: Categorias de vulnerabilidades (`INJECTION`, `CRYPTO`, `AUTH`, `XSS`)
   - `SecuritySeverity`: Níveis de severidade (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)

3. **Eliminação de Validadores Manuais**: Remoção de 30+ linhas de código boilerplate (validadores `@field_validator`).

4. **Cobertura de Tipagem Estrita**: Testes atualizados para usar valores do Enum, garantindo type safety completo.

**Exemplo da Solução:**

```python
# ✅ DEPOIS: Enums fornecem validação automática
from enum import Enum

class SecuritySeverity(str, Enum):
    """Severity levels with automatic validation."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityIssue(BaseModel):
    severity: SecuritySeverity  # Typos detectados em tempo de análise!
    category: SecurityCategory
    # Zero validadores manuais necessários
```

**Benefícios Mensuráveis:**

- **-30+ linhas de código**: Eliminação de validadores boilerplate
- **100% Type Safety**: Mypy detecta erros antes do runtime
- **Melhor DX**: Autocomplete e validação automática na IDE
- **Zero Regressões**: Testes garantem compatibilidade JSON/YAML
- **Documentação Explícita**: Valores válidos ficam visíveis no código

**Impacto em Arquivos:**

- `scripts/core/mock_ci/models.py`: Modelos de CI/CD
- `scripts/audit/models.py`: Modelos de auditoria
- `tests/test_*.py`: Testes atualizados com Enum values
- `docs/guides/ENGINEERING_STANDARDS.md`: Padrão documentado

**Referências:**

- [ENGINEERING_STANDARDS.md - Enums vs Magic Strings](../guides/ENGINEERING_STANDARDS.md#enums-vs-magic-strings)
- Sprint Issue: [P29] - Refatoração Enum Completa

---
