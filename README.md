# 🧠 CORTEX — Professional Python Template

> **The Symbolic Neural Network for Documentation as Code**
> _Creative Organized Rational Thinking EXecution_

[![Python](https://img.shields.io/badge/python-{{ python_version }}+-blue.svg)](https://www.python.org/downloads/)
[![Code Quality](https://img.shields.io/badge/ruff-checked-brightgreen.svg)](https://github.com/astral-sh/ruff)
[![Type Safety](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)
[![CORTEX Health](https://img.shields.io/badge/cortex%20health-60%2F100-orange.svg)](#-cortex-health-score)
[![Tests](https://img.shields.io/badge/tests-passing-success.svg)](./tests)

---

## 🎯 O Que é Este Template?

Este não é apenas um template Python — é um **sistema operacional completo para engenharia de software profissional**. Combina princípios de **SRE (Site Reliability Engineering)**, **Documentation as Code** e **Governance Automation** em uma arquitetura extensível e battle-tested.

### 🧬 Arquitetura em 4 Camadas

O sistema é construído sobre quatro pilares fundamentais:

```
┌──────────────────────────────────────────────────────────────┐
│                         CORTEX CORE                           │
│                                                               │
│  🧠 Neural Layer      🛡️ Guardian Layer    🔄 Automation     │
│  ──────────────       ───────────────      ──────────────    │
│  Vector Search        Config Scanner       Git Sync          │
│  Semantic Index       Security Blocks      Smart Hooks       │
│  ChromaDB             Shadow Detection     Auto-Doc Gen      │
│                                                               │
│  🕸️ Knowledge Layer   ✅ Quality Layer     🔧 DevTools        │
│  ─────────────────    ────────────────     ─────────────     │
│  Link Resolver        100+ Tests          CLI Commands       │
│  Graph Analysis       Mypy Strict         Dev Doctor         │
│  Health Metrics       Ruff Linter         Mock CI Runner     │
│  Bidirectional        Type Safety         Audit Dashboard    │
└──────────────────────────────────────────────────────────────┘
```

**Problemas Resolvidos:**

- 🔒 **Configurações hardcoded?** Guardian bloqueia commits automáticos.
- 🔗 **Links quebrados?** Knowledge Graph detecta e falha o CI.
- 📄 **Documentação órfã?** Health metrics identificam docs isolados.
- 🧪 **Código sem testes?** Audit dashboard rastreia cobertura em tempo real.
- 🔄 **Git sync complexo?** Automação inteligente de merge/rebase.
- 🤖 **Configurar ambiente?** Doctor diagnostica e corrige automaticamente.
- 🧠 **Buscar na documentação?** Neural search com embeddings semânticos.

---

## 🚀 Como Usar Este Template

Este projeto é um **template Copier** que permite criar novos projetos Python profissionais com toda a infraestrutura já configurada.

### 📦 Instalação do Copier

```bash
# Instalar Copier (recomendado via pipx para isolamento)
pipx install copier

# Ou via pip
pip install copier
```

### 🆕 Criar Novo Projeto

```bash
# Criar novo projeto a partir deste template
copier copy gh:Ismael-1712/python-template-profissional meu-novo-projeto

# Responder às perguntas interativas:
# - Nome do projeto
# - Autor
# - Versão do Python
# - Habilitar Docker/MkDocs, etc.

cd meu-novo-projeto
make install-dev                    # Configurar ambiente
```

### 🔄 Atualizar Projeto Existente

```bash
# Atualizar projeto criado a partir deste template
cd meu-projeto
copier update

# O sistema de toml-fusion preservará suas customizações
# enquanto aplica as melhorias do template
```

**Benefícios:**

- ✅ Setup completo em < 2 minutos
- ✅ Todas as ferramentas pré-configuradas (Ruff, Mypy, pre-commit)
- ✅ Infraestrutura SRE pronta para produção
- ✅ Updates inteligentes que preservam suas modificações

---

## ⚡ Comandos Rápidos (Quick Reference)

### 🎬 Setup Inicial (Desenvolvimento do Template)

```bash
# Clonar e configurar ambiente completo (< 2 minutos)
git clone {{ repository_url }}.git
cd {{ project_slug | replace('_', '-') }}
make install-dev                    # Cria .venv, instala deps, configura hooks
source .venv/bin/activate            # Ativar ambiente virtual
make doctor                          # Verificar saúde do ambiente
```

### 🔨 Desenvolvimento Diário

```bash
# Validação completa antes de commit
make validate                        # Quality Gate Unificado (Fonte Única da Verdade)

# Atalhos úteis
make format                          # Auto-formatar código (ruff)
make test                            # Rodar testes (436 testes, ~5s)
make tdd-check                       # Verificar cobertura delta (TDD Guardian)
make audit                           # Gerar dashboard de qualidade

# Commit inteligente (auto-formatting + hooks)
make save m="feat: add new feature"

# Commit com amend (auto-stage de arquivos voláteis)
make commit-amend
```

### 📦 Gerenciamento de Dependências

```bash
# Adicionar dependência de desenvolvimento
echo "black==24.1.0" >> requirements/dev.in
pip-compile --output-file requirements/dev.txt requirements/dev.in
make install-dev

# Sincronizar ambiente com lockfile (recomendado após git pull)
make sync                            # Usa .venv/bin/pip-sync para garantir sincronia exata

# Verificar estado do ambiente virtual
make check-venv                      # Diagnóstico: Python path, versões, pip-tools

# Atualizar todas as dependências
pip-compile --upgrade --output-file requirements/dev.txt requirements/dev.in

# ⚠️ IMPORTANTE: Sempre commite dev.in E dev.txt juntos!
git add requirements/dev.in requirements/dev.txt

# 📖 Guia completo: docs/guides/DEPENDENCY_MANAGEMENT.md
```

### 🧠 CORTEX — Comandos Essenciais

```bash
# === Knowledge Management ===
cortex audit docs/                   # Validar docs (frontmatter + links)
cortex audit --links --strict        # Modo CI (falha em broken links)
cortex init docs/guides/new-doc.md   # Adicionar frontmatter YAML
cortex map                           # Gerar .cortex/context.json (com knowledge)
cortex map --no-knowledge            # Gerar contexto sem regras de projeto
cortex knowledge-scan                # Listar todas as regras de projeto
cortex knowledge-sync --all          # Sincronizar regras de fontes remotas
# 📖 Guia completo: docs/guides/KNOWLEDGE_NODE.md

# === Guardian (Security) ===
cortex guardian check .              # Detectar configs hardcoded
cortex guardian probe                # Probe interativo

# === Neural Search (AI Powered) ===
cortex neural index                  # Indexar docs com IA (ChromaDB)
cortex neural index --memory-type ram # Modo RAM (sem persistência)
cortex neural ask "query"            # Busca semântica inteligente
cortex neural ask "query" --top 10   # Top 10 resultados
# 📖 Guia completo: docs/guides/NEURAL_CORTEX.md (ou seção README)
```

### 🐛 Diagnóstico e Troubleshooting

```bash
make doctor                          # Diagnóstico completo do ambiente
make clean                           # Limpar cache e artefatos
rm -rf .venv && make install-dev     # Reinstalação completa
cortex audit --links                 # Checar integridade de links
python -m pytest -vv tests/          # Debug de testes
```

### 📊 Relatórios e Métricas

```bash
make audit                           # Gerar audit_dashboard.html
cat docs/reports/KNOWLEDGE_HEALTH.md # Health do knowledge graph
cat .cortex/context.json             # Mapa completo do projeto
make test-coverage                   # Cobertura de testes
make mutation target=scripts/file.py # Mutation testing (local)
make mutation-report                 # Visualizar relatório HTML de mutation
```

**🧟 Mutation Testing:** Valida a qualidade dos seus testes. Consulte [Guia de Mutation Testing](docs/guides/MUTATION_TESTING.md) para detalhes.

### 🔄 Git & CI/CD

```bash
git-sync                             # Sincronizar com remoto (com auditoria)
git-sync --dry-run                   # Preview de mudanças
python -m scripts.cli.mock_ci        # Rodar pipeline CI localmente
make commit MSG="fix: bug"           # Commit com smart hooks
```

### 🌍 Internacionalização

```bash
make i18n-extract                    # Extrair strings traduzíveis
make i18n-init LOCALE=en_US          # Criar novo idioma
make i18n-update                     # Atualizar catálogos
make i18n-compile                    # Compilar .po → .mo
LANGUAGE=en_US cortex --help         # Rodar em inglês
```

### 📚 Documentação

```bash
make docs-serve                      # Servidor local (localhost:8000)
make docs-build                      # Build estático (pasta site/)
cat docs/architecture/CORTEX_INDICE.md  # Índice completo (115 docs)
```

---

## ✨ Features Completas

### 🧠 **Neural Cortex (AI Powered) — Semantic Search & Vector Memory**

**Sistema de busca semântica e memória de longo prazo usando IA real (SentenceTransformers) e persistência vetorial (ChromaDB).**

#### 🚀 Capacidades

- **Busca Semântica Inteligente**: Encontre documentação por conceito, não apenas palavras-chave
- **Memória de Longo Prazo**: ChromaDB persiste embeddings no disco (`.cortex/memory`)
- **Real AI Embeddings**: SentenceTransformers (`all-MiniLM-L6-v2`) para vetorização semântica
- **Arquitetura Hexagonal**: Ports & Adapters para trocar embedding engines ou vector stores
- **Fallback Graceful**: Sistema detecta quando IA não está disponível e alerta o usuário

#### 📦 Instalação

O sistema Neural é instalado automaticamente com as dependências de desenvolvimento:

```bash
# Instalar dependências completas (inclui IA)
make install-dev

# Ou manualmente
pip install -r requirements/dev.txt

# Dependências principais:
# - sentence-transformers: Embeddings semânticos
# - chromadb: Vector database persistente
# - torch: Backend para modelos de IA
```

#### 🎯 Uso Básico

```bash
# 1. Indexar toda a documentação
cortex neural index --memory-type chroma

# Banner exibe status do sistema:
# 🧠 CORTEX Neural System Status
# Motor Cognitivo: 🟢 SentenceTransformers (Real AI)
# Memória:        🟢 ChromaDB (Persistent)
# Modelo:         all-MiniLM-L6-v2
# Caminho:        .cortex/memory

# 2. Fazer perguntas em linguagem natural
cortex neural ask "Como funciona a arquitetura hexagonal?"

# 3. Buscar casos de uso específicos
cortex neural ask "Exemplos de testes com mocks"

# 4. Opções avançadas
cortex neural index --memory-type ram    # Usar RAM em vez de ChromaDB
cortex neural ask "query" --top 10       # Retornar 10 resultados
cortex neural ask "query" --db .custom   # Usar diretório customizado
```

#### 🏗️ Arquitetura Hexagonal

O Neural Cortex segue **Arquitetura Hexagonal** (Ports & Adapters):

```
┌─────────────────────────────────────────┐
│         VectorBridge (Core Logic)       │
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │ EmbeddingPort│    │VectorStorePort│ │
│  └──────┬───────┘    └──────┬────────┘ │
└─────────┼──────────────────┼───────────┘
          │                  │
     ┌────▼────┐       ┌─────▼──────┐
     │Adapters │       │  Adapters  │
     │─────────│       │────────────│
     │Sentence │       │  ChromaDB  │
     │Transform│       │  InMemory  │
     │Placeholder      │  (Future)  │
     └─────────┘       └────────────┘
```

**Benefícios:**

- ✅ **Substituível**: Trocar SentenceTransformers por OpenAI embeddings sem mudar lógica
- ✅ **Testável**: Mocks triviais para ports
- ✅ **Extensível**: Adicionar Pinecone/Weaviate apenas implementando `VectorStorePort`

**Gerar Diagramas:**

```bash
python scripts/docs/HEXAGONAL_VALIDATOR_DIAGRAMS.py
```

Documentação arquitetural completa em [`docs/architecture/`](docs/architecture/).

#### 🎛️ Modos de Operação

**🟢 Modo Produção (AI Real + Persistência)**

```bash
cortex neural index --memory-type chroma
# Motor Cognitivo: 🟢 SentenceTransformers (Real AI)
# Memória:        🟢 ChromaDB (Persistent)
```

**⚠️ Modo Fallback (Placeholder + RAM)**

```bash
# Se sentence-transformers não estiver instalado:
cortex neural index --memory-type ram
# Motor Cognitivo: ⚠️  Placeholder (Dummy Mode)
# Memória:        ⚠️  RAM (Volatile + JSON)
```

**Verbose by Default:** O banner de status SEMPRE exibe qual modo está ativo. Elimina "cegueira de ferramenta".

#### 🔧 Casos de Uso

**1. RAG (Retrieval-Augmented Generation)**

```bash
# Indexar documentação
cortex neural index

# Integrar com chatbot (exemplo Python)
from scripts.core.cortex.neural.vector_bridge import VectorBridge
results = bridge.query_similar("Como testar APIs?", limit=3)
context = "\n".join([r.chunk.content for r in results])
# Passar context para GPT-4/Claude
```

**2. Descoberta de Padrões**

```bash
cortex neural ask "Exemplos de dependency injection"
cortex neural ask "Como implementar observers?"
```

**3. Onboarding de Desenvolvedores**

```bash
cortex neural ask "Por onde começar no projeto?"
cortex neural ask "Como rodar testes localmente?"
```

#### 📊 Performance

- **Indexação**: ~100 docs/segundo (depende do hardware e modelo)
- **Busca**: < 100ms para 1000+ documentos
- **Memória**: Embeddings armazenados em disco (não consome RAM)
- **Modelo**: 384 dimensões, ~80MB em disco

#### 🛠️ Troubleshooting

**Erro: "Using placeholder embedding service"**

```bash
# Instalar dependências de IA
pip install sentence-transformers torch

# Verificar instalação
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
```

**Erro: "ChromaDB not installed"**

```bash
pip install chromadb
```

**Banco de dados corrompido:**

```bash
rm -rf .cortex/memory
cortex neural index  # Re-indexar do zero
```

---

### 🛡️ **Guardian Layer — Security & Configuration Governance**

**Sistema de governança que bloqueia configurações perigosas e garante conformidade.**

#### 🔍 Guardian Scanner

Detecta configurações hardcoded via análise AST:

```bash
# Escanear projeto completo
cortex guardian check .

# Modo CI (falha em findings críticos)
cortex guardian check . --fail-on-error

# Probe interativo
cortex guardian probe
```

**O que detecta:**

- ✅ `os.getenv("SECRET")` sem valor default
- ✅ `os.environ.get("API_KEY")` em código produção
- ✅ `os.environ["PASSWORD"]` (subscript direto)
- ✅ Configurações em `.env` não documentadas

**Whitelist:**
Adicione exceções em `.guardian-whitelist.yaml`:

```yaml
whitelist:
  - HOME
  - PATH
  - PYTHONPATH
```

#### 🧠 Hallucination Probe

Detecta discrepâncias entre documentação e código:

```bash
# Validar documentação vs implementação
cortex guardian probe --check-consistency
```

**Bloqueios Automáticos:**

- ❌ Commit de código com secrets hardcoded
- ❌ Documentação de features não implementadas
- ❌ Configuração de hooks sem idempotência

---

### 🕸️ **Knowledge Layer — Documentation Graph & Link Analysis**

**Sistema de grafo de conhecimento com validação bidirecional de links e sincronização de regras remotas.**

#### 🧠 Knowledge Node (Novo!)

**Sistema de gerenciamento de regras de projeto com sincronização remota e preservação de customizações locais.**

**O que resolve:**

- 📚 **Regras centralizadas**: Unifica padrões de projeto em `docs/knowledge/`
- 🔄 **Sync remoto**: Baixa regras de wikis, GitHub, Notion automaticamente
- 🛡️ **Proteção local**: Preserva customizações com marcadores `<!-- GOLDEN_PATH_START/END -->`
- 🤖 **LLM Context**: Enriquece `.cortex/context.json` com regras para GitHub Copilot/GPT-4

**Comandos:**

```bash
# Listar todas as regras de projeto
cortex knowledge-scan

# Sincronizar regras de fontes remotas
cortex knowledge-sync --all

# Gerar contexto para LLMs (com regras)
cortex map --include-knowledge

# Ver o que foi incluído
cat .cortex/context.json | jq '.knowledge_rules'
```

**Estrutura de um Knowledge Entry:**

```yaml
---
id: kno-auth-001
status: active
tags: [authentication, security]
golden_paths:
  - "src/app/auth/jwt.py -> docs/guides/auth.md"
sources:
  - url: "https://wiki.company.com/auth-standards.md"
    type: documentation
---

# Authentication Standards

Conteúdo sincronizado da wiki corporativa...

<!-- GOLDEN_PATH_START -->
## 🏢 Customizações Internas
Nossa empresa usa Azure AD B2C.
Esta seção NÃO será sobrescrita no sync.
<!-- GOLDEN_PATH_END -->
```

**📖 Guia Completo**: [docs/guides/KNOWLEDGE_NODE.md](docs/guides/KNOWLEDGE_NODE.md)

---

#### 📝 Frontmatter YAML Obrigatório

Todo documento deve ter metadados estruturados:

```yaml
---
id: my-document
type: guide               # guide | arch | reference | history
status: active            # draft | active | deprecated
version: 1.0.0
author: Engineering Team
date: '2025-12-15'
context_tags: [python, testing, ci-cd]
linked_code: [scripts/core/cortex/models.py]
---
```

**Comandos:**

```bash
# Adicionar frontmatter automaticamente
cortex init docs/guides/my-guide.md

# Forçar sobrescrever frontmatter existente
cortex init docs/guides/my-guide.md --force

# Migrar documentos legados
cortex migrate docs/ --interactive
```

#### 🔍 Link Scanner & Resolver

Extrai e valida todos os links na documentação:

```bash
# Auditar integridade de links
cortex audit --links

# Modo estrito (falha CI em broken links)
cortex audit --links --strict

# Gerar relatório de saúde
cortex audit --links --output docs/reports/KNOWLEDGE_HEALTH.md
```

**Tipos de Links Suportados:**

- `[Markdown](docs/guide.md)` → Markdown links
- `[[Wikilink]]` → Wiki-style links
- `[[Alias|Target]]` → Wikilinks com alias
- `scripts/core/models.py` → Referências a código

**Exemplo de Output:**

```markdown
# 📊 Knowledge Graph Health Report

**Overall Health Score:** 75.0/100 (🟡 Warning)

## Métricas

| Metric              | Value    | Status |
|---------------------|----------|--------|
| Total Nodes         | 45       | -      |
| Valid Links         | 120      | 🟢     |
| Broken Links        | 3        | 🔴     |
| Orphaned Documents  | 2        | 🟡     |
| Connectivity Score  | 82.5%    | 🟢     |

## 🔴 Broken Links

- `docs/guides/deprecated.md` → `scripts/old/removed.py` (MISSING)
```

#### 📊 Health Metrics

O sistema calcula automaticamente:

- **Connectivity Score**: % de documentos com links bidirecionais
- **Link Health Score**: % de links válidos vs. quebrados
- **Overall Health**: Score agregado (0-100)

**Thresholds:**

- 🟢 80-100: Excelente
- 🟡 60-79: Atenção
- 🔴 0-59: Crítico

---

### 🔄 **Automation Layer — Smart Tools & Git Sync**

#### 🔄 Git Sync Inteligente

Sincronização automática de branches com auditoria preventiva:

```bash
# Sincronizar com branch remota
git-sync

# Dry-run (preview de mudanças)
git-sync --dry-run

# Configuração customizada
git-sync --config custom_sync.yaml
```

**Funcionalidades:**

- ✅ Detecção automática de estratégia (merge vs. rebase)
- ✅ Auditoria de código antes do push
- ✅ Rollback automático em caso de conflitos
- ✅ Relatórios estruturados em JSON

**Configuração (`smart_git_sync_config.yaml`):**

```yaml
sync:
  default_strategy: merge  # ou 'rebase'
  auto_push: false
  audit_before_push: true
```

#### 🔧 Smart Governance Hooks

**Idempotência garantida** — Hooks podem rodar múltiplas vezes sem efeitos colaterais.

**Hooks Automáticos:**

1. **code-audit-security**: Auditoria de segurança em arquivos Python alterados
2. **cortex-audit**: Validação de documentação
3. **cortex-guardian**: Bloqueio de shadow configuration
4. **auto-doc-gen**: Geração automática de CLI docs
5. **cortex-neural-sync**: Sincronização do vector store

**Configuração (`.pre-commit-config.yaml`):**

```yaml
repos:
  - repo: local
    hooks:
      - id: cortex-guardian
        name: "CORTEX Guardian - Bloqueia Shadow Configuration"
        entry: python3 -m scripts.cli.cortex guardian check . --fail-on-error
        language: system
        types: [python]
```

---

### ✅ **Quality Layer — Testing & Validation**

#### 🧪 Testing Suite

**100+ testes unitários** cobrindo todos os módulos críticos:

```bash
# Rodar todos os testes
make test

# Testes em modo verboso
make test-verbose

# Testes com cobertura
make test-coverage

# Validar cobertura delta (TDD Guardian - CI)
make test-delta

# Matriz de versões Python (tox)
make test-matrix
```

**TDD Guardian - Aplicação Obrigatória de Testes:**

Este projeto implementa o **TDD Guardian**, um mecanismo de duas camadas que garante a presença de testes para todo código novo:

1. **Hook de Pre-commit (Estrutural) - Configurável para Múltiplos Diretórios**:

   O TDD Guardian agora suporta monitoramento de múltiplos diretórios com diferentes políticas de enforcement:

   - **`src/` (Modo STRICT)**: Bloqueia commits se testes estiverem faltando
     - `src/main.py` → **REQUER** `tests/test_main.py`
     - `src/core/utils.py` → **REQUER** `tests/core/test_utils.py`

   - **`scripts/` (Modo WARN-ONLY)**: Emite avisos mas não bloqueia commits
     - `scripts/deploy.py` → **RECOMENDA** `tests/scripts/test_deploy.py`
     - `scripts/cli/doctor.py` → **RECOMENDA** `tests/scripts/cli/test_doctor.py`

   - Arquivos `__init__.py` são ignorados automaticamente em ambos os modos

   **Uso Manual do Guardian:**

   ```bash
   # Modo padrão (strict, apenas src/)
   python scripts/hooks/tdd_guardian.py src/api.py

   # Monitorar múltiplos diretórios
   python scripts/hooks/tdd_guardian.py --dirs src scripts -- file1.py file2.py

   # Modo warn-only (não bloqueia)
   python scripts/hooks/tdd_guardian.py --warn-only scripts/deploy.py
   ```

2. **Validação de Cobertura Delta (CI)**: O comando `make test-delta` executa `diff-cover` com `--fail-under=100`, exigindo que **todo código modificado/adicionado** tenha 100% de cobertura de testes.

**Arquivos de Testes:**

- `test_cortex_*.py` — Testes do Knowledge Layer
- `test_guardian_*.py` — Testes do Guardian
- `test_link_*.py` — Testes de resolução de links
- `test_mock_ci_*.py` — Testes do Mock CI Runner
- `test_tdd_guardian.py` — Testes do TDD Guardian (meta-teste)

#### 🔬 Type Safety (Mypy Strict)

Verificação de tipos em modo estrito:

```bash
# Type checking completo
make type-check

# Apenas scripts
mypy scripts/

# Com relatório HTML
mypy scripts/ --html-report mypy-report/
```

**Configuração (`pyproject.toml`):**

```toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

#### 🎨 Code Quality (Ruff)

Linting e formatação automática:

```bash
# Lint apenas (check)
make lint

# Formatar código
make format

# Validação completa (lint + type-check + test)
make validate
```

#### 🛡️ Architectural Guardrails (Quality Suite)

**Tríade de Blindagem Arquitetural** com validação automatizada:

```bash
# Validação completa (executa todas as verificações abaixo)
make validate                   # ⭐ Quality Gate Unificado - Fonte Única da Verdade

# Verificações individuais (na ordem de execução do validate):
make format                     # Ruff: Auto-formatação + lint fixes
make deps-check                 # Verificação de sincronização requirements.in → .txt
make lint                       # Ruff: Estilo de código + McCabe complexity (C901)
make type-check                 # Mypy: Type safety estrito
make complexity-check           # Xenon: Complexidade ciclomática ≤ 10
make arch-check                 # Import Linter: Separação de camadas arquiteturais
make docs-check                 # Interrogate: Cobertura de docstrings (≥95%)
make ci-check                   # GitHub Actions workflows audit (versões + cache)
make audit-custom               # Auditoria de segurança customizada (fail-on: HIGH severity)
make security-sast              # Bandit: Static Application Security Testing
make security-sca               # Safety: Software Composition Analysis
make audit-security             # Suite completa de segurança (Custom + SAST + SCA)
make guardian-check             # Guardian: Políticas arquiteturais (shadow config detection)
make cortex-audit               # CORTEX: Integridade de documentação (links + frontmatter)
make test                       # Pytest: Suite de testes completa (779 testes)
make tdd-check                  # TDD Guardian: Cobertura delta 100% (código novo)
```

**Pipeline de Validação (Quality Gate):**

```
format → deps-check → lint → type-check → complexity-check → arch-check →
  docs-check → ci-check → audit-security → guardian-check → cortex-audit →
  test → tdd-check
    ↓         ↓         ↓        ↓              ↓               ↓
  Ruff     Verify   Ruff     Mypy          Xenon       Import Linter
                                                              ↓
                                                        Interrogate → GitHub Audit →
                                                        Security Audit → Guardian →
                                                        CORTEX → Pytest → diff-cover
```

**Métricas de Qualidade:**

| Pilar | Ferramenta | Threshold | Status Atual |
|-------|-----------|-----------|--------------|
| 🧠 **Complexidade** | Xenon | CC ≤ 10 | ✅ PASSED |
| 🏗️ **Arquitetura** | Import Linter | 0 violações novas | ⚠️ 1 baseline |
| 🧹 **Higiene** | Deptry | 0 deps não usadas | ✅ PASSED |
| 📚 **Documentação** | Interrogate | Cobertura ≥ 95% | ✅ 99.1% |
| 🎯 **Type Safety** | Mypy | Strict mode | ✅ PASSED |
| ✅ **Testes** | Pytest | 100% passing | ✅ 779/780 |
| 🛡️ **TDD Guardian** | diff-cover | Delta Coverage = 100% | ✅ ACTIVE |
| 🔒 **Segurança Custom** | Audit CLI | Fail-on HIGH | ✅ MONITORED |
| 🔐 **SAST** | Bandit | Code vulnerabilities | ✅ ACTIVE |
| 🔐 **SCA** | Safety | Dependency vulnerabilities | ✅ ACTIVE |
| 🛡️ **Guardian** | Config Scanner | Shadow detection | ✅ ACTIVE |
| 📄 **CORTEX** | Knowledge Graph | Links + metadata | ✅ VALIDATED |

**Estratégia de Baseline (Grandfathering):**

- Código legado tolerado (exit 0 em violações)
- Novas violações **bloqueiam** o build
- Meta: Melhoria contínua sem quebrar CI

---

### 🔧 **DevTools Layer — CLI & Utilities**

#### 🏥 Dev Doctor — Diagnostic Tool

Diagnóstico completo do ambiente de desenvolvimento:

```bash
# Executar diagnóstico
make doctor

# Ou diretamente
python -m scripts.cli.doctor
```

**O que verifica:**

- ✅ Versão do Python
- ✅ Dependências instaladas
- ✅ Git configurado corretamente
- ✅ Hooks pre-commit ativos
- ✅ Permissões de escrita
- ✅ Variáveis de ambiente necessárias

**Output Exemplo:**

```
🏥 Dev Doctor - Environment Diagnostic

✅ Python 3.11.5 detected
✅ Virtual environment active (.venv)
✅ Git repository initialized
⚠️  Pre-commit hooks not installed
❌ Missing environment variable: DATABASE_URL

Recommendations:
  • Run: pre-commit install
  • Set DATABASE_URL in .env file
```

#### 🧪 Mock CI Runner

Simulador de ambiente CI para testes locais:

```bash
# Gerar configuração inicial (scaffolding)
mock-ci init                         # Cria test_mock_config.yaml com comentários
mock-ci init --force                 # Sobrescreve configuração existente
mock-ci init --output custom.yaml    # Salva em arquivo customizado

# Rodar mock CI completo
python -m scripts.cli.mock_ci

# Gerar mocks de configuração
python -m scripts.cli.mock_generate

# Validar mocks existentes
python -m scripts.cli.mock_validate
```

**Casos de Uso:**

- 🆕 **Scaffolding rápido**: `mock-ci init` gera configuração auto-documentada
- Testar workflows GitHub Actions localmente
- Validar scripts CI antes do push
- Debug de falhas em pipelines

#### 📦 Install Dev — Intelligent Dependency Management

Instalação inteligente com cache de hash:

```bash
# Instalar/atualizar ambiente
make install-dev

# Forçar reinstalação
rm -rf .venv && make install-dev
```

**Funcionalidades:**

- ✅ Hash-based caching (evita reinstalações desnecessárias)
- ✅ Compilação automática de `requirements/dev.in` → `dev.txt`
- ✅ Instalação do pacote em modo editable (`pip install -e .`)
- ✅ Configuração de hooks pre-commit
- ✅ Indexação neural automática

#### 🔄 Upgrade Python — Version Manager

Atualização automatizada de versões Python:

```bash
# Verificar patches disponíveis
python -m scripts.cli.upgrade_python

# Atualizar versões (via pyenv)
make upgrade-python
```

**O que faz:**

- 🔍 Detecta versões Python instaladas via pyenv
- 📊 Verifica patches mais recentes disponíveis
- 🔄 Atualiza `.python-version` automaticamente
- ✅ Reinstala ambiente virtual com nova versão

#### 🗺️ CORTEX Mapper

Geração automática de contexto do projeto:

```bash
# Gerar mapa completo
cortex map

# Saída: .cortex/context.json
```

**Conteúdo gerado:**

- 📁 Estrutura de diretórios
- 🛠️ Comandos CLI disponíveis
- 📚 Documentos arquiteturais
- 🔧 Scripts disponíveis
- 📦 Dependências instaladas

**Uso:** LLMs e ferramentas de introspecção consomem `context.json` para entender o projeto automaticamente.

---

### 📊 **Audit Dashboard — Visual Code Quality Metrics**

Painel interativo HTML com métricas de qualidade:

```bash
# Gerar dashboard
make audit

# Saída: audit_dashboard.html
```

**Métricas Incluídas:**

- 📊 Complexidade ciclomática por função
- 📏 Linhas de código por módulo
- 🧪 Cobertura de testes
- 🔒 Vulnerabilidades de segurança
- 📈 Tendências ao longo do tempo

**Gráficos:**

- 🔥 Heatmap de complexidade
- 📉 Evolução de dívida técnica
- 🎯 Top 10 funções mais complexas

---

### 🌍 **Internationalization (i18n)**

Suporte nativo para múltiplos idiomas:

```bash
# Extrair strings traduzíveis
make i18n-extract

# Inicializar novo idioma
make i18n-init LOCALE=en_US

# Atualizar catálogos existentes
make i18n-update

# Compilar traduções
make i18n-compile

# Estatísticas de tradução
make i18n-stats
```

**Idiomas Suportados:**

- 🇧🇷 Português (pt_BR) — Padrão
- 🇺🇸 Inglês (en_US)

**Uso:**

```bash
# Rodar CLI em inglês
LANGUAGE=en_US cortex audit
```

---

## 🚀 Quick Start

### Pré-requisitos

- Python 3.10+ instalado
- Git configurado
- (Opcional) pyenv para gerenciamento de versões Python

### Instalação em 3 Passos

```bash
# 1. Clone o repositório
git clone {{ repository_url }}.git
cd {{ project_slug | replace('_', '-') }}

# 2. Configure o ambiente completo (cria .venv, instala deps, configura hooks)
make install-dev

# 3. Ative o ambiente virtual
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### Verificação da Instalação

```bash
# Verificar saúde do ambiente
make doctor

# Validar instalação completa
cortex --help
cortex map
```

---

## 🛠️ Comandos CLI Essenciais

### CORTEX (Comando Principal)

```bash
# === Documentation Management ===
cortex init <file>                        # Adicionar frontmatter YAML
cortex migrate docs/ --interactive        # Migrar documentos legados
cortex audit docs/                        # Auditar documentação
cortex audit --links                      # Validar grafo de conhecimento
cortex audit --links --strict             # Modo CI (falha em broken links)

# === Guardian (Security & Governance) ===
cortex guardian check .                   # Escanear configurações hardcoded
cortex guardian check . --fail-on-error   # Modo CI
cortex guardian probe                     # Probe interativo

# === Neural Interface ===
cortex neural index                       # Indexar documentação
cortex neural ask "query"                 # Busca semântica

# === Utilities ===
cortex map                                # Gerar mapa de contexto
cortex generate readme                    # Gerar README dinâmico
```

### Makefile (Automação)

```bash
# === Ambiente ===
make setup                     # Alias para install-dev
make install-dev               # Configurar ambiente completo
make clean                     # Remover cache e artefatos
make clean-all                 # Limpeza profunda (remove .venv)

# === Qualidade ===
make validate                  # Lint + Type Check + Tests
make lint                      # Ruff check
make format                    # Ruff format
make type-check                # Mypy strict
make test                      # Pytest completo
make test-verbose              # Testes detalhados
make test-coverage             # Com relatório de cobertura
make test-delta                # Cobertura delta (requer 100% em código novo)

# === Diagnóstico ===
make doctor                    # Diagnóstico de ambiente
make audit                     # Dashboard de qualidade

# === Desenvolvimento ===
make save m="message"          # Format + Add + Commit
make commit MSG="message"      # Commit inteligente com hooks
make commit-amend              # Amend com auto-staging

# === Internacionalização ===
make i18n-extract              # Extrair strings traduzíveis
make i18n-update               # Atualizar catálogos
make i18n-compile              # Compilar traduções

# === Documentação ===
make docs-serve                # Servidor local (localhost:8000)
make docs-build                # Build estático (pasta site/)

# === Utilitários ===
make version                   # Exibir versões
make info                      # Info do ambiente
make upgrade-python            # Atualizar patches Python
```

### Outros Comandos

```bash
# Git Sync
git-sync                       # Sincronizar com remoto
git-sync --dry-run             # Preview de mudanças

# Mock CI
python -m scripts.cli.mock_ci          # Rodar CI localmente
python -m scripts.cli.mock_generate    # Gerar mocks
python -m scripts.cli.mock_validate    # Validar mocks

# Auditoria Standalone
python -m scripts.cli.audit --config scripts/audit_config.yaml
```

---

## 📊 CORTEX Health Score

O sistema se auto-diagnostica continuamente. Score atual:

```json
{
  "health_score": 60.0,
  "status": "critical",
  "metrics": {
    "total_nodes": 0,
    "connectivity_score": 0.0,
    "link_health_score": 100.0,
    "broken_links": 0
  }
}
```

**Como Melhorar o Score:**

1. ✅ **Adicionar links bidirecionais** entre documentos (↑ `connectivity_score`)
2. ✅ **Corrigir links quebrados** com `cortex audit --links` (↑ `link_health_score`)
3. ✅ **Reduzir documentos órfãos** para <5% do total
4. ✅ **Adicionar frontmatter** em todos os `.md` files

**Thresholds:**

- 🟢 **80-100**: Excelente — Grafo saudável e bem conectado
- 🟡 **60-79**: Atenção — Algumas melhorias necessárias
- 🔴 **0-59**: Crítico — Requer ação imediata

---

## 🏗️ Estrutura do Projeto

```
python-template-profissional/
│
├── 🧠 .cortex/                      # CORTEX Brain — Sistema de Conhecimento
│   ├── context.json                # Mapa completo do projeto (auto-gerado)
│   └── vector_store/               # ChromaDB embeddings (neural search)
│
├── 📚 docs/                         # Documentation as Code
│   ├── architecture/               # ADRs e design docs
│   │   ├── CORTEX_INDICE.md       # Índice master das fases
│   │   └── *.md                   # Documentos arquiteturais
│   ├── guides/                     # Manuais de uso
│   ├── reference/                  # Referência de APIs/CLIs
│   │   └── CLI_COMMANDS.md        # 🔄 Auto-gerado via hooks
│   ├── reports/                    # Relatórios de auditoria
│   ├── templates/                  # 🆕 Templates Jinja2 (README, etc.)
│   ├── history/                    # Histórico de sprints
│   └── knowledge/                  # Knowledge base adicional
│
├── 🛠️ scripts/                      # Ferramentas de Engenharia
│   ├── cli/                        # 🎯 Comandos de Terminal (Typer)
│   │   ├── cortex.py              # 🧠 CORTEX CLI principal
│   │   ├── neural.py              # 🤖 Neural interface & semantic search
│   │   ├── audit.py               # 🔍 Auditoria de código
│   │   ├── doctor.py              # 🏥 Diagnóstico de ambiente
│   │   ├── git_sync.py            # 🔄 Git sync inteligente
│   │   ├── mock_ci.py             # 🧪 Mock CI runner
│   │   ├── install_dev.py         # 📦 Dependency manager
│   │   └── upgrade_python.py      # 🐍 Python version updater
│   │
│   ├── core/                       # 🏛️ Bibliotecas Core
│   │   ├── cortex/                # 🧠 Knowledge System
│   │   │   ├── models.py          # Pydantic models (KnowledgeEntry, KnowledgeLink)
│   │   │   ├── scanner.py         # Link scanner (AST + Regex)
│   │   │   ├── link_resolver.py   # Link resolution & validation
│   │   │   ├── knowledge_validator.py  # Graph validator
│   │   │   ├── mapper.py          # Context map generator
│   │   │   ├── metadata.py        # Frontmatter parser
│   │   │   ├── migrate.py         # Document migrator
│   │   │   ├── readme_generator.py # Dynamic README generator
│   │   │   └── neural/            # 🤖 Neural Layer
│   │   │       ├── vector_bridge.py   # ChromaDB interface
│   │   │       └── models.py          # Embedding models
│   │   │
│   │   ├── guardian/              # 🛡️ Governance System
│   │   │   ├── scanner.py         # AST-based config scanner
│   │   │   ├── matcher.py         # Documentation matcher
│   │   │   ├── hallucination_probe.py  # Consistency checker
│   │   │   └── models.py          # Guardian data models
│   │   │
│   │   └── doc_gen.py             # Auto-doc generator (CLI reference)
│   │
│   ├── utils/                      # 🔧 Utilitários
│   │   ├── logger.py              # Logging estruturado
│   │   ├── context.py             # Context managers
│   │   ├── filesystem.py          # Abstração de I/O
│   │   └── security.py            # Utilities de segurança
│   │
│   ├── audit/                      # 📊 Audit System
│   │   └── analyzer.py            # Code quality analyzer
│   │
│   └── git_sync/                   # 🔄 Git Sync Module
│       ├── orchestrator.py        # Sync orchestration
│       └── exceptions.py          # Custom exceptions
│
├── 📦 src/                          # Aplicação Principal
│   └── main.py                     # Entry point
│
├── ✅ tests/                        # Test Suite (100+ testes)
│   ├── test_cortex_*.py           # Testes CORTEX
│   ├── test_guardian_*.py         # Testes Guardian
│   ├── test_link_*.py             # Testes Link Resolution
│   ├── test_neural_*.py           # Testes Neural Layer
│   └── conftest.py                # Pytest fixtures
│
├── 📋 requirements/                 # Gerenciamento de Dependências
│   ├── dev.in                     # Dependências de desenvolvimento
│   └── dev.txt                    # 🔒 Lockfile (pip-compile)
│
├── ⚙️ Configurações
│   ├── pyproject.toml             # Configuração central (PEP 621)
│   ├── Makefile                   # Comandos de automação
│   ├── .pre-commit-config.yaml    # Hooks de governança
│   ├── mkdocs.yml                 # Documentação site
│   ├── tox.ini                    # Test matrix
│   └── docker-compose.yml         # Containerização
│
└── 📄 Documentação Raiz
    ├── README.md                   # 🆕 Este arquivo (gerado dinamicamente)
    ├── CONTRIBUTING.md             # Guia de contribuição
    ├── CHANGELOG.md                # Histórico de versões
    ├── CODE_OF_CONDUCT.md          # Código de conduta
    └── SECURITY.md                 # Política de segurança
```

### 🎯 Diretórios Críticos

| Diretório | Propósito | Auto-Gerado? |
|-----------|-----------|--------------|
| `.cortex/` | Metadados do Knowledge System | ✅ Sim |
| `docs/reference/CLI_COMMANDS.md` | Referência de comandos CLI | ✅ Sim (hook) |
| `audit_dashboard.html` | Dashboard de qualidade | ✅ Sim (`make audit`) |
| `docs/reports/` | Relatórios de auditoria | ✅ Sim (`cortex audit`) |
| `.cortex/vector_store/` | Embeddings ChromaDB | ✅ Sim (`cortex neural index`) |

---

## 🎓 Casos de Uso Reais

### 🔍 Caso 1: Onboarding de Novo Desenvolvedor

```bash
# 1. Clonar e configurar
git clone <repo> && cd <repo>
make install-dev

# 2. Entender o projeto
cortex map
cat .cortex/context.json

# 3. Explorar documentação semanticamente
cortex neural ask "Como funciona o sistema de auditoria?"

# 4. Validar ambiente
make doctor
```

### 🔒 Caso 2: Detectar Configurações Hardcoded

```bash
# Escanear projeto completo
cortex guardian check .

# Output:
# ❌ HIGH: os.getenv("SECRET_KEY") without default in src/config.py:42
# ⚠️  MEDIUM: os.environ.get("API_URL") in scripts/deploy.py:15
```

### 📚 Caso 3: Auditar Documentação Antes do Deploy

```bash
# Validar links e gerar relatório
cortex audit --links --output docs/reports/pre-deploy-audit.md

# Falhar CI se score < 80
cortex audit --links --strict --min-score 80
```

### 🔄 Caso 4: Sincronizar com Branch Principal

```bash
# Preview de mudanças
git-sync --dry-run

# Executar sync com auditoria
git-sync

# Output:
# ✅ Audit passed (0 critical issues)
# ✅ Merged main into feature-branch
# ✅ Pushed to origin/feature-branch
```

### 🧪 Caso 5: Testar CI Localmente

```bash
# Rodar pipeline completo
python -m scripts.cli.mock_ci

# Validar apenas linting
python -m scripts.cli.mock_ci --stage lint
```

---

## 🧪 Showcase: Poder do CORTEX

### 📊 Exemplo 1: Auditoria Automática de Links

```bash
$ cortex audit --links

🔍 Scanning knowledge graph...
✅ Loaded 45 knowledge nodes
🔗 Extracted 120 links
📊 Resolving targets...

📈 Health Metrics:
  Connectivity Score: 82.5%
  Link Health Score:  97.5%
  Overall Health:     75.0/100

📄 Report generated: docs/reports/KNOWLEDGE_HEALTH.md
```

**Casos de Uso para `cortex audit`:**

```bash
# Auditoria completa de documentação (frontmatter, links, órfãos)
cortex audit docs/

# Auditoria apenas de links (sem validar frontmatter)
cortex audit --links

# Modo estrito - falha CI se encontrar broken links
cortex audit --links --strict

# Gerar relatório HTML de saúde
cortex audit --links --output docs/reports/KNOWLEDGE_HEALTH.md

# Falhar se score < threshold
cortex audit --links --min-score 80
```

### 🕸️ Exemplo 2: Inversão de Grafo (Inbound Links)

**Antes (Outbound):**

```
CORTEX_FASE03_DESIGN.md → [models.py, link_resolver.py]
CORTEX_INDICE.md → [CORTEX_FASE03_DESIGN.md]
```

**Depois (Inbound):**

```
models.py ← [CORTEX_FASE03_DESIGN.md, CORTEX_INDICE.md, GUIDE_MODELS.md]
link_resolver.py ← [CORTEX_FASE03_DESIGN.md]
CORTEX_FASE03_DESIGN.md ← [CORTEX_INDICE.md]
```

**Insight:** `models.py` é um **Hub Node** (muito citado) → documentação crítica que requer atenção especial.

### 🤖 Exemplo 3: Busca Semântica Neural

```bash
$ cortex neural ask "Como configurar hooks do git?"

🔍 Searching documentation...

Top 3 Results:

1. docs/guides/CORTEX_AUTO_HOOKS.md (relevance: 95%)
   "Configure pre-commit hooks for automatic validation..."

2. docs/architecture/SMART_GOVERNANCE.md (relevance: 87%)
   "Idempotent hooks ensure safe re-execution..."

3. .pre-commit-config.yaml (relevance: 72%)
   "repos: - repo: local hooks: - id: cortex-audit..."
```

### 🛡️ Exemplo 4: Guardian Bloqueando Commit

```bash
$ git commit -m "Add config"

[cortex-guardian] Checking for shadow configuration...
❌ FAILED: Found 2 HIGH severity configuration issues

Issues:
  • src/app.py:15 - os.getenv("SECRET_KEY") without default
  • src/db.py:8 - os.environ["DATABASE_URL"] (subscript access)

Fix these issues before committing or add to .guardian-whitelist.yaml
```

---

## 📚 Documentação Completa

### 📖 Guias de Uso

| Documento | Descrição |
|-----------|-----------|
| [KNOWLEDGE_NODE_MANUAL.md](docs/guides/KNOWLEDGE_NODE_MANUAL.md) | Manual completo do sistema de Knowledge Nodes |
| [CORTEX_AUTO_HOOKS.md](docs/guides/CORTEX_AUTO_HOOKS.md) | Guia de hooks automáticos e governança |
| [PROTECTED_BRANCH_WORKFLOW.md](docs/guides/PROTECTED_BRANCH_WORKFLOW.md) | Fluxo Git completo com branch protegida e auto-propagação |
| [TESTING_STRATEGY_MOCKS.md](docs/guides/TESTING_STRATEGY_MOCKS.md) | Estratégia anti-I/O com mocks estritos (SRE Standard) |
| [REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md](docs/guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md) | Protocolo de refatoração segura para LLMs |

### 🏛️ Documentação Arquitetural

| Documento | Descrição |
|-----------|-----------|
| [CORTEX_INDICE.md](docs/architecture/CORTEX_INDICE.md) | Índice master das Fases 1-3 |
| [CORTEX_RESUMO_EXECUTIVO.md](docs/architecture/CORTEX_RESUMO_EXECUTIVO.md) | Executive Summary da Fase 1 |
| [CORTEX_FASE03_VALIDATOR_EXECUTIVE_SUMMARY.md](docs/architecture/CORTEX_FASE03_VALIDATOR_EXECUTIVE_SUMMARY.md) | Executive Summary da Fase 3 (Knowledge Validator) |
| [ARCHITECTURE_TRIAD.md](docs/architecture/ARCHITECTURE_TRIAD.md) | Arquitetura de branches (main/cli/api) |
| [SECURITY_STRATEGY.md](docs/architecture/SECURITY_STRATEGY.md) | Estratégia de segurança Defense in Depth |
| [AUDIT_DASHBOARD_INTEGRATION.md](docs/architecture/AUDIT_DASHBOARD_INTEGRATION.md) | Integração do Dashboard de Auditoria com CLI |
| [DEPENDENCY_DIAGRAM_SNAPSHOT.md](docs/architecture/DEPENDENCY_DIAGRAM_SNAPSHOT.md) | Snapshot de diagramas de dependências |
| [CORTEX_FASE03_README.md](docs/architecture/CORTEX_FASE03_README.md) | README geral da Fase 03 |
| [CORTEX_FASE03_EXECUTIVE_SUMMARY.md](docs/architecture/CORTEX_FASE03_EXECUTIVE_SUMMARY.md) | Sumário executivo da Fase 03 |
| [CORTEX_FASE03_PRODUCTION_SUMMARY.md](docs/architecture/CORTEX_FASE03_PRODUCTION_SUMMARY.md) | Sumário de produção Fase 03 |
| [CORTEX_FASE04_VECTOR_STORE_DESIGN.md](docs/architecture/CORTEX_FASE04_VECTOR_STORE_DESIGN.md) | Design do Vector Store (Fase 04) |
| [SECURITY_STRATEGY.md](docs/architecture/SECURITY_STRATEGY.md) | Estratégia de segurança Defense in Depth |
| [AUDIT_DASHBOARD_INTEGRATION.md](docs/architecture/AUDIT_DASHBOARD_INTEGRATION.md) | Integração do Dashboard de Auditoria com CLI |
| [DEPENDENCY_DIAGRAM_SNAPSHOT.md](docs/architecture/DEPENDENCY_DIAGRAM_SNAPSHOT.md) | Snapshot de diagramas de dependências |
| [CORTEX_FASE03_README.md](docs/architecture/CORTEX_FASE03_README.md) | README geral da Fase 03 |
| [CORTEX_FASE03_EXECUTIVE_SUMMARY.md](docs/architecture/CORTEX_FASE03_EXECUTIVE_SUMMARY.md) | Sumário executivo da Fase 03 |
| [CORTEX_FASE03_PRODUCTION_SUMMARY.md](docs/architecture/CORTEX_FASE03_PRODUCTION_SUMMARY.md) | Sumário de produção Fase 03 |
| [CORTEX_FASE04_VECTOR_STORE_DESIGN.md](docs/architecture/CORTEX_FASE04_VECTOR_STORE_DESIGN.md) | Design do Vector Store (Fase 04) |

### 🔍 Referência Técnica

| Documento | Descrição |
|-----------|-----------|
| [CLI_COMMANDS.md](docs/reference/CLI_COMMANDS.md) | Referência completa de comandos CLI (auto-gerado) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guia de contribuição ao projeto |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões e mudanças |

---

## 🤝 Contribuindo

Este projeto segue princípios de **SRE (Site Reliability Engineering)** e **Extreme Automation**.

### 🎯 Princípios

1. **Automação First**: Todo processo manual deve ser automatizado
2. **Observabilidade**: Logs estruturados e métricas automáticas em tudo
3. **Type Safety**: Mypy strict obrigatório, sem `# type: ignore`
4. **Documentation as Code**: Frontmatter YAML obrigatório em todos os `.md`
5. **Governance**: Hooks automáticos garantem conformidade antes do commit

### 🔄 Workflow de Contribuição

```bash
# 1. Fork o repositório
git clone https://github.com/<seu-usuario>/python-template-profissional.git
cd python-template-profissional

# 2. Configure o ambiente
make install-dev

# 3. Crie uma branch
git checkout -b feat/minha-feature

# 4. Desenvolva (os hooks rodam automaticamente)
# ... faça suas mudanças ...

# 5. Valide localmente
make validate              # Lint + Type Check + Tests
cortex audit --links       # Valida documentação
make doctor                # Verifica ambiente

# 6. Commit (hooks rodam automaticamente)
git add .
git commit -m "feat: adiciona nova funcionalidade"

# 7. Push e abra PR
git push origin feat/minha-feature
```

### ✅ Checklist de Qualidade

Antes de abrir um PR, certifique-se de que:

- [ ] `make validate` passa sem erros
- [ ] `make test` passa com 100% de sucesso
- [ ] `make doctor` não reporta problemas críticos
- [ ] `cortex audit --links` não detecta broken links
- [ ] Documentação atualizada com frontmatter YAML
- [ ] Testes adicionados para novas funcionalidades
- [ ] Type hints em todas as funções novas
- [ ] Commit messages seguem [Conventional Commits](https://www.conventionalcommits.org/)

### 🚫 O Que NÃO Fazer

- ❌ Adicionar `# type: ignore` sem justificativa sólida
- ❌ Fazer commit de configurações hardcoded (`os.getenv` sem default)
- ❌ Criar documentação `.md` sem frontmatter YAML
- ❌ Pular validação com `git commit --no-verify`
- ❌ Fazer merge direto na `main` sem PR

### 🛠️ Dicas para Desenvolvimento

**Uso do `make save` para commits rápidos:**

```bash
# Formata, adiciona e commita em um comando
make save m="fix: corrige bug no link resolver"
```

**Amend de commits com arquivos voláteis:**

```bash
# Auto-staging de arquivos gerados (audit_metrics.json, CLI_COMMANDS.md)
make commit-amend
```

**Debug de hooks pre-commit:**

```bash
# Rodar hook específico manualmente
PRE_COMMIT=1 python -m scripts.cli.cortex audit docs/

# Desabilitar hooks temporariamente (NÃO recomendado)
git commit --no-verify -m "WIP: trabalho em progresso"
```

---

## 🌍 Internationalization (i18n)

O projeto possui suporte nativo para **Português (pt_BR)** e **Inglês (en_US)**.

### Comandos i18n

```bash
# Extrair strings traduzíveis do código
make i18n-extract

# Inicializar novo idioma
make i18n-init LOCALE=fr_FR

# Atualizar catálogos existentes
make i18n-update

# Compilar traduções (.po → .mo)
make i18n-compile

# Ver estatísticas de tradução
make i18n-stats
```

### Uso em Runtime

```bash
# Rodar CLI em inglês
LANGUAGE=en_US cortex audit

# Configurar permanentemente
export LANGUAGE=en_US
cortex --help
```

---

## 🐳 Containerização

O projeto inclui suporte Docker para ambientes isolados:

```bash
# Build da imagem
docker build -t cortex:latest .

# Rodar container
docker-compose up -d

# Executar comandos dentro do container
docker-compose exec cortex cortex --help
```

**Arquivos:**

- `Dockerfile` — Imagem base Python 3.10+
- `docker-compose.yml` — Orquestração de serviços

---

## 🔧 Troubleshooting

### 📚 Documentação de Diagnóstico

Para problemas específicos, consulte os guias detalhados:

#### Ambiente de Desenvolvimento

- **[DEV_ENVIRONMENT_TROUBLESHOOTING.md](docs/guides/DEV_ENVIRONMENT_TROUBLESHOOTING.md)** — Problemas de configuração de ambiente
- **[OPERATIONAL_TROUBLESHOOTING.md](docs/guides/OPERATIONAL_TROUBLESHOOTING.md)** — Problemas operacionais e runtime
- **[QUICK_IMPLEMENTATION_GUIDE_PRE_COMMIT_FIX.md](docs/guides/QUICK_IMPLEMENTATION_GUIDE_PRE_COMMIT_FIX.md)** — Correção de hooks pre-commit
- **[DEPENDENCY_MAINTENANCE_GUIDE.md](docs/guides/DEPENDENCY_MAINTENANCE_GUIDE.md)** — Guia de manutenção de dependências
- **[DEPENDENCY_MAINTENANCE_GUIDE.md](docs/guides/DEPENDENCY_MAINTENANCE_GUIDE.md)** — Guia de manutenção de dependências

#### Análises e Otimizações

- **[DX_GOVERNANCE_BOTTLENECK_ANALYSIS.md](docs/analysis/DX_GOVERNANCE_BOTTLENECK_ANALYSIS.md)** — Análise de bottlenecks de governança
- **[EXECUTIVE_SUMMARY_DX_OPTIMIZATION.md](docs/analysis/EXECUTIVE_SUMMARY_DX_OPTIMIZATION.md)** — Sumário executivo de otimizações DX

#### Protocolos e Workflows

- **[ATOMIC_COMMIT_PROTOCOL.md](docs/guides/ATOMIC_COMMIT_PROTOCOL.md)** — Protocolo de commits atômicos
- **[PROTECTED_BRANCH_WORKFLOW.md](docs/guides/PROTECTED_BRANCH_WORKFLOW.md)** — Workflow de branches protegidas
- **[POST_PR_MERGE_PROTOCOL.md](docs/guides/POST_PR_MERGE_PROTOCOL.md)** — Protocolo pós-merge de PR
- **[DIRECT_PUSH_PROTOCOL.md](docs/guides/DIRECT_PUSH_PROTOCOL.md)** — Protocolo de push direto

#### Estratégias e Boas Práticas

- **[FAIL_FAST_PHILOSOPHY.md](docs/guides/FAIL_FAST_PHILOSOPHY.md)** — Filosofia Fail Fast
- **[REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md](docs/guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md)** — Protocolos de refatoração
- **[SAFE_SCRIPT_TRANSPLANT.md](docs/guides/SAFE_SCRIPT_TRANSPLANT.md)** — Migração segura de scripts
- **[DEV_PROD_PARITY_STRATEGY.md](docs/guides/DEV_PROD_PARITY_STRATEGY.md)** — Estratégia de paridade dev/prod

#### Histórico e Lições Aprendidas

- **[TRIAD_SYNC_LESSONS_LEARNED.md](docs/guides/TRIAD_SYNC_LESSONS_LEARNED.md)** — Lições aprendidas da sincronização Tríade
- **[SRE_EVOLUTION_METHODOLOGY.md](docs/history/SRE_EVOLUTION_METHODOLOGY.md)** — Metodologia de evolução SRE
- **[SRE_TECHNICAL_DEBT_CATALOG.md](docs/history/SRE_TECHNICAL_DEBT_CATALOG.md)** — Catálogo de débitos técnicos

### 🛠️ Diagnóstico Rápido

```bash
# Diagnóstico completo do ambiente
make doctor

# Verificar qualidade do código
make audit

# Validar documentação e links
cortex audit --links

# Verificar health do Knowledge Graph
cortex knowledge-graph --show-broken

# Consultar último relatório de saúde
cat docs/reports/KNOWLEDGE_HEALTH.md
```

### 📖 Documentação Completa

Para acesso ao catálogo completo de 115 documentos do projeto, consulte:

- **[CORTEX_INDICE.md](docs/architecture/CORTEX_INDICE.md)** — Índice completo e organizado de toda documentação

---

## 📜 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

**TL;DR:**

- ✅ Uso comercial permitido
- ✅ Modificação e distribuição permitidas
- ✅ Uso privado permitido
- ⚠️ Sem garantias ou responsabilidades

---

## 🙏 Agradecimentos

Desenvolvido com 🧠 por **Ismael Silva** e a comunidade de contribuidores.

### 🔧 Stack Tecnológica

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| [Python](https://www.python.org/) | 3.10+ | Linguagem core |
| [Pydantic](https://docs.pydantic.dev/) | v2 | Validação de dados |
| [Typer](https://typer.tiangolo.com/) | 0.12+ | CLI framework |
| [Ruff](https://github.com/astral-sh/ruff) | 0.14+ | Linter e formatter |
| [Mypy](https://mypy-lang.org/) | 1.19+ | Type checking |
| [Pytest](https://pytest.org/) | 8.x | Testing framework |
| [ChromaDB](https://www.trychroma.com/) | 0.5+ | Vector database |
| [Jinja2](https://jinja.palletsprojects.com/) | 3.x | Template engine |
| [MkDocs](https://www.mkdocs.org/) | 1.6+ | Documentation site |
| [Pre-commit](https://pre-commit.com/) | 3.x | Git hooks manager |

### 🌟 Inspirações e Créditos

- **Knowledge Graphs**: Inspirado por sistemas como Obsidian e Roam Research
- **Documentation as Code**: Philosophia do [Diátaxis Framework](https://diataxis.fr/)
- **SRE Principles**: Baseado no [Google SRE Book](https://sre.google/books/)
- **Type Safety**: Influência de linguagens como Rust e TypeScript

---

<div align="center">

**CORTEX** — _Where Documentation Meets Intelligence_

[📚 Documentação](docs/) • [🐛 Issues]({{ repository_url }}/issues) • [💬 Discussões]({{ repository_url }}/discussions)

</div>

---

_README atualizado em 2025-12-16 | CORTEX v3.1 Professional Edition (Task 013)_
