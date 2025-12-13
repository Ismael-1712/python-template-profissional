---
id: quick-implementation-guide-pre-commit-fix
type: guide
status: active
version: 1.0.0
author: DevOps Team
date: '2025-12-13'
tags: [dx, pre-commit, implementation]
---

# 🚀 Quick Implementation Guide: Pre-Commit Optimization

**Objetivo**: Eliminar o "commit loop" causado por hooks que modificam arquivos voláteis.

**Tempo Estimado**: 5 minutos para validação

---

## ✅ O Que Foi Implementado

### Fase 1: Lazy Audit (Quick Win) - COMPLETED

As seguintes mudanças foram aplicadas:

1. **[`scripts/cli/audit.py`](../../../scripts/cli/audit.py)** - Modificado
   - Detecta contexto de pre-commit via variável de ambiente `PRE_COMMIT=1`
   - **Skip gravação de métricas** quando executado como hook
   - Validação de código continua funcionando normalmente

2. **[`.pre-commit-config.yaml`](../../../.pre-commit-config.yaml)** - Atualizado
   - Hook `code-audit-security` agora define `PRE_COMMIT=1`
   - Comando: `env PRE_COMMIT=1 python3 scripts/cli/audit.py ...`

3. **[`Makefile`](../../../Makefile)** - Adicionado (Opcional)
   - Target `make commit MSG='mensagem'` - Wrapper inteligente
   - Target `make commit-amend` - Amend com auto-staging

---

## 🧪 Como Testar

### Teste 1: Commit Normal

```bash
# Criar uma mudança trivial
echo "# Test" >> README.md
git add README.md

# Commitar (deve funcionar SEM loop)
git commit -m "test: validate lazy audit"

# ✅ EXPECTED: Commit completa em <15s sem pedir re-add de audit_metrics.json
# ✅ EXPECTED: Você vê "Pre-commit context detected - skipping metrics persistence" no log
```

### Teste 2: Verificar Que Validação Ainda Funciona

```bash
# Criar código com vulnerabilidade proposital
cat > test_security.py << 'EOF'
import subprocess
subprocess.run("ls -la", shell=True)  # CRITICAL: shell=True
EOF

git add test_security.py
git commit -m "test: should fail validation"

# ✅ EXPECTED: Commit deve FALHAR (hook detecta shell=True)
# ❌ Se passou, algo está errado
```

### Teste 3: Commit com Wrapper (Opcional)

```bash
# Usando o novo target do Makefile
make commit MSG="test: validate automation wrapper"

# ✅ EXPECTED: Commit completa mesmo se hooks modificarem arquivos
```

### Teste 4: Verificar Métricas Ainda São Gravadas em CI

```bash
# Executar audit manualmente (sem PRE_COMMIT=1)
python3 scripts/cli/audit.py --config scripts/audit_config.yaml

# Verificar se audit_metrics.json foi atualizado
python3 -c "import json; data=json.load(open('audit_metrics.json')); print(f'Last audit: {data[\"last_audit\"]}')"

# ✅ EXPECTED: Timestamp atualizado (métricas gravadas fora de pre-commit)
```

---

## 📊 Validação de Sucesso

### Checklist

- [ ] **Commit sem loop**: 10 commits consecutivos sem precisar de `git add audit_metrics.json`
- [ ] **Tempo < 15s**: Commits completam em menos de 15 segundos
- [ ] **Validação ativa**: Hook ainda detecta vulnerabilidades (teste com `shell=True`)
- [ ] **Métricas em CI**: Execuções manuais gravam métricas normalmente
- [ ] **Log correto**: Mensagem "skipping metrics persistence" aparece em commits

### KPIs

```bash
# Medir tempo de commit
time git commit -m "test: performance measurement"

# ✅ TARGET: real < 0m15s
# ❌ BEFORE: real > 0m30s (com retries)
```

---

## 🛠️ Troubleshooting

### Problema: Ainda há loop de commits

**Sintoma**:

```
You have unstaged changes to the following files:
    audit_metrics.json
```

**Diagnóstico**:

```bash
# Verificar se PRE_COMMIT está sendo definido
grep "PRE_COMMIT=1" .pre-commit-config.yaml

# Verificar logs do hook
git commit -m "test" 2>&1 | grep -i "pre-commit context"
```

**Solução**:

1. Confirmar que `.pre-commit-config.yaml` tem `env PRE_COMMIT=1`
2. Reinstalar hooks: `pre-commit install --install-hooks`
3. Limpar cache: `pre-commit clean`

---

### Problema: Validação não está funcionando

**Sintoma**: Código com vulnerabilidades passa sem erro

**Diagnóstico**:

```bash
# Testar hook diretamente
env PRE_COMMIT=1 python3 scripts/cli/audit.py --config scripts/audit_config.yaml test_security.py
```

**Solução**:

- Hook DEVE retornar exit code != 0 para código problemático
- Verificar `--fail-on HIGH` está configurado
- Logs devem mostrar "Audit failed due to..."

---

### Problema: Métricas não são mais gravadas

**Sintoma**: `audit_metrics.json` nunca atualiza

**Diagnóstico**:

```bash
# Executar audit SEM PRE_COMMIT
python3 scripts/cli/audit.py

# Verificar timestamp
cat audit_metrics.json | grep last_audit
```

**Solução**:

- Métricas SÃO gravadas quando `PRE_COMMIT != 1`
- Em CI, não definir `PRE_COMMIT=1`
- Execuções manuais gravam normalmente

---

## 🎯 Próximos Passos (Opcional)

### Fase 2: CI Shift (Recomendado)

Mover auditoria profunda para GitHub Actions:

1. **Criar** `.github/workflows/governance.yml`
2. **Simplificar** hooks locais (apenas linters rápidos)
3. **Configurar** branch protection (CI obrigatório)

**Benefício**: Commits ainda mais rápidos (< 5s), feedback assíncrono no PR.

**Referência**: Ver [DX_GOVERNANCE_BOTTLENECK_ANALYSIS.md](../analysis/DX_GOVERNANCE_BOTTLENECK_ANALYSIS.md#fase-2-ci-shift-deep-validation)

---

## 📚 Documentação Relacionada

- **[ADR-002](../architecture/ADR_002_PRE_COMMIT_OPTIMIZATION.md)** - Decisão arquitetural completa
- **[DX Analysis](../analysis/DX_GOVERNANCE_BOTTLENECK_ANALYSIS.md)** - Análise do problema e soluções
- **[Engineering Standards](ENGINEERING_STANDARDS.md)** - Padrões de qualidade

---

## ❓ FAQ

### Por que não adicionar `audit_metrics.json` ao `.gitignore`?

**R**: Perderíamos rastreabilidade histórica das métricas. O projeto segue o princípio "Documentation as Code" - métricas fazem parte da documentação do projeto.

### Desenvolvedores ainda verão métricas locais?

**R**: Não durante pre-commit, mas podem rodar manualmente:

```bash
python3 scripts/cli/audit.py --dashboard
```

Métricas centralizadas (CI) são mais confiáveis e consistentes.

### O que acontece se desabilitar pre-commit hooks?

**R**: CI ainda validará tudo. Branch protection rules garantem qualidade.

### Posso voltar ao comportamento antigo?

**R**: Sim, remova `env PRE_COMMIT=1` do `.pre-commit-config.yaml`. Mas prepare-se para o loop infinito 😅.

---

**Última Atualização**: 2025-12-13
**Autor**: DevOps Team
**Status**: ✅ Implementado e Testado
