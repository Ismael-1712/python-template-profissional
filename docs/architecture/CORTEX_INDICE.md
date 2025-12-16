---
id: cortex-indice
type: arch
status: active
version: 1.4.0
author: Engineering Team
date: '2025-12-16'
context_tags: [knowledge-node, models, pydantic, link-validation, graph-analysis, retrospective, handover, complete-catalog]
linked_code: [scripts/core/cortex/models.py, scripts/core/cortex/link_resolver.py, scripts/core/cortex/knowledge_validator.py]
title: 🧠 CORTEX - Índice Completo da Documentação (115 Arquivos Catalogados)
---

# 🧠 CORTEX - Índice Completo da Documentação (115 Arquivos Catalogados)

**Data:** 16 de Dezembro de 2025
**Status:** 🟢 Fase 01 Completa + Fase 02 Completa + Fase 03 (Knowledge Validator) em Design
**Cobertura:** 115 arquivos .md (100% do projeto)

---

## 🆕 NOVIDADES - DOCUMENTAÇÃO DE RETROSPECTIVA E HANDOVER

### 📊 Análises de Governança e DX (Developer Experience)

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **DX Governance Bottleneck Analysis** | [docs/analysis/DX_GOVERNANCE_BOTTLENECK_ANALYSIS.md](../analysis/DX_GOVERNANCE_BOTTLENECK_ANALYSIS.md) | Análise de bottlenecks de governança no fluxo de desenvolvimento | ✅ Completo |
| **Executive Summary DX Optimization** | [docs/analysis/EXECUTIVE_SUMMARY_DX_OPTIMIZATION.md](../analysis/EXECUTIVE_SUMMARY_DX_OPTIMIZATION.md) | Sumário executivo das otimizações de Developer Experience | ✅ Completo |

**Conteúdo:**

- Identificação de gargalos em hooks pre-commit
- Análise de impacto no tempo de desenvolvimento
- Recomendações de otimização
- Métricas de performance e ROI

---

### 🏗️ ADRs (Architecture Decision Records)

| ADR | Título | Localização | Status |
|-----|--------|-------------|--------|
| **ADR-002** | Pre-Commit Hook Optimization | [docs/architecture/ADR_002_PRE_COMMIT_OPTIMIZATION.md](./ADR_002_PRE_COMMIT_OPTIMIZATION.md) | ✅ Aprovado |
| **ADR-003** | src/.gitkeep Stability Policy | [docs/architecture/ADR_003_SRC_GITKEEP_STABILITY.md](./ADR_003_SRC_GITKEEP_STABILITY.md) | ✅ Aprovado |

**Decisões Documentadas:**

- Estratégias de cache para hooks pre-commit
- Política de estabilidade para arquivos .gitkeep
- Impacto em CI/CD e fluxo de desenvolvimento

---

### 🛠️ Guias de Troubleshooting e Operação

| Guia | Localização | Propósito | Status |
|------|-------------|-----------|--------|
| **DEV_ENVIRONMENT_TROUBLESHOOTING** | [docs/guides/DEV_ENVIRONMENT_TROUBLESHOOTING.md](../guides/DEV_ENVIRONMENT_TROUBLESHOOTING.md) | Solução de problemas de ambiente | ✅ Completo |
| **OPERATIONAL_TROUBLESHOOTING** | [docs/guides/OPERATIONAL_TROUBLESHOOTING.md](../guides/OPERATIONAL_TROUBLESHOOTING.md) | Troubleshooting operacional | ✅ Completo |
| **QUICK_IMPLEMENTATION_GUIDE_PRE_COMMIT_FIX** | [docs/guides/QUICK_IMPLEMENTATION_GUIDE_PRE_COMMIT_FIX.md](../guides/QUICK_IMPLEMENTATION_GUIDE_PRE_COMMIT_FIX.md) | Guia rápido de correção de hooks | ✅ Completo |

**Casos Cobertos:**

- Problemas de instalação de dependências
- Erros de configuração Python
- Falhas em hooks pre-commit
- Issues de sincronização Git
- Problemas de performance

---

### 📖 Guias de Estratégia e Boas Práticas

| Guia | Localização | Área | Status |
|------|-------------|------|--------|
| **LLM_ENGINEERING_CONTEXT_AWARENESS** | [docs/guides/LLM_ENGINEERING_CONTEXT_AWARENESS.md](../guides/LLM_ENGINEERING_CONTEXT_AWARENESS.md) | Engenharia de LLM | ✅ Completo |
| **LLM_TASK_DECOMPOSITION_STRATEGY** | [docs/guides/LLM_TASK_DECOMPOSITION_STRATEGY.md](../guides/LLM_TASK_DECOMPOSITION_STRATEGY.md) | Decomposição de tarefas | ✅ Completo |
| **REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION** | [docs/guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md](../guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md) | Protocolos de refatoração | ✅ Completo |
| **SAFE_SCRIPT_TRANSPLANT** | [docs/guides/SAFE_SCRIPT_TRANSPLANT.md](../guides/SAFE_SCRIPT_TRANSPLANT.md) | Migração segura de scripts | ✅ Completo |

**Tópicos:**

- Estratégias de context awareness para LLMs
- Decomposição iterativa de tarefas complexas
- Protocolos de refatoração segura
- Migração de código entre projetos

---

### 🗂️ Documentação Histórica e Lições Aprendidas

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **NEWPROJECT_EVOLUTION** | [docs/history/NEWPROJECT_EVOLUTION.md](../history/NEWPROJECT_EVOLUTION.md) | Evolução do sistema newproject | ✅ Completo |
| **PHASE2_KNOWLEDGE_NODE_POSTMORTEM** | [docs/history/PHASE2_KNOWLEDGE_NODE_POSTMORTEM.md](../history/PHASE2_KNOWLEDGE_NODE_POSTMORTEM.md) | Postmortem da Fase 2 | ✅ Completo |
| **PHASE3_ROADMAP_HARDENING** | [docs/history/PHASE3_ROADMAP_HARDENING.md](../history/PHASE3_ROADMAP_HARDENING.md) | Hardening do roadmap Fase 3 | ✅ Completo |
| **SRE_EVOLUTION_METHODOLOGY** | [docs/history/SRE_EVOLUTION_METHODOLOGY.md](../history/SRE_EVOLUTION_METHODOLOGY.md) | Metodologia de evolução SRE | ✅ Completo |
| **SRE_TECHNICAL_DEBT_CATALOG** | [docs/history/SRE_TECHNICAL_DEBT_CATALOG.md](../history/SRE_TECHNICAL_DEBT_CATALOG.md) | Catálogo de débitos técnicos | ✅ Completo |

**Lições Aprendidas:**

- Evolução incremental de features
- Postmortems de implementações
- Catalogação de débitos técnicos
- Metodologias SRE aplicadas

---

## 🆕 DOCUMENTAÇÃO ADICIONAL

### 🏗️ Arquitetura de Scaffolding

**Arquivo:** [PROJECT_SCAFFOLDING_ARCHITECTURE.md](./PROJECT_SCAFFOLDING_ARCHITECTURE.md)

**Conteúdo:**

- Sistema "Molde + Fábrica" para criação de projetos
- Template Repository (python-template-profissional)
- Função bash `newproject` (automação)
- Branches especializadas (api, cli)
- Personalização automática via `sed`

**Status:** ✅ Implementado e em Produção

### 📜 Evolução do Sistema newproject

**Arquivo:** [../history/NEWPROJECT_EVOLUTION.md](../history/NEWPROJECT_EVOLUTION.md)

**Conteúdo:**

- Evolução histórica v1.2 → v1.5
- Problemas identificados e soluções
- Comparação de métricas (tempo, confiabilidade)
- Decisões de design validadas

**Status:** 🔵 Documento Histórico

---

## 🆕 DOCUMENTAÇÃO ADICIONAL

### 🏗️ Arquitetura de Scaffolding

**Arquivo:** [PROJECT_SCAFFOLDING_ARCHITECTURE.md](./PROJECT_SCAFFOLDING_ARCHITECTURE.md)

**Conteúdo:**

- Sistema "Molde + Fábrica" para criação de projetos
- Template Repository (python-template-profissional)
- Função bash `newproject` (automação)
- Branches especializadas (api, cli)
- Personalização automática via `sed`

**Status:** ✅ Implementado e em Produção

### 📜 Evolução do Sistema newproject

**Arquivo:** [../history/NEWPROJECT_EVOLUTION.md](../history/NEWPROJECT_EVOLUTION.md)

**Conteúdo:**

- Evolução histórica v1.2 → v1.5
- Problemas identificados e soluções
- Comparação de métricas (tempo, confiabilidade)
- Decisões de design validadas

**Status:** 🔵 Documento Histórico

---

## 📦 NOVIDADES - FASE 02: KNOWLEDGE NODE

### 🔷 Modelos de Dados (v2 - Pydantic)

**Arquivo:** `scripts/core/cortex/models.py`

**Novos Modelos Implementados:**

| Modelo | Tipo | Propósito | Status |
|--------|------|-----------|--------|
| `KnowledgeSource` | Pydantic BaseModel | Fonte externa de conhecimento (URL + metadados de sync) | ✅ Implementado |
| `KnowledgeEntry` | Pydantic BaseModel | Entrada de conhecimento com tags, golden paths e fontes | ✅ Implementado |

**Características Técnicas:**

- ✅ Pydantic v2 (`BaseModel`, `ConfigDict`, `Field`, `HttpUrl`)
- ✅ Imutabilidade garantida (`frozen=True`)
- ✅ Validação automática de URLs (apenas HTTP/HTTPS)
- ✅ Serialização/Deserialização JSON nativa
- ✅ Coexistência com dataclasses legados (sem breaking changes)
- ✅ Reutilização do Enum `DocStatus`

**Testes:**

- ✅ 21 testes unitários em `tests/test_knowledge_models.py`
- ✅ Cobertura: instanciação, validação, imutabilidade, serialização, round-trip

**Documentação:**

- Campo `url` (HttpUrl): Validação automática de esquema HTTP/HTTPS
- Campo `last_synced` (datetime | None): Timestamp da última sincronização
- Campo `etag` (str | None): Cache HTTP ETag
- Campo `golden_paths` (str): Regras imutáveis de relacionamento
- Campo `sources` (list[KnowledgeSource]): Fontes externas do conhecimento

---

## 📦 FASE 03: KNOWLEDGE GRAPH & VALIDATION

### 🔷 Design Documents (Link Analysis & Validation)

**Status:** 🔵 Design Phase

| Documento | Tarefa | Status | Propósito |
|-----------|--------|-----------|-----------|
| [CORTEX_FASE03_LINK_SCANNER_DESIGN.md](./CORTEX_FASE03_LINK_SCANNER_DESIGN.md) | [007] | ✅ Implementado | Extração de links semânticos do conteúdo |
| [CORTEX_FASE03_LINK_RESOLVER_DESIGN.md](./CORTEX_FASE03_LINK_RESOLVER_DESIGN.md) | [008] | ✅ Implementado | Resolução e validação de targets |
| [CORTEX_FASE03_VALIDATOR_DESIGN.md](./CORTEX_FASE03_VALIDATOR_DESIGN.md) | [009] | 🔵 Design | **Inversão de grafo e health metrics** |
| [CORTEX_FASE03_README.md](./CORTEX_FASE03_README.md) | - | ✅ Completo | README geral da Fase 03 |
| [CORTEX_FASE03_EXECUTIVE_SUMMARY.md](./CORTEX_FASE03_EXECUTIVE_SUMMARY.md) | - | ✅ Completo | Sumário executivo da Fase 03 |
| [CORTEX_FASE03_PRODUCTION_SUMMARY.md](./CORTEX_FASE03_PRODUCTION_SUMMARY.md) | - | ✅ Completo | Sumário de produção Fase 03 |
| [CORTEX_FASE03_VALIDATOR_EXECUTIVE_SUMMARY.md](./CORTEX_FASE03_VALIDATOR_EXECUTIVE_SUMMARY.md) | - | ✅ Completo | Sumário executivo do Validator |
| [CORTEX_FASE04_VECTOR_STORE_DESIGN.md](./CORTEX_FASE04_VECTOR_STORE_DESIGN.md) | [Future] | 🔵 Design | Design do Vector Store (Fase 04) |

### 🔷 Modelos de Dados Adicionais (Fase 03)

**Arquivo:** `scripts/core/cortex/models.py`

**Enums Adicionados:**

| Enum | Propósito | Valores |
|------|-----------|---------|
| `LinkType` | Tipo de link semântico | MARKDOWN, WIKILINK, WIKILINK_ALIASED, CODE_REFERENCE |
| `LinkStatus` | Status de resolução | UNRESOLVED, VALID, BROKEN, EXTERNAL, AMBIGUOUS |

**Novos Modelos (Pydantic):**

| Modelo | Tipo | Propósito | Status |
|--------|------|-----------|--------|
| `KnowledgeLink` | Pydantic BaseModel | Link semântico entre Knowledge Nodes | ✅ Implementado |
| `HealthMetrics` | Dataclass | Métricas de saúde do grafo | 🔵 Proposto |
| `AnomalyReport` | Dataclass | Agregação de anomalias (órfãos, becos, broken links) | 🔵 Proposto |
| `ValidationReport` | Dataclass | Relatório completo de validação | 🔵 Proposto |

**KnowledgeLink Schema:**

```python
KnowledgeLink(
    source_id: str,           # ID do Knowledge Node de origem
    target_raw: str,          # String bruta extraída ([[Fase 01]])
    target_resolved: str | None,  # Path ou ID resolvido
    target_id: str | None,    # Knowledge Node ID resolvido
    type: LinkType,           # WIKILINK, MARKDOWN, etc
    line_number: int,         # Linha onde foi encontrado
    context: str,             # Snippet de contexto
    status: LinkStatus,       # VALID, BROKEN, etc
    is_valid: bool,           # Deprecated (use status)
)
```

### 🔷 Componentes Implementados (Fase 03)

**Link Analyzer:**

- ✅ `scripts/core/cortex/link_analyzer.py`
- ✅ Extração de links via regex (wikilinks, markdown, code references)
- ✅ 15+ testes em `tests/test_link_analyzer.py`

**Link Resolver:**

- ✅ `scripts/core/cortex/link_resolver.py`
- ✅ Múltiplas estratégias de resolução (ID, path, alias, fuzzy)
- ✅ Índices reversos para lookup O(1)
- ✅ 20+ testes em `tests/test_link_resolver.py`

**Knowledge Validator (PRÓXIMO):**

- 🔵 `scripts/core/cortex/knowledge_validator.py` (Proposto)
- 🔵 Cálculo de Inbound Links (inversão de grafo)
- 🔵 Detecção de anomalias (orphans, dead ends, broken links)
- 🔵 Métricas de saúde (Connectivity Score, Link Health Score)
- 🔵 Geração de `docs/reports/KNOWLEDGE_HEALTH.md`

---

### 2. 📄 Resumo Executivo

**Arquivo:** [CORTEX_RESUMO_EXECUTIVO.md](./CORTEX_RESUMO_EXECUTIVO.md)

**Conteúdo:**

- Visão geral do projeto (1 página)
- Schema YAML em formato compacto
- Estrutura de arquivos resumida
- Dependências a adicionar
- Roadmap simplificado com estimativas
- Estratégia de migração resumida
- Comandos CLI (preview)

**Tamanho:** ~350 linhas
**Público:** Gerentes de Projeto, Product Owners, Stakeholders

### 4. 🌳 Árvore de Arquivos Proposta

**Arquivo:** [CORTEX_ARVORE_ARQUIVOS.md](./CORTEX_ARVORE_ARQUIVOS.md)

**Conteúdo:**

- Árvore visual completa do projeto
- Arquivos novos (15 arquivos 🆕)
- Arquivos modificados (32+ arquivos 📝)
- Estatísticas de criação
- Dependências entre arquivos
- Detalhamento dos arquivos principais
- Ordem de criação recomendada
- Validação final

**Tamanho:** ~500 linhas
**Público:** Desenvolvedores, DevOps, Arquitetos

---

## 📚 ARQUITETURA E DESIGN

### 🔌 Catálogo de Plugins de Auditoria

**Arquivo:** [CODE_AUDIT.md - Catálogo de Plugins](./CODE_AUDIT.md#🔌-catálogo-de-plugins-disponíveis)

**Conteúdo:**

- Documentação completa de plugins de auditoria disponíveis
- **Plugin `check_mock_coverage`**: Análise de cobertura de mocks em testes
- **Plugin `simulate_ci`**: Simulação de ambiente CI/CD local
- Templates para desenvolvimento de novos plugins
- Best practices de integração
- Exemplos de uso programático

**Plugins Documentados:**

| Plugin | Propósito | Status |
|--------|-----------|--------|
| `check_mock_coverage` | Verifica uso de mocks em testes | ✅ Documentado |
| `simulate_ci` | Simula variáveis de ambiente CI/CD | ✅ Documentado |

**Público:** Desenvolvedores, QA Engineers, DevOps

---

## 📖 GUIAS

### 🔬 Arquitetura Interna do Mock CI

**Arquivo:** [MOCK_SYSTEM.md - Arquitetura Interna](../guides/MOCK_SYSTEM.md#🔬-arquitetura-interna-do-mock-ci)

**Conteúdo:**

- Pipeline completo: **Detector → Checker → Fixer**
- Documentação detalhada de cada componente:
  - **Detector** (`detector.py`): Análise AST e detecção de ambiente CI/CD
  - **Checker** (`checker.py`): Validação read-only de testes e mocks
  - **Fixer** (`fixer.py`): Aplicação de patches e transformações AST
  - **Git Operations** (`git_ops.py`): Gestão de commits automáticos
- Fluxo de execução completo com exemplos
- Decisões de design e padrões arquiteturais
- Diagramas visuais do pipeline

**Público:** Desenvolvedores, Arquitetos de Software, SRE

**Tamanho:** ~180 linhas (nova seção)
**Status:** ✅ Completo

## 🎯 GUIA DE LEITURA POR PERFIL

### 👔 Para Gerentes/Product Owners

**Leia primeiro:**

1. [CORTEX_RESUMO_EXECUTIVO.md](./CORTEX_RESUMO_EXECUTIVO.md) (10 minutos)
2. Seções do [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md):
   - Executive Summary
   - Roadmap de Implementação
   - Riscos e Mitigações

**Objetivo:** Entender o ROI, timeline e riscos do projeto.

### 💻 Para Desenvolvedores

**Leia primeiro:**

1. [CORTEX_RESUMO_EXECUTIVO.md](./CORTEX_RESUMO_EXECUTIVO.md) (10 minutos)
2. [CORTEX_CHECKLIST_IMPLEMENTACAO.md](./CORTEX_CHECKLIST_IMPLEMENTACAO.md) (20 minutos)
3. [CORTEX_ARVORE_ARQUIVOS.md](./CORTEX_ARVORE_ARQUIVOS.md) (15 minutos)
4. Seções relevantes do [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md):
   - Arquitetura do Software (seção 3)
   - Roadmap de Implementação (seção 6)

**Objetivo:** Entender o que implementar e em qual ordem.

**Ação Prática:** Usar o checklist como guia durante desenvolvimento.

### 🔧 Para DevOps/SRE

**Leia primeiro:**

1. [CORTEX_RESUMO_EXECUTIVO.md](./CORTEX_RESUMO_EXECUTIVO.md) (10 minutos)
2. Seções do [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md):
   - Análise de Dependências (seção 1)
   - Integração com CI/CD (seção 5.3)
   - Sprint 4: Automation (seção 6)

**Objetivo:** Preparar pipelines de CI/CD e infraestrutura.

## ✅ CRITÉRIOS DE APROVAÇÃO (Fase 01)

**Este design está pronto para implementação quando:**

- [x] Schema YAML completo e validado
- [x] Estrutura de arquivos seguindo P26
- [x] Dependências identificadas
- [x] Estratégia de migração planejada
- [x] Integração com ferramentas documentada
- [x] Roadmap com estimativas estabelecido

**Status Atual:** ✅ **TODOS OS CRITÉRIOS ATENDIDOS**

## 📞 CONTATO E SUPORTE

**Dúvidas sobre o Design?**

- Consulte primeiro o [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md)
- Verifique o [CORTEX_RESUMO_EXECUTIVO.md](./CORTEX_RESUMO_EXECUTIVO.md)

**Implementando o CORTEX?**

- Use o [CORTEX_CHECKLIST_IMPLEMENTACAO.md](./CORTEX_CHECKLIST_IMPLEMENTACAO.md) como guia
- Consulte a [CORTEX_ARVORE_ARQUIVOS.md](./CORTEX_ARVORE_ARQUIVOS.md) para estrutura

**Problemas durante migração?**

- Revise a seção 4 do [CORTEX_FASE01_DESIGN.md](./CORTEX_FASE01_DESIGN.md)
- **Sempre faça backup antes de migrar!**

---

## 📚 CATÁLOGO COMPLETO DE DOCUMENTAÇÃO

### 🏛️ Arquitetura (Architecture Documents)

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **ARCHITECTURE_TRIAD** | [docs/architecture/ARCHITECTURE_TRIAD.md](./ARCHITECTURE_TRIAD.md) | Arquitetura da Tríade (Guardian + Knowledge + Neural) | ✅ Completo |
| **AUDIT_DASHBOARD_INTEGRATION** | [docs/architecture/AUDIT_DASHBOARD_INTEGRATION.md](./AUDIT_DASHBOARD_INTEGRATION.md) | Integração do Dashboard de Auditoria com CLI | ✅ Completo |
| **CORTEX_ROOT_LOCKDOWN** | [docs/architecture/CORTEX_ROOT_LOCKDOWN.md](./CORTEX_ROOT_LOCKDOWN.md) | Política de lockdown da raiz do projeto | ✅ Completo |
| **DATA_MODELS** | [docs/architecture/DATA_MODELS.md](./DATA_MODELS.md) | Documentação de modelos de dados | ✅ Completo |
| **DEPENDENCY_DIAGRAM_SNAPSHOT** | [docs/architecture/DEPENDENCY_DIAGRAM_SNAPSHOT.md](./DEPENDENCY_DIAGRAM_SNAPSHOT.md) | Snapshot de diagramas de dependências | ✅ Completo |
| **FORMATTER_PATTERN** | [docs/architecture/FORMATTER_PATTERN.md](./FORMATTER_PATTERN.md) | Padrões de formatação de código | ✅ Completo |
| **GIT_SYNC_HEARTBEAT_TELEMETRY** | [docs/architecture/GIT_SYNC_HEARTBEAT_TELEMETRY.md](./GIT_SYNC_HEARTBEAT_TELEMETRY.md) | Telemetria do sistema Git Sync | ✅ Completo |
| **I18N_STRATEGY** | [docs/architecture/I18N_STRATEGY.md](./I18N_STRATEGY.md) | Estratégia de internacionalização | ✅ Completo |
| **MOCK_CI_REFACTORING** | [docs/architecture/MOCK_CI_REFACTORING.md](./MOCK_CI_REFACTORING.md) | Refatoração do sistema Mock CI | ✅ Completo |
| **OBSERVABILITY** | [docs/architecture/OBSERVABILITY.md](./OBSERVABILITY.md) | Estratégia de observabilidade | ✅ Completo |
| **PLATFORM_ABSTRACTION** | [docs/architecture/PLATFORM_ABSTRACTION.md](./PLATFORM_ABSTRACTION.md) | Camada de abstração de plataforma | ✅ Completo |
| **ROADMAP_DELTA_AUDIT** | [docs/architecture/ROADMAP_DELTA_AUDIT.md](./ROADMAP_DELTA_AUDIT.md) | Auditoria de mudanças no roadmap | ✅ Completo |
| **SECURITY_STRATEGY** | [docs/architecture/SECURITY_STRATEGY.md](./SECURITY_STRATEGY.md) | Estratégia de segurança Defense in Depth | ✅ Completo |
| **TASK_RUNNER_PATTERN** | [docs/architecture/TASK_RUNNER_PATTERN.md](./TASK_RUNNER_PATTERN.md) | Padrão de Task Runners | ✅ Completo |
| **TRIAD_GOVERNANCE** | [docs/architecture/TRIAD_GOVERNANCE.md](./TRIAD_GOVERNANCE.md) | Governança da arquitetura Tríade | ✅ Completo |
| **VISIBILITY_GUARDIAN_DESIGN** | [docs/architecture/VISIBILITY_GUARDIAN_DESIGN.md](./VISIBILITY_GUARDIAN_DESIGN.md) | Design do Visibility Guardian | ✅ Completo |

---

### 📖 Guias Operacionais (Operational Guides)

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **ATOMIC_COMMIT_PROTOCOL** | [docs/guides/ATOMIC_COMMIT_PROTOCOL.md](../guides/ATOMIC_COMMIT_PROTOCOL.md) | Protocolo de commits atômicos | ✅ Completo |
| **CORTEX_AUTO_HOOKS** | [docs/guides/CORTEX_AUTO_HOOKS.md](../guides/CORTEX_AUTO_HOOKS.md) | Hooks automáticos do CORTEX | ✅ Completo |
| **CORTEX_INTROSPECTION_SYSTEM** | [docs/guides/CORTEX_INTROSPECTION_SYSTEM.md](../guides/CORTEX_INTROSPECTION_SYSTEM.md) | Sistema de introspecção CORTEX | ✅ Completo |
| **DEPENDENCY_MAINTENANCE_GUIDE** | [docs/guides/DEPENDENCY_MAINTENANCE_GUIDE.md](../guides/DEPENDENCY_MAINTENANCE_GUIDE.md) | Guia de manutenção de dependências | ✅ Completo |
| **DEV_PROD_PARITY_STRATEGY** | [docs/guides/DEV_PROD_PARITY_STRATEGY.md](../guides/DEV_PROD_PARITY_STRATEGY.md) | Estratégia de paridade dev/prod | ✅ Completo |
| **DIRECT_PUSH_PROTOCOL** | [docs/guides/DIRECT_PUSH_PROTOCOL.md](../guides/DIRECT_PUSH_PROTOCOL.md) | Protocolo de push direto | ✅ Completo |
| **ENGINEERING_STANDARDS** | [docs/guides/ENGINEERING_STANDARDS.md](../guides/ENGINEERING_STANDARDS.md) | Padrões de engenharia | ✅ Completo |
| **FAIL_FAST_PHILOSOPHY** | [docs/guides/FAIL_FAST_PHILOSOPHY.md](../guides/FAIL_FAST_PHILOSOPHY.md) | Filosofia Fail Fast | ✅ Completo |
| **GIT_AUTOMATION_SCRIPTS** | [docs/guides/GIT_AUTOMATION_SCRIPTS.md](../guides/GIT_AUTOMATION_SCRIPTS.md) | Scripts de automação Git | ✅ Completo |
| **KNOWLEDGE_NODE_MANUAL** | [docs/guides/KNOWLEDGE_NODE_MANUAL.md](../guides/KNOWLEDGE_NODE_MANUAL.md) | Manual do Knowledge Node | ✅ Completo |
| **POST_PR_MERGE_PROTOCOL** | [docs/guides/POST_PR_MERGE_PROTOCOL.md](../guides/POST_PR_MERGE_PROTOCOL.md) | Protocolo pós-merge de PR | ✅ Completo |
| **PROTECTED_BRANCH_WORKFLOW** | [docs/guides/PROTECTED_BRANCH_WORKFLOW.md](../guides/PROTECTED_BRANCH_WORKFLOW.md) | Workflow de branches protegidas | ✅ Completo |
| **SMART_GIT_SYNC_GUIDE** | [docs/guides/SMART_GIT_SYNC_GUIDE.md](../guides/SMART_GIT_SYNC_GUIDE.md) | Guia do Smart Git Sync | ✅ Completo |
| **TESTING_STRATEGY_MOCKS** | [docs/guides/TESTING_STRATEGY_MOCKS.md](../guides/TESTING_STRATEGY_MOCKS.md) | Estratégia de testes com mocks | ✅ Completo |
| **TRIAD_SYNC_LESSONS_LEARNED** | [docs/guides/TRIAD_SYNC_LESSONS_LEARNED.md](../guides/TRIAD_SYNC_LESSONS_LEARNED.md) | Lições aprendidas da Tríade | ✅ Completo |
| **VISIBILITY_GUARDIAN_QUICK_START** | [docs/guides/VISIBILITY_GUARDIAN_QUICK_START.md](../guides/VISIBILITY_GUARDIAN_QUICK_START.md) | Quick Start do Visibility Guardian | ✅ Completo |
| **logging** | [docs/guides/logging.md](../guides/logging.md) | Guia de logging | ✅ Completo |
| **testing** | [docs/guides/testing.md](../guides/testing.md) | Guia de testes | ✅ Completo |

---

### 📜 Histórico de Sprints (Sprint History)

#### Sprint 1 - Foundation

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **FASE01_DISCOVERY_CEGUEIRA_FERRAMENTA** | [docs/history/sprint_1_foundation/FASE01_DISCOVERY_CEGUEIRA_FERRAMENTA.md](../history/sprint_1_foundation/FASE01_DISCOVERY_CEGUEIRA_FERRAMENTA.md) | Discovery de limitações de ferramentas | ✅ Completo |
| **P12_CODE_AUDIT_REFACTORING_ANALYSIS** | [docs/history/sprint_1_foundation/P12_CODE_AUDIT_REFACTORING_ANALYSIS.md](../history/sprint_1_foundation/P12_CODE_AUDIT_REFACTORING_ANALYSIS.md) | Análise de refatoração Code Audit | ✅ Completo |
| **P13_AUDITORIA_WARNINGS_NOQA** | [docs/history/sprint_1_foundation/P13_AUDITORIA_WARNINGS_NOQA.md](../history/sprint_1_foundation/P13_AUDITORIA_WARNINGS_NOQA.md) | Auditoria de warnings e noqa | ✅ Completo |
| **P13_FASE02_CORRECOES_IMPLEMENTADAS** | [docs/history/sprint_1_foundation/P13_FASE02_CORRECOES_IMPLEMENTADAS.md](../history/sprint_1_foundation/P13_FASE02_CORRECOES_IMPLEMENTADAS.md) | Correções implementadas Fase 02 | ✅ Completo |
| **P26_FASE02_RELATORIO_FINAL** | [docs/history/sprint_1_foundation/P26_FASE02_RELATORIO_FINAL.md](../history/sprint_1_foundation/P26_FASE02_RELATORIO_FINAL.md) | Relatório final P26 Fase 02 | ✅ Completo |
| **P26_FASE02_3_RELATORIO_FINAL** | [docs/history/sprint_1_foundation/P26_FASE02_3_RELATORIO_FINAL.md](../history/sprint_1_foundation/P26_FASE02_3_RELATORIO_FINAL.md) | Relatório final P26 Fase 02.3 | ✅ Completo |
| **P26_FASE02_4_5_RELATORIO_FINAL** | [docs/history/sprint_1_foundation/P26_FASE02_4_5_RELATORIO_FINAL.md](../history/sprint_1_foundation/P26_FASE02_4_5_RELATORIO_FINAL.md) | Relatório final P26 Fase 02.4/5 | ✅ Completo |
| **P26_FASE02_6_RELATORIO_FINAL** | [docs/history/sprint_1_foundation/P26_FASE02_6_RELATORIO_FINAL.md](../history/sprint_1_foundation/P26_FASE02_6_RELATORIO_FINAL.md) | Relatório final P26 Fase 02.6 | ✅ Completo |
| **P26_FASE02_RELATORIO_PARCIAL** | [docs/history/sprint_1_foundation/P26_FASE02_RELATORIO_PARCIAL.md](../history/sprint_1_foundation/P26_FASE02_RELATORIO_PARCIAL.md) | Relatório parcial P26 Fase 02 | ✅ Completo |
| **P26_REFATORACAO_SCRIPTS_FASE01** | [docs/history/sprint_1_foundation/P26_REFATORACAO_SCRIPTS_FASE01.md](../history/sprint_1_foundation/P26_REFATORACAO_SCRIPTS_FASE01.md) | Refatoração de scripts Fase 01 | ✅ Completo |
| **SPRINT1_AUDITORIA_FASE01** | [docs/history/sprint_1_foundation/SPRINT1_AUDITORIA_FASE01.md](../history/sprint_1_foundation/SPRINT1_AUDITORIA_FASE01.md) | Auditoria Sprint 1 Fase 01 | ✅ Completo |
| **SPRINT1_AUDITORIA_SUMARIO** | [docs/history/sprint_1_foundation/SPRINT1_AUDITORIA_SUMARIO.md](../history/sprint_1_foundation/SPRINT1_AUDITORIA_SUMARIO.md) | Sumário de auditoria Sprint 1 | ✅ Completo |
| **SPRINT1_FASE02_RELATORIO** | [docs/history/sprint_1_foundation/SPRINT1_FASE02_RELATORIO.md](../history/sprint_1_foundation/SPRINT1_FASE02_RELATORIO.md) | Relatório Sprint 1 Fase 02 | ✅ Completo |
| **SPRINT1_MIGRATION_GUIDE** | [docs/history/sprint_1_foundation/SPRINT1_MIGRATION_GUIDE.md](../history/sprint_1_foundation/SPRINT1_MIGRATION_GUIDE.md) | Guia de migração Sprint 1 | ✅ Completo |
| **SPRINT1_README** | [docs/history/sprint_1_foundation/SPRINT1_README.md](../history/sprint_1_foundation/SPRINT1_README.md) | README do Sprint 1 | ✅ Completo |

#### Sprint 2 - CORTEX

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **IMPLEMENTATION_SUMMARY** | [docs/history/sprint_2_cortex/IMPLEMENTATION_SUMMARY.md](../history/sprint_2_cortex/IMPLEMENTATION_SUMMARY.md) | Sumário de implementação Sprint 2 | ✅ Completo |

#### Sprint 4 - Type Safety & Hooks

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **HOOKS_IMPLEMENTATION** | [docs/history/sprint_4/HOOKS_IMPLEMENTATION.md](../history/sprint_4/HOOKS_IMPLEMENTATION.md) | Implementação de hooks | ✅ Completo |
| **INDICE** | [docs/history/sprint_4/INDICE.md](../history/sprint_4/INDICE.md) | Índice do Sprint 4 | ✅ Completo |
| **MYPY_COMPARACAO_CONFIGS** | [docs/history/sprint_4/MYPY_COMPARACAO_CONFIGS.md](../history/sprint_4/MYPY_COMPARACAO_CONFIGS.md) | Comparação de configs Mypy | ✅ Completo |
| **SPRINT4_MYPY_AUDIT** | [docs/history/sprint_4/SPRINT4_MYPY_AUDIT.md](../history/sprint_4/SPRINT4_MYPY_AUDIT.md) | Auditoria Mypy Sprint 4 | ✅ Completo |
| **SPRINT4_MYPY_RESUMO_EXECUTIVO** | [docs/history/sprint_4/SPRINT4_MYPY_RESUMO_EXECUTIVO.md](../history/sprint_4/SPRINT4_MYPY_RESUMO_EXECUTIVO.md) | Resumo executivo Mypy Sprint 4 | ✅ Completo |

#### Sprint 5 - Link Scanner

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **SPRINT5_PHASE1_SCANNER_IMPLEMENTATION** | [docs/history/sprint_5/SPRINT5_PHASE1_SCANNER_IMPLEMENTATION.md](../history/sprint_5/SPRINT5_PHASE1_SCANNER_IMPLEMENTATION.md) | Implementação Scanner Sprint 5 | ✅ Completo |
| **SPRINT5_SUMMARY** | [docs/history/sprint_5/SPRINT5_SUMMARY.md](../history/sprint_5/SPRINT5_SUMMARY.md) | Sumário do Sprint 5 | ✅ Completo |

#### Task 004 - Dependencies

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **HARDENING_IMPLEMENTATION_REPORT** | [docs/history/task_004_dependencies/HARDENING_IMPLEMENTATION_REPORT.md](../history/task_004_dependencies/HARDENING_IMPLEMENTATION_REPORT.md) | Relatório de hardening | ✅ Completo |
| **TASK_004_DEPENDENCY_ANALYSIS** | [docs/history/task_004_dependencies/TASK_004_DEPENDENCY_ANALYSIS.md](../history/task_004_dependencies/TASK_004_DEPENDENCY_ANALYSIS.md) | Análise de dependências | ✅ Completo |
| **TASK_004_SUMARIO_EXECUTIVO** | [docs/history/task_004_dependencies/TASK_004_SUMARIO_EXECUTIVO.md](../history/task_004_dependencies/TASK_004_SUMARIO_EXECUTIVO.md) | Sumário executivo Task 004 | ✅ Completo |

#### Outros Históricos

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **visibility_guardian_orphan_detection_test** | [docs/history/visibility_guardian_orphan_detection_test.md](../history/visibility_guardian_orphan_detection_test.md) | Teste de detecção de órfãos | ✅ Completo |

---

### 📚 Referências (Reference Documentation)

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **CI_DOCS_VALIDATOR** | [docs/reference/CI_DOCS_VALIDATOR.md](../reference/CI_DOCS_VALIDATOR.md) | Validador de docs no CI | ✅ Completo |
| **CLI_COMMANDS** | [docs/reference/CLI_COMMANDS.md](../reference/CLI_COMMANDS.md) | Referência completa de comandos CLI (Auto-generated) | ✅ Completo |
| **DYNAMIC_README** | [docs/reference/DYNAMIC_README.md](../reference/DYNAMIC_README.md) | Sistema de README dinâmico | ✅ Completo |
| **git_sync** | [docs/reference/git_sync.md](../reference/git_sync.md) | Referência do Git Sync | ✅ Completo |

---

### 📊 Relatórios (Reports)

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **KNOWLEDGE_HEALTH** | [docs/reports/KNOWLEDGE_HEALTH.md](../reports/KNOWLEDGE_HEALTH.md) | Relatório de saúde do grafo de conhecimento | ✅ Completo |
| **STRUCTURE_CLEANUP_REPORT** | [docs/reports/STRUCTURE_CLEANUP_REPORT.md](../reports/STRUCTURE_CLEANUP_REPORT.md) | Relatório de limpeza estrutural | ✅ Completo |
| **TECHNICAL_ROADMAP_Q1_Q5_2026** | [docs/reports/TECHNICAL_ROADMAP_Q1_Q5_2026.md](../reports/TECHNICAL_ROADMAP_Q1_Q5_2026.md) | Roadmap técnico Q1-Q5 2026 | ✅ Completo |

---

### 🧠 Knowledge Base

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **OPERATIONAL_WAR_DIARY** | [docs/knowledge/OPERATIONAL_WAR_DIARY.md](../knowledge/OPERATIONAL_WAR_DIARY.md) | Diário operacional | ✅ Completo |
| **example-kno-001** | [docs/knowledge/example-kno-001.md](../knowledge/example-kno-001.md) | Exemplo de Knowledge Node | ✅ Completo |

---

### 📑 Meta Documentação

| Documento | Localização | Propósito | Status |
|-----------|-------------|-----------|--------|
| **docs/README** | [docs/README.md](../README.md) | README da pasta docs | ✅ Completo |
| **docs/index** | [docs/index.md](../index.md) | Índice da documentação | ✅ Completo |

---

## 🔄 HISTÓRICO DE VERSÕES

| Versão | Data | Mudanças |
|--------|------|----------|
| v1.5.0 | 2025-12-16 | **Fase 3 Retroativa:** Integração de 11 arquivos órfãos (SECURITY_STRATEGY, AUDIT_DASHBOARD_INTEGRATION, CLI_COMMANDS, CORTEX_FASE03 docs, KNOWLEDGE_HEALTH, etc) |
| v1.4.0 | 2025-12-16 | **Catalogação Completa:** Integrados TODOS os 104 arquivos .md do projeto (arquitetura, guias, histórico, referências, relatórios) |
| v1.3.0 | 2025-12-16 | **Retrospectiva:** Adicionados 40+ documentos de handover, troubleshooting, ADRs e lições aprendidas |
| v1.2.0 | 2025-12-14 | **Fase 03:** Design do Knowledge Validator (inversão de grafo + health metrics) |
| v1.1.0 | 2025-12-07 | **Fase 02:** Adição dos modelos `KnowledgeSource` e `KnowledgeEntry` (Pydantic v2) |
| v1.0.0 | 2025-11-30 | Design inicial completo (Fase 01) |

**Status Fase 01:** 🟢 **APROVADO E IMPLEMENTADO**
**Status Fase 02:** 🟢 **APROVADO E IMPLEMENTADO**
**Status Fase 03:** 🔵 **DESIGN EM APROVAÇÃO (Tarefa [009])**

**📊 Cobertura de Documentação:** 115 arquivos .md indexados (100% do projeto)

---

## 📝 NOTAS DE MANUTENÇÃO

### 🔧 Limpeza Estrutural (2025-12-16)

**Arquivos Realocados:**

- `docs/architecture/CORTEX_FASE03_DIAGRAMS.py` → `scripts/docs/CORTEX_FASE03_DIAGRAMS.py`
  - **Motivo:** Código executável (ASCII art diagrams) não deve residir em `docs/`
  - **Execução:** `python scripts/docs/CORTEX_FASE03_DIAGRAMS.py`

**Diretórios Removidos:**

- `tests/tests/` — Diretório de teste aninhado vazio (violação de estrutura)

**Governança Adicionada:**

- `tests/test_structure_policy.py` — Testes automáticos que impedem:
  - Arquivos `.py` dentro de `docs/`
  - Diretórios de teste aninhados
  - Nomenclatura ambígua de diretórios

---

**Data de Criação:** 2025-11-30
**Última Atualização:** 2025-12-16
**Autor:** Engineering Team
**Versão:** 1.5.0
