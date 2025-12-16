---
id: adr-003-src-gitkeep
type: arch
status: active
version: 1.0.0
author: SRE Team
date: '2025-11-15'
context_tags: [git, architecture, triad, stability]
linked_code:

  - scripts/cli/git_sync.py
title: 'ADR 003: Resolução de Conflito Arquitetural src/.gitkeep'
---

# ADR 003: Resolução de Conflito Arquitetural `src/.gitkeep`

## Status

**ACEITO** | Implementado em Novembro 2025 (v2.1.6)

## Contexto

O projeto utiliza uma **Arquitetura de Tríade** com três branches principais:

- `main`: "Chassi" SRE (ferramentas, docs, configs)
- `api`: Variante para aplicações web (adiciona `Dockerfile`, `src/main.py`)
- `cli`: Variante para ferramentas CLI (adiciona `typer`, `src/main.py`)

### O Problema: Conflito `modify/delete`

Durante operações de sincronização automática (`git-sync`) de `main` → `api`/`cli`, um **conflito permanente** foi descoberto:

1. **Branch `main`**: Contém `src/.gitkeep` (diretório vazio rastreado)
2. **Branches `api`/`cli`**: Substituem `src/.gitkeep` por `src/main.py` (código real)
3. **Conflito Git**: Quando `main` tenta atualizar `.gitkeep`, o Git detecta `modify/delete`
   - `main` quer **modificar** o arquivo
   - `api`/`cli` **deletaram** o arquivo (substituído por código)

**Impacto**: Quebra de automação `git-sync`, exigindo resolução manual em cada operação.

## Decisão

**Readicionar `src/.gitkeep` às branches `api` e `cli` mesmo sendo tecnicamente redundante.**

### Trade-off Arquitetural

```
Estabilidade da Automação > Pureza da Arquitetura
```

**Justificativa:**

- ✅ Elimina conflito permanente de `modify/delete`
- ✅ Permite automação `git-sync` rodar limpa (`Already up to date.`)
- ✅ Custo mínimo: arquivo de 1 linha coexiste com `src/main.py`
- ❌ Desvio da pureza: branches especializadas carregam arquivo do "chassi"

## Implementação

### 1. Estado Atual (v2.1.6)

Todas as três branches possuem `src/.gitkeep`:

```bash
# Branch main
src/.gitkeep  # Conteúdo: "# Este arquivo existe para garantir que o Git rastreie o diretório 'src'."

# Branch api
src/.gitkeep  # Mesmo conteúdo (coexiste com src/main.py)
src/main.py   # Código da aplicação

# Branch cli
src/.gitkeep  # Mesmo conteúdo (coexiste com src/main.py)
src/main.py   # Código da ferramenta
```

### 2. Proteção via Smart Git Sync

O script [`scripts/git_sync/sync_logic.py`](../../scripts/git_sync/sync_logic.py) detecta a branch `main` e bloqueia push direto:

```python
# Protection: prevent direct push to main
current_branch = git_status.get("current_branch")
if current_branch == "main":
    logger.error("🛑 OPERAÇÃO PROIBIDA NA 'main'")
    logger.error("A branch 'main' está protegida por regras ('Cofre').")
    raise SyncError("Tentativa de 'push' direto na 'main' protegida.")
```

### 3. Validação de Sincronização

Teste executado (Novembro 2025):

```bash
# Na branch api (após readição manual do .gitkeep)
git merge main

# Resultado
Already up to date.
```

**Prova**: Conflito resolvido permanentemente.

## Consequências

### Positivas

- ✅ **Automação Estável**: `git-sync` roda sem intervenção manual
- ✅ **Propagação Limpa**: Mudanças de `main` fluem sem conflitos
- ✅ **Rastreabilidade**: `src/` sempre rastreado pelo Git em todas as branches
- ✅ **Manutenibilidade**: LLMs futuras podem usar `git-sync` sem conhecimento do conflito histórico

### Negativas

- ❌ **Redundância Técnica**: `api`/`cli` têm arquivo desnecessário (1 linha)
- ⚠️ **Desvio Conceitual**: Branches especializadas carregam artefato do "chassi"

### Riscos Mitigados

- ✅ Eliminação de "toil" (trabalho manual repetitivo)
- ✅ Prevenção de erro humano em resolução de conflitos
- ✅ Garantia de idempotência do `git-sync`

## Alternativas Consideradas

### 1. Remover `src/.gitkeep` da `main`

**Problema**: `main` perderia rastreamento do diretório `src/`, quebrando a arquitetura do "chassi" puro.

### 2. Usar `.gitignore` em `api`/`cli`

**Problema**: Git não permite ignorar arquivo já rastreado. Conflito persistiria.

### 3. Resolver conflito manualmente a cada sync

**Problema**: Viola princípio de automação SRE. "Toil" inaceitável para operação recorrente.

## Referências

### Documentação Relacionada

- [TRIAD_GOVERNANCE.md](TRIAD_GOVERNANCE.md) - Arquitetura de branches
- [DIRECT_PUSH_PROTOCOL.md](../guides/DIRECT_PUSH_PROTOCOL.md) - Fluxo da Chave Mestra
- [SMART_GIT_SYNC_GUIDE.md](../guides/SMART_GIT_SYNC_GUIDE.md) - Automação de sincronização

### Código Implementado

- [`src/.gitkeep`](../../src/.gitkeep) - Arquivo de estabilização
- [`scripts/git_sync/sync_logic.py`](../../scripts/git_sync/sync_logic.py) - Proteção de `main`

### Histórico

- **Descoberta do Conflito**: Novembro 2025 (Interações 56-66)
- **Tentativa de Correção via PR**: PR #4 (Falha: conflito persistiu)
- **Resolução Final**: Readição manual em `api`/`cli` (Interação 78)
- **Validação**: Teste de `git-sync` rodou limpo (Interação 79)

---

**Última Atualização**: 2025-12-16
**Decisor**: Prof. de TI (Arquiteto Mentor) + Ismael Tavares (Engenheiro Chefe)
**Princípio Aplicado**: **Estabilidade > Arquitetura > Funcionalidades** (SRE v2.0)
