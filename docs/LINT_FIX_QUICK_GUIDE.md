# Sistema de Correção Automática de Linting

## Visão Geral

O `lint_fix.py` é um script **genérico** e **seguro** para correção automática de problemas comuns de linting em projetos Python.

## Características

- **Seguro:** Backups automáticos + modo dry-run
- **Idempotente:** Pode rodar múltiplas vezes sem problemas
- **Genérico:** Funciona em qualquer projeto Python
- **Configurável:** Lê `pyproject.toml` automaticamente

## Uso Básico

```bash
# Simular correções (recomendado primeiro)
python3 scripts/lint_fix.py --dry-run

# Aplicar correções
python3 scripts/lint_fix.py

# Aplicar e commitar automaticamente
python3 scripts/lint_fix.py --auto-commit
```

## Uso Avançado

```bash
# Processar diretórios específicos
python3 scripts/lint_fix.py src/ tests/

# Modo verboso
python3 scripts/lint_fix.py --verbose --dry-run

# Correção de emergência com commit
python3 scripts/lint_fix.py --auto-commit src/
```

## Estratégias de Correção

1. **Strings longas:** Quebra automaticamente strings que excedem limite
2. **Expressões longas:** Quebra em vírgulas e operadores
3. **Formatação:** Aplica `ruff format` automaticamente

## Configuração

O script lê automaticamente configurações do `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
```

## Integração CI/CD

```yaml
# GitHub Actions
- name: Fix lint issues
  run: |
    python3 scripts/lint_fix.py --dry-run
    python3 scripts/lint_fix.py --auto-commit
```

## Casos de Uso

### Correção de Emergência

```bash
# CI/CD falhando por linting
python3 scripts/lint_fix.py --auto-commit
```

### Auditoria Preventiva

```bash
# Verificar problemas antes do commit
python3 scripts/lint_fix.py --dry-run --verbose
```

## Vantagens

| Aspecto | Script Original | Nova Implementação |
|---------|----------------|-------------------|
| Segurança | ❌ Commits sem confirmação | ✅ Backups + dry-run |
| Portabilidade | ❌ Hardcoded específico | ✅ Genérico |
| Robustez | ❌ Sem tratamento de erros | ✅ Timeouts + validações |
| Idempotência | ❌ Aplica múltiplas vezes | ✅ Detecta já aplicadas |

## Exemplo de Saída

```
14:30:15 - INFO - 🚨 SISTEMA DE CORREÇÃO AUTOMÁTICA DE LINTING
14:30:15 - INFO - 📁 Projeto: python-template-profissional
14:30:15 - INFO - 📏 Linha máxima: 88 chars
14:30:15 - INFO - 📁 Encontrados 15 arquivos Python
14:30:15 - INFO - ✅ Fixed 3 long lines in utils.py
14:30:15 - INFO - ✅ Formatação automática concluída
14:30:15 - INFO - ✅ Todos os problemas de linting foram resolvidos!
```

## Evolução Futura

Este script **genérico** pode ser expandido para templates específicos:

- **python-template-api:** Correções específicas para FastAPI/Flask
- **python-template-cli:** Formatação de argumentos de CLI
- **python-template-lib:** Docstrings e type hints complexos

---

**Status:** ✅ Pronto para produção
**Branch:** `main` (genérico)
**Compatibilidade:** Python 3.10+ | Linux/macOS/Windows
**Dependências:** `ruff` (opcional)
