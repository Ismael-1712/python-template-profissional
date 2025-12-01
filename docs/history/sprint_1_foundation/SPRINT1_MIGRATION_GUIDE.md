---
id: sprint1-migration-guide
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code:
- scripts/utils/logger.py
- scripts/code_audit.py
- scripts/doctor.py
- scripts/smart_git_sync.py
title: Sprint 1 - Guia de Migração para Novo Sistema de Logging
---

# 🔧 Sprint 1 - Guia de Migração para Novo Sistema de Logging

**Relacionado:** [SPRINT1_AUDITORIA_FASE01.md](./SPRINT1_AUDITORIA_FASE01.md)

## 🔄 Exemplos de Migração

### Exemplo 1: `scripts/code_audit.py`

#### ❌ **ANTES** (Código Atual)

```python
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # ❌ Tudo vai para stdout
        logging.FileHandler("audit.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# Uso:
logger.info("Starting audit...")       # → stdout ✅
logger.error("File not found")         # → stdout ❌ (deveria ser stderr)
```

#### ✅ **DEPOIS** (Com Novo Logger)

```python
from scripts.utils.logger import setup_logging

# Configure logging com separação automática de streams
logger = setup_logging(
    name=__name__,
    level=logging.INFO,
    log_file="audit.log"
)

# Uso (sem mudanças):
logger.info("Starting audit...")       # → stdout ✅
logger.error("File not found")         # → stderr ✅ (corrigido automaticamente!)
```

**Mudanças:**

- Removido `import sys` (não mais necessário)
- Removido `logging.basicConfig()` (substituído por `setup_logging()`)
- Nenhuma mudança nas chamadas de log!

### Exemplo 3: Comparação de Versões (Doctor)

#### ❌ **ANTES** (Código Atual)

```python
def check_python_version(self) -> DiagnosticResult:
    """Verifica compatibilidade da versão Python e detecta Drift."""
    expected_version = "3.11.14"  # De .python-version
    current_full = "3.11.9"        # sys.version_info

    # ❌ Comparação rígida
    exact_match = current_full == expected_version  # False!

    if exact_match:
        return DiagnosticResult(True, "OK")

    # ✅ Apenas CI é flexível
    if os.environ.get("CI"):
        return DiagnosticResult(True, "CI - Drift ignorado")

    # ❌ Local falha
    return DiagnosticResult(False, "DRIFT DETECTADO!")
```

**Resultado:**

- Local: ❌ Falha (exige 3.11.14, tem 3.11.9)
- CI: ✅ Passa (ignora diferença)

#### ✅ **DEPOIS** (Com Comparação Flexível)

```python
def check_python_version(self, strict: bool = False) -> DiagnosticResult:
    """Verifica compatibilidade da versão Python e detecta Drift.

    Args:
        strict: Se True, exige match exato. Se False (padrão), aceita
                diferenças no patch level (recomendado para desenvolvimento).
    """
    expected_version = "3.11.14"
    current_full = "3.11.9"

    # ✅ Comparação flexível por padrão
    if self._compare_versions(current_full, expected_version, strict=strict):
        return DiagnosticResult(True, f"Python {current_full} (Compatível)")

    return DiagnosticResult(False, "DRIFT DETECTADO!")

def _compare_versions(self, current: str, expected: str, strict: bool) -> bool:
    """Compara versões com flexibilidade configurável."""
    curr_parts = tuple(map(int, current.split(".")))
    exp_parts = tuple(map(int, expected.split(".")))

    # Major.Minor sempre devem bater
    if curr_parts[:2] != exp_parts[:2]:
        return False

    # Patch: flexível se strict=False
    if strict:
        return curr_parts[2] == exp_parts[2]  # Exige exato
    else:
        return curr_parts[2] >= exp_parts[2]  # Aceita >= (mais novo OK)
```

**Resultado (com `strict=False`):**

- Local: ✅ Passa (3.11.9 ≠ 3.11.14, mas major.minor batem)
- CI: ✅ Passa (mesma lógica)

**Resultado (com `strict=True`):**

- Local: ❌ Falha (exige 3.11.14 exato)
- CI: ❌ Falha (mesma lógica)

**Flexibilidade:**

```bash
# Modo padrão (flexível - recomendado)
python scripts/doctor.py

# Modo estrito (CI/CD onde precisão é crítica)
python scripts/doctor.py --strict-version-check
```

### Antes: Cores em Pipe

```bash
$ python scripts/doctor.py | cat
^[[1m^[[94m🔍 Dev Doctor - Diagnóstico^[[0m  # ❌ Códigos ANSI no output

^[[92m✓ Python Version^[[0m                  # ❌ Poluição visual
```

### Depois: Cores Inteligentes

```bash
$ python scripts/doctor.py | cat
🔍 Dev Doctor - Diagnóstico                   # ✅ Sem códigos ANSI

✓ Python Version                               # ✅ Limpo e legível
```

```bash
$ python scripts/doctor.py  # Terminal interativo
🔍 Dev Doctor - Diagnóstico  # ✅ Cores renderizadas corretamente
✓ Python Version             # ✅ Verde bonito
```

## ✅ Checklist de Migração

### Para Cada Script

- [ ] Localizar `logging.basicConfig()`
- [ ] Substituir por `setup_logging()`
- [ ] Remover imports desnecessários (`sys` para stdout/stderr)
- [ ] Se usa cores: substituir constantes por `get_colors()`
- [ ] Testar em ambiente interativo
- [ ] Testar com pipe: `python script.py | cat`
- [ ] Testar redirecionamento: `python script.py 2>errors.log`
- [ ] Verificar que erros vão para stderr: `python script.py 2>/dev/null`
- [ ] Rodar testes automatizados
- [ ] Atualizar documentação do script

## 📚 Referências Rápidas

### API do Novo Logger

```python
# Setup básico
logger = setup_logging(__name__)

# Com arquivo de log
logger = setup_logging(__name__, log_file="app.log")

# Com nível DEBUG
logger = setup_logging(__name__, level=logging.DEBUG)

# Com formato customizado
logger = setup_logging(
    __name__,
    format_string="%(levelname)s: %(message)s"
)
```

### API das Cores

```python
# Get colors (desabilitadas automaticamente em pipes)
colors = get_colors()

# Forçar cores (útil para testes)
colors = get_colors(force=True)

# Usar cores
print(f"{colors.RED}Erro{colors.RESET}")
print(f"{colors.GREEN}Sucesso{colors.RESET}")
```

**Status:** 📝 Guia preparado - Aguardando implementação do logger
