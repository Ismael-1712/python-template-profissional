---
id: cortex-checklist-implementacao
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code:
- scripts/core/cortex/__init__.py
- scripts/core/cortex/models.py
- scripts/core/cortex/metadata.py
- tests/test_cortex_metadata.py
- scripts/cli/cortex.py
- scripts/core/cortex/scanner.py
- tests/test_cortex_scanner.py
- scripts/cortex_migrate.py
title: 🧠 CORTEX - Checklist de Implementação
---

# 🧠 CORTEX - Checklist de Implementação

**Referência:** [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md)
**Status Geral:** 🔴 Não Iniciado
**Última Atualização:** 2025-11-30

## 🚀 SPRINT 1: FOUNDATION (11h)

**Objetivo:** Sistema funcional de parsing e validação
**Status:** 🔴 Não Iniciado

### Task 1: Criar models.py (2h)

- [ ] Criar `scripts/core/cortex/models.py`
- [ ] Implementar `enum DocType`
- [ ] Implementar `enum DocStatus`
- [ ] Implementar `@dataclass DocumentMetadata`
- [ ] Implementar `@dataclass ValidationResult`
- [ ] Implementar `@dataclass LinkCheckResult`
- [ ] Adicionar type hints completos (Python 3.10+)
- [ ] Adicionar docstrings no formato Google

### Task 2: Implementar parser (4h)

- [ ] Criar `scripts/core/cortex/metadata.py`
- [ ] Implementar `class FrontmatterParser`
- [ ] Implementar método `parse_file(path: Path) -> DocumentMetadata`
- [ ] Implementar método `validate_metadata(metadata: dict) -> ValidationResult`
- [ ] Implementar validação de campo `id` (regex: `^[a-z0-9]+(-[a-z0-9]+)*$`)
- [ ] Implementar validação de campo `type` (enum)
- [ ] Implementar validação de campo `status` (enum)
- [ ] Implementar validação de campo `version` (semver: `^\d+\.\d+\.\d+$`)
- [ ] Implementar validação de campo `date` (ISO 8601: `YYYY-MM-DD`)
- [ ] Tratar erros de parsing YAML
- [ ] Tratar arquivos sem Frontmatter

### Task 3: Criar testes unitários (3h)

- [ ] Criar `tests/test_cortex_metadata.py`
- [ ] Criar fixtures com Markdown samples válidos
- [ ] Criar fixtures com Markdown samples inválidos
- [ ] Teste: `test_parse_valid_frontmatter()`
- [ ] Teste: `test_parse_missing_frontmatter()`
- [ ] Teste: `test_validate_id_kebab_case()`
- [ ] Teste: `test_validate_invalid_type()`
- [ ] Teste: `test_validate_invalid_semver()`
- [ ] Teste: `test_validate_invalid_date()`
- [ ] Mockar filesystem com `@patch("builtins.open")`
- [ ] Mockar Path com `@patch("pathlib.Path")`
- [ ] Validar cobertura de testes (mínimo 90%)

### Task 4: CLI básica (init) (2h)

- [ ] Criar `scripts/cli/cortex.py`
- [ ] Importar `typer`
- [ ] Criar `app = typer.Typer(name="cortex")`
- [ ] Implementar comando `@app.command() def init(path: Path)`
- [ ] Implementar geração de metadados base
- [ ] Implementar escrita de Frontmatter no arquivo
- [ ] Implementar modo `--interactive` (opcional)
- [ ] Adicionar logging via `scripts.utils.logger`
- [ ] Adicionar banner via `scripts.utils.banner`
- [ ] Criar `def main()` como entry point
- [ ] Testar execução: `cortex init docs/test.md`

**Entregável Sprint 1:** ✅ `cortex init file.md` funcionando

## 🔄 SPRINT 3: MIGRATION (16h)

**Objetivo:** Migrar todos os docs existentes para o novo formato
**Status:** 🔴 Não Iniciado

### Task 8: Script de migração (6h)

- [ ] Criar `scripts/cortex_migrate.py` (pode ser standalone ou integrado)
- [ ] Implementar função `generate_base_metadata(md_file: Path) -> dict`
- [ ] Inferir `type` baseado no diretório (architecture/, guides/, etc)
- [ ] Inferir `id` do nome do arquivo (kebab-case)
- [ ] Inferir `date` do timestamp de modificação do arquivo
- [ ] Implementar função `detect_code_references(md_content: str) -> list[str]`
- [ ] Usar regex para encontrar menções a arquivos `.py`
- [ ] Implementar função `inject_frontmatter(md_file: Path, metadata: dict)`
- [ ] Implementar modo `--dry-run` (não modifica arquivos)
- [ ] Implementar modo `--interactive` (pede confirmação para cada arquivo)
- [ ] Implementar modo `--auto-approve` (⚠️ use com cautela)
- [ ] Adicionar logging detalhado de cada operação
- [ ] Testar com arquivos de exemplo antes de aplicar em docs/

### Task 9: Migrar docs/ existentes (8h)

**⚠️ IMPORTANTE: Fazer backup antes de iniciar!**

- [ ] Criar backup de `docs/`: `cp -r docs/ docs.backup/`
- [ ] Executar `cortex migrate docs/ --dry-run` e revisar output
- [ ] Migrar `docs/architecture/*.md` (5 arquivos)
  - [ ] ARCHITECTURE_TRIAD.md
  - [ ] TRIAD_GOVERNANCE.md
  - [ ] AUDIT_DASHBOARD_INTEGRATION.md
  - [ ] CODE_AUDIT.md
  - [ ] CORTEX_FASE01_DESIGN.md (este arquivo!)
- [ ] Migrar `docs/guides/*.md` (2 arquivos)
  - [ ] SMART_GIT_SYNC_GUIDE.md
  - [ ] testing.md
- [ ] Migrar `docs/reference/*.md` (1 arquivo)
  - [ ] git_sync.md
- [ ] Migrar `docs/history/**/*.md` (20+ arquivos)
- [ ] Revisar manualmente cada arquivo migrado
- [ ] Ajustar `context_tags` e `linked_code` conforme necessário
- [ ] Validar que o conteúdo original não foi alterado

### Task 10: Validar migração (2h)

- [ ] Executar `cortex audit docs/` após migração
- [ ] Verificar que todos os arquivos têm Frontmatter válido
- [ ] Corrigir links quebrados identificados pelo audit
- [ ] Testar build do MkDocs: `mkdocs build --strict`
- [ ] Validar que a documentação renderiza corretamente
- [ ] Fazer commit das mudanças

**Entregável Sprint 3:** ✅ Todos os 30+ docs com Frontmatter válido

## ✅ CRITÉRIOS DE CONCLUSÃO

**O projeto CORTEX está completo quando:**

- [ ] Todas as tasks dos 4 sprints estão marcadas como ✅
- [ ] Testes unitários têm cobertura >= 90%
- [ ] Todos os testes passam: `pytest tests/test_cortex_*.py -v`
- [ ] Linting passa: `ruff check scripts/core/cortex/ scripts/cli/cortex.py`
- [ ] Type checking passa: `mypy scripts/core/cortex/ scripts/cli/cortex.py`
- [ ] Todos os docs/ têm Frontmatter válido
- [ ] `mkdocs build --strict` passa sem erros
- [ ] Pre-commit hook está ativo e funcionando
- [ ] CI/CD workflow está verde
- [ ] Documentação do CORTEX está atualizada (README, guides)

## 🔗 REFERÊNCIAS

- [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md) - Design completo
- [CORTEX_RESUMO_EXECUTIVO.md](./CORTEX_RESUMO_EXECUTIVO.md) - Resumo executivo
- [ARCHITECTURE_TRIAD.md](./ARCHITECTURE_TRIAD.md) - Padrão P26
- [testing.md](../guides/testing.md) - Guia de testes SRE

---

**Última Atualização:** 2025-11-30
**Mantenedor:** Engineering Team
