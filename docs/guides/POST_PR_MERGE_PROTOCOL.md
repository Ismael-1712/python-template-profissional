---
id: post-pr-merge-protocol
type: guide
status: active
version: 1.0.0
author: SRE Team
date: '2025-12-15'
context_tags: [git, workflow, devops, automation]
linked_code:
  - scripts/cli/git_sync.py
title: Protocolo Pós Pull Request Merge
---

# Protocolo Pós Pull Request Merge

> Procedimento padrão para sincronização após Squash & Merge no GitHub

## 📋 Visão Geral

Este documento define o **protocolo padrão** para sincronizar o repositório local após a aprovação e merge de um Pull Request no GitHub. O objetivo é manter o repositório limpo, organizado e sincronizado.

## 🎯 Quando Usar

Execute este protocolo **imediatamente após**:
- ✅ Pull Request aprovado e mergeado (Squash & Merge)
- ✅ Branch de feature não mais necessária
- ✅ Necessidade de atualizar branches de desenvolvimento

## 🔄 Protocolo Padrão (5 Passos)

### Passo 1: Sincronizar Branch Principal

```bash
# Voltar para a main
git checkout main

# Atualizar com o remote (contém o squash merge)
git pull origin main
```

**Resultado Esperado:**
```
Updating abc1234..def5678
Fast-forward
 20 files changed, 618 insertions(+), 58 deletions(-)
```

---

### Passo 2: Deletar Branch de Feature

```bash
# Deletar branch local
git branch -d feat/NOME-DA-FEATURE

# Deletar branch remota (se ainda existir)
git push origin --delete feat/NOME-DA-FEATURE
```

**Notas:**
- O GitHub já deleta automaticamente a branch remota no Squash & Merge
- Se você receber `error: remote ref does not exist`, está **OK** ✅
- Use `-D` (maiúsculo) apenas se realmente quiser forçar a deleção

**Resultado Esperado:**
```
Deleted branch feat/NOME-DA-FEATURE (was abc1234).
error: unable to delete 'feat/NOME-DA-FEATURE': remote ref does not exist
```

---

### Passo 3: Atualizar Branches de Desenvolvimento

Se você mantém branches de longa duração (`cli`, `api`, `dev`), sincronize-as:

```bash
# Atualizar branch CLI
git checkout cli
git pull origin cli  # Sincroniza com a versão remota atualizada

# Atualizar branch API
git checkout api
git pull origin api  # Sincroniza com a versão remota atualizada

# Voltar para main
git checkout main
```

**Estratégias de Merge:**

#### Opção A: Fast-Forward (Preferencial)
```bash
git checkout cli
git merge main --ff-only
```

#### Opção B: Rebase (Se houver divergências)
```bash
git checkout cli
git rebase main
```

⚠️ **ATENÇÃO**: Se houver conflitos no rebase, aborte e use `git pull`:
```bash
git rebase --abort
git pull origin cli  # Sincroniza com o remote
```

---

### Passo 4: Limpar Graph do Git

Execute garbage collection e remova referências obsoletas:

```bash
# Limpar refs remotas deletadas
git fetch --prune

# Garbage collection agressivo
git gc --aggressive --prune=now
```

**O que isso faz:**
- `--prune`: Remove objetos não alcançáveis
- `--aggressive`: Otimização mais profunda (mais lento)
- `now`: Remove imediatamente (em vez de esperar 2 semanas)

**Resultado Esperado:**
```
Enumerating objects: 3769, done.
Counting objects: 100% (3769/3769), done.
Compressing objects: 100% (3503/3503), done.
Total 3769 (delta 2501), reused 71 (delta 0)
```

---

### Passo 5: Validar Estado do Repositório

```bash
# Verificar que não há branches obsoletas locais
git branch -vv | grep ': gone]'

# Verificar branches remotas ativas
git branch -r

# Confirmar estado limpo
git status
```

**Resultado Esperado:**
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

---

## 🚀 Script de Automação (One-Liner)

Para automatizar todo o processo:

```bash
#!/bin/bash
# post-pr-cleanup.sh
# Uso: ./post-pr-cleanup.sh feat/P010-vector-bridge

BRANCH_NAME=$1

# 1. Sincronizar main
git checkout main && git pull origin main

# 2. Deletar branch local
git branch -d "$BRANCH_NAME"

# 3. Tentar deletar remota (ignora erro se não existir)
git push origin --delete "$BRANCH_NAME" 2>/dev/null || true

# 4. Atualizar branches de desenvolvimento
for branch in cli api; do
    git checkout "$branch" && git pull origin "$branch"
done

# 5. Limpar graph
git checkout main
git fetch --prune
git gc --aggressive --prune=now

# 6. Validar
echo "✅ Limpeza concluída!"
git status
```

Salve como `scripts/post-pr-cleanup.sh` e execute:

```bash
chmod +x scripts/post-pr-cleanup.sh
./scripts/post-pr-cleanup.sh feat/P010-vector-bridge
```

---

## 🛡️ Integração com Git Sync

Se você já usa o **Smart Git Sync**, considere adicionar um subcomando:

```bash
# Futuro comando proposto
git-sync cleanup --branch feat/NOME-DA-FEATURE
```

Isso executaria automaticamente todo o protocolo de limpeza.

---

## 📊 Checklist de Validação

Após executar o protocolo, verifique:

- [ ] Branch `main` atualizada com o squash merge
- [ ] Branch de feature deletada localmente
- [ ] Branches `cli` e `api` atualizadas
- [ ] `git fetch --prune` executado
- [ ] `git gc` finalizado sem erros
- [ ] `git status` mostra working tree clean
- [ ] Nenhuma branch obsoleta em `git branch -vv`

---

## ⚠️ Troubleshooting

### Problema: "Your branch is behind..."

**Solução:**
```bash
git pull origin NOME-DA-BRANCH
```

### Problema: Conflitos no rebase

**Solução:**
```bash
git rebase --abort
git pull origin BRANCH-ATUAL  # Sincroniza com remote
```

### Problema: Branch local não deleta

**Solução:**
```bash
# Forçar deleção (use com cuidado!)
git branch -D NOME-DA-BRANCH
```

### Problema: Refs remotas ainda aparecem após prune

**Solução:**
```bash
git remote prune origin
git fetch --prune --prune-tags
```

---

## 📚 Referências

- [Smart Git Sync Guide](./SMART_GIT_SYNC_GUIDE.md)
- [Git Best Practices](../architecture/GIT_WORKFLOW.md)
- [GitHub Squash Merge Documentation](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges#squash-and-merge-your-commits)

---

## 🔄 Versionamento

| Versão | Data       | Autor    | Mudanças                              |
|--------|------------|----------|---------------------------------------|
| 1.0.0  | 2025-12-15 | SRE Team | Versão inicial do protocolo padrão   |

---

**Mantenha este documento atualizado conforme o workflow evoluir.**
