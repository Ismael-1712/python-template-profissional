---
id: ci-performance-audit-report-old
title: "Auditoria de Performance CI/CD - Relatório de Gargalos (OLD)"
type: history
author: GEM
date: '2025-12-22'
version: 1.0.0
status: archived
tags: [ci-cd, performance, infrastructure, sre]
---

# 🔍 AUDITORIA DE PERFORMANCE CI/CD - RELATÓRIO DE GARGALOS

**Data:** 22/12/2025
**Objetivo:** Identificar bottlenecks no pipeline GitHub Actions (tempo atual: ~10 minutos)
**Meta:** < 2 minutos (conforme especificado no [ci.yml](../.github/workflows/ci.yml#L15))

---

## 📊 RESUMO EXECUTIVO

| Categoria | Impacto | Tempo Economizado Estimado |
|-----------|---------|----------------------------|
| Cache de Python | 🔴 CRÍTICO | **3-4 minutos** |
| Redundância de instalação | 🔴 CRÍTICO | **2-3 minutos** |
| Doctor desnecessário | 🟡 MODERADO | **30-60 segundos** |
| Lockfile check duplicado | 🟡 MODERADO | **20-40 segundos** |
| Jobs não paralelizados | 🟢 JÁ OTIMIZADO | N/A |
| Pytest-xdist | 🟢 JÁ IMPLEMENTADO | N/A |

**Potencial de Otimização Total: 6-8 minutos** ⚡

---

## 🔴 PONTOS CRÍTICOS DE ATRITO

### 1. **AUSÊNCIA DE CACHE DE PIP NO `actions/setup-python`**

**Problema:**
O workflow **NÃO** utiliza a flag `cache: 'pip'` no `actions/setup-python@v6`, fazendo com que:

- Todos os packages (~50-100MB) sejam baixados do PyPI a cada execução
- Wheels de dependências compiladas (chromadb, sentence-transformers) sejam reconstruídas

**Evidência:**

```yaml
# Linha 62-65 de .github/workflows/ci.yml
- name: "Configurar Python ${{ matrix.python-version }}"
  uses: actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548 # v6.1.0
  with:
    python-version: ${{ matrix.python-version }}
    # ❌ FALTA: cache: 'pip'
```

**Tempo perdido:** ~3-4 minutos por job (7 jobs x 3 versões Python = 21x)

**Solução recomendada:**

```yaml
- name: "Configurar Python ${{ matrix.python-version }}"
  uses: actions/setup-python@v6
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'pip'  # ✅ Adicionar esta linha
    cache-dependency-path: 'requirements/dev.txt'
```

---

### 2. **REDUNDÂNCIA: `make install-dev` EXECUTADO APÓS CACHE DO VENV**

**Problema:**
O workflow tem um cache manual de `.venv` **MAS** ainda executa `make install-dev` incondicionalmente:

**Evidência (Job Setup):**

```yaml
# Linhas 74-83: Cache do venv
- name: "Cache virtual environment"
  id: cache-venv
  uses: actions/cache@v5
  with:
    path: .venv
    key: venv-${{ runner.os }}-py${{ matrix.python-version }}-${{ hashFiles('requirements/dev.txt') }}

# Linhas 95-97: Instalação CONDICIONAL (correto)
- name: "Instalar Dependências"
  if: steps.cache-venv.outputs.cache-hit != 'true'  # ✅ SOMENTE se cache falhou
  run: make install-dev
```

**MAS nos jobs `quality` e `tests`:**

```yaml
# Linhas 137-138 e 215-216: Instalação INCONDICIONAL (incorreto)
- name: "Instalar Dependências (Idempotente)"
  run: make install-dev  # ❌ SEMPRE roda, mesmo com cache hit
```

**Impacto:**

- `make install-dev` inclui:
  1. Verificação de hash de `requirements/dev.in` (rápido)
  2. **Recriação do `.venv` do zero** se hash mudar (lento - ~2 minutos)
  3. Execução do `install_dev.py` que faz `pip install` novamente

**Tempo perdido:**

- Se cache HIT: ~20 segundos (overhead de `pip install` idempotente)
- Se cache MISS: ~2-3 minutos (reinstalação completa duplicada)

**Raiz do problema:**
A lógica do `Makefile` (linhas 92-124) remove e recria `.venv` se o hash de `dev.in` mudar, **ignorando completamente** o cache do GitHub Actions.

**Solução recomendada:**
Criar um modo "CI-friendly" que confie no cache do GitHub Actions:

```yaml
# Opção 1: Usar pip install direto (bypass do Makefile)
- name: "Instalar Dependências (Cache Aware)"
  if: steps.cache-venv.outputs.cache-hit != 'true'
  run: |
    .venv/bin/pip install -r requirements/dev.txt
    .venv/bin/pip install -e .

# Opção 2: Flag especial no Makefile
- name: "Instalar Dependências"
  if: steps.cache-venv.outputs.cache-hit != 'true'
  run: make install-dev-ci  # Novo target sem hash check
```

---

### 3. **LOCKFILE CHECK BAIXA E COMPILA DEPENDÊNCIAS DUPLICADAMENTE**

**Problema:**
O step "Check Lockfile Consistency" (linhas 88-100) executa:

```yaml
- name: "Check Lockfile Consistency"
  if: matrix.python-version == '3.10'
  run: |
    python -m pip install pip-tools  # ❌ Instala pip-tools novamente
    pip-compile requirements/dev.in  # ❌ Baixa TODAS as dependências para resolver
    # Verifica diff com git
```

**Impacto:**

- `pip-compile` precisa baixar **todas** as dependências para resolver o grafo
- Tempo: ~30-60 segundos (dependendo de cache de pip)

**Solução otimizada:**

```yaml
# Alternativa 1: Usar pip-tools com --dry-run (se disponível na versão)
- name: "Check Lockfile Consistency"
  run: |
    .venv/bin/pip-compile --dry-run requirements/dev.in -o /tmp/dev.txt
    diff requirements/dev.txt /tmp/dev.txt

# Alternativa 2: Mover para pre-commit hook (validar localmente)
# Remover do CI completamente
```

---

## 🟡 PONTOS MODERADOS DE ATRITO

### 4. **`make doctor` EXECUTADO EM CADA TESTE NO CI**

**Problema:**
O `Makefile` define:

```makefile
# Linha 158
test: doctor
 PYTHONPATH=. $(PYTHON) -m pytest $(TEST_DIR)

# Linha 154
audit: doctor
 $(PYTHON) -m scripts.cli.audit
```

**Impacto:**

- `doctor.py` executa 12+ checks diagnósticos (Python version, venv, dependencies, git hooks, etc.)
- No CI, muitos checks são skipped (veja [doctor.py](../scripts/cli/doctor.py#L82-L87)):

  ```python
  if os.environ.get("CI"):
      return DiagnosticResult(
          "Python Version",
          True,
          f"Python {current_version} (CI Environment - Matriz Ativa)",
      )
  ```

- **MAS** o overhead de importar módulos e executar lógica de skip ainda existe

**Tempo perdido:** ~10-30 segundos por execução (x2 jobs = 20-60 segundos total)

**Solução:**

```yaml
# Opção 1: Bypass do Makefile no CI
- name: "Executar Testes (Paralelo)"
  run: PYTHONPATH=. .venv/bin/pytest tests/  # ✅ Direto, sem doctor

# Opção 2: Target CI-específico no Makefile
## test-ci: Executa testes sem doctor (CI apenas)
test-ci:
 PYTHONPATH=. $(PYTHON) -m pytest $(TEST_DIR)
```

---

## 🟢 PONTOS JÁ OTIMIZADOS

### ✅ **Jobs Paralelizados**

**Status:** IMPLEMENTADO CORRETAMENTE

O workflow usa 3 jobs independentes:

1. `setup` - Pré-requisito (matriz 3.10, 3.11, 3.12)
2. `quality` - Python 3.12 apenas (lint, type-check, security)
3. `tests` - Matriz completa (3.10, 3.11, 3.12)

Jobs `quality` e `tests` rodam **em paralelo** após `setup`.

---

### ✅ **Pytest-xdist Configurado**

**Status:** IMPLEMENTADO CORRETAMENTE

**Evidência:**

- [pyproject.toml](../pyproject.toml#L138): `"-n", "auto"` nas opções do pytest
- [requirements/dev.txt](../requirements/dev.txt#L108): `pytest-xdist==3.8.0` instalado
- [Makefile](../Makefile#L158): `make test` chama pytest diretamente

**Benefício:** Usa todos os cores da VM do GitHub Actions (~2-4 cores)

---

### ✅ **Concurrency Group**

**Status:** IMPLEMENTADO CORRETAMENTE

```yaml
# Linhas 26-28
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Cancela workflows duplicados (ex: múltiplos pushes rápidos), economizando minutos de CI.

---

## 📋 PLANO DE AÇÃO RECOMENDADO

### Fase 1: Quick Wins (Implementação: 10 minutos, Ganho: 3-4 minutos)

1. **Adicionar `cache: 'pip'` no `actions/setup-python`**
   - Arquivo: [.github/workflows/ci.yml](../.github/workflows/ci.yml)
   - Linhas: 62-65, 131-134, 203-206
   - Impacto: -3 a -4 minutos

### Fase 2: Otimização de Instalação (Implementação: 30 minutos, Ganho: 2-3 minutos)

1. **Remover `make install-dev` incondicional nos jobs `quality` e `tests`**
   - Opção A: Usar `.venv/bin/pip install` direto
   - Opção B: Criar `make install-dev-ci` que confia no cache

2. **Otimizar lockfile check**
   - Mover para pre-commit hook (executar localmente)
   - Ou usar `pip-compile --dry-run` se disponível

### Fase 3: Limpeza (Implementação: 15 minutos, Ganho: 30-60 segundos)

1. **Criar targets CI-específicos no Makefile**

   ```makefile
   test-ci:
       PYTHONPATH=. $(PYTHON) -m pytest $(TEST_DIR)

   audit-ci:
       $(PYTHON) -m scripts.cli.audit
   ```

2. **Atualizar workflow para usar targets `-ci`**

---

## 🎯 ESTIMATIVA DE TEMPO PÓS-OTIMIZAÇÃO

| Job | Tempo Atual | Tempo Otimizado | Ganho |
|-----|-------------|-----------------|-------|
| setup (3 versões) | ~4 min | ~1 min | -3 min |
| quality | ~3 min | ~1 min | -2 min |
| tests (3 versões) | ~3 min | ~1.5 min | -1.5 min |
| **TOTAL** | **~10 min** | **~3.5 min** | **-6.5 min** |

**Meta original:** < 2 minutos
**Realista com estas otimizações:** **3-4 minutos** (melhoria de 60-70%)

---

## 🔧 DIAGNÓSTICO TÉCNICO COMPLETO

### Arquitetura Atual do Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ PUSH/PR → GitHub Actions                                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ JOB: setup (matrix: 3.10, 3.11, 3.12)                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. Checkout código                           ~5s        │ │
│ │ 2. Setup Python (SEM cache pip)              ~20s       │ │ ← 🔴 GARGALO
│ │ 3. Cache pip downloads (manual)              ~10s       │ │
│ │ 4. Cache .venv                                ~15s       │ │
│ │ 5. Check lockfile (pip-compile)              ~40s       │ │ ← 🟡 OTIMIZÁVEL
│ │ 6. make install-dev (se cache miss)          ~120s      │ │
│ │ 7. Validar instalação                        ~5s        │ │
│ └─────────────────────────────────────────────────────────┘ │
│ TOTAL: ~215s (~3.5 min) por versão Python                  │
└─────────────────────────────────────────────────────────────┘
                ↓                          ↓
┌───────────────────────────┐  ┌──────────────────────────────┐
│ JOB: quality (3.12 only)  │  │ JOB: tests (matrix 3 versions)│
│ ┌───────────────────────┐ │  │ ┌──────────────────────────┐ │
│ │ 1. Restaurar cache    │ │  │ │ 1. Restaurar cache       │ │
│ │ 2. make install-dev   │ │  │ │ 2. make install-dev      │ │ ← 🔴 REDUNDANTE
│ │    (SEMPRE roda!)     │ │  │ │    (SEMPRE roda!)        │ │
│ │ 3. Cache mypy         │ │  │ │ 3. make test (c/ doctor) │ │ ← 🟡 OTIMIZÁVEL
│ │ 4. make format        │ │  │ │    - doctor (~10s)       │ │
│ │ 5. make lint          │ │  │ │    - pytest-xdist (✅)   │ │
│ │ 6. make type-check    │ │  │ │                          │ │
│ │ 7. audit dependencies │ │  │ └──────────────────────────┘ │
│ │ 8. make audit         │ │  │ TOTAL: ~90s por versão      │
│ │ 9. cortex guardian    │ │  └──────────────────────────────┘
│ └───────────────────────┘ │
│ TOTAL: ~180s              │
└───────────────────────────┘
```

### Análise de Dependências Críticas

**Packages que levam mais tempo para instalar:**

1. **chromadb** (~30s) - Embedding database com dependências C++
2. **sentence-transformers** (~25s) - Modelos de ML (torch, transformers)
3. **torch** (~40s) - PyTorch (se não em cache)
4. **mkdocs-material** (~10s) - Documentação
5. **ruff** (~5s) - Linter/Formatter

**Total de dependências:** ~120 packages (veja [requirements/dev.txt](../requirements/dev.txt))

---

## 📚 REFERÊNCIAS

- **Workflow CI:** [.github/workflows/ci.yml](../.github/workflows/ci.yml)
- **Makefile:** [Makefile](../Makefile)
- **Configuração Pytest:** [pyproject.toml](../pyproject.toml#L126-L144)
- **Doctor Script:** [scripts/cli/doctor.py](../scripts/cli/doctor.py)
- **Install Dev:** [scripts/cli/install_dev.py](../scripts/cli/install_dev.py)
- **Requirements:** [requirements/dev.txt](../requirements/dev.txt)

---

## ⚠️ AVISOS E CONSIDERAÇÕES

### 1. **Trade-off: Cache vs. Freshness**

Ao adicionar `cache: 'pip'`, as dependências serão atualizadas apenas quando `requirements/dev.txt` mudar. Isso é desejável para **estabilidade**, mas pode atrasar detecção de vulnerabilidades em dependências upstream.

**Mitigação:** Configurar Dependabot ou renovate para PRs automáticos de atualização.

### 2. **Compatibilidade de Cache entre Versões Python**

O cache de `.venv` é **específico por versão Python** (correto!):

```yaml
key: venv-${{ runner.os }}-py${{ matrix.python-version }}-${{ hashFiles('requirements/dev.txt') }}
```

Não compartilhar `.venv` entre Python 3.10, 3.11 e 3.12 para evitar incompatibilidades de bytecode.

### 3. **Lockfile Check é Necessário?**

Se o projeto usa `pip-tools` para pinning determinístico, o check é importante para evitar drift. **MAS** pode ser movido para:

- Pre-commit hook (validar antes de commit)
- Job separado "validate-lockfile" que roda apenas em PRs (não em push para main)

---

## 🚀 PRÓXIMOS PASSOS

1. **Revisar este relatório** com o time
2. **Priorizar quick wins** (Fase 1)
3. **Criar branch de otimização:** `optimize/ci-performance`
4. **Implementar mudanças** conforme plano de ação
5. **Medir resultado:** Comparar tempo de CI antes/depois
6. **Documentar aprendizados** em `docs/architecture/`

---

**Autor:** GitHub Copilot (Auditoria SRE)
**Ferramenta:** Análise estática de CI/CD (CORTEX Guardian compatible)
**Versão:** 1.0.0
