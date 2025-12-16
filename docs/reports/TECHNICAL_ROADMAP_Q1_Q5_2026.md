---
id: technical-roadmap-q1-q5-2026
type: reference
status: active
version: 1.0.0
author: GEM & SRE Team
date: '2025-12-16'
tags: [roadmap, technical-debt, ux, observability, sre]
context_tags: [planning, maintenance, priorities]
related_docs:
  - docs/architecture/OBSERVABILITY.md
  - docs/architecture/SECURITY_STRATEGY.md
  - docs/architecture/PLATFORM_ABSTRACTION.md
  - docs/guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md
---

# Roadmap Técnico de Manutenção (Q1-Q5 2026)

## 📋 Visão Geral

Este documento consolida o plano de manutenção e evolução pós-Sprint V3.0, derivado do [Relatório de Handover de 05/12/2025](#fonte). As tarefas estão priorizadas por **impacto em UX, segurança e observabilidade**.

> **Contexto:** A fundação arquitetural está completa (FileSystemAdapter, PlatformStrategy, Pydantic V2, Trace ID). Este roadmap foca em **refinamento de UX operacional** e **expansão SRE**.

---

## 🔴 PRIORIDADE ALTA (Correções de UX e Débitos Críticos)

### [Q4] Visibilidade de Sanitização (Anti-Cegueira) 🚨

**Problema:**
- O `sanitize_env` ([scripts/utils/security.py](../../scripts/utils/security.py)) remove variáveis silenciosamente (log DEBUG).
- Usuários não entendem por que testes falham quando variáveis são bloqueadas.
- **Impacto UX:** Desenvolvedores gastam tempo debugando erros criptográficos ("variável X não encontrada") sem saber que foram intencionalmente filtradas.

**Solução:**
1. Emitir **WARNING** ao final da execução se variáveis foram bloqueadas:
   ```python
   if blocked_vars:
       logger.warning(
           f"⚠️  {len(blocked_vars)} variáveis bloqueadas por segurança. "
           f"Execute com LOG_LEVEL=DEBUG para ver detalhes."
       )
   ```
2. Adicionar flag `--verbose` em CLIs críticos (`test-mock-generator`, `code-audit`) para exibir variáveis bloqueadas.

**Critério de Sucesso:**
- Teste manual: Executar `test-mock-generator` com `AWS_SECRET_KEY` no ambiente e verificar WARNING visível.
- Sem false positives: Ambientes limpos (sem segredos) não emitem avisos.

**Estimativa:** 2h (1h implementação + 1h testes)

**Responsável:** Next Engineer/AI

**Links:**
- [SECURITY_STRATEGY.md](../architecture/SECURITY_STRATEGY.md) - Contexto de sanitização
- [scripts/utils/security.py](../../scripts/utils/security.py) - Implementação atual

---

### [Q5] Alerta de Compatibilidade Windows 🪟

**Problema:**
- `PlatformStrategy` no Windows faz _no-op_ para `chmod` e `fsync`.
- Usuários assumem que arquivos estão durabilizados quando não estão.
- **Impacto Segurança:** Perda de dados em crash do sistema.

**Solução:**
1. Emitir aviso único na inicialização se detectar Windows:
   ```python
   if sys.platform == "win32":
       logger.warning(
           "⚠️  Windows detectado. Operações de atomicidade (fsync) "
           "e permissões (chmod) têm limitações. "
           "Ver: docs/architecture/PLATFORM_ABSTRACTION.md#windows"
       )
   ```
2. Adicionar seção específica em [PLATFORM_ABSTRACTION.md](../architecture/PLATFORM_ABSTRACTION.md) sobre limitações Windows.

**Critério de Sucesso:**
- Aviso aparece exatamente uma vez por execução (não em cada operação).
- Documentação clara sobre o que funciona e o que não funciona.

**Estimativa:** 3h (2h implementação + 1h documentação)

**Responsável:** Next Engineer/AI

**Links:**
- [PLATFORM_ABSTRACTION.md](../architecture/PLATFORM_ABSTRACTION.md) - Arquitetura atual
- [scripts/utils/platform_strategy.py](../../scripts/utils/platform_strategy.py) - Código

---

### [Q1] Tipagem Completa de Testes 📝

**Problema:**
- Apenas 3 de 12 arquivos de teste críticos têm conformidade com `mypy --strict`.
- **Débito:** Testes não validam tipos, permitindo bugs sutis.

**Solução:**
1. Identificar os 9 arquivos de teste pendentes:
   ```bash
   grep -L "from __future__ import annotations" tests/test_*.py
   ```
2. Aplicar o **Protocolo de Fracionamento** (1 arquivo por commit):
   - Adicionar `from __future__ import annotations`
   - Tipar parâmetros e retornos
   - Executar `mypy tests/test_X.py --strict` e corrigir

**Critério de Sucesso:**
- `make validate` passa sem erros de tipo em **todos** os arquivos `tests/test_*.py`.

**Estimativa:** 9h (1h por arquivo × 9)

**Responsável:** Next Engineer/AI

**Referências:**
- [REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md](../guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md) - Metodologia

---

### [Q2] Redução de Complexidade Ciclomática 🔧

**Problema:**
- Métodos `analyze_file` e alguns em `doctor.py` excedem complexidade 10.
- **Impacto:** Difícil testar, manter e entender.

**Solução:**
1. Executar auditoria de complexidade:
   ```bash
   radon cc scripts/ -a -nb
   ```
2. Para cada método complexo (CC > 10):
   - Aplicar Extract Method (quebrar em funções menores)
   - Aplicar Extract Guard Clause (simplificar condicionais)
3. **Regra:** Máximo CC 8 (tolerância para lógica de negócio).

**Critério de Sucesso:**
- `radon cc scripts/ -a` não reporta nenhuma função com CC > 10.

**Estimativa:** 6h (depende de quantos métodos)

**Responsável:** Next Engineer/AI

---

## 🟡 PRIORIDADE MÉDIA (Expansão SRE)

### [P17] Integração HTTP e Métricas 📊

**Objetivo:** Padronizar chamadas HTTP externas com propagação de Trace ID e métricas.

**Implementação:**
1. Criar `scripts/utils/http_client.py`:
   ```python
   class TracedHTTPClient:
       def request(self, method, url, **kwargs):
           trace_id = get_trace_id()
           headers = kwargs.get("headers", {})
           headers["X-Trace-ID"] = trace_id
           # ... implementação
   ```
2. Adicionar contadores de sucesso/falha:
   - `http_requests_total{status, endpoint}`
   - `http_request_duration_seconds{endpoint}`

**Critério de Sucesso:**
- Todas as chamadas HTTP em `scripts/` propagam `X-Trace-ID`.
- Métricas exportáveis em formato Prometheus.

**Estimativa:** 8h

**Status:** 📋 Planejado (YAGNI - implementar quando houver chamadas HTTP externas)

**Referências:**
- [OBSERVABILITY.md](../architecture/OBSERVABILITY.md#padrão-de-chamadas-externas-http)

---

### [P18] Gestão de Logs em Produção 📁

**Objetivo:** Evitar discos cheios em ambientes de produção.

**Implementação:**
1. Adicionar `RotatingFileHandler` em `scripts/utils/logger.py`:
   ```python
   handler = RotatingFileHandler(
       "logs/app.log",
       maxBytes=50*1024*1024,  # 50MB
       backupCount=5
   )
   ```
2. Adicionar configuração via variável de ambiente (`LOG_ROTATION_SIZE`, `LOG_BACKUP_COUNT`).

**Critério de Sucesso:**
- Logs rotacionam automaticamente após 50MB.
- Máximo 5 arquivos de backup (250MB total).

**Estimativa:** 4h

**Status:** 📋 Planejado

---

## 🟣 PRIORIDADE BAIXA (Inovação)

### [P19] OpenTelemetry Integration 🔭

**Objetivo:** Tracing distribuído padrão OpenTelemetry.

**Implementação:**
- Substituir `contextvars` por OpenTelemetry Tracer.
- Exportar spans para Jaeger/Zipkin.

**Status:** 📋 Futuro (apenas se houver microservices)

**Estimativa:** 16h

---

### [P22] Internacionalização (i18n) 🌍

**Objetivo:** Tornar mensagens de erro traduzíveis.

**Implementação:**
- Usar `babel` (já configurado em `babel.cfg`).
- Extrair strings para `locales/messages.pot`.

**Status:** 📋 Futuro (apenas se houver internacionalização real)

**Estimativa:** 12h

---

## 📊 Resumo de Prioridades

| Prioridade | Tarefas | Estimativa Total | Prazo Sugerido |
|-----------|---------|------------------|----------------|
| 🔴 Alta | Q4, Q5, Q1, Q2 | 20h | Sprint Q1 2026 |
| 🟡 Média | P17, P18 | 12h | Sprint Q2 2026 |
| 🟣 Baixa | P19, P22 | 28h | Backlog |

---

## 🎯 Recomendações

1. **Começar por Q4 (Visibilidade de Sanitização)**: Maior impacto UX com menor esforço.
2. **Q1 (Tipagem de Testes)**: Aplicar Protocolo de Fracionamento (1 arquivo/dia).
3. **Não implementar P17/P18** até haver necessidade real (princípio YAGNI).
4. **Validar sempre:** Após cada tarefa, executar `make validate` antes de commit.

---

## 📚 Fonte

Este roadmap foi extraído do **Relatório Técnico de Evolução** (GEM & Humano, 05/12/2025), seção "4. 🗺️ AONDE PRETENDEMOS IR".

---

**Última Atualização:** 2025-12-16
**Próxima Revisão:** Q1 2026 (após completar tarefas de Alta Prioridade)
