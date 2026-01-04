---
id: guide-git-workflow-troubleshooting
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: '2026-01-04'
context_tags:
  - git
  - workflow
  - troubleshooting
  - automation
  - best-practices
linked_code: []
title: Git Workflow Troubleshooting Guide
---

# 🔧 Git Workflow Troubleshooting Guide

**Objetivo:** Resolver problemas comuns no workflow Git do projeto e prevenir sua recorrência.

---

## 🚨 Problema 1: "Working tree has uncommitted changes" ao executar post-pr-cleanup.sh

### Sintoma

```bash
❌ ERROR: Working tree has uncommitted changes. Please commit or stash them first.

Uncommitted changes:
 M docs/reports/COMPLEXITY_GOD_FUNCTIONS.md
```

### Causa Raiz

**Formatação Automática de Editores/IDEs:**

- Editores (VS Code, IntelliJ, etc.) podem auto-formatar arquivos ao salvar
- `.editorconfig` configurado com `trim_trailing_whitespace = true` afeta todos os arquivos
- Markdown pode ter espaços intencionais para quebras de linha
- Mudanças cosméticas (linhas em branco adicionadas) geram diff indesejado

### Solução Imediata

**Opção 1: Verificar e Descartar (Recomendado se forem apenas mudanças de formatação)**

```bash
# 1. Ver o que mudou
git diff <arquivo>

# 2. Se forem apenas mudanças cosméticas, descartar:
git restore <arquivo>

# 3. Executar limpeza
./scripts/git/post-pr-cleanup.sh <branch-name>
```

**Opção 2: Commitar (Se houver mudanças significativas)**

```bash
# 1. Ver mudanças
git diff

# 2. Adicionar e commitar
git add .
git commit -m "docs: fix formatting"

# 3. Push
git push

# 4. Executar limpeza
./scripts/git/post-pr-cleanup.sh <branch-name>
```

**Opção 3: Stash Temporário**

```bash
# 1. Guardar mudanças temporariamente
git stash

# 2. Executar limpeza
./scripts/git/post-pr-cleanup.sh <branch-name>

# 3. Recuperar mudanças (se necessário)
git stash pop
```

### Prevenção (Implementado)

**1. Configuração `.editorconfig` Atualizada:**

```ini
# Markdown: Preserve formatting to avoid auto-format conflicts
[*.md]
trim_trailing_whitespace = false
# Note: Markdown files may have intentional trailing spaces
```

**2. Boas Práticas:**

- ✅ **Sempre verificar `git status` antes de executar scripts de limpeza**
- ✅ **Desabilitar auto-save em editores ao trabalhar com documentação**
- ✅ **Usar `git diff` para revisar mudanças antes de descartar**
- ✅ **Commitar trabalho antes de mudar de branch**

---

## 🚨 Problema 2: Branches api/cli desincronizadas com main

### Sintoma

Branches `api` e `cli` ficam para trás (`behind`) em relação a `main` após merge de PRs.

### Causa Raiz

O script `post-pr-cleanup.sh` automatiza a sincronização, mas requer working tree limpa.

### Solução

**Automática (via post-pr-cleanup.sh):**

```bash
# O script já sincroniza api/cli automaticamente:
./scripts/git/post-pr-cleanup.sh <branch-merged>
```

**Manual (se necessário):**

```bash
# 1. Atualizar main
git checkout main
git pull origin main

# 2. Atualizar cli
git checkout cli
git pull origin cli
# Ou se estiver muito atrás:
git merge origin/main

# 3. Atualizar api
git checkout api
git pull origin api
# Ou se estiver muito atrás:
git merge origin/main

# 4. Voltar para main
git checkout main
```

### Prevenção

- ✅ **Sempre executar `post-pr-cleanup.sh` após merge de PR**
- ✅ **Não fazer mudanças manuais em branches sem sincronizar**
- ✅ **Usar `git branch -vv` para verificar estado de sincronização**

---

## 🚨 Problema 3: Conflitos de Merge em api/cli

### Sintoma

```
CONFLICT (content): Merge conflict in <file>
Automatic merge failed; fix conflicts and then commit the result.
```

### Causa Raiz

- Mudanças divergentes em arquivos compartilhados
- Falta de sincronização regular com main
- Edições manuais em branches que deveriam receber apenas propagação automática

### Solução

**1. Identificar Conflitos:**

```bash
git status
# Mostra arquivos em conflito
```

**2. Resolver Manualmente:**

```bash
# Abrir arquivo em editor e resolver marcadores:
# <<<<<<< HEAD
# =======
# >>>>>>> origin/main

# Após resolver:
git add <arquivo>
git commit -m "merge: resolve conflicts from main"
```

**3. Usar Ferramenta de Merge:**

```bash
git mergetool
```

### Prevenção

- ✅ **Sincronizar api/cli frequentemente com main**
- ✅ **Evitar edições manuais em branches api/cli**
- ✅ **Usar `git pull --rebase` quando possível**
- ✅ **Revisar mudanças antes de fazer merge**

---

## 🛠️ Comandos Úteis de Diagnóstico

### Verificar Estado Geral

```bash
# Status atual
git status

# Branches locais e remotas
git branch -vv

# Branches remotas
git branch -r

# Último commit
git log --oneline -1
```

### Verificar Sincronização

```bash
# Ver diferença entre local e remote
git fetch
git status

# Ver commits que faltam
git log HEAD..origin/main --oneline

# Ver commits à frente
git log origin/main..HEAD --oneline
```

### Limpar Working Tree

```bash
# Ver arquivos modificados
git status -s

# Ver mudanças específicas
git diff <arquivo>

# Descartar mudanças
git restore <arquivo>

# Descartar tudo (CUIDADO!)
git restore .

# Limpar arquivos não rastreados
git clean -fd
```

---

## 📋 Checklist Pré-Limpeza

Antes de executar `post-pr-cleanup.sh`:

- [ ] `git status` mostra working tree clean
- [ ] Todas as mudanças importantes foram commitadas
- [ ] PR foi merged com sucesso
- [ ] Não há trabalho não salvo em outras branches

---

## 🔗 Scripts Relacionados

- **`scripts/git/post-pr-cleanup.sh`** - Limpeza automática pós-merge
- **`scripts/git/direct-push-main.sh`** - Push direto para main (emergências)
- **`scripts/git/smart_git_sync.py`** - Sincronização inteligente de branches

---

## 📚 Referências

- [Git Workflow Guide](GIT_SYNC_GUIDE.md)
- [Post-PR Merge Protocol](POST_PR_MERGE_PROTOCOL.md)
- [Protected Branch Workflow](PROTECTED_BRANCH_WORKFLOW.md)

---

**Última Atualização:** 04 de Janeiro de 2026
**Próxima Revisão:** Trimestral
