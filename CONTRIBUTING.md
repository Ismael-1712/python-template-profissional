# 👷 Guia de Contribuição

Bem-vindo ao time de engenharia! Este projeto utiliza ferramentas de automação para garantir qualidade e padronização.

> **Versão do Projeto:** 0.1.0
> **Python Requerido:** 3.10+
> **Última Atualização:** 2025-12-15T14:21:48.706738+00:00

---

## 🚀 Quick Start

### 1️⃣ Setup do Ambiente

```bash
# Clone o repositório
git clone {{ repository_url }}.git
cd {{ project_slug | replace('_', '-') }}

# Configure o ambiente (Python 3.10+)
make setup

# Valide a instalação
make doctor
```

### 2️⃣ Validação Rápida

```bash
# Pipeline completo (lint + test)
make validate

# Ou etapa por etapa:
make format  # Formatar código
make lint    # Verificar problemas
make test    # Executar testes
```

---

## 🛠️ Fluxo de Trabalho Diário (The Happy Path)

Para evitar fricção com linters e formatadores, recomendamos fortemente o uso do comando `make save`.

### O Comando "Super Commit" 💎

Ao invés de rodar `git commit` manualmente e lutar contra o pre-commit, use:

```bash
make save m="tipo(escopo): sua mensagem"
```

**O que ele faz por você:**

1. ✨ Formata todo o código (Ruff)
2. 📦 Adiciona alterações ao stage (`git add .`)
3. ✅ Realiza o commit (que passará direto pelos hooks de verificação)

**Exemplo:**

```bash
make save m="feat(audit): adiciona detecção de código duplicado"
```

**Por que isso é melhor?**

- Não há surpresas no pre-commit
- Economiza tempo em ciclos de formatação
- Garante consistência antes de ir para o repositório

---

## 🧪 Testes e Qualidade

### Suite Completa de Testes

```bash
# Execução rápida
make test

# Modo verboso (para debugging)
make test-verbose

# Com relatório de cobertura
make test-coverage
```

**Métricas Atuais:**

- Total de Testes: 0 módulos testados
- Health Score: **60.0/100** (Status: critical)

### Tipagem e Linting 🔍

Todo o código passa por verificação estática.

**Formatador:** `ruff` (v0.14.6+)

```bash
# Verificar problemas (não modifica arquivos)
make lint

# Formatar automaticamente
make format
```

**Regras de Tipagem Moderna:**

1. **Future Annotations (Obrigatório):**
   - Todo arquivo Python deve começar com:

     ```python
     from __future__ import annotations
     ```

   - Isso habilita tipagem lazy (PEP 563) e evita problemas de referência circular.

2. **Imports Tardios para Evitar Ciclos:**
   - Use `TYPE_CHECKING` para imports apenas de tipagem:

     ```python
     from __future__ import annotations
     from typing import TYPE_CHECKING

     if TYPE_CHECKING:
         from module import MyClass  # Só importado durante type checking

     def my_function() -> MyClass:  # OK, string annotation é lazy
         ...
     ```

3. **Tipagem em Testes:**
   - Funções de teste devem ter anotação `-> None`:

     ```python
     def test_my_feature() -> None:
         assert True
     ```

---

## 🛡️ Sistema de Auditoria CORTEX

O projeto possui um sistema customizado de auditoria de código.

### Executar Auditoria Completa

```bash
make audit
```

**O que ele analisa:**

- 🔒 Vulnerabilidades de segurança (credenciais hardcoded, imports inseguros)
- 🔄 Código duplicado (blocos repetidos)
- 📊 Complexidade ciclomática (funções muito complexas)
- 📝 Cobertura de docstrings
- 🧪 Cobertura de testes

### Comandos CORTEX Disponíveis

| Comando | Descrição |
|---------|-----------|
| `audit` | Utilitário CORTEX |
| `cortex` | Utilitário CORTEX |
| `doctor` | Utilitário CORTEX |
| `git_sync` | Utilitário CORTEX |
| `install_dev` | Utilitário CORTEX |
| `mock_ci` | Utilitário CORTEX |
| `mock_generate` | Utilitário CORTEX |
| `mock_validate` | Utilitário CORTEX |
| `upgrade_python` | Utilitário CORTEX |

### Dashboard Interativo

Para visualizar métricas no console:

```bash
python3 scripts/audit_dashboard.py
```

Para gerar um relatório HTML standalone:

```bash
python3 scripts/audit_dashboard.py --export-html
```

---

## 🌍 Mantendo a Internacionalização (i18n)

O projeto é bilíngue (EN/PT). Se você alterar mensagens de UI ou adicionar novas strings, siga este fluxo:

### 1️⃣ Instrumentação

Use `_("Sua string")` no código Python. **Não use f-strings em UI.**

```python
# ❌ ERRADO
print(f"Processando {count} arquivos")

# ✅ CORRETO
print(_("Processando {} arquivos").format(count))
```

### 2️⃣ Extração → Atualização → Compilação

```bash
make i18n-extract   # Extrai strings
make i18n-update    # Sincroniza .po
make i18n-compile   # Gera binários .mo
```

### 📊 Verificar Estatísticas de Tradução

```bash
make i18n-stats
```

---

## 🛠️ Setup de Ambiente (Padrão Ouro)

### Requisitos de Sistema

- **Python:** 3.10+
- **Sistema Operacional:** Linux, macOS, ou Windows (com WSL2)
- **Ferramentas:** Git, Make, Pyenv (opcional mas recomendado)

### Gerenciamento de Versões Python (Pyenv)

O projeto utiliza **Pyenv** para garantir compatibilidade entre diferentes ambientes de desenvolvimento.

**Arquivo de Configuração:** `.python-version`

**Instalação do Pyenv (se necessário):**

```bash
# Linux/macOS
curl https://pyenv.run | bash

# Adicione ao ~/.bashrc ou ~/.zshrc:
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
```

**Instalar a versão Python do projeto:**

```bash
# Leia a versão do arquivo .python-version
pyenv install $(cat .python-version)
```

**💡 Dica:** Use `make upgrade-python` para atualizar automaticamente para os patches mais recentes.

### ✅ Validação do Ambiente

**Sempre execute após o setup inicial:**

```bash
make doctor
```

O `doctor` realiza um diagnóstico completo:

- 🔍 Verifica versão do Python
- 📦 Valida dependências instaladas
- 🛠️ Checa ferramentas de desenvolvimento
- ⚙️ Confirma configuração do ambiente virtual

### Testes Multi-Versão (Tox)

O projeto suporta **múltiplas versões do Python** (3.11, 3.12, 3.13). Antes de abrir um PR, valide a compatibilidade:

```bash
make test-matrix
```

**O que este comando faz:**

- ✅ Executa toda a suite de testes em Python 3.11, 3.12 e 3.13
- ✅ Valida que o código é compatível com todas as versões suportadas
- ✅ Detecta problemas de compatibilidade antes do merge

---

## 🔄 Fluxo de Trabalho Git

### Estratégia de Branches

Este projeto usa **Auto-Propagação**:

1. **`main`**: Branch protegida (fonte da verdade)
2. **`api` / `cli`**: Variantes automáticas (não fazer merge manual)

### Processo de Contribuição

1. **Criar branch de feature**

```bash
git checkout -b feat/minha-feature
```

1. **Desenvolver e testar localmente**

```bash
make format    # Formatar código
make validate  # Lint + Testes
```

1. **Commit com mensagem semântica**

```bash
make save m="feat(escopo): descrição clara"
```

**Tipos de commit válidos:**

- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Apenas documentação
- `refactor`: Refatoração (sem mudança de comportamento)
- `perf`: Melhoria de performance
- `test`: Adiciona/corrige testes
- `chore`: Tarefas de manutenção

1. **Push e Pull Request**

```bash
git push origin feat/minha-feature
```

Abra PR para `main` no GitHub. O CI validará automaticamente.

---

## 🚨 Checklist Antes de Abrir PR

- [ ] Ambiente validado com `make doctor`
- [ ] `make format` executado
- [ ] `make lint` passou sem erros
- [ ] `make test` passou 100%
- [ ] Strings de UI instrumentadas com `_()`
- [ ] `make i18n-compile` executado (se alterou UI)
- [ ] `make audit` não introduziu novos problemas críticos
- [ ] Commit segue Conventional Commits
- [ ] Descrição do PR explica o "porquê", não apenas o "o quê"
- [ ] Documentação atualizada (se aplicável)

---

## 🧰 Comandos Úteis para o Dia a Dia

```bash
# Validação rápida antes do commit
make validate

# Pipeline completo (setup + lint + test)
make all

# Limpeza de cache e artefatos
make clean

# Limpeza profunda (incluindo dependências)
make clean-all

# Ver versões das ferramentas
make version

# Ver ajuda com todos os comandos
make help
```

---

## 📚 Documentação Adicional

- [Arquitetura do CORTEX](docs/architecture/CORTEX_INDICE.md)
- [Sistema de Auditoria](docs/architecture/CODE_AUDIT.md)
- [Knowledge Graph](docs/architecture/CORTEX_FASE03_DESIGN.md)
- [Dynamic README](docs/reference/DYNAMIC_README.md)
- [Smart Git Sync](docs/SMART_GIT_SYNC_GUIDE.md)

---

## 💡 Dicas de Produtividade

### Alias no Shell

Adicione ao seu `.bashrc` ou `.zshrc`:

```bash
alias msave='make save m='
alias mcheck='make format && make validate'
```

Uso:

```bash
msave "feat: melhoria X"
mcheck
```

### VS Code

Instale a extensão **Ruff** para formatação automática ao salvar.

**settings.json:**

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

---

## 🤝 Perguntas?

Se tiver dúvidas sobre o fluxo de contribuição:

1. Consulte este guia primeiro
2. Leia a documentação em `docs/`
3. Abra uma issue com a tag `question`

---

## 🛡️ Padrões de Engenharia (As 3 Travas de Segurança)

Para evitar regressões e "alucinações" de código, todo desenvolvimento deve respeitar estritamente estas 3 leis:

### 🔒 Trava 1: Verificação Forense (Anti-Alucinação)

**Regra:** Nunca assuma que um arquivo ou classe existe. Verifique antes de importar.

- **Antes de criar um `__init__.py` ou `import`:** Execute `grep` ou `ls` para confirmar o nome exato da classe/função.
- **Exemplo:** Não importe `SecurityScanner` se a classe se chama `FileScanner`.

### 🔒 Trava 2: Tipagem Estática Absoluta

**Regra:** O `mypy` em modo estrito é a autoridade final.

- **Não ignore erros de tipo:** Se o Mypy reclamar, corrija o código, não use `Any` ou `# type: ignore` a menos que estritamente necessário.
- **Tipos > Testes:** Testes unitários podem passar com dados errados (falso positivo), mas a checagem estática não deixa passar contratos inválidos.

### 🔒 Trava 3: Princípio da Realidade dos Dados

**Regra:** Testes devem usar dados que espelham a produção, não invenções convenientes.

- **Ao criar Fixtures:** Olhe como o código de produção chama a função (ex: via `grep` no código consumidor).
- **Evite Estruturas Aninhadas Falsas:** Se a função espera `{'key': 'val'}`, não passe `{'wrapper': {'key': 'val'}}` no teste.

---

## Obrigado por contribuir! 🎉

**meu_projeto_placeholder** v0.1.0 - Construído com 🧠 pela Seu Nome

---

_Guia gerado dinamicamente em 2025-12-15T14:21:48.706738+00:00 por `cortex generate contributing`_
