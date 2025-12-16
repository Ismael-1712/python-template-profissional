---
id: phase3-roadmap-hardening
type: history
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-16'
tags: [roadmap, refactoring, ux, security, phase-3]
context_tags: [modernization, technical-debt, quality]
linked_code:
  - scripts/audit/
  - scripts/utils/logger.py
  - scripts/utils/security.py
related_docs:
  - ../history/PHASE2_KNOWLEDGE_NODE_POSTMORTEM.md
  - ../guides/LLM_TASK_DECOMPOSITION_STRATEGY.md
  - ../history/SRE_TECHNICAL_DEBT_CATALOG.md
title: 'Fase 3 Roadmap: Hardening & UX - Deep Cleaning do Código Legado'
---

# Fase 3 Roadmap: Hardening & UX - Deep Cleaning do Código Legado

## 🎯 Visão Geral da Fase

**Tema:** Refatoração & UX (Deep Cleaning)

**Período Estimado:** Jan-Fev 2026

**Objetivo Estratégico:** Elevar o código legado ao padrão de qualidade estabelecido pelo CORTEX Knowledge Node (Fase 2), focando em **experiência de usuário**, **segurança** e **manutenibilidade**.

> **Filosofia:** Não criar novas features, mas pagar a dívida técnica para que a fundação suporte crescimento futuro sustentável.

---

## 📊 Estado Atual vs. Estado Desejado

| Aspecto | Estado Atual (Pós-Fase 2) | Estado Desejado (Pós-Fase 3) |
|---------|---------------------------|------------------------------|
| **UI de Scripts** | `print()` cru, sem cores | `rich.console` com tabelas/painéis |
| **Logging** | Mistura de `print()` e `logging` | 100% `logging` estruturado |
| **Segurança** | Secrets podem aparecer em logs | `mask_secret()` aplicado globalmente |
| **Tipagem de Audit** | Strings mágicas (`"critical"`) | Enums (`SecuritySeverity.CRITICAL`) |
| **Cobertura de Testes (Audit)** | ~40% | >80% |
| **Conformidade Mypy (Audit)** | ~60% | 100% (strict) |

---

## 🗺️ Mapa de Prioridades

### Legenda de Severidade

| Símbolo | Severidade | Critério |
|---------|-----------|----------|
| 🔴 | **P0 - CRÍTICO** | Impacta segurança ou experiência de usuário crítica |
| 🟡 | **P1 - ALTO** | Impacta DX ou qualidade de código significativamente |
| 🟢 | **P2 - MÉDIO** | Melhoria desejável, não bloqueante |

---

## 🚀 Iniciativas da Fase 3

### Iniciativa 1: [P13-Revision] Hardening de Segurança & UX

**Prioridade:** 🔴 **P0 - CRÍTICO**

**Contexto:** Scripts de auditoria atualmente expõem potencialmente informações sensíveis (API Keys, Tokens) e têm UI primitiva.

---

#### [P13.1] 🛡️ Hardening de Segurança em Logs

**Problema Identificado:**

```python
# scripts/audit/security_analyzer.py (ATUAL - INSEGURO)
def analyze_dependencies(config: dict):
    print(f"Analyzing with config: {config}")  # ❌ Pode conter API keys
```

**Solução Proposta:**

##### Etapa 1: Criar Utilitário de Masking

**Arquivo:** `scripts/utils/security.py` (novo ou expandir existente)

```python
import re
from typing import Any

# Padrões de secrets conhecidos
SECRET_PATTERNS = [
    r'(api[_-]?key\s*[:=]\s*)["\']?([a-zA-Z0-9_-]+)',  # API Keys
    r'(token\s*[:=]\s*)["\']?([a-zA-Z0-9_-]+)',        # Tokens
    r'(password\s*[:=]\s*)["\']?([^"\']+)',            # Passwords
    r'(secret\s*[:=]\s*)["\']?([a-zA-Z0-9_-]+)',       # Secrets
]

def mask_secret(text: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mascara valores sensíveis em strings.

    Args:
        text: Texto a ser mascarado
        mask_char: Caractere de máscara (default: '*')
        visible_chars: Número de caracteres visíveis no final (default: 4)

    Returns:
        Texto com secrets mascarados

    Example:
        >>> mask_secret("api_key: sk_live_abcdef123456")
        "api_key: **************3456"
    """
    masked_text = text
    for pattern in SECRET_PATTERNS:
        def replacer(match: re.Match[str]) -> str:
            key = match.group(1)  # Parte da chave (ex: "api_key=")
            value = match.group(2)  # Valor secreto

            if len(value) <= visible_chars:
                masked_value = mask_char * len(value)
            else:
                masked_value = (
                    mask_char * (len(value) - visible_chars)
                    + value[-visible_chars:]
                )

            return f"{key}{masked_value}"

        masked_text = re.sub(pattern, replacer, masked_text, flags=re.IGNORECASE)

    return masked_text


def safe_repr(obj: Any) -> str:
    """Representação segura de objeto (mascara valores sensíveis).

    Example:
        >>> safe_repr({"api_key": "secret123", "name": "test"})
        "{'api_key': '******123', 'name': 'test'}"
    """
    text = repr(obj)
    return mask_secret(text)
```

##### Etapa 2: Aplicar em Scripts de Audit

**Arquivo:** `scripts/audit/security_analyzer.py`

```python
from scripts.utils.security import safe_repr

def analyze_dependencies(config: dict):
    # ✅ SEGURO: Secrets mascarados automaticamente
    logger.info(f"Analyzing with config: {safe_repr(config)}")
```

**Critério de Validação:**

```python
# Teste em test_utils_security.py
def test_mask_secret_api_key():
    text = "api_key: sk_live_1234567890abcdef"
    result = mask_secret(text)
    assert "sk_live" not in result
    assert "1234567890ab" not in result
    assert "cdef" in result  # Últimos 4 caracteres visíveis
```

**Commits Previstos:**

1. `feat(security): add mask_secret utility (P13.1.1)`
2. `fix(audit): apply secret masking to security analyzer (P13.1.2)`
3. `fix(audit): apply secret masking to dependency analyzer (P13.1.3)`

---

#### [P13.2] 🎨 Modernização de UI com Rich

**Problema Identificado:**

```python
# scripts/audit/code_audit.py (ATUAL - PRIMITIVO)
print("=== Security Audit Report ===")
print(f"Total Issues: {len(issues)}")
for issue in issues:
    print(f"- {issue['severity']}: {issue['message']}")
```

**Output Atual (Primitivo):**

```
=== Security Audit Report ===
Total Issues: 5
- critical: SQL Injection vulnerability in auth.py
- high: Hardcoded credential in config.py
- medium: Missing input validation
```

**Solução Proposta:**

##### Etapa 1: Criar Formatador Rich

**Arquivo:** `scripts/audit/formatters.py` (novo)

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from enum import Enum

console = Console()

class SecuritySeverity(str, Enum):
    """Níveis de severidade de segurança."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

SEVERITY_COLORS = {
    SecuritySeverity.CRITICAL: "red bold",
    SecuritySeverity.HIGH: "orange_red1",
    SecuritySeverity.MEDIUM: "yellow",
    SecuritySeverity.LOW: "blue",
    SecuritySeverity.INFO: "cyan",
}

def format_security_report(issues: list[dict]) -> None:
    """Formata relatório de segurança com Rich.

    Args:
        issues: Lista de issues com campos 'severity', 'message', 'file'
    """
    # Criar tabela
    table = Table(title="🛡️ Security Audit Report", show_header=True)
    table.add_column("Severity", style="bold", width=12)
    table.add_column("File", style="cyan", width=30)
    table.add_column("Issue", width=60)

    # Agrupar por severidade
    critical_count = 0
    high_count = 0

    for issue in issues:
        severity = SecuritySeverity(issue["severity"])
        color = SEVERITY_COLORS[severity]

        if severity == SecuritySeverity.CRITICAL:
            critical_count += 1
        elif severity == SecuritySeverity.HIGH:
            high_count += 1

        table.add_row(
            f"[{color}]{severity.value.upper()}[/{color}]",
            issue.get("file", "N/A"),
            issue["message"],
        )

    # Mostrar tabela
    console.print(table)

    # Painel de resumo
    if critical_count > 0:
        summary_style = "red bold"
        status = "🔴 CRITICAL ISSUES FOUND"
    elif high_count > 0:
        summary_style = "yellow"
        status = "⚠️  HIGH PRIORITY ISSUES"
    else:
        summary_style = "green"
        status = "✅ NO CRITICAL ISSUES"

    summary = Panel(
        f"[{summary_style}]{status}[/{summary_style}]\n"
        f"Total Issues: {len(issues)} | Critical: {critical_count} | High: {high_count}",
        title="Summary",
        border_style=summary_style,
    )
    console.print(summary)
```

##### Etapa 2: Refatorar Audit Scripts

**Arquivo:** `scripts/audit/code_audit.py`

```python
from scripts.audit.formatters import format_security_report

def run_security_audit():
    # ... lógica de análise ...

    issues = [
        {
            "severity": "critical",
            "file": "src/auth.py",
            "message": "SQL Injection vulnerability detected",
        },
        # ... mais issues ...
    ]

    # ✅ UI Moderna
    format_security_report(issues)
```

**Output Novo (Rico):**

```
╭─────────────────── 🛡️ Security Audit Report ───────────────────╮
│ Severity     │ File              │ Issue                      │
├──────────────┼───────────────────┼────────────────────────────┤
│ CRITICAL     │ src/auth.py       │ SQL Injection detected     │
│ HIGH         │ config.py         │ Hardcoded credential       │
│ MEDIUM       │ api/routes.py     │ Missing input validation   │
╰─────────────────────────────────────────────────────────────────╯

╭─────────────────────── Summary ───────────────────────╮
│ 🔴 CRITICAL ISSUES FOUND                              │
│ Total Issues: 5 | Critical: 1 | High: 2               │
╰───────────────────────────────────────────────────────╯
```

**Commits Previstos:**

1. `feat(audit): add Rich formatters with severity enums (P13.2.1)`
2. `refactor(audit): modernize security_analyzer UI (P13.2.2)`
3. `refactor(audit): modernize dependency_analyzer UI (P13.2.3)`

---

#### [P13.3] 📊 Aplicar Enums em Código Legado

**Problema Identificado:**

```python
# ANTES (Strings Mágicas)
if issue["severity"] == "critical":  # ❌ Typo-prone, sem autocomplete
    alert_security_team()
```

**Solução:**

```python
# DEPOIS (Enums Tipados)
from scripts.audit.formatters import SecuritySeverity

if issue.severity == SecuritySeverity.CRITICAL:  # ✅ Mypy valida, autocomplete funciona
    alert_security_team()
```

**Arquivos a Refatorar:**

1. `scripts/audit/security_analyzer.py`
2. `scripts/audit/dependency_analyzer.py`
3. `scripts/audit/analyzer.py`
4. `scripts/audit/reporter.py`

**Enums a Criar:**

```python
# scripts/audit/models.py (novo)
from enum import Enum

class SecuritySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class SecurityCategory(str, Enum):
    INJECTION = "injection"
    AUTH = "authentication"
    CRYPTO = "cryptography"
    CONFIG = "configuration"
    DEPENDENCY = "dependency"

class AuditStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"
```

**Commits Previstos:**

1. `feat(audit): add security and audit enums (P13.3.1)`
2. `refactor(audit): replace severity strings with enum (P13.3.2)`
3. `refactor(audit): replace category strings with enum (P13.3.3)`

---

### Iniciativa 2: [P40] Tipagem Estrita em Testes

**Prioridade:** 🟡 **P1 - ALTO**

**Contexto:** Testes atualmente têm muitos `Any` e falta de type hints, dificultando detecção de bugs.

**Estratégia:** Aplicar [Protocolo de Fracionamento](../guides/LLM_TASK_DECOMPOSITION_STRATEGY.md) - 1 arquivo de teste por dia.

---

#### Etapas de Execução

##### Semana 1: Testes de Core

| Dia | Arquivo | Foco |
|-----|---------|------|
| D1 | `test_knowledge_scanner.py` | ✅ Já está tipado (Fase 2) |
| D2 | `test_knowledge_sync.py` | ✅ Já está tipado (Fase 2) |
| D3 | `test_cortex_metadata.py` | Adicionar type hints em fixtures |
| D4 | `test_link_analyzer.py` | Tipar retornos de mocks |
| D5 | `test_link_resolver.py` | Tipar fixtures complexas |

##### Semana 2: Testes de Audit

| Dia | Arquivo | Foco |
|-----|---------|------|
| D6 | `test_audit_analyzer.py` | Substituir `dict` por `TypedDict` |
| D7 | `test_audit_dashboard.py` | Tipar callbacks de UI |
| D8 | `test_reporter.py` | Adicionar generics em listas |

**Critério de Validação (Por Arquivo):**

```bash
# Deve passar sem erros
mypy tests/test_<nome>.py --strict
```

**Commits Previstos:** 1 commit por arquivo (8 commits totais)

---

### Iniciativa 3: [P41] Documentação de Débitos Técnicos Conhecidos

**Prioridade:** 🟢 **P2 - MÉDIO**

**Objetivo:** Atualizar [SRE_TECHNICAL_DEBT_CATALOG.md](../history/SRE_TECHNICAL_DEBT_CATALOG.md) com os débitos identificados na Fase 2.

**Novos Débitos a Documentar:**

#### Débito #7: Syncer Apenas Anexa Conteúdo

**Arquivo:** `scripts/core/cortex/knowledge_sync.py`
**Severidade:** 🟡 Média

**Como Resolver:**

```python
# Implementar marcadores de seção
<!-- BEGIN_SYNC_SECTION -->
Conteúdo sincronizado
<!-- END_SYNC_SECTION -->
```

---

#### Débito #8: Tipagem Ignorada em Requests

**Arquivo:** `scripts/core/cortex/knowledge_sync.py`
**Severidade:** 🟢 Baixa

**Como Resolver:**

```bash
pip install types-requests
# Remover: # type: ignore[import-untyped]
```

---

#### Débito #9: Scripts de Audit Sem Rich UI

**Arquivos:** `scripts/audit/*.py`
**Severidade:** 🟡 Alta (DX Impact)

**Resolução:** Iniciativa [P13.2] (esta fase)

---

### Iniciativa 4: [P42] Índice de Busca para Knowledge Node

**Prioridade:** 🟢 **P2 - MÉDIO** (Otimização de Performance)

**Problema Atual:**

```python
# Busca linear em knowledge_scanner.py
def find_entry(self, entry_id: str) -> KnowledgeEntry | None:
    for entry in self.scan():  # ❌ O(n) - rescanneia todo o diretório
        if entry.id == entry_id:
            return entry
```

**Solução Proposta:**

```python
# scripts/core/cortex/knowledge_index.py (novo)
from pathlib import Path
from typing import Dict
import json

class KnowledgeIndex:
    """Índice em memória para busca rápida de Knowledge Entries."""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self._index: Dict[str, Path] = {}

    def build(self, entries: list[KnowledgeEntry]) -> None:
        """Constrói índice a partir de lista de entries."""
        self._index = {entry.id: entry.file_path for entry in entries}
        self._save()

    def get(self, entry_id: str) -> Path | None:
        """Busca O(1) por ID."""
        return self._index.get(entry_id)

    def _save(self) -> None:
        """Persiste índice em disco."""
        data = {k: str(v) for k, v in self._index.items()}
        self.cache_file.write_text(json.dumps(data, indent=2))
```

**Commits Previstos:**

1. `feat(cortex): add KnowledgeIndex for O(1) lookups (P42.1)`
2. `refactor(cortex): integrate index in scanner (P42.2)`

---

## 📅 Cronograma Estimado

| Semana | Iniciativa | Deliverables |
|--------|-----------|--------------|
| **S1** | [P13.1] Hardening Segurança | `mask_secret()`, testes, aplicação em 3 scripts |
| **S2** | [P13.2] Rich UI | Formatadores, refatoração de 3 audit scripts |
| **S3** | [P13.3] Enums | Criar enums, substituir strings em 4 arquivos |
| **S4-S5** | [P40] Tipagem Testes | Tipar 8 arquivos de teste (1/dia) |
| **S6** | [P41] Docs Débitos | Atualizar catálogo de débitos técnicos |
| **S7** | [P42] Índice (Opcional) | Implementar busca O(1) se tempo permitir |

**Duração Total:** 6-7 semanas (~1.5 meses)

---

## 🎯 Critérios de Sucesso da Fase 3

| Métrica | Meta | Como Medir |
|---------|------|------------|
| **Scripts com Rich UI** | 100% (audit/) | Inspeção visual + grep `from rich` |
| **Secrets Mascarados** | 100% (logs) | Teste automatizado em `test_utils_security.py` |
| **Enums Aplicados** | 100% (audit/) | Mypy strict passa sem `# type: ignore` |
| **Cobertura Testes (Audit)** | >80% | `pytest --cov=scripts/audit` |
| **Conformidade Mypy (Strict)** | 100% | `mypy scripts/audit/ --strict` |

---

## ⚠️ Riscos e Mitigações

### Risco 1: Regressão em Scripts Críticos

**Probabilidade:** Média
**Impacto:** Alto

**Mitigação:**

- Aplicar protocolo de Micro-Etapas (1 arquivo/dia)
- Testes de regressão obrigatórios antes de cada commit
- Manter branch `phase3-backup` antes de iniciar

---

### Risco 2: Scope Creep (Adicionar Features Não Planejadas)

**Probabilidade:** Alta (histórico de 30% das fases)
**Impacto:** Médio

**Mitigação:**

- Manter foco em "Deep Cleaning", não em novas features
- Qualquer nova ideia vai para backlog da Fase 4
- Revisão semanal de escopo

---

## 🔄 Próxima Fase (Fase 4 - Previsão)

**Tema Provável:** Observabilidade & Métricas

**Iniciativas Candidatas:**

- [P50] Integração com Prometheus/Grafana
- [P51] Trace logging distribuído
- [P52] Dashboard de métricas de qualidade em tempo real

**Nota:** Fase 4 será planejada após conclusão da Fase 3.

---

## 📚 Referências

- [PHASE2_KNOWLEDGE_NODE_POSTMORTEM.md](../history/PHASE2_KNOWLEDGE_NODE_POSTMORTEM.md) - Contexto da fase anterior
- [LLM_TASK_DECOMPOSITION_STRATEGY.md](../guides/LLM_TASK_DECOMPOSITION_STRATEGY.md) - Metodologia de execução
- [SRE_TECHNICAL_DEBT_CATALOG.md](../history/SRE_TECHNICAL_DEBT_CATALOG.md) - Catálogo de débitos conhecidos
- [REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md](../guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md) - Protocolo de refatoração

---

**Status:** 📋 **PLANEJADO** (Aguardando finalização da Fase 2)

**Data de Início Prevista:** Janeiro 2026

**Owner:** Equipe de Engenharia (Human + LLM Agents)
