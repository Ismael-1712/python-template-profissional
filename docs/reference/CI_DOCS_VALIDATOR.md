---
title: CI Documentation Validator Guide
description: Technical reference for the CI/CD documentation validation system
version: 1.0.0
id: ref-003
status: active
type: reference
author: Ismael-1712
date: 2025-12-13
tags: [ci, documentation, automation, github-actions]
---
# CI Documentation Validator

## Visão Geral

O `scripts/ci/check_docs.py` é um validador de documentação para pipelines CI/CD que garante que a documentação CLI esteja sempre sincronizada com o código.

## Características

- ✅ **Validação in-memory**: Gera documentação sem modificar arquivos
- 🔄 **Normalização inteligente**: Ignora timestamps e outras mudanças esperadas
- 📊 **Diff detalhado**: Mostra exatamente o que mudou quando a validação falha
- 🎯 **Exit codes apropriados**: Integração perfeita com CI/CD
- 🚀 **Rápido**: Validação em segundos

## Uso

### Execução Local

```bash
# Validar documentação
python scripts/ci/check_docs.py

# Saída esperada se OK:
# ✅ Documentation is up-to-date.
# Exit code: 0

# Saída esperada se desatualizada:
# ❌ Documentation is outdated!
# [mostra diff]
# Exit code: 1
```

### Integração CI/CD

#### GitHub Actions

Adicione ao seu workflow `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  validate-docs:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements/dev.txt

      - name: Validate CLI Documentation
        run: |
          python scripts/ci/check_docs.py
```

#### GitLab CI

Adicione ao seu `.gitlab-ci.yml`:

```yaml
validate-docs:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements/dev.txt
    - python scripts/ci/check_docs.py
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
```

#### Azure Pipelines

Adicione ao seu `azure-pipelines.yml`:

```yaml
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'

- script: |
    pip install -r requirements/dev.txt
    python scripts/ci/check_docs.py
  displayName: 'Validate CLI Documentation'
```

## Como Funciona

### 1. Geração In-Memory

O script instancia `CLIDocGenerator` e gera a documentação completa em memória usando `generator.generate_documentation()`, **sem** chamar `write_documentation()`.

### 2. Leitura do Arquivo Comprometido

Lê o conteúdo atual de `docs/reference/CLI_COMMANDS.md` do repositório.

### 3. Normalização

Antes de comparar, ambas as versões passam pela função `normalize_content()` que:

- Remove/substitui timestamps variáveis por placeholders fixos
- Normaliza whitespace quando apropriado
- Garante que apenas mudanças **reais** causem falha

Padrões normalizados:

- `Gerado em: **2024-12-13 20:30 UTC**` → `Gerado em: **TIMESTAMP**`
- `**Última Atualização:** 2024-12-13 20:30 UTC` → `**Última Atualização:** TIMESTAMP`
- `> Generated at: ...` → `> Generated at: TIMESTAMP`

### 4. Comparação

Compara o conteúdo normalizado. Se idênticos: ✅ sucesso. Se diferentes: ❌ falha.

### 5. Output e Exit Codes

| Cenário | Output | Exit Code |
|---------|--------|-----------|
| Documentação atualizada | `✅ Documentation is up-to-date.` | 0 |
| Documentação desatualizada | `❌ Documentation is outdated!` + diff | 1 |
| Arquivo não existe | `❌ Documentation file not found!` | 1 |
| Erro de importação | `❌ Import Error: ...` | 1 |
| Outro erro | `❌ Validation failed with error: ...` | 1 |

## Correção de Documentação Desatualizada

Quando o CI falhar com documentação desatualizada:

```bash
# 1. Gerar documentação atualizada
python scripts/core/doc_gen.py

# 2. Revisar mudanças
git diff docs/reference/CLI_COMMANDS.md

# 3. Commitar se correto
git add docs/reference/CLI_COMMANDS.md
git commit -m "docs: update CLI commands reference"

# 4. Push
git push
```

## Troubleshooting

### "Import Error" no CI

**Problema**: Dependências não instaladas no ambiente CI.

**Solução**:

```yaml
- name: Install dependencies
  run: pip install -r requirements/dev.txt
```

### Falha por Whitespace

**Problema**: Diff mostra apenas mudanças de espaços em branco.

**Possível causa**: Editor configurado para remover trailing whitespace.

**Solução**: Regenere a documentação com `python scripts/core/doc_gen.py`.

### Timestamps Causando Falha

**Problema**: Normalização não está capturando todos os formatos de timestamp.

**Solução**: Verifique o padrão regex em `normalize_content()` e adicione novos padrões se necessário.

## Arquitetura

```
scripts/ci/check_docs.py
├── validate_documentation()
│   ├── Lê docs/reference/CLI_COMMANDS.md
│   ├── Gera documentação (CLIDocGenerator)
│   ├── Normaliza ambas as versões
│   ├── Compara conteúdo
│   └── Retorna exit code
├── normalize_content()
│   └── Remove/substitui elementos voláteis
└── show_diff()
    └── Exibe unified diff quando há divergência
```

## Dependências

- **Python 3.11+**
- **scripts.core.doc_gen**: Gerador de documentação
- **difflib**: Comparação de texto (stdlib)
- **re**: Regex para normalização (stdlib)
- **pathlib**: Manipulação de paths (stdlib)

## Manutenção

### Adicionar Novos Padrões de Normalização

Se novos elementos voláteis forem adicionados à documentação:

```python
def normalize_content(content: str) -> str:
    # ... código existente ...

    # Adicione novo padrão aqui
    if "novo_elemento_volatil:" in line.lower():
        line = re.sub(r'padrão_regex', 'PLACEHOLDER', line)
```

### Atualizar Mensagens de Ajuda

As mensagens de erro incluem instruções de correção. Atualize-as em `validate_documentation()` se o processo mudar.

## Boas Práticas

1. ✅ **Execute localmente antes de commitar**: `python scripts/ci/check_docs.py`
2. ✅ **Integre com pre-commit hook** (opcional):

   ```yaml
   - repo: local
     hooks:
       - id: check-docs
         name: Validate CLI Documentation
         entry: python scripts/ci/check_docs.py
         language: system
         pass_filenames: false
   ```

3. ✅ **Documente mudanças de CLI**: Sempre que modificar comandos CLI, lembre de regenerar docs
4. ✅ **Monitore falhas no CI**: Documentação desatualizada é um problema de qualidade

## Versionamento

**Versão Atual**: 1.0.0

### Changelog

- **1.0.0** (2024-12-13): Release inicial
  - Validação in-memory
  - Normalização de timestamps
  - Unified diff output
  - Integração CI/CD

---

**Autor**: DevOps Engineering Team
**Licença**: MIT
**Manutenção**: Auto-gerenciado
