---
id: git-automation-scripts-guide
type: guide
status: active
version: 1.0.0
author: SRE Team
date: '2025-12-15'
context_tags: [git, automation, scripts, workflow]
linked_code: []
title: Guia de Scripts de Automação Git
---

# 🚀 Guia de Scripts de Automação Git

> Ferramentas para automatizar workflows Git repetitivos

## 📋 Visão Geral

Este projeto inclui **dois scripts de automação** que implementam os protocolos Git documentados, eliminando tarefas manuais repetitivas e reduzindo erros humanos.

### Scripts Disponíveis

| Script | Propósito | Protocolo Base |
|--------|-----------|----------------|
| `post-pr-cleanup.sh` | Limpeza após PR merge | [POST_PR_MERGE_PROTOCOL.md](./POST_PR_MERGE_PROTOCOL.md) |
| `direct-push-main.sh` | Push direto na main | [DIRECT_PUSH_PROTOCOL.md](./DIRECT_PUSH_PROTOCOL.md) |

---

## 🔧 Instalação e Configuração

### Verificar Permissões

Os scripts já vêm com permissões de execução configuradas:

```bash
ls -lh scripts/*.sh
```

**Resultado esperado:**
```
-rwxr-xr-x 1 user user 3.5K Dec 15 20:15 scripts/post-pr-cleanup.sh
-rwxr-xr-x 1 user user 3.3K Dec 15 20:16 scripts/direct-push-main.sh
```

### Se Necessário, Configure Permissões

```bash
chmod +x scripts/post-pr-cleanup.sh
chmod +x scripts/direct-push-main.sh
```

---

## 📘 Script 1: post-pr-cleanup.sh

### Descrição

Automatiza a limpeza do repositório após um Pull Request ser aprovado e mergeado (Squash & Merge).

### Quando Usar

✅ **Use quando:**
- PR foi aprovado e mergeado no GitHub
- Branch de feature não é mais necessária
- Precisa sincronizar branches de desenvolvimento

### Sintaxe

```bash
./scripts/post-pr-cleanup.sh <branch-name>
```

### Parâmetros

| Parâmetro | Obrigatório | Descrição | Exemplo |
|-----------|-------------|-----------|---------|
| `branch-name` | ✅ Sim | Nome completo da branch mergeada | `feat/P010-vector-bridge` |

### Exemplo de Uso

```bash
# Após PR #169 ser mergeado
./scripts/post-pr-cleanup.sh feat/P010-vector-bridge
```

### O Que o Script Faz

1. **📥 Sincroniza main** com origin/main
2. **🗑️ Deleta branch local** (feat/P010-vector-bridge)
3. **🌐 Tenta deletar branch remota** (se ainda existir)
4. **🔄 Atualiza branches de desenvolvimento** (cli, api)
5. **🧹 Limpa Git graph** (fetch --prune + gc --aggressive)

### Saída Esperada

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Post-PR Cleanup Protocol v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Branch: feat/P010-vector-bridge
Timestamp: 2025-12-15 19:35:13

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 Step 1/5: Syncing main with origin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Updating dd51c96..7ea3338
Fast-forward
 20 files changed, 618 insertions(+), 58 deletions(-)
✅ Main branch updated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗑️  Step 2/5: Deleting local branch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Local branch 'feat/P010-vector-bridge' deleted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 Step 3/5: Deleting remote branch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  WARNING: Remote branch does not exist (already deleted by GitHub)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Step 4/5: Updating development branches
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → Updating cli...
✅ Branch 'cli' updated
  → Updating api...
✅ Branch 'api' updated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧹 Step 5/5: Cleaning Git graph
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → Pruning remote refs...
  → Running garbage collection...
✅ Git graph cleaned

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current branch: main
Status:
✅ Working tree clean

Recent commits:
7ea3338 feat(core): Neural Interface & Vector Bridge Implementation
dd51c96 chore(deps): Bump python-semantic-release

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 Cleanup completed successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Tratamento de Erros

| Erro | Causa | Solução |
|------|-------|---------|
| `Branch name required` | Não passou nome da branch | Execute: `./scripts/post-pr-cleanup.sh <branch>` |
| `Failed to checkout main` | Conflitos não resolvidos | Resolva conflitos manualmente |
| `Could not delete local branch` | Branch tem mudanças não mergeadas | Use `git branch -D <branch>` para forçar |

---

## 📗 Script 2: direct-push-main.sh

### Descrição

Automatiza o workflow completo de push direto na branch main, incluindo validação, sincronização e limpeza.

### Quando Usar

✅ **Use quando:**
- Fez commits diretos na main (sem PR)
- Precisa validar antes de push
- Quer garantir sincronização pós-push

### Sintaxe

```bash
./scripts/direct-push-main.sh
```

### Parâmetros

❌ **Nenhum parâmetro necessário**

O script detecta automaticamente a branch atual.

### Pré-Requisitos

1. ✅ Estar na branch `main`
2. ✅ Ter commits pendentes para push
3. ✅ Ambiente de desenvolvimento configurado

### Exemplo de Uso

```bash
# Após fazer commit local na main
git add docs/guide/NEW_GUIDE.md
git commit -m "docs: Adiciona novo guia"

# Execute o script
./scripts/direct-push-main.sh
```

### O Que o Script Faz

1. **🔍 Valida código** (make validate: ruff + mypy + pytest + doctor)
2. **📤 Push para origin/main**
3. **🔄 Sincroniza local com remote** (git pull)
4. **🧹 Limpa Git graph** (fetch --prune + gc --auto)

### Saída Esperada

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Direct Push to Main Protocol v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Timestamp: 2025-12-15 20:18:22

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Step 1/4: Validating changes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Running quality checks...

PYTHONPATH=. .venv/bin/python -m ruff check .
All checks passed!
Success: no issues found in 130 source files
✅ Validação completa concluída
✅ All validations passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 Step 2/4: Pushing to origin/main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pushing commits to remote...

To github.com:USER/REPO.git
   271f2f4..687e1d9  main -> main
✅ Successfully pushed to origin/main

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Step 3/4: Syncing local with remote
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pulling latest changes from origin/main...

Already up to date.
✅ Local repository synchronized

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧹 Step 4/4: Cleaning Git graph
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → Pruning remote refs...
  → Running garbage collection (auto)...
✅ Git graph cleaned

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Final Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Branch: main
Status:
✅ Working tree clean

Recent commits:
687e1d9 (HEAD -> main, origin/main) feat(scripts): Adiciona scripts
271f2f4 docs(guide): Corrige formatação do protocolo
5d6a759 docs(guide): Adiciona protocolo para push direto

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 Direct push completed successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️  What was done:
  ✓ Code validated (ruff, mypy, pytest)
  ✓ Changes pushed to origin/main
  ✓ Local repository synchronized
  ✓ Git graph cleaned
```

### Tratamento de Erros

| Erro | Causa | Solução |
|------|-------|---------|
| `Not on main branch` | Executou em outra branch | `git checkout main` |
| `Validation failed` | Código não passou nos checks | Corrija erros reportados pelo `make validate` |
| `Failed to push` | Conflitos ou permissões | Verifique conflitos ou permissões no GitHub |
| `Pull failed` | Conflitos após push | Resolva conflitos com `git pull --rebase` |

---

## 🎯 Fluxos de Trabalho Recomendados

### Workflow 1: Desenvolvimento com Pull Request

```bash
# 1. Criar branch de feature
git checkout -b feat/nova-funcionalidade

# 2. Desenvolver e commitar
git add .
git commit -m "feat: implementa nova funcionalidade"

# 3. Push e criar PR no GitHub
git push origin feat/nova-funcionalidade

# 4. Após aprovação e merge no GitHub
./scripts/post-pr-cleanup.sh feat/nova-funcionalidade
```

### Workflow 2: Correções Diretas na Main

```bash
# 1. Fazer mudanças
git add docs/guide/correcao.md
git commit -m "docs: corrige typo no guia"

# 2. Usar script automatizado
./scripts/direct-push-main.sh
```

---

## 🔍 Troubleshooting

### Problema: Script não executa

**Sintomas:**
```bash
bash: ./scripts/direct-push-main.sh: Permission denied
```

**Solução:**
```bash
chmod +x scripts/direct-push-main.sh
chmod +x scripts/post-pr-cleanup.sh
```

---

### Problema: Validação falha no direct-push-main.sh

**Sintomas:**
```
❌ ERROR: Validation failed. Fix errors and try again.
```

**Solução:**
```bash
# Ver detalhes dos erros
make validate

# Corrigir erros reportados
# Commitar correções
git add .
git commit --amend  # ou novo commit

# Executar novamente
./scripts/direct-push-main.sh
```

---

### Problema: Branch não deleta no post-pr-cleanup.sh

**Sintomas:**
```
⚠️  WARNING: Could not delete local branch
```

**Soluções:**

**Opção 1: Forçar deleção**
```bash
git branch -D feat/branch-name
```

**Opção 2: Verificar se branch está mergeada**
```bash
git branch --merged main
```

---

### Problema: Conflitos após pull

**Sintomas:**
```
❌ ERROR: Pull failed. There might be conflicts.
```

**Solução:**
```bash
# Verificar conflitos
git status

# Resolver conflitos manualmente
# Editar arquivos conflitantes

# Marcar como resolvido
git add .
git commit

# Continuar
git pull origin main
```

---

## 📊 Comparação: Manual vs Automatizado

### Pós-PR Cleanup

| Tarefa | Manual | Com Script | Economia |
|--------|--------|------------|----------|
| Comandos | 12+ | 1 | 92% |
| Tempo | ~3-5 min | ~30 seg | 83% |
| Erros típicos | 15-20% | <1% | 95% |

### Push Direto na Main

| Tarefa | Manual | Com Script | Economia |
|--------|--------|------------|----------|
| Comandos | 6+ | 1 | 83% |
| Tempo | ~2-3 min | ~30 seg | 75% |
| Validação | Opcional | Obrigatória | - |

---

## ✅ Boas Práticas

### ✓ Faça:

- Execute os scripts do diretório raiz do projeto
- Revise a saída do script para detectar warnings
- Use `post-pr-cleanup.sh` imediatamente após merge
- Confie na validação automática do `direct-push-main.sh`

### ✗ Evite:

- Modificar os scripts sem testar
- Ignorar warnings do script
- Executar em branches erradas
- Pular validações manuais antes de usar os scripts

---

## 🚀 Exemplos Práticos

### Exemplo 1: Ciclo Completo de Feature

```bash
# Dia 1: Desenvolver feature
git checkout -b feat/search-optimization
# ... desenvolver ...
git add .
git commit -m "feat: otimiza busca com cache"
git push origin feat/search-optimization

# GitHub: Criar PR, passar CI, obter aprovação, Squash & Merge

# Dia 2: Limpar após merge
./scripts/post-pr-cleanup.sh feat/search-optimization
```

**Resultado:**
```
✅ Main atualizada com feature
✅ Branch local deletada
✅ Branches cli e api sincronizadas
✅ Graph limpo
```

---

### Exemplo 2: Hotfix Urgente

```bash
# Identificar bug crítico em produção
git checkout main
git add src/fix/critical_bug.py
git commit -m "fix: corrige vazamento de memória crítico"

# Push automatizado com validação
./scripts/direct-push-main.sh
```

**Resultado:**
```
✅ Código validado (ruff, mypy, pytest)
✅ Push para main realizado
✅ Local sincronizado
✅ Graph limpo
```

---

## 📚 Referências

- [POST_PR_MERGE_PROTOCOL.md](./POST_PR_MERGE_PROTOCOL.md) - Protocolo manual
- [DIRECT_PUSH_PROTOCOL.md](./DIRECT_PUSH_PROTOCOL.md) - Protocolo manual
- [Smart Git Sync Guide](./SMART_GIT_SYNC_GUIDE.md) - Sistema de sincronização avançado

---

## 🔄 Versionamento

| Versão | Data       | Autor    | Mudanças                              |
|--------|------------|----------|---------------------------------------|
| 1.0.0  | 2025-12-15 | SRE Team | Versão inicial com 2 scripts          |

---

## 💡 Dicas Avançadas

### Criar Aliases no Shell

Adicione ao seu `.bashrc` ou `.zshrc`:

```bash
# Aliases Git Automation
alias pr-cleanup='./scripts/post-pr-cleanup.sh'
alias push-main='./scripts/direct-push-main.sh'
```

**Uso:**
```bash
pr-cleanup feat/my-branch
push-main
```

---

### Integração com VS Code Tasks

Adicione ao `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Git: Direct Push Main",
      "type": "shell",
      "command": "./scripts/direct-push-main.sh",
      "group": "build",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

---

**Aproveite a automação e foque no que importa: escrever código de qualidade!** 🚀
