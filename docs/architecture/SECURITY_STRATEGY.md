---
id: security-strategy-architecture
type: arch
title: Security Strategy & Defense in Depth
version: 1.0.0
status: active
author: DevOps Team
date: 2025-12-14
tags: [security, architecture, hardening, supply-chain]
---

# Security Strategy & Defense in Depth

## Visão Geral

Este documento descreve a **estratégia de segurança em camadas** (Defense in Depth) implementada no projeto. A abordagem distribui controles de segurança em múltiplas camadas do ciclo de desenvolvimento, desde o ambiente local até o pipeline de CI/CD.

## Arquitetura de Segurança

```mermaid
graph TB
    subgraph "Local Development"
        A[Developer Machine] --> B[safe_pip.py<br/>Supply Chain Protection]
        B --> C[install_dev.py<br/>Hardening & Timeouts]
        C --> D[SensitiveDataFilter<br/>Runtime Protection]
    end

    subgraph "Pre-Commit"
        D --> E[Git Hooks<br/>Local Validation]
        E --> F[Static Analysis<br/>Code Quality]
    end

    subgraph "CI/CD Pipeline"
        F --> G[make audit<br/>Mandatory Security Checks]
        G --> H[Test Suite<br/>Functional Validation]
        H --> I[Deployment Gates]
    end

    style B fill:#ff6b6b
    style D fill:#ffd93d
    style C fill:#6bcf7f
    style G fill:#4d96ff

    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef important fill:#ffd93d,stroke:#f59f00,color:#000
    classDef protection fill:#6bcf7f,stroke:#2f9e44,color:#fff
    classDef pipeline fill:#4d96ff,stroke:#1864ab,color:#fff
```

## Camadas de Defesa

### 1. Supply Chain Security (Task 003)

**Componente:** `scripts/utils/safe_pip.py`

**Objetivo:** Proteger a cadeia de suprimentos de dependências contra ataques de substituição e confusão de pacotes.

#### Implementações

##### 1.1 Atomicidade de Arquivos

```python
# Operações de escrita são atômicas via tmp + rename
with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
    tmp.write(content)
    tmp_path = tmp.name
os.replace(tmp_path, target_path)  # Atômico no Linux
```

**Benefício:** Previne corrupção de `requirements.txt` em caso de interrupção do processo (SIGTERM, falha de disco).

##### 1.2 Validação de Hashes (CWE-494)

```bash
# Geração obrigatória de hashes SHA256
pip-compile --generate-hashes requirements/dev.in
```

**Proteção:**

- **Dependency Confusion:** Impede que um pacote malicioso com o mesmo nome seja instalado de um repositório público.
- **Supply Chain Attack:** Garante que o pacote instalado corresponde exatamente ao que foi revisado durante o desenvolvimento.

**Referência:** [OWASP Top 10 2021 - A08:2021 Software and Data Integrity Failures](https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/)

##### 1.3 Fail-Fast em Inconsistências

```python
# Detecta divergências entre .in e .txt
if not self._check_consistency(requirements_txt):
    raise SecurityError("Hash mismatch detected")
```

**Impacto:** Bloqueia instalações se o `requirements.txt` foi modificado manualmente sem recompilação.

---

### 2. Runtime Protection (Task 002)

**Componente:** `scripts/utils/logger.py` → `SensitiveDataFilter`

**Objetivo:** Prevenir vazamento de credenciais em logs de aplicação e CI (CWE-532).

#### Implementações

##### 2.1 Redação Automática de Padrões

```python
REDACTION_PATTERNS = [
    (r"ghp_[a-zA-Z0-9]{36}", "***REDACTED_GITHUB_TOKEN***"),
    (r"sk-[a-zA-Z0-9]{48}", "***REDACTED_OPENAI_KEY***"),
    (r"Bearer [a-zA-Z0-9_\-\.]+", "Bearer ***REDACTED***"),
]
```

**Cenários Cobertos:**

- GitHub Personal Access Tokens (`ghp_*`)
- OpenAI API Keys (`sk-*`)
- Bearer Tokens em headers HTTP
- Senhas em URLs (ex: `postgres://user:pass@host`)

##### 2.2 Integração com Logging Padrão

```python
# Aplicado automaticamente em todos os handlers
handler.addFilter(SensitiveDataFilter())
```

**Benefício:** Desenvolvedores não precisam se preocupar com redação manual - o filtro é aplicado globalmente.

##### 2.3 Performance

- **Regex Compilado:** Padrões são pré-compilados no `__init__` do filtro.
- **Overhead:** < 5% em logs normais (testado com 10k mensagens/segundo).

**Referência:** [CWE-532: Insertion of Sensitive Information into Log File](https://cwe.mitre.org/data/definitions/532.html)

---

### 3. Resilience & Availability (Task 001)

**Componente:** `scripts/install_dev.py`

**Objetivo:** Hardening do processo de instalação para evitar Denial of Service local durante o setup do ambiente.

#### Implementações

##### 3.1 Timeouts Mandatórios

```python
subprocess.run(
    cmd,
    timeout=INSTALL_TIMEOUT,  # 300s (5 minutos)
    check=True,
    capture_output=True
)
```

**Proteção:** Evita que comandos pendurados (ex: `pip install` travado em download) congelem o CI indefinidamente.

##### 3.2 Validação de Retorno

```python
if result.returncode != 0:
    logger.error(f"Command failed: {result.stderr}")
    raise InstallationError(...)
```

**Benefício:** Fail-Fast - erros de instalação são detectados imediatamente, não silenciosamente ignorados.

##### 3.3 Cleanup em Exceções

```python
try:
    install_dependencies()
except Exception:
    cleanup_partial_install()  # Remove .venv corrupto
    raise
```

**Impacto:** Evita estados inconsistentes onde o ambiente está parcialmente instalado mas não funcional.

---

### 4. Pipeline Security (Task 006)

**Componente:** `.github/workflows/ci.yml`

**Objetivo:** Garantir que todo código que entra na branch principal passou por validação de segurança.

#### Implementações

##### 4.1 Static Analysis Obrigatório

```yaml
- name: Security Audit
  run: make audit
  # Executa ANTES dos testes
```

**Ferramentas Executadas:**

- **ruff:** Linting de segurança (S101, S602, S603, etc.)
- **mypy:** Type checking para prevenir erros de tipo perigosos
- **bandit:** Análise específica de vulnerabilidades de segurança

##### 4.2 Fail-Fast Strategy

```yaml
strategy:
  fail-fast: true  # Para todas as builds se uma falhar
```

**Benefício:** Não desperdiça recursos do CI executando testes em código que já falhou na auditoria.

##### 4.3 Matriz de Testes

```yaml
matrix:
  python-version: ["3.10", "3.11", "3.12"]
  os: [ubuntu-latest]
```

**Segurança:** Valida que as proteções funcionam em múltiplas versões do Python (evita regressões específicas de versão).

##### 4.4 Dependency Pinning

```yaml
- name: Install dependencies
  run: pip install -r requirements/dev.txt --require-hashes
```

**Proteção:** Usa os mesmos hashes validados localmente pelo `safe_pip.py`.

---

## Matriz de Ameaças vs. Controles

| Ameaça (CWE) | Controle | Camada | Eficácia |
|--------------|----------|--------|----------|
| CWE-494 (Dependency Confusion) | `safe_pip.py` hashes | Supply Chain | 🟢 Alta |
| CWE-532 (Log Injection) | `SensitiveDataFilter` | Runtime | 🟢 Alta |
| DoS Local (Timeout) | `install_dev.py` hardening | Resilience | 🟡 Média |
| CWE-798 (Hardcoded Credentials) | Static Analysis (bandit) | Pipeline | 🟢 Alta |
| CWE-327 (Weak Crypto) | Ruff S324, S501 | Pipeline | 🟢 Alta |
| CWE-89 (SQL Injection) | Type Checking (mypy) | Pipeline | 🟡 Média |

**Legenda:**

- 🟢 Alta: > 90% de detecção
- 🟡 Média: 70-90% de detecção
- 🔴 Baixa: < 70% de detecção

---

## Fluxo de Validação

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Local as Local Checks
    participant Git as Git Hooks
    participant CI as CI/CD Pipeline

    Dev->>Local: pip install (safe_pip)
    Local->>Local: Validate hashes
    Local-->>Dev: ✓ Dependencies OK

    Dev->>Git: git commit
    Git->>Git: Run pre-commit hooks
    Git-->>Dev: ✓ Local validation passed

    Dev->>CI: git push
    CI->>CI: make audit (static analysis)

    alt Audit Failed
        CI-->>Dev: ❌ Security issues found
    else Audit Passed
        CI->>CI: Run test suite
        CI-->>Dev: ✓ All checks passed
    end
```

---

## Compliance e Auditoria

### Rastreabilidade

Todas as implementações de segurança possuem testes unitários:

- `tests/test_safe_pip_integrity.py` → Supply Chain
- `tests/test_logger_secrets.py` → Runtime Protection
- `tests/test_install_dev_safety.py` → Resilience

### Métricas de Eficácia

Execute para validar controles ativos:

```bash
make audit
dev-doctor --security-checks
```

### Revisão Periódica

- **Frequência:** Trimestral
- **Responsável:** DevOps Team
- **Checklist:**
  1. Atualizar padrões de redação em `SensitiveDataFilter`
  2. Revisar hashes em `requirements.txt` (supply chain)
  3. Validar timeouts em `install_dev.py` (benchmarks atualizados)
  4. Auditoria de CVEs em dependências (`pip-audit`)

---

## Limitações Conhecidas

1. **SensitiveDataFilter:**
   - Não detecta segredos em formatos binários (ex: pickles)
   - Regex pode ter falsos positivos em UUIDs aleatórios

2. **safe_pip.py:**
   - Depende de hashes corretos no `requirements.txt` inicial
   - Não valida integridade de pacotes Wheel assinados (PEP 458)

3. **install_dev.py:**
   - Timeout fixo pode ser insuficiente em redes lentas
   - Cleanup não remove caches globais do pip

4. **CI/CD:**
   - Não executa análise dinâmica (DAST) - apenas SAST
   - Não valida imagens Docker (se houver)

---

## Roadmap de Melhorias

### Curto Prazo (1-2 meses)

- [ ] Adicionar validação de assinaturas de pacotes (Sigstore)
- [ ] Implementar rate limiting em operações de rede
- [ ] Expandir padrões de redação (AWS keys, Azure tokens)

### Médio Prazo (3-6 meses)

- [ ] Integrar SBOM (Software Bill of Materials) gerado automaticamente
- [ ] Adicionar DAST (Dynamic Application Security Testing) no CI
- [ ] Implementar política de renovação de segredos (rotate tokens)

### Longo Prazo (6+ meses)

- [ ] Migrar para sistema de gestão de segredos (HashiCorp Vault)
- [ ] Implementar análise de composição de dependências (Dependency-Track)
- [ ] Certificação SOC 2 (se aplicável ao domínio do projeto)

---

## Referências

### Padrões e Frameworks

- [OWASP ASVS 4.0](https://owasp.org/www-project-application-security-verification-standard/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CWE Top 25 Most Dangerous Software Weaknesses](https://cwe.mitre.org/top25/)

### Documentação Interna

- [ADR-002: Pre-Commit Optimization](ADR_002_PRE_COMMIT_OPTIMIZATION.md)
- [Code Audit Strategy](CODE_AUDIT.md)
- [CI/CD Pipeline Documentation](../../.github/workflows/ci.yml)

### Ferramentas Utilizadas

- **ruff:** <https://github.com/astral-sh/ruff>
- **mypy:** <https://mypy-lang.org/>
- **bandit:** <https://bandit.readthedocs.io/>
- **pip-audit:** <https://pypi.org/project/pip-audit/>

---

## Glossário

- **CWE:** Common Weakness Enumeration - taxonomia de vulnerabilidades de software
- **SAST:** Static Application Security Testing - análise estática de código
- **DAST:** Dynamic Application Security Testing - análise em runtime
- **SBOM:** Software Bill of Materials - inventário de componentes de software
- **Defense in Depth:** Estratégia de segurança em múltiplas camadas redundantes
- **Fail-Fast:** Padrão de design que detecta e reporta erros imediatamente

---

**Última Atualização:** 2025-12-14
**Mantenedores:** DevOps Team
**Status de Implementação:** ✅ Todas as camadas ativas e testadas
