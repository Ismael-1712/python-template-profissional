---
id: architecture-data-models
type: arch
status: active
version: 1.0.0
author: DevOps Team
date: 2025-12-05
title: "Arquitetura de Modelos de Dados"
summary: "Definição dos modelos Pydantic para Mock CI Integration"
related:
  - docs/architecture/MOCK_CI_REFACTORING.md
  - scripts/core/mock_ci/models.py
tags:
  - pydantic
  - data-models
  - validation
  - mock-ci
---

# Arquitetura de Modelos de Dados

## Visão Geral

Este documento descreve a arquitetura dos modelos de dados utilizados no sistema Mock CI Integration. A transição de Dataclasses para **Pydantic v2** foi realizada na Sprint P14, trazendo benefícios significativos de validação, serialização e type-safety.

## Transição: Dataclasses → Pydantic

### Motivação

A migração para Pydantic foi motivada por:

1. **Validação Automática**: Validação de tipos e valores na criação dos objetos
2. **Serialização Robusta**: Conversão automática para JSON/dict com suporte a tipos complexos
3. **Imutabilidade**: Proteção contra modificações acidentais com `frozen=True`
4. **Documentação**: Schema JSON automático para integração com ferramentas externas
5. **Performance**: Validação otimizada em Rust (Pydantic v2)

### Benefícios Implementados

- ✅ **Type Safety**: Validação estrita de tipos em runtime
- ✅ **Imutabilidade**: Modelos imutáveis onde apropriado (`GitInfo`, `MockSuggestion`, `MockSuggestions`)
- ✅ **Validadores Customizados**: Regras de negócio aplicadas automaticamente
- ✅ **Serialização Consistente**: Métodos `model_dump()` e `to_dict()` padronizados
- ✅ **Enums Tipados**: Uso de `str, Enum` para valores controlados

## Modelos Principais

### 1. GitInfo (Imutável)

Encapsula informações do repositório Git.

```python
from pydantic import BaseModel, ConfigDict

class GitInfo(BaseModel):
    """Informações sobre o repositório git."""

    model_config = ConfigDict(frozen=True)

    is_git_repo: bool = False
    has_changes: bool = False
    current_branch: str | None = None
    commit_hash: str | None = None
```

**Características:**

- Imutável (`frozen=True`)
- Campos opcionais com valores padrão seguros

### 2. MockSuggestion (Imutável)

Representa uma sugestão de mock detectada.

```python
class MockSuggestion(BaseModel):
    """Sugestão de mock para um teste."""

    model_config = ConfigDict(frozen=True)

    severity: str  # "HIGH" | "MEDIUM" | "LOW"
    mock_type: str  # Ver MockType enum
    file_path: str
    line_number: int
    reason: str
    pattern: str | None = None

    @field_validator("line_number")
    @classmethod
    def validate_line_number(cls, v: int) -> int:
        """Valida que o número da linha é positivo."""
        if v <= 0:
            msg = "line_number deve ser maior que 0"
            raise ValueError(msg)
        return v
```

**Validadores:**

- `line_number` deve ser > 0 (números de linha começam em 1)

**Conversores de Enum:**

```python
suggestion.severity_enum  # Retorna Severity.HIGH
suggestion.mock_type_enum  # Retorna MockType.HTTP_REQUEST
```

### 3. MockSuggestions (Imutável)

Agregação de múltiplas sugestões com métricas.

```python
class MockSuggestions(BaseModel):
    """Agregação de sugestões de mock."""

    model_config = ConfigDict(frozen=True)

    total: int
    high_priority: int
    blocking: int
    details: list[MockSuggestion] = Field(default_factory=list)
```

**Factory Method:**

```python
suggestions = MockSuggestions.from_suggestions_list(
    suggestions=[...],
    blocking_mock_types={"HTTP_REQUEST", "DATABASE"}
)
```

### 4. CIReport (Mutável)

Relatório completo de uma execução CI/CD.

```python
class CIReport(BaseModel):
    """Relatório completo de verificação CI/CD."""

    timestamp: str
    environment: str
    workspace: str
    git_info: GitInfo
    validation_results: dict[str, bool]
    mock_suggestions: MockSuggestions
    summary: dict[str, Any]
    recommendations: list[str]
    status: str  # "SUCCESS" | "WARNING" | "FAILURE"
```

**Uso:**

```python
report = CIReport(
    timestamp="2025-12-05T12:00:00Z",
    environment="ci",
    workspace="/project",
    git_info=GitInfo(is_git_repo=True, current_branch="main"),
    validation_results={"mock_config": True, "test_structure": True},
    mock_suggestions=MockSuggestions(total=5, high_priority=2, blocking=1),
    summary={"total_tests": 42, "coverage": 85.5},
    recommendations=["Adicionar mocks HTTP"],
    status="SUCCESS"
)

# Serialização
report_dict = report.to_dict()  # Compatibilidade com código legado
report_json = report.model_dump_json()  # JSON string
```

### 5. FixResult (Mutável)

Resultado da aplicação de correções automáticas.

```python
class FixResult(BaseModel):
    """Resultado de aplicação de correções automáticas."""

    timestamp: str
    validation_fixes: int
    mock_fixes_applied: int
    mock_fixes_details: dict[str, Any]
    total_fixes: int
    commit_created: bool = False
    commit_message: str | None = None
```

## Enums Disponíveis

### Severity

```python
class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
```

### MockType

```python
class MockType(str, Enum):
    HTTP_REQUEST = "HTTP_REQUEST"
    SUBPROCESS = "SUBPROCESS"
    FILE_IO = "FILE_IO"
    DATABASE = "DATABASE"
    DATETIME = "DATETIME"
    RANDOM = "RANDOM"
    ENVIRONMENT = "ENVIRONMENT"
    NETWORK = "NETWORK"
    EXTERNAL_API = "EXTERNAL_API"
```

### CIStatus

```python
class CIStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILURE = "FAILURE"
```

## Exemplo Completo: Criação de CIReport

```python
from scripts.core.mock_ci.models import (
    CIReport,
    GitInfo,
    MockSuggestions,
    MockSuggestion,
)

# 1. Criar informações do Git (imutável)
git_info = GitInfo(
    is_git_repo=True,
    has_changes=False,
    current_branch="feature/pydantic-migration",
    commit_hash="a1b2c3d"
)

# 2. Criar sugestões de mock (imutáveis)
suggestion1 = MockSuggestion(
    severity="HIGH",
    mock_type="HTTP_REQUEST",
    file_path="tests/test_api.py",
    line_number=42,
    reason="Requisição HTTP não mockada",
    pattern="requests.get"
)

suggestion2 = MockSuggestion(
    severity="MEDIUM",
    mock_type="DATETIME",
    file_path="tests/test_utils.py",
    line_number=15,
    reason="Timestamp fixo recomendado para testes",
)

suggestions = MockSuggestions(
    total=2,
    high_priority=1,
    blocking=1,
    details=[suggestion1, suggestion2]
)

# 3. Criar relatório completo
report = CIReport(
    timestamp="2025-12-05T15:30:00Z",
    environment="github-actions",
    workspace="/home/runner/work/project",
    git_info=git_info,
    validation_results={
        "config_valid": True,
        "structure_valid": True,
        "dependencies_ok": True,
    },
    mock_suggestions=suggestions,
    summary={
        "total_tests": 128,
        "coverage_percent": 87.5,
        "execution_time_ms": 4532,
    },
    recommendations=[
        "Implementar mocks HTTP em tests/test_api.py:42",
        "Fixar timestamps em testes temporais",
    ],
    status="WARNING"
)

# 4. Serializar para JSON
import json
report_json = report.model_dump_json(indent=2)
print(report_json)

# 5. Converter para dict (formato legado)
report_dict = report.to_dict()
assert "git_info" in report_dict
assert report_dict["status"] == "WARNING"
```

## Padrões de Uso

### Validação Automática

```python
# ❌ Falha: line_number inválido
try:
    bad_suggestion = MockSuggestion(
        severity="HIGH",
        mock_type="HTTP_REQUEST",
        file_path="test.py",
        line_number=0,  # ERRO: deve ser > 0
        reason="teste"
    )
except ValueError as e:
    print(e)  # "line_number deve ser maior que 0"
```

### Imutabilidade

```python
git_info = GitInfo(is_git_repo=True)

# ❌ Falha: modelo é frozen
try:
    git_info.current_branch = "main"
except ValidationError:
    print("Não é possível modificar objeto imutável")
```

### Desserialização

```python
# JSON → Modelo Pydantic
json_data = '{"total": 5, "high_priority": 2, "blocking": 1, "details": []}'
suggestions = MockSuggestions.model_validate_json(json_data)

# Dict → Modelo Pydantic
dict_data = {"total": 5, "high_priority": 2, "blocking": 1}
suggestions = MockSuggestions.model_validate(dict_data)
```

## Compatibilidade com Código Legado

### Método `to_dict()`

Mantemos métodos `to_dict()` customizados em `CIReport` e `FixResult` para compatibilidade com código existente que espera estruturas específicas.

```python
# Pydantic padrão
report.model_dump()  # Dict com estrutura Pydantic

# Formato legado customizado
report.to_dict()  # Dict com estrutura específica do projeto
```

### Strings vs Enums

Os campos `severity`, `mock_type` e `status` são mantidos como `str` para compatibilidade com:

- Código existente que espera strings
- Serialização JSON direta
- Configurações YAML/JSON

Conversores de propriedade estão disponíveis quando necessário:

```python
suggestion.severity  # str: "HIGH"
suggestion.severity_enum  # Severity.HIGH
```

## Boas Práticas

1. **Use Imutabilidade**: Prefira `frozen=True` para modelos que não devem mudar após criação
2. **Valide Cedo**: Adicione `@field_validator` para regras de negócio críticas
3. **Type Hints Completos**: Sempre anote tipos, inclusive `None` em campos opcionais
4. **Factory Methods**: Use `@classmethod` para construtores complexos
5. **Documentação**: Mantenha docstrings atualizadas com `Attributes` seção

## Evolução Futura

### Melhorias Planejadas

- [ ] Converter `severity`, `mock_type`, `status` para enums nativos (breaking change)
- [ ] Adicionar schema JSON para integração com ferramentas CI/CD
- [ ] Implementar validadores cross-field (ex: `blocking <= high_priority`)
- [ ] Adicionar suporte a serialização YAML

### Migração Gradual

Para migrar código legado:

1. Substituir `from dataclasses import dataclass` por `from pydantic import BaseModel`
2. Adicionar `model_config = ConfigDict(frozen=True)` onde apropriado
3. Trocar `asdict()` por `model_dump()`
4. Adicionar validadores com `@field_validator`
5. Testar serialização/desserialização

## Referências

- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [scripts/core/mock_ci/models.py](../../scripts/core/mock_ci/models.py)
- [docs/architecture/MOCK_CI_REFACTORING.md](./MOCK_CI_REFACTORING.md)
- [tests/test_mock_ci_models.py](../../tests/test_mock_ci_models.py)

## Conclusão

A arquitetura baseada em Pydantic fornece uma base sólida para evolução do sistema, garantindo type-safety, validação robusta e serialização consistente. A compatibilidade com código legado é mantida através de métodos bridge, permitindo migração gradual.
