---
id: direct-push-protocol
type: guide
status: active
version: 1.0.0
author: SRE Team
date: '2025-12-15'
context_tags: [git, workflow, devops, main-branch]
linked_code:
  - scripts/cli/git_sync.py
title: Protocolo para Push Direto na Main
---

# Protocolo para Push Direto na Main

> Procedimento padrão para commits diretos na branch principal

## ⚠️ Quando Usar

Este protocolo aplica-se quando você faz **commits diretos na branch `main`** (sem Pull Request), típico para:

- 📝 Correções de documentação menores
- 🐛 Hotfixes críticos em produção
- 🔧 Ajustes de configuração
- ✨ Pequenas melhorias que não requerem review

## 🚨 Pré-Requisitos

Antes de fazer push direto na main:

1. ✅ Branch `main` está protegida mas você tem permissões de bypass
2. ✅ Mudanças são pequenas e de baixo risco
3. ✅ Todos os testes locais passaram (`make validate`)
4. ✅ Pre-commit hooks executaram com sucesso

## 🔄 Protocolo Padrão (4 Passos)

### Passo 1: Validar Mudanças Localmente

```bash
# Verificar estado do repositório
git status

# Validar qualidade do código
make validate

# Verificar pre-commit hooks
git add <arquivos>
git commit -m "sua mensagem"  # Pre-commit rodará automaticamente
```

**Resultado Esperado:**

```
check for added large files..............................................Passed
ruff format..............................................................Passed
mypy.....................................................................Passed
✓ Todos os hooks passaram
```

---

### Passo 2: Push para Origin Main

```bash
# Enviar para repositório remoto
git push origin main
```

**Resultado Esperado:**

```
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Writing objects: 100% (5/5), 643 bytes | 643.00 KiB/s, done.
To github.com:USER/REPO.git
   abc1234..def5678  main -> main
```

⚠️ **Nota**: Se a branch main estiver protegida, você verá:

```
remote: Bypassed rule violations for refs/heads/main:
remote: - Cannot update this protected ref.
```

Isso é **ESPERADO** se você tem permissões de bypass.

---

### Passo 3: Sincronizar Local com Remote

**CRÍTICO**: Após o push, **SEMPRE** sincronize seu repositório local:

```bash
# Garantir que local está em sincronia com remote
git pull origin main
```

**Por quê?**

- GitHub pode ter executado Actions/CI que criaram commits
- Outros desenvolvedores podem ter feito push simultaneamente
- Mantém histórico local consistente com remote

**Resultado Esperado:**

```
Already up to date.
```

OU (se houver novos commits do CI):

```
Updating abc1234..def5678
Fast-forward
 .github/workflows/deploy.yml | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

---

### Passo 4: Limpar Graph do Git

```bash
# Remover referências obsoletas
git fetch --prune

# Garbage collection automático
git gc --auto
```

**O que isso faz:**

- `--prune`: Remove refs remotas deletadas
- `--auto`: GC apenas se necessário (heurística do Git)

**Resultado Esperado:**

```
From github.com:USER/REPO
   abc1234..def5678  api        -> origin/api
   xyz9876..uvw4321  cli        -> origin/cli
```

---

## 🔁 Fluxo Completo (One-Liner)

```bash
# Validar → Push → Sync → Clean
make validate && \
git push origin main && \
git pull origin main && \
git fetch --prune && \
git gc --auto
```

---

## 🚀 Script de Automação

Salve como `scripts/direct-push-main.sh`:

```bash
#!/bin/bash
# scripts/direct-push-main.sh
# Protocolo automatizado para push direto na main

set -e  # Exit on error

echo "📋 Passo 1: Validando mudanças..."
make validate

echo ""
echo "📤 Passo 2: Enviando para origin/main..."
git push origin main

echo ""
echo "🔄 Passo 3: Sincronizando local com remote..."
git pull origin main

echo ""
echo "🧹 Passo 4: Limpando graph..."
git fetch --prune
git gc --auto

echo ""
echo "✅ Push direto concluído com sucesso!"
echo ""
git status
git log --oneline -3
```

**Uso:**

```bash
chmod +x scripts/direct-push-main.sh

# Após fazer commit localmente
./scripts/direct-push-main.sh
```

---

## 📊 Checklist de Validação

Após executar o protocolo, verifique:

- [ ] `git push origin main` executado com sucesso
- [ ] `git pull origin main` retornou "Already up to date" ou fast-forward
- [ ] `git fetch --prune` removeu refs obsoletas
- [ ] `git status` mostra "Your branch is up to date with 'origin/main'"
- [ ] `git log` mostra seu commit no histórico
- [ ] Nenhum arquivo unstaged ou untracked pendente

---

## ⚠️ Diferenças vs Post-PR Merge

| Aspecto                  | Push Direto                  | Pós-PR Merge                          |
|--------------------------|------------------------------|---------------------------------------|
| **Origem das mudanças**  | Commit local                 | Squash merge do GitHub                |
| **Branch cleanup**       | Não necessário               | Deletar branch de feature             |
| **Sincronização**        | `git pull` obrigatório       | `git pull` + atualizar outras branches|
| **Validação**            | `make validate` antes        | Já validado pelo CI do PR             |
| **Garbage collection**   | `git gc --auto` (leve)       | `git gc --aggressive` (completo)      |

---

## 🛡️ Troubleshooting

### Problema: "protected branch cannot be updated"

**Causa:** Você não tem permissões de bypass.

**Solução:**

1. Crie uma branch de feature
2. Abra um Pull Request
3. Siga o [Post-PR Merge Protocol](./POST_PR_MERGE_PROTOCOL.md)

---

### Problema: "Your branch is behind 'origin/main'"

**Causa:** Alguém fez push enquanto você commitava.

**Solução:**

```bash
git pull --rebase origin main
git push origin main
```

---

### Problema: Conflitos no pull após push

**Causa:** GitHub Actions criou commits conflitantes.

**Solução:**

```bash
git fetch origin
git reset --hard origin/main  # ⚠️ PERDE mudanças locais!
```

OU (preservar mudanças):

```bash
git stash
git pull origin main
git stash pop
# Resolver conflitos manualmente
```

---

## 🔗 Integração com Smart Git Sync

Se você usa o **Smart Git Sync**, considere adicionar um subcomando:

```bash
# Futuro comando proposto
git-sync push --branch main --sync-after
```

Isso executaria automaticamente:

1. Validação com auditoria preventiva
2. Push para main
3. Sincronização local
4. Limpeza de graph

---

## 📚 Referências

- [Post-PR Merge Protocol](./POST_PR_MERGE_PROTOCOL.md)
- [Smart Git Sync Guide](./SMART_GIT_SYNC_GUIDE.md)
- [Git Protected Branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

---

## 🎯 Boas Práticas

### ✅ Faça

- Sempre execute `make validate` antes do push
- Sincronize imediatamente após push (`git pull`)
- Use mensagens de commit semânticas (feat:, fix:, docs:, etc.)
- Execute `git fetch --prune` regularmente

### ❌ Evite

- Push direto de features grandes (use PR)
- Ignorar falhas nos pre-commit hooks
- Esquecer de sincronizar após push
- Fazer push sem testes locais

---

## 🔄 Versionamento

| Versão | Data       | Autor    | Mudanças                           |
|--------|------------|----------|------------------------------------|
| 1.0.0  | 2025-12-15 | SRE Team | Versão inicial do protocolo        |

---

**Use este protocolo sempre que fizer commits diretos na main!**
