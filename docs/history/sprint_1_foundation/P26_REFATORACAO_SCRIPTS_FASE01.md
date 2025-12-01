---
id: p26-refatoracao-scripts-fase01
type: reference
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code:
- scripts/cli/install_dev.py
- scripts/core/mock_generator.py
- scripts/core/mock_validator.py
- scripts/cli/doctor.py
- scripts/cli/audit.py
- scripts/cli/git_sync.py
- scripts/cli/upgrade_python.py
- scripts/cli/mock_ci.py
- scripts/utils/banner.py
title: 'P26 - Refatoração de Scripts: Fase 01 - Auditoria e Planejamento'
---

# P26 - Refatoração de Scripts: Fase 01 - Auditoria e Planejamento

**Data**: 30 de Novembro de 2025
**Objetivo**: Mapear dependências e planejar migração de scripts soltos para estrutura de pacote organizada
**Status**: ✅ Auditoria Completa

## 📊 1. Inventário de Scripts (Raiz)

### Scripts Executáveis (10 arquivos)

Todos os scripts abaixo possuem `if __name__ == "__main__":` e são executáveis diretamente.

| Script | Linhas | Tipo | Descrição |
|--------|--------|------|-----------|
| `audit_dashboard.py` | 51 | **Wrapper CLI** | Wrapper de compatibilidade para `audit_dashboard/` |
| `code_audit.py` | 369 | **CLI Principal** | Auditoria de segurança e qualidade de código |
| `doctor.py` | 388 | **CLI Principal** | Diagnóstico preventivo de ambiente |
| `install_dev.py` | 244 | **Bootstrap Script** | ⚠️ Script de instalação (pré-venv) |
| `smart_git_sync.py` | 112 | **CLI Wrapper** | Interface para `git_sync/` |
| `maintain_versions.py` | 327 | **CLI Principal** | Automação de versões Python (pyenv) |
| `ci_test_mock_integration.py` | 552 | **CLI Principal** | Integração de mocks no CI/CD |
| `integrated_audit_example.py` | 212 | **Exemplo/Demo** | Demonstração de integração |
| `test_mock_generator.py` | 772 | **CLI Principal** | Gerador de mocks para testes |
| `validate_test_mocks.py` | 524 | **CLI Principal** | Validador de mocks gerados |

## 🏗️ 3. Classificação Funcional

### 3.1 **CLI Tools** (Ferramentas Executáveis)

Devem ir para `scripts/cli/`:

| Script | Justificativa | Banner Necessário |
|--------|---------------|-------------------|
| `doctor.py` | Ferramenta de diagnóstico ativa | ✅ Sim |
| `code_audit.py` | Ferramenta de auditoria ativa | ✅ Sim |
| `smart_git_sync.py` | Wrapper CLI para git sync | ✅ Sim |
| `maintain_versions.py` | Gerenciador de versões Python | ✅ Sim |
| `ci_test_mock_integration.py` | Integração de CI/CD | ✅ Sim |

### 3.2 **Core Libraries** (Lógica de Negócio)

Devem ir para `scripts/core/`:

| Script | Justificativa | Banner Necessário |
|--------|---------------|-------------------|
| `test_mock_generator.py` | Motor de geração de mocks | ✅ Sim (quando CLI) |
| `validate_test_mocks.py` | Motor de validação de mocks | ✅ Sim (quando CLI) |

### 3.3 **Wrappers de Compatibilidade**

Mantêm localização atual (temporário):

| Script | Justificativa | Ação |
|--------|---------------|------|
| `audit_dashboard.py` | Wrapper para `audit_dashboard/` | Manter 1 ciclo de release |
| `smart_git_sync.py` | Wrapper fino para `git_sync/` | Pode migrar para CLI |

### 3.4 **Exemplos e Demos**

Devem ir para `examples/` ou ser removidos:

| Script | Justificativa | Ação |
|--------|---------------|------|
| `integrated_audit_example.py` | Demonstração de integração | Mover para `examples/` |

### 3.5 **Bootstrap Scripts** (⚠️ Caso Especial)

Devem permanecer na raiz:

| Script | Justificativa | Ação |
|--------|---------------|------|
| `install_dev.py` | Executado **antes** do venv existir | **MANTER NA RAIZ** |

## 🎯 5. Arquitetura Target (Proposta)

### 5.1 Estrutura de Diretórios Proposta

```
scripts/
├── __init__.py                    # Torna scripts/ um pacote Python
├── cli/                           # 🆕 CLI Tools (Executáveis)
│   ├── __init__.py
│   ├── audit.py                   # ← code_audit.py (renomeado)
│   ├── doctor.py                  # ← doctor.py
│   ├── git_sync.py                # ← smart_git_sync.py (renomeado)
│   ├── install_dev.py             # ← install_dev.py
│   ├── mock_ci.py                 # ← ci_test_mock_integration.py
│   ├── mock_generate.py           # ← test_mock_generator.py (quando CLI)
│   ├── mock_validate.py           # ← validate_test_mocks.py (quando CLI)
│   └── upgrade_python.py          # ← maintain_versions.py
│
├── core/                          # 🆕 Lógica de Negócio (Bibliotecas)
│   ├── __init__.py
│   ├── mock_generator.py          # ← test_mock_generator.py (classes)
│   └── mock_validator.py          # ← validate_test_mocks.py (classes)
│
├── utils/                         # ✅ Já existe - manter
│   ├── __init__.py
│   ├── atomic.py
│   ├── logger.py
│   └── safe_pip.py
│
├── audit/                         # ✅ Já existe - manter
│   └── ...
│
├── audit_dashboard/               # ✅ Já existe - manter
│   └── ...
│
├── ci_recovery/                   # ✅ Já existe - manter
│   └── ...
│
└── git_sync/                      # ✅ Já existe - manter
    └── ...
```

### 5.2 Wrappers Temporários (Backward Compatibility)

Para evitar quebrar scripts existentes, criar wrappers na raiz:

```
scripts/
├── audit_dashboard.py             # Wrapper existente (manter)
├── code_audit.py                  # 🆕 Wrapper → cli.audit
├── doctor.py                      # 🆕 Wrapper → cli.doctor
├── smart_git_sync.py              # 🆕 Wrapper → cli.git_sync
├── maintain_versions.py           # 🆕 Wrapper → cli.upgrade_python
└── ... (outros wrappers)
```

**Exemplo de Wrapper**:

```python
#!/usr/bin/env python3
"""[DEPRECATED] Wrapper for backward compatibility.
Use: python -m scripts.cli.doctor
"""
import sys
from scripts.cli.doctor import main

if __name__ == "__main__":
    sys.exit(main())
```

### 5.3 Pontos de Entrada no `pyproject.toml`

Adicionar console scripts para facilitar execução:

```toml
[project.scripts]
dev-doctor = "scripts.cli.doctor:main"
dev-audit = "scripts.cli.audit:main"
dev-git-sync = "scripts.cli.git_sync:main"
dev-upgrade-python = "scripts.cli.upgrade_python:main"
mock-generate = "scripts.cli.mock_generate:main"
mock-validate = "scripts.cli.mock_validate:main"
```

## 📍 7. Banner de Inicialização (Anti-Cegueira)

### 7.1 Implementação Reutilizável

Criar utilitário em `scripts/utils/banner.py`:

```python
"""Banner de inicialização para combater Cegueira de Ferramenta."""
from pathlib import Path
from datetime import datetime

def print_startup_banner(
    tool_name: str,
    version: str,
    description: str,
    script_path: Path,
    width: int = 70
) -> None:
    """Imprime banner de inicialização da ferramenta.

    Args:
        tool_name: Nome da ferramenta (ex: "Dev Doctor")
        version: Versão da ferramenta
        description: Descrição curta da ferramenta
        script_path: Path(__file__) do script
        width: Largura do banner
    """
    border = "=" * width
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{border}")
    print(f"  {tool_name} v{version}")
    print(f"  {description}")
    print(f"{border}")
    print(f"  Timestamp: {timestamp}")
    print(f"  Script:    {script_path.relative_to(Path.cwd())}")
    print(f"{border}\n")
```

### 7.2 Pontos de Injeção

Cada script CLI terá o banner injetado no `if __name__ == "__main__":`:

```python
if __name__ == "__main__":
    from scripts.utils.banner import print_startup_banner

    print_startup_banner(
        tool_name="Dev Doctor",
        version="2.0.0",
        description="Diagnóstico Preventivo de Ambiente",
        script_path=Path(__file__)
    )

    sys.exit(main())
```

### 7.3 Scripts que Receberão Banners

✅ **Ferramentas CLI** (7 scripts):

- `doctor.py`
- `code_audit.py` (audit.py)
- `smart_git_sync.py` (git_sync.py)
- `maintain_versions.py` (upgrade_python.py)
- `ci_test_mock_integration.py` (mock_ci.py)
- `test_mock_generator.py` (quando executado como CLI)
- `validate_test_mocks.py` (quando executado como CLI)

❌ **Não Receberão Banners**:

- `install_dev.py` (bootstrap silencioso)
- `integrated_audit_example.py` (exemplo/demo)
- `audit_dashboard.py` (wrapper temporário)

## ✅ 9. Checklist de Prontidão (Fase 02)

Antes de iniciar a Fase 02 (implementação), garantir:

- [x] Auditoria completa de dependências realizada
- [x] Grafo de dependências documentado
- [x] Arquitetura target definida e aprovada
- [x] Estratégia de migração documentada
- [x] Caso especial `install_dev.py` analisado
- [x] Pontos de injeção de banner identificados
- [x] Matriz de risco documentada
- [ ] Branch de feature criada (`feature/P26-scripts-refactoring`)
- [ ] Backup do workspace realizado

## 📚 Referências

- **Código Fonte**: `scripts/*.py`
- **Makefile**: Verificação de uso de `install_dev.py`
- **Pacotes Existentes**: `audit/`, `audit_dashboard/`, `git_sync/`, `ci_recovery/`
- **Padrões de DevOps**: Idempotência, Backward Compatibility, Deprecation Notices

---

**Auditoria Realizada Por**: GitHub Copilot (Claude Sonnet 4.5)
**Data de Conclusão**: 30 de Novembro de 2025
**Status Final**: ✅ Aprovado para Fase 02
