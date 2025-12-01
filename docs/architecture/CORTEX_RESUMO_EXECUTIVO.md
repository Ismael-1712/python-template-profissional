# 🧠 CORTEX - Relatório de Design (Fase 01): RESUMO EXECUTIVO

**Data:** 30 de Novembro de 2025
**Status:** 🟡 Design Completo - Aguardando Implementação
**Documento Completo:** [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md)

---

## 📊 VISÃO GERAL

| Aspecto | Resultado |
|---------|-----------|
| **Objetivo** | Sistema de governança de documentação que trata `.md` como código |
| **Princípio** | "Se não tem metadados YAML, não existe no sistema" |
| **Padrão Arquitetural** | P26 (CLI + Core separados) |
| **Dependências Novas** | `python-frontmatter>=1.0.0`, `pyyaml>=6.0` |
| **Arquivos a Criar** | 8 novos arquivos Python + testes |
| **Migração Necessária** | 30+ arquivos `.md` existentes precisam de Frontmatter |

---

## 🎯 SCHEMA YAML DEFINITIVO

### Campos Obrigatórios

```yaml
---
id: unique-kebab-case-id              # ✅ OBRIGATÓRIO
type: guide | arch | reference | history  # ✅ OBRIGATÓRIO
status: draft | active | deprecated | archived  # ✅ OBRIGATÓRIO
version: 1.0.0                         # ✅ OBRIGATÓRIO (Semver)
author: Engineering Team               # ✅ OBRIGATÓRIO
date: 2025-11-30                       # ✅ OBRIGATÓRIO (ISO 8601)
context_tags: [testing, ci-cd]         # ⚠️ RECOMENDADO
linked_code:                           # ⚠️ RECOMENDADO
  - scripts/cli/cortex.py
dependencies: []                       # ❌ OPCIONAL
related_docs: []                       # ❌ OPCIONAL
---
```

### Validações Automáticas

| Campo | Validação | Regex/Enum |
|-------|-----------|------------|
| `id` | kebab-case | `^[a-z0-9]+(-[a-z0-9]+)*$` |
| `type` | Enum | `[guide, arch, reference, history]` |
| `status` | Enum | `[draft, active, deprecated, archived]` |
| `version` | Semver | `^\d+\.\d+\.\d+$` |
| `date` | ISO 8601 | `YYYY-MM-DD` |
| `linked_code` | Arquivo existe | Verifica paths relativos |

---

## 🏗️ ESTRUTURA DE ARQUIVOS (8 Novos Arquivos)

```
python-template-profissional/
├── scripts/
│   ├── cli/
│   │   └── 🆕 cortex.py                    # Interface Typer (CLI)
│   │
│   └── core/
│       └── 🆕 cortex/                      # Módulo Core
│           ├── __init__.py
│           ├── metadata.py                 # Parser de Frontmatter
│           ├── scanner.py                  # Validador de Links
│           ├── models.py                   # Data Classes
│           └── config.py                   # Configuração
│
├── tests/
│   ├── 🆕 test_cortex_metadata.py
│   ├── 🆕 test_cortex_scanner.py
│   └── fixtures/
│       └── 🆕 sample_docs/
│
└── pyproject.toml (atualizar dependencies)
```

---

## 📦 DEPENDÊNCIAS A ADICIONAR

### Adicionar em `pyproject.toml`

```toml
[project.optional-dependencies]
dev = [
    "pip-tools~=7.4",
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.25",

    # 🆕 CORTEX Dependencies
    "python-frontmatter>=1.0.0",  # Parser de Frontmatter
    "pyyaml>=6.0",                 # Validação YAML
]

[project.scripts]
cortex = "scripts.cli.cortex:main"  # 🆕 Novo entry point
```

### Instalar Dependências

```bash
# Após atualizar pyproject.toml
pip install -e .[dev]

# Ou via pip-tools
pip-compile requirements/dev.in
pip-sync requirements/dev.txt
```

---

## 🚀 ROADMAP DE IMPLEMENTAÇÃO

### Sprint 1: Foundation (11h) - **PRIORIDADE MÁXIMA**

| # | Task | Arquivo | Tempo |
|---|------|---------|-------|
| 1 | Criar models.py | `scripts/core/cortex/models.py` | 2h |
| 2 | Implementar parser | `scripts/core/cortex/metadata.py` | 4h |
| 3 | Criar testes unitários | `tests/test_cortex_metadata.py` | 3h |
| 4 | CLI básica (init) | `scripts/cli/cortex.py` | 2h |

**Entregável:** `cortex init file.md` funcionando

### Sprint 2: Validation (12h) - **ALTA PRIORIDADE**

| # | Task | Arquivo | Tempo |
|---|------|---------|-------|
| 5 | Implementar scanner | `scripts/core/cortex/scanner.py` | 5h |
| 6 | CLI audit command | `scripts/cli/cortex.py` | 3h |
| 7 | Testes de integração | `tests/test_cortex_scanner.py` | 4h |

**Entregável:** `cortex audit docs/` detectando links quebrados

### Sprint 3: Migration (16h) - **MÉDIA PRIORIDADE**

| # | Task | Arquivo | Tempo |
|---|------|---------|-------|
| 8 | Script de migração | `scripts/cortex_migrate.py` | 6h |
| 9 | Migrar docs/ existentes | Manual | 8h |
| 10 | Validar migração | - | 2h |

**Entregável:** Todos os 30+ docs com Frontmatter válido

### Sprint 4: Automation (7h) - **BAIXA PRIORIDADE**

| # | Task | Arquivo | Tempo |
|---|------|---------|-------|
| 11 | Pre-commit hook | `.pre-commit-config.yaml` | 1h |
| 12 | CI/CD workflow | `.github/workflows/docs-validation.yml` | 2h |
| 13 | Report command | `scripts/cli/cortex.py` | 4h |

**Entregável:** Validação automática em commits e PRs

**Total Estimado:** 46 horas (1,5 semanas para 1 desenvolvedor)

---

## 🔄 ESTRATÉGIA DE MIGRAÇÃO (Não-Destrutiva)

### Problema

30+ arquivos `.md` existentes **SEM** Frontmatter precisam ser migrados.

### Solução: Migração Semi-Automática em 3 Fases

#### Fase A: Geração Automática

- Script infere metadados básicos do contexto (diretório, nome do arquivo, data de modificação)
- Gera `id`, `type`, `status`, `version`, `author`, `date` automaticamente

#### Fase B: Revisão Manual Assistida

- CLI interativa sugere campos que precisam de revisão
- Detecta referências a arquivos `.py` no conteúdo e sugere `linked_code`
- Permite edição campo por campo

#### Fase C: Validação Pós-Migração

- `cortex audit docs/` verifica todos os arquivos
- Detecta Frontmatter inválido ou faltante
- Valida links quebrados

### Exemplo de Comando

```bash
# Dry-run (não modifica arquivos)
cortex migrate docs/ --dry-run

# Migração assistida (interativa)
cortex migrate docs/ --interactive

# Migração automática (⚠️ usar com cautela)
cortex migrate docs/ --auto-approve
```

---

## 🔒 CONFORMIDADE COM PADRÃO P26

### Checklist ✅

- [x] CLI separada do Core (`scripts/cli/cortex.py` vs `scripts/core/cortex/`)
- [x] Core sem dependências de Typer ou prints
- [x] Testes unitários isolados (mocks para filesystem)
- [x] Uso de `pathlib.Path` em vez de strings
- [x] Type hints completos (Python 3.10+)
- [x] Docstrings no formato Google
- [x] Logging via `scripts.utils.logger`
- [x] Banner via `scripts.utils.banner`

### Exemplo de Teste (SRE Standard)

```python
from unittest.mock import MagicMock, mock_open, patch

@patch("scripts.core.cortex.metadata.Path")
@patch("builtins.open", new_callable=mock_open, read_data=SAMPLE_MD)
def test_parse_valid_frontmatter(mock_file, mock_path):
    """❌ NUNCA toca no disco real"""
    mock_path.return_value.exists.return_value = True

    parser = FrontmatterParser()
    result = parser.parse_file(Path("fake.md"))

    assert result.id == "test-doc"
```

---

## 🚨 RISCOS E MITIGAÇÕES

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Frontmatter quebra MkDocs | 🟡 MÉDIO | Testar `mkdocs build` antes de commit |
| Migração manual lenta | 🟡 MÉDIO | Detecção automática de `linked_code` |
| Conflito de merge | 🟢 BAIXO | Git trata YAML bem (linha por linha) |
| Performance | 🟢 BAIXO | Usar generators (`Path.rglob("*.md")`) |

---

## 📋 COMANDOS CLI (Preview)

```bash
# Inicializar Frontmatter em arquivo novo
cortex init docs/new-guide.md

# Adicionar Frontmatter a arquivo existente (interativo)
cortex init docs/existing.md --interactive

# Auditar docs/ completo
cortex audit docs/

# Auditar e falhar em erros (CI mode)
cortex audit --fail-on-error

# Gerar relatório de cobertura
cortex report --format json --output cortex-report.json

# Migração em massa
cortex migrate docs/ --dry-run
```

---

## ✅ CRITÉRIOS DE ACEITAÇÃO (Fase 01)

**Este Design Está Completo:**

- [x] Schema YAML completo com validações definidas
- [x] Estrutura de arquivos seguindo P26 proposta
- [x] Dependências identificadas (`python-frontmatter`, `pyyaml`)
- [x] Estratégia de migração não-destrutiva planejada
- [x] Integração com MkDocs, Git, CI documentada
- [x] Roadmap de implementação por sprints estabelecido

**Próximos Passos:**

1. ✅ Revisar e aprovar schema YAML
2. ✅ Confirmar compatibilidade com MkDocs (testar com `mkdocs build`)
3. ✅ Validar estratégia de migração com stakeholders
4. 🟡 **Criar branch `feature/cortex-implementation`**
5. 🟡 **Iniciar Sprint 1 (Foundation)**

---

## 📚 REFERÊNCIAS

- **Documento Completo:** [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md)
- **Padrão P26:** [ARCHITECTURE_TRIAD.md](./ARCHITECTURE_TRIAD.md)
- **Guia de Testes:** [docs/guides/testing.md](../guides/testing.md)
- **Biblioteca Principal:** [python-frontmatter (PyPI)](https://pypi.org/project/python-frontmatter/)

---

**Status:** 🟢 **PRONTO PARA IMPLEMENTAÇÃO**
**Estimativa Total:** 46 horas (1,5 semanas)
**Próxima Ação:** Aprovação do Design e início do Sprint 1
