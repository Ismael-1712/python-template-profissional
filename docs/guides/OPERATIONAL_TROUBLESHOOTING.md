---
id: operational-troubleshooting
type: guide
status: active
version: 1.0.0
author: SRE Engineering Team
date: '2025-12-16'
tags: [troubleshooting, debugging, known-issues, workarounds]
context_tags: [operational-knowledge, best-practices]
linked_code:
  - scripts/cli/git_sync.py
  - scripts/cli/audit.py
  - scripts/utils/atomic.py
title: 'Guia de Troubleshooting Operacional - Armadilhas Conhecidas e Soluções'
---

# Guia de Troubleshooting Operacional - Armadilhas Conhecidas e Soluções

## Propósito

Este guia consolida **armadilhas operacionais conhecidas**, **bugs documentados** e **workarounds validados** descobertos durante a evolução do projeto. Use este documento como **primeiro recurso de diagnóstico** quando encontrar comportamentos inesperados.

> **Filosofia SRE:** "Um erro documentado é um erro resolvido pela próxima geração."

---

## 🚨 CATEGORIA 1: Conflitos de Merge na Arquitetura Tríade

### 🔴 Problema #1: Perda de Delta em `git reset --hard`

**Sintoma:**

- Você executa `git reset --hard main` na branch `cli` ou `api`
- A aplicação desaparece (`src/main.py` volta ao estado vazio ou inexistente)
- O `pyproject.toml` perde dependências como `typer` ou `fastapi`

**Causa Raiz:**
A Arquitetura Tríade funciona por **herança com personalidade** (Main + Delta). O comando `reset --hard` **sobrescreve** o Delta, transformando a branch produto em clone da `main`.

**Diagnóstico:**

```bash
# Verificar se você tem Delta em risco
git diff --name-status main...HEAD

# Saída esperada em branches produto (cli/api):
# M    pyproject.toml
# M    src/main.py
# A    Dockerfile  (apenas API)
```

**Solução (Prevenção):**

```bash
# ❌ NUNCA FAÇA ISSO em branches cli/api:
git reset --hard main
git reset --hard origin/main

# ✅ Use sincronização segura:
git merge main  # Resolve conflitos manualmente
# OU
git-sync        # Usa o script validado
```

**Solução (Recuperação se já aconteceu):**

```bash
# 1. Encontrar o commit anterior (antes do reset)
git reflog

# Saída exemplo:
# abc1234 HEAD@{1}: reset: moving to main  ← Erro aconteceu aqui
# def5678 HEAD@{2}: commit: feat: add API endpoint  ← Estado bom

# 2. Criar branch de resgate
git checkout -b recovery-branch def5678

# 3. Cherry-pick os arquivos de Delta
git checkout cli  # Voltar para branch corrompida
git checkout recovery-branch -- src/main.py pyproject.toml

# 4. Commit a recuperação
git add src/main.py pyproject.toml
git commit -m "fix: restore product Delta after accidental reset"
```

**Referências:**

- [ARCHITECTURE_TRIAD.md](../architecture/ARCHITECTURE_TRIAD.md#regra-nº-1-o-respeito-ao-delta)
- [TRIAD_SYNC_LESSONS_LEARNED.md](TRIAD_SYNC_LESSONS_LEARNED.md)

---

### 🟡 Problema #2: Conflitos em `pyproject.toml` Durante Merge

**Sintoma:**

```bash
git merge main
# Auto-merging pyproject.toml
# CONFLICT (content): Merge conflict in pyproject.toml
```

**Causa Raiz:**
O `pyproject.toml` contém:

- **Base (Main):** Ferramentas de desenvolvimento (`ruff`, `mypy`, `pytest`)
- **Delta (Produto):** Dependências de runtime (`fastapi`, `typer`)

Quando a `main` atualiza uma ferramenta de dev E a branch produto adiciona uma dependência de runtime, o Git não sabe como unir.

**Solução (Resolução Manual):**

```toml
# ❌ ERRADO: Aceitar "theirs" (perde o Delta)
git checkout --theirs pyproject.toml

# ❌ ERRADO: Aceitar "ours" (perde atualizações da Main)
git checkout --ours pyproject.toml

# ✅ CORRETO: Fusão Aditiva Manual
# Abra o arquivo e mescle ambas as seções

[project]
dependencies = [
    # Deps da Main (Dev Tools)
    "ruff>=0.8.4",
    "mypy>=1.14.0",
    # Deps do Delta (Produto)
    "fastapi>=0.115.6",  # ← Adicione do Delta
    "typer[all]>=0.15.1" # ← Se for branch CLI
]
```

**Automação (Git-Sync):**
O comando `git-sync` tem lógica específica para detectar e alertar sobre conflitos em `pyproject.toml`. Use-o preferencialmente para propagação de mudanças.

```bash
git-sync --source main --target cli
# ⚠️  Conflict detected in pyproject.toml
# Please resolve manually preserving both Main tools AND Product deps
```

---

## 🚨 CATEGORIA 2: Problemas de Cache e CI

### 🟡 Problema #3: Dependência Removida Ainda Aparece no CI

**Sintoma:**

- Você remove `deprecated-package` do `requirements/dev.txt`
- Localmente funciona (`make install-dev` passa)
- No CI (GitHub Actions), o pacote ainda é importado e usado

**Causa Raiz:**
O GitHub Actions usa cache de `pip` baseado em hash de `requirements/*.txt`. Se você apenas **remove** uma linha sem modificar outras, o **hash pode não mudar** suficientemente para invalidar o cache.

**Diagnóstico:**

```yaml
# .github/workflows/ci.yml
- name: Cache Python dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements/*.txt') }}
    #                             ↑ Cache key baseado em hash
```

**Solução (Forçar Invalidação):**

```bash
# Adicione um comentário com timestamp em requirements/dev.txt
echo "# Cache-bust: $(date +%s)" >> requirements/dev.txt
git add requirements/dev.txt
git commit -m "chore: bust CI cache after dependency removal"
```

**Solução (Limpeza Manual no CI):**
No GitHub Actions, adicione step de limpeza antes de instalar:

```yaml
- name: Clear pip cache (manual)
  run: |
    rm -rf ~/.cache/pip
    pip cache purge
```

**Referência:**

- [ADR_002_PRE_COMMIT_OPTIMIZATION.md](../architecture/ADR_002_PRE_COMMIT_OPTIMIZATION.md)

---

## 🚨 CATEGORIA 3: Bugs Conhecidos e Workarounds

### 🟢 Bug #1: Conflito de Nome `git-sync` vs Pacote Sistema

**Status:** ⚠️ DÉBITO TÉCNICO ACEITO (Resolução: v3.0.0)

**Sintoma:**

- Em sistemas Linux com pacote `git-extras` instalado, o comando `git-sync` pode invocar o binário do sistema ao invés do script do projeto
- Comportamento: Sincronização falha silenciosamente ou executa operação errada

**Causa Raiz:**
O pacote `git-extras` (comum em Debian/Ubuntu) instala `/usr/bin/git-sync`, que tem precedência sobre scripts locais em `PATH`.

**Diagnóstico:**

```bash
# Verificar qual git-sync está sendo usado
which git-sync
# Se retornar /usr/bin/git-sync → Conflito confirmado

# Verificar se é o script do projeto
git-sync --version
# Saída esperada do projeto:
# GIT-SYNC v2.0.0 - Smart Branch Synchronization
```

**Workaround (Temporário):**

```bash
# Usar caminho explícito
python3 scripts/cli/git_sync.py --source main --target cli

# OU via Makefile (preferido)
make sync-to-cli
```

**Resolução Planejada:**

- **Versão:** v3.0.0 (Roadmap Sprint 6)
- **Ação:** Renomear comando para `dev-sync` para evitar colisão
- **Motivo da Postergação:** Compatibilidade com documentação e scripts existentes

**Referência:**

- Issue interna: "Rename git-sync to dev-sync for namespace safety"

---

### 🟢 Bug #2: `TypeError` em `CORTEX Audit` com Campo `source_file`

**Status:** 🛠️ EM CORREÇÃO (Sprint 5)

**Sintoma:**

```bash
cortex audit
# TypeError: __init__() missing 1 required positional argument: 'source_file'
```

**Causa Raiz:**
Durante a refatoração do módulo Guardian (Sprint 5 - Fase 1), adicionamos o campo `source_file` ao modelo `ConfigFinding` em `scripts/core/guardian/models.py`. Nem todos os pontos de instanciação em `scripts/core/cortex/scanner.py` foram atualizados.

**Código Problemático:**

```python
# scripts/core/cortex/scanner.py (ANTIGO)
finding = ConfigFinding(
    config_type="env_var",
    name=var_name,
    file_path=str(file_path),
    line_number=node.lineno,
    # ❌ Falta: source_file=str(file_path)
)
```

**Workaround:**

```bash
# Evitar usar cortex audit temporariamente
# Usar validação manual de links
cortex map  # Funciona normalmente
```

**Correção (Em desenvolvimento):**

```python
# scripts/core/cortex/scanner.py (CORRIGIDO - Sprint 5)
finding = ConfigFinding(
    config_type="env_var",
    name=var_name,
    file_path=str(file_path),
    source_file=str(file_path),  # ✅ Adicionado
    line_number=node.lineno,
)
```

**Referência:**

- [VISIBILITY_GUARDIAN_DESIGN.md](../architecture/VISIBILITY_GUARDIAN_DESIGN.md)
- PR pendente: "fix(cortex): add missing source_file to all ConfigFinding instantiations"

---

## 🚨 CATEGORIA 4: Alertas de Segurança (Prioridade Máxima)

### 🔴 Alerta #1: Propagação de Tokens em Subprocessos

**Status:** ⚠️ RISCO LATENTE (Correção: Sprint 5 - Prioridade 1)

**Descrição:**
O módulo `scripts/audit/plugins.py` executa subprocessos (ex: `subprocess.run(['git', 'status'])`) que herdam **TODAS** as variáveis de ambiente do processo pai, incluindo tokens sensíveis como `GITHUB_TOKEN`.

**Código Vulnerável:**

```python
# scripts/audit/plugins.py (EXEMPLO VULNERÁVEL)
def run_git_command(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        # ❌ PROBLEMA: env não está filtrado
        # Processo filho recebe GITHUB_TOKEN, CI_TOKEN, etc.
    )
    return result.stdout
```

**Vetor de Ataque:**

- Plugin malicioso ou comprometido pode exfiltrar tokens via subprocesso
- Logs de debug podem vazar variáveis de ambiente

**Solução (Implementação Pendente):**

```python
# scripts/audit/plugins.py (SEGURO)
import os

SAFE_ENV_VARS = {
    "PATH", "HOME", "USER", "LANG", "PWD"
}

def sanitize_env() -> dict[str, str]:
    """Return environment with sensitive vars removed."""
    return {
        k: v for k, v in os.environ.items()
        if k in SAFE_ENV_VARS or not k.endswith("_TOKEN")
    }

def run_git_command(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=sanitize_env(),  # ✅ Ambiente filtrado
    )
    return result.stdout
```

**Ação Imediata:**
Até a correção ser implementada, **NÃO USE** plugins de auditoria em ambientes com tokens críticos (produção, CI com permissões de escrita).

**Referência:**

- [SECURITY.md](../../SECURITY.md)
- Ticket: "P-SEC-01: Implement subprocess environment sanitization in audit plugins"

---

## 🛠️ CATEGORIA 5: Ferramentas de Diagnóstico

### Verificação Rápida de Saúde do Projeto

```bash
# 1. Estado do Git (detectar conflitos, arquivos órfãos)
git status --short

# 2. Saúde do ambiente Python
dev-doctor

# 3. Validade da documentação
cortex map && cortex audit

# 4. Qualidade de código
make validate  # Roda ruff, mypy, pytest

# 5. Logs de CI (última execução)
gh run view --log  # Requer GitHub CLI
```

### Limpeza de Estado Corrompido

```bash
# Limpar caches e reconstruir ambiente
rm -rf .mypy_cache .pytest_cache __pycache__
rm -rf .venv  # ⚠️ CUIDADO: Remove ambiente virtual
make install-dev  # Recria do zero

# Resetar Git para estado limpo (APENAS se tiver backup)
git clean -fdx  # Remove TODOS os arquivos não rastreados
git reset --hard origin/$(git branch --show-current)
```

---

## 📚 Referências Cruzadas

### Documentação Arquitetural

- [ARCHITECTURE_TRIAD.md](../architecture/ARCHITECTURE_TRIAD.md) - Fundamentos da Tríade
- [VISIBILITY_GUARDIAN_DESIGN.md](../architecture/VISIBILITY_GUARDIAN_DESIGN.md) - Sistema Guardian
- [SRE_TECHNICAL_DEBT_CATALOG.md](../history/SRE_TECHNICAL_DEBT_CATALOG.md) - Catálogo de Débitos

### Guias Operacionais

- [TRIAD_SYNC_LESSONS_LEARNED.md](TRIAD_SYNC_LESSONS_LEARNED.md) - Lições de sincronização
- [PROTECTED_BRANCH_WORKFLOW.md](PROTECTED_BRANCH_WORKFLOW.md) - Workflow de proteção
- [SMART_GIT_SYNC_GUIDE.md](SMART_GIT_SYNC_GUIDE.md) - Guia do git-sync

### Ferramentas

- [scripts/cli/doctor.py](../../scripts/cli/doctor.py) - Diagnóstico de ambiente
- [scripts/cli/git_sync.py](../../scripts/cli/git_sync.py) - Sincronização de branches
- [scripts/cli/cortex.py](../../scripts/cli/cortex.py) - Sistema de introspecção

---

## 🤝 Contribuindo com Novas Descobertas

Se você encontrar uma nova armadilha operacional:

1. **Documente imediatamente:**

   ```bash
   # Adicione à seção apropriada deste arquivo
   # Inclua: Sintoma, Causa Raiz, Diagnóstico, Solução
   ```

2. **Crie um teste de regressão:**

   ```bash
   # Adicione teste em tests/ que previna o problema no futuro
   ```

3. **Atualize o CORTEX:**

   ```bash
   cortex map  # Regenera contexto com novo conhecimento
   ```

4. **Commit atômico:**

   ```bash
   git add docs/guides/OPERATIONAL_TROUBLESHOOTING.md
   git commit -m "docs(ops): add troubleshooting for [PROBLEMA]"
   ```

---

**Última Atualização:** 2025-12-16
**Manutenedores:** SRE Engineering Team
**Status:** Documento Vivo (Atualizado continuamente)
