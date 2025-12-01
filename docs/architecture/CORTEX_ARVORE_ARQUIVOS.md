# 📂 CORTEX - Árvore de Arquivos Proposta

**Referência:** [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md)
**Data:** 2025-11-30

---

## 🎯 VISÃO GERAL

Esta árvore mostra TODOS os arquivos que serão criados/modificados durante a implementação do CORTEX.

**Legenda:**

- 🆕 Arquivo novo a ser criado
- 📝 Arquivo existente a ser modificado
- 📁 Diretório novo a ser criado

---

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

---

## 📊 ESTATÍSTICAS

### Arquivos Novos (🆕)

| Categoria | Quantidade | Sprint |
|-----------|------------|--------|
| **Core Python** | 5 | 1-2 |
| - models.py | 1 | 1 |
| - metadata.py | 1 | 1 |
| - scanner.py | 1 | 2 |
| - config.py | 1 | 1 |
| - \_\_init\_\_.py | 1 | 1 |
| **CLI Python** | 1 | 1-2-4 |
| - cortex.py | 1 | 1-2-4 |
| **Scripts** | 1 | 3 |
| - cortex_migrate.py | 1 | 3 |
| **Testes** | 2 | 1-2 |
| - test_cortex_metadata.py | 1 | 1 |
| - test_cortex_scanner.py | 1 | 2 |
| **Fixtures** | 5 | 1 |
| - valid_guide.md | 1 | 1 |
| - valid_arch.md | 1 | 1 |
| - invalid_missing_id.md | 1 | 1 |
| - invalid_bad_semver.md | 1 | 1 |
| - no_frontmatter.md | 1 | 1 |
| **CI/CD** | 1 | 4 |
| - docs-validation.yml | 1 | 4 |
| **TOTAL** | **15** | - |

### Arquivos Modificados (📝)

| Categoria | Quantidade | Sprint |
|-----------|------------|--------|
| **Configuração** | 2 | 0-4 |
| - pyproject.toml | 1 | 0 |
| - .pre-commit-config.yaml | 1 | 4 |
| **Documentação** | 30+ | 3 |
| - docs/architecture/*.md | 5 | 3 |
| - docs/guides/*.md | 2 | 3 |
| - docs/reference/*.md | 1 | 3 |
| - docs/history/**/*.md | 20+ | 3 |
| - docs/*.md | 3 | 3 |
| **TOTAL** | **32+** | - |

---

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

---

## 🔍 DETALHAMENTO DOS ARQUIVOS PRINCIPAIS

### 1. `scripts/core/cortex/models.py` (Sprint 1)

**Linhas Estimadas:** ~80 linhas
**Dependências:** `dataclasses`, `enum`, `pathlib`, `datetime`

```python
# Conteúdo:
- enum DocType(Enum): 4 valores
- enum DocStatus(Enum): 4 valores
- @dataclass DocumentMetadata: 10+ campos
- @dataclass ValidationResult: 3 campos
- @dataclass LinkCheckResult: 4 campos
```

### 2. `scripts/core/cortex/metadata.py` (Sprint 1)

**Linhas Estimadas:** ~150 linhas
**Dependências:** `frontmatter`, `pathlib`, `re`, `models.py`

```python
# Conteúdo:
- class FrontmatterParser:
    - parse_file(path: Path) -> DocumentMetadata
    - validate_metadata(metadata: dict) -> ValidationResult
    - _validate_id(id: str) -> bool
    - _validate_version(version: str) -> bool
    - _validate_date(date: str) -> bool
    - extract_missing_fields(metadata: dict) -> list[str]
```

### 3. `scripts/core/cortex/scanner.py` (Sprint 2)

**Linhas Estimadas:** ~120 linhas
**Dependências:** `pathlib`, `ast`, `models.py`

```python
# Conteúdo:
- class CodeLinkScanner:
    - check_python_files(linked_code: list[str]) -> list[Issue]
    - check_doc_links(related_docs: list[str]) -> list[Issue]
    - analyze_python_exports(py_file: Path) -> list[str]
    - _parse_ast(py_file: Path) -> ast.Module
```

### 4. `scripts/cli/cortex.py` (Sprint 1, 2, 4)

**Linhas Estimadas:** ~250 linhas
**Dependências:** `typer`, `pathlib`, `metadata.py`, `scanner.py`, `logger`, `banner`

```python
# Conteúdo:
- app = typer.Typer(name="cortex", help="...")
- @app.command() def init(path: Path, interactive: bool = False)
- @app.command() def audit(path: Path = None, fail_on_error: bool = False)
- @app.command() def report(format: str = "table", output: Path = None)
- def main()
```

### 5. `scripts/cortex_migrate.py` (Sprint 3)

**Linhas Estimadas:** ~200 linhas
**Dependências:** `pathlib`, `re`, `datetime`, `metadata.py`

```python
# Conteúdo:
- def generate_base_metadata(md_file: Path) -> dict
- def detect_code_references(md_content: str) -> list[str]
- def inject_frontmatter(md_file: Path, metadata: dict)
- def migrate_directory(dir_path: Path, dry_run: bool, interactive: bool)
- def main()  # CLI standalone
```

### 6. `tests/test_cortex_metadata.py` (Sprint 1)

**Linhas Estimadas:** ~200 linhas
**Dependências:** `pytest`, `unittest.mock`, `metadata.py`, `models.py`

```python
# Conteúdo:
- Fixtures: SAMPLE_VALID_MD, SAMPLE_INVALID_MD
- test_parse_valid_frontmatter()
- test_parse_missing_frontmatter()
- test_validate_id_valid()
- test_validate_id_invalid()
- test_validate_version_valid()
- test_validate_version_invalid()
- test_validate_date_valid()
- test_validate_date_invalid()
- test_extract_missing_fields()
```

### 7. `tests/test_cortex_scanner.py` (Sprint 2)

**Linhas Estimadas:** ~180 linhas
**Dependências:** `pytest`, `unittest.mock`, `scanner.py`, `models.py`

```python
# Conteúdo:
- test_check_valid_python_file()
- test_check_missing_python_file()
- test_check_valid_doc_link()
- test_check_missing_doc_link()
- test_analyze_python_exports()
- test_scan_directory_recursive()
```

---

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

11. Criar `scripts/cli/cortex.py` (comando `init` apenas)
12. Testar manualmente: `cortex init docs/test.md`

### Fase 4: Scanner (5 horas)

13. Criar `scripts/core/cortex/scanner.py` ✅ **CRÍTICO**
14. Criar `tests/test_cortex_scanner.py`
15. Atualizar `scripts/cli/cortex.py` (comando `audit`)

### Fase 5: Migração (14 horas)

16. Criar `scripts/cortex_migrate.py`
17. Testar em 1-2 arquivos manualmente
18. Migrar `docs/` completo
19. Validar com `cortex audit docs/`

### Fase 6: Automação (3 horas)

20. Atualizar `.pre-commit-config.yaml`
21. Criar `.github/workflows/docs-validation.yml`
22. Atualizar `scripts/cli/cortex.py` (comando `report`)

---

## 📝 NOTAS IMPORTANTES

### Sobre Fixtures de Teste

Os arquivos em `tests/fixtures/sample_docs/` são Markdown **reais** usados nos testes.

**Exemplo: `valid_guide.md`**

```markdown
---
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
  - scripts/cli/cortex.py
---

# Example Guide

This is a test fixture.
```

### Sobre Migração de `docs/`

**⚠️ CRÍTICO:** Fazer backup antes de migrar!

```bash
# Backup completo
cp -r docs/ docs.backup.$(date +%Y%m%d)/

# Ou usar Git
git checkout -b backup-pre-cortex
git add docs/
git commit -m "Backup: docs/ antes da migração CORTEX"
git checkout feature/cortex-implementation
```

---

## ✅ VALIDAÇÃO FINAL

**Antes de considerar o CORTEX completo, validar:**

- [ ] Todos os 15 arquivos novos foram criados
- [ ] `pyproject.toml` foi atualizado com dependências
- [ ] Todos os 30+ arquivos `.md` têm Frontmatter
- [ ] `pytest tests/test_cortex_*.py -v` passa (100% dos testes)
- [ ] `ruff check scripts/core/cortex/ scripts/cli/cortex.py` passa
- [ ] `mypy scripts/core/cortex/ scripts/cli/cortex.py` passa
- [ ] `mkdocs build --strict` passa
- [ ] `cortex audit docs/` retorna 0 erros
- [ ] Pre-commit hook funciona
- [ ] CI/CD workflow está verde

---

**Última Atualização:** 2025-11-30
**Referência:** [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md)
