---
id: newproject-evolution
type: history
status: archived
version: 1.0.0
author: Engineering Team
date: '2025-12-16'
context_tags: [scaffolding, evolution, bash, automation]
linked_code: []
title: 📜 Evolução do Sistema newproject (v1.2 → v1.5)
---

# 📜 Evolução do Sistema `newproject` (v1.2 → v1.5)

**Período:** Outubro de 2025
**Status:** 🔵 Documento Histórico (Sistema Atual: v1.5)
**Baseado em:** Relatório Técnico de Evolução e Handover (28/10/2025)

---

## 🎯 Objetivo deste Documento

Registrar a **evolução arquitetural** do sistema de scaffolding `newproject`, desde sua forma inicial rudimentar (v1.2) até a solução profissional atual (v1.5). Este documento serve como:

- 📚 **Registro Histórico:** Para futuros desenvolvedores entenderem decisões de design
- 🧠 **Contexto Arquitetural:** Para justificar a arquitetura "Molde + Fábrica" atual
- ⚠️ **Anti-Padrões Identificados:** Para evitar regressão arquitetural

---

## 🕰️ Linha do Tempo

```
Outubro/2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

v1.2 (Início)          v1.3 (Refatoração)    v1.4 (Personalização)    v1.5 (Qualidade)
   │                        │                      │                        │
   │ "Construtora          │ "Fábrica"            │ "Customização"         │ "Controle de Qualidade"
   │  de Cabanas"          │ Introdução           │ Automação de sed       │ Commit automático
   │                        │ git clone            │                        │
   │ mkdir + touch          │                      │                        │
   │                        │                      │                        │
   ▼                        ▼                      ▼                        ▼
[Arquivos vazios]     [Clone completo]      [Personalização]         [Estado limpo]
```

---

## 🏚️ v1.2: "Construtora de Cabanas" (Estado Inicial)

### Implementação

Uma **única função Bash** no `~/.bashrc` que criava estruturas vazias.

```bash
newproject() {
    PROJECT_NAME="$1"
    PROJECT_DIR="$HOME/projects/$PROJECT_NAME"

    # Criar estrutura
    mkdir -p "$PROJECT_DIR/src"
    mkdir -p "$PROJECT_DIR/tests"
    mkdir -p "$PROJECT_DIR/docs"

    # Criar arquivos vazios
    touch "$PROJECT_DIR/pyproject.toml"
    touch "$PROJECT_DIR/README.md"
    touch "$PROJECT_DIR/Dockerfile"
    touch "$PROJECT_DIR/.gitignore"
    touch "$PROJECT_DIR/.editorconfig"

    cd "$PROJECT_DIR"
    code .
}
```

### Problemas Críticos Identificados

| Problema | Impacto | Severidade |
|----------|---------|------------|
| **Arquivos Vazios** | Desenvolvedor precisa preencher manualmente `pyproject.toml`, `Dockerfile`, etc. | 🔴 Crítico |
| **Falta de Padronização** | Cada projeto tem configurações diferentes (Ruff, EditorConfig) | 🔴 Crítico |
| **Manutenção Difícil** | Adicionar novo arquivo requer editar `~/.bashrc` (script longo e frágil) | 🟠 Alto |
| **Sem Versionamento** | Não há conceito de "versão do template" | 🟡 Médio |
| **Sem Git** | Projeto não nasce com repositório Git | 🟡 Médio |
| **Sem Ambiente Virtual** | Desenvolvedor precisa criar `.venv` manualmente | 🟡 Médio |

### Métrica de Dor

- ⏱️ **Tempo para Setup Manual:** ~30-45 minutos
- 🐛 **Taxa de Erros:** ~40% (esquecimento de arquivos, configurações erradas)
- 📝 **Linhas de Código Duplicadas:** ~500 linhas/projeto (copiando de projetos antigos)

---

## 🏗️ v1.3: "Fábrica" (Primeira Refatoração)

### Mudança Arquitetural Chave

**Substituição do `mkdir`/`touch` por `git clone`.**

```bash
newproject() {
    PROJECT_NAME="$1"
    PROJECT_DIR="$HOME/projects/$PROJECT_NAME"
    TEMPLATE_REPO="git@github.com:Ismael-1712/python-template-profissional.git"

    # ⭐ Mudança principal: Clone em vez de mkdir
    git clone "$TEMPLATE_REPO" "$PROJECT_DIR"

    cd "$PROJECT_DIR"

    # Cortar vínculo com o template
    rm -rf .git
    git init -b main

    # Criar ambiente virtual
    python3 -m venv .venv

    code .
}
```

### Melhorias Alcançadas

| Aspecto | Antes (v1.2) | Depois (v1.3) |
|---------|--------------|---------------|
| **Arquivos de Configuração** | Vazios | ✅ Pré-preenchidos (`.gitignore`, `.editorconfig`, etc.) |
| **pyproject.toml** | Vazio | ✅ Completo (deps, Ruff rules, etc.) |
| **Dockerfile** | Vazio | ✅ Multi-stage build profissional |
| **Tempo de Setup** | ~30 min | ~2 min (ainda com passos manuais) |

### Problemas Remanescentes

- ⚠️ **Placeholders:** Arquivos ainda continham `meu_projeto_placeholder`, `[ano]`, `Seu Nome`
- ⚠️ **Personalização Manual:** Desenvolvedor precisava editar `README.md`, `LICENSE`, etc.
- ⚠️ **Sem Commit Inicial:** Projeto ficava em estado "unstaged"

---

## 🎨 v1.4: "Personalização" (Automação de `sed`)

### Mudança Arquitetural Chave

**Adição de "estação de personalização" usando `sed` e `git config`.**

```bash
newproject() {
    PROJECT_NAME="$1"
    PROJECT_DIR="$HOME/projects/$PROJECT_NAME"
    TEMPLATE_REPO="git@github.com:Ismael-1712/python-template-profissional.git"

    git clone "$TEMPLATE_REPO" "$PROJECT_DIR"
    cd "$PROJECT_DIR"

    rm -rf .git
    git init -b main

    # ⭐ Nova seção: Personalização automática
    AUTHOR_NAME=$(git config user.name)
    AUTHOR_EMAIL=$(git config user.email)
    CURRENT_YEAR=$(date +"%Y")

    # Substituir placeholders
    grep -rl "meu_projeto_placeholder" . --exclude-dir={.git,.venv} | \
        xargs -r sed -i "s/meu_projeto_placeholder/$PROJECT_NAME/g"

    grep -rl "[ano]" . --exclude-dir={.git,.venv} | \
        xargs -r sed -i "s/\[ano\]/$CURRENT_YEAR/g"

    grep -rl "Seu Nome" . --exclude-dir={.git,.venv} | \
        xargs -r sed -i "s/Seu Nome/$AUTHOR_NAME/g"

    grep -rl "seu-email@dominio.com" . --exclude-dir={.git,.venv} | \
        xargs -r sed -i "s/seu-email@dominio.com/$AUTHOR_EMAIL/g"

    python3 -m venv .venv
    code .
}
```

### Melhorias Alcançadas

| Arquivo | Placeholder | Substituído Por |
|---------|-------------|-----------------|
| `README.md` | `meu_projeto_placeholder` | Nome do projeto (`$PROJECT_NAME`) |
| `pyproject.toml` | `meu_projeto_placeholder` | Nome do projeto |
| `pyproject.toml` | `seu-email@dominio.com` | Email do desenvolvedor (`git config user.email`) |
| `pyproject.toml` | `Seu Nome` | Nome do desenvolvedor (`git config user.name`) |
| `LICENSE` | `[ano]` | Ano atual (`date +"%Y"`) |
| `LICENSE` | `Seu Nome` | Nome do desenvolvedor |
| `SECURITY.md` | `seu-email@dominio.com` | Email do desenvolvedor |

### Métrica de Melhoria

- ⏱️ **Tempo de Personalização Manual:** ~10 min → ~0 segundos
- 🐛 **Taxa de Erros de Placeholder:** ~30% → 0%

### Problema Crítico Identificado (Etapa 27)

Durante validação com projeto real (`Automated-Notes-in-Obsidian`), detectou-se que:

```bash
git status  # Mostrava dezenas de arquivos "unstaged"
```

**Implicação:** Projetos ficavam em estado "sujo" após criação, violando princípio de "estado inicial limpo".

---

## ✅ v1.5: "Controle de Qualidade" (Estado Atual)

### Mudança Arquitetural Chave

**Adição de `git add .` e `git commit` automático.**

```bash
newproject() {
    # ... (lógica de v1.4) ...

    # ⭐ Nova seção: Salvamento automático
    echo "💾 Salvando estado inicial..."
    git add .
    git commit -m "feat: initial project setup from template"

    echo "✅ Projeto '$PROJECT_NAME' criado com sucesso!"
    code .
}
```

### Melhorias Alcançadas

| Aspecto | v1.4 | v1.5 |
|---------|------|------|
| **Estado Git** | Unstaged (sujo) | ✅ Commit limpo |
| **Histórico Git** | Vazio | ✅ 1 commit inicial rastreável |
| **Rastreabilidade** | Impossível saber quando/como projeto foi criado | ✅ Commit message indica origem ("from template") |
| **Facilidade de Push** | Desenvolvedor precisa fazer `git add .` e `git commit` | ✅ Pronto para `git remote add` e `git push` |

### Validação Completa (Cenário Real)

```bash
# 1. Remover projeto obsoleto (criado com v1.2)
rm -rf ~/projects/Automated-Notes-in-Obsidian

# 2. Recriar com v1.5
newproject Automated-Notes-in-Obsidian

# 3. Verificar estado
cd ~/projects/Automated-Notes-in-Obsidian
git log --oneline
# Output:
# a1b2c3d feat: initial project setup from template

git status
# Output:
# On branch main
# nothing to commit, working tree clean ✅

# 4. Verificar personalização
grep "Automated-Notes-in-Obsidian" README.md
# ✅ Encontrado

grep "meu_projeto_placeholder" README.md
# (nenhum resultado) ✅
```

---

## 🔄 Evolução Adicional: Suporte a Branches (v1.5+)

### Implementação de `--tipo`

Durante a fase v1.5, foi adicionado suporte a **branches especializadas** do template.

```bash
newproject meu-servico --tipo=api
# Clona branch 'api' (pré-configurado com FastAPI)

newproject minha-cli --tipo=cli
# Clona branch 'cli' (pré-configurado com Typer)
```

### Mudanças no Template Repository

| Branch | Base | Dependências Adicionais | Estrutura |
|--------|------|-------------------------|-----------|
| `main` | Genérico | `pytest`, `ruff`, `mypy` | `src/` genérico |
| `api` | main | `+ fastapi`, `uvicorn` | `src/api/` com routes |
| `cli` | main | `+ typer`, `rich` | `src/cli/` com commands |

---

## 📊 Comparação Final: v1.2 vs v1.5

| Métrica | v1.2 | v1.5 | Melhoria |
|---------|------|------|----------|
| **Tempo Total de Setup** | ~30-45 min | ~5 segundos | 🚀 **99% mais rápido** |
| **Arquivos Pré-preenchidos** | 0 | ~25 arquivos | 🎯 **∞% mais completo** |
| **Taxa de Erros** | ~40% | <1% | ✅ **40x mais confiável** |
| **Padronização (Ruff, Mypy)** | Inconsistente | 100% padronizado | ✅ **100% conformidade** |
| **Variedade de Tipos** | 1 (genérico) | 3+ (genérico, api, cli) | 🎨 **3x mais flexível** |
| **Estado Git Inicial** | Nenhum | Commit limpo | ✅ **Rastreabilidade completa** |

---

## 🎓 Lições Aprendidas

### Decisões de Design Validadas

1. **Separação Molde/Fábrica**
   - ✅ **Pro:** Facilita manutenção (molde no Git, fábrica no shell)
   - ✅ **Pro:** Permite versionamento do molde (branches, tags)
   - ⚠️ **Con:** Requer sincronização entre dois componentes

2. **Personalização via `sed`**
   - ✅ **Pro:** Rápido e portátil (funciona em Linux/Mac)
   - ✅ **Pro:** Não requer dependências Python
   - ⚠️ **Con:** Frágil se placeholders mudarem formato

3. **Commit Automático**
   - ✅ **Pro:** Garante estado limpo desde o início
   - ✅ **Pro:** Facilita integração com GitHub (pronto para push)
   - ⚠️ **Con:** Desenvolvedor não pode revisar antes do commit (trade-off aceitável)

### Anti-Padrões Evitados

| Anti-Padrão | Por que Evitamos |
|-------------|------------------|
| **Hardcoded Paths** | Usamos `$HOME/projects` e `git config` (flexível) |
| **Arquivos Vazios** | Clone completo do template (tudo pré-preenchido) |
| **Histórico Poluído** | `rm -rf .git` + `git init` (histórico limpo) |
| **Estado Sujo** | `git commit` automático (working tree limpo) |

---

## 🚀 Roadmap Futuro (Baseado no Relatório Original)

### Prioridade 1 (Crítica): CI/CD no Molde

**Objetivo:** Adicionar `.github/workflows/ci.yml` ao template.

**Benefício:** Novos projetos já nascem com testes automatizados no GitHub Actions.

### Prioridade 2 (Alta): Branch `data-science`

**Objetivo:** Criar variante para projetos de Data Science.

**Dependências:** `pandas`, `jupyter`, `scikit-learn`, `matplotlib`

**Estrutura:** `notebooks/`, `src/data/`, `src/models/`

### Prioridade 3 (Média): Scripts Reutilizáveis

**Objetivo:** Transplantar scripts úteis (ex: `copilot_audit.py`) para `scripts/` do template.

**Benefício:** Novos projetos herdam ferramentas de auditoria/recuperação.

### Prioridade 4 (Baixa): Teste da Fábrica

**Objetivo:** Criar `~/test_factory.sh` para validar `newproject`.

**Exemplo:**

```bash
#!/bin/bash
# test_factory.sh

newproject _test_project_

# Validações
grep "_test_project_" ~/projects/_test_project_/README.md || exit 1
grep "$(git config user.name)" ~/projects/_test_project_/LICENSE || exit 1

# Limpeza
rm -rf ~/projects/_test_project_

echo "✅ FÁBRICA OK"
```

---

## 📚 Referências

- Relatório Técnico de Evolução e Handover (28/10/2025)
- [Arquitetura de Scaffolding Atual](./PROJECT_SCAFFOLDING_ARCHITECTURE.md)
- [Instruções Perpétuas do Copilot](../.github/copilot-instructions.md)

---

**Autor:** Engineering Team
**Baseado em:** Relatório do Prof. de TI e Ismael Tavares Dos Reis
**Status:** 🔵 Documento Histórico (Referência)
**Última Atualização:** 2025-12-16
