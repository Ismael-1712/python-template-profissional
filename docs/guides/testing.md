---
id: testing
type: guide
status: active
version: 1.1.0
author: Engineering Team
date: '2025-12-01'
last_updated: '2025-12-05'
context_tags:
  - testing
  - in-memory
  - filesystem
linked_code:
  - tests/test_smart_git_sync.py
  - scripts/utils/filesystem.py
related_docs:
  - docs/architecture/PLATFORM_ABSTRACTION.md
title: Guia de Testes (SRE Standard)
---

# 🧪 Guia de Testes (SRE Standard)

Este projeto adota uma filosofia estrita de **Testes Unitários Isolados**.
O objetivo é garantir que a suíte de testes seja rápida (< 50ms), determinística e segura (sem efeitos colaterais).

## 🚫 O Que Não Fazer (Anti-Patterns)

1. **Nunca toque no disco real:** Não use `os.mkdir`, `open("arquivo_real")` ou `tempfile.mkdtemp`.
2. **Nunca execute comandos reais:** Não chame `subprocess.run(["git", ...])` sem mock.
3. **Nunca dependa de estado externo:** Não assuma que o usuário tem Git instalado ou configurado.

## ✅ Como Escrever Testes (The Right Way)

Usamos `unittest.mock` intensivamente.

### Exemplo: Mockando Arquivos e Comandos

```python
from unittest.mock import MagicMock, patch
from pathlib import Path

# 1. Patch no subprocess (Blindagem)
@patch("scripts.git_sync.sync_logic.subprocess.run")
# 2. Patch no Path (Filesystem Virtual)
@patch("scripts.git_sync.sync_logic.Path")
def test_exemplo_seguro(self, mock_path, mock_run):

    # Configurar o Mock do Filesystem
    mock_path.return_value.exists.return_value = True

    # Configurar o Mock do Comando
    mock_run.return_value.returncode = 0

    # Executar (O código acha que está tocando no disco, mas não está)
    resultado = minha_funcao_perigosa()

    # Validar
    assert resultado == True
```

Consulte `tests/test_smart_git_sync.py` para exemplos avançados de mocks em cadeia.

---

## 🚀 Testes de Alta Velocidade (In-Memory)

### Problema: Testes Lentos com I/O Real

Testes que tocam o disco real são **lentos** e **frágeis**:

- ⏱️ **Latência**: 50-100ms por arquivo (vs. 0.5ms em memória)
- 🐛 **Flakiness**: Race conditions em testes paralelos
- 🧹 **Cleanup**: Necessário gerenciar arquivos temporários
- 🔒 **Isolamento**: Difícil garantir independência entre testes

### Solução: FileSystemAdapter + MemoryFileSystem

Use **`MemoryFileSystem`** para simular I/O em memória pura.

#### Exemplo: Teste com Disco Real (❌ Lento)

```python
import tempfile
import shutil
from pathlib import Path

def test_load_config_slow():
    # Setup (50ms) - cria diretório temporário
    tmpdir = tempfile.mkdtemp()
    config_path = Path(tmpdir) / "config.yaml"
    config_path.write_text("key: value")

    # Test (10ms)
    manager = GitSyncManager(config_path)
    config = manager.load_config()

    # Cleanup (20ms) - remove arquivos
    shutil.rmtree(tmpdir)

    assert config == {"key": "value"}
# Total: ~80ms
```

**Problemas:**

- Lento (80ms)
- Precisa de cleanup manual
- Pode deixar arquivos órfãos em caso de erro
- Não funciona bem em CI/CD com filesystem read-only

#### Exemplo: Teste In-Memory (✅ Rápido)

```python
from pathlib import Path
from scripts.utils.filesystem import MemoryFileSystem

def test_load_config_fast():
    # Setup (0.1ms) - filesystem virtual em RAM
    fs = MemoryFileSystem()
    fs.write_text(Path("config.yaml"), "key: value")

    # Test (0.3ms) - injeta dependência
    manager = GitSyncManager(Path("config.yaml"), fs=fs)
    config = manager.load_config()

    # Cleanup: Automático! (0ms)

    assert config == {"key": "value"}
# Total: ~0.5ms (160x mais rápido!)
```

**Benefícios:**

- ⚡ **160x mais rápido** (0.5ms vs 80ms)
- 🧹 **Zero cleanup** (garbage collector cuida)
- 🔒 **Isolamento total** (cada teste tem seu próprio filesystem)
- 🎯 **Determinístico** (sem race conditions)

### API Completa do MemoryFileSystem

```python
from pathlib import Path
from scripts.utils.filesystem import MemoryFileSystem

# Criar filesystem virtual
fs = MemoryFileSystem()

# Escrever arquivos
fs.write_text(Path("config.yaml"), "key: value")
fs.write_text(Path("data/users.json"), '{"name": "Alice"}')

# Ler arquivos
content = fs.read_text(Path("config.yaml"))  # "key: value"

# Verificar existência
assert fs.exists(Path("config.yaml"))        # True
assert fs.is_file(Path("config.yaml"))       # True
assert fs.is_dir(Path("data"))               # True
assert not fs.exists(Path("inexistente"))    # False

# Criar diretórios
fs.mkdir(Path("logs/2025/12"))

# Glob patterns (simplificado)
files = fs.glob(Path("."), "*.yaml")         # [Path("config.yaml")]

# Copiar arquivos
fs.copy(Path("config.yaml"), Path("backup/config.yaml"))
```

### Padrão de Injeção de Dependência

Para tornar código testável, **injete** o `FileSystemAdapter`:

#### ❌ Código Não Testável

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

#### ✅ Código Testável (com DI)

```python
from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem

class GitSyncManager:
    def __init__(
        self,
        config_path: Path,
        fs: FileSystemAdapter | None = None  # Injeção
    ):
        self.config_path = config_path
        self.fs = fs or RealFileSystem()  # Default produção

    def load_config(self):
        # Usa abstração
        if self.fs.exists(self.config_path):
            content = self.fs.read_text(self.config_path)
            return yaml.safe_load(content)
        return {}
```

#### 🧪 Teste Unitário

```python
def test_load_config_quando_existe():
    # Arrange
    fs = MemoryFileSystem()
    fs.write_text(Path("config.yaml"), "key: value")

    # Act
    manager = GitSyncManager(Path("config.yaml"), fs=fs)
    config = manager.load_config()

    # Assert
    assert config == {"key": "value"}

def test_load_config_quando_nao_existe():
    # Arrange
    fs = MemoryFileSystem()  # Filesystem vazio

    # Act
    manager = GitSyncManager(Path("config.yaml"), fs=fs)
    config = manager.load_config()

    # Assert
    assert config == {}
```

### Cenários Avançados

#### Simulando Erros de I/O

```python
from scripts.utils.filesystem import MemoryFileSystem

def test_handle_file_not_found():
    fs = MemoryFileSystem()
    manager = GitSyncManager(Path("config.yaml"), fs=fs)

    # Arquivo não existe, deve retornar {}
    config = manager.load_config()
    assert config == {}

def test_read_invalid_yaml():
    fs = MemoryFileSystem()
    fs.write_text(Path("config.yaml"), "invalid: [yaml")  # YAML inválido

    manager = GitSyncManager(Path("config.yaml"), fs=fs)

    with pytest.raises(yaml.YAMLError):
        manager.load_config()
```

#### Testando Operações de Diretório

```python
def test_create_nested_directories():
    fs = MemoryFileSystem()

    # Cria estrutura profunda
    fs.mkdir(Path("logs/2025/12/05"))
    fs.write_text(Path("logs/2025/12/05/app.log"), "INFO: Started")

    # Verifica hierarquia
    assert fs.is_dir(Path("logs"))
    assert fs.is_dir(Path("logs/2025"))
    assert fs.is_dir(Path("logs/2025/12"))
    assert fs.is_file(Path("logs/2025/12/05/app.log"))
```

#### Testando Glob Patterns

```python
def test_find_test_files():
    fs = MemoryFileSystem()
    fs.write_text(Path("test_utils.py"), "# test")
    fs.write_text(Path("test_models.py"), "# test")
    fs.write_text(Path("main.py"), "# app")

    # Busca apenas testes
    test_files = fs.glob(Path("."), "test_*.py")

    assert len(test_files) == 2
    assert Path("test_utils.py") in test_files
    assert Path("test_models.py") in test_files
    assert Path("main.py") not in test_files
```

### Quando Usar vs. Mocks Tradicionais

| Cenário | Use MemoryFileSystem | Use unittest.mock |
|---------|---------------------|-------------------|
| **Testes de lógica de negócio** | ✅ Sim | ❌ Verboso |
| **Múltiplas operações I/O** | ✅ Sim (simples) | ❌ Complexo |
| **Verificar estado do filesystem** | ✅ Sim (natural) | ⚠️ Trabalhoso |
| **Código legado sem DI** | ❌ Não (precisa refatorar) | ✅ Sim (patch) |
| **Testar erro específico** | ⚠️ Limitado | ✅ Sim (mock.side_effect) |
| **Operações binárias** | ❌ Não (apenas texto) | ✅ Sim |

### Migração Gradual

Se você tem código legado usando `unittest.mock`, migre gradualmente:

1. **Adicione injeção de dependência** no construtor
2. **Use MemoryFileSystem em novos testes**
3. **Mantenha mocks antigos funcionando** (não quebre)
4. **Refatore aos poucos** conforme tocar no código

### Limitações do MemoryFileSystem

⚠️ **Não suporta:**

- Arquivos binários (apenas texto UTF-8)
- Permissões de arquivo (sempre 0o644 implícito)
- Links simbólicos
- Timestamps (criação/modificação)
- Glob patterns complexos (apenas `*` e `?`)

Para esses casos, use `unittest.mock.patch` ou `RealFileSystem` com `tempfile`.

### Referências

- [Abstração de Plataforma e I/O](../architecture/PLATFORM_ABSTRACTION.md) - Design detalhado
- [`scripts/utils/filesystem.py`](../../scripts/utils/filesystem.py) - Código-fonte completo
- [Testes Existentes](../../tests/) - Exemplos práticos

---

**Última atualização:** 2025-12-05 (v1.1.0) - Adicionada seção de testes in-memory
