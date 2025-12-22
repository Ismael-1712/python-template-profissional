---
id: atomic-commit-protocol
type: guide
status: active
version: 1.0.0
author: SRE Team
date: '2025-12-16'
tags: [git, best-practice, workflow, safety]
context_tags: [version-control, reliability, governance]
linked_code:
  - scripts/cortex/cli.py
title: 'Protocolo de Commit Atômico - Segurança e Rastreabilidade em Git'
---

# Protocolo de Commit Atômico - Segurança e Rastreabilidade em Git

## Status

**Active** - Metodologia obrigatória desde Sprint 4 (Nov 2025)

## Contexto e Motivação

### O Problema: "Contaminação de Estado" em Commits

Durante operações de refatoração e manutenção, a equipe enfrentou um padrão recorrente de **commits contaminados**:

**Caso Real (Interação 60 - Sprint 4):**

```bash
# Intenção: Commitar refatoração de ci_failure_recovery.py
$ git add .
$ git commit -m "refactor: extract models module"

# Resultado real:
[main abc1234] refactor: extract models module
 9 files changed, 234 insertions(+), 89 deletions(-)
 #     ^^^^^^^ ← Deveria ser 2 arquivos!
```

**Arquivos commitados:**

- ✅ `scripts/ci_recovery/models.py` (intencional)
- ✅ `ci_failure_recovery.py` (intencional)
- ❌ `scripts/old_audit.py` (153 erros de lint)
- ❌ `tests/broken_test.py` (teste falhando)
- ❌ `src/legacy_api.py` (código descontinuado)
- ❌ `audit_report_2025.json` (artefato temporário)
- ❌ `sync_log.json` (artefato temporário)
- ❌ `debug_output.txt` (lixo de debug)

**Consequências:**

- ⚠️  CI falhou no PR (erros de lint dos arquivos contaminados)
- ⚠️  Histórico Git poluído (commit sem relação clara com mensagem)
- ⚠️  Code review dificultado (reviewer precisa separar mudanças intencionais de lixo)
- ⚠️  Rollback impossível (reverteria mudanças legítimas + lixo)

**Tempo perdido:** 3 horas de debugging + rebuild do PR.

---

## Princípios Fundamentais

### 1. Atomicidade

> **"Um commit deve representar UMA mudança lógica coerente e reversível."**

**Bons exemplos:**

- ✅ "fix: correct typo in README.md" (1 arquivo)
- ✅ "feat: add user authentication" (auth.py + tests/test_auth.py + config)
- ✅ "refactor: extract data models" (models.py + original_file.py - relacionados)

**Maus exemplos:**

- ❌ "update stuff" (12 arquivos não relacionados)
- ❌ "fix: typo + add feature + refactor" (3 mudanças diferentes)

### 2. Rastreabilidade

Cada commit deve permitir responder:

- **O quê mudou?** (arquivos específicos)
- **Por quê mudou?** (mensagem de commit)
- **Como reverter?** (`git revert <commit>` deve ser seguro)

### 3. Prevenção de Contaminação

**Assuma que o working tree está sempre sujo em repositórios legados.**

---

## O Protocolo (Workflow Obrigatório)

### Passo 1: Identifique Mudanças Intencionais

**Antes de qualquer `git add`, inspecione o estado:**

```bash
# Liste TODOS os arquivos modificados
git status

# Veja o diff completo
git diff --name-only
```

**Exemplo de saída problemática:**

```bash
$ git diff --name-only
README.md                     # ✅ Você editou (intencional)
scripts/audit.py              # ❌ Editado acidentalmente por IDE
tests/test_old.py             # ❌ Merge conflict não resolvido
audit_metrics.json            # ❌ Artefato gerado por script
.venv/lib/python3.11/...      # ❌ Lixo de dependências
```

**Decisão:** Adicionar **apenas** `README.md`.

### Passo 2: Staging Explícito (NUNCA use `git add .`)

**❌ PROIBIDO em repositórios com histórico:**

```bash
git add .  # Adiciona TUDO indiscriminadamente
```

**✅ OBRIGATÓRIO:**

```bash
# Método 1: Adicionar arquivo por arquivo
git add README.md
git add docs/guides/NEW_GUIDE.md

# Método 2: Adicionar diretório específico (se todos os arquivos são intencionais)
git add scripts/new_feature/

# Método 3: Adicionar por padrão (use com cautela)
git add docs/**/*.md
```

### Passo 3: Validação Pré-Commit

**Sempre revise o que SERÁ commitado (não o working tree):**

```bash
# Mostra diff do staging area (o que será commitado)
git diff --cached

# Lista arquivos que serão commitados
git diff --cached --name-only
```

**Validação:**

- ✅ Todos os arquivos listados são intencionais?
- ✅ Nenhum artefato temporário (.json, .log, **pycache**)?
- ✅ Nenhum arquivo de ambiente (.venv, .env)?

**Se encontrar lixo:**

```bash
# Remover arquivo específico do staging
git restore --staged audit_metrics.json

# OU: Resetar staging completamente e recomeçar
git restore --staged .
```

### Passo 4: Commit com Mensagem Semântica

**Formato obrigatório (Conventional Commits):**

```bash
git commit -m "<tipo>(<escopo>): <descrição curta>

<corpo opcional: contexto, motivação, detalhes técnicos>

<rodapé opcional: refs #123, breaking changes>"
```

**Tipos válidos:**

- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `refactor`: Mudança de código sem alterar comportamento
- `docs`: Apenas documentação
- `test`: Adição/modificação de testes
- `chore`: Tarefas de manutenção (build, deps, config)
- `ci`: Mudanças em CI/CD
- `perf`: Melhorias de performance

**Exemplos reais:**

```bash
# ✅ BOM: Específico e reversível
git commit -m "refactor(ci-recovery): extract data models to separate module

- Created scripts/ci_recovery/models.py
- Migrated RecoveryAction and FailureContext dataclasses
- Updated imports in ci_failure_recovery.py
- All existing tests pass"

# ❌ RUIM: Vago e não atômico
git commit -m "update code"
```

### Passo 5: Verificação Pós-Commit (Opcional mas Recomendado)

```bash
# Veja o commit que acabou de criar
git log -1 --stat

# Saída esperada:
# commit abc1234...
# Author: ...
# Date: ...
#
#     refactor(ci-recovery): extract data models
#
#  scripts/ci_recovery/models.py | 45 ++++++++++++++++++
#  ci_failure_recovery.py        | 30 ++----------
#  2 files changed, 50 insertions(+), 25 deletions(-)
#
# ✅ Apenas 2 arquivos (correto!)
```

**Se detectar contaminação:**

```bash
# Desfazer último commit (mantém mudanças no working tree)
git reset HEAD~1

# Recomeçar do Passo 1
```

---

## Limpeza de Working Tree (Higiene)

### Remover Arquivos Não-Intencionais

**Se arquivos foram modificados acidentalmente:**

```bash
# Restaurar arquivo específico para versão do HEAD
git restore scripts/audit.py tests/test_old.py

# OU: Restaurar TODOS os arquivos não-staged
git restore .
```

**⚠️  CUIDADO:** `git restore` descarta mudanças permanentemente.

### Remover Artefatos Temporários

**Deletar arquivos que nunca deveriam estar no working tree:**

```bash
# Manual
rm audit_metrics.json sync_log.json

# Automático (via Makefile)
make clean  # Remove artefatos de build + cache
```

### Prevenir Futuros Artefatos (.gitignore)

**Adicione padrões ao `.gitignore`:**

```bash
# .gitignore
# Artefatos de auditoria
audit_report_*.json
audit_metrics.json
audit_dashboard.html

# Logs de scripts
sync_report_*.json
*.log

# Ambientes Python
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Build artifacts
dist/
build/
*.egg-info/
```

**Validar que .gitignore funciona:**

```bash
# Gere um artefato
python scripts/code_audit.py  # Cria audit_metrics.json

# Confirme que Git ignora
git status
# Saída esperada: audit_metrics.json NÃO deve aparecer
```

---

## Casos Especiais

### Commit de Arquivos Voláteis (Atualizados Automaticamente)

Alguns arquivos são **legitimamente** atualizados por scripts (ex: `audit_metrics.json`, `docs/reference/CLI_COMMANDS.md`).

**Problema:** Eles aparecem no `git status` sempre, tentando você a usar `git add .`.

**Solução 1: Ignorar (se não for crítico para o repositório):**

```bash
# Adicionar ao .gitignore
echo "audit_metrics.json" >> .gitignore
```

**Solução 2: Commit separado e explícito:**

```bash
# Commit funcionalidade principal
git add src/new_feature.py tests/test_new_feature.py
git commit -m "feat: add new feature"

# Commit atualização de métricas SEPARADAMENTE
git add audit_metrics.json
git commit -m "chore: update audit metrics [automated]"
```

**Solução 3: Makefile target (automatiza a Solução 2):**

```makefile
# Makefile (já existe no projeto)
commit-amend:
 @git add -u
 @git add audit_metrics.json docs/reference/CLI_COMMANDS.md 2>/dev/null || true
 @git commit --amend --no-edit
 @echo "✅ Commit amended with volatile files!"
```

Uso:

```bash
# 1. Commit principal
git add src/feature.py
git commit -m "feat: add feature"

# 2. Amend com arquivos voláteis
make commit-amend
```

---

### Refatoração Multi-Arquivo (Como Manter Atomicidade)

**Problema:** Refatorações legítimas podem tocar 10+ arquivos.

**Solução:** Use **commits intermediários** dentro de uma branch feature.

```bash
# Criar branch feature
git checkout -b refactor/audit-tool

# Commit 1: Extrair modelos
git add scripts/audit/models.py code_audit.py
git commit -m "refactor(audit): extract data models"

# Commit 2: Extrair scanner
git add scripts/audit/scanner.py code_audit.py
git commit -m "refactor(audit): extract file scanner"

# Commit 3: Extrair reporter
git add scripts/audit/reporter.py code_audit.py
git commit -m "refactor(audit): extract report generator"

# PR: Todos os 3 commits juntos (mas cada um é atômico e reversível)
git push origin refactor/audit-tool
```

**Vantagem:** Se o Commit 2 introduzir bug, você pode revertê-lo isoladamente sem afetar Commit 1 e 3.

---

## Integração com Ferramentas do Projeto

### Makefile Targets

O projeto já possui targets que seguem o protocolo:

```bash
# Formata código + stage automático (CUIDADO: adiciona tudo com -u)
make save m="feat: add feature"
# ⚠️  Usa git add -u (adiciona apenas arquivos TRACKED modificados)
# ✅ Seguro se você não criou arquivos novos

# Commit inteligente com staging explícito
make commit MSG="feat: add feature"
# Internamente: git add -u (tracked files only)

# Amend com arquivos voláteis
make commit-amend
# Adiciona audit_metrics.json + CLI_COMMANDS.md apenas
```

**Recomendação:** Use `make save` apenas se você tem certeza que não há lixo no working tree.

### Pre-Commit Hooks

O projeto usa `pre-commit` para validar **antes** do commit. Isso ajuda mas não substitui staging explícito.

**O que o pre-commit valida:**

- ✅ Formatação (ruff)
- ✅ Linting (ruff)
- ✅ Type checking (mypy)
- ❌ **NÃO** valida se você adicionou arquivos errados (sua responsabilidade)

---

## Checklist de Commit Seguro

```markdown
Antes de cada commit:

- [ ] **1. Status:** `git status` (vejo todos os arquivos modificados?)
- [ ] **2. Diff:** `git diff --name-only` (quais arquivos mudei?)
- [ ] **3. Staging explícito:** `git add <arquivos>` (NUNCA `git add .`)
- [ ] **4. Revisão:** `git diff --cached --name-only` (confirmo que staging está correto?)
- [ ] **5. Artefatos:** Nenhum .json, .log, __pycache__ no staging?
- [ ] **6. Mensagem:** Segue Conventional Commits (<tipo>(<escopo>): <desc>)?
- [ ] **7. Commit:** `git commit -m "..."`
- [ ] **8. Validação:** `git log -1 --stat` (quantidade de arquivos faz sentido?)
```

---

## Recuperação de Desastres

### Commit Contaminado Já Feito (Não Pushed)

```bash
# Desfazer último commit (mantém mudanças)
git reset HEAD~1

# Limpar lixo do working tree
git restore scripts/lixo.py
rm audit_metrics.json

# Refazer commit corretamente
git add <arquivos_corretos>
git commit -m "mensagem correta"
```

### Commit Contaminado Já Pushed

```bash
# ⚠️  CUIDADO: Reescreve histórico (só faça se ninguém mais fez pull)
git reset HEAD~1
# ... limpar e refazer commit ...
git push --force-with-lease
```

**Se outras pessoas já fizeram pull:** Não reescreva histórico. Crie commit de correção:

```bash
# Reverter arquivos indesejados
git restore --source=HEAD~1 scripts/lixo.py
git add scripts/lixo.py
git commit -m "chore: remove accidentally committed files"
```

---

## Educação de Equipe

### Para Novos Desenvolvedores

**Regra Simplificada:**

> "Nunca use `git add .` neste projeto. Sempre adicione arquivos explicitamente."

### Para LLMs (Agentes de Código)

**Instrução Obrigatória no Prompt:**

```markdown
When committing changes:
1. Use `git add <specific_file>` (NEVER `git add .`)
2. Run `git diff --cached --name-only` before commit
3. Ensure only intentional files are staged
4. Use Conventional Commits format
```

---

## Referências Cruzadas

- **Refatoração:** [REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md](REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md) - Fase 4 exige commits atômicos
- **Troubleshooting:** [DEV_ENVIRONMENT_TROUBLESHOOTING.md](DEV_ENVIRONMENT_TROUBLESHOOTING.md) - Seção 3 (Contaminação de Estado)
- **CI/CD:** [.github/workflows/ci.yml](../../.github/workflows/ci.yml) - Valida commits no PR
- **Makefile:** [Makefile](../../Makefile) - Targets `commit`, `commit-amend`, `save`

---

## Histórico de Revisões

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0.0 | 2025-12-16 | Versão inicial baseada em incident Sprint 4 (Interação 60) |
