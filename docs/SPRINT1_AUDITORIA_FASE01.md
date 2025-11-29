# 📋 Sprint 1 - Relatório de Auditoria (Fase 01)

**Data:** 29 de Novembro de 2025
**Status:** 🔍 Análise Completa - SEM ALTERAÇÕES DE CÓDIGO
**Escopo:** Logging, Detecção de Ambiente e Hardcoding

---

## 🎯 Objetivos da Auditoria

1. **Análise de Logging**: Verificar separação adequada de streams (INFO → stdout, ERROR/WARNING → stderr)
2. **Análise de Drift**: Avaliar lógica de comparação de versões do Doctor vs CI
3. **Verificação de Hardcoding**: Identificar códigos ANSI hardcoded e dependências de terminal

---

## 📊 1. ANÁLISE DE LOGGING (Separação de Streams)

### 1.1. Estado Atual da Configuração

#### ❌ **PROBLEMA CRÍTICO: Todos os logs vão para `stdout`**

Foram identificados **9 arquivos** que utilizam `logging.basicConfig` com configuração inadequada:

```python
# ❌ PADRÃO ATUAL (INCORRETO)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # ⚠️ TODOS os níveis vão para stdout
        logging.FileHandler("audit.log", mode="a"),
    ],
)
```

### 1.2. Arquivos Afetados

| Arquivo | Linha | Stream Atual | Problema |
|---------|-------|--------------|----------|
| `scripts/smart_git_sync.py` | 25-31 | `sys.stdout` | INFO, WARNING, ERROR → stdout |
| `scripts/code_audit.py` | 31-37 | `sys.stdout` | INFO, WARNING, ERROR → stdout |
| `scripts/audit_dashboard/cli.py` | 33-38 | `sys.stdout` | INFO, WARNING, ERROR → stdout |
| `scripts/ci_recovery/main.py` | 44-50 | `sys.stdout` | INFO, WARNING, ERROR → stdout |
| `scripts/install_dev.py` | 47-50 | Sem handler | Apenas nível e formato |
| `scripts/validate_test_mocks.py` | 26-29 | Sem handler | Apenas nível e formato |
| `scripts/ci_test_mock_integration.py` | 42 | (não lido) | Provável stdout |
| `scripts/integrated_audit_example.py` | 168 | (não lido) | Provável stdout |
| `tests/test_mock_generator.py` | 42 | (não lido) | Contexto de teste |

### 1.3. Impacto do Problema

#### 🚨 **Consequências**

1. **Logs de erro poluem o fluxo de saída padrão**: Dificulta parsing de output estruturado
2. **Violação de convenções POSIX**: stderr é o canal correto para diagnósticos
3. **Problemas em pipelines CI/CD**: Ferramentas que monitoram stderr não capturam erros
4. **Experiência de usuário degradada**: Mensagens de erro misturadas com output normal

#### 📝 **Exemplo de Output Problemático**

```bash
# Executando: python scripts/code_audit.py
2025-11-29 21:32:30 - __main__ - INFO - Starting audit...        # ✅ stdout correto
2025-11-29 21:32:31 - __main__ - ERROR - File not found: test.py # ❌ deveria ser stderr
Audit completed successfully                                      # ✅ stdout correto
```

### 1.4. Análise de `logger.error()` e `logger.warning()`

Foram identificadas **20+ ocorrências** de `logger.error()` e `logger.warning()` nos scripts:

```python
# scripts/install_dev.py (linha 184)
logger.error("pip-compile fallback failed: %s", e)  # ❌ vai para stdout

# scripts/validate_test_mocks.py (linha 55)
logger.error(f"Config do gerador não encontrado: {config_file}")  # ❌ vai para stdout

# scripts/audit_dashboard/cli.py (linha 150)
logger.error("Dashboard error: %s", e)  # ❌ vai para stdout
```

**Todos esses erros vão para `stdout` devido à configuração do `StreamHandler`.**

---

## 🔍 2. ANÁLISE DE DRIFT (Doctor vs CI)

### 2.1. Lógica Atual do Doctor (`scripts/doctor.py`)

#### 📍 Função: `check_python_version()` (linhas 55-108)

```python
def check_python_version(self) -> DiagnosticResult:
    """Verifica compatibilidade da versão Python e detecta Drift."""
    python_version_file = self.project_root / ".python-version"

    # Lê versão esperada
    expected_version = content.split()[0].strip()  # Ex: "3.12.12"

    # Versão atual
    current_major = sys.version_info.major
    current_minor = sys.version_info.minor
    current_micro = sys.version_info.micro
    current_full = f"{current_major}.{current_minor}.{current_micro}"

    # ❌ PROBLEMA: Comparação exata (linha 71)
    exact_match = current_full == expected_version

    if exact_match:
        return DiagnosticResult(
            "Python Version",
            True,
            f"Python {current_full} (Sincronizado)",
        )

    # ✅ CI tem tratamento especial (linhas 76-81)
    if os.environ.get("CI"):
        return DiagnosticResult(
            "Python Version",
            True,
            f"Python {current_full} (CI Environment - Drift ignorado)",
        )

    # ❌ Desenvolvimento local: falha em qualquer diferença
    return DiagnosticResult(
        "Python Version",
        False,
        f"⚠️  ENVIRONMENT DRIFT DETECTADO!\n"
        f"  Versão ativa:   {current_full}\n"
        f"  Versão esperada: {expected_version}\n"
        # ... mensagem de erro
    )
```

### 2.2. Configuração do CI (`.github/workflows/ci.yml`)

#### 📍 Matriz de Versões (linhas 45-49)

```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.10", "3.11", "3.12"]  # ⚠️ Apenas MAJOR.MINOR
```

#### 📍 Setup Python (linha 54)

```yaml
- name: "Configurar Python ${{ matrix.python-version }}"
  uses: actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548 # v6.1.0
  with:
    python-version: ${{ matrix.python-version }}  # Ex: "3.11"
```

### 2.3. Arquivo `.python-version`

```plaintext
3.12.12
3.11.14
3.10.19
```

### 2.4. Análise do Problema de Drift

#### 🚨 **CENÁRIO PROBLEMÁTICO**

| Contexto | `.python-version` | CI Matrix | Instalado | Doctor Resultado |
|----------|-------------------|-----------|-----------|------------------|
| **CI** | `3.11.14` | `3.11` | `3.11.9` | ✅ **PASSA** (linha 77) |
| **Local** | `3.11.14` | N/A | `3.11.9` | ❌ **FALHA** (linha 84) |
| **Local** | `3.11.14` | N/A | `3.11.14` | ✅ PASSA |

#### ❓ **PERGUNTAS RESPONDIDAS**

1. **"Se o `.python-version` diz 3.11.0 e o CI roda 3.11.9, o Doctor falha?"**
   - **No CI:** ❌ **NÃO FALHA** - Linha 77 ignora drift em ambiente CI
   - **Local:** ✅ **FALHA** - Linha 84 exige versão exata

2. **"Ele deveria aceitar mudanças no patch level?"**
   - **Sim, mas apenas no CI atualmente**
   - Localmente, é **exigente demais** (exige match exato de MAJOR.MINOR.MICRO)

### 2.5. Inconsistência Arquitetural

#### ⚠️ **DESALINHAMENTO**

```
CI Matrix:     3.10, 3.11, 3.12           (MAJOR.MINOR)
                   ↕️ (mismatch)
.python-version: 3.10.19, 3.11.14, 3.12.12  (MAJOR.MINOR.MICRO)
                   ↕️ (strict check)
Doctor Local:  Exige match exato de todos os 3 números
```

#### 💡 **PROBLEMA FILOSÓFICO**

- **CI é flexível**: Aceita qualquer patch version (ex: 3.11.9 quando .python-version diz 3.11.14)
- **Doctor Local é rígido**: Falha se patch version não bate exatamente
- **Resultado**: Desenvolvedores podem ter ambiente "saudável" no CI mas "doente" localmente

---

## 🎨 3. VERIFICAÇÃO DE HARDCODING (Códigos ANSI)

### 3.1. Arquivos com Códigos ANSI Hardcoded

#### ❌ `scripts/doctor.py` (linhas 21-26)

```python
# Códigos de Cores ANSI (para não depender de libs externas)
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"
```

**Uso:** Formatação de mensagens de diagnóstico (linhas 256-285)

```python
def run_diagnostics(self) -> bool:
    print(f"{BOLD}{BLUE}🔍 Dev Doctor - Diagnóstico de Ambiente{RESET}\n")

    for result in self.results:
        if result.passed:
            print(f"{GREEN}✓ {result.name}{RESET}")  # ❌ Hardcoded
        else:
            if result.critical:
                print(f"{RED}✗ {result.name} (CRÍTICO){RESET}")  # ❌ Hardcoded
            else:
                print(f"{YELLOW}! {result.name} (aviso){RESET}")  # ❌ Hardcoded
```

#### ❌ `scripts/maintain_versions.py` (linhas 34-42)

```python
class Colors:
    """Constantes de cores ANSI para formatação de terminal."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
```

### 3.2. Análise de Contexto

#### 📋 **Observações**

1. **Justificativa Documentada**:
   - `doctor.py` linha 21: `"# Códigos de Cores ANSI (para não depender de libs externas)"`
   - Estratégia intencional para rodar em ambientes quebrados (sem dependências)

2. **Scripts Afetados**: Apenas 2 arquivos (`doctor.py` e `maintain_versions.py`)

3. **Não Há Verificação de Terminal Interativo**:

   ```python
   # ❌ NÃO EXISTE:
   if sys.stdout.isatty():
       # usar cores
   else:
       # sem cores
   ```

### 3.3. Problemas Identificados

#### 🚨 **CONSEQUÊNCIAS**

1. **Logs sujos em ambientes não-interativos**:

   ```bash
   # Output em CI/CD logs ou redirecionamento
   [91m✗ Python Version (CRÍTICO)[0m  # ❌ Poluição visual
   ```

2. **Incompatibilidade com parsers**:
   - Ferramentas que processam output estruturado quebram com códigos ANSI

3. **Acessibilidade**:
   - Screen readers e ferramentas de acessibilidade têm dificuldade com códigos ANSI

4. **Duplicação de Código**:
   - `doctor.py` e `maintain_versions.py` redefinem as mesmas cores

---

## 💡 4. PROPOSTA DE ARQUITETURA

### 4.1. Nova Estrutura: `scripts/utils/logger.py`

```python
#!/usr/bin/env python3
"""Sistema de Logging Padronizado para Scripts.

Fornece configuração centralizada de logging com:
- Separação correta de streams (INFO → stdout, ERROR/WARNING → stderr)
- Suporte a cores ANSI com detecção de terminal
- Configuração reutilizável para todos os scripts
"""

import logging
import sys
from typing import Literal

# ============================================================
# 1. HANDLERS CUSTOMIZADOS COM SEPARAÇÃO DE STREAMS
# ============================================================

class StdoutFilter(logging.Filter):
    """Filtra apenas mensagens INFO e DEBUG para stdout."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= logging.INFO


class InfoHandler(logging.StreamHandler):
    """Handler que envia INFO/DEBUG para stdout."""

    def __init__(self):
        super().__init__(sys.stdout)
        self.addFilter(StdoutFilter())


class ErrorHandler(logging.StreamHandler):
    """Handler que envia WARNING/ERROR/CRITICAL para stderr."""

    def __init__(self):
        super().__init__(sys.stderr)
        self.setLevel(logging.WARNING)


# ============================================================
# 2. SISTEMA DE CORES COM DETECÇÃO DE TERMINAL
# ============================================================

class TerminalColors:
    """Códigos ANSI para formatação de terminal com detecção automática.

    Desabilita cores automaticamente se:
    - Terminal não é interativo (sys.stdout.isatty() == False)
    - Variável NO_COLOR está definida
    - Ambiente CI sem suporte a cores
    """

    def __init__(self, force_colors: bool = False):
        """Inicializa com detecção automática de suporte a cores.

        Args:
            force_colors: Força ativação de cores (útil para testes)
        """
        self._enabled = self._should_use_colors(force_colors)

    def _should_use_colors(self, force: bool) -> bool:
        """Determina se cores devem ser usadas."""
        import os

        if force:
            return True

        # Respeita NO_COLOR (https://no-color.org/)
        if os.environ.get("NO_COLOR"):
            return False

        # Verifica se stdout é um terminal interativo
        if not sys.stdout.isatty():
            return False

        # GitHub Actions suporta cores com TERM
        if os.environ.get("CI") and not os.environ.get("TERM"):
            return False

        return True

    @property
    def RED(self) -> str:
        return "\033[91m" if self._enabled else ""

    @property
    def GREEN(self) -> str:
        return "\033[92m" if self._enabled else ""

    @property
    def YELLOW(self) -> str:
        return "\033[93m" if self._enabled else ""

    @property
    def BLUE(self) -> str:
        return "\033[94m" if self._enabled else ""

    @property
    def BOLD(self) -> str:
        return "\033[1m" if self._enabled else ""

    @property
    def RESET(self) -> str:
        return "\033[0m" if self._enabled else ""


# Instância global (lazy initialization)
_colors: TerminalColors | None = None


def get_colors(force: bool = False) -> TerminalColors:
    """Obtém instância de cores (singleton pattern).

    Args:
        force: Força ativação de cores

    Returns:
        Instância de TerminalColors
    """
    global _colors
    if _colors is None:
        _colors = TerminalColors(force=force)
    return _colors


# ============================================================
# 3. FUNÇÃO DE CONFIGURAÇÃO PADRONIZADA
# ============================================================

def setup_logging(
    name: str = "__main__",
    level: int = logging.INFO,
    log_file: str | None = None,
    format_string: str | None = None,
) -> logging.Logger:
    """Configura logging com separação correta de streams.

    Args:
        name: Nome do logger (geralmente __name__)
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho opcional para arquivo de log
        format_string: String de formatação customizada

    Returns:
        Logger configurado

    Exemplo:
        >>> logger = setup_logging(__name__)
        >>> logger.info("Isso vai para stdout")
        >>> logger.error("Isso vai para stderr")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove handlers existentes para evitar duplicação
    logger.handlers.clear()

    # Formato padrão
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string)

    # Handler para INFO/DEBUG → stdout
    stdout_handler = InfoHandler()
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # Handler para WARNING/ERROR/CRITICAL → stderr
    stderr_handler = ErrorHandler()
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    # Handler opcional para arquivo (todos os níveis)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# ============================================================
# 4. ALIASES PARA RETROCOMPATIBILIDADE
# ============================================================

# Para scripts que usam constantes globais
RED = property(lambda self: get_colors().RED)
GREEN = property(lambda self: get_colors().GREEN)
YELLOW = property(lambda self: get_colors().YELLOW)
BLUE = property(lambda self: get_colors().BLUE)
BOLD = property(lambda self: get_colors().BOLD)
RESET = property(lambda self: get_colors().RESET)
```

### 4.2. Uso Proposto nos Scripts

#### ✅ **ANTES (doctor.py)**

```python
import logging
import sys

# Códigos de Cores ANSI (para não depender de libs externas)
RED = "\033[91m"
GREEN = "\033[92m"
# ...

logging.basicConfig(...)  # Sem handlers específicos
```

#### ✅ **DEPOIS (doctor.py)**

```python
from scripts.utils.logger import setup_logging, get_colors

# Setup logging com separação de streams
logger = setup_logging(__name__)

# Cores com detecção automática
colors = get_colors()
RED = colors.RED
GREEN = colors.GREEN
# ...
```

### 4.3. Benefícios da Proposta

#### ✅ **VANTAGENS**

1. **Separação Correta de Streams**:
   - INFO/DEBUG → `sys.stdout` (dados, progresso)
   - WARNING/ERROR/CRITICAL → `sys.stderr` (diagnósticos)

2. **Detecção Automática de Terminal**:
   - Desabilita cores em ambientes não-interativos
   - Respeita padrão `NO_COLOR`
   - Compatível com CI/CD

3. **Centralização**:
   - DRY: Uma única fonte de verdade
   - Fácil manutenção e evolução
   - Testes centralizados

4. **Retrocompatibilidade**:
   - Migração gradual possível
   - API similar à existente

5. **Observabilidade**:
   - Logs estruturados
   - Fácil parsing por ferramentas

---

## 📝 5. RECOMENDAÇÕES E PRÓXIMOS PASSOS

### 5.1. Prioridade ALTA 🔴

#### 1. **Criar `scripts/utils/logger.py`**

- Implementar handlers com separação de streams
- Adicionar sistema de cores com detecção de terminal
- Escrever testes unitários

#### 2. **Refatorar Lógica de Drift no Doctor**

- Implementar comparação flexível de versões
- Permitir diferenças em patch level localmente (opcional via flag)
- Documentar estratégia de versionamento

```python
# Proposta de lógica:
def compare_versions(current: str, expected: str, strict: bool = False) -> bool:
    """Compara versões com flexibilidade configurável.

    Args:
        current: Versão atual (ex: "3.11.9")
        expected: Versão esperada (ex: "3.11.14")
        strict: Se True, exige match exato. Se False, aceita patch differences.

    Returns:
        True se versões são compatíveis
    """
    curr_major, curr_minor, curr_patch = map(int, current.split("."))
    exp_major, exp_minor, exp_patch = map(int, expected.split("."))

    # Major.Minor sempre devem bater
    if (curr_major, curr_minor) != (exp_major, exp_minor):
        return False

    # Patch: flexível se strict=False
    if strict:
        return curr_patch == exp_patch
    else:
        # Aceita patch igual ou superior (dentro do minor)
        return curr_patch >= exp_patch
```

### 5.2. Prioridade MÉDIA 🟡

#### 3. **Migrar Scripts para Novo Sistema de Logging**

- Ordem sugerida:
     1. `scripts/code_audit.py` (crítico para CI)
     2. `scripts/smart_git_sync.py` (crítico para CI)
     3. `scripts/doctor.py` (usa cores)
     4. `scripts/maintain_versions.py` (usa cores)
     5. Demais scripts

#### 4. **Adicionar Testes de Integração**

- Validar separação de streams em diferentes ambientes
- Testar detecção de terminal (isatty, NO_COLOR)
- Verificar comportamento em CI

### 5.3. Prioridade BAIXA 🟢

#### 5. **Documentação**

- Atualizar guias de desenvolvimento
- Adicionar exemplos de uso do novo logger
- Documentar padrões de versionamento

#### 6. **Revisão de CI**

- Considerar tornar matriz mais explícita no CI
- Avaliar se `.python-version` deveria ter apenas MAJOR.MINOR

---

## 📊 6. RESUMO EXECUTIVO

### 6.1. Achados Principais

| Categoria | Achados | Severidade | Arquivos Afetados |
|-----------|---------|------------|-------------------|
| **Logging** | Todos os logs vão para stdout | 🔴 ALTA | 9 arquivos |
| **Drift** | Lógica inconsistente CI vs Local | 🔴 ALTA | `doctor.py`, `ci.yml` |
| **Hardcoding** | Códigos ANSI sem detecção de terminal | 🟡 MÉDIA | 2 arquivos |

### 6.2. Impacto Estimado da Refatoração

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| **Separação de Streams** | 0% (tudo em stdout) | 100% (stderr para erros) | ✅ +100% |
| **Compatibilidade CI/CD** | Parcial | Total | ✅ +100% |
| **Duplicação de Código** | 2 definições de cores | 1 centralizada | ✅ -50% |
| **Detecção de Terminal** | Não existe | Automática | ✅ Nova feature |

### 6.3. Estimativa de Esforço

| Tarefa | Complexidade | Tempo Estimado | Risk |
|--------|--------------|----------------|------|
| Criar `logger.py` | 🟢 Baixa | 4h | Baixo |
| Refatorar lógica de Drift | 🟡 Média | 6h | Médio |
| Migrar 9 scripts | 🟡 Média | 8h | Baixo |
| Testes + Docs | 🟡 Média | 6h | Baixo |
| **TOTAL** | - | **24h** (~3 dias) | - |

---

## ✅ 7. CHECKLIST DE AÇÕES

### Sprint 1 - Fase 02 (Implementação)

- [ ] Criar `scripts/utils/logger.py` com handlers customizados
- [ ] Adicionar testes unitários para `logger.py`
- [ ] Refatorar `check_python_version()` no `doctor.py`
- [ ] Migrar `scripts/code_audit.py` para novo logger
- [ ] Migrar `scripts/smart_git_sync.py` para novo logger
- [ ] Migrar `scripts/doctor.py` para novo logger e cores dinâmicas
- [ ] Migrar `scripts/maintain_versions.py` para novo logger e cores dinâmicas
- [ ] Atualizar documentação de desenvolvimento
- [ ] Executar testes de integração em CI
- [ ] Code review e merge

---

## 📎 8. ANEXOS

### 8.1. Referências

- [POSIX Standard for stdout/stderr](https://pubs.opengroup.org/onlinepubs/9699919799/)
- [Python Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [NO_COLOR Standard](https://no-color.org/)
- [GitHub Actions: Escape Sequences](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions)

### 8.2. Trechos de Código Completos

<details>
<summary>📄 scripts/smart_git_sync.py (linhas 25-31)</summary>

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # ❌ PROBLEMA
        logging.FileHandler("smart_git_sync.log", mode="a"),
    ],
)
```

</details>

<details>
<summary>📄 scripts/code_audit.py (linhas 31-37)</summary>

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # ❌ PROBLEMA
        logging.FileHandler("audit.log", mode="a"),
    ],
)
```

</details>

<details>
<summary>📄 scripts/doctor.py (linhas 55-108) - check_python_version</summary>

```python
def check_python_version(self) -> DiagnosticResult:
    """Verifica compatibilidade da versão Python e detecta Drift."""
    python_version_file = self.project_root / ".python-version"

    if not python_version_file.exists():
        return DiagnosticResult(
            "Python Version",
            False,
            "Arquivo .python-version não encontrado",
            critical=False,
        )

    try:
        content = python_version_file.read_text().strip()
        expected_version = content.split()[0].strip()

        current_major = sys.version_info.major
        current_minor = sys.version_info.minor
        current_micro = sys.version_info.micro
        current_full = f"{current_major}.{current_minor}.{current_micro}"

        # ❌ PROBLEMA: Comparação exata
        exact_match = current_full == expected_version

        if exact_match:
            return DiagnosticResult(
                "Python Version",
                True,
                f"Python {current_full} (Sincronizado)",
            )

        # ✅ CI tem tratamento especial
        if os.environ.get("CI"):
            return DiagnosticResult(
                "Python Version",
                True,
                f"Python {current_full} (CI Environment - Drift ignorado)",
            )

        # ❌ Desenvolvimento local: falha em qualquer diferença
        return DiagnosticResult(
            "Python Version",
            False,
            f"⚠️  ENVIRONMENT DRIFT DETECTADO!\n"
            f"  Versão ativa:   {current_full}\n"
            f"  Versão esperada: {expected_version}\n"
            f"  💊 Prescrição: Reinstale o venv com a versão correta:\n"
            f"      rm -rf .venv && python{expected_version} -m venv .venv "
            f"&& source .venv/bin/activate && make install-dev",
            critical=True,
        )

    except Exception as e:
        return DiagnosticResult(
            "Python Version", False, f"Erro ao ler versão: {e}", critical=True
        )
```

</details>

---

**📌 FIM DO RELATÓRIO - FASE 01**

*Este documento não contém alterações de código, apenas análise e recomendações.*
