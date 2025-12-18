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

- **Hardware:** TBD (será atualizado após implementação do `scripts/benchmark_cortex.py`)
- **Dataset:** Arquivos Markdown com frontmatter YAML (~2KB cada)
- **Métricas:** Tempo médio de scan completo (5 execuções)

### Resultados Preliminares

| File Count | Sequential | Parallel (4 workers) | Speedup | Overhead |
|------------|-----------|----------------------|---------|----------|
| 10 files   | TBD ms    | TBD ms               | TBD x   | TBD ms   |
| 50 files   | TBD ms    | TBD ms               | TBD x   | TBD ms   |
| 100 files  | TBD ms    | TBD ms               | TBD x   | TBD ms   |

**Notas:**

- Speedup calculado como: `tempo_sequencial / tempo_paralelo`
- Overhead estimado: diferença entre tempo paralelo ideal e real
- _(Benchmarks serão atualizados na Etapa 2 - Prova de Valor)_

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
