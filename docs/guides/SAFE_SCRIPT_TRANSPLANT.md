---
id: safe-script-transplant
type: guide
status: active
version: 1.0.0
author: Prof. de TI & Ismael Tavares
date: '2025-12-16'
tags: [legacy, migration, security, sre]
context_tags: [best-practice, risk-management]
linked_code:
  - scripts/cli/audit.py
  - scripts/cli/git_sync.py
title: 'Transplante Seguro de Scripts Legados - Metodologia de Migração SRE'
---

# Transplante Seguro de Scripts Legados - Metodologia de Migração SRE

## Status

**Active** - Metodologia validada durante migração de 8 scripts legados (Nov 2025)

## Contexto Histórico

Durante a evolução do projeto (v1.5 → v2.0), enfrentamos o desafio de migrar 8 scripts Python de um projeto descontinuado (`nota-obsidian`) para o template profissional. Estes scripts continham **conceitos valiosos** (auditoria de código, sincronização Git, geração de mocks), mas eram:

- ❌ **Inseguros**: Uso de `shell=True`, `os.system()`, execução de código não-sanitizado
- ❌ **Quebrados**: Dependências ausentes, imports falhando
- ❌ **Instáveis**: Bugs de ambiente (`python` vs `python3`, paths hardcoded)
- ❌ **Não-Testados**: Zero cobertura de testes

**Dilema**: Como extrair o conhecimento sem importar os bugs?

## Metodologia: O "Transplante Seguro"

Desenvolvemos um processo de 4 etapas inspirado em práticas de SRE e migração de sistemas críticos.

### Metáfora Médica

```
┌───────────────────────────────────────────────────┐
│  PACIENTE (Script Legado)                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  - Órgão útil: Lógica de auditoria               │
│  - Doença: Código inseguro                        │
│  - Vírus: Dependências quebradas                  │
└─────────────┬─────────────────────────────────────┘
              │
              │ (1) QUARENTENA
              ▼
┌───────────────────────────────────────────────────┐
│  SALA DE ISOLAMENTO (Análise Estática)           │
│  - Executar AST parsing (sem executar código)    │
│  - Identificar padrões inseguros                  │
│  - Extrair "DNA" (conceitos)                      │
└─────────────┬─────────────────────────────────────┘
              │
              │ (2) TRIAGEM
              ▼
┌───────────────────────────────────────────────────┐
│  COMITÊ DE AUDITORIA (IA + Humano)               │
│  - Classificar: GENÉRICO vs LIXO                 │
│  - Validar conceito: "É útil?"                    │
│  - Decidir: Reescrever ou descartar?             │
└─────────────┬─────────────────────────────────────┘
              │
              │ (3) TRANSPLANTE
              ▼
┌───────────────────────────────────────────────────┐
│  NOVO ÓRGÃO (Script Reescrito)                   │
│  - Código limpo (ruff, mypy compliant)           │
│  - Seguro (sem shell=True, sanitização)          │
│  - Testado (pytest, 80%+ cobertura)              │
└───────────────────────────────────────────────────┘
```

## Processo Detalhado

### Etapa 1: Quarentena (Isolamento do Risco)

**Objetivo**: Analisar o script legado **sem executá-lo**.

#### 1.1. Criação da Zona de Quarentena

```bash
# NUNCA adicione scripts legados diretamente ao projeto principal
mkdir -p /tmp/legacy_quarantine
cp projeto-antigo/scripts/*.py /tmp/legacy_quarantine/
```

#### 1.2. Análise Estática (AST Parsing)

Use ferramentas que **não executam** o código:

```bash
# Análise de segurança
bandit -r /tmp/legacy_quarantine/ -f json -o audit_legacy.json

# Análise de qualidade
ruff check /tmp/legacy_quarantine/ --output-format json > ruff_legacy.json

# Detecção de padrões perigosos
grep -r "shell=True\|os.system\|eval\|exec" /tmp/legacy_quarantine/
```

**Output Esperado**:

```json
{
  "results": [
    {
      "filename": "copilot_audit.py",
      "issue_text": "subprocess call with shell=True",
      "line_number": 42,
      "severity": "HIGH"
    }
  ]
}
```

#### 1.3. Extração de Conceitos (Leitura Humana)

**NUNCA execute o script**. Leia o código para entender **o que ele faz**:

```python
# Exemplo: legacy/smart_sync_command.py

def sync_to_remote(branch: str):
    """
    CONCEITO IDENTIFICADO:
    - Workflow de push seguro
    - Validação de branch antes de push
    - Execução de testes pré-push

    IMPLEMENTAÇÃO PROBLEMÁTICA:
    - Usa subprocess.run(shell=True)  ❌
    - Path hardcoded: /home/user/...  ❌
    - Sem tratamento de erro          ❌
    """
    cmd = f"git push origin {branch}"  # Injeção de comando!
    os.system(cmd)  # INSEGURO
```

**Resultado da Extração**:

- 💡 **Conceito Válido**: "Workflow de push com validação pré-push"
- ❌ **Implementação Inválida**: Código inseguro e frágil

### Etapa 2: Triagem (Classificação de Valor)

**Objetivo**: Decidir se o conceito merece ser reimplementado.

#### Critérios de Classificação

| Classificação | Critério | Ação |
|---------------|----------|------|
| **GENÉRICO** | Conceito aplicável a **qualquer** projeto Python | ✅ Reescrever |
| **ESPECÍFICO** | Conceito útil **apenas** no contexto do projeto antigo | ⚠️ Adaptar ou descartar |
| **LIXO** | Código obsoleto, workaround temporário ou duplicado | ❌ Descartar |

#### Exemplo de Triagem Real (Scripts do Relatório v2.0)

| Script Legado | Conceito | Classificação | Decisão |
|---------------|----------|---------------|---------|
| `copilot_audit.py` | Auditoria de segurança em código Python | GENÉRICO | ✅ Reescrever como `scripts/cli/audit.py` |
| `smart_sync_command.py` | Workflow Git com validação pré-push | GENÉRICO | ✅ Reescrever como `scripts/cli/git_sync.py` |
| `test_mock_generator.py` | Geração de mocks via AST | GENÉRICO | ✅ Reescrever (mesmo nome) |
| `nota_obsidian_sync.py` | Sincronização com Obsidian Vault | ESPECÍFICO | ❌ Descartar (não aplicável) |
| `temp_debug_helper.py` | Helper temporário para debug | LIXO | ❌ Descartar |

**Resultado**: 5 scripts classificados como GENÉRICO foram reimplementados. 3 descartados.

### Etapa 3: Transplante (Reescrita Segura)

**Objetivo**: Reimplementar o conceito do zero, seguindo padrões SRE.

#### 3.1. Comitê de Auditoria (Pair Programming: IA + Humano)

**Arquitetura de Reescrita**:

1. **Humano**: Define requisitos funcionais do conceito

   ```
   "Preciso de um script que audite código Python em busca de:
   - subprocess.run(shell=True)
   - Uso de eval() ou exec()
   - Imports de bibliotecas perigosas

   Requisitos não-funcionais:
   - Código type-safe (mypy strict)
   - Configuração via YAML
   - Saída em JSON/YAML
   - Testável (pytest)
   ```

2. **IA** (Copilot/ChatGPT): Gera implementação inicial

3. **Humano**: Revisa criticamente:
   - ✅ Verifica que não reproduziu os bugs do legado
   - ✅ Valida tratamento de erros
   - ✅ Adiciona testes

#### 3.2. Checklist de Segurança (Pré-Merge)

**Antes de adicionar o script reescrito ao projeto, validar:**

- [ ] **Zero `shell=True`**: Pesquisar `grep -r "shell=True" scripts/`
- [ ] **Sanitização de Inputs**: Argumentos de usuário são validados?
- [ ] **Paths Relativos**: Nenhum path hardcoded (`/home/user/...`)
- [ ] **Tratamento de Erros**: Todos os `subprocess.run` tem `try/except`?
- [ ] **Type Safety**: `mypy --strict` passa?
- [ ] **Testes**: Cobertura > 70% do código crítico?

#### 3.3. Exemplo de Reescrita

**Antes (Legado Inseguro)**:

```python
# legacy/copilot_audit.py (INSEGURO)
import os

def audit_file(filename):
    os.system(f"grep -r 'shell=True' {filename}")  # ❌ Injeção de comando
```

**Depois (Reescrito Seguro)**:

```python
# scripts/cli/audit.py (SEGURO)
import subprocess
from pathlib import Path

def audit_file(filepath: Path) -> list[str]:
    """Audita arquivo Python em busca de padrões inseguros.

    Args:
        filepath: Caminho do arquivo (validado)

    Returns:
        Lista de issues encontrados

    Raises:
        FileNotFoundError: Se arquivo não existir
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    # ✅ Seguro: sem shell=True, lista de argumentos
    result = subprocess.run(
        ["grep", "-n", "shell=True", str(filepath)],
        capture_output=True,
        text=True,
        check=False,  # Não falha se grep não encontrar matches
    )

    return result.stdout.splitlines()
```

**Diferenças Críticas**:

- ✅ **Type hints** (`Path`, `list[str]`)
- ✅ **Validação** (check `filepath.exists()`)
- ✅ **Segurança** (argumentos de lista, não string)
- ✅ **Tratamento de erro** (exceções explícitas)
- ✅ **Documentação** (docstring)

### Etapa 4: Validação (Teste de Aceitação)

**Objetivo**: Provar que o novo script funciona **melhor** que o legado.

#### 4.1. Testes Comparativos

```bash
# Cenário: Auditar um arquivo de teste
$ cat test_sample.py
import subprocess
subprocess.run("ls", shell=True)  # Código inseguro

# Executar script reescrito
$ python scripts/cli/audit.py test_sample.py
[
  {
    "file": "test_sample.py",
    "line": 2,
    "issue": "shell=True detected",
    "severity": "HIGH"
  }
]
✅ SUCESSO: Detectou o problema

# Executar script legado (em quarentena)
$ python /tmp/legacy_quarantine/copilot_audit.py test_sample.py
Traceback (most recent call last):
  ...
ModuleNotFoundError: No module named 'old_dependency'
❌ FALHA: Dependência ausente
```

#### 4.2. Auditoria de Regressão

**Garantir que o novo script não introduziu novos bugs**:

```bash
# Executar suite de testes
$ pytest tests/test_audit.py -v
test_audit_detects_shell_true ...................... PASSED
test_audit_handles_missing_file .................... PASSED
test_audit_sanitizes_user_input .................... PASSED
test_audit_runs_without_network .................... PASSED  # ✅ Importante

================================ 4 passed in 0.5s ================================
```

## Lições Aprendidas (Casos Reais)

### ✅ Sucesso: `test_mock_generator.py`

**Conceito Legado**: Gerar mocks de teste via parsing AST.

**Problema do Legado**: Código funcionava, mas era extremamente frágil (quebrava com Python 3.11+).

**Transplante**:

1. **Conceito Preservado**: Usar `ast.parse()` para analisar código
2. **Implementação Modernizada**:
   - Adicionado suporte a `match/case` (Python 3.10+)
   - Type hints completos
   - Configuração via YAML (antes era hardcoded)
   - Testes automatizados (antes não existiam)

**Resultado**: Script 3x mais robusto que o original.

### ⚠️ Lição: `ci_failure_recovery.py`

**Conceito Legado**: Recuperação automática de falhas de CI.

**Problema da Reescrita Inicial**: A IA gerou um **monólito de 700+ linhas** que violava SOLID (Single Responsibility Principle).

**Lição Aprendida**:

- ✅ **Humano deve revisar SEMPRE**: IA pode reintroduzir anti-patterns
- ✅ **Débito Técnico é OK**: Aceitamos o monólito temporariamente e criamos um ticket de refatoração (Prioridade 2 do Roadmap v2.0)

### ❌ Falha Evitada: `nota_obsidian_sync.py`

**Conceito Legado**: Sincronizar notas Markdown com Obsidian Vault.

**Tentação**: "Esse conceito pode ser útil para syncar documentação do projeto!"

**Decisão Correta**: Classificar como **ESPECÍFICO** e descartar.

**Razão**: O conceito era muito acoplado ao workflow pessoal do projeto antigo. Reimplementar custaria 10h para benefício marginal.

## Indicadores de Sucesso

Após a migração dos 8 scripts legados (Nov 2025):

- ✅ **8.000+ linhas** de código SRE adicionadas ao template
- ✅ **Zero vulnerabilidades** de segurança (`bandit` passou 100%)
- ✅ **80%+ cobertura** de testes nos scripts críticos
- ✅ **100% type-safe** (`mypy --strict` em todos os scripts)
- ✅ **Zero dependências quebradas** (instalação funciona em qualquer ambiente)

## Quando Usar Este Processo

### ✅ Use "Transplante Seguro" quando

- Migrando scripts de projetos descontinuados
- Integrando ferramentas de desenvolvedores externos (ex: GitHub Gist)
- Adotando código de exemplos de tutoriais (que podem ser desatualizados)

### ❌ Não use quando

- Código já está em um repositório profissional e auditado
- Código é de biblioteca oficial (ex: do PyPI)
- Código é trivial (<50 linhas) e você pode reescrever em 10 minutos

## Ferramentas Recomendadas

| Ferramenta | Propósito | Comando |
|------------|-----------|---------|
| `bandit` | Análise de segurança | `bandit -r path/to/legacy/ -f json` |
| `ruff` | Análise de qualidade | `ruff check path/to/legacy/` |
| `mypy` | Análise de tipos | `mypy --strict path/to/new_script.py` |
| `pytest` | Testes | `pytest tests/test_new_script.py -v` |
| `grep` | Busca de padrões | `grep -r "shell=True" .` |

## Referências

- [Relatório de Evolução v2.0](../history/EVOLUTION_REPORT_V2.md) - Origem desta metodologia
- [Scripts Migrados](../../scripts/cli/) - Resultado final do transplante
- [Código: audit.py](../../scripts/cli/audit.py) - Exemplo de script reescrito
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

---

**Autor**: Prof. de TI & Ismael Tavares
**Validado em**: Nov 2025 (Migração de 8 scripts legados)
**Última Atualização**: 2025-12-16
**Status**: Active (metodologia comprovada)
