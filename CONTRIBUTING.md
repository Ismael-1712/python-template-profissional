# 👷 Guia de Contribuição

Bem-vindo ao time de engenharia! Este projeto utiliza ferramentas de automação para garantir qualidade e padronização.

---

## 🚀 Fluxo de Trabalho Diário (The Happy Path)

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

### 2️⃣ Extração

Rode `make i18n-extract` para atualizar o template `.pot`.

```bash
make i18n-extract
```

Isso gera/atualiza o arquivo `locales/messages.pot` com todas as strings traduzíveis.

### 3️⃣ Atualização

Rode `make i18n-update` para sincronizar os arquivos `.po`.

```bash
make i18n-update
```

### 4️⃣ Tradução

Edite `locales/en_US/LC_MESSAGES/messages.po` e preencha os `msgstr`:

```po
#: scripts/smart_git_sync.py:42
msgid "Processando {} arquivos"
msgstr "Processing {} files"
```

### 5️⃣ Compilação

Rode `make i18n-compile` para gerar os binários `.mo`:

```bash
make i18n-compile
```

### 📊 Verificar Estatísticas de Tradução

Para ver o status das traduções:

```bash
make i18n-stats
```

---

## 🧪 Testes e Qualidade

### Testes do Dashboard 📊

Se você alterar o `audit_dashboard.py`, é **obrigatório** rodar a bateria de testes isolada para garantir que o HTML não quebrou:

```bash
pytest tests/test_audit_dashboard.py
```

**Por que isso é crítico?**
O dashboard gera HTML dinâmico com métricas. Testes validam:

- ✅ Estrutura HTML válida
- ✅ Injeção correta de dados
- ✅ Renderização de gráficos
- ✅ Tratamento de edge cases

### Suite Completa de Testes

```bash
# Execução rápida
make test

# Modo verboso (para debugging)
make test-verbose

# Com relatório de cobertura
make test-coverage
```

### Tipagem e Linting 🔍

Todo o código passa por verificação estática.

**Formatador:** `ruff` (v0.14.6+)

```bash
# Verificar problemas (não modifica arquivos)
make lint

# Formatar automaticamente
make format
```

**Regras Ativas:**

- ✅ Pycodestyle (E, W)
- ✅ Pyflakes (F)
- ✅ isort (I) - Ordenação de imports
- ✅ pep8-naming (N) - Convenções de nomes
- ✅ pyupgrade (UP) - Modernização de sintaxe
- ✅ flake8-bugbear (B) - Detecção de bugs comuns
- ✅ pydocstyle (D) - Validação de docstrings (Google Style)

---

## 🛡️ Sistema de Auditoria

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

**Saída:**
O comando gera um relatório JSON (`audit_report_*.json`) e pode abrir um dashboard HTML interativo.

### Dashboard Interativo

Para visualizar métricas no console:

```bash
python3 scripts/audit_dashboard.py
```

Para gerar um relatório HTML standalone:

```bash
python3 scripts/audit_dashboard.py --export-html
```

O arquivo HTML gerado contém gráficos e tabelas detalhadas que podem ser abertos em qualquer navegador.

---

## 🛠️ Setup de Ambiente (Padrão Ouro)

### Gerenciamento de Versões Python (Pyenv)

O projeto utiliza **Pyenv** para garantir compatibilidade entre diferentes ambientes de desenvolvimento.

**Arquivo de Configuração:** `.python-version`

Este arquivo define a versão Python recomendada para o projeto. O Pyenv ativa automaticamente a versão correta ao entrar no diretório.

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

**💡 Dica:** Use `make upgrade-python` para atualizar automaticamente para os patches mais recentes de todas as versões Python suportadas (3.11, 3.12, 3.13).

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

Se encontrar problemas, ele fornece instruções de correção detalhadas.

### Testes Multi-Versão (Tox)

O projeto suporta **múltiplas versões do Python** (3.11, 3.12, 3.13). Antes de abrir um PR, valide a compatibilidade:

```bash
make test-matrix
```

**O que este comando faz:**

- ✅ Executa toda a suite de testes em Python 3.11, 3.12 e 3.13
- ✅ Valida que o código é compatível com todas as versões suportadas
- ✅ Detecta problemas de compatibilidade antes do merge
- ✅ Usa Tox para gerenciar ambientes virtuais isolados

**Pré-requisito:** As versões Python devem estar instaladas via Pyenv.

**Quando usar:**

- 🔴 **Obrigatório** antes de abrir PR que altera lógica de negócio
- 🟡 **Recomendado** para qualquer mudança em dependências ou código core
- 🟢 **Opcional** para mudanças apenas em documentação

### ⚡ Automação de Ambiente (Direnv)

Este projeto suporta **ativação automática de ambiente**. Ao entrar na pasta do projeto, o virtualenv é ativado sozinho.

**Pré-requisito:**
Instale o [direnv](https://direnv.net/) no seu sistema:

```bash
# Ubuntu/Debian
sudo apt install direnv

# MacOS
brew install direnv
```

**Ativação:**
Na primeira vez, execute:

```bash
direnv allow
```

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
make check     # Lint + Testes
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

---

## 🧰 Comandos Úteis para o Dia a Dia

```bash
# Validação rápida antes do commit
make check

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

- [Sistema de Auditoria](docs/CODE_AUDIT.md)
- [Sistema de Mocks](docs/README_test_mock_system.md)
- [Smart Git Sync](docs/SMART_GIT_SYNC_GUIDE.md)
- [Testes](docs/guides/testing.md)

---

## 💡 Dicas de Produtividade

### Alias no Shell

Adicione ao seu `.bashrc` ou `.zshrc`:

```bash
alias msave='make save m='
alias mcheck='make format && make check'
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

## 🆘 Troubleshooting & Exit Codes

O `smart_git_sync.py` utiliza códigos de saída padronizados para facilitar a integração em pipelines CI/CD e debugging.

### Códigos de Saída (Exit Codes)

| Código | Significado | Descrição |
|--------|-------------|-----------|
| `0` | **Sucesso** | Operação concluída sem erros |
| `1` | **Erro de Operação** | Erro de lógica de negócio (Git error, Linter error, etc.) |
| `2` | **Bug Interno** | Crash/Exceção inesperada - **Requer atenção da Engenharia** |
| `130` | **Interrupção do Usuário** | Processo cancelado pelo usuário (Ctrl+C) |

### 📋 Logs e Debugging

**Importante:** Erros com **Exit Code 2** geram logs com traceback completo para debugging.

Esses logs são cruciais para identificar problemas internos e bugs no sistema. Se você encontrar um Exit Code 2, verifique os logs para detalhes técnicos completos.

**Exemplo de verificação em scripts:**

```bash
python scripts/smart_git_sync.py
EXIT_CODE=$?

if [ $EXIT_CODE -eq 2 ]; then
    echo "⚠️  Bug interno detectado! Verifique os logs."
    exit 1
fi
```

---

## Obrigado por contribuir! 🎉

---

## 🛡️ Padrões de Engenharia (As 3 Travas de Segurança)

Para evitar regressões e "alucinações" de código, todo desenvolvimento deve respeitar estritamente estas 3 leis:

### 🔒 Trava 1: Verificação Forense (Anti-Alucinação)

**Regra:** Nunca assuma que um arquivo ou classe existe. Verifique antes de importar.

- **Antes de criar um `__init__.py` ou `import`:** Execute `grep` ou `ls` para confirmar o nome exato da classe/função.
- **Exemplo:** Não importe `SecurityScanner` se a classe se chama `FileScanner`. A divergência entre o "Mapa Mental" e o "Território Real" é a maior causa de quebras em CI.

### 🔒 Trava 2: Tipagem Estática Absoluta

**Regra:** O `mypy` em modo estrito é a autoridade final.

- **Não ignore erros de tipo:** Se o Mypy reclamar, corrija o código, não use `Any` ou `# type: ignore` a menos que estritamente necessário.
- **Tipos > Testes:** Testes unitários podem passar com dados errados (falso positivo), mas a checagem estática não deixa passar contratos inválidos.

### 🔒 Trava 3: Princípio da Realidade dos Dados

**Regra:** Testes devem usar dados que espelham a produção, não invenções convenientes.

- **Ao criar Fixtures:** Olhe como o código de produção chama a função (ex: via `grep` no código consumidor).
- **Evite Estruturas Aninhadas Falsas:** Se a função espera `{'key': 'val'}`, não passe `{'wrapper': {'key': 'val'}}` no teste.
