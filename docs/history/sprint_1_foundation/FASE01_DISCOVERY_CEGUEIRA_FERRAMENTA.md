---
id: fase01-discovery-cegueira-ferramenta
type: history
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code: []
title: 'Fase 01 - Discovery: Mapeamento de Configurações e Decisões Silenciosas'
---

# Fase 01 - Discovery: Mapeamento de Configurações e Decisões Silenciosas

**Data de Auditoria:** 29 de Novembro de 2025
**Objetivo:** Combater "Cegueira de Ferramenta" mapeando todas as configurações que alteram o comportamento do sistema
**Escopo:** `scripts/**/*.py`

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

### 2.6 Script: `validate_test_mocks.py`

| Argumento | Tipo | Padrão | Obrigatório | Descrição | Documentado? |
|-----------|------|--------|-------------|-----------|--------------|
| `--workspace` | `Path` | `cwd()` | ❌ | Caminho do workspace | ⚠️ |
| `--verbose` / `-v` | `action="store_true"` | `False` | ❌ | Logging detalhado | ✅ |
| `--fix-found-issues` | `action="store_true"` | `False` | ❌ | **MODIFICADOR** - Corrige problemas automaticamente | ❌ |

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

### 4.4 Modo Dry-Run Sobrescrito Silenciosamente

**Em `ci_recovery/main.py:292`:**

```python
dry_run = args.dry_run or os.getenv("CI_RECOVERY_DRY_RUN", "").lower() == "true"
```

**Problema:**
Usuário passa `--dry-run=False` mas env var `CI_RECOVERY_DRY_RUN=true` força dry-run silenciosamente.

### 4.6 Configuração de Idioma (i18n)

**Em múltiplos arquivos:**

```python
languages=[os.getenv("LANGUAGE", "pt_BR")],
```

**Problema:**

- Padrão hardcoded para `pt_BR`
- Usuários anglófonos veem mensagens em português sem saber como mudar
- Variável `LANGUAGE` não documentada em nenhum README

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

## 📊 6. MÉTRICAS DE IMPACTO

### Distribuição de Severidade

| Severidade | Quantidade | Exemplos |
|------------|------------|----------|
| 🔴 CRÍTICO | 3 | Propagação de tokens, CI mode sem banner, env var override silencioso |
| 🟠 ALTO | 5 | Configs não documentados, modo full scan sem aviso, arquivos criados automaticamente |
| 🟡 MÉDIO | 7 | Idioma hardcoded, fallbacks silenciosos, detecção de terminal |
| 🟢 BAIXO | 3 | `.python-version` opcional, TERM checking, color detection |

## 📝 Notas de Auditoria

- **Metodologia:** Grep search + análise manual de código
- **Ferramentas:** `grep_search`, `read_file`, análise estática
- **Limitação:** Não foram testados comportamentos em runtime real
- **Cobertura:** 100% dos arquivos em `scripts/**/*.py`

---

**Relatório Gerado Por:** GitHub Copilot Agent
**Validado Por:** Sistema de Auditoria de Código
**Versão do Relatório:** 1.0.0
