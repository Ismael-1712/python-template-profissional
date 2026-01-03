---
id: cortex-auto-hooks
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 2025-12-01
context_tags: [cortex, git-hooks, automation, introspection]
linked_code:
  - scripts/cortex/cli.py
---

# CORTEX Auto-Hooks: Contexto Sempre Atualizado

## Visão Geral

O sistema de **Auto-Hooks do CORTEX** automatiza a regeneração do mapa de contexto do projeto sempre que houver mudanças no repositório Git. Isso garante que o contexto da IA (`.cortex/context.json`) permaneça sempre fresco e atualizado.

## Motivação

### Problema

Durante o desenvolvimento, o contexto do projeto muda frequentemente:

- Novos comandos CLI são adicionados
- Documentação é criada ou atualizada
- Dependências são modificadas
- A estrutura de arquivos evolui

Se o mapa de contexto não for atualizado, a IA pode:

- Não conhecer novos comandos disponíveis
- Referenciar documentação desatualizada
- Ter uma visão incorreta da arquitetura
- Fazer suposições erradas sobre o estado do projeto

### Solução

Os **Git Hooks** regeneram automaticamente o contexto após:

- `git pull` / `git merge` (hook: `post-merge`)
- `git checkout` / troca de branch (hook: `post-checkout`)
- `git rebase` / `git commit --amend` (hook: `post-rewrite`)

## Instalação

### Comando

```bash
cortex setup-hooks
```

### Saída Esperada

```
🔧 Installing Git hooks for CORTEX...

✅ Git hooks installed successfully!

📋 Installed hooks:
  • post-merge           - Runs after git pull/merge
  • post-checkout        - Runs after git checkout (branch switch)
  • post-rewrite         - Runs after git rebase/commit --amend

🎉 Context map will now auto-regenerate after Git operations!

💡 Test it: git checkout - (to switch back and forth)
```

## Como Funciona

### 1. Criação dos Hooks

O comando `cortex setup-hooks` cria três arquivos em `.git/hooks/`:

```
.git/hooks/
├── post-merge      (executável)
├── post-checkout   (executável)
└── post-rewrite    (executável)
```

### 2. Conteúdo do Hook

Cada hook contém um script bash robusto e portável:

```bash
#!/bin/bash
# Auto-generated CORTEX post-checkout hook
# Maintains AI context fresh after Git operations
# WSL-compatible: Uses Python module instead of PATH-dependent 'cortex' command

# Locate repository root dynamically
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

# Locate Python interpreter in virtual environment
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"

# Execute CORTEX command if venv exists
if [ -f "$VENV_PYTHON" ]; then
    cd "$REPO_ROOT" || exit 0
    "$VENV_PYTHON" -m scripts.cortex.cli map --output .cortex/context.json >/dev/null 2>&1 || true
fi

exit 0
```

**🔧 Melhorias de Robustez (v0.1.0+):**

- ✅ **WSL-Compatible**: Não depende de `cortex` no PATH
- ✅ **Portável**: Localiza raiz do repositório dinamicamente via `git rev-parse`
- ✅ **Ambiente Virtual**: Usa Python do `.venv` diretamente (não requer ativação manual)
- ✅ **Módulo Python**: Executa `python -m scripts.cortex.cli` (não depende de entry points)
- ✅ **Silencioso**: Redireciona saída para evitar poluir terminal Git
- ✅ **Graceful Failure**: Sempre retorna código 0 (não bloqueia operações Git)

### 3. Execução Automática

Após cada operação Git relevante, o hook executa silenciosamente em segundo plano:

```
$ git checkout feature-branch
Switched to branch 'feature-branch'
# Hook executa automaticamente sem output (modo silencioso)
```

Para verificar se o hook está funcionando, você pode temporariamente remover o redirecionamento `>/dev/null 2>&1` do hook e observar a saída.

## Robustez e Segurança

### Detecção Dinâmica do Ambiente

O hook detecta automaticamente o ambiente Python correto:

```bash
# Localiza raiz do repositório (funciona em subdiretórios)
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

# Localiza Python do venv sem depender de PATH
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
```

Isso garante que:

- ✅ Funciona em **WSL** (Windows Subsystem for Linux)
- ✅ Funciona em **shells não-interativos** (onde `.bashrc` não é carregado)
- ✅ Funciona **sem `pip install -e .`** (não depende de entry points)
- ✅ Funciona em **subdiretórios** do repositório
- ✅ Funciona em **ambientes CI/CD** com venvs isolados

### Validação de Pré-Condições

Antes de executar, o hook valida que o ambiente virtual existe:

```bash
if [ -f "$VENV_PYTHON" ]; then
    # Executa apenas se venv estiver configurado
    "$VENV_PYTHON" -m scripts.cortex.cli map --output .cortex/context.json
fi
```

Isso garante que:

- Não falha se `.venv` não existir
- Não bloqueia operações Git em ambientes sem Python configurado
- Funciona em repositórios clonados recentemente (antes de setup)

### Backup de Hooks Existentes

Se você já tiver hooks personalizados:

```
📦 Backing up existing post-merge to post-merge.backup
```

O comando preserva seus hooks existentes com a extensão `.backup`.

### Permissões Corretas

Os hooks são criados com permissão de execução:

```bash
chmod +x .git/hooks/post-merge
chmod +x .git/hooks/post-checkout
chmod +x .git/hooks/post-rewrite
```

## Casos de Uso

### 1. Trabalho Multi-Branch

```bash
# Trabalhando em feature-branch
$ git checkout feature-branch
🔄 Regenerating CORTEX context map...
✅ Context map updated successfully!

# Voltando para main
$ git checkout main
🔄 Regenerating CORTEX context map...
✅ Context map updated successfully!
```

### 2. Sincronização com Remoto

```bash
$ git pull origin main
Updating abc123..def456
Fast-forward
 scripts/cli/new_command.py | 50 ++++++++++++++++++++
🔄 Regenerating CORTEX context map...
✅ Context map updated successfully!
```

### 3. Rebase/Amend

```bash
$ git rebase main
Successfully rebased and updated refs/heads/feature-branch.
🔄 Regenerating CORTEX context map...
✅ Context map updated successfully!
```

## Troubleshooting

### Hook Não Está Executando

**Problema**: Hook não é executado após operações Git.

**Verificações**:

1. **Permissões**:

   ```bash
   ls -la .git/hooks/post-*
   # Deve mostrar: -rwxr-xr-x (executável)
   ```

2. **Ambiente Virtual Configurado**:

   ```bash
   ls -la .venv/bin/python
   # Deve retornar: .venv/bin/python (symlink ou executável)
   ```

3. **Hook existe**:

   ```bash
   cat .git/hooks/post-merge
   # Deve mostrar o script do hook com git rev-parse e python -m
   ```

**Solução**:

```bash
cortex setup-hooks  # Reinstalar hooks com versão atualizada
```

### Erro de Permissão

**Problema**: `Permission denied: .git/hooks/post-merge`

**Solução**:

```bash
chmod +x .git/hooks/post-*
```

### Ambiente Virtual Não Encontrado

**Problema**: Hook não executa (sem erro visível, modo silencioso).

**Causa**: O arquivo `.venv/bin/python` não existe (venv não criado ou caminho incorreto).

**Verificação**:

```bash
# Teste manual do hook
bash .git/hooks/post-checkout
# Se nada acontecer, verifique o venv
```

**Solução**:

```bash
# Criar ambiente virtual
python3 -m venv .venv

# Instalar dependências
.venv/bin/pip install -e ".[dev]"

# Reinstalar hooks
.venv/bin/python -m scripts.cortex.cli setup-hooks
```

### Migração de Hooks Antigos (Versão < 0.1.0)

**Problema**: Hooks antigos ainda exibem warning `'cortex' command not found` em WSL.

**Causa**: Hooks foram gerados por versão anterior que dependia de `cortex` no PATH.

**Solução - Atualizar Hooks**:

```bash
# Reinstalar hooks com versão atualizada
.venv/bin/python -m scripts.cortex.cli setup-hooks

# Verificar conteúdo atualizado
cat .git/hooks/post-checkout | grep "git rev-parse"
# Deve retornar: REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
```

## Desinstalação

Para remover os hooks:

```bash
rm .git/hooks/post-merge
rm .git/hooks/post-checkout
rm .git/hooks/post-rewrite
```

Para restaurar hooks backupeados:

```bash
mv .git/hooks/post-merge.backup .git/hooks/post-merge
mv .git/hooks/post-checkout.backup .git/hooks/post-checkout
mv .git/hooks/post-rewrite.backup .git/hooks/post-rewrite
```

## Considerações de Performance

### Impacto

A regeneração do contexto é rápida (< 1 segundo para projetos médios), mas pode adicionar latência perceptível em repositórios grandes.

### Quando Não Usar

- **Repositórios enormes**: Se `cortex map` demora muito
- **CI/CD pipelines**: Hooks Git geralmente não são necessários em ambientes automatizados
- **Ambientes compartilhados**: Onde múltiplos usuários não controlam o CLI

### Otimização

Para projetos grandes, considere:

```bash
# Hook condicional - só regenera se arquivos relevantes mudaram
if git diff-tree --name-only -r HEAD | grep -E '(scripts|docs|pyproject.toml)'; then
    cortex map --output .cortex/context.json
fi
```

## Integração com CI/CD

### GitHub Actions

```yaml
name: Update Context
on: [push, pull_request]
jobs:
  update-context:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -e .
      - name: Generate context
        run: cortex map
      - name: Commit context
        run: |
          git config user.name "GitHub Action"
          git config user.email "action@github.com"
          git add .cortex/context.json
          git commit -m "chore: update context map" || true
          git push
```

### GitLab CI

```yaml
update-context:
  script:
    - pip install -e .
    - cortex map
    - git add .cortex/context.json
    - git commit -m "chore: update context map" || true
    - git push
```

## Princípios de Design

### 1. Fail-Safe

Os hooks **nunca bloqueiam** operações Git, mesmo se `cortex` falhar:

```bash
exit 0  # Always exit successfully
```

### 2. Informativo

Feedback claro sobre o que está acontecendo:

```
🔄 Regenerating CORTEX context map...
✅ Context map updated successfully!
```

### 3. Não-Intrusivo

- Não modifica hooks existentes sem backup
- Pode ser facilmente desinstalado
- Funciona silenciosamente quando não há contexto

## Próximos Passos

- [ ] Adicionar hook condicional baseado em `git diff`
- [ ] Suportar configuração de hooks customizados
- [ ] Integração com `husky` para projetos Node.js
- [ ] Hook para `pre-commit` que valida contexto antes de commit

## Referências

- [Git Hooks Documentation](https://git-scm.com/docs/githooks)
- [CORTEX Introspection System](./CORTEX_INTROSPECTION_SYSTEM.md)
- [Comandos CLI do CORTEX](../reference/cortex.md)

## Conclusão

Os **CORTEX Auto-Hooks** eliminam o trabalho manual de manter o contexto atualizado, garantindo que a IA sempre tenha acesso às informações mais recentes sobre o projeto.

Com uma única instalação (`cortex setup-hooks`), o sistema passa a funcionar de forma transparente e automática, tornando a experiência de desenvolvimento mais fluida e confiável.
