---
id: cortex-indice
type: arch
status: active
version: 1.3.0
author: Engineering Team
date: '2025-12-16'
context_tags: [knowledge-node, models, pydantic, link-validation, graph-analysis, retrospective, handover]
linked_code: [scripts/core/cortex/models.py, scripts/core/cortex/link_resolver.py, scripts/core/cortex/knowledge_validator.py]
title: 🧠 CORTEX - Índice da Documentação (Fase 01 + Fase 02 + Fase 03 + Retrospectiva)
---

# 🧠 CORTEX - Índice da Documentação (Fase 01 + Fase 02 + Fase 03 + Retrospectiva)

**Data:** 16 de Dezembro de 2025
**Status:** 🟢 Fase 01 Completa + Fase 02 Completa + Fase 03 (Knowledge Validator) em Design

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
|-----------|--------|--------|-----------|
| [CORTEX_FASE03_LINK_SCANNER_DESIGN.md](./CORTEX_FASE03_LINK_SCANNER_DESIGN.md) | [007] | ✅ Implementado | Extração de links semânticos do conteúdo |
| [CORTEX_FASE03_LINK_RESOLVER_DESIGN.md](./CORTEX_FASE03_LINK_RESOLVER_DESIGN.md) | [008] | ✅ Implementado | Resolução e validação de targets |
| [CORTEX_FASE03_VALIDATOR_DESIGN.md](./CORTEX_FASE03_VALIDATOR_DESIGN.md) | [009] | 🔵 Design | **Inversão de grafo e health metrics** |

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

## 🔄 HISTÓRICO DE VERSÕES

| Versão | Data | Mudanças |
|--------|------|----------|
| v1.3.0 | 2025-12-16 | **Retrospectiva:** Adicionados 40+ documentos de handover, troubleshooting, ADRs e lições aprendidas |
| v1.2.0 | 2025-12-14 | **Fase 03:** Design do Knowledge Validator (inversão de grafo + health metrics) |
| v1.1.0 | 2025-12-07 | **Fase 02:** Adição dos modelos `KnowledgeSource` e `KnowledgeEntry` (Pydantic v2) |
| v1.0.0 | 2025-11-30 | Design inicial completo (Fase 01) |

**Status Fase 01:** 🟢 **APROVADO E IMPLEMENTADO**
**Status Fase 02:** 🟢 **APROVADO E IMPLEMENTADO**
**Status Fase 03:** 🔵 **DESIGN EM APROVAÇÃO (Tarefa [009])**

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
**Autor:** Engineering Team
**Versão:** 1.3.0
