---
id: handover-next-team
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags:
  - onboarding
  - architecture
  - tooling
linked_code:
  - scripts/cli/cortex.py
  - scripts/cli/doctor.py
  - scripts/cli/git_sync.py
title: '🎯 Manual de Sobrevivência - Handover para Próxima Equipe'
---

# 🎯 Manual de Sobrevivência - Handover para Próxima Equipe

**Data:** 01 de Dezembro de 2025
**Versão do Projeto:** 0.1.0
**Status:** Produção Pronta (Post-Sprint 4)

---

## 🚨 LEIA ISTO PRIMEIRO

Este projeto **NÃO é um aplicativo comum**. É uma **plataforma de engenharia** que serve como base para três produtos independentes através de um sistema de branches chamado **A Tríade**.

**NÃO ASSUMA NADA. SEMPRE VERIFIQUE.**

---

## 📐 Arquitetura: A Tríade

### Conceito Fundamental: "Herança com Personalidade"

Este repositório implementa um modelo de **três branches estratégicas** que coexistem como produtos distintos:

```
┌─────────────────────────────────────────────────────────────┐
│                    🟢 MAIN (Nave Mãe)                        │
│  • Infraestrutura e Automação                                │
│  • Scripts de DevOps (scripts/)                              │
│  • Configuração de Linting (ruff, mypy)                      │
│  • CORTEX (Sistema de Introspecção)                          │
│  • CI/CD Pipelines                                            │
└─────────────────────────────────────────────────────────────┘
           │                              │
           ├──────────────┐              ├──────────────┐
           ▼              │              ▼              │
┌──────────────────┐     │   ┌──────────────────┐     │
│  🔵 CLI Branch   │     │   │  🟣 API Branch   │     │
│                  │     │   │                  │     │
│  • Herda: main   │     │   │  • Herda: main   │     │
│  • Adiciona:     │     │   │  • Adiciona:     │     │
│    - Comandos    │     │   │    - Endpoints   │     │
│    - TUIs        │     │   │    - Models      │     │
│    - Validators  │     │   │    - Middleware  │     │
└──────────────────┘     │   └──────────────────┘     │
                         │                             │
                         └─────────────────────────────┘
                         (Sincronizados via git-sync)
```

### 🟢 Branch `main` - Plataforma de Engenharia

**Propósito:** Infraestrutura compartilhada e ferramentas de desenvolvimento.

**Contém:**

- `scripts/` - Automação e CLIs de desenvolvimento
- `docs/` - Documentação técnica e arquitetural
- `tests/` - Testes de infraestrutura
- `.github/` - CI/CD e configurações
- Configurações: `pyproject.toml`, `mypy_strict.ini`, `ruff.toml`

**NÃO contém:**

- Lógica de negócio
- Código de aplicação
- Endpoints HTTP
- Interfaces de usuário

### 🔵 Branch `cli` - Produto de Linha de Comando

**Propósito:** Aplicação CLI para usuários finais.

**Herda:** Tudo de `main`

**Adiciona:**

- `src/cli/` - Comandos CLI do produto
- `src/validators/` - Validação de inputs
- `src/tui/` - Interfaces TUI (Textual)

### 🟣 Branch `api` - Produto REST API

**Propósito:** Serviço HTTP/REST para integrações.

**Herda:** Tudo de `main`

**Adiciona:**

- `src/api/` - Endpoints REST
- `src/models/` - Modelos de dados
- `src/middleware/` - Autenticação, CORS, etc.

---

## 🛠️ Ferramentas Essenciais

### 1. `make install-dev` - Setup Completo

**Uso:**

```bash
make install-dev
```

**O que faz:**

- Instala dependências de desenvolvimento
- Configura pre-commit hooks
- Valida ambiente Python
- Instala comandos CLI (`cortex`, `dev-doctor`, `git-sync`)

**Quando usar:**

- Primeiro clone do repositório
- Após atualizar `requirements/dev.txt`
- Sempre que você trocar de branch da Tríade

---

### 2. `cortex map` - Mapa do Projeto

**Uso:**

```bash
cortex map
```

**Saída:** `.cortex/context.json`

**O que faz:**

- Lista todos os comandos CLI disponíveis
- Mapeia documentos arquiteturais
- Identifica dependências instaladas
- Gera estrutura de diretórios

**Quando usar:**

- **ANTES de fazer qualquer suposição sobre o projeto**
- Após fazer merge de `main` em `cli` ou `api`
- Quando o GitHub Copilot perguntar sobre a estrutura

**Exemplo de Saída:**

```json
{
  "cli_commands": [
    {"name": "cortex", "script_path": "scripts/cli/cortex.py"},
    {"name": "doctor", "script_path": "scripts/cli/doctor.py"},
    {"name": "git_sync", "script_path": "scripts/cli/git_sync.py"}
  ],
  "architecture_docs": [
    "docs/architecture/ARCHITECTURE_TRIAD.md",
    "docs/architecture/CORTEX_INDICE.md"
  ]
}
```

---

### 3. `dev-doctor` - Diagnóstico do Ambiente

**Uso:**

```bash
dev-doctor
```

**O que valida:**

- ✅ Python 3.10+ instalado
- ✅ Dependências críticas presentes
- ✅ Pre-commit configurado
- ✅ Git configurado corretamente
- ✅ Permissões de arquivos

**Quando usar:**

- Após `make install-dev`
- Quando algo não funciona (primeira linha de debug)
- Antes de abrir issues

**Saída Exemplo:**

```plaintext
✅ Python 3.11.6 detectado
✅ 21 dependências instaladas
⚠️  Pre-commit não configurado (executar: pre-commit install)
✅ Git user.name configurado
```

---

### 4. `git-sync` - Sincronização Segura da Tríade

**Uso:**

```bash
git-sync --source main --target cli --mode safe
```

**Modos:**

- `safe` - Merge com validação (padrão)
- `fast-forward` - Apenas fast-forward
- `rebase` - Rebase interativo

**Quando usar:**

- Trazer atualizações de `main` para `cli` ou `api`
- **NUNCA fazer merge manual entre branches da Tríade**

**Proteções:**

- Verifica conflitos antes de iniciar
- Cria backup automático
- Valida testes após merge
- Rollback automático em caso de falha

**Exemplo:**

```bash
# Atualizar branch CLI com mudanças de main
git checkout cli
git-sync --source main --target cli

# Atualizar branch API
git checkout api
git-sync --source main --target api
```

---

### 5. `dev-audit` - Auditoria de Qualidade

**Uso:**

```bash
dev-audit
```

**O que valida:**

- Mypy strict mode (type checking)
- Ruff linting (formatação)
- Pytest coverage (> 80%)
- CORTEX compliance (documentação)

**Saída:** `audit_report_YYYYMMDD_HHMMSS.json`

**Quando usar:**

- Antes de abrir Pull Request
- Após implementar feature
- Parte do CI/CD (automático)

---

## 📊 Estado Atual (Post-Sprint 4)

### ✅ Implementações Completas

1. **Mypy Strict Mode Ativo**
   - 13 regras de type checking ativas
   - Cobertura: 95% do código
   - 0 erros na baseline
   - Arquivo de config: `mypy_strict.ini`

2. **Testes Limpos**
   - 47 testes passando
   - Coverage: 89%
   - Sem warnings de deprecação

3. **Dependências Otimizadas**
   - Removidas 3 dependências fantasmas (`toml`, `colorama`, `pydantic`)
   - 21 dependências ativas
   - Instalação ~30% mais rápida

4. **CORTEX Operacional**
   - Sistema de introspecção funcionando
   - Documentação validada
   - Links bidirecionais ativos

### 🚧 Itens Pendentes

1. **Pre-commit Hook para Mypy**
   - Status: Planejado para Sprint 5
   - Blocker: Nenhum
   - Esforço: 2 horas

2. **Documentação de Type Hints**
   - Status: 70% completo
   - Faltam: Exemplos de Protocols e TypedDict
   - Localização: `docs/guides/type_hints.md`

3. **CI Check para Dependências Não Utilizadas**
   - Status: Design phase
   - Ferramenta: `pipreqs` + GitHub Action
   - Frequência: Semanal

---

## 🧠 CORTEX: Documentação Como Código

### Conceito

O CORTEX é um **sistema de introspecção** que trata documentação como código executável. Ele valida:

- Links entre código e documentação
- Metadata YAML (frontmatter)
- Estrutura de arquivos
- Dependências entre documentos

### Frontmatter CORTEX (YAML)

**Todo documento Markdown deve ter:**

```yaml
---
id: unique-identifier
type: arch|guide|history|reference
status: active|draft|deprecated
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: [mypy, testing, ci]
linked_code:
  - scripts/utils/logger.py
  - tests/test_logger.py
title: Título do Documento
---
```

### Comandos CORTEX

```bash
# Gerar mapa do projeto
cortex map

# Validar documentação
cortex audit .

# Adicionar frontmatter a documento
cortex init docs/guides/novo_documento.md

# Escanear links quebrados
cortex scan
```

### Regras Importantes

1. **Documentação é Obrigatória**
   - Mudanças arquiteturais → `docs/architecture/`
   - Guias de uso → `docs/guides/`
   - Histórico de sprints → `docs/history/sprintX/`

2. **Links São Bidirecionais**
   - Se `logger.py` é mencionado em `ARCHITECTURE_TRIAD.md`, deve haver `linked_code: [scripts/utils/logger.py]`

3. **Validação no CI**
   - `cortex audit .` roda em todo PR
   - Documentação sem frontmatter = CI falha
   - Links quebrados = CI falha

---

## 🔒 Princípios de Segurança

### Root Lockdown

O diretório raiz (`/`) **NÃO deve conter código de aplicação**.

**Arquivos Permitidos na Raiz:**

- `pyproject.toml`, `Makefile`, `README.md`
- `Dockerfile`, `docker-compose.yml`
- Arquivos de configuração (`.ruff.toml`, `mypy.ini`)
- Este arquivo (`HANDOVER_NEXT_TEAM.md`)

**Arquivos NÃO Permitidos na Raiz:**

- `main.py` → mover para `src/main.py`
- `utils.py` → mover para `src/utils/`
- `config.py` → mover para `src/config/`

**Razão:** Separação de concerns, evita poluição do namespace.

---

## 📚 Documentação Crítica

### Leitura Obrigatória

1. **docs/architecture/ARCHITECTURE_TRIAD.md**
   - Manifesto da Tríade
   - Protocolos de merge entre branches

2. **docs/architecture/CORTEX_INDICE.md**
   - Índice de toda documentação
   - Ordem de leitura recomendada

3. **docs/guides/SMART_GIT_SYNC_GUIDE.md**
   - Como usar `git-sync` com segurança

4. **docs/history/sprint_4/MYPY_STRICT_IMPLEMENTATION.md**
   - Estado atual do type checking

### Índice Rápido

```plaintext
docs/
├── architecture/          # Decisões arquiteturais
│   ├── ARCHITECTURE_TRIAD.md
│   ├── CORTEX_INDICE.md
│   └── TRIAD_GOVERNANCE.md
├── guides/                # Guias de uso
│   ├── CORTEX_INTROSPECTION_SYSTEM.md
│   ├── SMART_GIT_SYNC_GUIDE.md
│   └── testing.md
├── history/               # Histórico de sprints
│   ├── sprint_1_foundation/
│   ├── sprint_2_cortex/
│   ├── sprint_4/
│   │   └── MYPY_STRICT_IMPLEMENTATION.md
└── reference/             # Referências técnicas
```

---

## 🎯 Fluxo de Trabalho Recomendado

### Para Nova Feature

```bash
# 1. Entenda o contexto
cortex map
cat .cortex/context.json

# 2. Consulte arquitetura
cat docs/architecture/CORTEX_INDICE.md

# 3. Verifique branch correta
git branch -a
# Você deve estar em main, cli ou api

# 4. Sincronize com main (se em cli/api)
git-sync --source main --target $(git branch --show-current)

# 5. Implemente a feature
# ... código aqui ...

# 6. Valide qualidade
dev-audit

# 7. Documente mudanças
# Adicione em docs/architecture/ se arquitetural
# Atualize docs/guides/ se feature de usuário

# 8. Abra Pull Request
```

### Para Bugfix

```bash
# 1. Diagnóstico
dev-doctor

# 2. Reproduza o bug
pytest tests/test_nome_do_modulo.py -v

# 3. Corrija
# ... código aqui ...

# 4. Valide
mypy scripts/ tests/
pytest tests/ --cov

# 5. Documente (se relevante)
# Adicione em docs/history/sprintX/BUGFIX_XXX.md
```

---

## 🚨 Armadilhas Comuns

### ❌ NÃO FAÇA

1. **Merge manual entre branches da Tríade**

   ```bash
   # ❌ ERRADO
   git checkout cli
   git merge main
   ```

   ```bash
   # ✅ CORRETO
   git checkout cli
   git-sync --source main --target cli
   ```

2. **Assumir estrutura de diretórios**

   ```bash
   # ❌ ERRADO
   "Vou adicionar a API em src/api/"

   # ✅ CORRETO
   cortex map
   cat .cortex/context.json  # Verificar estrutura
   ```

3. **Ignorar erros do Mypy**

   ```python
   # ❌ ERRADO
   result = função_sem_tipo()  # type: ignore

   # ✅ CORRETO
   result: dict[str, Any] = função_sem_tipo()
   ```

4. **Criar arquivos na raiz**

   ```bash
   # ❌ ERRADO
   touch utils.py

   # ✅ CORRETO
   touch src/utils/helpers.py
   ```

---

## 🆘 Solução de Problemas

### Problema: "Comando `cortex` não encontrado"

**Solução:**

```bash
make install-dev
# OU
pip install -e .
```

### Problema: "Mypy reporta erros em biblioteca de terceiros"

**Solução:**
Adicionar ao `mypy_strict.ini`:

```ini
[mypy-nome_da_biblioteca.*]
ignore_missing_imports = True
```

### Problema: "Conflito de merge ao sincronizar branches"

**Solução:**

```bash
git-sync --source main --target cli --mode rebase
# Resolver conflitos manualmente
# git-sync fará rollback se falhar
```

### Problema: "CORTEX audit falhando"

**Solução:**

```bash
# Ver detalhes do erro
cortex audit . --verbose

# Adicionar frontmatter faltante
cortex init docs/guides/arquivo_sem_metadata.md

# Validar links
cortex scan
```

---

## 📞 Contatos e Recursos

### Documentação Externa

- [Python Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [Pytest Best Practices](https://docs.pytest.org/)

### Comandos de Emergência

```bash
# Reset completo do ambiente
make clean
make install-dev

# Reverter última sincronização
git-sync --rollback

# Gerar relatório de auditoria completo
dev-audit --full-report

# Verificar saúde do repositório
dev-doctor --check-all
```

---

## 🎓 Princípios SRE Aplicados

Este projeto segue os princípios de **Site Reliability Engineering**:

1. **Automação** - Scripts reutilizáveis (`scripts/cli/`)
2. **Observabilidade** - Logging estruturado (via `scripts/utils/logger.py`)
3. **Confiabilidade** - Testes > 80% coverage
4. **Simplicidade** - Soluções diretas, não over-engineering

---

## 🚀 Próximos Passos Sugeridos

### Curto Prazo (Sprint 5)

- [ ] Adicionar Mypy no pre-commit hook
- [ ] Completar documentação de Type Hints
- [ ] Implementar CI check para dependências não usadas

### Médio Prazo (Sprints 6-8)

- [ ] Migrar para `pyright` (experimento)
- [ ] Adicionar benchmarks de performance
- [ ] Implementar telemetria (OpenTelemetry)

### Longo Prazo (Q1 2026)

- [ ] Containerização completa (Docker)
- [ ] Deploy automatizado (GitHub Actions → Cloud Run)
- [ ] Documentação interativa (MkDocs + Jupyter)

---

## ✅ Checklist de Onboarding

Você concluiu o onboarding quando conseguir:

- [ ] Executar `make install-dev` com sucesso
- [ ] Gerar `.cortex/context.json` com `cortex map`
- [ ] Executar `dev-doctor` sem erros críticos
- [ ] Sincronizar branches com `git-sync`
- [ ] Passar `dev-audit` em 100%
- [ ] Entender a diferença entre `main`, `cli` e `api`
- [ ] Adicionar frontmatter CORTEX a um documento
- [ ] Criar um PR seguindo o fluxo de trabalho recomendado

---

**Última Atualização:** 01/12/2025
**Mantenedor:** Engineering Team
**Contato:** Consulte `CONTRIBUTING.md` para canais de comunicação

---

**Bem-vindo à equipe. Boa sorte! 🚀**
