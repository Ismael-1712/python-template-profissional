---
id: cortex-fase03-readme
title: CORTEX Fase 3 - Visão Geral
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: 2025-12-14
tags:
  - fase-3
  - link-scanner
  - knowledge-graph
---

# 🧠 CORTEX Fase 3: The Link Scanner

**Missão [006]** - Transformando Nós Isolados em Grafo Conectado

---

## 📦 ARTEFATOS DESTE DESIGN

### 📄 Documentação

1. **[CORTEX_FASE03_LINK_SCANNER_DESIGN.md](./CORTEX_FASE03_LINK_SCANNER_DESIGN.md)** (Principal)
   - Design técnico completo (20+ páginas)
   - Arquitetura detalhada
   - Modelo de dados (Pydantic)
   - Estratégias de parsing (Regex)
   - Fluxo de processamento
   - Integração com CLI
   - Casos de uso

2. **[CORTEX_FASE03_EXECUTIVE_SUMMARY.md](./CORTEX_FASE03_EXECUTIVE_SUMMARY.md)** (Resumo)
   - Visão executiva (1 página)
   - Problema e solução
   - Arquitetura resumida
   - Roadmap de implementação
   - Critérios de aceitação

3. **[CORTEX_FASE03_DIAGRAMS.py](./CORTEX_FASE03_DIAGRAMS.py)** (Visualização)
   - Diagramas ASCII art
   - Fluxo de dados
   - Estrutura do grafo
   - Workflow da CLI

---

### 💻 Código (Protótipos)

4. **[../../scripts/core/cortex/link_analyzer_prototype.py](../../scripts/core/cortex/link_analyzer_prototype.py)**
   - Implementação funcional do `LinkAnalyzer`
   - Implementação funcional do `LinkResolver`
   - Modelos de dados (`KnowledgeLink`, `LinkType`)
   - Regex patterns validadas
   - Exemplo de uso executável

5. **[../../tests/test_link_analyzer_prototype.py](../../tests/test_link_analyzer_prototype.py)**
   - 29 testes unitários (100% passando ✅)
   - Cobertura completa das 3 regex
   - Testes de extração de links
   - Testes de edge cases

---

## 🚀 QUICK START

### Visualizar Diagramas

```bash
python docs/architecture/CORTEX_FASE03_DIAGRAMS.py
```

**Saída:** Diagramas ASCII mostrando arquitetura, fluxo de dados, regex patterns, etc.

---

### Executar Protótipo

```bash
python scripts/core/cortex/link_analyzer_prototype.py
```

**Saída:** Demonstração de extração de links de um documento de exemplo.

```
📋 Extracted 5 links:

1. [markdown] Line 9
   Target: ../knowledge_scanner.py
   Context: - Check [Knowledge Scanner](../knowledge_scanner.py) for i......

2. [wikilink] Line 8
   Target: CORTEX Fase 01
   Context: - See [[CORTEX Fase 01]] for the initial design...
```

---

### Executar Testes

```bash
pytest tests/test_link_analyzer_prototype.py -v
```

**Resultado Esperado:** 29 testes passando ✅

```
tests/test_link_analyzer_prototype.py::TestMarkdownLinkPattern::test_basic_markdown_link PASSED
tests/test_link_analyzer_prototype.py::TestWikilinkPattern::test_simple_wikilink PASSED
tests/test_link_analyzer_prototype.py::TestCodeReferencePattern::test_code_reference_file_only PASSED
...
============================== 29 passed in 0.33s ==============================
```

---

## 📚 LEITURA RECOMENDADA (Ordem)

**Para Product Owners / Stakeholders:**

1. Leia [CORTEX_FASE03_EXECUTIVE_SUMMARY.md](./CORTEX_FASE03_EXECUTIVE_SUMMARY.md) (5 min)
2. Execute `python docs/architecture/CORTEX_FASE03_DIAGRAMS.py` para visualizar (2 min)
3. Decisão: Aprovar ou solicitar ajustes

**Para Desenvolvedores:**

1. Leia [CORTEX_FASE03_EXECUTIVE_SUMMARY.md](./CORTEX_FASE03_EXECUTIVE_SUMMARY.md) (5 min)
2. Leia [CORTEX_FASE03_LINK_SCANNER_DESIGN.md](./CORTEX_FASE03_LINK_SCANNER_DESIGN.md) (30 min)
3. Execute o protótipo: `python scripts/core/cortex/link_analyzer_prototype.py` (2 min)
4. Analise o código: `scripts/core/cortex/link_analyzer_prototype.py` (15 min)
5. Revise os testes: `tests/test_link_analyzer_prototype.py` (10 min)

**Para Arquitetos:**

1. Leia [CORTEX_FASE03_LINK_SCANNER_DESIGN.md](./CORTEX_FASE03_LINK_SCANNER_DESIGN.md) completo
2. Revise decisões arquiteturais (Seção: Arquitetura do Componente)
3. Valide modelo de dados (Seção: Modelo de Dados)
4. Verifique estratégias de resolução (Seção: Resolução de Caminhos)

---

## ✅ STATUS DO DESIGN

| Componente | Status | Artefato |
|------------|--------|----------|
| **Especificação Técnica** | ✅ Completa | [CORTEX_FASE03_LINK_SCANNER_DESIGN.md](./CORTEX_FASE03_LINK_SCANNER_DESIGN.md) |
| **Resumo Executivo** | ✅ Completo | [CORTEX_FASE03_EXECUTIVE_SUMMARY.md](./CORTEX_FASE03_EXECUTIVE_SUMMARY.md) |
| **Diagramas Visuais** | ✅ Completos | [CORTEX_FASE03_DIAGRAMS.py](./CORTEX_FASE03_DIAGRAMS.py) |
| **Protótipo Funcional** | ✅ Implementado | [link_analyzer_prototype.py](../../scripts/core/cortex/link_analyzer_prototype.py) |
| **Testes Unitários** | ✅ 29 passando | [test_link_analyzer_prototype.py](../../tests/test_link_analyzer_prototype.py) |
| **Regex Patterns** | ✅ Validadas | 3 patterns com 100% cobertura |
| **Modelo de Dados** | ✅ Definido | `KnowledgeLink`, `LinkType`, extensão de `KnowledgeEntry` |
| **ADR (Architecture Decision Record)** | 🔵 Pendente | Documentar escolha de Composição vs Herança |

---

## 🎯 DECISÕES DE DESIGN PRINCIPAIS

### 1. Composição sobre Herança

**Decisão:** Criar `LinkAnalyzer` como componente independente ao invés de estender `KnowledgeScanner`.

**Justificativa:**

- Single Responsibility Principle
- Melhor testabilidade
- Maior reusabilidade

### 2. Pydantic para Modelos de Grafo

**Decisão:** Usar Pydantic BaseModel para `KnowledgeLink`.

**Justificativa:**

- Validação automática
- Serialização JSON nativa
- Imutabilidade (`frozen=True`)
- Consistência com `KnowledgeEntry` (Fase 2)

### 3. Múltiplas Estratégias de Resolução

**Decisão:** `LinkResolver` suporta 4 tipos de referências (ID, título, caminho, código).

**Justificativa:**

- Flexibilidade para diferentes estilos de escrita
- Compatibilidade com convenções existentes
- Suporte a migrações (links legados)

### 4. Grafo Bidirecional

**Decisão:** Armazenar tanto `outbound_links` quanto `inbound_link_ids`.

**Justificativa:**

- Navegação bidirecional (quem referencia / é referenciado)
- Performance (O(1) para backlinks)
- Análise de impacto de mudanças

---

## 🔄 PRÓXIMOS PASSOS

### Fase de Aprovação (Atual)

- [ ] Review do design técnico com equipe
- [ ] Validação de stakeholders (Product Owner)
- [ ] Aprovação final da arquitetura

### Fase 3.1: Link Extraction (MVP) - Semana 1

- [ ] Mover `link_analyzer_prototype.py` para `link_analyzer.py` (produção)
- [ ] Implementar `KnowledgeIndex` com busca fuzzy
- [ ] Integrar com `KnowledgeScanner` existente
- [ ] Testes de integração

### Fase 3.2: Link Resolution - Semana 2

- [ ] Implementar `LinkResolver` completo
- [ ] Adicionar resolução por caminho (frontmatter parsing)
- [ ] Integrar com `CodeLinkScanner` (validação de código)
- [ ] Testes de resolução (edge cases)

### Fase 3.3: Graph Building - Semana 2 (final)

- [ ] Estender `KnowledgeEntry` com campos de grafo
- [ ] Algoritmo de construção de backlinks
- [ ] Validação de consistência do grafo

### Fase 3.4: CLI Integration - Semana 3

- [ ] Comando `cortex knowledge-graph`
- [ ] Export JSON/DOT
- [ ] Integração com CI/CD
- [ ] Testes E2E

---

## 📞 CONTATO

**Responsável:** Engineering Team
**Data de Criação:** 14 de Dezembro de 2025
**Última Atualização:** 14 de Dezembro de 2025

**Para Dúvidas ou Feedback:**

- Abra uma Issue no repositório
- Marque o time com `@engineering-team`
- Use a tag `[CORTEX-FASE3]` no título

---

## 📜 LICENÇA

MIT License - Ver arquivo `LICENSE` na raiz do projeto.

---

**Status:** 🔵 Aguardando Aprovação
**Versão:** 0.1.0 (Design Phase)
