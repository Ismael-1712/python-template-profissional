---
id: knowledge-node-guide
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 2025-12-20
context_tags: [cortex, knowledge-node, synchronization, golden-paths, documentation]
linked_code:
  - scripts/core/cortex/knowledge_sync.py
  - scripts/core/cortex/knowledge_scanner.py
  - scripts/core/cortex/mapper.py
---

# 🧠 CORTEX Knowledge Node - Guia Completo

> **Sistema de sincronização e preservação de regras de projeto**

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Conceitos Fundamentais](#-conceitos-fundamentais)
- [🛡️ Zonas de Proteção (Golden Paths)](#️-zonas-de-proteção-golden-paths)
- [Fluxo de Trabalho](#-fluxo-de-trabalho)
- [Comandos CLI](#-comandos-cli)
- [Exemplos Práticos](#-exemplos-práticos)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Visão Geral

O **Knowledge Node** é um subsistema do CORTEX que resolve dois problemas críticos:

1. **Sincronização de Conhecimento Remoto**: Busca regras e padrões de fontes externas (URLs, wikis, GitHub) e mantém cópias locais atualizadas.
2. **Contexto para LLMs**: Enriquece o contexto do projeto (`cortex map`) com regras institucionais, permitindo que LLMs entendam não apenas o código, mas também os **padrões e convenções** do projeto.

### 🔑 Problema Resolvido

**Antes:**

```
❌ Regras de projeto espalhadas em wikis, Notion, Google Docs
❌ LLMs sugerem código que viola convenções internas
❌ Edições locais perdidas quando fonte remota atualiza
❌ Onboarding lento (devs não sabem onde estão as regras)
```

**Depois:**

```
✅ Regras centralizadas em docs/knowledge/ (versionadas no Git)
✅ LLMs recebem regras via cortex map --include-knowledge
✅ Edições locais protegidas com marcadores Golden Path
✅ Onboarding acelerado (cortex knowledge-scan lista todas as regras)
```

---

## 🧩 Conceitos Fundamentais

### Knowledge Entry

Um **Knowledge Entry** é um arquivo Markdown em `docs/knowledge/` com frontmatter YAML:

```yaml
---
id: kno-auth-001                    # Identificador único
status: active                       # active | draft | deprecated
tags: [authentication, security]     # Tags para categorização
golden_paths:                        # Caminhos de código relacionados
  - "src/app/auth/jwt.py -> docs/guides/auth.md"
sources:                             # Fontes remotas (opcionais)
  - url: "https://wiki.company.com/auth-standards.md"
    type: documentation
    priority: high
    etag: "abc123"                   # Cache HTTP
    last_synced: 2025-12-20T10:00:00Z
---

# Authentication Standards

All API authentication MUST use JWT tokens with HS256 algorithm.

## Implementation

Use the centralized handler in `src/app/auth/jwt.py`.
```

### Golden Paths

**Golden Paths** são caminhos bidirecionais entre código e documentação:

```
src/app/auth/jwt.py  ←→  docs/guides/authentication.md
```

**Benefícios:**

- LLMs sabem qual código implementa qual documentação
- Devs navegam rapidamente entre código e specs
- CI/CD pode validar se implementação segue o padrão

---

## 🛡️ Zonas de Proteção (Golden Paths)

### ⚠️ ATENÇÃO: Leia Esta Seção Com Cuidado

O Knowledge Node suporta **sincronização de fontes remotas** via `cortex knowledge-sync`.
Por padrão, **todo o conteúdo local é sobrescrito** pelo conteúdo remoto.

Para preservar edições locais, você **DEVE** usar os marcadores HTML especiais:

### 🔒 Marcadores de Proteção

```markdown
<!-- GOLDEN_PATH_START -->
Tudo nesta seção será PRESERVADO durante o sync remoto.
Adicione suas notas, customizações e regras específicas do projeto aqui.
<!-- GOLDEN_PATH_END -->
```

### ⚙️ Como Funciona

**Comportamento durante `cortex knowledge-sync`:**

1. ✅ **Frontmatter YAML**: Sempre preservado (nunca sobrescrito)
2. ✅ **Blocos entre `<!-- GOLDEN_PATH_START/END -->`**: Preservados
3. ❌ **Resto do conteúdo**: **SOBRESCRITO** pelo conteúdo remoto

### 📝 Exemplo Visual

**Arquivo Local Antes do Sync:**

```markdown
---
id: kno-auth-001
sources:
  - url: "https://example.com/auth.md"
---

# Authentication Rules

Este parágrafo será sobrescrito.

<!-- GOLDEN_PATH_START -->
## 🏢 Customizações Internas

Nossa empresa usa Azure AD B2C, não implementação genérica.
Endpoint: https://mycompany.b2clogin.com/

### Exceções de Segurança
- Ambientes de dev/staging: JWT opcional
- Webhooks internos: API Key permitida
<!-- GOLDEN_PATH_END -->

Outro parágrafo que será sobrescrito.
```

**Fonte Remota (<https://example.com/auth.md>):**

```markdown
# Authentication Rules

NOVO CONTEÚDO REMOTO: Use OAuth 2.0 com PKCE.

## Implementation Guide

Step 1: Install library...
```

**Arquivo Local Depois do Sync:**

```markdown
---
id: kno-auth-001
sources:
  - url: "https://example.com/auth.md"
    last_synced: 2025-12-20T15:30:00Z
---

# Authentication Rules

NOVO CONTEÚDO REMOTO: Use OAuth 2.0 com PKCE.

## Implementation Guide

Step 1: Install library...

<!-- GOLDEN_PATH_START -->
## 🏢 Customizações Internas

Nossa empresa usa Azure AD B2C, não implementação genérica.
Endpoint: https://mycompany.b2clogin.com/

### Exceções de Segurança
- Ambientes de dev/staging: JWT opcional
- Webhooks internos: API Key permitida
<!-- GOLDEN_PATH_END -->
```

### ✂️ Snippet Copy & Paste

Use este snippet para criar zonas protegidas:

```html
<!-- GOLDEN_PATH_START -->
Suas customizações locais aqui.
<!-- GOLDEN_PATH_END -->
```

**Dica:** Crie múltiplos blocos protegidos se necessário:

```markdown
# Remote Section 1
Conteúdo sincronizado...

<!-- GOLDEN_PATH_START -->
Minhas notas sobre Section 1
<!-- GOLDEN_PATH_END -->

# Remote Section 2
Mais conteúdo sincronizado...

<!-- GOLDEN_PATH_START -->
Minhas notas sobre Section 2
<!-- GOLDEN_PATH_END -->
```

---

## 🔄 Fluxo de Trabalho

### Diagrama do Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│ 1️⃣ Fonte Remota (Wiki, GitHub, Notion)                          │
│    https://wiki.company.com/standards/auth.md                    │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ cortex knowledge-sync
                         │ (Baixa via HTTP + ETag caching)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2️⃣ Arquivo Local (docs/knowledge/authentication.md)             │
│    - Frontmatter preservado                                      │
│    - Blocos GOLDEN_PATH preservados                              │
│    - Resto do conteúdo substituído                               │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ cortex map --include-knowledge
                         │ (Extrai golden_paths + formata Markdown)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3️⃣ Context Map (.cortex/context.json)                           │
│    {                                                              │
│      "golden_paths": [                                            │
│        "src/app/auth/jwt.py -> docs/guides/auth.md"              │
│      ],                                                           │
│      "knowledge_rules": "# Project Rules\n..."                   │
│    }                                                              │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ Consumido por LLMs/IDEs
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4️⃣ LLM (GitHub Copilot, GPT-4, etc.)                            │
│    - Lê .cortex/context.json                                     │
│    - Entende regras do projeto                                   │
│    - Gera código alinhado com convenções                         │
└──────────────────────────────────────────────────────────────────┘
```

### Workflow Típico

#### Cenário 1: Projeto Novo (Sem Knowledge Remoto)

```bash
# 1. Criar entrada de conhecimento manualmente
mkdir -p docs/knowledge
cat > docs/knowledge/architecture.md <<EOF
---
id: kno-arch-001
status: active
tags: [architecture, patterns]
golden_paths:
  - "src/app/models/*.py -> docs/architecture/database.md"
---

# Architecture Patterns

## Database Models

All models MUST inherit from BaseModel and follow naming conventions.
EOF

# 2. Gerar contexto para LLMs
cortex map --include-knowledge

# 3. LLM agora entende as regras do projeto!
```

#### Cenário 2: Sincronizar com Wiki Corporativa

```bash
# 1. Criar entrada com fonte remota
cat > docs/knowledge/security.md <<EOF
---
id: kno-sec-001
status: active
tags: [security, compliance]
sources:
  - url: "https://wiki.company.com/security-standards.md"
    type: documentation
    priority: high
---

<!-- GOLDEN_PATH_START -->
## 🏢 Exceções Corporativas

Nossa empresa permite autenticação via API Key para webhooks internos.
Endpoint de auditoria: https://audit.company.com/logs
<!-- GOLDEN_PATH_END -->
EOF

# 2. Sincronizar conteúdo remoto
cortex knowledge-sync

# 3. Conteúdo remoto é baixado e mesclado
# ✅ Bloco GOLDEN_PATH preservado
# ✅ Frontmatter preservado
# ❌ Resto substituído por conteúdo da wiki

# 4. Gerar contexto atualizado
cortex map --include-knowledge
```

#### Cenário 3: Atualização Periódica

```bash
# Adicionar ao CI/CD ou cron job
# Este comando sincroniza todas as entradas com sources definidas
cortex knowledge-sync --all

# Regenerar contexto após sync
cortex map
```

---

## 🛠️ Comandos CLI

### `cortex knowledge-scan`

**Propósito**: Listar e validar todas as entradas de conhecimento.

```bash
# Listar todas as entradas
cortex knowledge-scan

# Output exemplo:
# 🧠 Knowledge Base Scanner
# Workspace: /project
# Knowledge Directory: docs/knowledge/
#
# ✅ Found 3 knowledge entries
#
# ✅ kno-auth-001 (active)
# ✅ kno-db-001 (active)
# 📝 kno-draft-002 (draft)

# Modo verboso (mostra tags, golden paths, sources)
cortex knowledge-scan --verbose

# Modo experimental paralelo (para 100+ entries)
cortex knowledge-scan --parallel
```

### `cortex knowledge-sync`

**Propósito**: Sincronizar conteúdo de fontes remotas.

```bash
# Sincronizar uma entrada específica
cortex knowledge-sync --entry kno-auth-001

# Sincronizar todas as entradas com fontes definidas
cortex knowledge-sync --all

# Forçar re-download (ignora cache ETag)
cortex knowledge-sync --entry kno-auth-001 --force

# Modo dry-run (mostra o que seria feito)
cortex knowledge-sync --all --dry-run
```

**Comportamento de Cache:**

- ✅ **ETag**: Se servidor retorna HTTP 304 (Not Modified), conteúdo local não é atualizado.
- ✅ **Timestamp**: Campo `last_synced` no frontmatter rastreia última sincronização.
- ✅ **Timeout**: Requests têm timeout de 10s (protege contra servidores lentos).

### `cortex map`

**Propósito**: Gerar contexto do projeto para LLMs.

```bash
# Gerar contexto COM knowledge (padrão)
cortex map

# Gerar contexto SEM knowledge (opt-out)
cortex map --no-knowledge

# Modo verboso (mostra golden paths)
cortex map --verbose

# Output personalizado
cortex map -o custom/context.json

# Integração: Map + Sync config
cortex map --update-config
```

**Output JSON (`.cortex/context.json`):**

```json
{
  "project_name": "my-project",
  "version": "1.0.0",
  "cli_commands": [...],
  "documents": [...],
  "golden_paths": [
    "src/app/auth/jwt.py -> docs/guides/authentication.md",
    "src/app/models/*.py -> docs/guides/database.md"
  ],
  "knowledge_rules": "# Project Rules & Golden Paths\n\n## Active Rules\n\n### kno-auth-001 [ACTIVE]\n**Tags:** `authentication`, `security`\n\n**Golden Paths:**\n- `src/app/auth/jwt.py -> docs/guides/authentication.md`\n\n**Rule Summary:**\n> All API authentication MUST use JWT tokens.\n\n---"
}
```

---

## 💡 Exemplos Práticos

### Exemplo 1: Regra de Naming Convention

**Arquivo**: `docs/knowledge/naming.md`

```markdown
---
id: kno-naming-001
status: active
tags: [code-style, naming]
golden_paths:
  - "src/app/**/*.py -> docs/guides/code-style.md"
---

# Naming Conventions

## Python Classes

- **Models**: Singular noun, PascalCase (e.g., `User`, `Product`)
- **Services**: Verb + "Service" (e.g., `AuthService`, `EmailService`)
- **Utils**: Descriptive noun (e.g., `StringHelper`, `DateFormatter`)

<!-- GOLDEN_PATH_START -->
## 🏢 Company-Specific Rules

### Database Tables
- All table names MUST use schema prefix: `app_users`, `app_products`
- Never use plurals in table names (use `app_user`, not `app_users`)

### API Endpoints
- Use kebab-case: `/api/user-profile`, not `/api/userProfile`
<!-- GOLDEN_PATH_END -->
```

**Uso no LLM:**

```
Prompt: "Create a new service to handle email notifications"

LLM (com cortex map):
✅ Cria EmailService (segue convenção "Verb + Service")
✅ Evita criar email_notification_service (não segue padrão)
```

### Exemplo 2: Security Standards com Fonte Remota

**Arquivo**: `docs/knowledge/security.md`

```markdown
---
id: kno-sec-001
status: active
tags: [security, owasp, compliance]
sources:
  - url: "https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Authentication_Cheat_Sheet.md"
    type: documentation
    priority: high
    etag: "W/\"abc123\""
    last_synced: 2025-12-19T10:00:00Z
---

# Authentication Security Standards

(Conteúdo sincronizado do OWASP será inserido aqui)

<!-- GOLDEN_PATH_START -->
## 🏢 Internal Compliance Requirements

### Azure AD Integration
- Production: Use managed identity with RBAC
- Staging: Service principal with limited scope
- Dev: Local emulator allowed

### Audit Logging
All authentication events MUST be logged to Azure Monitor:
- Endpoint: https://mycompany.monitor.azure.com
- Log Level: INFO (success), WARN (failures)
- Retention: 90 days (compliance requirement)
<!-- GOLDEN_PATH_END -->
```

**Workflow:**

```bash
# 1. Sincronizar com OWASP
cortex knowledge-sync --entry kno-sec-001

# Output:
# ✅ Fetched: OWASP Authentication Cheat Sheet
# ✅ Merged with local customizations
# ✅ Updated last_synced timestamp

# 2. Gerar contexto
cortex map

# 3. LLM agora tem:
#    - Padrões OWASP atualizados
#    - Customizações internas da empresa
```

### Exemplo 3: API Design Guidelines

**Arquivo**: `docs/knowledge/api-design.md`

```markdown
---
id: kno-api-001
status: active
tags: [api, rest, openapi]
golden_paths:
  - "src/app/routes/*.py -> docs/architecture/api-spec.md"
  - "openapi.yaml -> docs/guides/api-design.md"
---

# REST API Design Guidelines

## Versioning

- Use URL versioning: `/api/v1/users`, `/api/v2/users`
- Never break backward compatibility within same major version

## Error Responses

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Email format is invalid",
    "details": {"field": "email"}
  }
}
```

<!-- GOLDEN_PATH_START -->
## 🏢 Company Standards

### Rate Limiting

- Free tier: 100 req/min
- Pro tier: 1000 req/min
- Enterprise: Unlimited (with fair use policy)

### Response Headers (Required)

```
X-Request-ID: <uuid>
X-RateLimit-Remaining: <int>
X-Response-Time: <ms>
```

### Webhook Delivery

- Retry policy: Exponential backoff (1s, 2s, 4s, 8s, 16s)
- Timeout: 30s per attempt
- Dead letter queue: Azure Service Bus
<!-- GOLDEN_PATH_END -->
```

---

## 🔧 Troubleshooting

### Problema: Sync sobrescreve minhas edições

**Causa**: Edições locais fora dos blocos `<!-- GOLDEN_PATH_START/END -->`

**Solução**:
```markdown
❌ ERRADO (será sobrescrito):
## Minhas Notas
Texto importante aqui

✅ CORRETO (será preservado):
<!-- GOLDEN_PATH_START -->
## Minhas Notas
Texto importante aqui
<!-- GOLDEN_PATH_END -->
```

### Problema: `cortex knowledge-sync` falha com timeout

**Causa**: Fonte remota lenta ou indisponível

**Detalhes**: O sistema tem timeout de 10s. Se o servidor não responder, o erro é logado mas o sync não falha.

**Solução**:

```bash
# Ver logs detalhados
tail -f cortex_knowledge_sync.log

# Output:
# WARNING: Timeout fetching https://slow-server.com/doc.md
# INFO: Local content preserved (no data loss)

# Forçar retry depois
cortex knowledge-sync --entry kno-xxx-001 --force
```

### Problema: LLM não recebe as regras

**Verificação**:

```bash
# 1. Verificar se knowledge está no context.json
cat .cortex/context.json | jq '.knowledge_rules'

# 2. Garantir que cortex map foi executado
cortex map --verbose

# 3. Verificar se LLM está consumindo o arquivo correto
# (Para GitHub Copilot, verificar .copilot-instructions.md)
```

### Problema: Entry malformado não aparece

**Causa**: YAML frontmatter inválido ou falta campo `id`

**Solução**:

```bash
# Escanear e ver erros
cortex knowledge-scan --verbose

# Output mostrará:
# ⚠️ Failed to parse docs/knowledge/broken.md: Missing required field 'id'

# Corrigir o frontmatter:
---
id: kno-fix-001  # ← Adicionar ID obrigatório
status: active
tags: []
---
```

### Problema: Golden Path não funciona

**Verificação do Regex**:

Os marcadores devem seguir exatamente este formato (espaços opcionais):

```html
<!-- GOLDEN_PATH_START -->
Conteúdo
<!-- GOLDEN_PATH_END -->
```

**Variações aceitas:**

```html
<!--GOLDEN_PATH_START-->
<!-- GOLDEN_PATH_START-->
<!--  GOLDEN_PATH_START  -->
```

**NÃO aceitas:**

```html
<!-- GOLDEN PATH START -->  ❌ (espaço no nome)
<!-- Golden_Path_Start -->  ❌ (case-sensitive)
<-- GOLDEN_PATH_START -->  ❌ (typo)
```

---

## 🎓 Melhores Práticas

### 1. Organize por Domínio

```
docs/knowledge/
├── authentication.md    # Auth & Security
├── database.md          # Data models
├── api-design.md        # REST API standards
├── deployment.md        # CI/CD & Infrastructure
└── code-style.md        # Naming & formatting
```

### 2. Use Tags Consistentes

```yaml
tags: [authentication, security, oauth]  # ✅ Lowercase, hyphens
tags: [Auth, SECURITY, OAuth2]           # ❌ Inconsistent case
```

### 3. Mantenha Entries Focados

```markdown
✅ BOM: Um entry por tópico
- kno-auth-jwt-001: JWT implementation
- kno-auth-oauth-001: OAuth flows

❌ RUIM: Entry genérico demais
- kno-auth-everything-001: All auth stuff
```

### 4. Golden Paths para Customizações

Use Golden Paths para:

- ✅ Exceções específicas da empresa
- ✅ Configurações de ambiente (URLs, credenciais)
- ✅ Notas de troubleshooting local
- ✅ Lições aprendidas em produção

NÃO use para:

- ❌ Conteúdo que deveria estar na fonte remota
- ❌ Regras gerais (essas devem estar no conteúdo sincronizado)

### 5. Automatize Syncs

```bash
# Adicionar ao CI/CD (.github/workflows/knowledge-sync.yml)
name: Sync Knowledge
on:
  schedule:
    - cron: '0 9 * * 1'  # Toda segunda às 9h
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: cortex knowledge-sync --all
      - run: cortex map
      - run: git commit -am "chore: sync knowledge base"
      - run: git push
```

---

## 📚 Referências

- **Código-fonte**:
  - [`scripts/core/cortex/knowledge_sync.py`](../../scripts/core/cortex/knowledge_sync.py)
  - [`scripts/core/cortex/knowledge_scanner.py`](../../scripts/core/cortex/knowledge_scanner.py)
  - [`scripts/core/cortex/mapper.py`](../../scripts/core/cortex/mapper.py)

- **Arquitetura**:
  - [CORTEX Architecture](../architecture/CORTEX_INDICE.md)
  - [Knowledge Models](../architecture/CORTEX_KNOWLEDGE_MODELS.md)

- **Testes**:
  - [`tests/test_knowledge_sync.py`](../../tests/test_knowledge_sync.py)
  - [`tests/test_cortex_map_knowledge.py`](../../tests/test_cortex_map_knowledge.py)

---

## 🤝 Contribuindo

Encontrou um bug ou tem uma sugestão? Abra uma issue ou envie um PR!

**Áreas para melhoria:**

- [ ] Suporte a fontes além de HTTP (Git submodules, S3, etc.)
- [ ] UI web para visualizar knowledge graph
- [ ] Validação automática de Golden Paths (verificar se caminhos existem)
- [ ] Metrics: rastrear quais regras são mais consultadas por LLMs

---

**Última atualização**: 2025-12-20
**Versão do guia**: 1.0.0
**Autores**: Engineering Team
