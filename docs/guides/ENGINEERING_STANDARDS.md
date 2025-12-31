---
id: guide-engineering-standards
title: Padrões de Engenharia e Boas Práticas
type: guide
status: active
version: 2.0.0
author: DevOps Team
date: 2025-12-31
tags: [standards, python, security, typing, testing, observability, http, complexity, architecture, dependencies, documentation]
---

# Padrões de Engenharia e Boas Práticas

Este documento consolida as decisões técnicas e padrões de engenharia adotados no projeto. Todos os desenvolvedores devem seguir estas diretrizes para garantir consistência, segurança e manutenibilidade do código.

---

## 📚 Índice

1. [Complexidade Ciclomática Máxima](#complexidade-ciclomática-máxima)
2. [Arquitetura em Camadas (Import Linter)](#arquitetura-em-camadas-import-linter)
3. [Higiene de Dependências (Deptry)](#higiene-de-dependências-deptry)
4. [Cobertura de Documentação (Interrogate)](#cobertura-de-documentação-interrogate)
5. [Lazy Imports](#lazy-imports)
6. [Sanitização de Ambiente](#sanitização-de-ambiente)
7. [Tipagem em Testes](#tipagem-em-testes)
8. [Future Annotations](#future-annotations)
9. [Atomicidade em Scripts de Infraestrutura](#atomicidade-em-scripts-de-infraestrutura)
10. [Enums vs Magic Strings](#enums-vs-magic-strings)
11. [Requisições HTTP e Observabilidade](#requisições-http-e-observabilidade)

---

## 🧠 Complexidade Ciclomática Máxima

### Motivação

Funções e métodos com alta complexidade ciclomática (muitos caminhos de execução) são:

- **Difíceis de Entender**: Muitas ramificações (`if`, `for`, `while`) tornam o código confuso.
- **Difíceis de Testar**: Cada caminho precisa de um teste específico, aumentando exponencialmente o esforço.
- **Propensos a Bugs**: Maior complexidade = maior chance de erros lógicos.
- **Difíceis de Manter**: Modificações podem quebrar comportamentos inesperados.

### Padrão Ouro: Complexidade ≤ 10

Este projeto adota **complexidade ciclomática máxima de 10** (McCabe Complexity), o padrão ouro da indústria recomendado por:

- **IEEE Computer Society**
- **Software Engineering Institute (SEI)**
- **Clean Code (Robert C. Martin)**

### Ferramentas de Validação

#### 1. Ruff (Feedback Imediato)

O Ruff está configurado para avisar sobre complexidade durante o desenvolvimento:

```toml
[tool.ruff.lint]
select = ["C901"]  # McCabe Complexity

[tool.ruff.lint.mccabe]
max-complexity = 10
```

Execute: `make lint` ou `ruff check .`

#### 2. Xenon (Gatekeeper Estrito)

O Xenon bloqueia commits que violam o padrão de complexidade:

```bash
make complexity-check
# ou
xenon --max-absolute B --max-modules A --max-average A scripts/ src/
```

**Métricas do Xenon:**

- `--max-absolute B`: Nenhum bloco pode ter complexidade C ou pior (≥ 11)
- `--max-modules A`: Módulos inteiros devem manter complexidade média A (≤ 5)
- `--max-average A`: Projeto inteiro deve manter média A

**O build FALHARÁ se estas métricas não forem atendidas.**

### Como Resolver Erros de Complexidade

Se você encontrar erro `C901` (McCabe complexity) ou falha no Xenon:

#### ❌ **NÃO FAÇA ISSO:**

```python
def process_order(order, user, inventory, payment):
    if user.is_premium():
        if order.total > 100:
            if inventory.check_stock(order.items):
                if payment.validate():
                    if order.shipping == "express":
                        # ... mais lógica
                        return success
    return failure
```

**Complexidade: ~15** (God Function!)

#### ✅ **FAÇA ISSO (Extrair Método):**

```python
def process_order(order: Order, user: User, inventory: Inventory, payment: Payment) -> Result:
    """Process customer order with validation."""
    if not _is_order_eligible(order, user):
        return Result.failure("Order not eligible")

    if not _validate_inventory_and_payment(order, inventory, payment):
        return Result.failure("Validation failed")

    return _execute_order(order)

def _is_order_eligible(order: Order, user: User) -> bool:
    """Check if order is eligible for processing."""
    return user.is_premium() and order.total > 100

def _validate_inventory_and_payment(
    order: Order, inventory: Inventory, payment: Payment
) -> bool:
    """Validate inventory and payment for order."""
    return inventory.check_stock(order.items) and payment.validate()

def _execute_order(order: Order) -> Result:
    """Execute the order based on shipping type."""
    if order.shipping == "express":
        return _process_express_shipping(order)
    return _process_standard_shipping(order)
```

**Complexidade de cada função: ≤ 5**

### Benefícios da Refatoração

- ✅ **Código Auto-Documentado**: Cada função tem nome que explica o que faz
- ✅ **Testável**: Funções pequenas são fáceis de testar isoladamente
- ✅ **Manutenível**: Mudanças são localizadas e seguras
- ✅ **Reutilizável**: Funções pequenas podem ser usadas em outros contextos

### Integração com CI/CD

O comando `make validate` executa todas as verificações, incluindo complexidade:

```bash
make validate
# Executa: lint → type-check → complexity-check → arch-check → deps-check → docs-check → test
```

**Qualquer falha bloqueia o merge.** Isso garante que código complexo nunca entre na base.

### Referências

- [McCabe Complexity - Wikipedia](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Clean Code, Chapter 3 - Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
- [Xenon Documentation](https://xenon.readthedocs.io/)
- [Ruff C901 Rule](https://docs.astral.sh/ruff/rules/complex-structure/)

---

## 🏗️ Arquitetura em Camadas (Import Linter)

### Motivação

Arquiteturas sem fronteiras claras sofrem de:

- **Acoplamento Circular**: Módulo A depende de B, que depende de A (ciclos de importação).
- **Violação de SoC (Separation of Concerns)**: Lógica de negócio misturada com CLI/UI.
- **Dificuldade de Teste**: Camadas altas (CLI) não deveriam ser importadas por camadas baixas (Core).
- **Mudanças em Cascata**: Alteração em um módulo quebra vários outros inesperadamente.

### Padrão: Arquitetura em Camadas

Este projeto adota **Layered Architecture** com separação clara:

```
┌─────────────────────────────────┐
│  CLI / UI (scripts/cli)         │  ← Camada de Apresentação
├─────────────────────────────────┤
│  Application (scripts/cortex)   │  ← Orquestração de Casos de Uso
├─────────────────────────────────┤
│  Core / Domain (scripts/core)   │  ← Lógica de Negócio Pura
└─────────────────────────────────┘
```

**Regra de Ouro**: **Camadas inferiores NÃO podem importar camadas superiores**.

### Contratos Arquiteturais

O **Import Linter** valida os seguintes contratos:

#### 1. Core não deve importar CLI

```python
# ❌ PROIBIDO em scripts/core/**/*.py
from scripts.cli.doctor import run_diagnostics

# ✅ PERMITIDO: Core expõe interfaces, CLI consome
from scripts.core.diagnostic_engine import DiagnosticEngine
```

**Motivação**: Core deve ser reutilizável em diferentes contextos (CLI, API, testes).

#### 2. Cortex Core não deve importar Cortex CLI

```python
# ❌ PROIBIDO em scripts/core/cortex/**/*.py
from scripts.cortex.cli import main

# ✅ PERMITIDO: Inversão de dependência
from scripts.core.cortex.orchestrator import CortexOrchestrator
```

**Motivação**: Lógica de orquestração não deve depender de comandos CLI.

### Como Verificar

Execute:

```bash
make arch-check
# ou
lint-imports
```

**Saída esperada:**

```
=============
Import Linter
=============

Contracts
---------

Core não deve importar CLI KEPT ✓
Cortex Core não deve importar Cortex CLI KEPT ✓

Contracts: 2 kept, 0 broken.
```

### Como Resolver Violações

Se você encontrar erro de violação de contrato:

#### ❌ **VIOLAÇÃO DETECTADA:**

```
scripts.core.cortex.audit_orchestrator -> scripts.cortex.core.knowledge_auditor (l.61)
```

**Problema**: `scripts/core/cortex/audit_orchestrator.py` está importando de `scripts/cortex/`, violando a separação de camadas.

#### ✅ **SOLUÇÃO 1: Mover Módulo**

Mova `scripts/cortex/core/knowledge_auditor.py` para `scripts/core/cortex/knowledge_auditor.py`.

#### ✅ **SOLUÇÃO 2: Inversão de Dependência**

```python
# scripts/core/cortex/audit_orchestrator.py
from abc import ABC, abstractmethod

class KnowledgeAuditor(ABC):
    """Interface para auditores de conhecimento."""

    @abstractmethod
    def audit(self, path: Path) -> AuditResult:
        """Audita arquivo de conhecimento."""
        pass

# scripts/cortex/core/knowledge_auditor.py (implementação concreta)
from scripts.core.cortex.audit_orchestrator import KnowledgeAuditor

class ConcreteKnowledgeAuditor(KnowledgeAuditor):
    """Implementação concreta do auditor."""

    def audit(self, path: Path) -> AuditResult:
        # Implementação específica
        pass
```

### Estratégia de Baseline (Grandfathering)

Código legado pode ter violações. Para não quebrar o build:

```toml
# pyproject.toml
[[tool.importlinter.contracts]]
name = "Core não deve importar CLI"
type = "forbidden"
source_modules = ["scripts.core"]
forbidden_modules = ["scripts.cli"]
```

**Violações atuais são toleradas**, mas:
- ✅ Novas violações **bloquearão** o build
- 🔄 Violações legadas devem ser corrigidas gradualmente

### Benefícios

- ✅ **Testabilidade**: Core pode ser testado sem depender de CLI
- ✅ **Reutilização**: Core pode ser usado em API, Worker, CLI
- ✅ **Manutenção**: Mudanças em CLI não quebram Core
- ✅ **Clareza**: Arquitetura explícita e auditável

### Referências

- [Import Linter Documentation](https://import-linter.readthedocs.io/)
- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)

---

## 🧹 Higiene de Dependências (Deptry)

### Motivação

Dependências não utilizadas causam:

- **Bloat de Imagem Docker**: Pacotes desnecessários aumentam tamanho da imagem.
- **Vulnerabilidades Desnecessárias**: Mais deps = mais superfície de ataque.
- **Confusão**: Desenvolvedores não sabem quais deps são realmente usadas.
- **Build Lento**: `pip install` instala pacotes inúteis.

### Padrão: Zero Dependências Não Utilizadas

Este projeto adota **higiene estrita de dependências**:

- ✅ Toda dependência em `pyproject.toml` **DEVE** ser usada no código.
- ✅ Toda importação no código **DEVE** estar declarada em `pyproject.toml`.

### Ferramenta: Deptry

**Deptry** escaneia o código e detecta:

1. **DEP002**: Dependência declarada mas não usada
2. **DEP001**: Importação usada mas não declarada
3. **DEP003**: Dependência transitiva usada diretamente

### Como Verificar

Execute:

```bash
make deps-check
# ou
deptry .
```

**Saída esperada:**

```
📦 Verificando dependências não utilizadas...
Scanning 5 files...

Success! No dependency issues found.
```

### Como Resolver Violações

#### ❌ **VIOLAÇÃO: DEP002 (Dependência não usada)**

```
pyproject.toml: DEP002 'requests' defined as a dependency but not used in the codebase
```

**Solução**: Remova `requests` de `pyproject.toml` se não for usado.

```toml
# pyproject.toml - ANTES
dependencies = [
    "fastapi",
    "requests",  # ← Não usado, remove!
]

# pyproject.toml - DEPOIS
dependencies = [
    "fastapi",
]
```

#### ❌ **VIOLAÇÃO: DEP001 (Importação não declarada)**

```
src/app/api.py: DEP001 'pydantic' imported but not declared in dependencies
```

**Solução**: Adicione `pydantic` às dependências.

```toml
# pyproject.toml
dependencies = [
    "fastapi",
    "pydantic>=2.0",  # ← Adicionar
]
```

### Configuração de Exclusões

Algumas pastas não precisam de validação estrita:

```toml
# pyproject.toml
[tool.deptry]
extend_exclude = [
    "scripts/",  # Scripts CLI podem usar deps de dev
    "tests/",    # Testes podem usar pytest, etc.
]
```

### Estratégia de Baseline (Grandfathering)

Dependências legadas do template podem ser ignoradas temporariamente:

```toml
[tool.deptry.per_rule_ignores]
DEP002 = [
    "uvicorn",  # Usado em produção via CLI, não em imports diretos
    "chromadb", # Template placeholder
]
```

**Novas dependências NÃO terão essa tolerância.**

### Benefícios

- ✅ **Imagens Docker Enxutas**: Apenas deps necessárias
- ✅ **Segurança**: Menos deps = menos CVEs
- ✅ **Clareza**: Documentação implícita das dependências reais
- ✅ **Build Rápido**: `pip install` mais eficiente

### Referências

- [Deptry Documentation](https://deptry.com/)
- [PEP 621 - Dependency Specification](https://peps.python.org/pep-0621/)

---

## 📚 Cobertura de Documentação (Interrogate)

### Motivação

Código sem docstrings é:

- **Difícil de Entender**: Desenvolvedores perdem tempo tentando decifrar o que faz.
- **Difícil de Manter**: Mudanças podem quebrar comportamentos não documentados.
- **Não Profissional**: Falta de documentação sinaliza baixa maturidade.
- **Incompatível com Geração de Docs**: MkDocs, Sphinx não conseguem gerar documentação.

### Padrão: Cobertura Mínima de 95%

Este projeto exige **95% de cobertura de docstrings** em:

- Módulos (docstring no topo do arquivo)
- Classes (docstring logo após `class`)
- Funções e métodos públicos (docstring logo após `def`)

**Exceções:**
- Métodos mágicos (`__init__`, `__str__`)
- Métodos privados (começam com `_`)
- Setters (`@property.setter`)

### Ferramenta: Interrogate

**Interrogate** escaneia o código e gera relatório de cobertura:

```bash
make docs-check
# ou
interrogate -vv scripts/ src/
```

**Saída esperada:**

```
📚 Verificando cobertura de documentação...

======= Coverage for /home/ismae/projects/python-template-profissional/ ========
|------------------------------------------------|-------|------|-------|--------|
| TOTAL                                          |   813 |    7 |   806 |  99.1% |
---------------- RESULT: PASSED (minimum: 95.0%, actual: 99.1%) -----------------
```

### Como Escrever Docstrings

#### ✅ **PADRÃO: Google Docstring Style**

```python
def process_order(order_id: str, user_id: str) -> OrderResult:
    """Process customer order and update inventory.

    This function validates the order, checks inventory availability,
    processes payment, and updates the database atomically.

    Args:
        order_id: Unique identifier of the order to process.
        user_id: Unique identifier of the user placing the order.

    Returns:
        OrderResult object containing success status and order details.

    Raises:
        OrderNotFoundError: If order_id does not exist in database.
        InsufficientStockError: If inventory is insufficient for order.
        PaymentFailedError: If payment processing fails.

    Example:
        >>> result = process_order("ORD-123", "USR-456")
        >>> print(result.status)
        'success'
    """
    # Implementação
    pass
```

#### ❌ **EVITE: Docstrings Vazias**

```python
def process_order(order_id: str, user_id: str) -> OrderResult:
    """Process order."""  # ← Não explica nada!
    pass
```

#### ❌ **EVITE: Sem Docstring**

```python
def process_order(order_id: str, user_id: str) -> OrderResult:
    # ← Nenhuma documentação!
    pass
```

### Configuração

```toml
# pyproject.toml
[tool.interrogate]
ignore-init-method = true      # __init__ não precisa de docstring
ignore-magic = true            # __str__, __repr__ não precisam
fail-under = 95.0              # Mínimo 95% de cobertura
verbose = 1
exclude = ["setup.py", "build/"]
```

### Estratégia de Baseline (Grandfathering)

Código legado pode ter baixa cobertura. Configuração inicial:

```toml
[tool.interrogate]
fail-under = 0  # Baseline inicial: tolerar código legado
```

**Meta progressiva:**
- Sprint 1: 0% → 50%
- Sprint 2: 50% → 75%
- Sprint 3: 75% → 95%

**Novas funções DEVEM ter 100% de cobertura.**

### Benefícios

- ✅ **Código Auto-Explicativo**: Docstrings servem como documentação viva
- ✅ **Geração de Docs**: MkDocs gera documentação bonita automaticamente
- ✅ **Onboarding Rápido**: Novos devs entendem o código mais rápido
- ✅ **Manutenção Segura**: Docstrings previnem regressões

### Referências

- [Interrogate Documentation](https://interrogate.readthedocs.io/)
- [Google Python Style Guide - Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)

---

## 🔄 Lazy Imports

### Motivação

Python carrega módulos no momento do `import`. Em projetos grandes, isso pode causar:

- **Ciclos de Importação**: Módulo A importa B, que importa A.
- **Startup Lento**: Carregar dependências pesadas mesmo quando não são usadas.
- **Acoplamento Desnecessário**: Módulos ficam dependentes uns dos outros apenas para type checking.

### Solução: TYPE_CHECKING

Use `TYPE_CHECKING` para imports que são necessários apenas para type checkers (mypy, pyright):

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .heavy_module import HeavyClass  # Só carregado durante type checking

def process_data(data: HeavyClass) -> None:  # Type hint funciona!
    """Process data using HeavyClass.

    Args:
        data: Instance of HeavyClass to process
    """
    # Neste ponto, HeavyClass não foi importado em runtime
    pass
```

**Quando usar:**

- ✅ Type hints de parâmetros e retornos
- ✅ Tipos em docstrings (via anotações)
- ✅ Quebrar ciclos de importação

**Quando NÃO usar:**

- ❌ Classes base (herança)
- ❌ Decorators
- ❌ Variáveis globais do tipo

### Exemplo Real: MockPattern

O módulo `scripts/core/mock_ci/models.py` usa este padrão:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

class MockPattern:
    """Pattern for generating test mocks."""

    def save_to_file(self, path: Path) -> None:
        """Save pattern to file.

        Args:
            path: Target file path
        """
        from pathlib import Path  # Late import - só quando método é chamado

        resolved_path = Path(path)  # Agora Path está disponível
        resolved_path.write_text(self.to_json())
```

**Benefícios:**

1. Type checker vê `Path` no type hint
2. Runtime não carrega `pathlib` até método ser chamado
3. Zero overhead se método nunca for executado

### Imports Tardios em Métodos

Para dependências pesadas que só são usadas em métodos específicos:

```python
def generate_dashboard(self) -> None:
    """Generate HTML dashboard with charts."""
    from plotly import graph_objects as go  # Late import - só se dashboard for gerado

    fig = go.Figure(data=[...])
    fig.write_html("dashboard.html")
```

**Quando usar:**

- ✅ Dependências opcionais (ex: `plotly`, `pandas`)
- ✅ Módulos pesados usados raramente
- ✅ CLI commands com muitas dependências específicas

---

## 🔐 Sanitização de Ambiente

### Motivação

Subprocessos podem herdar variáveis de ambiente perigosas que contêm:

- Tokens de autenticação (GitHub, CI/CD)
- Chaves de API (AWS, Azure, GCP)
- Senhas e credenciais
- Configurações que alteram comportamento do Python (`PYTHONSTARTUP`)

**Risco:** Um `subprocess.run()` sem sanitização pode vazar credenciais em logs, ou executar código arbitrário.

### Solução: Whitelist-Based Sanitization

Implementamos uma abordagem de **menor privilégio**: apenas variáveis explicitamente seguras são propagadas.

**Módulo:** `scripts/utils/security.py`

```python
from __future__ import annotations
import os
from scripts.utils.security import sanitize_env

# Ambiente seguro para subprocessos
safe_env = sanitize_env(os.environ)

# Usar em subprocessos
subprocess.run(["pytest"], env=safe_env, check=True)
```

### Variáveis Permitidas (Whitelist)

**Sistema Essenciais:**

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TZ`
- `TMPDIR`, `TEMP`, `TMP`

**Python Seguras:**

- `PYTHONPATH`, `PYTHONUNBUFFERED`, `PYTHONHASHSEED`
- `PYTHONDONTWRITEBYTECODE`, `PYTHONIOENCODING`
- `VIRTUAL_ENV`
- `PY*` (ex: `PYTEST_CURRENT_TEST`)

### Variáveis Bloqueadas (Blocklist)

Padrões sensíveis são **rejeitados automaticamente**:

- `*TOKEN*` - Tokens de autenticação
- `*KEY*` - Chaves de API
- `*SECRET*` - Segredos genéricos
- `*PASSWORD*` - Senhas
- `*CREDENTIAL*` - Credenciais
- `*API*` - Chaves/tokens de API

**Python Perigosas (Hardened Block):**

- `PYTHONSTARTUP` - Pode executar código arbitrário no startup
- `PYTHONHOME` - Pode redirecionar instalação Python
- `PYTHONINSPECT` - Abre modo interativo após execução

### Por Que Whitelist em Vez de Blocklist?

**Abordagem de Blocklist (Insegura):**

```python
# ❌ RUIM: Fácil esquecer algum padrão perigoso
if "TOKEN" not in key and "PASSWORD" not in key:
    sanitized[key] = value
```

**Problemas:**

- Esqueceu `API_SECRET`, `DB_PASSWORD_PROD`, `JWT_KEY`...
- Novos padrões de secrets surgem constantemente
- **Fail-open**: Erro expõe tudo por padrão

**Abordagem de Whitelist (Segura):**

```python
# ✅ BOM: Apenas o necessário é exposto
if key in allowed_keys:
    sanitized[key] = value
```

**Vantagens:**

- Princípio do Menor Privilégio
- **Fail-closed**: Erro bloqueia tudo por padrão
- Auditável: Lista curta de variáveis permitidas

### Implementação Detalhada

```python
def sanitize_env(original_env: dict[str, str]) -> dict[str, str]:
    """Sanitize environment variables to prevent leaking sensitive data.

    Implements a whitelist-based approach with explicit blocklist for secrets.
    Only safe and necessary variables are propagated to subprocesses.

    Args:
        original_env: Original environment dictionary from os.environ

    Returns:
        Sanitized environment dictionary safe for subprocess execution

    Security:
        - Blocks: TOKEN, KEY, SECRET, PASSWORD, CREDENTIAL, API patterns
        - Allows: Essential system vars + Safe Python-specific vars
        - Hardened: Only explicitly safe PYTHON* vars (no PYTHONSTARTUP)
    """
    allowed_keys = {
        "PATH", "PYTHONPATH", "HOME", "LANG", "LC_ALL", "TZ",
        "USER", "VIRTUAL_ENV", "TMPDIR", "TEMP", "TMP",
    }

    safe_python_vars = {
        "PYTHONPATH", "PYTHONUNBUFFERED", "PYTHONHASHSEED",
        "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING",
    }

    blocked_patterns = ("TOKEN", "KEY", "SECRET", "PASSWORD", "CREDENTIAL", "API")

    sanitized: dict[str, str] = {}

    for key, value in original_env.items():
        # Explicit block: reject any key containing sensitive patterns
        if any(pattern in key.upper() for pattern in blocked_patterns):
            logger.debug("Blocked sensitive environment variable: %s", key)
            continue

        # Allow whitelisted keys
        if key in allowed_keys:
            sanitized[key] = value
            continue

        # Allow only explicitly safe Python variables (HARDENED)
        if key in safe_python_vars:
            sanitized[key] = value
            continue

        # Allow PY* prefix (shorter Python vars like PYTEST_*)
        if key.startswith("PY") and not key.startswith("PYTHON"):
            sanitized[key] = value
            continue

        # Implicitly deny everything else (Least Privilege principle)
        logger.debug("Filtered environment variable: %s", key)

    return sanitized
```

### Exemplo de Uso em Testes

```python
def test_subprocess_security() -> None:
    """Verify subprocess doesn't leak credentials."""
    import os
    from scripts.utils.security import sanitize_env

    # Simular ambiente com credenciais
    original_env = os.environ.copy()
    original_env["GITHUB_TOKEN"] = "ghp_secret123"
    original_env["AWS_SECRET_KEY"] = "aws_secret456"

    # Sanitizar
    safe_env = sanitize_env(original_env)

    # Verificar que credenciais foram bloqueadas
    assert "GITHUB_TOKEN" not in safe_env
    assert "AWS_SECRET_KEY" not in safe_env

    # Verificar que variáveis seguras foram preservadas
    assert "PATH" in safe_env
    assert "HOME" in safe_env
```

---

## 🧪 Tipagem em Testes

### Motivação

Testes sem type hints levam a:

- **Falsos Positivos**: Mypy não detecta erros de tipo em testes
- **Manutenção Difícil**: Refatorações quebram testes silenciosamente
- **Documentação Pobre**: Não fica claro o que a fixture retorna

### Solução: Type Hints Obrigatórios

**Regra:** Toda função de teste e fixture deve ter anotação de tipo.

### Funções de Teste

```python
from __future__ import annotations

def test_user_creation() -> None:
    """Test that user is created with correct attributes."""
    user = User(name="Alice", age=30)
    assert user.name == "Alice"
    assert user.age == 30
```

**Por que `-> None`?**

- Testes não retornam valores (pytest os chama, não usa o retorno)
- Mypy detecta se você acidentalmente retornar algo
- Consistência: toda função tem type hint

### Fixtures

```python
from __future__ import annotations
from typing import TYPE_CHECKING
import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import Generator

@pytest.fixture
def temp_workspace(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary workspace directory.

    Args:
        tmp_path: Pytest's temporary path fixture

    Yields:
        Path to temporary workspace directory
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    yield workspace
    # Cleanup automático pelo pytest
```

**Type Hint da Fixture:**

- `Generator[Path, None, None]` - Fixture que yielda um `Path`
- Primeiro `Path`: Tipo do valor yielded
- Segundo `None`: Tipo do valor enviado (não usado em fixtures)
- Terceiro `None`: Tipo do retorno após generator finalizar

### Exemplo Real: test_reporter.py

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

@pytest.fixture
def sample_report() -> dict[str, Any]:
    """Create a complete sample audit report for testing.

    Returns:
        Dictionary with audit report structure
    """
    return {
        "metadata": {
            "timestamp": "2025-11-27T15:30:00",
            "workspace": "/test/workspace",
            "duration_seconds": 1.23,
            "files_scanned": 42,
        },
        "results": {
            "security": {"score": 100, "issues": []},
            "duplication": {"score": 95, "duplicates": []},
        },
    }

def test_reporter_initialization(sample_report: dict[str, Any]) -> None:
    """Test that reporter initializes correctly with valid report.

    Args:
        sample_report: Fixture providing sample report data
    """
    from scripts.audit.reporter import AuditReporter

    reporter = AuditReporter(sample_report)
    assert reporter.report == sample_report
```

### Benefícios

1. **Type Safety**: Mypy detecta erros de tipo em testes
2. **Refactoring Seguro**: Mudanças em tipos quebram testes imediatamente
3. **Documentação**: Type hints documentam o que fixtures retornam
4. **Autocomplete**: IDEs oferecem autocomplete correto

---

## 📝 Future Annotations

### Motivação

Python avalia type hints no momento da importação. Isso causa problemas:

1. **Referências Circulares**: Classe A referencia B, que referencia A
2. **Performance**: Avaliar tipos complexos é lento
3. **Forward References**: Não pode referenciar classe antes de definir

### Solução: PEP 563 - Postponed Evaluation

**Regra:** Todo arquivo deve começar com:

```python
from __future__ import annotations
```

### Como Funciona

**Sem `future annotations`:**

```python
# ❌ ERRO: MyClass não está definida ainda
class MyClass:
    def clone(self) -> MyClass:  # NameError!
        return MyClass()
```

**Com `future annotations`:**

```python
from __future__ import annotations

# ✅ OK: Type hint é tratado como string
class MyClass:
    def clone(self) -> MyClass:  # Funciona!
        return MyClass()
```

### Evitando Ciclos de Importação

**Antes (Ciclo):**

```python
# module_a.py
from module_b import ClassB  # Importa B

class ClassA:
    def use_b(self, b: ClassB) -> None:  # Usa B no type hint
        pass

# module_b.py
from module_a import ClassA  # Importa A

class ClassB:
    def use_a(self, a: ClassA) -> None:  # Usa A no type hint
        pass

# Resultado: ImportError - Ciclo detectado!
```

**Depois (Sem Ciclo):**

```python
# module_a.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_b import ClassB  # Só importado durante type checking

class ClassA:
    def use_b(self, b: ClassB) -> None:  # OK! ClassB é string em runtime
        pass

# module_b.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_a import ClassA  # Só importado durante type checking

class ClassB:
    def use_a(self, a: ClassA) -> None:  # OK! ClassA é string em runtime
        pass

# Resultado: Funciona! Nenhum ciclo de importação.
```

### Impacto em Runtime

**Comportamento:**

- Type hints não são avaliados em runtime
- São armazenados como strings em `__annotations__`
- Type checkers (mypy) avaliam as strings

**Exemplo:**

```python
from __future__ import annotations

def process(data: list[dict[str, int]]) -> None:
    pass

# Em runtime:
print(process.__annotations__)
# Output: {'data': 'list[dict[str, int]]', 'return': 'None'}
```

### Checklist de Adoção

- ✅ Adicione `from __future__ import annotations` em todo arquivo `.py`
- ✅ Use `TYPE_CHECKING` para imports apenas de tipo
- ✅ Não use `get_type_hints()` sem `from typing import get_type_hints`
- ✅ Configure mypy para verificar tipo em modo estrito

### Configuração Mypy

```toml
# myproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 🔒 Atomicidade em Scripts de Infraestrutura

### Motivação

Scripts que modificam arquivos de configuração críticos (como `requirements.txt`, `.env`, `config.yaml`) podem deixar o sistema em estado inconsistente se falharem no meio da execução. Isso resulta em:

- **Ambientes Quebrados**: Desenvolvedores não conseguem instalar dependências
- **Debugging Difícil**: Estado parcial é difícil de diagnosticar
- **Perda de Confiança**: Desenvolvedores evitam usar ferramentas não confiáveis
- **Intervenção Manual**: Tempo perdido restaurando backups manualmente

### Solução: Padrão Backup-Try-Rollback

Todo script de infraestrutura que modifica arquivos críticos deve implementar o padrão **Backup-Try-Rollback**:

```python
from pathlib import Path
import shutil

def atomic_update_config(config_file: Path) -> None:
    """Update configuration file atomically.

    Args:
        config_file: Path to configuration file

    Raises:
        Exception: If update fails (after rollback)
    """
    backup_file = config_file.with_suffix(".bak")

    # 1. CREATE BACKUP
    if config_file.exists():
        shutil.copy2(config_file, backup_file)  # Preserva metadados
        logger.info("📦 Backup criado: %s", backup_file)

    try:
        # 2. EXECUTE CRITICAL OPERATION
        # Escreve em arquivo temporário primeiro
        temp_file = config_file.with_suffix(".tmp")
        with open(temp_file, 'w') as f:
            f.write(generate_new_config())

        # Validação antes de sobrescrever
        validate_config(temp_file)

        # Atomic replace (POSIX garantido)
        temp_file.replace(config_file)
        logger.info("✅ Configuração atualizada com sucesso")

    except Exception as e:
        # 3. ROLLBACK ON FAILURE
        if backup_file.exists():
            backup_file.replace(config_file)
            logger.warning(
                "🛡️ ROLLBACK ATIVADO: Operação falhou, mas sistema "
                "restaurado para estado anterior. Nenhuma alteração aplicada."
            )
        raise  # Re-lança exceção após rollback

    finally:
        # 4. CLEANUP
        if backup_file.exists():
            backup_file.unlink()
            logger.debug("🧹 Backup removido")
```

### Checklist de Implementação

**Antes da Operação:**

- ✅ Criar backup com `shutil.copy2()` (preserva timestamps, permissões)
- ✅ Usar sufixo `.bak` para consistência
- ✅ Verificar se arquivo original existe (primeira execução)

**Durante a Operação:**

- ✅ Escrever em arquivo temporário primeiro (`.tmp`)
- ✅ Validar conteúdo antes de sobrescrever
- ✅ Usar `Path.replace()` para atomic rename (POSIX)
- ✅ Nunca sobrescrever diretamente com `open(..., 'w')`

**Após a Operação:**

- ✅ Em caso de sucesso: remover backup
- ✅ Em caso de falha: restaurar backup e re-lançar exceção
- ✅ Sempre fazer cleanup de arquivos temporários (`.tmp`)

### Exemplo Real: install_dev.py

O script `scripts/cli/install_dev.py` implementa este padrão:

```python
def install_dev_environment(workspace_root: Path) -> int:
    """Install development environment with rollback protection."""
    requirements_file = workspace_root / "requirements" / "dev.txt"
    backup_file: Path | None = None

    try:
        # Step 1: Install pip-tools
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], check=True)

        # Step 2: Create backup before compilation
        backup_file = _create_backup(requirements_file)

        # Step 3: Compile dependencies (atomic)
        safe_pip_compile(
            input_file=workspace_root / "requirements" / "dev.in",
            output_file=requirements_file,
            pip_compile_path="pip-compile",
            workspace_root=workspace_root,
        )

        # Step 4: Install with rollback protection
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                check=True
            )
        except subprocess.CalledProcessError:
            _restore_backup(backup_file, requirements_file)  # Rollback!
            raise

        # Step 5: Cleanup on success
        _cleanup_backup(backup_file)
        return 0

    except Exception as e:
        logger.error("❌ Installation failed: %s", e)
        return 1
```

### Anti-Padrões (Evitar)

❌ **Sobrescrever Direto**

```python
# ERRADO: Sem backup, sem validação
with open("config.yaml", "w") as f:
    f.write(new_config)  # Se falhar aqui, arquivo corrompido!
```

❌ **Backup Sem Rollback**

```python
# ERRADO: Backup existe mas não é usado
shutil.copy2("config.yaml", "config.yaml.bak")
with open("config.yaml", "w") as f:
    f.write(new_config)  # Falha aqui = arquivo corrompido
# Backup nunca é restaurado automaticamente!
```

❌ **Rollback Sem Re-raise**

```python
# ERRADO: Rollback silencioso esconde erro
try:
    update_config()
except Exception:
    restore_backup()
    # Faltou: raise!  Erro é engolido silenciosamente
```

### Quando Aplicar Este Padrão

**Aplicar sempre em:**

- ✅ Scripts de instalação/configuração
- ✅ Migrações de banco de dados
- ✅ Atualizações de arquivos `.env`
- ✅ Compilação de dependências (`pip-compile`, `poetry lock`)
- ✅ Geração de configuração a partir de templates

**Não necessário em:**

- ❌ Logs (append-only, não crítico)
- ❌ Cache (pode ser recriado)
- ❌ Arquivos temporários de build
- ❌ Outputs de testes

### Mensagens User-Friendly

Mensagens de erro devem focar na **solução**, não no problema:

**❌ Mensagem Técnica (Gera Ansiedade):**

```
⚠️ Installation failed. Rolled back: /path/to/requirements/dev.txt
```

**✅ Mensagem Orientada a Solução (Gera Confiança):**

```
🛡️ ROLLBACK ATIVADO: A instalação falhou, mas seu ambiente foi
restaurado com segurança para a versão anterior (dev.txt).
Nenhuma alteração foi aplicada.
```

**Princípios:**

1. Use emoji de proteção (🛡️) não de perigo (⚠️)
2. Enfatize "restaurado com segurança" antes de "falhou"
3. Seja explícito: "Nenhuma alteração aplicada"
4. Use apenas nome do arquivo, não path completo (menos poluição visual)

---

## 🎯 Resumo Executivo

| Padrão | Quando Usar | Benefício |
|--------|-------------|-----------|
| **Lazy Imports** | Type hints, dependências pesadas | Evita ciclos, reduz startup |
| **Sanitização de Ambiente** | Sempre em `subprocess.run()` | Previne vazamento de credenciais |
| **Tipagem em Testes** | Todo teste e fixture | Type safety, refactoring seguro |
| **Future Annotations** | Todo arquivo Python | Evita ciclos, melhora performance |
| **Atomicidade (Backup-Try-Rollback)** | Scripts de infra, arquivos críticos | Previne corrupção, zero downtime |
| **Enums vs Magic Strings** | Campos com valores restritos | Validação automática, type safety |

---

## 🔢 Enums vs Magic Strings

### Motivação

O uso de strings literais ("magic strings") em modelos de dados apresenta riscos significativos:

- **Erros de Digitação**: `severity = "HIHG"` passa despercebido até runtime
- **Falta de Autocomplete**: IDEs não sugerem valores válidos
- **Validação Manual**: Necessidade de validadores boilerplate
- **Refatoração Frágil**: Mudanças em strings exigem busca manual no código
- **Documentação Implícita**: Valores válidos ficam ocultos na implementação

### Solução: Enums Nativos

Em modelos de dados (Pydantic), **proíbe-se** o uso de strings literais para campos com valores restritos (ex: status, tipos, severidade).

**❌ Incorreto:**

```python
from pydantic import BaseModel, field_validator

class SecurityIssue(BaseModel):
    severity: str  # Qualquer string é aceita!
    category: str

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Manual validation boilerplate."""
        if v not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            raise ValueError(f"Invalid severity: {v}")
        return v
```

**✅ Correto:**

```python
from enum import Enum
from pydantic import BaseModel

class SecuritySeverity(str, Enum):
    """Severity levels for security issues.

    Inherits from str for JSON serialization compatibility.
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityCategory(str, Enum):
    """Categories of security issues."""
    INJECTION = "INJECTION"
    CRYPTO = "CRYPTO"
    AUTH = "AUTH"
    XSS = "XSS"

class SecurityIssue(BaseModel):
    severity: SecuritySeverity  # Type-safe, auto-validated
    category: SecurityCategory
```

### Benefícios

1. **Validação Automática**: Pydantic rejeita valores inválidos na instanciação
2. **Autocomplete**: IDEs mostram valores válidos ao digitar
3. **Type Safety**: Mypy detecta erros de tipo em tempo de análise
4. **Zero Boilerplate**: Elimina validadores manuais
5. **Refatoração Segura**: Renomear enum value é detectado pelo IDE
6. **Documentação Explícita**: Valores válidos ficam visíveis na definição

### Padrão: Herdar de `str, Enum`

```python
class Status(str, Enum):
    """Status must inherit from str for JSON serialization."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
```

**Por que `str, Enum` e não apenas `Enum`?**

- **JSON Serialization**: `str` permite serialização direta para JSON/YAML
- **Backward Compatibility**: Valores são strings comuns em APIs/DBs
- **Pydantic Integration**: Funciona perfeitamente com `model_dump()` e `model_dump_json()`

### Exemplo Real: Auditoria de Código

**Antes (v7.0):**

```python
# 30+ linhas de validadores manuais
class SecurityIssue(BaseModel):
    severity: str
    category: str

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if v not in allowed:
            raise ValueError(f"Invalid severity: {v}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = ["INJECTION", "CRYPTO", "AUTH", "XSS"]
        if v not in allowed:
            raise ValueError(f"Invalid category: {v}")
        return v
```

**Depois (v8.0):**

```python
# Zero validadores, validação automática
class SecurityIssue(BaseModel):
    severity: SecuritySeverity
    category: SecurityCategory
```

**Resultado:**

- 30+ linhas de código removidas
- Validação mais robusta (detecta erros antes do runtime com mypy)
- Melhor experiência de desenvolvimento (autocomplete, type hints)

### Quando Usar

✅ **Use Enums para:**

- Status de workflows (`PENDING`, `RUNNING`, `COMPLETED`)
- Níveis de severidade (`LOW`, `MEDIUM`, `HIGH`)
- Categorias de classificação (`TYPE_A`, `TYPE_B`)
- Modos de operação (`READ`, `WRITE`, `ADMIN`)
- Qualquer campo com conjunto finito e conhecido de valores

❌ **NÃO use Enums para:**

- Strings de texto livre (nomes, descrições)
- Valores dinâmicos (IDs gerados, timestamps)
- Conjuntos que mudam frequentemente (adicionar valor requer código change)

### Integração com Testes

```python
def test_enum_validation() -> None:
    """Verify Enum provides automatic validation."""
    # Valid: instanciação bem-sucedida
    issue = SecurityIssue(
        severity=SecuritySeverity.HIGH,
        category=SecurityCategory.INJECTION
    )
    assert issue.severity == SecuritySeverity.HIGH

    # Invalid: Pydantic rejeita automaticamente
    with pytest.raises(ValidationError):
        SecurityIssue(
            severity="HIHG",  # Typo detectado!
            category="INJECTION"
        )
```

### Migração de Strings para Enums

**Checklist:**

1. Definir Enum herdando de `str, Enum`
2. Substituir `field: str` por `field: EnumName`
3. Remover validadores manuais (`@field_validator`)
4. Atualizar testes para usar valores do Enum
5. Executar mypy para detectar usos incorretos
6. Validar serialização JSON/YAML

---

## 🌐 Requisições HTTP e Observabilidade

### Motivação

Sistemas distribuídos requerem **rastreabilidade end-to-end** para diagnóstico de problemas. Quando um serviço faz chamadas HTTP para APIs externas ou outros microserviços, precisamos:

- **Correlacionar logs** entre diferentes sistemas usando Trace IDs
- **Medir performance** (latência, taxa de erro, throughput)
- **Detectar falhas** rapidamente em cascatas de serviços
- **Garantir consistência** na instrumentação de código

### Princípio Fundamental

> **REGRA DE OURO:**
> É **PROIBIDO** usar `requests`, `httpx` ou qualquer cliente HTTP diretamente no código de produção.
> **OBRIGATÓRIO** usar wrapper centralizado com observabilidade integrada.

### Status Atual

⚠️ **ATENÇÃO:** O projeto atualmente **NÃO FAZ CHAMADAS HTTP EXTERNAS**.

Esta regra está documentada para **implementação futura**. Se você for o primeiro a precisar de chamadas HTTP:

1. Consulte `docs/architecture/OBSERVABILITY.md` para templates completos
2. Implemente `scripts/utils/http_client.py` baseado no padrão
3. Adicione testes em `tests/test_http_client.py`
4. Valide injeção de `X-Trace-ID` nos headers

### Padrão CORRETO ✅

```python
from scripts.utils.http_client import HttpClient
from scripts.utils.context import trace_context

def fetch_external_data(resource_id: str) -> dict:
    """Busca dados de API externa com observabilidade completa."""

    # Context manager garante Trace ID único para a operação
    with trace_context():
        client = HttpClient(base_url="https://api.example.com")

        # X-Trace-ID injetado automaticamente
        # Métricas de sucesso/falha registradas
        # Logs correlacionados
        response = client.get(f"/resources/{resource_id}")
        response.raise_for_status()

        return response.json()

# Benefícios automáticos:
# ✅ Header X-Trace-ID propagado
# ✅ Métricas: http_requests_total, http_request_duration_seconds
# ✅ Logs estruturados com Trace ID
# ✅ Tratamento de erros padronizado
```

### Padrão INCORRETO ❌

```python
import requests

def fetch_external_data(resource_id: str) -> dict:
    """NÃO FAZER ISSO!"""

    # ❌ Sem Trace ID - impossível correlacionar com logs internos
    # ❌ Sem métricas - não sabemos se está falhando
    # ❌ Sem logging padronizado - dificulta debugging
    # ❌ Sem retry logic - falhas transitórias viram incidentes
    response = requests.get(f"https://api.example.com/resources/{resource_id}")
    return response.json()
```

### Caso de Uso: Microserviços Distribuídos

Imagine um fluxo onde **Serviço A** → **Serviço B** → **Serviço C**:

```python
# Serviço A (entry point)
@app.post("/api/order")
def create_order(request: Request):
    # Extrai ou cria Trace ID
    trace_id = request.headers.get("X-Trace-ID")

    with trace_context(trace_id):
        logger.info("Starting order creation")

        # Chama Serviço B
        client = HttpClient()
        inventory_response = client.post(
            "http://service-b/api/reserve",
            json={"items": [...]}
        )

        # Trace ID propagado automaticamente para Serviço B!
        # Se Serviço B chamar Serviço C, o Trace ID continua o mesmo

        logger.info("Order creation completed")
        return {"order_id": "123", "trace_id": get_trace_id()}

# Resultado: Todos os logs de A, B e C têm o MESMO Trace ID
# Facilita debugar problemas em cascata
```

### Infraestrutura Atual

O projeto já possui **infraestrutura completa de Trace ID**:

| Componente | Status | Localização |
|-----------|--------|-------------|
| **Trace ID Context** | ✅ Implementado | `scripts/utils/context.py` |
| **Structured Logging** | ✅ Implementado | `scripts/utils/logger.py` |
| **HTTP Client Wrapper** | 📋 Template disponível | `docs/architecture/OBSERVABILITY.md` |
| **Metrics System** | 📋 Template disponível | `docs/architecture/OBSERVABILITY.md` |

### Justificativa

**Por que não usar `requests` diretamente?**

1. **Rastreabilidade Distribuída**
   - Sem Trace ID, é impossível correlacionar logs entre serviços
   - Debugging vira "caça às bruxas" sem contexto

2. **Métricas de Confiabilidade**
   - Precisamos saber: "Quantas chamadas para API X falharam hoje?"
   - SLAs e SLOs dependem de métricas precisas

3. **Consistência de Implementação**
   - Retry logic, timeouts, circuit breakers devem ser uniformes
   - Centralizar evita código duplicado

4. **Auditoria e Compliance**
   - Facilita auditorias de segurança
   - Permite rate limiting centralizado

### Exceções à Regra

✅ **Permitido usar `requests` diretamente em:**

- **Testes unitários** (com mocking apropriado)
- **Scripts de desenvolvimento** one-off (não em produção)
- **Exemplos didáticos** em documentação

❌ **NUNCA use `requests` diretamente em:**

- Código de produção (APIs, serviços)
- Scripts de CI/CD
- CLIs que fazem chamadas externas

### Checklist de Implementação

Ao adicionar a primeira chamada HTTP no projeto:

- [ ] Ler `docs/architecture/OBSERVABILITY.md` completamente
- [ ] Implementar `scripts/utils/http_client.py` baseado no template
- [ ] Implementar `scripts/utils/metrics.py` baseado no template
- [ ] Adicionar dependência `requests` ou `httpx` em `pyproject.toml`
- [ ] Criar `tests/test_http_client.py`
- [ ] Validar injeção de `X-Trace-ID` com testes
- [ ] Validar registro de métricas
- [ ] Executar `dev-audit` para verificar conformidade
- [ ] Atualizar este documento com exemplos reais

### Referências

- **Documentação Completa:** `docs/architecture/OBSERVABILITY.md`
- **Trace ID API:** `docs/guides/logging.md`
- **Sistema de Contexto:** `scripts/utils/context.py`

---

## 🎯 Resumo Executivo

---

## 📚 Referências

- [PEP 563 - Postponed Evaluation of Annotations](https://peps.python.org/pep-0563/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Python subprocess Security](https://docs.python.org/3/library/subprocess.html#security-considerations)

---

## 🤝 Contribuição

Se você identificar novos padrões ou melhorias para estes guidelines:

1. Documente o padrão com exemplos
2. Adicione testes que demonstrem o benefício
3. Abra PR com tag `docs` e `standards`
4. Referencie este documento em code reviews

---

**Última Atualização:** 2025-12-07
**Versão:** 1.1.0
**Autores:** DevOps Team
