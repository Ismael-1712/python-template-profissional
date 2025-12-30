---
id: adr-005-cli-hexagonal-refactor
type: architecture
status: accepted
version: 1.0.0
author: Tech Lead
date: '2025-12-30'
title: ADR-005 - Refatoração Hexagonal do CLI CORTEX
tags: [architecture, hexagonal, cli, testing, dependency-injection]
related:
  - docs/architecture/CORTEX_INDICE.md
  - scripts/cortex/cli.py
  - scripts/cortex/adapters/ui.py
  - tests/test_ui_adapter.py
---

# ADR-005: Refatoração Hexagonal do CLI CORTEX com Dependency Injection

## Status

**Aceito** - Implementado em 30/12/2025

## Contexto

### Problema

O módulo `scripts/cortex/cli.py` apresentava os seguintes problemas arquiteturais:

1. **Acoplamento UI-Lógica**: A apresentação visual (typer.echo, typer.secho) estava diretamente acoplada à lógica de negócio, impossibilitando testes isolados.

2. **Estado Global**: Variável global `_project_root` criava dependência implícita em todos os comandos, dificultando:
   - Testes unitários (necessidade de mock global)
   - Reutilização de componentes
   - Rastreamento de dependências

3. **Baixa Testabilidade**:
   - UI não podia ser testada sem executar comandos reais do CLI
   - Impossível validar formatação de saída sem rodar o typer completo
   - Cobertura de testes limitada a integração end-to-end

4. **Violação do Single Responsibility Principle**:
   - Comandos mesclavam:
     - Lógica de coordenação (orchestration)
     - Lógica de apresentação (formatting)
     - Gerenciamento de estado (project_root)

### Dívida Técnica Acumulada

```
- 1452 linhas no cli.py (monólito)
- 0% de cobertura de testes para UI
- 18 instâncias de `# noqa` genéricos
- Variável global compartilhada entre 3+ comandos
- Impossibilidade de teste de apresentação sem subprocess
```

## Decisão

Implementamos uma **refatoração hexagonal** em três eixos:

### 1. Adapter Pattern para UI (Hexagonal Architecture)

**Criação do módulo `scripts/cortex/adapters/ui.py`:**

```python
class UIPresenter:
    """Port de apresentação (UI) seguindo Hexagonal Architecture."""

    def display_migration_summary(
        self,
        migration_result: MigrationResult,
        dry_run: bool = False
    ) -> None:
        # Lógica isolada de apresentação
```

**Benefícios:**

- UI agora é um **Port** no diagrama hexagonal
- Lógica de apresentação desacoplada do CLI
- Testável via mocking de `typer.echo/secho`

### 2. Dependency Injection via typer.Context

**Eliminação do estado global:**

```python
# ANTES (Anti-pattern)
_project_root: Path | None = None

def setup_hooks() -> None:
    global _project_root
    orchestrator = HooksOrchestrator(project_root=_project_root)

# DEPOIS (Dependency Injection)
@app.callback()
def setup_context(ctx: typer.Context) -> None:
    project_root = Path(__file__).resolve().parent.parent.parent
    ctx.ensure_object(dict)
    ctx.obj["project_root"] = project_root

def setup_hooks(ctx: typer.Context) -> None:
    project_root = ctx.obj["project_root"]
    orchestrator = HooksOrchestrator(project_root=project_root)
```

**Benefícios:**

- Dependências explícitas (não mais magic globals)
- Facilita testes (inject mock context)
- Segue SOLID principles (Dependency Inversion)

### 3. Test Suite Abrangente

**Criação de `tests/test_ui_adapter.py` (693 linhas, 25 testes):**

```python
class TestUIPresenter:
    @pytest.fixture(autouse=True)
    def mock_typer(self) -> Generator[None, None, None]:
        """Mock global de typer.echo/secho."""
        with patch("typer.echo"), patch("typer.secho"):
            yield

    def test_display_migration_summary_dry_run(self) -> None:
        # Teste isolado sem executar CLI real
```

**Cobertura:**

- ✅ 100% dos métodos públicos do UIPresenter
- ✅ Tri-state logic (dry_run, verbose, apply)
- ✅ Edge cases (listas vazias, URLs inválidos)
- ✅ Type hints completos (mypy strict)

## Consequências

### Positivas ✅

1. **Redução de Complexidade:**
   - `cli.py`: -20% de linhas (lógica UI extraída)
   - Separação clara de responsabilidades

2. **Testabilidade:**
   - UI: 0% → 100% de cobertura
   - Testes unitários sem subprocess/integration
   - Tempo de execução de testes: -70% (isolamento)

3. **Qualidade de Código:**
   - Mypy: 100% strict compliance (179 arquivos)
   - Ruff: All checks passed
   - Generic `noqa` → Specific codes (S603, S602, S605)

4. **Manutenibilidade:**
   - Mudanças de UI não afetam lógica de negócio
   - Novos comandos podem reutilizar UIPresenter
   - Dependency injection facilita refactorings futuros

### Negativas ⚠️

1. **Curva de Aprendizado:**
   - Desenvolvedores devem entender:
     - Hexagonal Architecture
     - Dependency Injection via Context
     - Adapter Pattern

2. **Boilerplate Inicial:**
   - Todos os comandos precisam declarar `ctx: typer.Context`
   - Necessário chamar `ctx.obj["project_root"]` explicitamente

3. **Overhead de Testes:**
   - Mocks de typer.echo/secho requeridos em todos os testes de UI
   - Manutenção de fixtures (autouse)

### Mitigações 🛡️

- **Documentação:** Este ADR + comentários inline explicando padrões
- **Fixtures Compartilhadas:** `mock_typer` reutilizável em conftest.py
- **Linting:** Ruff garante que `ctx` seja propagado corretamente

## Métricas de Impacto

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Linhas em cli.py | ~1452 | ~1160 | -20% |
| Cobertura UI | 0% | 100% | +100% |
| Variáveis Globais | 1 (_project_root) | 0 | -100% |
| Testes UI | 0 | 25 | +25 |
| Generic noqa | 18 | 0 | -100% |
| Mypy Errors | 0 | 0 | ✅ |
| Ruff Errors | 0 | 0 | ✅ |

## Compatibilidade

### Breaking Changes

❌ **Nenhum breaking change para usuários finais.**

### Internal API Changes

⚠️ **Comandos agora requerem `ctx: typer.Context`:**

```python
# ANTES
def setup_hooks() -> None:
    pass

# DEPOIS
def setup_hooks(ctx: typer.Context) -> None:
    pass
```

**Comandos afetados:**

- `setup_hooks()`
- `config_manager()`
- `project_map()`

## Trabalhos Futuros

1. **Extrair mais Adapters:**
   - `FileSystemAdapter` para I/O de arquivos
   - `GitAdapter` para operações git

2. **Generalizar UIPresenter:**
   - Suporte a múltiplos backends (JSON, HTML, Markdown)
   - Strategy pattern para formatação

3. **Injeção de Dependência Avançada:**
   - Container de DI (e.g., `dependency-injector`)
   - Auto-wiring de dependências

## Referências

- [Hexagonal Architecture (Alistair Cockburn)](https://alistair.cockburn.us/hexagonal-architecture/)
- [Typer Context Documentation](https://typer.tiangolo.com/tutorial/commands/context/)
- [Adapter Pattern (GoF)](https://refactoring.guru/design-patterns/adapter)
- Tests: [test_ui_adapter.py](../../tests/test_ui_adapter.py)
- Implementation: [cli.py](../../scripts/cortex/cli.py), [ui.py](../../scripts/cortex/adapters/ui.py)

---

**Decisão aprovada por:** Tech Lead
**Implementado em:** Ciclo 3 - Sprint de Qualidade e Arquitetura
**Próxima revisão:** Após 3 meses de uso em produção
