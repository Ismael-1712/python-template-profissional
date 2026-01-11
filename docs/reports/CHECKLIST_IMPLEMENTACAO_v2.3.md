---
id: checklist-implementacao-v23
type: guide
status: draft
version: 1.0.0
author: Engineering Team
date: 2026-01-11
context_tags: []
linked_code: []
---

# ✅ CHECKLIST DE IMPLEMENTAÇÃO - Deep Consistency Check v2.3

## 📋 STATUS GERAL

- [x] Investigação forense concluída
- [x] Causa raiz identificada (race condition temporal de PyPI)
- [x] Solução proposta e documentada
- [ ] Implementação iniciada
- [ ] Testes escritos
- [ ] CI atualizado
- [ ] Documentação atualizada
- [ ] Deploy em produção

---

## 🔬 FASE 1: IMPLEMENTAÇÃO DO CÓDIGO

### 1.1. Dependency Guardian - Core Logic

**Arquivo:** `scripts/core/dependency_guardian.py`

- [ ] Adicionar método `validate_deep_consistency()`
  - [ ] Implementar compilação em memória (tempfile)
  - [ ] Executar pip-compile com flags compatíveis com verify_deps.py
  - [ ] Comparação de conteúdo (comment-agnostic)
  - [ ] Geração de relatório de diferenças
  - [ ] Tratamento de erros (pip-compile failure)

- [ ] Adicionar método `_compare_content_deep()`
  - [ ] Leitura de ambos os arquivos
  - [ ] Filtro de comentários e linhas em branco
  - [ ] Comparação linha a linha
  - [ ] Retornar lista de mismatches

- [ ] Adicionar método `_format_diff_report()`
  - [ ] Formatação legível de diferenças
  - [ ] Incluir sugestões de remediação

**Critérios de Aceitação:**

- ✅ Código passa em `make lint`
- ✅ Código passa em `make type-check`
- ✅ Sem dependências externas adicionadas

---

### 1.2. CLI Interface Update

**Arquivo:** `scripts/core/dependency_guardian.py` (função `main()`)

- [ ] Adicionar ação `validate-deep` ao argparse
  - [ ] Suporte para `--python-exec` opcional
  - [ ] Exit codes corretos (0=sucesso, 1=falha)
  - [ ] Output formatado para humanos E CI

- [ ] Manter compatibilidade com ações existentes
  - [ ] `compute` (sem mudanças)
  - [ ] `seal` (sem mudanças)
  - [ ] `validate` (sem mudanças, deprecated)

**Critérios de Aceitação:**

- ✅ `python -m scripts.core.dependency_guardian validate-deep dev` funciona
- ✅ Output contém diff legível quando falhar
- ✅ Exit code 0 quando sincronizado
- ✅ Exit code 1 quando desincronizado

---

## 🧪 FASE 2: TESTES UNITÁRIOS

### 2.1. Testes de Detecção de Drift

**Arquivo:** `tests/test_dependency_guardian_deep.py` (criar novo)

- [ ] `test_deep_consistency_detects_pypi_drift()`
  - [ ] Setup: criar dev.in com dependência não pinada
  - [ ] Compilar lockfile fresco
  - [ ] Simular downgrade manual (tomli 2.4.0 → 2.3.0)
  - [ ] Validar que deep check detecta discrepância
  - [ ] Assert: `is_valid == False`
  - [ ] Assert: diff contém ambas as versões

- [ ] `test_deep_consistency_passes_when_synced()`
  - [ ] Setup: criar dev.in com dependências pinadas
  - [ ] Compilar lockfile fresco
  - [ ] Executar deep check imediatamente
  - [ ] Assert: `is_valid == True`
  - [ ] Assert: `diff == ""`

- [ ] `test_deep_consistency_detects_manual_edit()`
  - [ ] Setup: lockfile válido
  - [ ] Adicionar dependência fake no meio do arquivo
  - [ ] Executar deep check
  - [ ] Assert: detecção de adulteração

**Critérios de Aceitação:**

- ✅ 3 testes passam com `pytest`
- ✅ Coverage > 90% para novos métodos
- ✅ Testes não dependem de estado externo (PyPI)

---

### 2.2. Testes de Edge Cases

- [ ] `test_deep_check_handles_missing_input_file()`
  - [ ] Assert: retorna `(False, "Input file not found: ...")`

- [ ] `test_deep_check_handles_missing_lockfile()`
  - [ ] Assert: retorna `(False, "Lockfile not found: ...")`

- [ ] `test_deep_check_handles_pip_compile_failure()`
  - [ ] Simular falha do pip-compile (arquivo corrompido)
  - [ ] Assert: retorna `(False, "pip-compile failed: ...")`

**Critérios de Aceitação:**

- ✅ Todos os edge cases cobertos
- ✅ Mensagens de erro são descritivas

---

## 🔧 FASE 3: INTEGRAÇÃO AO MAKEFILE

### 3.1. Novo Target: deps-deep-check

**Arquivo:** `Makefile`

- [ ] Adicionar target `deps-deep-check`

  ```makefile
  ## deps-deep-check: Validação profunda de dependências (compilação em memória)
  deps-deep-check:
   @echo "🛡️  Executando Deep Consistency Check (Protocolo v2.3)..."
   @$(PYTHON) -m scripts.core.dependency_guardian validate-deep dev
   @echo "✅ Lockfile em paridade total com estado atual do PyPI"
  ```

- [ ] Atualizar target `validate`

  ```makefile
  validate: lint type-check deps-deep-check audit
  ```

- [ ] Deprecar `deps-check` (manter por compatibilidade)

  ```makefile
  ## deps-check: Validação rápida (selo SHA-256) [DEPRECATED]
  deps-check:
   @echo "⚠️  Aviso: deps-check usa validação v2.2 (pode ter falsos positivos)"
   @echo "   Use: make deps-deep-check (v2.3 recomendado)"
   @$(PYTHON) scripts/ci/verify_deps.py
  ```

**Critérios de Aceitação:**

- ✅ `make deps-deep-check` executa sem erros em lockfile sincronizado
- ✅ `make validate` inclui deep check
- ✅ `make deps-check` mostra warning de deprecação

---

## 🚀 FASE 4: ATUALIZAÇÃO DO CI WORKFLOW

### 4.1. GitHub Actions Workflow

**Arquivo:** `.github/workflows/ci.yml`

- [ ] Substituir step "Check Lockfile Consistency"

  ```yaml
  - name: "Check Lockfile Deep Consistency (v2.3)"
    env:
      PYTHON_BASELINE: "3.10"
    run: |
      echo "🛡️ Validando sincronização de dependências (Deep Check)..."
      python -m scripts.core.dependency_guardian validate-deep dev --python-exec python3.10
      echo "✅ Lockfile em paridade total com PyPI (Protocolo v2.3)"
  ```

- [ ] (Opcional) Adicionar cache de pip-compile

  ```yaml
  - name: "Cache pip-compile results"
    uses: actions/cache@v5
    with:
      path: .cache/pip-compile
      key: deps-${{ hashFiles('requirements/dev.in', 'requirements/dev.txt') }}
  ```

**Critérios de Aceitação:**

- ✅ CI passa em lockfile sincronizado
- ✅ CI falha em lockfile desatualizado (tomli 2.3.0 vs 2.4.0)
- ✅ Mensagem de erro é clara e acionável

---

## 📚 FASE 5: DOCUMENTAÇÃO

### 5.1. README Principal

**Arquivo:** `README.md`

- [ ] Adicionar seção "Validação de Dependências (v2.3)"
  - [ ] Explicar diferença entre v2.2 (selo) e v2.3 (deep check)
  - [ ] Comandos de uso diário (`make validate`)
  - [ ] Troubleshooting (quando deep check falhar)

- [ ] Atualizar seção de comandos Make

  ```markdown
  ### Comandos de Desenvolvimento

  | Comando | Descrição |
  |---------|-----------|
  | `make validate` | Validação completa (lint + tipos + **deep deps check**) |
  | `make deps-deep-check` | Validação profunda de dependências (v2.3) |
  | `make requirements` | Sincronizar e selar lockfile |
  ```

**Critérios de Aceitação:**

- ✅ Documentação está clara para novos desenvolvedores
- ✅ Inclui exemplos de uso

---

### 5.2. Arquivo de Arquitetura

**Arquivo:** `docs/architecture/DEPENDENCY_GUARDIAN_v2.3.md` (criar novo)

- [ ] Documentar decisões de design
  - [ ] Por que deep check é necessário
  - [ ] Trade-offs de performance
  - [ ] Alternativas consideradas (dual-hash seal)

- [ ] Incluir diagramas de sequência
  - [ ] Fluxo de `make validate`
  - [ ] Fluxo de `make requirements`

**Critérios de Aceitação:**

- ✅ ADR (Architecture Decision Record) completo
- ✅ Diagramas incluídos

---

## 🔍 FASE 6: TESTES DE INTEGRAÇÃO

### 6.1. Teste End-to-End

**Cenário:** Simular falha de CI no GitHub Actions

- [ ] Criar branch de teste
- [ ] Fazer downgrade manual de dependência (tomli 2.4.0 → 2.3.0)
- [ ] Commitar e push
- [ ] Verificar que CI falha com mensagem clara
- [ ] Executar `make requirements` localmente
- [ ] Push novamente
- [ ] Verificar que CI passa

**Critérios de Aceitação:**

- ✅ CI detecta dessincronia em <5 minutos
- ✅ Mensagem de erro é acionável
- ✅ Fix é trivial (`make requirements`)

---

### 6.2. Teste de Regressão

**Cenário:** Garantir que não quebramos funcionalidades existentes

- [ ] Executar `make validate` em branch main (deve passar)
- [ ] Executar `python -m scripts.core.dependency_guardian validate dev` (v2.2, deve passar)
- [ ] Executar `python -m scripts.core.dependency_guardian seal dev` (deve funcionar)
- [ ] Verificar que selo SHA-256 ainda é injetado corretamente

**Critérios de Aceitação:**

- ✅ Todas as funcionalidades v2.2 continuam funcionando
- ✅ Selo SHA-256 é mantido para compatibilidade

---

## 📊 FASE 7: MÉTRICAS E MONITORAMENTO

### 7.1. Coletar Métricas de Performance

- [ ] Medir tempo de `make validate` antes e depois
  - [ ] Baseline (v2.2): `time make validate` (sem deep check)
  - [ ] Nova versão (v2.3): `time make validate` (com deep check)
  - [ ] Calcular delta

- [ ] Medir tempo do CI
  - [ ] Job "Quality" antes: ~X minutos
  - [ ] Job "Quality" depois: ~Y minutos
  - [ ] Verificar se está dentro do SLA (<10 minutos)

**Critérios de Aceitação:**

- ✅ Delta de performance documentado
- ✅ CI não ultrapassa 10 minutos

---

### 7.2. Alertas de Drift Frequente

- [ ] (Opcional) Adicionar log quando deep check detecta drift
  - [ ] Registrar qual dependência mudou
  - [ ] Enviar métrica para observability (se disponível)

**Critérios de Aceitação:**

- ✅ Logs são informativos
- ✅ Facilita debugging futuro

---

## 🚢 FASE 8: DEPLOY E ROLLOUT

### 8.1. Preparação para Merge

- [ ] Criar PR com todas as mudanças
  - [ ] Título: `feat(deps): implement Deep Consistency Check v2.3`
  - [ ] Descrição detalhada (link para relatório forense)
  - [ ] Screenshots de testes passando

- [ ] Code review
  - [ ] Pelo menos 1 aprovação de tech lead
  - [ ] Todos os comentários resolvidos

**Critérios de Aceitação:**

- ✅ PR aprovado
- ✅ CI verde
- ✅ Sem merge conflicts

---

### 8.2. Merge e Comunicação

- [ ] Merge para main
- [ ] Comunicar mudança ao time
  - [ ] Slack/Discord: "🚀 Dependency Guardian v2.3 deployed!"
  - [ ] Destacar que `make validate` agora é mais rigoroso
  - [ ] Pedir para time rodar `make requirements` se deep check falhar

- [ ] Monitorar primeiros dias
  - [ ] Verificar se CI está passando em todos os PRs
  - [ ] Coletar feedback do time

**Critérios de Aceitação:**

- ✅ Time notificado
- ✅ Sem regressões reportadas em 48h

---

## 🎯 CRITÉRIOS DE SUCESSO FINAL

### Funcionalidade

- [x] Deep check detecta drift de PyPI (testado com tomli 2.3.0 vs 2.4.0)
- [ ] Deep check passa quando lockfile está sincronizado
- [ ] Deep check falha quando lockfile está desatualizado
- [ ] Mensagens de erro são claras e acionáveis

### Performance

- [ ] `make validate` executa em <15 segundos (local)
- [ ] CI job "Quality" executa em <10 minutos (GitHub Actions)
- [ ] Cache de pip-compile reduz tempo em ~50% em hits

### Documentação

- [ ] README atualizado
- [ ] ADR criado em `docs/architecture/`
- [ ] Relatório forense arquivado em `docs/reports/`

### Qualidade

- [ ] Coverage de testes > 90%
- [ ] Nenhuma violação de lint/type-check
- [ ] Zero regressões em funcionalidades existentes

---

## 📅 ESTIMATIVA DE TEMPO

| Fase | Estimativa | Prioridade |
|------|------------|------------|
| 1. Implementação Core | 4-6 horas | 🔴 ALTA |
| 2. Testes Unitários | 2-3 horas | 🔴 ALTA |
| 3. Integração Makefile | 1 hora | 🟡 MÉDIA |
| 4. Atualização CI | 1-2 horas | 🔴 ALTA |
| 5. Documentação | 2-3 horas | 🟡 MÉDIA |
| 6. Testes Integração | 2 horas | 🟡 MÉDIA |
| 7. Métricas | 1 hora | 🟢 BAIXA |
| 8. Deploy | 1 hora | 🔴 ALTA |
| **TOTAL** | **14-19 horas** | |

**Sprint recomendado:** 1 sprint (2 semanas) com 1 desenvolvedor full-time

---

## 🔗 REFERÊNCIAS

- [Relatório Forense Completo](./FORENSE_DEPENDENCY_GUARDIAN_v2.2_INCIDENT_20260111.md)
- [Proposta de Implementação](./PROPOSTA_DEEP_CONSISTENCY_CHECK_v2.3.md)
- [Diagramas Técnicos](./FORENSE_DEPENDENCY_GUARDIAN_v2.2_DIAGRAMS.md)
- [Sumário Executivo](./SUMARIO_EXECUTIVO_INVESTIGACAO_FORENSE.md)

---

**Checklist criada por:** GitHub Copilot (Claude Sonnet 4.5)
**Data:** 2026-01-11
**Versão:** 1.0
