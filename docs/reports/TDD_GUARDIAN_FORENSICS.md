---
id: tdd-guardian-forensics
type: report
status: active
version: 1.0.0
author: Engineering Team
date: '2026-01-04'
context_tags:
  - tdd
  - testing
  - technical-debt
  - automation
linked_code:
  - scripts/hooks/tdd_guardian.py
  - scripts/git-hooks/pre-commit
title: TDD Guardian - Análise Forense e Viabilidade de Expansão
---

# 🛡️ TDD GUARDIAN - ANÁLISE FORENSE E VIABILIDADE DE EXPANSÃO

**Data da Análise:** 03 de Janeiro de 2026
**Status:** Implementado (Fase 1 - Warn Only)

---

## 🔍 1. AUTÓPSIA DO TDD GUARDIAN

### 1.1 O Que é?

O TDD Guardian é um mecanismo de defesa em duas camadas que impede a entrada de
código sem testes:

1. **Camada Estrutural (Pre-Commit):** Verifica se para cada arquivo `src/X.py`
   existe um `tests/test_X.py`.
2. **Camada de Cobertura (CI):** Verifica se as linhas novas têm 100% de
   cobertura (via `diff-cover`).

### 1.2 O Problema Detectado (Cegueira de Scripts)

Originalmente, a ferramenta monitorava apenas o diretório `src/`. Uma análise
forense revelou que o diretório `scripts/`, crítico para a automação do projeto,
estava **invisível** para o guardião.

---

## 📊 2. LEVANTAMENTO FORENSE: O "CAOS" EM SCRIPTS/

A investigação revelou um cenário de alto risco e débito técnico acumulado:

- **Total de Arquivos Python em `scripts/`:** ~140 arquivos.
- **Cobertura Padronizada:** 0%. Nenhum segue o padrão `tests/scripts/test_X.py`.
- **Testes Dispersos:** Alguns scripts críticos (`doctor.py`, `install_dev.py`)
  possuem testes, mas eles estão "escondidos" em locais não padronizados
  (ex: `tests/test_doctor_hooks.py`), dificultando a rastreabilidade automática.

### Arquivos Críticos sem Teste Direto (Amostra)

1. `scripts/git_sync/sync_logic.py` (Core da sincronia Git)
2. `scripts/utils/safe_pip.py` (Gerenciador de pacotes seguro)
3. `scripts/audit/reporter.py` (Gerador de relatórios de segurança)

---

## 🧪 3. ESTRATÉGIA DE EXPANSÃO (SOLUÇÃO IMPLEMENTADA)

Para resolver este problema sem paralisar a equipe (bloqueando 140 arquivos de
uma vez), adotamos a estratégia de **"Soft Launch"**:

### 3.1 Dual-Mode Enforcement

Refatoramos o Guardian para suportar políticas diferentes por diretório:

| Diretório | Política | Comportamento ao Falhar | Objetivo |
| :--- | :--- | :--- | :--- |
| `src/` | **STRICT** | ❌ Bloqueia Commit | Manter qualidade zero-defect |
| `scripts/` | **WARN-ONLY** | ⚠️ Emite Aviso | Dar visibilidade ao débito sem travar |

### 3.2 Nova Estrutura de Testes

A partir de agora, testes para scripts devem espelhar a estrutura de pastas:

- Script: `scripts/cli/doctor.py`
- Teste: `tests/scripts/cli/test_doctor.py`

---

## 📈 4. STATUS ATUAL (PÓS-IMPLEMENTAÇÃO V2)

### 4.1 Fase 1 Concluída ✅

A implementação da **Fase 1 - Warn Only para Scripts** foi concluída com sucesso
em Janeiro de 2026. As seguintes mudanças foram aplicadas:

**Alterações no TDD Guardian:**

- ✅ Refatoração do hook de pre-commit para suportar múltiplas políticas
- ✅ Implementação do modo `WARN_ONLY` para o diretório `scripts/`
- ✅ Manutenção do modo `STRICT` para o diretório `src/`
- ✅ Estrutura de testes padronizada: `tests/scripts/` espelha `scripts/`

**Benefícios Observados:**

- **Visibilidade:** Desenvolvedores agora recebem avisos claros quando adicionam
  scripts sem testes
- **Não-Bloqueante:** Fluxo de trabalho continua fluido, sem interrupções
  disruptivas
- **Rastreabilidade:** Métrica de débito técnico agora é mensurável
  (140 arquivos sem cobertura padrão)

### 4.2 Próximas Fases (Roadmap)

**Fase 2 - Pagamento de Débito (Q1 2026):**

- Migrar testes existentes para a estrutura padronizada `tests/scripts/`
- Priorizar scripts críticos (git_sync, audit, utils)
- Meta: Reduzir débito de 140 para <50 arquivos

**Fase 3 - Endurecimento (Q2 2026):**

- Quando cobertura de scripts atingir 70%, mudar política para `STRICT`
- Implementar exceções configuráveis para scripts legados específicos
- Adicionar métricas de tendência no dashboard de auditoria

**Fase 4 - Cobertura Total (Q3 2026):**

- 100% dos scripts críticos com testes
- Guardian em modo `STRICT` universal
- Zero-tolerance para código sem teste

### 4.3 Métricas de Acompanhamento

Para monitorar o progresso, use:

```bash
# Ver avisos do Guardian
git commit -a  # Observar warnings de scripts sem teste

# Gerar relatório de cobertura de scripts
make test-coverage

# Dashboard de métricas
make audit
```

---

## 🏁 CONCLUSÃO E PRÓXIMOS PASSOS

A ferramenta evoluiu de um script simples para uma plataforma de governança de
testes configurável. A abordagem gradual (warn-only) permite adoção sem fricção,
mantendo visibilidade total do débito técnico.

**Ações Imediatas para o Time:**

1. **Novos Scripts:** Devem nascer com testes em `tests/scripts/...`. O Guardian
   avisará se você esquecer.
2. **Pagamento de Débito:** Migrar gradualmente os testes "órfãos" para a nova
   estrutura padronizada.
3. **Endurecimento:** Futuramente, quando a cobertura de scripts subir, a
   política de `scripts/` será alterada para **STRICT**.

**Princípios de Design:**

- **Não Bloqueante:** Avisos informativos em vez de barreiras absolutas
- **Mensurável:** Débito técnico quantificável
- **Incremental:** Melhorias progressivas sem refatoração massiva

---

**Referências:**

- Implementação: `scripts/git-hooks/pre-commit`
- Configuração: `scripts/git-hooks/tdd_guardian.py`
- Testes: `tests/scripts/` (estrutura em construção)
