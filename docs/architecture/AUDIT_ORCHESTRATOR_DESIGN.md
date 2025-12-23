---
id: audit-orchestrator-design
type: arch
status: draft
version: 0.1.0
author: GitHub Copilot + Engineering Team
date: 2025-12-23
context_tags:
  - refactoring
  - thin-cli
  - audit
  - architecture
  - orchestrator-pattern
linked_code:
  - scripts/core/cortex/audit_orchestrator.py
  - scripts/core/cortex/models.py
  - scripts/cortex/cli.py
related_docs:
---

# AUDIT ORCHESTRATOR - Design de Refatoração

## 📋 Contexto

**Problema Identificado:**
O comando `cortex audit` em `scripts/cortex/cli.py` viola o princípio de "Thin CLI", contendo lógica de negócio pesada misturada com apresentação.

**Violações Detectadas:**

- ✗ Lógica de validação de Knowledge Graph inline
- ✗ Verificação de Root Lockdown no CLI
- ✗ Auditoria de Metadados (Frontmatter) com lógica espalhada
- ✗ Geração de Relatórios acoplada à apresentação
- ✗ Condicionais complexas (flags `--links`, `--strict`, `--fail-on-error`)

## 🎯 Objetivo da Refatoração

Extrair a lógica de auditoria para um **Orquestrador** seguindo o padrão já estabelecido em:

- `scripts/core/cortex/project_orchestrator.py`
- `scripts/core/cortex/knowledge_orchestrator.py`
- `scripts/core/cortex/hooks_orchestrator.py`

## 🏗️ Arquitetura Proposta

### 1. Novo Componente: `AuditOrchestrator`

**Localização:** `scripts/core/cortex/audit_orchestrator.py`

**Responsabilidades:**

1. Coletar arquivos Markdown para auditoria
2. Coordenar auditoria de metadados (delegar para `MetadataAuditor`)
3. Coordenar auditoria de Knowledge Graph (delegar para `KnowledgeAuditor`)
4. Combinar resultados de múltiplas auditorias
5. Salvar relatórios de saúde

**Dependências:**

```python
- FrontmatterParser (scripts/core/cortex/metadata.py)
- MetadataAuditor (scripts/cortex/core/metadata_auditor.py)
- KnowledgeAuditor (scripts/cortex/core/knowledge_auditor.py)
- FileSystemAdapter (scripts/utils/filesystem.py)
```

### 2. Modelos de Resultado

**Localização:** `scripts/core/cortex/models.py`

Três novos modelos Pydantic para desacoplar resultados do CLI:

#### `MetadataAuditResult`

```python
- report: AuditReport
- files_audited: list[Path]
- root_violations: list[str]
- should_fail: bool

# Properties computadas:
- is_successful -> bool
- total_errors -> int
- total_warnings -> int
```

#### `KnowledgeAuditResult`

```python
- validation_report: ValidationReport
- num_entries: int
- total_links: int
- valid_links: int
- broken_links: int
- should_fail: bool
- output_path: Path

# Properties computadas:
- is_healthy -> bool
- health_score -> float
```

#### `FullAuditResult`

```python
- metadata_result: MetadataAuditResult | None
- knowledge_result: KnowledgeAuditResult | None
- should_fail: bool

# Properties computadas:
- is_successful -> bool
```

### 3. Interface Pública do Orquestrador

```python
class AuditOrchestrator:
    def __init__(
        self,
        workspace_root: Path,
        knowledge_dir: Path | None = None,
        fs: FileSystemAdapter | None = None,
    ) -> None:
        """Initialize audit orchestrator with dependencies."""

    def collect_markdown_files(
        self,
        path: Path,
    ) -> list[Path]:
        """Collect all Markdown files from path."""

    def run_metadata_audit(
        self,
        path: Path | None = None,
        *,
        fail_on_error: bool = False,
    ) -> MetadataAuditResult:
        """Run metadata audit on documentation files."""

    def run_knowledge_audit(
        self,
        *,
        strict: bool = False,
        output_path: Path | None = None,
    ) -> KnowledgeAuditResult:
        """Run Knowledge Graph audit and generate health report."""

    def run_full_audit(
        self,
        path: Path | None = None,
        *,
        check_links: bool = False,
        fail_on_error: bool = False,
        strict: bool = False,
        output_path: Path | None = None,
    ) -> FullAuditResult:
        """Run combined metadata and Knowledge Graph audit."""

    def save_knowledge_report(
        self,
        validation_report: ValidationReport,
        output_path: Path,
    ) -> None:
        """Save Knowledge Graph health report to file."""
```

## 📊 Diagrama de Fluxo (Antes vs. Depois)

### ANTES (Thin CLI Violado)

```
┌─────────────────┐
│  cortex audit   │
│   (cli.py)      │
├─────────────────┤
│ • Parse args    │
│ • Validate KG   │◄── Lógica de negócio no CLI!
│ • Check Root    │
│ • Audit Metadata│
│ • Generate Report│
│ • Display UI    │
└─────────────────┘
```

### DEPOIS (Thin CLI Restaurado)

```
┌─────────────────┐         ┌──────────────────────┐
│  cortex audit   │         │  AuditOrchestrator   │
│   (cli.py)      │────────►│  (audit_orchestrator)│
├─────────────────┤         ├──────────────────────┤
│ • Parse args    │         │ • Collect files      │
│ • Call orchestrator        │ • Delegate metadata  │
│ • Display results│◄────────│ • Delegate KG        │
└─────────────────┘         │ • Combine results    │
                            └──────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Metadata   │ │  Knowledge   │ │   Report     │
            │   Auditor    │ │   Auditor    │ │  Generator   │
            └──────────────┘ └──────────────┘ └──────────────┘
```

## 🧪 Mapeamento de Responsabilidades

### Responsabilidades Extraídas de `cli.audit()`

| Responsabilidade | Localização Atual | Nova Localização |
|-----------------|-------------------|------------------|
| Parse argumentos CLI | `cli.py` | ✓ Permanece no CLI |
| Validação Knowledge Graph | `cli.py` (inline) | `AuditOrchestrator.run_knowledge_audit()` |
| Verificação Root Lockdown | `cli.py` (via MetadataAuditor) | `AuditOrchestrator.run_metadata_audit()` |
| Auditoria de Metadados | `cli.py` (via MetadataAuditor) | `AuditOrchestrator.run_metadata_audit()` |
| Cálculo de métricas | `cli.py` (inline) | `KnowledgeAuditResult` (property) |
| Salvar relatórios | `cli.py` (inline) | `AuditOrchestrator.save_knowledge_report()` |
| Display de resultados | `cli.py` + `UIPresenter` | ✓ Permanece no CLI |

## 🔄 Etapas de Implementação

### ✅ Etapa 01: DESIGN (Concluída)

- [x] Criar estrutura de `AuditOrchestrator`
- [x] Definir modelos de resultado em `models.py`
- [x] Documentar interface pública com type hints
- [x] Adicionar properties computadas nos modelos
- [x] Usar `NotImplementedError` para métodos pendentes

### ✅ Etapa 02: IMPLEMENTAÇÃO (Concluída)

- [x] Implementar `collect_markdown_files()`
- [x] Implementar `run_metadata_audit()`
- [x] Implementar `run_knowledge_audit()`
- [x] Implementar `run_full_audit()`
- [x] Implementar `save_knowledge_report()`
- [x] Criar testes unitários (16 testes, 100% pass)

### ✅ Etapa 03: INTEGRAÇÃO (Concluída)

- [x] Refatorar `cli.audit()` para usar `AuditOrchestrator`
- [x] Mover lógica de negócio para orquestrador
- [x] Manter apenas apresentação no CLI
- [x] Atualizar imports e dependências
- [x] Validar comportamento funcional (testes manuais)

### ⏭️ Etapa 04: VALIDAÇÃO

### ⏭️ Etapa 03: INTEGRAÇÃO (Concluída)

- [x] Refatorar `cli.audit()` para usar `AuditOrchestrator`
- [x] Mover lógica de negócio para orquestrador
- [x] Manter apenas apresentação no CLI
- [x] Atualizar imports e dependências
- [x] Validar comportamento funcional (testes manuais)

### ⏭️ Etapa 04: VALIDAÇÃO

- [ ] Criar testes de integração end-to-end
- [ ] Validar comportamento funcional inalterado (regression tests)
- [ ] Executar auditoria de código (`dev-audit`)
- [ ] Atualizar documentação final
- [ ] Marcar como concluído

## 🎨 Padrões de Design Aplicados

1. **Facade Pattern**: `AuditOrchestrator` simplifica interface complexa
2. **Delegation Pattern**: Delega para `MetadataAuditor` e `KnowledgeAuditor`
3. **Result Object Pattern**: Modelos Pydantic encapsulam resultados
4. **Dependency Injection**: `FileSystemAdapter` injetado no `__init__`
5. **Keyword-Only Arguments**: Flags booleanos como `*, fail_on_error=False`

## 📝 Decisões de Design

### Por que Pydantic em vez de `@dataclass`?

- ✓ Consistência com outros modelos (`DocumentMetadata`, `KnowledgeEntry`)
- ✓ Validação automática em tempo de execução
- ✓ Suporte nativo a `@property` em frozen models
- ✓ Serialização/desserialização built-in

### Por que separar os modelos em `models.py`?

- ✓ Evitar importações circulares
- ✓ Centralizar definições de tipos
- ✓ Facilitar reuso entre módulos
- ✓ Seguir padrão estabelecido no projeto

### Por que usar `NotImplementedError`?

- ✓ Sinaliza claramente interface incompleta
- ✓ Permite validar estrutura antes da implementação
- ✓ Falha rápida se usado prematuramente
- ✓ Type checkers reconhecem como "never returns"

## 🔗 Relações com Outros Componentes

```
AuditOrchestrator
├── Depende de:
│   ├── MetadataAuditor (core/metadata_auditor.py)
│   ├── KnowledgeAuditor (core/knowledge_auditor.py)
│   ├── FrontmatterParser (core/metadata.py)
│   └── FileSystemAdapter (utils/filesystem.py)
│
├── É usado por:
│   └── cortex audit (cortex/cli.py)
│
└── Retorna:
    ├── MetadataAuditResult
    ├── KnowledgeAuditResult
    └── FullAuditResult
```

## ⚠️ Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Regressão funcional | Testes end-to-end antes e depois |
| Importações circulares | TYPE_CHECKING e imports locais |
| Compatibilidade com CLI existente | Manter interface pública inalterada |
| Performance overhead | Medir com benchmarks pré/pós |

## 📌 Conclusão

Esta refatoração restaura o princípio de **Thin CLI** no CORTEX, movendo a lógica de auditoria para um orquestrador dedicado. O design segue padrões estabelecidos no projeto e facilita:

- ✅ Testabilidade (lógica isolada do CLI)
- ✅ Reusabilidade (pode ser chamado por outras interfaces)
- ✅ Manutenibilidade (responsabilidades claras)
- ✅ Extensibilidade (novos tipos de auditoria podem ser adicionados)

---

**Status:** 🟢 Etapa 03 concluída - CLI integrado ao orquestrador
**Próximo Passo:** Testes de integração e validação final (Etapa 04)
**Testes Unitários:** ✅ 16/16 passando
**Testes Manuais:** ✅ Validado com `cortex audit`, `--links`, `--fail-on-error`
