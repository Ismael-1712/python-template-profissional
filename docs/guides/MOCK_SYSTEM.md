---
id: readme-test-mock-system
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
last_updated: '2025-12-01'
context_tags: []
linked_code:
- scripts/test_mock_generator.py
- scripts/validate_test_mocks.py
- scripts/ci_test_mock_integration.py
title: Test Mock Generator System
---

# Test Mock Generator System

Sistema robusto de geração automática de mocks para testes Python, seguindo padrões DevOps e SRE.

## 🎯 Propósito

Este sistema automatiza a geração e aplicação de mocks em arquivos de teste Python, garantindo que:

- **Testes sejam estáveis no CI/CD** (sem dependências externas)
- **Código seja portável** entre diferentes ambientes
- **Padrões de qualidade** sejam mantidos automaticamente

## 🏗️ Arquitetura

```
scripts/
├── test_mock_generator.py      # Gerador principal de mocks
├── test_mock_config.yaml       # Configuração extensível
├── validate_test_mocks.py      # Validador do sistema
├── ci_test_mock_integration.py # Integração CI/CD
└── README_test_mock_system.md  # Este arquivo
```

## � Arquitetura Interna do Mock CI

O sistema Mock CI segue um pipeline de 3 estágios com separação clara de responsabilidades:

### Pipeline: Detector → Checker → Fixer

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Detector   │ ───> │   Checker   │ ───> │    Fixer    │
│             │      │             │      │             │
│ • Scan AST  │      │ • Validate  │      │ • Apply     │
│ • Find      │      │ • Report    │      │   Patches   │
│   Patterns  │      │ • Classify  │      │ • Commit    │
└─────────────┘      └─────────────┘      └─────────────┘
       ↓                    ↓                    ↓
   External            Mock State          Code Modified
   Calls Found         Analyzed             & Committed
```

### Componentes Principais

#### 1️⃣ **Detector** (`scripts/core/mock_ci/detector.py`)

**Responsabilidade:** Análise AST para identificar dependências externas.

```python
from scripts.core.mock_ci.detector import detect_ci_environment

# Detecta ambiente CI/CD baseado em variáveis de ambiente
env = detect_ci_environment()  # "github-actions", "gitlab-ci", "local"
```

**Funcionalidades:**

- ✅ Detecção automática de ambiente CI/CD (GitHub Actions, GitLab CI, Jenkins)
- ✅ Identificação de chamadas externas em código Python via AST
- ✅ Classificação de dependências (HTTP, subprocess, filesystem, database)
- ✅ Suporte a múltiplas plataformas CI/CD

**Padrões Detectados:**

- HTTP: `requests.*`, `httpx.*`, `urllib.*`
- Subprocess: `subprocess.run()`, `subprocess.Popen()`
- Filesystem: `open()`, `Path.read_text()`
- Database: `sqlite3.connect()`, `psycopg2.connect()`

---

#### 2️⃣ **Checker** (`scripts/core/mock_ci/checker.py`)

**Responsabilidade:** Validação read-only de estado de testes e mocks.

```python
from scripts.core.mock_ci.checker import CIChecker

checker = CIChecker(generator, validator, ci_environment="github-actions")
report = checker.check_tests(git_info)
```

**Funcionalidades:**

- ✅ Verificação de cobertura de mocks sem modificar arquivos
- ✅ Geração de relatórios detalhados (CIReport)
- ✅ Classificação de severidade (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Detecção de testes instáveis (dependências externas não mockadas)

**Outputs:**

- `CIReport`: Relatório estruturado com findings e recomendações
- `CIStatus`: Estado do CI (PASS, WARNING, FAIL)
- `MockSuggestions`: Lista de sugestões de mocks para aplicar

---

#### 3️⃣ **Fixer** (`scripts/core/mock_ci/fixer.py`)

**Responsabilidade:** Aplicação automática de patches e transformações AST.

```python
from scripts.core.mock_ci.fixer import CIFixer

fixer = CIFixer(generator, validator, git_ops)
result = fixer.apply_fixes(git_info, dry_run=False)
```

**Funcionalidades:**

- ✅ Aplicação de mocks em código Python
- ✅ Transformações AST seguras (validação pré/pós aplicação)
- ✅ Modo dry-run para preview de mudanças
- ✅ Rollback automático em caso de erro

**Operações:**

1. Aplica patches usando `TestMockGenerator`
2. Valida sintaxe e semântica pós-patch
3. Integra com `GitOperations` para commit automático

---

#### 4️⃣ **Git Operations** (`scripts/core/mock_ci/git_ops.py`)

**Responsabilidade:** Gestão de commits automáticos e controle de versão.

**Funcionalidades:**

- ✅ Commits atômicos com mensagens descritivas
- ✅ Detecção de repositório Git
- ✅ Validação de estado limpo antes de modificações
- ✅ Integração com CI/CD (skip CI flags quando apropriado)

**Exemplo de Commit:**

```
fix(tests): Apply automatic mocks for CI stability

- Added mocks for httpx.get() in test_api.py
- Added mocks for subprocess.run() in test_cli.py
- Detected by Mock CI system

[skip ci]
```

---

### Fluxo de Execução Completo

```python
# 1. DETECÇÃO
ci_env = detect_ci_environment()  # "github-actions"

# 2. VERIFICAÇÃO (Read-Only)
checker = CIChecker(generator, validator, ci_env)
report = checker.check_tests(git_info)

if report.status == CIStatus.FAIL:
    # 3. CORREÇÃO (Write)
    fixer = CIFixer(generator, validator, git_ops)
    fix_result = fixer.apply_fixes(git_info, dry_run=False)

    # 4. COMMIT AUTOMÁTICO
    if fix_result.success:
        git_ops.commit_changes("fix(tests): Apply automatic mocks")
```

### Decisões de Design

**Separação de Concerns:**

- `Detector`: Apenas leitura e análise
- `Checker`: Apenas validação e relatório
- `Fixer`: Apenas modificação e commit

**Vantagens:**

- ✅ Testabilidade: Cada componente é testável isoladamente
- ✅ Reusabilidade: Componentes podem ser usados em diferentes contextos
- ✅ Segurança: Operações destrutivas isoladas no Fixer
- ✅ Auditabilidade: Logs estruturados em cada estágio

---

## �🚀 Uso Rápido

### 1. Escanear Arquivos de Teste

```bash
mock-ci --scan
```

### 2. Preview das Correções

```bash
mock-ci --apply --dry-run
```

### 3. Aplicar Correções

```bash
mock-ci --apply
```

### 4. Validar Sistema

```bash
mock-ci --check --fail-on-issues
```

## 📋 Funcionalidades

### ✅ Detecção Automática

- **Requisições HTTP** (`httpx.get`, `requests.post`, etc.)
- **Execução de subprocessos** (`subprocess.run`, `Popen`)
- **Operações de arquivo** (`open()`, `pathlib.Path`)
- **Conexões de banco** (`sqlite3.connect`)

### 🛡️ Segurança & Robustez

- **Backup automático** antes de modificar arquivos
- **Idempotência** - pode ser executado múltiplas vezes
- **Logging estruturado** para auditoria
- **Validação de sintaxe** antes e depois

### 🔧 Configurabilidade

- **Padrões extensíveis** via YAML
- **Templates personalizáveis** de mock
- **Severidade configurável** (HIGH, MEDIUM, LOW)
- **Filtros por tipo** de projeto

## 🏭 Integração CI/CD

### GitHub Actions

```yaml
- name: Check Test Mocks
  run: mock-ci --check --fail-on-issues

- name: Auto-fix Test Issues
  run: mock-ci --auto-fix --commit
```

### GitLab CI

```yaml
test_mock_check:
  script:
    - mock-ci --check --fail-on-issues
  allow_failure: false
```

## 📊 Relatórios

O sistema gera relatórios detalhados em JSON:

```json
{
  "timestamp": "2025-10-31T18:00:00Z",
  "summary": {
    "total_suggestions": 15,
    "high_priority": 8,
    "files_analyzed": 25
  },
  "suggestions": [
    {
      "file": "tests/test_api.py",
      "function": "test_get_user",
      "line": 45,
      "pattern": "httpx.get(",
      "severity": "HIGH",
      "description": "HTTP GET request - needs mocking for CI stability"
    }
  ]
}
```

## 🎛️ Configuração

### Arquivo `test_mock_config.yaml`

```yaml
# Padrões customizáveis
mock_patterns:
  http_patterns:
    - pattern: "httpx.get("
      severity: "HIGH"
      mock_template: |
        @patch("httpx.get")
        def {func_name}(self, mock_get, *args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

# Configurações de execução
execution:
  min_severity_for_auto_apply: "HIGH"
  create_backups: true
  backup_directory: ".test_mock_backups"
```

## 🏆 Padrões de Qualidade

### Compatibilidade

- **Python 3.10+**
- **POSIX-compliant** (Linux, macOS, WSL)
- **Portabilidade** entre ambientes CI/CD

### Segurança

- ✅ Sem uso de `shell=True`
- ✅ Validação de caminhos de arquivo
- ✅ Tratamento seguro de exceptions
- ✅ Logging de auditoria

### Performance

- ✅ Processamento em lote
- ✅ Cache de análise AST
- ✅ Operações idempotentes

### Manutenibilidade

- ✅ Type hints completos
- ✅ Documentação inline
- ✅ Testes automatizados
- ✅ Configuração declarativa

## 🔧 Extensibilidade

### Adicionando Novos Padrões

1. **Edite `test_mock_config.yaml`:**

```yaml
custom_patterns:
  - pattern: "my_library.connect("
    type: "CUSTOM_SERVICE"
    severity: "HIGH"
    mock_template: |
      @patch("my_library.connect")
      def {func_name}(self, mock_connect, *args, **kwargs):
          mock_connect.return_value = Mock()
```

2. **O sistema detectará automaticamente** novos padrões

### Integrando com Ferramentas

```python
from test_mock_generator import TestMockGenerator
from pathlib import Path

# Uso programático
workspace = Path.cwd()
config_path = Path(__file__).parent / "test_mock_config.yaml"
generator = TestMockGenerator(workspace, config_path) # <-- CORRIGIDO

report = generator.scan_test_files()
generator.apply_suggestions(dry_run=False)
```

## 📈 Métricas e Monitoramento

### Códigos de Saída

- `0` - Sucesso completo
- `1` - Warning (problemas menores)
- `2` - Failure (problemas críticos)

### Logs Estruturados

```
2025-10-31 18:00:00 [INFO] test_mock_generator: Escaneamento concluído: 15 sugestões geradas
2025-10-31 18:00:05 [INFO] test_mock_generator: Mock aplicado: test_api.py:test_get_user
```

## 🛠️ Resolução de Problemas

### Problema: "Nenhuma sugestão encontrada"

```bash
# Verificar configuração e reescanear
mock-ci --scan
```

### Problema: "Erro de sintaxe após aplicação"

```bash
# Recomenda-se executar os testes para validar as correções:
python3 -m pytest tests/
```

### Problema: "Git commit falhou"

```bash
# Verificar status
git status
git diff

# Commit manual se necessário
git add .
git commit -m "fix(tests): Apply test mocks"
```

## 🎯 Casos de Uso

### 1. Projeto CLI

- Foco em mocks de `subprocess` e `sys.argv`
- Validação de entrada/saída

### 2. Projeto API

- Mocks de requisições HTTP
- Mocks de banco de dados
- Validação de endpoints

### 3. Projeto Library

- Mocks minimais
- Foco na lógica de negócio
- Testes de integração opcional

## 📚 Referências

- [PEP 8 - Style Guide](https://pep8.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [DevOps Automation Patterns](https://martinfowler.com/articles/devops-automation.html)

## 🤝 Contribuição

Este sistema faz parte do **Python Template Profissional** e segue os padrões:

- **Idempotência** obrigatória
- **Logging estruturado**
- **Configuração declarativa**
- **Testes automatizados**
- **Documentação completa**

---

**Autor:** DevOps Template Generator
**Versão:** 1.0.0
**Licença:** MIT
**Compatibilidade:** Python 3.10+, POSIX
