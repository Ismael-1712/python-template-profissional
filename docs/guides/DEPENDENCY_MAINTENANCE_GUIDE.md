---
id: doc-guide-dep-001
type: guide
title: Dependency Maintenance Guide
version: 1.0.0
status: active
author: DevOps Team
date: 2025-12-14
tags: [dependencies, maintenance, guide]
---

# 🛠️ Guia de Manutenção - Dependências e Acoplamento

**Baseado em:** Tarefa [004] - Análise de Dependências Cíclicas
**Última Atualização:** 2025-12-14

---

## 🎯 Objetivo

Este guia fornece diretrizes práticas para manter a saúde arquitetural do projeto em relação a dependências e acoplamento.

---

## 📜 Regras Fundamentais

### 1. Hierarquia de Camadas (OBRIGATÓRIO)

```
cli/    (Nível 3) ─┐
                   ├─> Pode importar
core/   (Nível 2) ─┤
                   ├─> Pode importar
utils/  (Nível 1) ─┘
```

**Regras Rígidas:**

- ❌ **NUNCA:** `utils/` importa `core/` ou `cli/`
- ❌ **NUNCA:** `core/` importa `cli/`
- ✅ **OK:** `cli/` importa `core/` e `utils/`
- ✅ **OK:** `core/` importa `utils/`

### 2. Verificação Rápida (Pre-Commit)

Adicione ao `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Detectar violações de hierarquia

VIOLATIONS=$(grep -r "from scripts\." scripts/utils/*.py | grep -E "(core|cli)")
if [ -n "$VIOLATIONS" ]; then
    echo "❌ VIOLAÇÃO DE HIERARQUIA DETECTADA em utils/"
    echo "$VIOLATIONS"
    exit 1
fi

VIOLATIONS=$(grep -r "from scripts\.cli" scripts/core/**/*.py)
if [ -n "$VIOLATIONS" ]; then
    echo "❌ VIOLAÇÃO DE HIERARQUIA DETECTADA em core/"
    echo "$VIOLATIONS"
    exit 1
fi

echo "✅ Hierarquia de camadas OK"
```

---

## 🔴 Módulos Hub Críticos

### `scripts.utils.logger` (14 imports)

**⚠️ Atenção Especial Requerida**

#### Antes de Modificar

1. **Verificar Impacto:**

   ```bash
   grep -r "from scripts.utils.logger import" scripts/**/*.py | wc -l
   ```

2. **Checklist de Mudanças:**
   - [ ] API pública está preservada?
   - [ ] Breaking changes estão documentados?
   - [ ] Existe deprecation warning (mínimo 2 releases)?
   - [ ] Testes cobrem backward compatibility?

3. **Procedimento de Deprecation:**

   ```python
   # Antes (v1.0):
   def setup_logging(name: str) -> Logger:
       ...

   # Durante deprecation (v1.1):
   def setup_logging(name: str, *, new_param: str = "default") -> Logger:
       warnings.warn(
           "Parameter 'new_param' será obrigatório em v2.0",
           DeprecationWarning,
           stacklevel=2
       )
       ...

   # Depois (v2.0):
   def setup_logging(name: str, new_param: str) -> Logger:
       ...
   ```

#### Mudanças Permitidas sem Revisão

- ✅ Adicionar novos loggers
- ✅ Corrigir bugs internos
- ✅ Melhorar documentação
- ✅ Refatorar código interno (sem mudar API)

#### Mudanças que Requerem Revisão SRE

- 🔴 Alterar assinatura de `setup_logging()`
- 🔴 Remover ou renomear funções públicas
- 🔴 Mudar comportamento de `get_colors()`
- 🔴 Alterar stream handling (stdout/stderr)

---

### `scripts.utils.filesystem` (12 imports)

**⚠️ Contrato de Interface (Protocol)**

#### Regra de Ouro: Protocol Extension Only

❌ **ERRADO** (quebra 12 módulos):

```python
class FileSystemAdapter(Protocol):
    def read_text(self, path: Path) -> str:  # Mudou assinatura
        ...
```

✅ **CERTO** (backward compatible):

```python
class FileSystemAdapter(Protocol):
    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        ...

    # Novo método (opcional)
    def read_json(self, path: Path) -> dict[str, Any]:
        ...
```

#### Teste de Contrato Obrigatório

```python
# tests/test_filesystem_contract.py
import pytest
from scripts.utils.filesystem import FileSystemAdapter, RealFileSystem, MemoryFileSystem

@pytest.mark.parametrize("fs_class", [RealFileSystem, MemoryFileSystem])
def test_filesystem_adapter_contract(fs_class):
    """Garante que todas implementações seguem o Protocol."""
    fs = fs_class()
    assert isinstance(fs, FileSystemAdapter)
```

---

## 🟡 Padrões Aceitos (Não São Anti-Patterns)

### 1. TYPE_CHECKING para Type Hints

✅ **USO CORRETO** (não é ciclo real):

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.core.mock_generator import TestMockGenerator
else:
    TestMockGenerator = None  # Runtime fallback

class TestMockValidator:
    def __init__(self, generator: TestMockGenerator | None = None):
        ...
```

**Por quê?**

- Type hints não são executados em runtime
- Evita import overhead
- Resolve ciclos de tipos sem criar ciclos reais

### 2. Lazy Imports Documentados

✅ **USO CORRETO** (com documentação):

```python
def _get_mock_pattern_class() -> type[MockPattern]:
    """Lazy import to avoid circular dependency.

    MockPattern é importado apenas quando necessário para
    evitar carregar models_pydantic em tempo de módulo.
    """
    from scripts.core.mock_ci.models_pydantic import MockPattern
    return MockPattern
```

**Quando Usar:**

- Dependência pesada (Pydantic, SQLAlchemy)
- Evitar ciclo de inicialização
- Plugin system / extensões opcionais

**Quando NÃO Usar:**

- Imports leves (dataclasses, typing)
- Dependências core do módulo
- Performance crítica (lazy import tem overhead)

### 3. Try/Except Imports (Graceful Degradation)

✅ **USO CORRETO** (resiliência SRE):

```python
try:
    from scripts.utils.context import get_trace_id
except ImportError:
    logger.warning("⚠️ Observability degraded: tracing disabled")
    def get_trace_id() -> str:
        return "no-trace-id"
```

**Quando Usar:**

- Dependências opcionais
- Fallback para funcionalidade core
- Compatibilidade com ambientes limitados

**Quando NÃO Usar:**

- Dependências core obrigatórias
- Silenciar erros de instalação
- Ocultar bugs de import

---

## 🚨 Anti-Patterns a Evitar

### ❌ Import dentro de Utils para Core

```python
# ❌ ERRADO - scripts/utils/logger.py
from scripts.core.config import get_log_level  # VIOLAÇÃO!

def setup_logging(name: str) -> Logger:
    level = get_log_level()  # utils depende de core!
    ...
```

**Solução:**

```python
# ✅ CORRETO - Inversão de Dependência
def setup_logging(name: str, level: str = "INFO") -> Logger:
    # Quem chama (core ou cli) passa o level
    ...
```

### ❌ Ciclo Real de Imports

```python
# ❌ ERRADO - scripts/core/module_a.py
from scripts.core.module_b import ClassB

class ClassA:
    def use_b(self, b: ClassB):
        ...

# ❌ ERRADO - scripts/core/module_b.py
from scripts.core.module_a import ClassA

class ClassB:
    def use_a(self, a: ClassA):
        ...
```

**Solução 1: Extract Interface**

```python
# ✅ CORRETO - scripts/core/interfaces.py
from typing import Protocol

class InterfaceA(Protocol):
    def method(self) -> str: ...

class InterfaceB(Protocol):
    def other(self) -> int: ...

# module_a.py
from scripts.core.interfaces import InterfaceB

class ClassA:
    def use_b(self, b: InterfaceB):  # Depende de interface
        ...

# module_b.py
from scripts.core.interfaces import InterfaceA

class ClassB:
    def use_a(self, a: InterfaceA):  # Depende de interface
        ...
```

**Solução 2: TYPE_CHECKING**

```python
# ✅ CORRETO - usar TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.core.module_b import ClassB

class ClassA:
    def use_b(self, b: "ClassB"):  # String annotation
        ...
```

### ❌ God Object / Hub Excessivo

```python
# ❌ ERRADO - scripts/utils/everything.py com 50+ funções
def setup_logging(): ...
def parse_yaml(): ...
def run_subprocess(): ...
def validate_email(): ...
# ... 46 outras funções
```

**Solução: Single Responsibility**

```python
# ✅ CORRETO - Módulos focados
scripts/utils/logger.py      # Apenas logging
scripts/utils/yaml_parser.py # Apenas YAML
scripts/utils/subprocess.py  # Apenas subprocess
scripts/utils/validators.py  # Apenas validações
```

---

## 📊 Monitoramento Contínuo

### Comando de Auditoria (Executar Semanalmente)

```bash
#!/bin/bash
# scripts/audit_dependencies.sh

echo "🔍 Auditoria de Dependências"
echo "=" | head -c 70; echo

# 1. Verificar violações
echo "1. Verificando violações de hierarquia..."
VIOLATIONS=$(grep -r "from scripts\." scripts/utils/*.py | grep -E "(core|cli)")
if [ -n "$VIOLATIONS" ]; then
    echo "❌ VIOLAÇÕES DETECTADAS:"
    echo "$VIOLATIONS"
    exit 1
else
    echo "✅ Nenhuma violação"
fi

# 2. Contar TYPE_CHECKING
echo -e "\n2. Blocos TYPE_CHECKING:"
TYPE_CHECK_COUNT=$(grep -r "if TYPE_CHECKING:" scripts/**/*.py | wc -l)
echo "   Total: $TYPE_CHECK_COUNT"

# 3. Top hubs
echo -e "\n3. Top 5 Módulos Hub:"
grep -r "from scripts\." scripts/**/*.py 2>/dev/null | \
    cut -d: -f2 | \
    sort | uniq -c | \
    sort -rn | \
    head -5

echo -e "\n✅ Auditoria concluída"
```

### Métricas para Dashboards

```python
# scripts/ci/dependency_metrics.py
import json
from pathlib import Path

def collect_metrics():
    """Coleta métricas de dependências para dashboards."""
    return {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "layer_violations": count_violations(),
            "type_checking_blocks": count_type_checking(),
            "hub_modules": get_hub_modules(threshold=10),
            "circular_dependencies": detect_cycles(),
        }
    }
```

---

## 🛡️ Sistema de Autoimunidade de Dependências

**Adicionado:** 2026-01-06
**Versão:** 2.0.0

### Visão Geral

O sistema de autoimunidade protege contra commits com arquivos de dependências (`requirements.txt`) dessincronizados com seus arquivos fonte (`.in`). Esse problema pode causar:

- ❌ Falhas no CI/CD devido a versões incompatíveis
- ❌ Bugs silenciosos causados por dependências erradas
- ❌ Conflitos de merge em `requirements.txt`

### Camadas de Proteção

#### 1. 🔒 Pre-Commit Hook (Prevenção Local)

**Localização:** `.pre-commit-config.yaml`

```yaml
- id: lockfile-sync-guard
  name: "🔒 Lockfile Sync Guard"
  entry: python scripts/ci/verify_deps.py
  language: system
  files: ^requirements/.*\.(in|txt)$
```

**Comportamento:**

- Bloqueia commits se `requirements/dev.txt` não estiver sincronizado com `requirements/dev.in`
- Executa antes do commit (proteção imediata)
- Exibe mensagem de correção com comandos exatos

**Como corrigir se bloqueado:**

```bash
# Opção 1: Usar Makefile (recomendado)
make requirements

# Opção 2: Comando direto
python3.10 -m piptools compile requirements/dev.in -o requirements/dev.txt

# Depois do recompile:
git add requirements/dev.txt
git commit -m "chore: ressincronizar lockfile"
```

#### 2. 🩺 Dev Doctor (Diagnóstico Proativo)

**Comando:** `make doctor` ou `python -m scripts.cli.doctor`

**Nova verificação crítica:**

```python
check_lockfile_sync() -> DiagnosticResult:
    """Verifica sincronização entre .in e .txt"""
    # critical=True - Bloqueia se dessincronizado
```

**Output esperado:**

```
🔍 Dev Doctor - Diagnóstico de Ambiente

✓ Platform Strategy
  🖥️  Platform: LinuxStrategy | Git: git | ✓ fsync

✓ Python Version
  Python 3.10.15 (Sincronizado)

✓ Lockfile Sync
  requirements/dev.txt sincronizado com dev.in ✓

────────────────────────────────────────────────────
✓ Ambiente SAUDÁVEL - Pronto para desenvolvimento! 🎉
```

**Se dessincronizado:**

```
✗ Lockfile Sync
  ❌ requirements/dev.txt está DESSINCRONIZADO com dev.in!
  🔒 RISCO: Você pode estar trabalhando com dependências incorretas.
  💊 PRESCRIÇÃO:
     1. Execute: make requirements
     2. Ou: pip-compile requirements/dev.in -o requirements/dev.txt
     3. Depois: git add requirements/dev.txt

────────────────────────────────────────────────────
✗ Ambiente DOENTE - 1 problema(s) crítico(s) detectado(s)! 🚨
```

#### 3. 🚦 CI/CD (Última Linha de Defesa)

**Makefile target:** `make validate`

```makefile
validate: format deps-check lint type-check ... test
```

**Script:** `scripts/ci/verify_deps.py`

**Melhorias (v2.0):**

- ✅ Suporte a `PYTHON_BASELINE` env var (força uso de Python 3.10)
- ✅ Comparação ignora comentários e metadados do pip-compile
- ✅ Mensagens de erro detalhadas com comandos de correção

### Workflow Recomendado

#### Adicionando Nova Dependência

```bash
# 1. Editar arquivo .in
echo "requests>=2.31.0" >> requirements/dev.in

# 2. Recompilar lockfile (usa Python 3.10 baseline)
make requirements

# 3. Verificar mudanças
git diff requirements/dev.txt

# 4. Commit (pre-commit hook irá validar)
git add requirements/dev.in requirements/dev.txt
git commit -m "feat: adicionar requests para API calls"

# O pre-commit hook automaticamente valida:
# 🔒 Lockfile Sync Guard ... Passed
```

#### Atualizando Dependências

```bash
# Atualizar versão no .in
sed -i 's/pytest>=7.0.0/pytest>=8.0.0/' requirements/dev.in

# Recompilar
make requirements

# Revisar mudanças (pode atualizar dependências transitivas)
git diff requirements/dev.txt

# Commit
git add requirements/
git commit -m "chore: atualizar pytest para v8"
```

### Troubleshooting

#### ❌ Erro: "DESSINCRONIZADO" no CI mas local está OK

**Causa:** Diferença de versão Python entre local e CI

**Solução:**

```bash
# Verificar Python local
python --version
# Output: Python 3.11.5 (problema!)

# CI usa Python 3.10 (baseline)
# Forçar recompile com baseline:
make requirements

# Ou especificar explicitamente:
python3.10 -m piptools compile requirements/dev.in -o requirements/dev.txt
```

#### ❌ Pre-commit hook sempre falha mesmo após `make requirements`

**Causa:** Hook rodando com Python diferente do baseline

**Solução:**

```bash
# Verificar qual Python o hook está usando
pre-commit run lockfile-sync-guard --verbose

# Reinstalar pre-commit no venv correto
source .venv/bin/activate
pre-commit clean
pre-commit install
```

#### ❌ Conflito de merge em `requirements/dev.txt`

**Solução:**

```bash
# NUNCA resolver manualmente!
# Aceitar versão de uma branch:
git checkout --theirs requirements/dev.txt  # ou --ours

# Recompilar do zero:
make requirements

# Validar:
python scripts/ci/verify_deps.py

# Commit resolução:
git add requirements/dev.txt
git commit -m "chore: resolver conflito de lockfile via recompile"
```

### Python Baseline Strategy

O projeto usa **Python 3.10** como baseline para garantir compatibilidade CI/CD.

**Variável de ambiente:**

```bash
export PYTHON_BASELINE="3.10"
```

**Comportamento do `verify_deps.py`:**

1. Se `PYTHON_BASELINE` está definido:
   - Tenta usar `python3.10` (ou versão especificada)
   - Exibe warning se não encontrado
   - Fallback para Python do sistema

2. Se não definido:
   - Usa `.venv/bin/python` (desenvolvimento local)
   - Fallback para `sys.executable`

**Makefile integration:**

```makefile
PYTHON_BASELINE := 3.10

requirements:
 @python$(PYTHON_BASELINE) -m piptools compile ...
```

### Testes de Validação

**Arquivo:** `tests/test_dependency_safety.py`

**Cenários cobertos:**

- ✅ Cenário A: Arquivos sincronizados (deve passar)
- ✅ Cenário B: Arquivos dessincronizados (deve falhar)
- ✅ Cenário C: Python version mismatch (deve alertar)
- ✅ Integração com `verify_deps.py`
- ✅ Integração com Dev Doctor
- ✅ Simulação de pre-commit hook

**Executar testes:**

```bash
pytest tests/test_dependency_safety.py -v
```

### Referências Técnicas

- **Script de verificação:** [`scripts/ci/verify_deps.py`](../../scripts/ci/verify_deps.py)
- **Doctor check:** [`scripts/cli/doctor.py:check_lockfile_sync()`](../../scripts/cli/doctor.py)
- **Pre-commit config:** [`.pre-commit-config.yaml:lockfile-sync-guard`](../../.pre-commit-config.yaml)
- **Testes:** [`tests/test_dependency_safety.py`](../../tests/test_dependency_safety.py)

---

## 🎓 Checklist de Code Review

### Para Reviewers

Ao revisar PRs que tocam `scripts/`:

- [ ] Imports respeitam hierarquia (utils → core → cli)?
- [ ] Nenhum novo import de `core` em `utils`?
- [ ] Nenhum novo import de `cli` em `core`?
- [ ] Mudanças em `logger` ou `filesystem` têm testes?
- [ ] TYPE_CHECKING está sendo usado corretamente?
- [ ] Lazy imports estão documentados?

### Para Desenvolvedores

Antes de fazer commit:

```bash
# Executar verificação rápida
./scripts/audit_dependencies.sh

# Executar testes de contrato
pytest tests/test_filesystem_contract.py
pytest tests/test_logger_contract.py
```

---

## 📚 Referências

- [Tarefa [004] - Relatório Completo](./TASK_004_DEPENDENCY_ANALYSIS.md)
- [Sumário Executivo](../../TASK_004_SUMARIO_EXECUTIVO.md)
- [Diagrama de Dependências](./TASK_004_DEPENDENCY_DIAGRAM.md)
- [PEP 544 - Protocols](https://peps.python.org/pep-0544/)
- [PEP 563 - Postponed Annotation Evaluation](https://peps.python.org/pep-0563/)

---

**Mantido por:** SRE Team
**Última Revisão:** 2025-12-14
**Próxima Revisão:** 2026-01-14 (mensal)
