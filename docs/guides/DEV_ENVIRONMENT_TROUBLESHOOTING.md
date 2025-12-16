---
id: development-environment-troubleshooting
type: guide
status: active
version: 1.0.0
author: SRE Team
date: '2025-12-16'
tags: [troubleshooting, environment, pre-commit, hooks]
context_tags: [dx, developer-experience, debugging]
linked_code:
  - scripts/cli/doctor.py
title: 'Troubleshooting de Ambiente de Desenvolvimento - Problemas Comuns e Soluções'
---

# Troubleshooting de Ambiente de Desenvolvimento

## Status

**Active** - Baseado em problemas reais diagnosticados durante Sprint 4 (Nov 2025)

## Contexto

Este documento concentra **conhecimento tácito** adquirido durante o desenvolvimento: problemas que não estão nas documentações oficiais das ferramentas, mas que surgem em ambientes reais e causam atrasos significativos.

---

## 1. Armadilha do "Hook Obsoleto" (Stale Hook)

### Sintoma

Mesmo após corrigir o `.pre-commit-config.yaml`, os commits continuam falhando com erros como:

```bash
$ git commit -m "fix: update config"
[ERROR] File scripts/old_file.py não encontrado
[ERROR] pre-commit hook failed!
```

**O arquivo `scripts/old_file.py` foi deletado há semanas, mas o hook continua procurando por ele.**

### Causa Raiz

O **`pre-commit` não se atualiza automaticamente** quando você edita `.pre-commit-config.yaml`.

**Como funciona o pre-commit:**

1. Ao rodar `pre-commit install`, ele cria um binário em `.git/hooks/pre-commit`
2. Este binário **copia** a configuração de `.pre-commit-config.yaml` para um cache interno
3. Edições subsequentes no `.yaml` **não** afetam o binário já instalado

**Analogia:** É como editar o código-fonte de um programa mas continuar executando a versão compilada antiga.

### Diagnóstico

Verifique quando o hook foi instalado pela última vez:

```bash
# Verifica a data de modificação do hook
ls -lh .git/hooks/pre-commit
# -rwxr-xr-x  1 user  staff   478B Nov  5 14:23 .git/hooks/pre-commit
#                                    ^^^^^^^^^^^ <- Data de instalação
```

Se esta data é **anterior** à última edição do `.pre-commit-config.yaml`, você está com hook obsoleto.

### Solução Obrigatória

**Force a reinstalação do hook:**

```bash
pre-commit install -f
```

O flag `-f` (force) sobrescreve o binário existente.

**Validação:**

```bash
# Teste o hook manualmente (sem fazer commit)
pre-commit run --all-files

# Se passar, tente o commit novamente
git commit -m "test: verify hook update"
```

### Prevenção

**Sempre** que modificar `.pre-commit-config.yaml`:

```bash
# Workflow recomendado
vim .pre-commit-config.yaml  # Editar configuração
pre-commit install -f        # ⚠️  OBRIGATÓRIO: Forçar reinstalação
pre-commit run --all-files   # Testar antes de commitar
git add .pre-commit-config.yaml
git commit -m "ci: update pre-commit hooks"
```

### Caso Real (Interações 26-28 - Sprint 4)

**Timeline:**

- **26 Nov:** Deletamos `scripts/lint_fix.py` (script obsoleto)
- **26 Nov:** Removemos referência no `.pre-commit-config.yaml`
- **26 Nov:** Tentamos commit → **FALHA** (hook procurando arquivo deletado)
- **26 Nov:** Diagnosticamos: `.git/hooks/pre-commit` datava de 15 Nov
- **26 Nov:** Rodamos `pre-commit install -f` → **SUCESSO**

**Tempo perdido:** 2 horas de debugging.

**Lição:** Este problema é **invisível** (não há mensagem de erro clara indicando "hook desatualizado").

---

## 2. Paradoxo "Inception" do Auditor

### Sintoma

Ao tentar commitar correções na própria ferramenta de auditoria (`code_audit.py`), ela **bloqueia o próprio commit**:

```bash
$ git commit -m "fix: update code_audit to ignore comments"
Running code audit...
[ERROR] scripts/code_audit.py:145: Detected shell=True (SECURITY RISK)
[ERROR] Audit failed! Aborting commit.
```

**O problema:** A linha 145 está dentro de um **comentário** ou **docstring** explicando os riscos do `shell=True`, mas a ferramenta detecta mesmo assim.

### Causa Raiz

A ferramenta `code_audit.py` (versões < v2.0) usa **regex simples** para detectar padrões perigosos:

```python
# Exemplo de detecção problemática (ANTES)
def detect_shell_risk(file_content: str) -> list[int]:
    pattern = r'shell\s*=\s*True'
    matches = re.finditer(pattern, file_content)
    return [match.start() for match in matches]
```

**O problema:** Regex não entende contexto de código Python. Ela detecta `shell=True` em:

- ✅ Código executável (correto detectar)
- ❌ Comentários (`# Never use shell=True`)
- ❌ Docstrings (`"""Avoid shell=True"""`)
- ❌ Strings literais (`error_msg = "shell=True is dangerous"`)

### Solução Emergencial (Curto Prazo)

**Opção 1: Usar supressão explícita (`# noqa`)**

```python
# code_audit.py
result = subprocess.run(cmd, shell=True)  # noqa: subprocess
```

O `code_audit.py` (v1.5+) respeita a convenção `# noqa: <regra>`.

**Opção 2: Bypass temporário do hook**

```bash
# ⚠️  USE COM CUIDADO (apenas para commits que CORRIGEM o auditor)
git commit -m "fix: code_audit false positives" --no-verify
```

### Solução Definitiva (Longo Prazo)

**Substituir detecção por Regex por Análise AST (Abstract Syntax Tree):**

```python
# Exemplo de detecção correta (DEPOIS - Planejado para P12)
import ast

def detect_shell_risk_ast(file_path: str) -> list[int]:
    """Detect shell=True only in EXECUTABLE code (not comments/strings)."""
    with open(file_path) as f:
        tree = ast.parse(f.read())

    risks = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                    if keyword.value.value is True:
                        risks.append(node.lineno)
    return risks
```

**Vantagens:**

- ✅ Ignora comentários/docstrings automaticamente
- ✅ Detecta apenas código executável
- ✅ Mais confiável (usa o parser oficial do Python)

**Status:** Planejado para **Tarefa P12** (Refatoração de `code_audit.py`) no Roadmap v2.2.

### Caso Real (Interação 61 - Sprint 4)

**Contexto:** Durante a implementação de supressões `# noqa`, o próprio commit de melhoria do `code_audit.py` foi bloqueado por falso positivo.

**Solução Aplicada:** Commit manual com `--no-verify` (justificado em code review).

---

## 3. Contaminação de Estado em Repositórios Legados

### Sintoma

Você faz um commit pontual (ex: "fix typo in README"), mas ao rodar `git status` vê:

```bash
$ git status
On branch main
Changes not staged for commit:
  modified:   scripts/old_script.py
  modified:   tests/broken_test.py
  modified:   src/legacy_module.py
  ...
  (7 arquivos modificados não relacionados)
```

**Perigo:** Se você usar `git add .`, todos esses arquivos (possivelmente com erros) serão incluídos no commit.

### Causa Raiz

Em repositórios com histórico longo ou mesclagens recentes, arquivos podem ficar "sujos" no working tree por:

- Merges mal resolvidos
- Stashes aplicados parcialmente
- Edições acidentais de ferramentas (IDEs, formatters rodando em background)

### Solução (Protocolo de Commit Atômico)

**❌ NUNCA use `git add .` em repositórios legados.**

**✅ Use staging explícito:**

```bash
# 1. Identifique o que VOCÊ modificou intencionalmente
git diff --name-only

# 2. Adicione APENAS esses arquivos
git add README.md  # Apenas o arquivo que você quis modificar

# 3. Verifique o que será commitado
git diff --cached

# 4. Commit
git commit -m "docs: fix typo in README"
```

### Limpeza (Remover Arquivos Sujos)

Se os arquivos modificados são lixo acidental:

```bash
# ⚠️  CUIDADO: Isso descarta mudanças não-commitadas
git restore scripts/old_script.py tests/broken_test.py

# Ou, para restaurar TUDO (extremo):
git restore .
```

### Prevenção (`.gitignore` Proativo)

Adicione padrões de arquivos que nunca devem ser commitados:

```bash
# .gitignore (exemplo)
*.log
*.json  # Relatórios de auditoria
__pycache__/
.venv/
.mypy_cache/
.ruff_cache/
audit_report_*.json
sync_report_*.json
```

**Status:** Tarefa **P10** (Higiene do `.gitignore`) está no Roadmap v2.2.

### Caso Real (Interação 60 - Sprint 4)

**Contexto:** Durante refatoração de `ci_failure_recovery.py`:

- Intenção: Commitar apenas `scripts/ci_recovery/models.py` + `ci_failure_recovery.py`
- Acidente: `git add .` arrastou **7 arquivos** com 153 erros de lint acumulados
- Resultado: CI falhou no PR, atrasando o merge em 3 horas

**Solução:** Revertemos o commit (`git reset HEAD~1`), limpamos o working tree, e adicionamos arquivos manualmente.

---

## 4. Dependências Ausentes Após Clone Fresco

### Sintoma

Você clona o repositório, instala dependências, mas ao rodar testes:

```bash
$ make test
ModuleNotFoundError: No module named 'typer'
```

**Mas o `requirements/dev.txt` lista `typer`!**

### Causa Raiz

O ambiente virtual (`.venv`) pode estar:

1. Corrompido (instalação interrompida)
2. Apontando para Python version errado
3. Usando cache pip desatualizado

### Solução (Reconstrução Limpa)

```bash
# 1. Deletar ambiente virtual completamente
rm -rf .venv

# 2. Limpar caches Python
rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache

# 3. Reinstalar do zero
make install-dev

# 4. Validar instalação
make doctor  # Executa diagnóstico do ambiente
```

### Validação Manual

```bash
# Confirme que o Python correto está sendo usado
which python
# Saída esperada: /path/to/repo/.venv/bin/python

# Teste import direto
python -c "import typer; print(typer.__version__)"
# Saída esperada: 0.x.x (não deve dar erro)
```

### Automação (Makefile)

O projeto já possui target `make clean-all` para isso:

```bash
make clean-all  # Remove .venv e todos os artefatos
make setup      # Recria ambiente do zero
```

---

## 5. Conflitos de Formatação (Ruff vs Ruff-Format)

### Sintoma

O CI falha com:

```bash
[ERROR] Ruff format check failed:
  File src/main.py would be reformatted
```

**Mas você rodou `make format` localmente e passou!**

### Causa Raiz

Versões diferentes de `ruff` entre local e CI (ou configurações diferentes em `pyproject.toml`).

### Solução

**1. Sincronize versões:**

```bash
# Confirme a versão local
ruff --version
# ruff 0.1.9

# Compare com requirements/dev.txt
grep ruff requirements/dev.txt
# ruff==0.1.8  # ⚠️  Versão diferente!
```

**2. Force reinstalação:**

```bash
make clean-all
make install-dev
```

**3. Rode formatação + validação:**

```bash
make format
git diff  # Se houver mudanças, faça commit
```

### Prevenção

**Pin exato de versões no `requirements/dev.in`:**

```ini
# requirements/dev.in
ruff==0.1.9  # ← Versão exata (não ~= ou >=)
mypy==1.7.0
```

Depois compile:

```bash
pip-compile requirements/dev.in
```

---

## Checklist de Troubleshooting Geral

Quando algo quebrar sem motivo aparente:

```markdown
- [ ] **1. Hook obsoleto:** `pre-commit install -f`
- [ ] **2. Ambiente sujo:** `make clean-all && make setup`
- [ ] **3. Git working tree:** `git status` (verificar arquivos não-intencionais)
- [ ] **4. Versões sincronizadas:** `pip list | grep ruff` (local) vs `requirements/dev.txt`
- [ ] **5. Cache corrompido:** `rm -rf .venv __pycache__ .pytest_cache`
- [ ] **6. Diagnóstico automatizado:** `make doctor`
```

---

## Referências

- **Ferramenta de Diagnóstico:** [`scripts/cli/doctor.py`](../../scripts/cli/doctor.py)
- **Configuração de Hooks:** [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml)
- **Roadmap:** [Tarefas P10-P12](../architecture/ROADMAP_DELTA_AUDIT.md) planejam melhorias nas ferramentas de auditoria

---

## Contribuindo

Se você encontrar um novo problema de ambiente:

1. Documente o sintoma, causa e solução neste arquivo
2. Considere adicionar um check automatizado no `make doctor`
3. Abra PR com tag `[dx-improvement]`
