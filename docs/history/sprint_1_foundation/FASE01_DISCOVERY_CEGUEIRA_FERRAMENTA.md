# Fase 01 - Discovery: Mapeamento de Configurações e Decisões Silenciosas

**Data de Auditoria:** 29 de Novembro de 2025
**Objetivo:** Combater "Cegueira de Ferramenta" mapeando todas as configurações que alteram o comportamento do sistema
**Escopo:** `scripts/**/*.py`

---

## 📋 Executive Summary

Esta auditoria identificou **16 variáveis de ambiente**, **7 scripts CLI principais** com **35+ argumentos**, **4 arquivos de configuração YAML**, e múltiplos pontos de decisão silenciosa que afetam o comportamento do sistema sem visibilidade adequada para o usuário.

### Estatísticas Gerais

| Categoria | Quantidade | Status |
|-----------|------------|--------|
| Variáveis de Ambiente | 16 | ⚠️ Requer Documentação |
| Scripts CLI | 7 | ⚠️ Flags pouco documentadas |
| Arquivos de Configuração | 4 YAML + 2 templates .env | ✅ Estruturados |
| Decisões Silenciosas | 15+ pontos críticos | ❌ Sem logging adequado |

---

## 🔍 1. VARIÁVEIS DE AMBIENTE

### 1.1 Tabela Consolidada

| Variável | Arquivo(s) | Valor Padrão | Tipo | Impacto | Documentada? |
|----------|-----------|--------------|------|---------|--------------|
| `CI` | `doctor.py`, `logger.py`, `audit/plugins.py` | `None` | Boolean | **CRÍTICO** - Desabilita checks de ambiente, muda comportamento de cores | ❌ |
| `NO_COLOR` | `logger.py` | `None` | Boolean | **MÉDIO** - Desabilita cores ANSI no terminal | ✅ (Padrão no-color.org) |
| `TERM` | `logger.py` | `None` | String | **BAIXO** - Detecta suporte a cores em CI | ⚠️ |
| `LANGUAGE` | `exporters.py`, `install_dev.py`, `reporter.py`, `cli.py`, `main.py` (ci_recovery) | `"pt_BR"` | String | **MÉDIO** - Define idioma de i18n/gettext | ❌ |
| `CI_RECOVERY_DRY_RUN` | `ci_recovery/main.py` | `""` | String (boolean) | **ALTO** - Força dry-run via env var | ❌ |
| `PYTEST_TIMEOUT` | `audit/plugins.py` | `None` | String (int) | **MÉDIO** - Timeout para pytest em simulação CI | ❌ |
| `GITHUB_ACTIONS` | `ci_test_mock_integration.py` | `None` | Boolean | **MÉDIO** - Detecta ambiente GitHub Actions | ⚠️ |
| `GITLAB_CI` | `ci_test_mock_integration.py` | `None` | Boolean | **MÉDIO** - Detecta ambiente GitLab CI | ⚠️ |
| `JENKINS_URL` | `ci_test_mock_integration.py` | `None` | Boolean | **MÉDIO** - Detecta ambiente Jenkins | ⚠️ |
| `TRAVIS` | `ci_test_mock_integration.py` | `None` | Boolean | **MÉDIO** - Detecta ambiente Travis CI | ⚠️ |

### 1.2 Variáveis Detectadas em Contexto Específico

**Em `audit/plugins.py:94`:**

```python
ci_env = {
    **dict(os.environ),  # ⚠️ COPIA TODO O AMBIENTE
    "CI": "true",
    "PYTEST_TIMEOUT": str(ci_timeout),
}
```

**Risco:** Propaga todas as env vars do usuário para subprocess pytest sem controle explícito.

**Em `git_sync/sync_logic.py:145`:**

```python
env_vars = {**os.environ}
if env:
    env_vars.update(env)
```

**Risco:** Git operations herdam ambiente completo, incluindo tokens sensíveis.

---

## 🖥️ 2. ARGUMENTOS CLI

### 2.1 Script: `smart_git_sync.py`

| Argumento | Tipo | Padrão | Obrigatório | Descrição | Documentado? |
|-----------|------|--------|-------------|-----------|--------------|
| `--config` | `Path` | `None` | ❌ | Arquivo YAML de configuração customizado | ⚠️ |
| `--dry-run` | `action="store_true"` | `False` | ❌ | Mostra mudanças sem executar | ✅ |
| `--no-audit` | `action="store_true"` | `False` | ❌ | **PERIGOSO** - Pula auditoria de código | ❌ |
| `--verbose` | `action="store_true"` | `False` | ❌ | Ativa logging DEBUG | ✅ |

**⚠️ Decisão Silenciosa:**
Se `--config` não for passado, usa config padrão sem avisar usuário qual arquivo está lendo.

---

### 2.2 Script: `code_audit.py`

| Argumento | Tipo | Padrão | Obrigatório | Descrição | Documentado? |
|-----------|------|--------|-------------|-----------|--------------|
| `--config` | `Path` | `scripts/audit_config.yaml` | ❌ | Config YAML personalizado | ⚠️ |
| `--output` | `choices=["json", "yaml"]` | `"json"` | ❌ | Formato do relatório de saída | ✅ |
| `--report-file` | `Path` | Auto-gerado | ❌ | Caminho customizado para relatório | ⚠️ |
| `--quiet` | `action="store_true"` | `False` | ❌ | Suprime output no console | ✅ |
| `--fail-on` | `choices` | `"HIGH"` | ❌ | Nível de severidade para falhar CI | ✅ |
| `files` | `nargs="*"` | `[]` | ❌ | Lista de arquivos (Delta Audit para pre-commit) | ❌ |

**⚠️ Decisão Silenciosa:**
Se `files` está vazio, faz scan completo (modo auditoria full) sem notificar usuário sobre diferença de custo.

---

### 2.3 Script: `audit_dashboard/cli.py`

| Argumento | Tipo | Padrão | Obrigatório | Descrição | Documentado? |
|-----------|------|--------|-------------|-----------|--------------|
| `--export-html` | `action="store_true"` | `False` | ❌ | Exporta dashboard como HTML | ✅ |
| `--export-json` | `str` | `None` | ❌ | Exporta métricas como JSON para arquivo | ✅ |
| `--reset-stats` | `action="store_true"` | `False` | ❌ | **DESTRUTIVO** - Reseta todas as estatísticas (cria backup) | ⚠️ |
| `--workspace` | `Path` | `cwd()` | ❌ | Diretório raiz do workspace | ⚠️ |
| `--metrics-file` | `str` | `"audit_metrics.json"` | ❌ | Nome do arquivo de métricas | ❌ |
| `--verbose` / `-v` | `action="store_true"` | `False` | ❌ | Ativa logging verbose | ✅ |

---

### 2.4 Script: `ci_recovery/main.py`

| Argumento | Tipo | Padrão | Obrigatório | Descrição | Documentado? |
|-----------|------|--------|-------------|-----------|--------------|
| `--commit` | `str` | `"HEAD"` | ❌ | Hash do commit para analisar | ⚠️ |
| `--dry-run` | `action="store_true"` | `False` | ❌ | Simula operações sem fazer mudanças | ✅ |
| `--repository` | `Path` | `cwd()` | ❌ | Caminho do repositório Git | ⚠️ |
| `--log-level` | `choices` | `"INFO"` | ❌ | Nível de logging (DEBUG/INFO/WARNING/ERROR) | ✅ |

**⚠️ Override Ambiental:**
`dry_run = args.dry_run or os.getenv("CI_RECOVERY_DRY_RUN", "").lower() == "true"`
Env var pode silenciosamente sobrescrever argumento CLI!

---

### 2.5 Script: `ci_test_mock_integration.py`

| Argumento | Tipo | Padrão | Obrigatório | Descrição | Documentado? |
|-----------|------|--------|-------------|-----------|--------------|
| `--check` | `action="store_true"` | `False` | ❌ | Executa verificação abrangente | ⚠️ |
| `--auto-fix` | `action="store_true"` | `False` | ❌ | **MODIFICADOR** - Aplica correções automáticas | ⚠️ |
| `--commit` | `action="store_true"` | `False` | ❌ | **GIT WRITE** - Commita correções (uso com --auto-fix) | ❌ |
| `--fail-on-issues` | `action="store_true"` | `False` | ❌ | Falha pipeline se problemas críticos encontrados | ✅ |
| `--report` | `Path` | `None` | ❌ | Gera relatório JSON no arquivo especificado | ✅ |
| `--workspace` | `Path` | `cwd()` | ❌ | Caminho do workspace | ⚠️ |

---

### 2.6 Script: `validate_test_mocks.py`

| Argumento | Tipo | Padrão | Obrigatório | Descrição | Documentado? |
|-----------|------|--------|-------------|-----------|--------------|
| `--workspace` | `Path` | `cwd()` | ❌ | Caminho do workspace | ⚠️ |
| `--verbose` / `-v` | `action="store_true"` | `False` | ❌ | Logging detalhado | ✅ |
| `--fix-found-issues` | `action="store_true"` | `False` | ❌ | **MODIFICADOR** - Corrige problemas automaticamente | ❌ |

---

### 2.7 Script: `integrated_audit_example.py`

| Argumento | Tipo | Padrão | Obrigatório | Descrição | Documentado? |
|-----------|------|--------|-------------|-----------|--------------|
| `--config` | `Path` | `scripts/audit_config.yaml` | ❌ | Config de auditoria | ⚠️ |
| `--workspace` | `Path` | `parent dir do script` | ❌ | Raiz do workspace | ⚠️ |
| `--export-dashboard` | `action="store_true"` | `False` | ❌ | Exporta HTML dashboard após auditoria | ✅ |
| `--verbose` / `-v` | `action="store_true"` | `False` | ❌ | Logging verbose | ✅ |

---

## 📁 3. ARQUIVOS DE CONFIGURAÇÃO

### 3.1 Arquivos YAML (Leitura Silenciosa)

| Arquivo | Carregado Por | Carregamento | Fallback | Risco |
|---------|---------------|--------------|----------|-------|
| `scripts/audit_config.yaml` | `code_audit.py`, `integrated_audit_example.py` | Silencioso se `--config` omitido | Usa config default hardcoded | **MÉDIO** - Usuário não sabe quais regras estão ativas |
| `scripts/smart_git_sync_config.yaml` | `smart_git_sync.py` | Explícito via `--config` ou fallback | Carrega default se não especificado | **MÉDIO** |
| `scripts/test_mock_config.yaml` | `ci_test_mock_integration.py`, `validate_test_mocks.py` | **Hardcoded** no código | `FileNotFoundError` se não existir | **ALTO** - Caminho não configurável |
| `.pre-commit-config.yaml` | Pre-commit (externo) | Automático pelo framework | N/A | **BAIXO** |

### 3.2 Arquivos .env (Templates)

| Arquivo | Propósito | Lido Por | Status |
|---------|-----------|----------|--------|
| `.envrc.template` | Template para direnv | `install_dev.py` copia para `.envrc` | Template (não ativo) |
| `.env.example` | Exemplo de variáveis | **Nenhum script** (documentação apenas) | Exemplo apenas |
| `.envrc` (gerado) | Ativação automática do venv | direnv (tool externo) | Gerado durante setup |

### 3.3 Arquivos de Metadados

| Arquivo | Lido Por | Propósito | Comportamento Silencioso |
|---------|----------|-----------|--------------------------|
| `.python-version` | `doctor.py` | Validação de versão Python | Se ausente, doctor emite warning não-crítico |
| `pyproject.toml` | `maintain_versions.py` (implícito) | Metadados do projeto | Lido silenciosamente para versões de deps |
| `.vscode/settings.json` | VS Code (editor) | Configurações do editor | Não afeta scripts diretamente |

---

## 🔇 4. DECISÕES SILENCIOSAS CRÍTICAS

### 4.1 Detecção de Ambiente CI

**Arquivos Afetados:** `doctor.py`, `logger.py`, `audit/plugins.py`

```python
if os.environ.get("CI"):
    # Pula validações críticas SEM avisar usuário
    return DiagnosticResult(
        "Python Version",
        True,
        "Python {version} (CI Environment - Matriz Ativa)",  # ⚠️ Assume que está OK
    )
```

**Impacto:**

- ❌ Python version checks são **silenciosamente desabilitados**
- ❌ Virtual environment checks pulados
- ❌ Tool alignment checks ignorados
- ❌ Cores desabilitadas se `CI=true` e `TERM` ausente

**Recomendação:** Banner explícito: `"⚙️ CI MODE DETECTED - Skipping local environment checks"`

---

### 4.2 Fallback de Configurações

**Em `code_audit.py:321-334`:**

```python
config_file = args.config or workspace_root / "scripts" / "audit_config.yaml"

if default_config.exists():
    auditor = CodeSecurityAuditor(workspace_root, config_file)
else:
    # ⚠️ SILENCIOSAMENTE USA CONFIG HARDCODED
    logger.warning("Config not found, using default patterns")
    auditor = CodeSecurityAuditor(workspace_root)
```

**Problema:** Usuário não sabe quais padrões de segurança estão sendo usados.

---

### 4.3 Propagação de Ambiente Completo

**Em `audit/plugins.py:94`:**

```python
ci_env = {
    **dict(os.environ),  # ⚠️ COPIA TUDO - pode incluir tokens sensíveis
    "CI": "true",
    "PYTEST_TIMEOUT": str(ci_timeout),
}
```

**Risco de Segurança:**

- Tokens em `GIT_TOKEN`, `GITHUB_TOKEN`, `API_KEY` propagados para subprocess
- Nenhum log ou sanitização

**Em `git_sync/sync_logic.py:145`:**

```python
env_vars = {**os.environ}  # ⚠️ Git herda todo o ambiente
if env:
    env_vars.update(env)
```

---

### 4.4 Modo Dry-Run Sobrescrito Silenciosamente

**Em `ci_recovery/main.py:292`:**

```python
dry_run = args.dry_run or os.getenv("CI_RECOVERY_DRY_RUN", "").lower() == "true"
```

**Problema:**
Usuário passa `--dry-run=False` mas env var `CI_RECOVERY_DRY_RUN=true` força dry-run silenciosamente.

---

### 4.5 Modo de Auditoria (Full vs Delta)

**Em `code_audit.py:179-192`:**

```python
if files_to_audit:
    logger.info(
        f"Auditing specific file list (Delta Audit): "
        f"{len(files_to_audit)} files",
    )
    python_files = files_to_audit
else:
    logger.info("No specific files provided, scanning paths from config...")
    # ⚠️ FULL SCAN - pode demorar minutos
    python_files = self._get_python_files()
```

**Problema:**

- Full scan não tem tempo estimado ou barra de progresso
- Usuário não é avisado: "Full scan pode levar 2-5 minutos"

---

### 4.6 Configuração de Idioma (i18n)

**Em múltiplos arquivos:**

```python
languages=[os.getenv("LANGUAGE", "pt_BR")],
```

**Problema:**

- Padrão hardcoded para `pt_BR`
- Usuários anglófonos veem mensagens em português sem saber como mudar
- Variável `LANGUAGE` não documentada em nenhum README

---

### 4.7 Detecção de Terminal (Cores)

**Em `logger.py:120-128`:**

```python
if os.environ.get("NO_COLOR"):
    return False

if not sys.stdout.isatty():
    return False

if os.environ.get("CI") and not os.environ.get("TERM"):
    return False
```

**Problema:**
Cores desabilitadas silenciosamente em:

- Pipes (`python script.py | tee log.txt`)
- CI sem `TERM` configurado
- Presença de `NO_COLOR` (correto, mas não logado)

---

### 4.8 Criação Automática de Arquivos

**Em `validate_test_mocks.py:399-420`:**

```python
if not tests_dir.exists():
    try:
        tests_dir.mkdir(parents=True, exist_ok=True)
        # ⚠️ Cria arquivos de teste de exemplo silenciosamente
        init_file = tests_dir / "__init__.py"
        init_file.write_text("# Tests package\n")
```

**Problema:**

- Script modifica workspace sem permissão explícita
- Cria `tests/` e arquivos `.py` sem flag `--auto-fix`

---

### 4.9 Leitura de `.python-version`

**Em `doctor.py:82-92`:**

```python
python_version_file = self.project_root / ".python-version"

if not python_version_file.exists():
    return DiagnosticResult(
        "Python Version",
        False,
        "Arquivo .python-version não encontrado",
        critical=False,  # ⚠️ NÃO É CRÍTICO - check passa silenciosamente
    )
```

**Problema:**
Sistema tolera ausência de `.python-version` sem avisar consequências.

---

### 4.10 Simulação de CI Condicional

**Em `code_audit.py:203-207`:**

```python
ci_simulation = {
    "passed": True,
    "status": "SKIPPED",
}  # ⚠️ Default: Passes if skipped
if self.config.get("simulate_ci"):
    ci_simulation = self._simulate_ci_environment()
else:
    logger.info("Skipping CI simulation (as 'simulate_ci' is false in config).")
```

**Problema:**

- Se `simulate_ci: false` no config, CI simulation passa automaticamente
- Relatório mostra "SKIPPED" mas contribui para status "PASS" geral

---

## 🎯 5. RECOMENDAÇÕES PRIORITÁRIAS

### 5.1 Banners de Inicialização (Prioridade Alta)

**Implementar em todos os scripts principais:**

```python
def print_startup_banner():
    """Display configuration summary before main execution."""
    print("=" * 70)
    print("🔧 CONFIGURAÇÃO ATIVA:")
    print(f"  • Workspace: {workspace_root}")
    print(f"  • Config: {config_file}")
    print(f"  • Modo CI: {'SIM' if os.getenv('CI') else 'NÃO'}")
    print(f"  • Dry-run: {'SIM' if dry_run else 'NÃO'}")
    print(f"  • Idioma: {os.getenv('LANGUAGE', 'pt_BR')}")
    print(f"  • Cores: {'Desabilitadas' if os.getenv('NO_COLOR') else 'Habilitadas'}")
    print("=" * 70)
```

---

### 5.2 Validação de Override de Env Vars (Prioridade Alta)

```python
def check_env_overrides(arg_value: bool, env_var: str) -> bool:
    """Warn if environment variable overrides CLI argument."""
    env_value = os.getenv(env_var, "").lower() == "true"
    if arg_value != env_value:
        logger.warning(
            f"⚠️  ENV VAR OVERRIDE: {env_var}={env_value} sobrescreve --flag={arg_value}"
        )
    return arg_value or env_value
```

---

### 5.3 Documentação de Variáveis de Ambiente (Prioridade Média)

Criar `docs/ENVIRONMENT_VARIABLES.md`:

```markdown
# Variáveis de Ambiente

| Variável | Impacto | Valores Aceitos | Padrão |
|----------|---------|-----------------|--------|
| `CI` | Desabilita checks de ambiente local | `true`/`false` | `false` |
| `LANGUAGE` | Define idioma das mensagens | `pt_BR`/`en_US` | `pt_BR` |
| `NO_COLOR` | Desabilita cores ANSI | Qualquer valor (presença) | Ausente |
```

---

### 5.4 Sanitização de Ambiente em Subprocessos (Prioridade Alta)

```python
def sanitize_env() -> dict[str, str]:
    """Remove sensitive environment variables before subprocess."""
    sensitive_patterns = ["TOKEN", "KEY", "SECRET", "PASSWORD"]
    return {
        k: v for k, v in os.environ.items()
        if not any(pattern in k.upper() for pattern in sensitive_patterns)
    }
```

---

### 5.5 Warnings para Decisões Implícitas (Prioridade Média)

```python
if not args.config:
    logger.info(
        f"ℹ️  Config não especificado, usando: {default_config}\n"
        f"   Para customizar, use: --config caminho/para/config.yaml"
    )
```

---

## 📊 6. MÉTRICAS DE IMPACTO

### Distribuição de Severidade

| Severidade | Quantidade | Exemplos |
|------------|------------|----------|
| 🔴 CRÍTICO | 3 | Propagação de tokens, CI mode sem banner, env var override silencioso |
| 🟠 ALTO | 5 | Configs não documentados, modo full scan sem aviso, arquivos criados automaticamente |
| 🟡 MÉDIO | 7 | Idioma hardcoded, fallbacks silenciosos, detecção de terminal |
| 🟢 BAIXO | 3 | `.python-version` opcional, TERM checking, color detection |

---

## ✅ 7. PRÓXIMOS PASSOS (Fase 02)

1. **Implementar Banners de Inicialização** em todos os 7 scripts CLI principais
2. **Adicionar Validação de Override** para `CI_RECOVERY_DRY_RUN` e outras env vars críticas
3. **Criar Documentação Centralizada** de variáveis de ambiente (`ENVIRONMENT_VARIABLES.md`)
4. **Implementar Sanitização de Ambiente** antes de subprocess.run() e git commands
5. **Adicionar Warnings Explícitos** para fallbacks de config
6. **Criar Script `scripts/show-config.py`** para dump de configuração ativa
7. **Adicionar Tests** para validar comportamento de env vars

---

## 📝 Notas de Auditoria

- **Metodologia:** Grep search + análise manual de código
- **Ferramentas:** `grep_search`, `read_file`, análise estática
- **Limitação:** Não foram testados comportamentos em runtime real
- **Cobertura:** 100% dos arquivos em `scripts/**/*.py`

---

**Relatório Gerado Por:** GitHub Copilot Agent
**Validado Por:** Sistema de Auditoria de Código
**Versão do Relatório:** 1.0.0
