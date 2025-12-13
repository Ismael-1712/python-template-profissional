---
id: adr-002-pre-commit-optimization
type: arch
status: active
version: 1.0.0
author: DevOps Team
date: '2025-12-13'
tags: [dx, pre-commit, governance, performance]
context_tags: [critical-decision, architecture]
linked_code:
  - scripts/cli/audit.py
title: 'ADR 002: Pre-Commit Hook Optimization for Developer Experience'
---

# ADR 002: Pre-Commit Hook Optimization for Developer Experience

## Status

**Accepted** - 2025-12-13

## Context

### The Problem

Desenvolvedores enfrentavam um "commit loop" frustrante:

```bash
git commit -m "feat: nova funcionalidade"
# ❌ Hook modifica audit_metrics.json
# ❌ Git bloqueia: "You have unstaged changes"
git add audit_metrics.json
git commit -m "feat: nova funcionalidade"
# ❌ Loop infinito ou frustração
```

### Root Cause Analysis

1. **State Mutation in Validators**: O hook `code-audit-security` executava [`audit.py`](../../scripts/cli/audit.py), que:
   - Validava código (correto ✅)
   - **Gravava métricas em `audit_metrics.json`** (problemático ❌)
   - Atualizava timestamp `last_audit` **sempre** (causa do loop ❌)

2. **Tracked Volatile Files**: `audit_metrics.json` estava versionado no Git, mas mudava a cada execução do hook.

3. **Violation of SRP**: Pre-commit hook tinha duas responsabilidades:
   - **Validation** (deve fazer)
   - **Metrics Recording** (não deve fazer)

### Impact

- ⏱️ **DX Degradation**: Commits demoravam 30-60s (com retries manuais)
- 😤 **Developer Frustration**: Desenvolvedores usavam `--no-verify` (~20% dos commits)
- 📊 **Inconsistent Metrics**: Dados locais não refletiam realidade do CI

## Decision

Implementar **"Lazy Audit"** - context-aware metrics recording:

### Core Change

Modificar [`audit.py`](../../scripts/cli/audit.py) para detectar contexto de execução:

```python
# Detect execution context to avoid metrics write during pre-commit
is_pre_commit = os.getenv("PRE_COMMIT") == "1"
is_git_hook = os.getenv("GIT_AUTHOR_NAME") is not None

skip_metrics = (is_pre_commit or is_git_hook) and not args.dashboard

if not skip_metrics:
    dashboard.record_audit(report)  # Grava métricas
    logger.info("Audit results recorded in metrics")
else:
    logger.debug("Pre-commit context - skipping metrics persistence")
```

### Configuration Change

Atualizar [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml):

```yaml
- id: code-audit-security
  entry: env PRE_COMMIT=1 python3 scripts/cli/audit.py ...
  #      ^^^^^^^^^^^^^^^^ Define variável de ambiente
```

## Consequences

### Positive ✅

1. **Instant Commits**: Redução de 30-60s para 5-10s
2. **Zero Loops**: `audit_metrics.json` não é mais modificado durante pre-commit
3. **Validation Preserved**: Código ainda é validado rigorosamente
4. **Better Metrics**: Métricas gravadas em contextos significativos (CI, manual)

### Negative ⚠️

1. **No Local Metrics**: Desenvolvedores não veem suas próprias estatísticas locais
   - **Mitigação**: CI gera métricas centralizadas e confiáveis
2. **Async Feedback**: Métricas aparecem apenas após push/PR
   - **Mitigação**: Validação (fail fast) ainda é síncrona
3. **Environment Dependency**: Detecção depende de variáveis de ambiente
   - **Mitigação**: Fallback para `GIT_AUTHOR_NAME` (sempre presente em hooks)

### Neutral ➖

- `audit_metrics.json` continua versionado (atualizado pelo CI)
- Execuções manuais de `audit.py` ainda gravam métricas normalmente

## Alternatives Considered

### 1. Volatile Ignore (Descartado)

**Abordagem**: Adicionar `audit_metrics.json` ao `.gitignore`

**Pros**:

- ✅ Fix imediato (1 linha)
- ✅ Elimina loop completamente

**Cons**:

- ❌ **Perde rastreabilidade histórica**
- ❌ Violação do princípio "Documentation as Code"
- ❌ Dashboards de tendência impossíveis

**Decisão**: ❌ Rejeitado - conflita com governança

### 2. CI Shift (Planejado para Fase 2)

**Abordagem**: Mover hooks pesados para GitHub Actions

**Pros**:

- ✅ Commits instantâneos
- ✅ Métricas centralizadas
- ✅ Parallelização de auditorias

**Cons**:

- ⚠️ Feedback tardio (assíncrono)
- ⚠️ Custo de CI maior

**Decisão**: ✅ Adotar em paralelo (complementa Lazy Audit)

### 3. Automation Wrapper (Opcional)

**Abordagem**: Criar `make commit` que lida com loop automaticamente

**Pros**:

- ✅ Transparente para hooks
- ✅ Fácil de implementar

**Cons**:

- ⚠️ Não funciona em IDEs
- ⚠️ Mascara o problema ao invés de resolver

**Decisão**: ✅ Manter como conveniência opcional

## Implementation Plan

### Phase 1: Quick Win ⚡ (Implemented)

- [x] Modificar `audit.py` para detectar contexto
- [x] Atualizar `.pre-commit-config.yaml` com `PRE_COMMIT=1`
- [x] Testar com 10 commits consecutivos
- [x] Documentar no ADR

### Phase 2: CI Shift 🏗️ (Roadmap)

- [ ] Criar `.github/workflows/governance.yml`
- [ ] Configurar upload de métricas como artifacts
- [ ] Adicionar PR comments com resultados
- [ ] Simplificar hooks locais (apenas validação rápida)

### Phase 3: Developer Convenience 🎁 (Optional)

- [ ] Adicionar `make commit` ao Makefile
- [ ] Documentar workflow no CONTRIBUTING.md
- [ ] Treinar time no novo processo

## Validation Metrics

### Before (Baseline)

```
Tempo médio de commit: 30-60s
Frustração: 🔥🔥🔥🔥🔥
Commits com --no-verify: ~20%
```

### After (Expected)

```
Tempo médio de commit: 5-10s
Frustração: ⭐⭐⭐⭐⭐
Commits com --no-verify: <1%
```

### Success Criteria

- ✅ Commits completam em < 15s
- ✅ Zero loops de re-add em 100 commits consecutivos
- ✅ CI gera métricas em 100% dos PRs (após Fase 2)

## References

- [Analysis Document](../analysis/DX_GOVERNANCE_BOTTLENECK_ANALYSIS.md) - Análise completa do problema
- [Pre-commit Best Practices](https://pre-commit.com/#usage)
- [Google SRE - Eliminating Toil](https://sre.google/sre-book/eliminating-toil/)
- [Engineering Standards](../guides/ENGINEERING_STANDARDS.md#atomicidade-em-scripts-de-infraestrutura)

## Notes

### Key Principle

> **"Pre-commit hooks should be gatekeepers, not record-keepers."**

Validação deve ser síncrona e rápida.
Persistência deve ser assíncrona e centralizada.

### Future Work

- **Dashboard Auto-Deploy**: CI publica `audit_dashboard.html` no GitHub Pages
- **Trend Analysis**: Análise de métricas ao longo do tempo
- **Alerting**: Notificações automáticas para degradação de qualidade

---

**Decision Made By**: DevOps Team & GitHub Copilot
**Date**: 2025-12-13
**Review Date**: 2025-Q1 (3 meses após implementação)
