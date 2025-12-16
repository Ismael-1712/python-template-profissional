---
id: roadmap-delta-audit-optimization
type: arch
status: draft
version: 1.0.0
author: Prof. de TI & Ismael Tavares
date: '2025-12-16'
tags: [pre-commit, optimization, delta-audit, roadmap]
context_tags: [future-work, performance]
linked_code:
  - scripts/cli/audit.py
title: 'Roadmap: Delta Audit - Pre-Commit Inteligente (Apenas Arquivos Staged)'
---

# Roadmap: Delta Audit - Pre-Commit Inteligente (Apenas Arquivos Staged)

## Status

**Proposed** - Identificado como Prioridade 4 (Média-Alta) no Relatório de Evolução v2.0

## Problema Atual

Nosso hook `pre-commit` de auditoria de segurança é **seguro**, mas **ineficiente**:

```yaml
# .pre-commit-config.yaml (atual)
- id: code-audit-security
  name: Code Security Audit
  entry: env PRE_COMMIT=1 python3 scripts/cli/audit.py
  language: system
  pass_filenames: false  # ❌ Ignora arquivos modificados
  always_run: true       # ❌ Re-escaneia TODO o projeto
```

**Comportamento Atual**:

1. Desenvolvedor modifica `src/api/routes.py`
2. Executa `git commit`
3. Hook `pre-commit` executa `audit.py`
4. **Problema**: `audit.py` re-escaneia **TODOS** os arquivos em `src/`, `tests/`, `scripts/` (definidos em `audit_config.yaml`)
5. Resultado: 5-10 segundos de auditoria mesmo para um único arquivo modificado

**Impacto**:

- 🟡 **DX Degradado**: Commits demoram mais do que deveriam
- 🟡 **Desperdício de CPU**: Re-auditoria de código que não mudou
- 🟡 **Escalabilidade**: Projetos grandes (10k+ linhas) terão hooks extremamente lentos

## Solução Proposta: "Delta Audit"

Implementar auditoria **incremental** que escaneia **apenas** os arquivos Python modificados (staged).

### Arquitetura Proposta

```
┌──────────────────────────────────────────────────────┐
│  PRE-COMMIT HOOK                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  .pre-commit-config.yaml                             │
│                                                       │
│  - id: code-audit-security                           │
│    entry: python3 scripts/cli/audit.py --delta      │
│    pass_filenames: true   ◄── MUDANÇA CHAVE          │
│                                                       │
└──────────────┬───────────────────────────────────────┘
               │
               │ (1) Lista de arquivos staged (.py)
               ▼
┌──────────────────────────────────────────────────────┐
│  AUDIT.PY (Modificado)                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                       │
│  if args.delta:                                      │
│      # (2) Usar lista de arquivos recebidos         │
│      files_to_scan = sys.argv[1:]  # Staged files   │
│  else:                                               │
│      # (3) Comportamento padrão (escanear tudo)     │
│      files_to_scan = get_files_from_config()        │
│                                                       │
│  # (4) Auditar APENAS os arquivos relevantes        │
│  for file in files_to_scan:                          │
│      run_security_checks(file)                       │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### Fluxo de Dados (Delta Audit)

```bash
# Estado inicial: Desenvolvedor modifica 2 arquivos
$ git status
modified:   src/api/routes.py
modified:   tests/test_routes.py

# Adiciona ao stage
$ git add src/api/routes.py tests/test_routes.py

# Executa commit
$ git commit -m "feat: add new route"

# Pre-commit intercepta e passa arquivos staged
$ pre-commit run code-audit-security
# Internamente executa:
# python3 scripts/cli/audit.py --delta src/api/routes.py tests/test_routes.py

# ✅ Auditoria RÁPIDA (apenas 2 arquivos, não 50+)
```

## Implementação Detalhada

### Passo 1: Modificar `.pre-commit-config.yaml`

```yaml
# .pre-commit-config.yaml (nova versão)
repos:
  - repo: local
    hooks:
      - id: code-audit-security
        name: Code Security Audit (Delta)
        entry: python3 scripts/cli/audit.py --delta
        language: system
        types: [python]           # ✅ NOVO: Filtra apenas .py
        pass_filenames: true      # ✅ NOVO: Passa arquivos staged
        # always_run: false       # ✅ NOVO: Roda apenas se há .py modificados
```

**Mudanças Chave**:

- `pass_filenames: true`: Pre-commit passa lista de arquivos staged como argumentos
- `types: [python]`: Filtra apenas arquivos `.py` (ignora `.md`, `.yaml`, etc.)
- Remove `always_run: true`: Hook só executa se houver arquivos Python modificados

### Passo 2: Modificar `scripts/cli/audit.py`

#### Adicionar Flag `--delta`

```python
# scripts/cli/audit.py

import argparse
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--delta",
        action="store_true",
        help="Delta mode: audit only files passed as arguments (for pre-commit)"
    )
    parser.add_argument(
        "files",
        nargs="*",  # Aceita zero ou mais arquivos
        help="Files to audit (only used with --delta)"
    )
    args = parser.parse_args()

    # LÓGICA DE SELEÇÃO DE ARQUIVOS
    if args.delta:
        # Modo Delta: usar arquivos recebidos do pre-commit
        if not args.files:
            logger.info("No Python files staged. Skipping audit.")
            sys.exit(0)
        files_to_scan = args.files
        logger.info(f"Delta Audit: Scanning {len(files_to_scan)} staged files")
    else:
        # Modo Completo: usar scan_paths do audit_config.yaml
        config = load_config("scripts/audit_config.yaml")
        files_to_scan = discover_files(config["scan_paths"])
        logger.info(f"Full Audit: Scanning {len(files_to_scan)} files")

    # EXECUTAR AUDITORIA (código existente)
    results = run_audit(files_to_scan)
    # ...
```

#### Lógica de Descoberta

```python
def discover_files(scan_paths: list[str]) -> list[str]:
    """Descobre arquivos Python em diretórios configurados.

    Args:
        scan_paths: Lista de diretórios (ex: ["src/", "tests/"])

    Returns:
        Lista de caminhos absolutos de arquivos .py
    """
    files = []
    for path in scan_paths:
        if Path(path).is_file():
            files.append(path)
        elif Path(path).is_dir():
            files.extend(Path(path).rglob("*.py"))
    return [str(f) for f in files]
```

### Passo 3: Preservar Compatibilidade

**Requisito Crítico**: O `audit.py` deve continuar funcionando em **modo completo** quando executado manualmente ou no CI.

```bash
# Modo Delta (pre-commit)
$ python scripts/cli/audit.py --delta src/api/routes.py
# ✅ Escaneia apenas routes.py

# Modo Completo (manual)
$ python scripts/cli/audit.py
# ✅ Escaneia todos os arquivos em audit_config.yaml

# Modo Completo (CI)
$ make audit
# ✅ Escaneia tudo (como antes)
```

## Benefícios Esperados

### Performance

| Cenário | Antes (Full Scan) | Depois (Delta) | Ganho |
|---------|-------------------|----------------|-------|
| 1 arquivo modificado | ~8s | ~1s | **8x** |
| 5 arquivos modificados | ~8s | ~2s | **4x** |
| 50 arquivos modificados | ~8s | ~8s | 1x (degrada gracefully) |

**Nota**: Para commits massivos (50+ arquivos), o delta se aproxima do full scan, o que é esperado.

### Developer Experience

- ✅ **Commits Rápidos**: 90% dos commits tocam 1-5 arquivos (benefício 4-8x)
- ✅ **Feedback Imediato**: Auditoria rápida = loop de desenvolvimento mais ágil
- ✅ **Escalabilidade**: Projetos grandes não degradam o DX

## Riscos e Mitigações

### Risco 1: Arquivos Não-Staged Não São Auditados

**Cenário**:

```bash
vim src/api/dangerous.py  # Adiciona código inseguro
git add src/api/safe.py   # Adiciona outro arquivo
git commit                # Hook audita apenas safe.py, ignora dangerous.py
```

**Mitigação**:

1. **CI como Rede de Segurança**: O CI **sempre** executa `make audit` (full scan)
2. **Educação**: Desenvolvedores devem executar `git add .` ou `make audit` localmente antes de push

### Risco 2: Falsos Negativos em Dependências

**Cenário**: Arquivo A importa arquivo B (inseguro). Se apenas A é modificado, B não é auditado.

**Mitigação**:

1. **Static Analysis Avançado**: Ferramentas como `bandit` auditam imports automaticamente
2. **CI Full Scan**: Garante que nada escapa

## Roadmap de Implementação

### Fase 1: Prova de Conceito (1-2h)

- [ ] Criar branch `feat/delta-audit`
- [ ] Modificar `audit.py` (adicionar flag `--delta`)
- [ ] Testar localmente com `git commit` em arquivos únicos

### Fase 2: Validação (2-4h)

- [ ] Escrever testes automatizados (`test_audit_delta.py`)
  - Testar com 1 arquivo staged
  - Testar com 10 arquivos staged
  - Testar com 0 arquivos staged (skip)
- [ ] Verificar compatibilidade com `make audit` (full scan)

### Fase 3: Deploy (1h)

- [ ] Atualizar `.pre-commit-config.yaml`
- [ ] Atualizar documentação (`docs/architecture/ADR_002_PRE_COMMIT_OPTIMIZATION.md`)
- [ ] Merge para `main`

**Tempo Estimado Total**: 4-7 horas de trabalho

## Alternativas Consideradas

### Alternativa 1: Cache de Resultados

**Ideia**: Cachear resultados de auditoria por arquivo e re-usar se o arquivo não mudou.

**Rejeição**: Complexidade alta (gerenciamento de cache, invalidação) para ganho marginal.

### Alternativa 2: Auditoria Paralela

**Ideia**: Executar auditoria de múltiplos arquivos em paralelo (multithreading).

**Rejeição**: Ganho de 2-3x, mas delta audit entrega 8x com menos complexidade.

## Métricas de Sucesso

- 🎯 **P90 Commit Time**: Reduzir de 8s para 2s (75% de redução)
- 🎯 **Adoção**: 0% de commits com `--no-verify` (indica que o hook não é "chato")
- 🎯 **Cobertura de Segurança**: 100% (CI ainda executa full scan)

## Referências

- [Código: audit.py](../../scripts/cli/audit.py)
- [Código: .pre-commit-config.yaml](../../.pre-commit-config.yaml)
- [ADR 002: Pre-Commit Optimization](./ADR_002_PRE_COMMIT_OPTIMIZATION.md) - Decisão anterior de otimização de hooks
- [Relatório de Evolução v2.0](../history/EVOLUTION_REPORT_V2.md) - Origem desta prioridade

---

**Autor**: Prof. de TI & Ismael Tavares
**Prioridade**: Média-Alta (P4 do Roadmap v2.0)
**Esforço Estimado**: 4-7 horas
**Última Atualização**: 2025-12-16
