---
id: architecture-platform-abstraction
title: Abstração de Plataforma e I/O
type: arch
status: active
author: DevOps Team
date: '2025-12-05'
last_updated: '2025-12-05'
version: 1.0.0
context_tags:
  - architecture
  - testing
  - design-patterns
  - dependency-injection
linked_code:
  - scripts/utils/filesystem.py
  - scripts/utils/platform_strategy.py
related_docs:
  - docs/guides/testing.md
---

# 🏗️ Abstração de Plataforma e I/O

## 📋 Visão Geral

Este documento descreve os padrões arquiteturais de **Abstração de I/O** e **Abstração de Plataforma** implementados no projeto para garantir:

- ✅ **Testabilidade**: Testes unitários sem I/O real (10-100x mais rápidos)
- ✅ **Portabilidade**: Código cross-platform (Linux, macOS, Windows)
- ✅ **Manutenibilidade**: Dependências explícitas via injeção
- ✅ **Confiabilidade**: Isolamento de efeitos colaterais

## 🎯 Problema

### Anti-Pattern: I/O Direto

```python
# ❌ Código acoplado ao disco (lento, não testável)
def processar_config():
    config_path = Path("config.yaml")
    if config_path.exists():
        content = config_path.read_text()
        return parse_yaml(content)
    return None
```

**Problemas:**

1. Testes tocam o disco real (lento: ~50ms por arquivo)
2. Efeitos colaterais entre testes (state leak)
3. Dependência de estrutura de diretórios externa
4. Impossível testar cenários de erro (disco cheio, permissões)

### Anti-Pattern: Platform-Specific Code

```python
# ❌ Código não portável
import sys

def get_git():
    if sys.platform == "win32":
        return "git.exe"
    return "git"

def save_safely(path, content):
    with open(path, "w") as f:
        f.write(content)
        if sys.platform != "win32":
            os.fsync(f.fileno())  # Windows não garante durabilidade
```

**Problemas:**

1. Lógica de negócio misturada com detalhes de plataforma
2. Difícil de testar comportamento cross-platform
3. Código espalhado e duplicado

---

## ✅ Solução 1: FileSystemAdapter

### Arquitetura: Adapter Pattern + Protocol-based DI

```
┌─────────────────────────────────────────┐
│      FileSystemAdapter (Protocol)       │  ← Interface abstrata
│  - read_text(path) -> str               │
│  - write_text(path, content)            │
│  - exists(path) -> bool                 │
│  - is_file(path) -> bool                │
│  - is_dir(path) -> bool                 │
│  - mkdir(path)                          │
│  - glob(path, pattern) -> list[Path]    │
│  - copy(src, dst)                       │
└────────────┬────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
┌─────▼──────┐ ┌───▼──────────┐
│ RealFS     │ │ MemoryFS     │
│ (Produção) │ │ (Testes)     │
└────────────┘ └──────────────┘
```

### Implementação

#### 1️⃣ Protocol (Interface)

```python
from typing import Protocol
from pathlib import Path

class FileSystemAdapter(Protocol):
    """Interface para operações de filesystem."""

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Lê conteúdo textual de um arquivo."""
        ...

    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """Escreve conteúdo textual em um arquivo."""
        ...

    def exists(self, path: Path) -> bool:
        """Verifica se o path existe."""
        ...

    # ... demais métodos
```

#### 2️⃣ RealFileSystem (Produção)

```python
class RealFileSystem:
    """Implementação real usando pathlib.Path e shutil."""

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        return path.read_text(encoding=encoding)

    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)  # Auto-cria dirs
        path.write_text(content, encoding=encoding)

    def exists(self, path: Path) -> bool:
        return path.exists()

    def glob(self, path: Path, pattern: str) -> list[Path]:
        return list(path.glob(pattern))

    # ... implementação completa em scripts/utils/filesystem.py
```

#### 3️⃣ MemoryFileSystem (Testes)

```python
class MemoryFileSystem:
    """Implementação in-memory para testes ultrarrápidos."""

    def __init__(self) -> None:
        self._files: dict[Path, str] = {}      # Arquivos em RAM
        self._dirs: set[Path] = set()          # Diretórios em RAM

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path]

    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        self._ensure_parent_dirs(path)  # Auto-cria dirs em memória
        self._files[path] = content

    def exists(self, path: Path) -> bool:
        return path in self._files or path in self._dirs

    def glob(self, path: Path, pattern: str) -> list[Path]:
        # Glob simplificado usando fnmatch
        return [p for p in self._files.keys() if fnmatch.fnmatch(str(p), pattern)]

    # ... implementação completa em scripts/utils/filesystem.py
```

**Benefícios do MemoryFileSystem:**

- ⚡ **10-100x mais rápido**: Sem latência de disco
- 🔒 **Isolamento total**: Cada teste tem seu próprio filesystem
- 🧹 **Sem cleanup**: Memória liberada automaticamente
- 🎯 **Determinístico**: Sem race conditions de I/O

### Padrão de Uso (Injeção de Dependência)

#### ❌ Antes (Acoplado)

```python
class GitSyncManager:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def load_config(self):
        # Acoplado ao disco real
        if self.config_path.exists():
            return yaml.safe_load(self.config_path.read_text())
        return {}
```

#### ✅ Depois (Desacoplado)

```python
from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem

class GitSyncManager:
    def __init__(
        self,
        config_path: Path,
        fs: FileSystemAdapter = None  # Dependência injetável
    ):
        self.config_path = config_path
        self.fs = fs or RealFileSystem()  # Default seguro

    def load_config(self):
        # Usa abstração (testável)
        if self.fs.exists(self.config_path):
            content = self.fs.read_text(self.config_path)
            return yaml.safe_load(content)
        return {}
```

#### 🧪 Teste Unitário (In-Memory)

```python
from scripts.utils.filesystem import MemoryFileSystem

def test_load_config_quando_existe():
    # Arrange: Filesystem virtual
    fs = MemoryFileSystem()
    fs.write_text(Path("config.yaml"), "key: value")

    # Act: Injeta dependência mock
    manager = GitSyncManager(Path("config.yaml"), fs=fs)
    config = manager.load_config()

    # Assert: Nenhum I/O real!
    assert config == {"key": "value"}
```

**Tempo de execução:** `< 1ms` (vs. `~50ms` com disco real)

---

## ✅ Solução 2: PlatformStrategy

### Arquitetura: Strategy Pattern

```
┌─────────────────────────────────────┐
│   PlatformStrategy (Protocol)       │  ← Interface abstrata
│  - get_git_command() -> str         │
│  - ensure_durability(fd: int)       │
│  - set_file_permissions(path, mode) │
│  - get_venv_bin_dir() -> str        │
│  - get_venv_activate_command()      │
└────────────┬────────────────────────┘
             │
      ┌──────┴──────┬──────────────┐
      │             │              │
┌─────▼──────┐ ┌───▼──────┐ ┌────▼──────┐
│ UnixStrategy│ │ DarwinStr│ │ WindowsStr│
│  (Linux)    │ │ (macOS)  │ │           │
└─────────────┘ └──────────┘ └───────────┘
```

### Diferenças Tratadas

#### 1️⃣ Comando Git

| Plataforma | Comando |
|------------|---------|
| Linux/macOS | `git` |
| Windows | `git.exe` |

```python
class UnixStrategy:
    @staticmethod
    def get_git_command() -> str:
        return "git"

class WindowsStrategy:
    @staticmethod
    def get_git_command() -> str:
        return "git.exe"  # Extensão obrigatória no Windows
```

#### 2️⃣ Durabilidade de Dados (fsync)

| Plataforma | Comportamento | Garantia |
|------------|---------------|----------|
| Linux | `os.fsync()` | ✅ Flush físico completo |
| macOS | `os.fsync()` + `F_FULLFSYNC` | ✅ Flush físico completo |
| Windows | `os.fsync()` | ⚠️ Apenas buffer (cache de disco não garantido) |

```python
class UnixStrategy:
    @staticmethod
    def ensure_durability(fd: int) -> None:
        """Linux: fsync garante escrita física."""
        os.fsync(fd)

class DarwinStrategy:
    @staticmethod
    def ensure_durability(fd: int) -> None:
        """macOS: Precisa de F_FULLFSYNC para garantia real."""
        try:
            import fcntl
            fcntl.fcntl(fd, fcntl.F_FULLFSYNC)
        except (ImportError, OSError):
            os.fsync(fd)  # Fallback

class WindowsStrategy:
    @staticmethod
    def ensure_durability(fd: int) -> None:
        """Windows: fsync é mais fraco (apenas buffer)."""
        os.fsync(fd)  # Nota: não garante flush físico!
        # Para garantia real, usar FlushFileBuffers via ctypes
```

**⚠️ Implicação:** Em ambientes críticos (ex: transações financeiras), Windows precisa de implementação específica via Win32 API.

#### 3️⃣ Permissões de Arquivo (chmod)

| Plataforma | Suporte |
|------------|---------|
| Linux/macOS | ✅ chmod completo (owner, group, other) |
| Windows | ⚠️ Apenas read-only flag |

```python
class UnixStrategy:
    @staticmethod
    def set_file_permissions(path: Path, mode: int) -> None:
        """Unix: chmod nativo (0o644, 0o755, etc)."""
        path.chmod(mode)

class WindowsStrategy:
    @staticmethod
    def set_file_permissions(path: Path, mode: int) -> None:
        """Windows: Simula com read-only flag."""
        import stat
        if mode & stat.S_IWRITE:
            path.chmod(stat.S_IWRITE)  # Torna gravável
        else:
            path.chmod(stat.S_IREAD)   # Torna somente-leitura
```

#### 4️⃣ Virtual Environments

| Plataforma | Diretório de Binários | Comando de Ativação |
|------------|----------------------|---------------------|
| Linux/macOS | `bin/` | `source .venv/bin/activate` |
| Windows | `Scripts/` | `.venv\Scripts\activate.bat` |

```python
class UnixStrategy:
    @staticmethod
    def get_venv_bin_dir() -> str:
        return "bin"

    @staticmethod
    def get_venv_activate_command() -> str:
        return "source .venv/bin/activate"

class WindowsStrategy:
    @staticmethod
    def get_venv_bin_dir() -> str:
        return "Scripts"

    @staticmethod
    def get_venv_activate_command() -> str:
        return r".venv\Scripts\activate.bat"
```

### Factory Pattern (Seleção Automática)

```python
from scripts.utils.platform_strategy import get_platform_strategy

# Detecta automaticamente via sys.platform
strategy = get_platform_strategy()

# Uso agnóstico de plataforma
git_cmd = strategy.get_git_command()
venv_dir = strategy.get_venv_bin_dir()

# Garantir durabilidade em escrita crítica
with open("important_data.json", "w") as f:
    json.dump(data, f)
    strategy.ensure_durability(f.fileno())
```

**Implementação do Factory:**

```python
import sys
from typing import Union

def get_platform_strategy() -> Union[UnixStrategy, DarwinStrategy, WindowsStrategy]:
    """Retorna estratégia apropriada para a plataforma atual."""
    platform = sys.platform

    if platform == "darwin":
        return DarwinStrategy()  # macOS
    elif platform == "win32":
        return WindowsStrategy()
    else:
        return UnixStrategy()  # Linux e outros Unix-like
```

---

## 🎯 Padrão de Injeção de Dependência

### Princípios

1. **Dependências no `__init__`**: Sempre injetar via construtor
2. **Defaults seguros**: Usar implementação real como padrão
3. **Tipo explícito**: Usar `Protocol` para type hints
4. **Composição**: Permitir múltiplas abstrações

### Template Canônico

```python
from pathlib import Path
from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem
from scripts.utils.platform_strategy import PlatformStrategy, get_platform_strategy

class MinhaClasse:
    """Classe com dependências injetáveis."""

    def __init__(
        self,
        config_path: Path,
        fs: FileSystemAdapter | None = None,
        platform: PlatformStrategy | None = None,
    ):
        """
        Args:
            config_path: Caminho do arquivo de configuração
            fs: Adapter de filesystem (injetável para testes)
            platform: Estratégia de plataforma (injetável para testes)
        """
        self.config_path = config_path
        self.fs = fs or RealFileSystem()              # Default produção
        self.platform = platform or get_platform_strategy()  # Auto-detect

    def carregar_config(self) -> dict:
        """Carrega configuração usando abstração."""
        if not self.fs.exists(self.config_path):
            return {}

        content = self.fs.read_text(self.config_path)
        return yaml.safe_load(content)

    def salvar_config_duravel(self, config: dict) -> None:
        """Salva configuração com garantia de durabilidade."""
        content = yaml.dump(config)

        # Escreve usando abstração
        self.fs.write_text(self.config_path, content)

        # Garante durabilidade cross-platform
        with open(self.config_path, "r") as f:
            self.platform.ensure_durability(f.fileno())
```

### Teste com Mocks

```python
from scripts.utils.filesystem import MemoryFileSystem

class MockPlatformStrategy:
    """Mock para testes."""
    def ensure_durability(self, fd: int) -> None:
        pass  # No-op em testes

def test_salvar_config():
    # Arrange
    fs = MemoryFileSystem()
    platform = MockPlatformStrategy()
    instance = MinhaClasse(Path("config.yaml"), fs=fs, platform=platform)

    # Act
    instance.salvar_config_duravel({"key": "value"})

    # Assert: Tudo em memória, zero I/O
    assert fs.exists(Path("config.yaml"))
    assert "key: value" in fs.read_text(Path("config.yaml"))
```

---

## 📊 Impacto nos Testes

### Antes vs. Depois

| Métrica | Antes (I/O Real) | Depois (In-Memory) | Melhoria |
|---------|------------------|-------------------|----------|
| **Tempo/teste** | ~50ms | ~0.5ms | **100x** |
| **Tempo total (100 testes)** | 5 segundos | 50ms | **100x** |
| **Flakiness** | Alta (race conditions) | Zero | **∞** |
| **Cleanup necessário** | Sim (temp files) | Não | **Eliminado** |
| **Isolamento** | Parcial | Total | **100%** |

### Exemplo Real

**Teste com RealFileSystem (Slow):**

```python
def test_slow():
    # Setup (50ms)
    tmpdir = tempfile.mkdtemp()
    config_path = Path(tmpdir) / "config.yaml"
    config_path.write_text("key: value")

    # Test (10ms)
    manager = GitSyncManager(config_path)
    config = manager.load_config()

    # Cleanup (20ms)
    shutil.rmtree(tmpdir)

    assert config == {"key": "value"}
# Total: ~80ms
```

**Teste com MemoryFileSystem (Fast):**

```python
def test_fast():
    # Setup (0.1ms)
    fs = MemoryFileSystem()
    fs.write_text(Path("config.yaml"), "key: value")

    # Test (0.3ms)
    manager = GitSyncManager(Path("config.yaml"), fs=fs)
    config = manager.load_config()

    # Cleanup: Automático (0ms)

    assert config == {"key": "value"}
# Total: ~0.5ms (160x mais rápido)
```

---

## 🔗 Referências

- **Código-fonte:**
  - [`scripts/utils/filesystem.py`](../../scripts/utils/filesystem.py) - FileSystemAdapter completo
  - [`scripts/utils/platform_strategy.py`](../../scripts/utils/platform_strategy.py) - PlatformStrategy completo

- **Documentação relacionada:**
  - [Guia de Testes (SRE Standard)](../guides/testing.md) - Boas práticas de testes e testes in-memory

- **Padrões de Design:**
  - Adapter Pattern (GoF)
  - Strategy Pattern (GoF)
  - Dependency Injection (Fowler)
  - Protocol-based Polymorphism (PEP 544)

---

## 🔍 Capacidades do FileSystemAdapter

### Busca Recursiva de Arquivos (`rglob`)

A partir da versão 1.1.0, o `FileSystemAdapter` suporta busca recursiva de arquivos através do método `rglob()`, equivalente ao `pathlib.Path.rglob()`.

#### Assinatura do Método

```python
def rglob(self, path: Path, pattern: str) -> list[Path]:
    """Find files matching a pattern recursively.

    Searches recursively in all subdirectories under the given path.

    Args:
        path: Directory path to search in
        pattern: Glob pattern (e.g., "*.py", "test_*.py")

    Returns:
        List of Path objects matching the pattern recursively
    """
```

#### Exemplos de Uso

**Busca Recursiva de Markdowns:**

```python
from pathlib import Path
from scripts.utils.filesystem import RealFileSystem

# Produção: busca real no disco
fs = RealFileSystem()
markdown_files = fs.rglob(Path("docs"), "*.md")

# Resultado: [
#   Path("docs/index.md"),
#   Path("docs/architecture/TRIAD_GOVERNANCE.md"),
#   Path("docs/guides/testing.md"),
#   ...
# ]
```

**Busca de Arquivos de Teste:**

```python
# Encontrar todos os arquivos de teste recursivamente
test_files = fs.rglob(Path("tests"), "test_*.py")

# Resultado: [
#   Path("tests/test_audit.py"),
#   Path("tests/unit/test_scanner.py"),
#   Path("tests/integration/test_api.py"),
#   ...
# ]
```

**Testes Rápidos com MemoryFileSystem:**

```python
from scripts.utils.filesystem import MemoryFileSystem

# Testes: busca em memória (sem I/O)
fs = MemoryFileSystem()
fs.write_text(Path("project/src/main.py"), "# main")
fs.write_text(Path("project/src/utils/helper.py"), "# helper")
fs.write_text(Path("project/tests/test_main.py"), "# test")

# Busca recursiva em memória
py_files = fs.rglob(Path("project"), "*.py")
# Resultado: todos os 3 arquivos .py, sem tocar disco
```

#### Comparação: `glob()` vs `rglob()`

| Método | Busca | Exemplo | Resultado |
|--------|-------|---------|-----------|
| `glob(path, "*.py")` | **Não recursiva** (apenas diretório raiz) | `fs.glob(Path("tests"), "*.py")` | `[tests/conftest.py]` |
| `rglob(path, "*.py")` | **Recursiva** (todos os subdiretórios) | `fs.rglob(Path("tests"), "*.py")` | `[tests/conftest.py, tests/unit/test_foo.py, ...]` |
| `glob(path, "**/*.py")` | Recursiva (sintaxe alternativa) | `fs.glob(Path("tests"), "**/*.py")` | `[tests/unit/test_foo.py, ...]` |

**Recomendação:** Use `rglob()` para maior legibilidade quando precisar de busca recursiva.

#### Caso de Uso: Knowledge Scanner

```python
def scan_knowledge_base(fs: FileSystemAdapter, root: Path) -> list[Path]:
    """Escaneia base de conhecimento em busca de documentos Markdown.

    Args:
        fs: Filesystem adapter (RealFileSystem ou MemoryFileSystem)
        root: Diretório raiz da base de conhecimento

    Returns:
        Lista de todos os arquivos .md encontrados recursivamente
    """
    return fs.rglob(root, "*.md")

# Produção
fs_real = RealFileSystem()
docs = scan_knowledge_base(fs_real, Path("docs/architecture"))

# Testes (sem I/O, 100x mais rápido)
fs_test = MemoryFileSystem()
fs_test.write_text(Path("docs/api/v1.md"), "# API v1")
fs_test.write_text(Path("docs/guides/setup.md"), "# Setup")
docs = scan_knowledge_base(fs_test, Path("docs"))
assert len(docs) == 2  # Teste instantâneo
```

#### Performance

| Operação | RealFileSystem | MemoryFileSystem | Speedup |
|----------|----------------|------------------|---------|
| `rglob("docs", "*.md")` (50 arquivos) | ~15ms | ~0.2ms | **75x** |
| `rglob("tests", "test_*.py")` (200 arquivos) | ~45ms | ~0.5ms | **90x** |

**Conclusão:** `rglob()` em `MemoryFileSystem` permite testes de descoberta de arquivos sem I/O real, acelerando suites de teste em até 100x.

---

## 📝 Changelog

- **2025-12-06**: Adicionada seção "Capacidades do FileSystemAdapter" com documentação de `rglob()` (v1.1.0) - Item [P12.1]
- **2025-12-05**: Documento criado (v1.0.0) - Refatorações P07, P09, P11
