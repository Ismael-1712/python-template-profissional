# Smart Git Sync - Documentação de Uso

## Visão Geral

O **Smart Git Sync** é um sistema de sincronização inteligente de Git que integra auditoria preventiva, correções automáticas e operações Git seguras. Foi desenvolvido seguindo padrões DevOps/SRE para ser **idempotente**, **seguro** e **robusto**.

## Características Principais

### ✅ **Padrões DevOps Implementados**

- **Idempotência:** Pode ser executado múltiplas vezes sem efeitos colaterais
- **POSIX Compliance:** Scripts compatíveis com diferentes sistemas Unix/Linux
- **Segurança:** Nunca usa `shell=True`, valida todas as entradas
- **Type Safety:** Código completamente tipado com Python 3.10+
- **Structured Logging:** Sistema de logging profissional com níveis
- **Rollback Capability:** Desfaz operações em caso de falha
- **Configurabilidade:** Totalmente configurável via YAML

### 🛡️ **Recursos de Segurança**

- Validação de entrada rigorosa
- Execução de subprocess segura (sem `shell=True`)
- Rollback automático em falhas de push
- Auditoria preventiva de código
- Exclusão automática de arquivos sensíveis

### 🔍 **Auditoria Preventiva**

- Análise de segurança estática
- Detecção de dependências externas
- Simulação de ambiente CI/CD
- Correções automáticas de lint
- Relatórios estruturados

## Instalação

### Pré-requisitos

```bash
# Python 3.10+ required
python3 --version

# Instalar dependências (incluindo PyYAML e tomli)
pip install .[dev]
```

### Estrutura de Arquivos

```
scripts/
├── smart_git_sync.py              # Script principal
├── smart_git_sync_config.yaml     # Configuração
├── test_smart_git_sync.py         # Testes
└── code_audit.py                  # Sistema de auditoria (existente)
```

## Uso Básico

### 1. Execução Simples

```bash
# Sincronização completa com auditoria
python3 scripts/smart_git_sync.py

# Modo dry-run (apenas simula)
python3 scripts/smart_git_sync.py --dry-run

# Com configuração personalizada
python3 scripts/smart_git_sync.py --config custom_config.yaml
```

### 2. Configuração Personalizada

Crie um arquivo `custom_config.yaml`:

```yaml
# Configuração customizada
audit_enabled: true
audit_fail_threshold: "MEDIUM"
auto_fix_enabled: true
strict_audit: false
cleanup_enabled: true

# Timeouts
audit_timeout: 180
git_timeout: 60
lint_timeout: 120

# Segurança
excluded_paths:
  - ".env"
  - "*.log"
  - "__pycache__/"

allowed_file_extensions:
  - ".py"
  - ".yaml"
  - ".md"
```

### 3. Integração com CI/CD

#### GitHub Actions

```yaml
name: Smart Sync
on: [push, pull_request]

jobs:
  smart-sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: pip install pyyaml

      - name: Run Smart Git Sync (Dry Run)
        run: python3 scripts/smart_git_sync.py --dry-run --verbose
```

## Funcionalidades Avançadas

### 1. Workflow Completo

O Smart Git Sync executa as seguintes fases:

```
📋 FASE 1: Análise do Status do Repositório
├── Verifica mudanças pendentes
├── Identifica branch atual
└── Valida estado do repositório

🔍 FASE 2: Auditoria Preventiva de Código
├── Executa análise de segurança
├── Simula ambiente CI/CD
├── Detecta vulnerabilidades
└── Gera relatório de auditoria

🔧 FASE 3: Correções Automáticas (se necessário)
├── Aplica fixes de lint
├── Corrige imports
├── Formata código
└── Remove código não utilizado

📤 FASE 4: Operações Git
├── Adiciona arquivos ao stage
├── Cria commit inteligente
├── Faz push para remote
└── Rollback em caso de falha

🧹 FASE 5: Limpeza do Repositório
├── Git garbage collection
├── Remote prune
└── Otimizações de performance
```

### 2. Mensagens de Commit Inteligentes

O sistema analisa as mudanças e gera mensagens seguindo convenções:

```
feat: smart sync with preventive audit (5 files) [audit-fixes]
fix: smart sync with preventive audit (2 files)
docs: smart sync with preventive audit (3 files)
test: smart sync with preventive audit (1 files)
chore: smart sync with preventive audit (4 files)
```

### 3. Relatórios Estruturados

Cada execução gera um relatório JSON completo:

```json
{
  "metadata": {
    "sync_id": "20231102_143022",
    "timestamp": "2023-11-02T14:30:22.123456Z",
    "workspace": "/path/to/project",
    "dry_run": false
  },
  "steps": [
    {
      "name": "git_status",
      "status": "success",
      "duration_seconds": 0.125,
      "details": {
        "is_clean": false,
        "total_changes": 3,
        "current_branch": "main"
      }
    }
  ],
  "summary": {
    "total_steps": 5,
    "successful_steps": 5,
    "failed_steps": 0,
    "total_duration": 12.45
  }
}
```

## Tratamento de Erros

### 1. Rollback Automático

```python
# Se o push falhar, o sistema automaticamente:
try:
    git_push()
except GitOperationError:
    # Rollback do commit
    git reset --soft HEAD~1
    # Log do erro
    # Preserva mudanças locais
```

### 2. Tipos de Erro

- **SyncError:** Erro geral de sincronização
- **GitOperationError:** Falha em operação Git
- **AuditError:** Falha na auditoria de código

### 3. Recuperação Graceful

```bash
# O sistema preserva estado em caso de falha
# Relatórios são sempre salvos
# Logs detalhados para debugging
# Operações são atômicas quando possível
```

## Testes

### 1. Executar Testes

```bash
# Testes completos
python3 scripts/test_smart_git_sync.py

# Apenas testes unitários
python3 scripts/test_smart_git_sync.py --unit-tests-only

# Modo verbose
python3 scripts/test_smart_git_sync.py --verbose
```

### 2. Validação de Segurança

```bash
# O sistema de testes inclui:
# - Verificação de padrões inseguros
# - Validação de configuração
# - Testes de integração
# - Análise de cobertura de código
```

## Configuração Avançada

### 1. Configuração Completa

```yaml
# smart_git_sync_config.yaml

# Auditoria
audit_enabled: true
audit_timeout: 300
audit_fail_threshold: "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
strict_audit: true

# Correções automáticas
auto_fix_enabled: true
lint_timeout: 180

# Git
git_timeout: 120
cleanup_enabled: true

# Segurança
allowed_file_extensions:
  - ".py"
  - ".yaml"
  - ".json"
  - ".md"

excluded_paths:
  - ".git/"
  - "__pycache__/"
  - ".env"
  - "*.log"

# CI/CD
simulate_ci: true
ci_timeout: 300

# Performance
max_files_per_commit: 100
max_commit_message_length: 72

# Logging
log_level: "INFO"
log_to_file: true
log_file: "smart_git_sync.log"
```

### 2. Integração com Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
python3 scripts/smart_git_sync.py --dry-run
```

## Solução de Problemas

### 1. Problemas Comuns

**Erro: "Not a Git repository"**

```bash
# Certifique-se de estar em um repositório Git
git init
```

**Erro: "Code audit failed"**

```bash
# Execute auditoria manualmente para debug
python3 scripts/code_audit.py --verbose
```

**Erro: "Push failed"**

```bash
# Verifique conectividade e permissões
git remote -v
git push origin main
```

### 2. Debug Mode

```bash
# Ativar debug completo
python3 scripts/smart_git_sync.py --verbose

# Verificar logs
tail -f smart_git_sync.log
```

### 3. Modo de Recuperação

```bash
# Se algo der errado, use dry-run primeiro
python3 scripts/smart_git_sync.py --dry-run --verbose

# Desabilite auditoria temporariamente
python3 scripts/smart_git_sync.py --no-audit
```

## Boas Práticas

### 1. Uso em Produção

- Sempre teste com `--dry-run` primeiro
- Configure timeouts apropriados
- Use auditoria estrita em produção
- Monitore logs regularmente
- Mantenha backups de configuração

### 2. Desenvolvimento

- Use modo verbose durante desenvolvimento
- Execute testes antes de commits
- Revise relatórios de auditoria
- Configure exclusões apropriadas
- Documente configurações customizadas

### 3. CI/CD Integration

- Execute sempre em modo dry-run no CI
- Use configurações específicas por ambiente
- Monitore métricas de performance
- Configure alertas para falhas
- Mantenha logs centralizados

## Roadmap

### Funcionalidades Futuras

- [ ] Integração com ferramentas de qualidade (SonarQube, CodeClimate)
- [ ] Suporte a múltiplos repositórios
- [ ] Dashboard web para métricas
- [ ] Integração com sistemas de tickets
- [ ] Suporte a Git LFS
- [ ] Notificações via Slack/Teams
- [ ] Análise de performance de código
- [ ] Integração com ferramentas de segurança (Snyk, etc.)

---

## Conclusão

O **Smart Git Sync** fornece uma solução robusta e segura para automação de Git que pode ser usada em qualquer projeto Python. Seguindo padrões DevOps, ele garante operações idempotentes, seguras e auditáveis.

Para suporte ou contribuições, consulte a documentação do projeto ou abra uma issue no repositório.
