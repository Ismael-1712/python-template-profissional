# 📚 Documentação do Projeto

Bem-vindo à documentação do **Python Template Profissional**. Este índice organiza toda a documentação do projeto de forma clara e acessível.

---

## 🏗️ Estrutura da Documentação

### 📋 Documentação Principal

- **[index.md](index.md)** - Página inicial da documentação
- **[README_test_mock_system.md](README_test_mock_system.md)** - Sistema de geração de mocks

---

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

---

## 📖 Guias (`guides/`)

Guias práticos e tutoriais para desenvolvimento:

- **[testing.md](guides/testing.md)** - Guia de testes e estratégias de teste

- **[SMART_GIT_SYNC_GUIDE.md](guides/SMART_GIT_SYNC_GUIDE.md)** - Guia completo do sistema de sincronização Git inteligente

- **[SPRINT1_MIGRATION_GUIDE.md](guides/SPRINT1_MIGRATION_GUIDE.md)** - Guia de migração da Sprint 1

- **[SPRINT1_README.md](guides/SPRINT1_README.md)** - Documentação da Sprint 1

---

## 📚 Referência Técnica (`reference/`)

Documentação técnica detalhada:

- **[git_sync.md](reference/git_sync.md)** - Referência técnica do sistema de sincronização Git

---

## 📜 Histórico (`history/`)

### Sprint 1 - Foundation Phase (`history/sprint_1_foundation/`)

Relatórios e documentação histórica da Sprint 1 (fase de fundação):

#### Relatórios de Auditoria

- **P26_FASE02_RELATORIO_FINAL.md** - Relatório final da Fase 02
- **P26_FASE02_RELATORIO_PARCIAL.md** - Relatório parcial da Fase 02
- **P26_FASE02_3_RELATORIO_FINAL.md** - Relatório final Fase 02.3
- **P26_FASE02_4_5_RELATORIO_FINAL.md** - Relatório final Fase 02.4 e 02.5
- **P26_FASE02_6_RELATORIO_FINAL.md** - Relatório final Fase 02.6
- **P26_REFATORACAO_SCRIPTS_FASE01.md** - Refatoração de scripts da Fase 01

#### Auditorias de Código

- **P13_AUDITORIA_WARNINGS_NOQA.md** - Auditoria de warnings e noqa
- **P13_FASE02_CORRECOES_IMPLEMENTADAS.md** - Correções implementadas na Fase 02
- **P12_CODE_AUDIT_REFACTORING_ANALYSIS.md** - Análise de refatoração

#### Relatórios Sprint

- **SPRINT1_AUDITORIA_FASE01.md** - Auditoria da Fase 01
- **SPRINT1_AUDITORIA_SUMARIO.md** - Sumário das auditorias
- **SPRINT1_FASE02_RELATORIO.md** - Relatório da Fase 02

#### Discovery

- **FASE01_DISCOVERY_CEGUEIRA_FERRAMENTA.md** - Documentação de discovery sobre limitações de ferramentas

---

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

---

## 🔍 Busca de Documentação

```bash
# Buscar em toda a documentação
grep -r "termo" docs/

# Buscar apenas em arquitetura
grep -r "termo" docs/architecture/

# Buscar apenas em guias
grep -r "termo" docs/guides/

# Listar toda a estrutura
tree docs/
```

---

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
