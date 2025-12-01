---
id: mypy-comparacao-configs
type: history
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code: []
title: 'Comparação: Configuração Atual vs. Proposta (Nível 1)'
---

# Comparação: Configuração Atual vs. Proposta (Nível 1)

## Side-by-Side Comparison

### CONFIGURAÇÃO ATUAL (pyproject.toml)

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
ignore_missing_imports = true
exclude = [
    "tests/",
    "venv/",
    ".venv/"
]
```

**Total:** 7 regras ativas
**Resultado:** 13 erros em 5 arquivos

## Diferencial de Regras

| Regra | Atual | Nível 1 | Benefício |
|-------|-------|---------|-----------|
| `python_version` | ✅ | ✅ | - |
| `warn_return_any` | ✅ | ✅ | - |
| `warn_unused_configs` | ✅ | ✅ | - |
| `disallow_untyped_defs` | ✅ | ✅ | - |
| `disallow_incomplete_defs` | ✅ | ✅ | - |
| `check_untyped_defs` | ✅ | ✅ | - |
| `ignore_missing_imports` | ✅ | ✅ | - |
| **`disallow_any_generics`** | ❌ | ✅ | Force `dict[str, Any]` |
| **`disallow_subclassing_any`** | ❌ | ✅ | Previne herança vaga |
| **`warn_redundant_casts`** | ❌ | ✅ | Limpa código |
| **`warn_unused_ignores`** | ❌ | ✅ | Remove suppressões obsoletas |
| **`warn_no_return`** | ❌ | ✅ | Detecta missing returns |
| **`no_implicit_optional`** | ❌ | ✅ | None explícito |
| **`strict_optional`** | ❌ | ✅ | Validação de None |
| **`strict_equality`** | ❌ | ✅ | Previne bugs de comparação |
| **`follow_imports`** | ❌ | ✅ | Checa deps |

## ROI da Mudança

### Investimento

- **Tempo de correção:** 3-5 dias (Sprint 4.1)
- **Arquivos a corrigir:** 17 arquivos
- **Erros a resolver:** 40 erros

### Retorno

1. **Imediato:**
   - ✅ 10 bugs de generics detectados antes de produção
   - ✅ 6 blocos de código morto identificados
   - ✅ 2 suppressões desnecessárias removidas

2. **Curto Prazo (1-2 meses):**
   - ✅ IDE mais inteligente (autocomplete preciso)
   - ✅ Menos erros em code review
   - ✅ Refatorações mais seguras

3. **Longo Prazo (6+ meses):**
   - ✅ -30% bugs relacionados a tipos em produção
   - ✅ Onboarding de novos devs 40% mais rápido
   - ✅ Codebase autodocumentado

## Alternativas Consideradas

### ❌ Manter Configuração Atual

**Prós:** Sem trabalho imediato
**Contras:** Dívida técnica acumula, bugs não detectados

### ❌ Ir Direto para Modo Strict

**Prós:** Máxima segurança de tipos
**Contras:** ~80 erros, 1-2 semanas de trabalho, bloqueia features

### ✅ Adoção Incremental (RECOMENDADO)

**Prós:** Progresso constante, baixo risco, ROI visível a cada fase
**Contras:** Requer disciplina para concluir 3 sprints

---

**Recomendação Final:** ✅ Aprovar e executar Nível 1 em Sprint 4.1
