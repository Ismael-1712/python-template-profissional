---
id: cortex-arvore-arquivos
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code:
- scripts/core/cortex/models.py
- scripts/core/cortex/metadata.py
- scripts/core/cortex/scanner.py
- scripts/cortex/cli.py
- scripts/core/cortex/migrate.py
- tests/test_cortex_metadata.py
- tests/test_cortex_scanner.py
- scripts/core/cortex/__init__.py
- scripts/core/cortex/config.py
title: 📂 CORTEX - Árvore de Arquivos Proposta
---

# 📂 CORTEX - Árvore de Arquivos Proposta

**Referência:** [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md)
**Data:** 2025-11-30

## 🌳 ESTRUTURA COMPLETA

```
python-template-profissional/
│
├── 📝 pyproject.toml                          # Adicionar dependências + entry point
│
├── 📝 .pre-commit-config.yaml                 # Sprint 4: Adicionar hook cortex-audit
│
├── .github/
│   └── workflows/
│       └── 🆕 docs-validation.yml             # Sprint 4: CI/CD para validação
│
├── scripts/
│   │
│   ├── 🆕 cortex_migrate.py                   # Sprint 3: Script de migração standalone
│   │
│   ├── cli/
│   │   └── 🆕 cortex.py                       # Sprint 1 & 2 & 4: Interface Typer
│   │
│   └── core/
│       └── 📁 cortex/                         # Módulo Core do CORTEX
│           ├── 🆕 __init__.py                 # Sprint 1: Módulo marker
│           ├── 🆕 models.py                   # Sprint 1: Data Classes
│           ├── 🆕 metadata.py                 # Sprint 1: Parser de Frontmatter
│           ├── 🆕 scanner.py                  # Sprint 2: Validador de Links
│           └── 🆕 config.py                   # Sprint 1: Configuração padrão
│
├── tests/
│   ├── 🆕 test_cortex_metadata.py             # Sprint 1: Testes do parser
│   ├── 🆕 test_cortex_scanner.py              # Sprint 2: Testes do scanner
│   │
│   └── fixtures/
│       └── 📁 sample_docs/                    # Sprint 1: Markdown samples
│           ├── 🆕 valid_guide.md              # Fixture: Doc válido tipo guide
│           ├── 🆕 valid_arch.md               # Fixture: Doc válido tipo arch
│           ├── 🆕 invalid_missing_id.md       # Fixture: Doc sem campo id
│           ├── 🆕 invalid_bad_semver.md       # Fixture: Doc com version inválida
│           └── 🆕 no_frontmatter.md           # Fixture: Doc sem Frontmatter
│
└── docs/                                      # Sprint 3: Migrar TODOS os .md
    ├── 📝 index.md                            # Adicionar Frontmatter
    ├── 📝 README.md                           # Adicionar Frontmatter
    ├── 📝 README_test_mock_system.md          # Adicionar Frontmatter
    │
    ├── architecture/
    │   ├── 📝 ARCHITECTURE_TRIAD.md           # Adicionar Frontmatter
    │   ├── 📝 TRIAD_GOVERNANCE.md             # Adicionar Frontmatter
    │   ├── 📝 AUDIT_DASHBOARD_INTEGRATION.md  # Adicionar Frontmatter
    │   ├── 📝 CODE_AUDIT.md                   # Adicionar Frontmatter
    │   ├── CORTEX_FASE01_DESIGN.md            # JÁ TEM Frontmatter (criado neste PR)
    │   ├── CORTEX_RESUMO_EXECUTIVO.md         # SEM Frontmatter (criado neste PR)
    │   ├── CORTEX_CHECKLIST_IMPLEMENTACAO.md  # SEM Frontmatter (criado neste PR)
    │   └── CORTEX_ARVORE_ARQUIVOS.md          # SEM Frontmatter (este arquivo)
    │
    ├── guides/
    │   ├── 📝 SMART_GIT_SYNC_GUIDE.md         # Adicionar Frontmatter
    │   └── 📝 testing.md                      # Adicionar Frontmatter
    │
    ├── reference/
    │   └── 📝 git_sync.md                     # Adicionar Frontmatter
    │
    └── history/
        └── sprint_1_foundation/
            ├── 📝 FASE01_DISCOVERY_CEGUEIRA_FERRAMENTA.md
            ├── 📝 SPRINT1_README.md
            ├── 📝 P26_REFATORACAO_SCRIPTS_FASE01.md
            └── ... (20+ arquivos a migrar)
```

## 🎯 DEPENDÊNCIAS ENTRE ARQUIVOS

### Sprint 1: Foundation

```
models.py (independente)
    ↓
metadata.py (depende de models.py)
    ↓
test_cortex_metadata.py (depende de models.py + metadata.py)
    ↓
cortex.py (init command) (depende de metadata.py)
```

### Sprint 2: Validation

```
scanner.py (depende de models.py)
    ↓
test_cortex_scanner.py (depende de scanner.py)
    ↓
cortex.py (audit command) (depende de metadata.py + scanner.py)
```

### Sprint 3: Migration

```
cortex_migrate.py (depende de metadata.py + scanner.py)
    ↓
Migração manual de docs/ (usa cortex_migrate.py)
    ↓
Validação (usa cortex.py audit)
```

### Sprint 4: Automation

```
.pre-commit-config.yaml (usa cortex.py audit)
docs-validation.yml (usa cortex.py audit)
cortex.py (report command) (depende de scanner.py)
```

## 🚀 ORDEM DE CRIAÇÃO RECOMENDADA

### Fase 0: Setup (30 minutos)

1. Atualizar `pyproject.toml`
2. Executar `pip install -e .[dev]`
3. Criar diretórios: `scripts/core/cortex/`, `tests/fixtures/sample_docs/`

### Fase 1: Core (6 horas)

4. Criar `scripts/core/cortex/__init__.py`
5. Criar `scripts/core/cortex/models.py` ✅ **BASE**
6. Criar `scripts/core/cortex/config.py`
7. Criar `scripts/core/cortex/metadata.py` ✅ **CRÍTICO**
8. Criar fixtures em `tests/fixtures/sample_docs/`

### Fase 2: Testes (3 horas)

9. Criar `tests/test_cortex_metadata.py` ✅ **VALIDAÇÃO**
10. Executar testes: `pytest tests/test_cortex_metadata.py -v`

### Fase 3: CLI Básica (2 horas)

11. Criar `scripts/cortex/cli.py` (comando `init` apenas)
12. Testar manualmente: `cortex init docs/test.md`

### Fase 4: Scanner (5 horas)

13. Criar `scripts/core/cortex/scanner.py` ✅ **CRÍTICO**
14. Criar `tests/test_cortex_scanner.py`
15. Atualizar `scripts/cortex/cli.py` (comando `audit`)

### Fase 5: Migração (14 horas)

16. Criar `scripts/cortex_migrate.py`
17. Testar em 1-2 arquivos manualmente
18. Migrar `docs/` completo
19. Validar com `cortex audit docs/`

### Fase 6: Automação (3 horas)

20. Atualizar `.pre-commit-config.yaml`
21. Criar `.github/workflows/docs-validation.yml`
22. Atualizar `scripts/cortex/cli.py` (comando `report`)

id: example-guide
type: guide
status: active
version: 1.0.0
author: Test Author
date: 2025-11-30
context_tags:

- testing
- example
linked_code:
- scripts/cortex/cli.py

## ✅ VALIDAÇÃO FINAL

**Antes de considerar o CORTEX completo, validar:**

- [ ] Todos os 15 arquivos novos foram criados
- [ ] `pyproject.toml` foi atualizado com dependências
- [ ] Todos os 30+ arquivos `.md` têm Frontmatter
- [ ] `pytest tests/test_cortex_*.py -v` passa (100% dos testes)
- [ ] `ruff check scripts/core/cortex/ scripts/cortex/cli.py` passa
- [ ] `mypy scripts/core/cortex/ scripts/cortex/cli.py` passa
- [ ] `mkdocs build --strict` passa
- [ ] `cortex audit docs/` retorna 0 erros
- [ ] Pre-commit hook funciona
- [ ] CI/CD workflow está verde

---

**Última Atualização:** 2025-11-30
**Referência:** [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md)
