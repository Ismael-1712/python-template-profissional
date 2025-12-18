---
id: arch-perf-001
description: Considerações de Performance do Sistema Cortex
type: arch
version: 1.0.0
status: active
tags: [performance, concurrency, optimization, cortex]
author: SRE & Performance Engineering Team
date: 2025-12-17
---

# Performance & Concurrency - Cortex System

> ⚠️ **STATUS (v0.1.0):** Parallel processing **DISABLED** due to performance regression.
> Empirical benchmarks show 34% slowdown (0.66x speedup) with `ThreadPoolExecutor` due to GIL contention.
> Sequential processing is enforced for all workloads (`PARALLEL_THRESHOLD = sys.maxsize`).
> See [Performance Analysis](#performance-analysis--action-items) for details and future roadmap.

## Visão Geral

Este documento descreve as estratégias de otimização de performance implementadas
no sistema CORTEX, com foco em paralelização de operações I/O e garantias de
thread-safety para ambientes concorrentes.

---

## KnowledgeScanner Parallelization

### Estratégia de Paralelização

O `KnowledgeScanner` implementa paralelização automática baseada em threshold
para otimizar o processamento de grandes bases de conhecimento:

**Threshold Decision:**

- **< 10 arquivos:** Processamento sequencial (evita overhead de threads)
- **≥ 10 arquivos:** Processamento paralelo (até 4 workers)

**Justificativa:**

- Para conjuntos pequenos (<10 arquivos), o overhead de criação do `ThreadPoolExecutor`
  excede o ganho de paralelização
- Para conjuntos grandes (≥10 arquivos), os ganhos de I/O paralelo compensam o overhead
- Limite de 4 workers evita saturação de CPU e contenção de recursos

### Configuração de Workers

```python
max_workers = min(4, os.cpu_count() or 1)
```

**Racionalidade:**

- **4 workers:** Balanceamento entre throughput e contenção de recursos
- Baseado em benchmarks empíricos com cargas típicas de documentação
- Pode ser aumentado em hardware high-end (futuro: tornar configurável)

---

## Thread Safety Guarantees

### MemoryFileSystem (v1.1.0+)

O `MemoryFileSystem` implementa thread-safety completa através de `threading.RLock`:

**Operações Protegidas:**

- ✅ `read_text()` - Leituras concorrentes seguras
- ✅ `write_text()` - Escritas sem race conditions
- ✅ `exists()` - Verificações atômicas
- ✅ `mkdir()` - Criação de diretórios thread-safe
- ✅ `glob()` / `rglob()` - Buscas concorrentes consistentes
- ✅ `copy()` - Cópias atômicas

**Limitações Conhecidas:**

- Check-then-act patterns requerem sincronização externa:

  ```python
  # ❌ NÃO é atômico (requer lock externo)
  if not fs.exists(path):
      fs.write_text(path, "data")  # Pode falhar se outro thread criou

  # ✅ Atômico (internamente protegido)
  try:
      fs.read_text(path)
  except FileNotFoundError:
      fs.write_text(path, "data")
  ```

### RealFileSystem

Thread-safety delegada ao sistema operacional:

- Operações de arquivo são atômicas no nível do kernel
- Escritas concorrentes no mesmo arquivo podem causar corrupção (limitação do OS)
- **Recomendação:** Use `scripts.utils.atomic` para escritas críticas

---

## Benchmarks de Performance

### Metodologia

Benchmarks executados em:

- **Hardware:** Linux 6.6.87.2-WSL2, x86_64, 16 CPU cores
- **Python:** 3.12.12
- **Dataset:** Arquivos Markdown com frontmatter YAML (~2KB cada)
- **Métricas:** Tempo médio de scan completo (5 execuções por cenário)
- **Script:** `scripts/benchmark_cortex_perf.py`

### Resultados Empíricos (2025-12-17)

| File Count | Sequential | Parallel (4 workers) | Speedup | Overhead |
|------------|-----------|----------------------|---------|----------|
| 10 files   |    5.29 ms |               8.84 ms |   0.60x |   0.00 ms |
| 50 files   |   21.17 ms |              32.37 ms |   0.65x |   0.00 ms |
| 100 files  |   42.47 ms |              60.19 ms |   0.71x |   0.00 ms |
| 500 files  |  207.16 ms |             301.57 ms |   0.69x |   0.00 ms |

**Notas Críticas:**

- ⚠️ **Speedup < 1.0:** Modo paralelo está **mais lento** que sequencial em todos os cenários
- **Causa Raiz:** Overhead de `ThreadPoolExecutor` + GIL (Global Interpreter Lock) do Python
- **I/O Bound Myth:** Embora I/O seja assíncrono no OS, o parsing de YAML/Markdown é CPU-bound
- **Recomendação Imediata:** Aumentar threshold de 10 para **100+ arquivos** ou desabilitar paralelo
- **Speedup calculado como:** `tempo_sequencial / tempo_paralelo` (valores <1.0 = regressão)
- _(Benchmarks executados em 2025-12-17 via `scripts/benchmark_cortex_perf.py`)_

---

## Performance Analysis & Action Items

### Critical Findings from Benchmarks

**1. Parallel Processing Regression**

Os benchmarks empíricos revelam que a implementação atual de paralelização está
causando **degradação de performance** em vez de aceleração:

- **Speedup médio:** 0.66x (regressão de ~34%)
- **Pior caso:** 10 arquivos = 0.60x (40% mais lento)
- **Melhor caso:** 100 arquivos = 0.71x (ainda 29% mais lento)

**Root Cause Analysis:**

1. **GIL Contention:** Python's Global Interpreter Lock serializa execução de bytecode,
   mesmo em threads I/O-bound. O parsing de YAML/Markdown é suficientemente CPU-bound
   para criar contenção.

2. **Thread Overhead:** Criação do `ThreadPoolExecutor`, scheduling, e context switching
   têm custo fixo que excede os ganhos em datasets pequenos/médios.

3. **False I/O Assumption:** Assumiu-se que leitura de arquivos era o gargalo, mas
   benchmarks mostram que parsing (CPU) domina o tempo total.

**2. Threshold Inadequado**

O threshold atual de **10 arquivos** para ativar paralelização é muito baixo:

- Com 10 arquivos, paralelo é 40% mais lento
- Mesmo com 500 arquivos, paralelo ainda é 31% mais lento
- Dados sugerem que threshold deveria ser **muito maior** ou desabilitado

**3. Ações Recomendadas (Prioridade Decrescente)**

| Prioridade | Ação | Impacto Estimado | Complexidade |
|------------|------|------------------|--------------|
| **P0** | Desabilitar paralelização (threshold = ∞) | +34% speedup imediato | Trivial (1 linha) |
| **P1** | Implementar com `multiprocessing` (bypass GIL) | +50-100% speedup | Média (refactor) |
| **P2** | Profile CPU vs I/O ratio com `cProfile` | Dados para decisões | Baixa (adicionar logging) |
| **P3** | Implementar async I/O com `asyncio` + `aiofiles` | +20-40% speedup | Alta (rewrite) |

**Decisão Executiva:**

Para **Etapa 3 (Otimização)**, recomenda-se:

1. Remover paralelização atual (1 linha de código)
2. Re-implementar com `multiprocessing.Pool` se necessário para bases >1000 arquivos
3. Adicionar flag `--max-workers` para usuários experimentarem

---

## Known Limitations

### Configurabilidade

- **`max_workers=4` hardcoded:** Não configurável via CLI ou variável de ambiente
  - **Impacto:** Usuários com hardware high-end não podem aumentar paralelismo
  - **Workaround:** Editar `knowledge_scanner.py` diretamente (não recomendado)

### Paralelização de Links

- **Link extraction é sequencial:** Cada worker processa links de forma independente
  - **Impacto:** Para arquivos com muitos links, pode haver gargalo
  - **Mitigação planejada:** Paralelizar `LinkAnalyzer.extract_links()` na Etapa 3

### Memória

- **Todo conteúdo em RAM:** Arquivos grandes podem causar pressão de memória
  - **Impacto:** Bases de conhecimento com centenas de arquivos grandes (>1MB)
  - **Mitigação:** Limitar `cached_content` ou implementar lazy loading

---

## Testing Strategy

### Cobertura de Testes de Concorrência

Implementado em `tests/test_cortex_concurrency.py`:

1. **`test_parallel_integrity`**
   - Valida que 50 arquivos retornam exatamente 50 entradas
   - Detecta duplicatas ou perdas de dados

2. **`test_concurrent_scans_shared_filesystem`**
   - Stress test: 4 scans simultâneos no mesmo FS
   - Valida RLock do MemoryFileSystem

3. **`test_parallel_determinism`**
   - Executa scan 10 vezes e compara resultados
   - Garante que paralelismo não introduz não-determinismo

4. **`test_threshold_sequential_processing`**
   - Valida que 9 arquivos usam modo sequencial
   - Verifica logs de debug

5. **`test_threshold_parallel_processing`**
   - Valida que 50 arquivos usam modo paralelo
   - Verifica logs de worker count

### Execução de Testes

```bash
# Testes sequenciais
pytest tests/test_cortex_concurrency.py -v

# Stress test paralelo (detecta race conditions raras)
pytest tests/test_cortex_concurrency.py -n 8 --count=10

# Com cobertura
pytest tests/test_cortex_concurrency.py \
  --cov=scripts.core.cortex.knowledge_scanner \
  --cov-report=term-missing
```

---

## Future Optimizations

### Roadmap de Performance

- [ ] **P1:** Paralelizar `LinkAnalyzer.extract_links()` (Etapa 3)
  - Benefício: ~20% speedup em arquivos link-heavy
  - Complexidade: Média (requer refatoração do analyzer)

- [ ] **P2:** Tornar `max_workers` configurável via CLI
  - Benefício: Flexibilidade para diferentes ambientes
  - Implementação: Adicionar flag `--max-workers` ao `cortex scan`

- [ ] **P3:** Implementar cache de parsed entries
  - Benefício: Evitar re-parsing em scans repetidos
  - Complexidade: Alta (requer invalidação de cache inteligente)

- [ ] **P4:** Lazy loading de `cached_content`
  - Benefício: Reduzir consumo de memória em bases grandes
  - Trade-off: Pode aumentar latência em operações de leitura

### Considerações para Scaling

Para bases de conhecimento com **>500 arquivos**:

- Considere aumentar `max_workers` para 8-16 (requer edição manual)
- Monitore consumo de memória (cada entry ~5-10KB em RAM)
- Implemente batching se enfrentar `MemoryError`

---

## References

- **Código Fonte:** [`scripts/core/cortex/knowledge_scanner.py`](../../scripts/core/cortex/knowledge_scanner.py)
- **Testes:** [`tests/test_cortex_concurrency.py`](../../tests/test_cortex_concurrency.py)
- **FileSystem Adapter:** [`scripts/utils/filesystem.py`](../../scripts/utils/filesystem.py)

---

**Última Atualização:** 2025-12-17
**Versão:** 1.0.0
**Autor:** SRE & Performance Engineering Team
