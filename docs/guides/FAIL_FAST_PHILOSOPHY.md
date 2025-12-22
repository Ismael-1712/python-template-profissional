---
id: fail-fast-philosophy
type: guide
status: active
version: 1.0.0
author: GEM & SRE Team
date: '2025-12-16'
tags: [error-handling, reliability, exit-codes, sre, best-practice]
context_tags: [engineering-philosophy, observability, ci-cd]
linked_code:
  - scripts/cli/git_sync.py
  - scripts/cli/doctor.py
  - scripts/cortex/cli.py
  - scripts/ci_recovery/main.py
  - scripts/ci/check_docs.py
title: 'Fail Fast Philosophy - Exit Codes & Error Handling Strategy'
---

# ⚡ Fail Fast Philosophy - Exit Codes & Error Handling Strategy

## Status

**Active** - Filosofia consolidada durante Sprint 4 (P30 & P33 - Nov 2025), validada em produção

## Contexto e Motivação

### O Problema: Falhas Silenciosas

No início do projeto, o sistema sofria de **Mascaramento de Erros Críticos**:

```python
# ❌ ANTI-PADRÃO: Exception genérica silenciosa
try:
    critical_operation()
except Exception:
    pass  # Bug crítico mascarado!
```

**Sintomas Operacionais:**

- 🐛 **Bugs Invisíveis:** Falhas críticas não geravam logs ou alertas
- 🔄 **Loops Infinitos:** Scripts travavam sem timeout, consumindo recursos
- 💥 **Crash sem Contexto:** Quando o sistema falhava, não havia traceback
- 🤷 **Ambiguidade de Erros:** Exit code sempre `1`, impossível distinguir tipos de falha

#### Caso Real: O Bug Mascarado

```python
# Código legado problemático
def sync_branches(self):
    try:
        subprocess.run(["git", "push"], check=True)
    except Exception:
        pass  # Falha de push SILENCIADA!

    # Código continua executando, pensando que push funcionou
    self.update_status("synced")  # FALSO STATUS!
```

**Consequência:** PRs marcados como sincronizados quando na verdade falharam no push, causando divergência de branches.

### A Solução: Fail Fast com Exit Codes Semânticos

Durante o **Sprint 4 (Tarefas P30 & P33)**, implementamos a filosofia **Fail Fast** com dois pilares:

1. **Eliminação de `except Exception: pass`**
2. **Exit Codes Semânticos** (0, 1, 2, 130) para diferenciação de falhas

---

## Princípios Fundamentais

### 1️⃣ Abortar com Traceback Completo

**Regra:** Bugs internos devem **SEMPRE** exibir traceback e abortar a execução.

```python
# ✅ CORRETO: Traceback completo em bugs
try:
    result = external_api_call()
    process_data(result)  # Possível bug interno
except KeyError as e:
    # Bug interno: dados inesperados
    logger.critical("UNEXPECTED ERROR (possible bug): %s", e, exc_info=True)
    sys.exit(2)  # Exit code 2 = Internal Error
```

**Exit Code 2:** Indica **bug de software** (não erro de usuário), priorizando correção imediata.

### 2️⃣ Diferenciação de Erros

**Regra:** Cada tipo de falha deve ter um exit code distinto.

| Exit Code | Significado | Exemplo |
|-----------|-------------|---------|
| **0** | Sucesso completo | Operação concluída sem problemas |
| **1** | Erro de negócio/usuário | Auditoria falhou (vulnerabilidades detectadas), validação de input falhou |
| **2** | Bug interno (software) | NoneType error, KeyError inesperado, import falhando |
| **130** | Cancelamento de usuário | SIGINT (Ctrl+C) capturado gracefully |

**Implementação de Referência:**

```python
# scripts/cli/git_sync.py (lines 110-118)
def main() -> None:
    """Main entry point for the Smart Git Sync CLI."""
    try:
        # ... lógica principal ...
        sys.exit(0)
    except KeyboardInterrupt:
        logger.warning("Synchronization interrupted by user")
        sys.exit(130)  # Standard SIGINT exit code
    except SyncError:
        logger.exception("Synchronization error")
        sys.exit(1)  # Erro de negócio (ex: merge conflict)
    except Exception as e:
        logger.critical("UNEXPECTED ERROR (possible bug): %s", e, exc_info=True)
        sys.exit(2)  # Bug interno
```

### 3️⃣ Não Mascarar Exceções

**Regra:** `except` sem re-raise ou logging é **PROIBIDO**.

```python
# ❌ ERRADO: Exceção mascarada
try:
    critical_operation()
except Exception:
    pass  # Silencia erro crítico

# ❌ ERRADO: Log genérico sem detalhes
try:
    critical_operation()
except Exception as e:
    logger.error("Erro")  # Sem contexto!

# ✅ CORRETO: Log com contexto + re-raise ou exit
try:
    critical_operation()
except SpecificError as e:
    logger.error("Falha ao executar operação X: %s", e, exc_info=True)
    sys.exit(1)

# ✅ CORRETO: Re-raise após cleanup
try:
    critical_operation()
except Exception:
    cleanup_resources()
    raise  # Re-lança para caller decidir
```

### 4️⃣ Timeouts Obrigatórios

**Regra:** Operações de I/O (rede, subprocess) devem ter timeout.

```python
# ✅ CORRETO: Timeout em subprocess
result = subprocess.run(
    ["git", "fetch"],
    timeout=300,  # 5 minutos
    check=False,
)

# ✅ CORRETO: Timeout em HTTP
response = httpx.get(url, timeout=30.0)
```

**Referência:** `install_dev.py` usa `PIP_TIMEOUT_SECONDS = 300` para prevenir CI freezes.

---

## Padrões de Implementação

### Pattern 1: CLI Entry Point

**Template para todos os scripts CLI:**

```python
#!/usr/bin/env python3
"""Script description.

Exit Codes:
    0: Success
    1: Business/User error
    2: Internal error (bug)
    130: User interruption (Ctrl+C)
"""

import logging
import sys

from scripts.utils.logger import setup_logging

logger = setup_logging(__name__)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = success)
    """
    try:
        # Lógica principal
        logger.info("✅ Success!")
        return 0

    except ValueError as e:
        # Erro de negócio/input inválido
        logger.error("Invalid input: %s", e)
        return 1

    except KeyError as e:
        # Bug interno
        logger.critical("UNEXPECTED ERROR (possible bug): %s", e, exc_info=True)
        return 2

    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        return 130


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
```

### Pattern 2: Subprocess com Check Flags

**Regra:** Use `check=False` quando você quer TRATAR o erro. Use `check=True` quando falha é terminal.

```python
# ✅ check=False: Erro é tratável
result = subprocess.run(
    ["git", "push"],
    check=False,  # Não levanta exceção
    capture_output=True,
)

if result.returncode != 0:
    logger.warning("Push failed: %s", result.stderr)
    # Decidir se continua ou aborta

# ✅ check=True: Erro é FATAL
subprocess.run(
    ["pip", "install", "-r", "requirements.txt"],
    check=True,  # Levanta CalledProcessError se falhar
    timeout=300,
)
```

### Pattern 3: Validação Fail Fast

**Regra:** Valide inputs ANTES de iniciar operações custosas.

```python
def run_audit(self, workspace: Path) -> int:
    """Execute code audit.

    Returns:
        Exit code (0 = success, 1 = vulnerabilities found)
    """
    # ✅ FASE 1: Validações (Fail Fast)
    if not workspace.exists():
        logger.error("Workspace não existe: %s", workspace)
        return 1

    audit_script = workspace / "scripts" / "code_audit.py"
    if not audit_script.exists():
        logger.error("Script de auditoria não encontrado")
        return 1

    # ✅ FASE 2: Operação (já validado)
    result = subprocess.run(
        [sys.executable, str(audit_script)],
        timeout=300,
        check=False,
    )

    return result.returncode
```

---

## Exit Codes em Contextos Específicos

### CI/CD Pipelines

**Objetivo:** Diferenciar falhas recuperáveis de bugs críticos.

```yaml
# .github/workflows/ci.yml
- name: Run Code Audit
  run: make audit
  continue-on-error: false  # Exit 1 ou 2 = falha do job

- name: Check Documentation
  run: python scripts/ci/check_docs.py
  # Exit 0 = docs OK
  # Exit 1 = docs com problemas (falha pipeline)
```

**Implementação:**

```python
# scripts/ci/check_docs.py
def validate_documentation() -> int:
    """Validate documentation completeness.

    Returns:
        0: All docs valid
        1: Docs incomplete (fail CI)
    """
    missing = find_missing_docs()

    if missing:
        print(f"❌ {len(missing)} files missing documentation")
        return 1

    print("✅ All documentation complete")
    return 0

if __name__ == "__main__":
    sys.exit(validate_documentation())
```

### Typer CLI (Exceções Especiais)

**Typer usa `typer.Exit(code=X)` em vez de `sys.exit(X)`:**

```python
# scripts/cortex/cli.py
@app.command()
def audit(...) -> None:
    """Run metadata audit."""
    try:
        # ... lógica ...

        if strict and has_broken_links:
            typer.secho(
                "\n❌ Validation FAILED (--strict mode)",
                fg=typer.colors.RED,
                bold=True,
            )
            raise typer.Exit(code=1)  # Exit code 1 para falha de validação

        typer.secho("✅ Validation PASSED", fg=typer.colors.GREEN)

    except Exception as e:
        logger.error("Error during audit: %s", e, exc_info=True)
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e
```

### Test Runners (Pytest)

**Exit Codes do pytest (NÃO modificamos):**

| Exit Code | Significado Pytest |
|-----------|-------------------|
| 0 | Todos os testes passaram |
| 1 | Testes falharam |
| 2 | Interrupção de usuário |
| 3 | Erro interno do pytest |
| 4 | Erro de uso (pytest) |
| 5 | Nenhum teste coletado |

**Uso em CI:**

```bash
# CI valida exit code do pytest
pytest tests/ --maxfail=5
# Exit 0 = testes OK
# Exit 1 = falhas detectadas (falha pipeline)
```

---

## Observabilidade e Debugging

### Logging de Exceções

**Pattern:** Use `exc_info=True` para capturar traceback completo.

```python
try:
    process_data(payload)
except Exception as e:
    # ✅ Traceback completo vai para o log
    logger.exception("Failed to process data: %s", e)
    # Equivalente a:
    logger.error("Failed to process data: %s", e, exc_info=True)
    sys.exit(2)
```

**Saída de Log:**

```
2025-12-16 10:30:15 ERROR Failed to process data: 'key' not found
Traceback (most recent call last):
  File "script.py", line 42, in process_data
    value = payload["key"]
KeyError: 'key'
```

### Mensagens de Erro para Usuários

**Regra:** Erros de negócio (exit 1) devem ter mensagens claras sem traceback.

```python
# ✅ CORRETO: Mensagem amigável para erro de negócio
if not workspace.exists():
    logger.error("❌ Workspace não encontrado: %s", workspace)
    logger.info("💡 Dica: Execute 'cortex init' para criar o workspace")
    sys.exit(1)

# ✅ CORRETO: Traceback completo para bugs internos
try:
    data = parse_json(file)
except KeyError as e:
    logger.critical(
        "BUG DETECTED: Missing required key in JSON: %s",
        e,
        exc_info=True,  # Traceback completo
    )
    sys.exit(2)
```

---

## Casos de Estudo

### Caso 1: git_sync.py - Hierarquia de Exceções

**Implementação:**

```python
# scripts/cli/git_sync.py
class GitSyncError(Exception):
    """Base exception for git sync errors."""
    pass

class SyncError(GitSyncError):
    """Erro de sincronização (recuperável)."""
    pass

class AuditError(GitSyncError):
    """Erro de auditoria (falha de negócio)."""
    pass

def main() -> None:
    try:
        orchestrator = SyncOrchestrator(config)
        orchestrator.execute()
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("Sync interrupted by user")
        sys.exit(130)

    except (SyncError, AuditError) as e:
        # Erro de negócio: mensagem sem traceback
        logger.error("Sync failed: %s", e)
        sys.exit(1)

    except Exception as e:
        # Bug interno: traceback completo
        logger.critical("UNEXPECTED ERROR (possible bug): %s", e, exc_info=True)
        sys.exit(2)
```

**Benefício:** CI pode distinguir falha de teste (exit 1, retry) de bug de código (exit 2, alerta dev).

### Caso 2: doctor.py - Validação de Ambiente

**Implementação:**

```python
# scripts/cli/doctor.py
def main() -> int:
    """Diagnose development environment.

    Returns:
        0: Environment healthy
        1: Problems detected
    """
    doctor = DevDoctor(project_root)
    success = doctor.run_diagnostics()

    return 0 if success else 1

if __name__ == "__main__":
    with trace_context():
        sys.exit(main())
```

**Exit Codes:**

- `0`: Ambiente saudável (CI pode prosseguir)
- `1`: Problemas detectados (CI deve falhar, dev deve corrigir)

**Uso em CI:**

```bash
make doctor
if [ $? -eq 1 ]; then
    echo "❌ Environment unhealthy, cannot proceed"
    exit 1
fi
```

### Caso 3: ci_recovery/main.py - Recovery System

**Implementação:**

```python
# scripts/ci_recovery/main.py
def main() -> None:
    """Main entry point for CI recovery system."""
    try:
        recovery_system = CIFailureRecoverySystem(...)
        success = recovery_system.execute_recovery()
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Failed to initialize recovery system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    with trace_context():
        main()
```

**Exit Codes:**

- `0`: Recovery bem-sucedido
- `1`: Recovery falhou (CI deve abortar)

---

## Anti-Padrões e Correções

### Anti-Padrão 1: Exception Genérica sem Contexto

```python
# ❌ ERRADO
try:
    process()
except Exception as e:
    print("Error")
    sys.exit(1)

# ✅ CORRETO
try:
    process()
except SpecificError as e:
    logger.error("Process failed: %s", e, exc_info=True)
    sys.exit(1)
except Exception as e:
    logger.critical("BUG: Unexpected error: %s", e, exc_info=True)
    sys.exit(2)
```

### Anti-Padrão 2: Exit Code Sempre 1

```python
# ❌ ERRADO: Não diferencia tipos de falha
def main():
    try:
        run()
    except Exception:
        sys.exit(1)  # Bug ou erro de negócio?

# ✅ CORRETO: Exit codes semânticos
def main():
    try:
        run()
    except ValidationError:
        sys.exit(1)  # Erro de negócio
    except Exception:
        sys.exit(2)  # Bug interno
```

### Anti-Padrão 3: Silenciar KeyboardInterrupt

```python
# ❌ ERRADO: Não é possível cancelar
try:
    long_running_task()
except KeyboardInterrupt:
    pass  # Ctrl+C ignorado!

# ✅ CORRETO: Cleanup graceful
try:
    long_running_task()
except KeyboardInterrupt:
    logger.info("Task cancelled by user")
    cleanup_resources()
    sys.exit(130)
```

---

## Checklist de Revisão de Código

Ao revisar código, verifique:

- [ ] **Exit Codes Documentados:** Docstring contém seção `Exit Codes:`
- [ ] **Sem `except Exception: pass`:** Todas as exceções são logadas ou re-raised
- [ ] **Exit Code 2 para Bugs:** Erros inesperados usam `sys.exit(2)`
- [ ] **KeyboardInterrupt Tratado:** Exit code 130 em caso de Ctrl+C
- [ ] **Timeouts Configurados:** Subprocess e HTTP têm timeout
- [ ] **Logging com exc_info:** Bugs internos logam com `exc_info=True`
- [ ] **Mensagens Claras:** Erros de negócio têm mensagens amigáveis

---

## Referências Técnicas

### Implementações de Referência

- [scripts/cli/git_sync.py](../../scripts/cli/git_sync.py#L110-L118) - Hierarquia de exceções
- [scripts/cli/doctor.py](../../scripts/cli/doctor.py#L416-L430) - Exit codes em diagnóstico
- [scripts/cortex/cli.py](../../scripts/cortex/cli.py#L582-L600) - Typer exit codes
- [scripts/ci_recovery/main.py](../../scripts/ci_recovery/main.py#L291-L303) - Recovery system
- [scripts/maintain_versions.py](../../scripts/maintain_versions.py#L37-L46) - KeyboardInterrupt handling

### Documentação Relacionada

- [scripts/ci/README.md](../../scripts/ci/README.md#L48-L54) - Princípios de design de scripts CI
- [SECURITY_STRATEGY.md](../architecture/SECURITY_STRATEGY.md#L194-L228) - Fail-Fast em pipeline
- [CONTRIBUTING.md](../../CONTRIBUTING.md#L434-L457) - Três Travas de Segurança

### Standard POSIX Exit Codes

- [Advanced Bash-Scripting Guide - Exit Codes](https://tldp.org/LDP/abs/html/exitcodes.html)
- [Bash Exit Status Reference](https://www.gnu.org/software/bash/manual/html_node/Exit-Status.html)

---

## Histórico de Revisões

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0.0 | 2025-12-16 | Versão inicial baseada em Sprint 4 learnings (P30, P33) e retrospectiva v8.0 |

---

**Mantenha este documento atualizado conforme novos padrões de error handling forem estabelecidos.**
