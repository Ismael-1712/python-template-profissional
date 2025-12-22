---
id: sprint4-mypy-audit
type: history
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code:
- scripts/utils/atomic.py
- scripts/core/mock_generator.py
- scripts/core/cortex/mapper.py
- scripts/cli/mock_ci.py
- scripts/core/cortex/migrate.py
- scripts/audit_dashboard/storage.py
- scripts/cortex/cli.py
title: 📊 Sprint 4 - Relatório de Auditoria de Tipagem Mypy
---

# 📊 Sprint 4 - Relatório de Auditoria de Tipagem Mypy

## 🎯 Objetivo

Elevar a segurança do código ativando o modo estrito do Mypy para melhorar a
qualidade de tipos e detectar erros em tempo de desenvolvimento.

## 📋 Sumário Executivo

| Métrica | Valor |
|---------|-------|
| **Configuração Atual** | Moderada (7 regras ativas) |
| **Erros Baseline** | 13 erros em 5 arquivos |
| **Erros com Modo Estrito** | 40 erros em 17 arquivos |
| **Incremento** | +207% (+27 erros) |
| **Arquivos Verificados** | 64 arquivos Python |
| **Recomendação** | Adoção incremental em 3 fases |

## 🚀 Configuração State of the Art Proposta

### 📦 Configuração Recomendada (3 Níveis)

#### **Nível 1: Rigor Básico** (Atual + 5 regras)

```toml
[tool.mypy]
python_version = "3.10"

# === RIGOR DE TIPAGEM ===
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_any_generics = true          # ⭐ NOVO: Força especificar generics
disallow_subclassing_any = true       # ⭐ NOVO: Previne herança de Any

# === WARNINGS ===
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true           # ⭐ NOVO: Detecta casts desnecessários
warn_unused_ignores = true            # ⭐ NOVO: Limpa # type: ignore
warn_no_return = true                 # ⭐ NOVO: Detecta funções sem return

# === CONTROLE DE NONE ===
no_implicit_optional = true           # ⭐ NOVO: None explícito
strict_optional = true

# === IMPORTS ===
ignore_missing_imports = false        # ⭐ MUDANÇA: Exige stubs
follow_imports = "normal"

# === MISC ===
strict_equality = true                # ⭐ NOVO: Igualdade type-safe

exclude = ["tests/", "venv/", ".venv/"]
```

**Impacto Estimado:** ~40 erros

#### **Nível 2: Rigor Avançado** (Nível 1 + 3 regras)

```toml
# Adicionar ao Nível 1:
disallow_untyped_calls = true         # Não permite chamar funções sem tipos
disallow_untyped_decorators = true    # Decoradores devem ter tipos
warn_unreachable = true               # Detecta código morto
```

**Impacto Estimado:** +15 erros (~55 total)

#### **Nível 3: Modo Strict** (strict = true)

```toml
[tool.mypy]
strict = true  # Equivale a todas as flags anteriores + extras
python_version = "3.10"
exclude = ["tests/", "venv/", ".venv/"]

# Overrides específicos se necessário:
# [[tool.mypy.overrides]]
# module = "scripts.legacy.*"
# ignore_errors = true
```

**Impacto Estimado:** +25 erros (~80 total)

## 🛠️ Plano de Ação Recomendado

### Fase 1: Preparação (Sprint 4.1)

**Objetivo:** Corrigir erros críticos e preparar infraestrutura

1. **Instalar Type Stubs Faltantes**

   ```bash
   pip install types-PyYAML types-python-frontmatter
   ```

2. **Corrigir 13 Erros Baseline**
   - `scripts/utils/atomic.py`: Fix **exit** return type e unreachable code
   - `scripts/audit_dashboard/storage.py`: Anotar retorno corretamente
   - `scripts/core/mock_generator.py`: Adicionar anotações de variáveis
   - `scripts/core/cortex/mapper.py`: Anotar listas vazias
   - `scripts/cortex/cli.py`: Anotar file_warnings

3. **Atualizar pyproject.toml para Nível 1**

**Entrega:** 0 erros com configuração Nível 1

### Fase 2: Hardening (Sprint 4.2)

**Objetivo:** Adicionar regras avançadas

1. **Adicionar Regras Nível 2**
2. **Corrigir Novos Erros** (~15 erros)
   - Foco em `type-arg` (generics)
   - Remover `# type: ignore` desnecessários

**Entrega:** 0 erros com configuração Nível 2

### Fase 3: Excelência (Sprint 4.3 - Opcional)

**Objetivo:** Modo strict completo

1. **Ativar `strict = true`**
2. **Corrigir Todos os Erros**
3. **Documentar Overrides** (se necessário)

**Entrega:** 0 erros com modo strict

## 🎯 Métricas de Sucesso

| Métrica | Baseline | Meta Sprint 4.1 | Meta Sprint 4.2 | Meta Sprint 4.3 |
|---------|----------|-----------------|-----------------|-----------------|
| **Erros Mypy** | 13 | 0 | 0 | 0 |
| **Regras Ativas** | 7 | 13 | 16 | 20+ (strict) |
| **Cobertura de Tipos** | ~70% | ~85% | ~95% | ~99% |
| **Arquivos com Erros** | 5 | 0 | 0 | 0 |

## 🔖 Anexos

### A1: Configuração Completa Proposta (Nível 1)

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.10"

# === RIGOR DE TIPAGEM ===
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_any_generics = true
disallow_subclassing_any = true

# === WARNINGS ===
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

# === CONTROLE DE NONE ===
no_implicit_optional = true
strict_optional = true

# === IMPORTS ===
# Temporariamente true até instalarmos todos os stubs
ignore_missing_imports = true
follow_imports = "normal"

# === MISC ===
strict_equality = true

# === EXCLUSÕES ===
exclude = [
    "tests/",
    "venv/",
    ".venv/",
    "build/",
    "dist/"
]

# === OVERRIDES PER-MODULE (se necessário) ===
# [[tool.mypy.overrides]]
# module = "scripts.legacy.*"
# ignore_errors = true
```

### A2: Comandos de Verificação

```bash
# Baseline atual
mypy . --show-error-codes --pretty

# Teste com Nível 1
mypy . --config-file mypy_strict.ini --show-error-codes

# Contagem de erros
mypy . | grep "error:" | wc -l

# Relatório HTML
mypy . --html-report mypy-report/
```

---

**Gerado por:** Copilot (Sprint 4 - Auditoria de Tipagem)
**Data:** 2025-12-01
**Baseline:** 13 erros em 5 arquivos
**Modo Estrito:** 40 erros em 17 arquivos
**Incremento:** +207%
