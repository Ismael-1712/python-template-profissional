---
id: task-runner-pattern
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-16'
tags: [ci-cd, makefile, task-runner, automation]
context_tags: [architecture, dx-optimization]
linked_code:
  - scripts/cli/install_dev.py
title: 'Task Runner Pattern - Makefile como Fonte Única da Verdade'
---

# Task Runner Pattern - Makefile como Fonte Única da Verdade

## Status

**Active** - Implementado em 2025-11

## Conceito

O **Task Runner Pattern** é uma arquitetura de CI/CD onde o workflow do GitHub Actions (ou qualquer CI) **não contém lógica de negócio**. Toda a lógica de execução (como executar lint, testes, build) está centralizada em um único artefato: o `Makefile`.

### Metáfora

```
┌─────────────────────────────────────────────────┐
│  CI/CD Workflow (.github/workflows/ci.yml)      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  "Porteiro" - Delega, não executa               │
│                                                  │
│    steps:                                        │
│      - run: make lint    ◄─────┐               │
│      - run: make test    ◄─────┼───┐           │
│      - run: make audit   ◄─────┘   │           │
│                                      │           │
└──────────────────────────────────────┼───────────┘
                                       │
                                       │ Delega
                                       ▼
┌─────────────────────────────────────────────────┐
│  Makefile (Fonte Única da Verdade)              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  "Orquestrador" - Contém a lógica real          │
│                                                  │
│  lint:                                           │
│    $(PYTHON) -m ruff check .                    │
│                                                  │
│  test:                                           │
│    $(PYTHON) -m pytest $(TEST_DIR)              │
│                                                  │
│  audit:                                          │
│    $(PYTHON) $(SCRIPTS_DIR)/code_audit.py       │
└─────────────────────────────────────────────────┘
```

## Por Que Isso Importa?

### Problema Antes (CI/CD com Lógica Acoplada)

**Antes**, nosso `.github/workflows/ci.yml` poderia conter:

```yaml
- name: Run Lint
  run: |
    python -m ruff check src/ tests/ --config pyproject.toml
    python -m mypy src/ tests/ --strict
```

**Problemas:**

1. ❌ **Duplicação**: Se mudássemos o comando de lint, teríamos que atualizar o workflow YAML
2. ❌ **Testabilidade Local**: Desenvolvedores não podiam executar **exatamente** o mesmo comando localmente
3. ❌ **Deriva de Configuração**: CI e ambiente local divergiam ao longo do tempo
4. ❌ **Lock-in de CI**: Migrar para GitLab CI ou Azure Pipelines requereria reescrever toda a lógica

### Solução Atual (Task Runner Pattern)

**Agora**, nosso `.github/workflows/ci.yml` contém:

```yaml
- name: Run Lint
  run: make lint
```

E o `Makefile` define:

```makefile
lint:
 PYTHONPATH=. $(PYTHON) -m ruff check .
```

**Benefícios:**

1. ✅ **DRY**: Um único local define como executar lint
2. ✅ **Paridade Local/CI**: `make lint` funciona **idêntico** em qualquer ambiente
3. ✅ **Portabilidade**: Trocar de CI requer apenas mudar `run: make lint` (sintaxe universal)
4. ✅ **Manutenibilidade**: Mudanças de ferramentas (ex: trocar `ruff` por `pylint`) requerem editar apenas o Makefile

## Implementação Atual

### 1. Estrutura do Makefile

Nosso [`Makefile`](../../Makefile) está organizado em **targets** (tarefas):

```makefile
# Targets principais usados pelo CI
lint:        # Verificação de código (ruff)
type-check:  # Análise de tipos (mypy)
test:        # Suite de testes (pytest)
audit:       # Auditoria de segurança
validate:    # Validação completa (lint + type-check + test)

# Targets de desenvolvimento
format:      # Auto-formatação
install-dev: # Setup do ambiente
doctor:      # Diagnóstico do ambiente
```

### 2. Integração com CI/CD

O workflow [`ci.yml`](../../.github/workflows/ci.yml) delega **todas** as tarefas ao Makefile:

```yaml
jobs:
  quality-gate:
    steps:
      - name: "Instalar Dependências"
        run: make install-dev

      - name: "Executar Linting"
        run: make lint

      - name: "Executar Type Checking"
        run: make type-check

      - name: "Executar Testes"
        run: make test
```

**Nota Crítica**: O `ci.yml` não contém nenhum comando Python direto. É um "porteiro burro" que apenas delega.

### 3. VENV-Aware Execution

O Makefile detecta automaticamente o ambiente virtual:

```makefile
# Detecção automática de venv
ifneq ($(wildcard $(VENV)/bin/python),)
 PYTHON := $(VENV)/bin/python
else
 PYTHON := $(SYSTEM_PYTHON)
endif

lint:
 PYTHONPATH=. $(PYTHON) -m ruff check .
```

Isso garante que:

- 🟢 **Localmente**: Desenvolvedores executam `make lint` e o Makefile usa `.venv/bin/python`
- 🟢 **No CI**: GitHub Actions executa `make lint` e o Makefile detecta o mesmo `.venv/bin/python` criado pelo CI

## Padrões de Uso

### Desenvolvedor Local

```bash
# Setup inicial
make install-dev

# Durante desenvolvimento
make lint          # Verifica código
make test          # Roda testes
make format        # Formata código

# Antes de commit
make validate      # Roda lint + type-check + test
```

### CI/CD (GitHub Actions)

```yaml
- run: make install-dev
- run: make lint
- run: make test
```

### Outros CIs (GitLab, Azure)

A migração é trivial:

```yaml
# GitLab CI
script:
  - make install-dev
  - make lint
  - make test

# Azure Pipelines
- script: make install-dev
- script: make lint
- script: make test
```

## Evolução e Roadmap

### Estado Atual (v1.0)

- ✅ Makefile como único ponto de entrada
- ✅ CI/CD workflow agnóstico (apenas delega)
- ✅ Paridade local/CI garantida

### Futuro (Propostas)

#### P3 (Prioridade Média): Migrar Scripts Python CLI para Makefile

**Contexto**: Atualmente temos comandos CLI em `scripts/cli/` (ex: `dev-doctor`, `dev-audit`) definidos no `pyproject.toml`. Estes **não** quebram o padrão, mas existe redundância.

**Proposta**:

```makefile
# Hoje (coexistem):
make doctor      # Via Makefile
dev-doctor       # Via console script (pyproject.toml)

# Futuro (consolidado):
make doctor      # Única interface
```

**Benefício**: Reduz duplicação e fortalece o Makefile como "interface universal".

**Trade-off**: Console scripts são úteis para automações externas (ex: `docker run meu-app dev-audit`).

## Lições Aprendidas

### ✅ O Que Funciona

1. **Simplicidade Vence**: Um `Makefile` de 100 linhas é mais mantível que 500 linhas de YAML complexo
2. **Universalidade**: Desenvolvedores conhecem `make` há décadas
3. **Testabilidade**: Bugs de CI são reproduzíveis localmente com `make <target>`

### ⚠️ Trade-offs

1. **Curva de Aprendizado**: Desenvolvedores júnior podem não conhecer sintaxe Make
   - **Mitigação**: `make help` lista todos os comandos
2. **Menos Features**: Makefile não tem versionamento de dependências como Taskfile.yml ou Poetry scripts
   - **Mitigação**: Para projetos Python complexos, isso não é limitante

## Referências

- [Código: Makefile](../../Makefile)
- [Código: CI Workflow](../../.github/workflows/ci.yml)
- [Documentação: CI/CD Integration](../guides/CI_CD_INTEGRATION.md) (se existir)

## Mudanças Relacionadas

- [ADR 002: Pre-Commit Optimization](./ADR_002_PRE_COMMIT_OPTIMIZATION.md) - Outro exemplo de "Source of Truth" pattern

---

**Autor**: Engineering Team
**Última Atualização**: 2025-12-16
**Status**: Active
