---
id: rep-complexity-god-functions
type: knowledge
status: active
version: 1.0.0
author: CORTEX Architecture
date: '2026-01-04'
context_tags:
  - refactoring
  - technical-debt
  - complexity
  - god-functions
  - maintenance
linked_code:
  - scripts/core/cortex/knowledge_validator.py
  - scripts/core/cortex/knowledge_orchestrator.py
  - scripts/core/cortex/metadata.py
  - scripts/core/cortex/migrate.py
golden_paths:
  - path: "Identificar funções com alta complexidade → Criar testes de caracterização → Aplicar Extract Method → Validar com make test"
    description: "Fluxo seguro de refatoração de God Functions"
  - path: "Rank D (CC > 20) → Prioridade máxima → Dividir em funções < 15 CC"
    description: "Critério de priorização para refatoração"
title: Matriz de Prioridade de Refatoração - God Functions
---

# 📉 Matriz de Prioridade de Refatoração: "God Functions"

**Data da Análise:** 04 de Janeiro de 2026
**Ferramentas Utilizadas:** Radon (CC - Cyclomatic Complexity)
**Escopo:** 858 blocos analisados (scripts/ + src/)
**Complexidade Média Global:** A (3.6) ✅

## 🧠 O Que é uma "God Function"?

Uma função que "sabe demais" ou "faz demais". Alta complexidade ciclomática indica código difícil de testar, propenso a bugs e caro para manter.

### Critérios de Classificação
- **Rank A (1-5):** Baixa complexidade (Ideal) ✅
- **Rank B (6-10):** Baixo risco 🟢
- **Rank C (11-20):** Moderado (Alerta 🚧)
- **Rank D (21-40):** Alta complexidade (Perigo ⚠️)
- **Rank E (41+):** Instabilidade Extrema (Emergência 🚨)

---

## 📋 RELATÓRIO DE DÍVIDA TÉCNICA (Ordenado por Criticidade)

### 🚨 NÍVEL 1: CRITICIDADE EXTREMA (RANK E - F)
_Refatoração Obrigatória. Este código é instável, difícil de testar e propenso a bugs._

**Status:** ✅ **NENHUMA FUNÇÃO NESTE NÍVEL**
O projeto não possui funções com complexidade superior a 40 (Rank E).

---

### ⚠️ NÍVEL 2: ALTA CRITICIDADE (RANK D)
_Refatoração Recomendada. Código denso que dificulta a manutenção._

| Rank | CC Score | Arquivo | Função / Método | Linha |
| :---: | :---: | --- | --- | :---: |
| **D** | **29** | `scripts/core/cortex/metadata.py` | `FrontmatterParser.validate_metadata` | 139 |
| **D** | **23** | `scripts/core/cortex/knowledge_orchestrator.py` | `KnowledgeOrchestrator.sync_multiple` | 167 |
| **D** | **21** | `scripts/core/cortex/migrate.py` | `DocumentMigrator.print_summary` | 386 |

**Total de Funções Rank D:** 3
**Impacto:** Alta criticidade no sistema CORTEX (Documentation as Code).

---

### 🚧 NÍVEL 3: MODERADA CRITICIDADE (RANK C - Top 15)
_Monitorar. Não quebra o sistema, mas pode ser simplificado._

| Rank | CC Score | Arquivo | Função / Método | Linha |
| :---: | :---: | --- | --- | :---: |
| **C** | **20** | `scripts/cli/mock_generate.py` | `main` | 36 |
| **C** | **18** | `scripts/git_sync/sync_logic.py` | `SyncOrchestrator._prune_merged_local_branches` | 457 |
| **C** | **17** | `scripts/cli/install_dev.py` | `install_dev_environment` | 172 |
| **C** | **17** | `scripts/cli/audit.py` | `main` | 316 |
| **C** | **16** | `scripts/git_sync/sync_logic.py` | `SyncOrchestrator._generate_smart_commit_message` | 312 |
| **C** | **15** | `scripts/cortex/commands/docs.py` | `generate_docs` | 125 |
| **C** | **15** | `scripts/cli/mock_ci.py` | `main` | 283 |
| **C** | **15** | `scripts/cli/audit.py` | `CodeAuditor.run_audit` | 224 |
| **C** | **15** | `scripts/core/mock_generator.py` | `TestMockGenerator.scan_test_files` | 263 |
| **C** | **15** | `scripts/core/cortex/mapper.py` | `ProjectMapper._format_knowledge_markdown` | 472 |
| **C** | **14** | `scripts/example_guardian_scanner.py` | `main` | 15 |
| **C** | **14** | `scripts/cortex/adapters/ui.py` | `UIPresenter.display_audit_results` | 212 |
| **C** | **14** | `scripts/ci_recovery/executor.py` | `run_command` | 19 |
| **C** | **14** | `scripts/core/cortex/knowledge_scanner.py` | `KnowledgeScanner.scan` | 81 |
| **C** | **14** | `scripts/core/mock_ci/git_ops.py` | `GitOperations.run_command` | 47 |

**Total de Funções Rank C (min 11):** 38
**Complexidade Média (Rank C):** 14.2

---

## 🎯 Análise de Impacto por Módulo

### 📦 Módulos Mais Afetados (Concentração de Dívida)

| Módulo | Funções Rank D | Funções Rank C | Total Débito |
| --- | :---: | :---: | :---: |
| **CORTEX (scripts/core/cortex/)** | 3 | 8 | **11** ⚠️ |
| **CLI Tools (scripts/cli/)** | 0 | 6 | 6 |
| **Git Sync (scripts/git_sync/)** | 0 | 3 | 3 |
| **Mock System** | 0 | 3 | 3 |
| **Audit System** | 0 | 4 | 4 |

**Conclusão:** O módulo **CORTEX** concentra a maior dívida técnica (3 funções Rank D + 8 Rank C).

---

## 🛠️ Plano de Ação Sugerido

### 🎯 Prioridade 1: Refatorar Rank D (CORTEX)

#### 1. `FrontmatterParser.validate_metadata` (CC: 29)
**Arquivo:** `scripts/core/cortex/metadata.py:139`
**Problema:** Validação monolítica com 29 branches de decisão.
**Estratégia:**
- Extrair validação de cada campo para métodos auxiliares privados
- Implementar pattern Chain of Responsibility para validators
- Adicionar testes unitários antes da refatoração

**Ticket Sugerido:** `refactor(cortex): split validate_metadata into validators chain`

#### 2. `KnowledgeOrchestrator.sync_multiple` (CC: 23)
**Arquivo:** `scripts/core/cortex/knowledge_orchestrator.py:167`
**Problema:** Orquestração complexa de sincronização de múltiplos documentos.
**Estratégia:**
- Extrair lógica de sincronização individual para método privado
- Aplicar pattern Strategy para diferentes tipos de sincronização
- Mover tratamento de erros para decorator

**Ticket Sugerido:** `refactor(cortex): simplify sync_multiple orchestration`

#### 3. `DocumentMigrator.print_summary` (CC: 21)
**Arquivo:** `scripts/core/cortex/migrate.py:386`
**Problema:** Formatação de output com muitas condicionais.
**Estratégia:**
- Mover formatação para classe Formatter dedicada
- Usar template method pattern para diferentes formatos
- Separar lógica de cálculo da apresentação

**Ticket Sugerido:** `refactor(cortex): extract summary formatting to dedicated formatter`

---

### 🎯 Prioridade 2: Monitorar Rank C (Top 5)

| Função | CC | Ação Recomendada |
| --- | :---: | --- |
| `mock_generate.py:main` | 20 | Extrair subcomandos para funções |
| `SyncOrchestrator._prune_merged_local_branches` | 18 | Simplificar lógica de filtragem |
| `install_dev.py:install_dev_environment` | 17 | Extrair steps de instalação |
| `audit.py:main` | 17 | Aplicar Command Pattern |
| `SyncOrchestrator._generate_smart_commit_message` | 16 | Usar template strings |

---

## 📊 Métricas de Sucesso

### Baseline Atual (04 Jan 2026)
- ✅ Complexidade Média Global: **A (3.6)**
- ⚠️ Funções Rank D: **3**
- 🚧 Funções Rank C (11+): **38**
- 🚨 Funções Rank E: **0**

### Metas Q1 2026
- 🎯 Reduzir Rank D para: **0** (eliminar todas as 3 funções)
- 🎯 Reduzir Rank C para: **< 25** (65% do atual)
- 🎯 Manter Rank E: **0**
- 🎯 Manter Média Global: **A (< 5.0)**

---

## 🔄 Processo de Refatoração Segura

### Checklist Obrigatório (ANTES de tocar em God Function)

1. **✅ Cobertura de Testes:** Garantir >= 80% de cobertura na função antes de refatorar
2. **✅ Testes de Caracterização:** Criar testes que documentem o comportamento atual
3. **✅ Isolamento:** Usar mocks/stubs para dependências externas
4. **✅ Benchmark:** Medir performance antes (se aplicável)
5. **✅ Documentação:** Registrar decisões de design no código

### Técnicas de Refatoração Recomendadas

- **Extract Method:** Mover blocos lógicos para funções auxiliares privadas
- **Replace Conditional with Polymorphism:** Substituir if/else por Strategy/Command Pattern
- **Introduce Parameter Object:** Agrupar parâmetros relacionados em dataclass
- **Decompose Conditional:** Simplificar expressões booleanas complexas
- **Replace Temp with Query:** Eliminar variáveis temporárias com métodos de acesso

---

## 📚 Referências

- **Radon Documentation:** https://radon.readthedocs.io/
- **Cyclomatic Complexity (Wikipedia):** https://en.wikipedia.org/wiki/Cyclomatic_complexity
- **Refactoring Catalog (Martin Fowler):** https://refactoring.com/catalog/
- **CORTEX Architecture:** `docs/architecture/CORTEX_INDICE.md`

---

## 🔗 Relacionados

- **TDD Guardian Forensics:** `docs/reports/TDD_GUARDIAN_FORENSICS.md`
- **Engineering Standards:** `docs/guides/ENGINEERING_STANDARDS.md`
- **Refactoring Protocol:** `docs/guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md`

---

**Última Atualização:** 04 de Janeiro de 2026
**Próxima Revisão:** 04 de Abril de 2026 (Trimestral)
