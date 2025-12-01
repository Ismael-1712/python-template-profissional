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

## 🎯 Navegação Rápida

### Para Novos Desenvolvedores

1. Comece pelo **[TRIAD_GOVERNANCE.md](architecture/TRIAD_GOVERNANCE.md)** para entender a arquitetura
2. Leia o **[SMART_GIT_SYNC_GUIDE.md](guides/SMART_GIT_SYNC_GUIDE.md)** para workflow de Git
3. Consulte **[testing.md](guides/testing.md)** para padrões de teste

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
