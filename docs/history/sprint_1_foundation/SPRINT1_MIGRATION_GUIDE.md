# 🔧 Sprint 1 - Guia de Migração para Novo Sistema de Logging

**Relacionado:** [SPRINT1_AUDITORIA_FASE01.md](./SPRINT1_AUDITORIA_FASE01.md)

---

## 📋 Visão Geral

Este guia demonstra como migrar scripts existentes para o novo sistema de logging centralizado em `scripts/utils/logger.py`.

---

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

---

### Exemplo 2: `scripts/doctor.py` (Com Cores)

#### ❌ **ANTES** (Código Atual)

```python
import sys

# Códigos de Cores ANSI (para não depender de libs externas)
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

def run_diagnostics(self) -> bool:
    print(f"{BOLD}{BLUE}🔍 Dev Doctor - Diagnóstico{RESET}\n")

    for result in self.results:
        if result.passed:
            print(f"{GREEN}✓ {result.name}{RESET}")  # ❌ Cores sempre ativas
        else:
            print(f"{RED}✗ {result.name}{RESET}")    # ❌ Mesmo em pipes
```

**Problemas:**

- Cores aparecem em logs não-interativos
- Códigos ANSI poluem output em CI
- Sem logging estruturado

#### ✅ **DEPOIS** (Com Novo Logger e Cores Inteligentes)

```python
from scripts.utils.logger import setup_logging, get_colors

# Setup logger
logger = setup_logging(__name__)

# Get colors (desabilitadas automaticamente em pipes/CI)
colors = get_colors()
RED = colors.RED
GREEN = colors.GREEN
YELLOW = colors.YELLOW
BLUE = colors.BLUE
BOLD = colors.BOLD
RESET = colors.RESET

def run_diagnostics(self) -> bool:
    # Cores desabilitadas automaticamente se não for terminal interativo
    print(f"{BOLD}{BLUE}🔍 Dev Doctor - Diagnóstico{RESET}\n")

    for result in self.results:
        if result.passed:
            logger.info(f"{GREEN}✓ {result.name}{RESET}")  # → stdout
        else:
            logger.error(f"{RED}✗ {result.name}{RESET}")   # → stderr
```

**Melhorias:**

- Cores desabilitadas automaticamente em pipes: `python doctor.py | tee log.txt`
- Cores desabilitadas em CI sem quebrar nada
- Logs estruturados (com `logger.info/error`)
- Separação correta de streams

---

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

---

## 🧪 Exemplos de Output

### Antes: Logging Inadequado

```bash
$ python scripts/code_audit.py 2>/dev/null
2025-11-29 21:32:30 - audit - INFO - Starting audit...
2025-11-29 21:32:31 - audit - ERROR - File not found: test.py  # ❌ Não foi para stderr
2025-11-29 21:32:32 - audit - INFO - Audit completed
```

### Depois: Logging Correto

```bash
$ python scripts/code_audit.py 2>/dev/null
2025-11-29 21:32:30 - audit - INFO - Starting audit...
2025-11-29 21:32:32 - audit - INFO - Audit completed
# ✅ Erro foi para stderr e foi filtrado por 2>/dev/null

$ python scripts/code_audit.py 2>&1 | grep ERROR
2025-11-29 21:32:31 - audit - ERROR - File not found: test.py  # ✅ Capturado do stderr
```

---

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

---

## 📦 Template de Migração

### Para Scripts Simples

```python
# === REMOVER ===
# import logging
# import sys
# logging.basicConfig(...)
# logger = logging.getLogger(__name__)

# === ADICIONAR ===
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__)

# === O RESTO DO CÓDIGO PERMANECE IGUAL ===
```

### Para Scripts Com Cores

```python
# === REMOVER ===
# RED = "\033[91m"
# GREEN = "\033[92m"
# ...

# === ADICIONAR ===
from scripts.utils.logger import setup_logging, get_colors

logger = setup_logging(__name__)
colors = get_colors()
RED = colors.RED
GREEN = colors.GREEN
# ...

# === O RESTO DO CÓDIGO PERMANECE IGUAL ===
```

---

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

---

## 🧪 Testes Sugeridos

### Teste de Separação de Streams

```bash
# Criar script de teste
cat > test_logger.py << 'EOF'
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__)

logger.info("Mensagem INFO")
logger.warning("Mensagem WARNING")
logger.error("Mensagem ERROR")
EOF

# Teste 1: Apenas stdout
python test_logger.py 2>/dev/null
# Esperado: Apenas "Mensagem INFO"

# Teste 2: Apenas stderr
python test_logger.py 1>/dev/null
# Esperado: "Mensagem WARNING" e "Mensagem ERROR"

# Teste 3: Separar em arquivos
python test_logger.py 1>out.log 2>err.log
cat out.log  # Esperado: INFO
cat err.log  # Esperado: WARNING, ERROR
```

### Teste de Cores

```bash
# Teste 1: Terminal interativo (cores ativas)
python scripts/doctor.py
# Esperado: Cores renderizadas

# Teste 2: Pipe (cores desabilitadas)
python scripts/doctor.py | cat
# Esperado: Sem códigos ANSI

# Teste 3: NO_COLOR (cores desabilitadas)
NO_COLOR=1 python scripts/doctor.py
# Esperado: Sem cores
```

---

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

---

## 🚀 Próximos Passos

1. Implementar `scripts/utils/logger.py` (Fase 02)
2. Migrar `scripts/code_audit.py` (script crítico)
3. Migrar `scripts/smart_git_sync.py` (script crítico)
4. Migrar `scripts/doctor.py` (usa cores)
5. Migrar demais scripts
6. Atualizar documentação geral

---

**Status:** 📝 Guia preparado - Aguardando implementação do logger
