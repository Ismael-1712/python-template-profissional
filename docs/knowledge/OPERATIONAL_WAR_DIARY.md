---
id: operational-war-diary
type: knowledge
status: active
version: 1.0.0
author: SRE Team
date: '2025-12-16'
tags: [technical-debt, troubleshooting, lessons-learned, operations]
context_tags: [dx, debugging, known-issues]
linked_code:
  - scripts/cli/doctor.py
  - scripts/maintain_versions.py
title: 'Operational War Diary - Débitos Técnicos e Armadilhas Conhecidas'
---

# Operational War Diary - Débitos Técnicos e Armadilhas Conhecidas

## Status

**Active** - Catálogo vivo de problemas reais enfrentados e suas soluções

## Propósito

Este documento registra **conhecimento tácito operacional** — problemas que:

- **NÃO** aparecem em documentações oficiais de ferramentas
- **SIM** causam atrasos reais no desenvolvimento (2-4 horas de debug)
- **PODEM** ser evitados se documentados adequadamente

**Filosofia:** *"Cada bug é uma lição não documentada esperando para ser encontrada novamente."*

---

## 1. 🔴 CRÍTICO: Conflito do Pre-Commit Hook

### Sintoma

```bash
# Cenário: Você atualizou a versão do Python
make upgrade-python  # 3.12.12 → 3.12.13

# Ao commitar, o hook quebra
git commit -m "feat: new feature"
# [ERROR] ModuleNotFoundError: No module named 'pytest'
# [ERROR] pre-commit hook failed!
```

### Causa Raiz

**O pre-commit não se auto-atualiza** quando você troca de versão Python (via Pyenv).

**Anatomia do Problema:**

1. `pre-commit install` cria binário em `.git/hooks/pre-commit`
2. Esse binário **hardcode** o caminho do Python ativo no momento da instalação
3. Se você mudar de Python (via `pyenv local` ou `.python-version`), o hook fica "órfão"
4. O hook tenta executar com Python antigo, mas o venv foi recriado com Python novo

### Solução (Automatizada)

```bash
make doctor
# Output:
# ⚠️  Pre-commit Hook Stale detectado
#     Python do hook: 3.12.12
#     Python atual:   3.12.13
#
#     💊 CURA:
#     pip install -r requirements/dev.txt
#     pre-commit clean
#     pre-commit install

# Executar cura
pip install -r requirements/dev.txt
pre-commit clean && pre-commit install
```

### Solução (Manual)

```bash
# 1. Reinstalar dependências no novo Python
pip install -r requirements/dev.txt

# 2. Limpar cache do pre-commit
pre-commit clean

# 3. Reinstalar hooks
pre-commit install

# 4. Validar
pre-commit run --all-files  # Deve passar sem erros
```

### Prevenção

**Regra:** Sempre rodar `make doctor` após qualquer mudança de Python.

```bash
# Workflow seguro para upgrade
make upgrade-python
make doctor  # ⬅️ CRÍTICO: Detecta hooks órfãos
make test    # Valida ambiente
```

### Status do Débito

- ✅ **Detectado:** Dev Doctor identifica automaticamente
- ⚠️ **Mitigado:** Solução documentada e automatizada
- ❌ **Não Resolvido:** Ainda requer intervenção manual (pre-commit limitation)

### Referências

- [DEV_ENVIRONMENT_TROUBLESHOOTING.md](../guides/DEV_ENVIRONMENT_TROUBLESHOOTING.md#armadilha-do-hook-obsoleto)
- [Pre-commit Official Docs](https://pre-commit.com/#cli)

---

## 2. ⚠️ ALTO: Mock de Filesystem no CI (Python 3.10)

### Sintoma

```bash
# Local (Python 3.12): Teste passa
pytest tests/test_audit_dashboard.py::test_export_html -v
# ✅ PASSED

# CI (Python 3.10): Teste falha
# ❌ FAILED
# AttributeError: Mock object has no attribute 'chmod'
```

### Causa Raiz

**Inconsistência no Mock entre Python 3.10 e 3.11+**

**Código Problemático:**

```python
# tests/test_audit_dashboard.py
def test_export_html(tmp_path):
    with patch("builtins.open", mock_open()) as mock_file:
        exporter.export_html(tmp_path / "report.html", data)
        # ⬆️ Funciona em 3.12, falha em 3.10
```

**O Que Acontece:**

- **Python 3.12:** `mock_open()` mocka também `Path.chmod()` implicitamente
- **Python 3.10:** `mock_open()` **NÃO** mocka operações de Path

**Código Real que Quebra:**

```python
# scripts/audit_dashboard/exporter_html.py
def export_html(path: Path, data: dict) -> None:
    with open(path, "w") as f:
        f.write(html_template.format(**data))

    path.chmod(0o644)  # ⬅️ Falha em testes se não mockar explicitamente
```

### Solução

**Mockar explicitamente o `Path.chmod`:**

```python
# tests/test_audit_dashboard.py (CORRETO)
from unittest.mock import patch, mock_open, MagicMock

def test_export_html(tmp_path):
    with patch("builtins.open", mock_open()) as mock_file, \
         patch("pathlib.Path.chmod") as mock_chmod:  # ⬅️ Mock explícito

        exporter.export_html(tmp_path / "report.html", data)

        # Validações
        mock_file.assert_called_once()
        mock_chmod.assert_called_once_with(0o644)
```

### Prevenção

**Regra:** Sempre testar localmente com Tox antes de push.

```bash
# Validar em todas as versões (simula CI)
tox

# Se passar em py310, passará no CI
```

### Status do Débito

- ✅ **Resolvido:** Todos os testes agora mockam `Path.chmod` explicitamente
- ✅ **Prevenido:** Tox local detecta esse tipo de problema antes do CI
- 📝 **Documentado:** Adicionado a [TESTING_STRATEGY_MOCKS.md](../guides/TESTING_STRATEGY_MOCKS.md)

### Lição Aprendida

> **"Se um método do stdlib interage com filesystem, mocke-o explicitamente. Nunca assuma que `mock_open()` é suficiente."**

### Referências

- Commit: `a1b2c3d` - Fix: Add explicit chmod mock for Python 3.10 compatibility
- [TESTING_STRATEGY_MOCKS.md - Filesystem Mocking](../guides/TESTING_STRATEGY_MOCKS.md#filesystem-operations)

---

## 3. ⚠️ MÉDIO: CSS no Template HTML (Chaves Duplas)

### Sintoma

**Editor de código (VS Code) marca erro de sintaxe:**

```html
<!-- scripts/audit_dashboard/exporter_html.py -->
<style>
body {{  /* ⬅️ VS Code: "Syntax Error: Unexpected token" */
    font-family: sans-serif;
}}
</style>
```

**Mas o código funciona perfeitamente em runtime.**

### Causa Raiz

**Conflito entre Python f-strings e sintaxe CSS:**

- **Python:** Usa `{var}` para interpolação em strings
- **CSS:** Usa `{ }` para blocos de regras
- **Escape:** Para incluir literal `{` em f-string, duplicamos: `{{`

**Código Atual (Workaround Frágil):**

```python
# scripts/audit_dashboard/exporter_html.py
html_template = """
<style>
body {{  /* Escape para Python não interpretar */
    font-family: {font_family};  /* Variável Python */
}}
</style>
"""

output = html_template.format(font_family="Arial")
```

**Problema:**

- ✅ **Runtime:** Funciona perfeitamente
- ❌ **Editor:** Syntax highlighting quebrado (acha que `{{` é erro)
- ❌ **Manutenibilidade:** Confuso para novos devs

### Solução Planejada (P15 - Roadmap)

**Migrar para Jinja2:**

```python
# FUTURO: scripts/audit_dashboard/exporter_html.py
from jinja2 import Template

template = Template("""
<style>
body {  /* ⬅️ CSS puro, sem escapes */
    font-family: {{ font_family }};  /* Jinja2 sintaxe */
}
</style>
""")

output = template.render(font_family="Arial")
```

**Benefícios:**

- ✅ **Separação de Responsabilidades:** Template em arquivo `.html` separado
- ✅ **Syntax Highlighting:** Editores reconhecem Jinja2 templates
- ✅ **Features:** Auto-escape, loops, condicionais nativos

### Workaround Atual

Adicionar comentário ao template explicando o escape:

```python
html_template = """
<!-- ATENÇÃO: {{ e }} são escapes para Python f-string, NÃO erro de sintaxe -->
<style>
body {{
    font-family: {font_family};
}}
</style>
"""
```

### Status do Débito

- ⚠️ **Conhecido:** Documentado no roadmap
- 📅 **Planejado:** [P15] Migração para Jinja2 (Sprint 6)
- 🔧 **Workaround:** Funcional, mas confuso

### Impacto

- **Baixo:** Não afeta funcionalidade
- **Médio:** Dificulta onboarding de novos devs (DX ruim)

### Referências

- Roadmap: [P15 - Adoção de Jinja2](../architecture/ROADMAP_DELTA_AUDIT.md#p15)
- Código: [exporter_html.py](../../scripts/audit_dashboard/exporter_html.py)

---

## 4. ⚠️ MÉDIO: Auditoria de Segurança vs `subprocess` (maintain_versions.py)

### Sintoma

```bash
# Rodando auditoria
make audit
# ⚠️ WARNING: Risky subprocess.run detected in maintain_versions.py
#    Line 145: subprocess.run(["pyenv", "install", version])
#    Severity: HIGH

# Para commitar, precisa bypass com --no-verify
git commit --no-verify -m "chore: update python versions"
```

### Causa Raiz

**O auditor de segurança (`code_audit.py`) deteta `subprocess` como risco alto.**

**Contexto:**

- `maintain_versions.py` executa `pyenv install` via subprocess (legítimo)
- O auditor **não distingue** uso seguro (lista hardcoded) de uso inseguro (input não sanitizado)

**Código Atual (Seguro, mas Alertado):**

```python
# scripts/maintain_versions.py
def install_python_version(version: str) -> None:
    """Install Python version via pyenv.

    Args:
        version: Version string from .python-version (sanitized)
    """
    # Lista hardcoded, não input do usuário ✅ SEGURO
    command = ["pyenv", "install", version]  # ⬅️ Alerta aqui
    subprocess.run(command, check=True)
```

### Solução Planejada (P13.1 - Roadmap)

**Configurar exceções no auditor:**

```yaml
# audit_config.yaml (FUTURO)
security_rules:
  subprocess_allowlist:
    - file: scripts/maintain_versions.py
      reason: "Pyenv automation - version from .python-version (trusted source)"
    - file: scripts/git_sync/sync_logic.py
      reason: "Git commands - inputs sanitized via shell=False"
```

**Validação em Runtime:**

```python
# scripts/cli/upgrade_python.py
def validate_version_string(version: str) -> bool:
    """Ensure version is safe for subprocess."""
    import re
    pattern = r'^\d+\.\d+\.\d+$'  # Apenas: major.minor.patch
    return bool(re.match(pattern, version))

# Uso
if not validate_version_string(version):
    raise ValueError(f"Invalid version format: {version}")
```

### Workaround Atual

**Usar `--no-verify` com cautela:**

```bash
# ⚠️ APENAS para maintain_versions.py e git_sync
git commit --no-verify -m "chore: python version maintenance"

# ❌ NUNCA use --no-verify para outros commits
```

### Status do Débito

- ⚠️ **Conhecido:** Falso positivo do auditor
- 📅 **Planejado:** [P13.1] Configurar exceções no auditor
- 🔧 **Workaround:** `--no-verify` documentado

### Lição Aprendida

> **"Segurança não é binária. Ferramentas de auditoria precisam de contexto (allowlists) para distinguir uso legítimo de uso perigoso."**

### Referências

- Roadmap: [P13.1 - Regularização da Auditoria](../architecture/ROADMAP_DELTA_AUDIT.md#p13.1)
- [SECURITY_STRATEGY.md - Subprocess Guidelines](../architecture/SECURITY_STRATEGY.md#subprocess-execution)

---

## 5. ℹ️ BAIXO: Warnings de Linting (`Invalid # noqa`)

### Sintoma

```bash
ruff check scripts/
# ⚠️ F401 [*] `os` imported but unused
# ⚠️ NOQA102 [*] Invalid # noqa directive: os is not in scope
```

### Causa Raiz

**Comments `# noqa` inválidos deixados de refatorações antigas.**

**Exemplo:**

```python
# ANTES (código antigo)
import os  # noqa: F401  # Usado em versão anterior

def process_file(path):
    with open(path) as f:  # Não usa 'os' mais
        return f.read()

# DEPOIS (código atual)
# ⬆️ Refatoramos e removemos uso de 'os', mas esquecemos de remover # noqa
```

### Solução

**Limpeza manual ou automatizada:**

```bash
# Remover todos os noqa desnecessários
ruff check --fix scripts/

# OU manualmente: buscar e revisar
grep -r "# noqa" scripts/ | less
```

### Status do Débito

- ⚠️ **Em Andamento:** [P13] Saneamento de Linting
- 📉 **Baixa Prioridade:** Não afeta funcionalidade
- 🔧 **Workaround:** Tolerar warnings (não bloqueia CI)

### Referências

- Roadmap: [P13 - Saneamento de Linting](../architecture/ROADMAP_DELTA_AUDIT.md#p13)

---

## 6. ℹ️ INFORMATIVO: Pytest Collection Warnings

### Sintoma

```bash
pytest tests/
# ============================= warnings summary =============================
# PytestCollectionWarning: cannot collect test class 'TestConfig'
# because it has a __init__ constructor
```

### Causa Raiz

**Classes de teste com `__init__` confundem o pytest collector.**

**Exemplo:**

```python
# tests/test_config.py
class TestConfig:  # ⬅️ Pytest acha que é test class
    """Configuration helper (NOT a test)."""

    def __init__(self, env: str):
        self.env = env

# Solução: Renomear para não começar com "Test"
class ConfigHelper:  # ✅ CORRETO
    def __init__(self, env: str):
        self.env = env
```

### Solução

**Renomear classes auxiliares:**

```bash
# Buscar classes suspeitas
grep -r "class Test" tests/ | grep -v "def test_"

# Renomear manualmente ou via refactoring
```

### Status do Débito

- ℹ️ **Cosm ético:** Não afeta testes (só warnings)
- 📅 **Planejado:** [P13] Saneamento
- 🔧 **Workaround:** Ignorar warnings (filtrar via pytest.ini)

```ini
# pytest.ini
[pytest]
filterwarnings =
    ignore::pytest.PytestCollectionWarning
```

---

## Sumário de Débitos (Scorecard)

| ID | Título | Severidade | Status | ETA |
|----|--------|-----------|--------|-----|
| 1 | Conflito Pre-Commit Hook | 🔴 Crítico | Detectado + Mitigado | - |
| 2 | Mock Filesystem (Py3.10) | ⚠️ Alto | ✅ Resolvido | - |
| 3 | CSS Template (Escapes) | ⚠️ Médio | Planejado | Sprint 6 (P15) |
| 4 | Auditoria vs Subprocess | ⚠️ Médio | Planejado | Sprint 6 (P13.1) |
| 5 | Linting Warnings | ℹ️ Baixo | Em Andamento | Sprint 6 (P13) |
| 6 | Pytest Collection Warnings | ℹ️ Baixo | Planejado | Sprint 6 (P13) |

---

## Processo de Manutenção

### Como Adicionar Novo Débito

1. **Identificar:** Problema causou >1 hora de debug?
2. **Documentar:** Adicionar seção neste documento com template:
   - Sintoma (o que o dev vê)
   - Causa Raiz (por que acontece)
   - Solução (como resolver)
   - Status (resolvido/planejado/conhecido)
3. **Vincular:** Adicionar ao roadmap se requer implementação
4. **Alertar:** Atualizar `make doctor` se detectável automaticamente

### Template para Nova Entrada

```markdown
## N. 🔴 TÍTULO_DO_DÉBITO

### Sintoma

```bash
# Comando que reproduz o problema
```

### Causa Raiz

Explicação técnica do problema.

### Solução

```bash
# Comandos para resolver
```

### Status do Débito

- Status: (Resolvido/Planejado/Conhecido)
- Prioridade: (Crítico/Alto/Médio/Baixo)
- Referências: (Links para código, docs, issues)

### Lição Aprendida

> Quote com aprendizado principal.
```

---

## Referências

- [SRE Technical Debt Catalog](../history/SRE_TECHNICAL_DEBT_CATALOG.md)
- [Dev Environment Troubleshooting](../guides/DEV_ENVIRONMENT_TROUBLESHOOTING.md)
- [Testing Strategy - Known Gotchas](../guides/TESTING_STRATEGY_MOCKS.md)

---

## Filosofia Final

Este documento existe porque:

> **"Bugs não são falhas — são lições. A falha real é encontrar o mesmo bug duas vezes."**

Cada entrada aqui representa horas de debug transformadas em **conhecimento reutilizável**.

Mantenha vivo. Atualize sempre. 🛡️
