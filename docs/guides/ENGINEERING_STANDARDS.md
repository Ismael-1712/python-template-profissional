---
id: guide-engineering-standards
title: Padrões de Engenharia e Boas Práticas
type: guide
status: active
version: 1.0.0
author: DevOps Team
date: 2025-12-05
tags: [standards, python, security, typing, testing]
---

# Padrões de Engenharia e Boas Práticas

Este documento consolida as decisões técnicas e padrões de engenharia adotados no projeto. Todos os desenvolvedores devem seguir estas diretrizes para garantir consistência, segurança e manutenibilidade do código.

---

## 📚 Índice

1. [Lazy Imports](#lazy-imports)
2. [Sanitização de Ambiente](#sanitização-de-ambiente)
3. [Tipagem em Testes](#tipagem-em-testes)
4. [Future Annotations](#future-annotations)

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

## 🎯 Resumo Executivo

| Padrão | Quando Usar | Benefício |
|--------|-------------|-----------|
| **Lazy Imports** | Type hints, dependências pesadas | Evita ciclos, reduz startup |
| **Sanitização de Ambiente** | Sempre em `subprocess.run()` | Previne vazamento de credenciais |
| **Tipagem em Testes** | Todo teste e fixture | Type safety, refactoring seguro |
| **Future Annotations** | Todo arquivo Python | Evita ciclos, melhora performance |

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

**Última Atualização:** 2025-12-05
**Versão:** 1.0.0
**Autores:** DevOps Team
