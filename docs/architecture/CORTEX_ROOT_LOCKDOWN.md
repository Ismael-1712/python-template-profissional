---
id: cortex-root-lockdown
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: [cortex, governance, documentation]
linked_code:
- scripts/core/cortex/scanner.py
- scripts/cortex/cli.py
related_docs:
- docs/architecture/CORTEX_INDICE.md
- docs/guides/CORTEX_INTROSPECTION_SYSTEM.md
title: CORTEX Root Lockdown - Proteção da Raiz do Projeto
---

# CORTEX Root Lockdown - Proteção da Raiz do Projeto

## 🎯 Objetivo

Impedir que arquivos Markdown não autorizados sejam criados na raiz do projeto, forçando
que toda documentação resida em `docs/`, mantendo a raiz limpa e organizada.

## 🔒 Política de Root Lockdown

### Allowlist de Arquivos Permitidos

Apenas os seguintes arquivos Markdown são permitidos na raiz do projeto:

- `README.md` - Documentação principal do projeto
- `CONTRIBUTING.md` - Guia de contribuição
- `CHANGELOG.md` - Histórico de mudanças
- `LICENSE` - Licença do projeto
- `SECURITY.md` - Política de segurança
- `CODE_OF_CONDUCT.md` - Código de conduta

### Regra de Violação

Qualquer outro arquivo `.md` ou `.markdown` encontrado na raiz do projeto será reportado
como **erro de auditoria** pelo comando `cortex audit`.

## 🏗️ Implementação

### 1. Constante de Allowlist

**Arquivo**: `scripts/core/cortex/scanner.py`

```python
ALLOWED_ROOT_MARKDOWN_FILES = frozenset([
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "LICENSE",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
])
```

### 2. Método de Validação

**Classe**: `CodeLinkScanner`
**Método**: `check_root_markdown_files()`

```python
def check_root_markdown_files(self) -> list[str]:
    """Validate that only approved Markdown files exist in project root.

    Returns:
        List of error messages for unauthorized .md files in root
    """
```

O método:

1. Lista todos os arquivos `.md` e `.markdown` na raiz (não recursivo)
2. Verifica se cada arquivo está na allowlist
3. Retorna lista de erros descritivos para arquivos não autorizados

### 3. Integração com `cortex audit`

**Arquivo**: `scripts/cortex/cli.py`
**Comando**: `cortex audit`

A validação é executada automaticamente no início de toda auditoria:

```python
# ROOT LOCKDOWN: Check for unauthorized .md files in root
typer.echo("🔒 Checking Root Lockdown policy...")
root_violations = scanner.check_root_markdown_files()

if root_violations:
    typer.secho(
        f"  ❌ {len(root_violations)} violation(s):",
        fg=typer.colors.RED,
    )
    # ... reporta erros
```

Os erros de Root Lockdown são:

- Contabilizados no total de erros da auditoria
- Causam falha do comando se `--fail-on-error` está ativo
- Reportados com mensagens descritivas indicando a política

## 📊 Comportamento

### Exemplo de Violação

```bash
$ cortex audit
🔒 Checking Root Lockdown policy...
  ❌ 1 violation(s):
     • File placement violation: 'lixo.md' found in project root.
       Documentation must reside in docs/, not project root.
       Allowed root files: CHANGELOG.md, CODE_OF_CONDUCT.md, ...

❌ Found 1 error(s) in 1 file(s)
```

### Exemplo de Sucesso

```bash
$ cortex audit
🔒 Checking Root Lockdown policy...
  ✅ Root Lockdown: OK

✅ All checks passed!
```

## ✅ Testes

### Teste Manual Realizado

1. **Criação de arquivo não autorizado**:

   ```bash
   echo "# Test" > lixo.md
   ```

2. **Execução da auditoria**:

   ```bash
   cortex audit
   ```

3. **Resultado**: ❌ Falha detectada corretamente
   - Arquivo `lixo.md` reportado como violação
   - Mensagem descritiva explicando a política
   - Total de erros incrementado

4. **Limpeza e re-teste**:

   ```bash
   rm lixo.md
   cortex audit
   ```

5. **Resultado**: ✅ Root Lockdown OK

## 🎨 Design Decisions

### Por que `frozenset`?

- Imutável - previne modificações acidentais
- Performance O(1) para verificação de membership
- Sinaliza intenção de constante

### Por que no `scanner.py`?

- Responsabilidade do scanner é validar estrutura de arquivos
- Mantém separação de concerns
- Reutilizável em outros contextos além do CLI

### Por que integrar no `audit`?

- Auditoria é o ponto natural de validação
- Execução automática em CI/CD
- Feedback imediato ao desenvolvedor

## 🚀 Uso em CI/CD

Para forçar conformidade em pipeline:

```yaml
- name: CORTEX Audit
  run: |
    python -m scripts.cli.cortex audit --fail-on-error
```

O comando falhará (exit code 1) se:

- Arquivos não autorizados estiverem na raiz
- Qualquer outro erro de auditoria for detectado

## 📚 Impacto no Projeto

### Limpeza Realizada

Como parte da implementação, os seguintes arquivos foram organizados:

1. `IMPLEMENTATION_SUMMARY.md` → `docs/history/sprint_2_cortex/IMPLEMENTATION_SUMMARY.md`
2. `docs/README_test_mock_system.md` → `docs/guides/MOCK_SYSTEM.md`

Ambos os arquivos receberam frontmatter YAML para conformidade com CORTEX.

### Prevenção Futura

O sistema agora impede automaticamente:

- Criação acidental de docs na raiz
- Proliferação de arquivos README secundários
- Documentação dispersa fora de `docs/`

## 🔄 Manutenção

### Para Adicionar Arquivo à Allowlist

Edite `scripts/core/cortex/scanner.py`:

```python
ALLOWED_ROOT_MARKDOWN_FILES = frozenset([
    "README.md",
    "CONTRIBUTING.md",
    # ... arquivos existentes ...
    "NOVO_ARQUIVO.md",  # Adicionar aqui
])
```

**Critério**: Apenas arquivos de documentação de **alto nível** e **essenciais**
para a raiz do projeto devem ser permitidos.

## 📖 Referências

- Princípio de "Documentation as Code" do CORTEX
- SRE Best Practices: Automated Governance
- [CORTEX Índice](../architecture/CORTEX_INDICE.md)
- [Sistema de Introspecção](../guides/CORTEX_INTROSPECTION_SYSTEM.md)

---

**Status**: ✅ Implementado e testado
**Data**: 2025-12-01
**Versão CORTEX**: 0.1.0
