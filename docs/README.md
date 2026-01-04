---
id: readme
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code: []
title: Documentação do Projeto
---

# 📚 Documentação do Projeto

Bem-vindo à documentação do **Python Template Profissional**. Este índice organiza toda a documentação do projeto de forma clara e acessível.

## 🏛️ Arquitetura (`architecture/`)

Documentação sobre os princípios arquiteturais e decisões de design do projeto:

- **[TRIAD_GOVERNANCE.md](architecture/TRIAD_GOVERNANCE.md)** - 🎯 **CONSTITUIÇÃO DO PROJETO**
  - Manifesto da Tríade (main/cli/api)
  - Regras de governança entre branches
  - Princípios de não-contaminação
  - Robô de propagação inteligente

- **[ARCHITECTURE_TRIAD.md](architecture/ARCHITECTURE_TRIAD.md)** - Detalhes técnicos da arquitetura em tríade

- **[CODE_AUDIT.md](architecture/CODE_AUDIT.md)** - Sistema de auditoria de código

- **[AUDIT_DASHBOARD_INTEGRATION.md](architecture/AUDIT_DASHBOARD_INTEGRATION.md)** - Integração do dashboard de auditoria

## 📚 Referência Técnica (`reference/`)

Documentação técnica detalhada:

- **[git_sync.md](reference/git_sync.md)** - Referência técnica do sistema de sincronização Git

## 📜 Histórico de Evolução (`history/`)

Postmortems, retrospectivas e roadmaps de cada fase do projeto:

- **[PHASE2_KNOWLEDGE_NODE_POSTMORTEM.md](history/PHASE2_KNOWLEDGE_NODE_POSTMORTEM.md)** - 🧠 **Retrospectiva da Fase 2**
  - Implementação do CORTEX Knowledge Node
  - Modelo de Sucesso P31 (Micro-Etapas Atômicas)
  - Protocolo de Auditoria Ping-Pong
  - Lições sobre limitações de LLMs em tarefas complexas

- **[PHASE3_ROADMAP_HARDENING.md](history/PHASE3_ROADMAP_HARDENING.md)** - 🚀 **Roadmap da Fase 3**
  - Hardening de segurança (`mask_secret()`)
  - Modernização de UI com Rich
  - Aplicação de Enums em código legado
  - Tipagem estrita em testes

## 🎓 Guias de Melhores Práticas (`guides/`)

Metodologias e padrões validados em produção:

- **[LLM_TASK_DECOMPOSITION_STRATEGY.md](guides/LLM_TASK_DECOMPOSITION_STRATEGY.md)** - 🤖 **Estratégia de Decomposição de Tarefas**
  - Modelo P31: Como dividir tarefas complexas em micro-etapas
  - Os 3 Critérios de Atomicidade (Comitável + Testável + Independente)
  - Protocolo de Auditoria Ping-Pong
  - Padrões de decomposição validados

- **[REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md](guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md)** - Protocolo de Fracionamento Iterativo

## 📊 Relatórios Técnicos (`reports/`)

Análises técnicas, métricas de débito técnico e planos de ação:

- **[TDD_GUARDIAN_FORENSICS.md](reports/TDD_GUARDIAN_FORENSICS.md)** - 🛡️ **Análise Forense do TDD Guardian**
  - Análise forense da cobertura de testes em scripts
  - Levantamento de débito técnico (~140 arquivos sem cobertura padronizada)
  - Plano de expansão do TDD Guardian (Fase 1: Warn-Only implementada)
  - Roadmap de endurecimento progressivo (Q1-Q3 2026)

## 🎯 Navegação Rápida

### Para Novos Desenvolvedores

1. Comece pelo **[TRIAD_GOVERNANCE.md](architecture/TRIAD_GOVERNANCE.md)** para entender a arquitetura
2. Leia o **[LLM_TASK_DECOMPOSITION_STRATEGY.md](guides/LLM_TASK_DECOMPOSITION_STRATEGY.md)** para metodologia de trabalho com LLMs
3. Leia o **[SMART_GIT_SYNC_GUIDE.md](guides/SMART_GIT_SYNC_GUIDE.md)** para workflow de Git
4. Consulte **[testing.md](guides/testing.md)** para padrões de teste

### Para LLMs e Agentes de IA

1. **SEMPRE** leia **[LLM_TASK_DECOMPOSITION_STRATEGY.md](guides/LLM_TASK_DECOMPOSITION_STRATEGY.md)** antes de tarefas complexas
2. Revise **[PHASE2_KNOWLEDGE_NODE_POSTMORTEM.md](history/PHASE2_KNOWLEDGE_NODE_POSTMORTEM.md)** para aprender com sucessos/falhas anteriores
3. Consulte **[PHASE3_ROADMAP_HARDENING.md](history/PHASE3_ROADMAP_HARDENING.md)** para entender próximas prioridades

### Para Entender o Sistema

- **Arquitetura**: Veja `architecture/`
- **Workflows**: Consulte `guides/`
- **Referências**: Explore `reference/`

### Para Contexto Histórico

- **Sprint 1**: Todos os relatórios em `history/sprint_1_foundation/`

## 📝 Contribuindo para a Documentação

Ao adicionar nova documentação:

- **Arquitetura**: Coloque em `docs/architecture/`
- **Guias práticos**: Coloque em `docs/guides/`
- **Referências técnicas**: Coloque em `docs/reference/`
- **Relatórios históricos**: Coloque em `docs/history/sprint_X/`

Mantenha a raiz de `docs/` limpa - apenas este README e arquivos essenciais.

---

**Última Atualização**: Novembro 2025
**Status**: Documentação Ativa
**Contato**: Ver [CONTRIBUTING.md](../CONTRIBUTING.md)
