# Sistema de Correção Automática de Linting

## Visão Geral

O `lint_fix.py` é um script **genérico** e **seguro** para correção automática de problemas comuns de linting em projetos Python. Ele substitui scripts específicos por uma solução robusta e reutilizável.

## Características Principais

### 🔒 Segurança

- **Backups automáticos** antes de qualquer modificação
- **Modo dry-run** para simular mudanças
- **Timeout de segurança** em operações subprocess
- **Validação de caminhos** antes de processar

### 🔄 Idempotência

- Pode ser executado múltiplas vezes sem problemas
- Detecta se correções já foram aplicadas
- Não duplica correções existentes

### 🌍 Portabilidade

- Funciona em qualquer projeto Python
- Detecta configurações automaticamente (`pyproject.toml`)
- Não depende de estruturas de projeto específicas
- Compatível com POSIX (Linux/macOS/WSL)

### ⚙️ Configurabilidade

- Lê configurações do `pyproject.toml`
- Arquivo de configuração opcional (`lint_fix.toml`)
- Estratégias de correção modulares
- Caminhos customizáveis

## Uso

### Básico

```bash
# Modo interativo (padrão)
python3 scripts/lint_fix.py

# Simular correções (recomendado primeiro)
python3 scripts/lint_fix.py --dry-run

# Aplicar e commitar automaticamente
python3 scripts/lint_fix.py --auto-commit
```

### Avançado

```bash
# Processar apenas diretórios específicos
python3 scripts/lint_fix.py src/ tests/

# Modo verboso com dry-run
python3 scripts/lint_fix.py --dry-run --verbose

# Correção de emergência com commit automático
python3 scripts/lint_fix.py --auto-commit src/
```

## Estratégias de Correção

### 1. **Correção de Strings Longas**

```python
# Antes (linha longa)
error_msg = f"Erro ao processar arquivo {file_path} na linha {line_num} com conteúdo {content}"

# Depois (quebrada automaticamente)
error_msg = f"Erro ao processar arquivo {file_path} na linha {line_num} " \
            f"com conteúdo {content}"
```

### 2. **Quebra de Expressões**

```python
# Antes
result = some_very_long_function_name(param1, param2, param3, param4, param5)

# Depois
result = some_very_long_function_name(
    param1, param2, param3,
    param4, param5
)
```

### 3. **Formatação Automática**

- Aplica `ruff format` automaticamente
- Respeita configurações existentes do projeto
- Mantém estilo consistente

## Configuração

### Via `pyproject.toml` (Recomendado)

```toml
[tool.ruff]
line-length = 88

[tool.black]
line-length = 88
```

## Integração CI/CD

### GitHub Actions

```yaml
- name: Fix lint issues automatically
  run: |
    python3 scripts/lint_fix.py --dry-run --verbose
    if [ $? -eq 0 ]; then
      python3 scripts/lint_fix.py --auto-commit
      git push
    fi
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: lint-fix
        name: Auto-fix lint issues
        entry: python3 scripts/lint_fix.py
        language: system
        pass_filenames: false
```

## Casos de Uso

### 🚨 **Correção de Emergência**

```bash
# CI/CD falhando por problemas de linting
python3 scripts/lint_fix.py --auto-commit
git push
```

### 🔍 **Auditoria Preventiva**

```bash
# Verificar problemas antes do commit
python3 scripts/lint_fix.py --dry-run --verbose
```

### 🛠️ **Manutenção Regular**

```bash
# Executar periodicamente no projeto
python3 scripts/lint_fix.py src/
```

## Vantagens sobre Script Original

| Aspecto | Script Original | Nova Implementação |
|---------|----------------|-------------------|
| **Segurança** | ❌ Commits automáticos sem confirmação | ✅ Backups + modo dry-run |
| **Portabilidade** | ❌ Hardcoded para projeto específico | ✅ Genérico para qualquer projeto |
| **Manutenibilidade** | ❌ Regex complexas hardcoded | ✅ Estratégias modulares |
| **Robustez** | ❌ Sem tratamento de erros | ✅ Timeouts + validações |
| **Idempotência** | ❌ Pode aplicar correções múltiplas | ✅ Detecta correções já aplicadas |
| **Configuração** | ❌ Sem configuração | ✅ Via pyproject.toml + config file |

## Logs e Debugging

```bash
# Modo verboso para debugging
python3 scripts/lint_fix.py --verbose --dry-run

# Exemplo de saída:
# 14:30:15 - INFO - 🚨 SISTEMA DE CORREÇÃO AUTOMÁTICA DE LINTING
# 14:30:15 - INFO - 📁 Projeto: python-template-profissional
# 14:30:15 - INFO - 📏 Linha máxima: 88 chars
# 14:30:15 - INFO - 🎯 Caminhos: ['src', 'tests', 'scripts']
# 14:30:15 - INFO - 📁 Encontrados 15 arquivos Python
# 14:30:15 - INFO - ✅ Fixed 3 long lines in utils.py
# 14:30:15 - INFO - ✅ Formatação automática concluída
# 14:30:15 - INFO - ✅ Todos os problemas de linting foram resolvidos!
```

## Limitações e Considerações

### ⚠️ **Limitações**

- Correções são **heurísticas**, podem não cobrir 100% dos casos
- Strings muito complexas podem precisar correção manual
- Não corrige problemas lógicos, apenas formatação

### 💡 **Recomendações**

1. **Sempre execute `--dry-run` primeiro** em projetos críticos
2. **Configure seu editor** para mostrar linha de 88 caracteres
3. **Use em conjunto com pre-commit hooks** para prevenção
4. **Revise commits automáticos** antes do push

## Evolução para Templates Específicos

Este script **genérico** pode ser expandido para templates específicos:

### Para `python-template-api`

- Correções específicas para FastAPI/Flask
- Validação de schemas longas
- Quebra de rotas complexas

### Para `python-template-cli`

- Correções para argumentos de CLI longos
- Quebra de help strings
- Formatação de comandos complexos

### Para `python-template-lib`

- Correções para docstrings longas
- Quebra de type hints complexos
- Formatação de exemplos de código

---

**Status:** ✅ Pronto para produção
**Branch de destino:** `main` (genérico)
**Compatibilidade:** Python 3.10+ | Linux/macOS/Windows
**Dependências:** `ruff` (opcional, mas recomendado)
