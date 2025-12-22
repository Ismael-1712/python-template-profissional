# Guia de Sincronização Git

Este documento contém os comandos e scripts para manter seu repositório sincronizado.

## 📦 Arquivos Alterados Enviados

✅ **Commit realizado**: `936bd16`
✅ **Push para origin/main**: Concluído com sucesso

### Alterações enviadas

- Reorganização do Cortex com orquestrador centralizado
- Remoção do CLI duplicado (`scripts/cli/cortex.py`)
- Atualização dos hooks do pre-commit
- Novos arquivos de documentação de PR

---

## 🔄 Scripts de Sincronização Criados

### 1. Sincronização Completa (Recomendado)

```bash
./scripts/git/sync-all-branches.sh
```

Este script executa automaticamente:

1. ✓ Atualiza o repositório local (`git fetch --all`)
2. ✓ Atualiza a branch `main`
3. ✓ Atualiza as branches `cli` e `api` com merge da `main`
4. ✓ Faz push de todas as alterações

---

### 2. Scripts Individuais

#### Atualizar Repositório Local

```bash
./scripts/git/update-local.sh
```

- Executa `git fetch --all --prune --tags`
- Sincroniza todas as referências remotas

#### Atualizar Branch Main

```bash
./scripts/git/update-main.sh
```

- Muda para a branch `main`
- Executa `git pull origin main`
- Retorna para a branch original

#### Atualizar Branches de Trabalho

```bash
./scripts/git/update-branches.sh
```

- Atualiza `main` primeiro
- Para cada branch (`cli`, `api`):
  - Faz pull do remoto
  - Faz merge da `main`
  - Faz push das alterações

---

## 📋 Comandos Git Diretos

### Atualizar Repositório Local

```bash
# Sincronizar todas as referências remotas
git fetch --all --prune --tags

# Ver status de todas as branches
git branch -vv
```

### Atualizar Main

```bash
# Mudar para main e atualizar
git checkout main
git pull origin main

# Ver commits recentes
git log --oneline -5
```

### Atualizar Branches CLI e API

#### Branch CLI

```bash
# Atualizar branch cli
git checkout cli
git pull origin cli
git merge main --no-edit
git push origin cli
```

#### Branch API

```bash
# Atualizar branch api
git checkout api
git pull origin api
git merge main --no-edit
git push origin api
```

#### Atualizar Ambas (Loop)

```bash
for branch in cli api; do
    git checkout $branch
    git pull origin $branch
    git merge main --no-edit
    git push origin $branch
done

# Voltar para main
git checkout main
```

---

## 🚀 Fluxo de Trabalho Recomendado

### Início do Dia

```bash
# Sincronizar tudo
./scripts/git/sync-all-branches.sh
```

### Antes de Começar uma Feature

```bash
# Atualizar repositório local
git fetch --all

# Criar branch de feature a partir da main atualizada
git checkout main
git pull origin main
git checkout -b feature/minha-feature
```

### Após Fazer Alterações

```bash
# Adicionar e commitar
git add .
git commit -m "feat: descrição da mudança"

# Atualizar com a main antes de push
git fetch origin main
git merge origin/main

# Enviar para remoto
git push origin feature/minha-feature
```

### Após Merge de PR

```bash
# Sincronizar todas as branches
./scripts/git/sync-all-branches.sh

# Ou manualmente:
git checkout main
git pull origin main

git checkout cli
git merge main
git push origin cli

git checkout api
git merge main
git push origin api
```

---

## ⚙️ Configurações Úteis

### Aliases Git Úteis

Adicione ao seu `~/.gitconfig`:

```ini
[alias]
    # Sincronização rápida
    sync = !git fetch --all --prune && git pull

    # Status mais bonito
    st = status -sb

    # Log mais legível
    lg = log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit

    # Ver branches com último commit
    br = branch -vv

    # Atualizar branch atual com main
    update = !git fetch origin main && git merge origin/main
```

Uso:

```bash
git sync    # Sincronizar branch atual
git st      # Status resumido
git lg      # Log bonito
git br      # Ver branches
git update  # Atualizar branch atual com main
```

---

## 🔍 Troubleshooting

### Conflitos ao Fazer Merge

```bash
# Listar arquivos em conflito
git status

# Após resolver conflitos:
git add .
git merge --continue

# Ou abortar o merge:
git merge --abort
```

### Branch Desatualizada

```bash
# Forçar atualização (CUIDADO!)
git fetch origin
git reset --hard origin/main  # Para main
git reset --hard origin/cli   # Para cli
git reset --hard origin/api   # Para api
```

### Ver Diferenças

```bash
# Ver diferença entre local e remoto
git diff main origin/main

# Ver commits não sincronizados
git log origin/main..main     # Commits locais não enviados
git log main..origin/main     # Commits remotos não baixados
```

---

## 📊 Status Atual

### Verificar Estado

```bash
# Ver estado de todas as branches
git fetch --all
git branch -vv

# Ver último commit de cada branch
git show-branch main cli api

# Ver diferenças entre branches
git log --oneline --graph --all -10
```

### Informações das Branches

| Branch | Propósito | Upstream |
|--------|-----------|----------|
| `main` | Branch principal | `origin/main` |
| `cli` | Desenvolvimento CLI | `origin/cli` |
| `api` | Desenvolvimento API | `origin/api` |

---

## 📝 Notas Importantes

1. **Sempre sincronize antes de começar a trabalhar**: Use `./scripts/git/sync-all-branches.sh`

2. **Commits pequenos e frequentes**: Melhor fazer vários commits pequenos do que um grande

3. **Mensagens de commit descritivas**: Use [conventional commits](https://www.conventionalcommits.org/):
   - `feat:` para novas features
   - `fix:` para correções
   - `docs:` para documentação
   - `refactor:` para refatoração
   - `test:` para testes

4. **Pull antes de push**: Sempre atualize sua branch antes de enviar

5. **Use os scripts**: Eles já têm toda a lógica de sincronização e tratamento de erros

---

## 🎯 Próximos Passos

1. Execute a sincronização completa:

   ```bash
   ./scripts/git/sync-all-branches.sh
   ```

2. Verifique o estado:

   ```bash
   git branch -vv
   git log --oneline --graph --all -10
   ```

3. Configure os aliases recomendados no seu `.gitconfig`

4. Adicione este guia aos favoritos para referência rápida
