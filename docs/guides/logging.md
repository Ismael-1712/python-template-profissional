---
id: logging-guide
title: Guia de Observabilidade e Logging
author: DevOps Team
date: 2025-12-03
type: guide
status: active
version: 1.0.0
linked_code:
  - scripts/utils/logger.py
  - scripts/utils/context.py
env_vars:
  LOG_LEVEL:
    description: Define o nível de verbosidade dos logs
    values: [DEBUG, INFO, WARNING, ERROR, CRITICAL]
    default: INFO
    required: false
    example: "LOG_LEVEL=DEBUG python scripts/cli/cortex.py"
  LOG_FORMAT:
    description: Define o formato de saída dos logs
    values: [text, json]
    default: text
    required: false
    example: "LOG_FORMAT=json python scripts/cli/cortex.py"
tags:
  - observability
  - logging
  - tracing
  - structured-logging
---

# Guia de Observabilidade e Logging

## 📋 Visão Geral

Este guia documenta o sistema de **Logging Estruturado com Distributed Tracing** implementado no projeto. O sistema fornece observabilidade completa através de Trace IDs automáticos, suporte a JSON structured logging e configuração flexível via variáveis de ambiente.

### Principais Características

- ✅ **Trace ID Automático**: Correlação de logs via UUID único por operação
- ✅ **JSON Structured Logging**: Formato parseable para ferramentas de APM
- ✅ **Thread-safe e Async-safe**: Usa `contextvars` do Python 3.7+
- ✅ **Separação de Streams**: INFO/DEBUG → stdout, WARNING/ERROR → stderr
- ✅ **Configuração via ENV**: Controle sem modificar código

---

## 🔧 Configuração

### Variáveis de Ambiente

#### `LOG_LEVEL`

Controla o nível de verbosidade dos logs.

**Valores aceitos:**

- `DEBUG` - Máximo detalhe (desenvolvimento)
- `INFO` - Informações gerais (padrão)
- `WARNING` - Apenas avisos e erros
- `ERROR` - Apenas erros
- `CRITICAL` - Apenas erros críticos

**Exemplo:**

```bash
# Ativar modo debug
LOG_LEVEL=DEBUG python scripts/cli/cortex.py

# Apenas erros (produção)
LOG_LEVEL=ERROR python scripts/cli/audit.py
```

---

#### `LOG_FORMAT`

Define o formato de saída dos logs.

**Valores aceitos:**

- `text` - Formato texto legível (padrão)
- `json` - JSON structured logging

**Exemplo:**

```bash
# Formato texto (padrão)
python scripts/cli/cortex.py

# Formato JSON (para integração com ELK, Splunk, etc.)
LOG_FORMAT=json python scripts/cli/cortex.py
```

---

## 🎯 Sistema de Trace ID

### Como Funciona

O **Trace ID** é um identificador único (UUID4) gerado automaticamente no início de cada operação. Ele é propagado automaticamente através de todas as chamadas de função dentro do mesmo contexto.

**Arquitetura:**

```
┌─────────────────────────────────────────────┐
│  Entry Point (CLI)                          │
│  with trace_context():                      │
│    ├─ Trace ID gerado: a1b2c3d4-...        │
│    ├─ function_1()                          │
│    │   └─ logger.info() [a1b2c3d4]         │
│    ├─ function_2()                          │
│    │   └─ logger.warning() [a1b2c3d4]      │
│    └─ function_3()                          │
│        └─ logger.error() [a1b2c3d4]        │
└─────────────────────────────────────────────┘
```

**Todos os logs compartilham o mesmo Trace ID = Correlação perfeita!**

---

### Uso Básico

#### 1. Em CLIs (Entry Points)

```python
from scripts.utils.context import trace_context
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__)

def main():
    """Entry point com Trace ID automático."""
    with trace_context():
        logger.info("CLI iniciado")
        process_command()
        logger.info("CLI finalizado")

if __name__ == "__main__":
    with trace_context():
        main()
```

**Output:**

```
2025-12-03 19:40:21,340 - [9f872d32-6557-4e5f-a44f-e31c1412ccdc] - __main__ - INFO - CLI iniciado
2025-12-03 19:40:21,341 - [9f872d32-6557-4e5f-a44f-e31c1412ccdc] - __main__ - INFO - CLI finalizado
```

---

#### 2. Em Módulos Internos

```python
from scripts.utils.logger import setup_logging
from scripts.utils.context import get_trace_id

logger = setup_logging(__name__)

def process_data(data):
    """Função que herda Trace ID automaticamente."""
    logger.info("Processando dados")

    # Trace ID está disponível
    trace_id = get_trace_id()
    logger.debug("Current Trace ID: %s", trace_id)

    # Processar...
    logger.info("Dados processados com sucesso")
```

**Não é necessário passar Trace ID explicitamente!** Ele é propagado via `contextvars`.

---

### Trace ID Customizado

Para propagar Trace ID de sistemas externos (ex: HTTP headers):

```python
from scripts.utils.context import trace_context

def handle_http_request(request):
    """Propaga Trace ID do HTTP header."""
    incoming_trace_id = request.headers.get("X-Trace-ID")

    with trace_context(incoming_trace_id):
        logger.info("Processando request com Trace ID externo")
        process_request(request)
```

---

## 📊 JSON Structured Logging

### Quando Usar

Use JSON logging quando:

- ✅ Integrar com ferramentas de APM (Datadog, New Relic, Elastic)
- ✅ Processar logs automaticamente
- ✅ Criar métricas e alertas baseados em logs
- ✅ Armazenar logs em bancos de dados NoSQL

### Formato de Saída

**Exemplo de Log JSON:**

```json
{
  "timestamp": "2025-12-03T22:40:28.253346+00:00",
  "level": "INFO",
  "logger": "scripts.cli.audit",
  "message": "Starting comprehensive code audit",
  "trace_id": "5d21eb17-a504-4ebc-9cbb-6d2ca86aa1c8",
  "location": "audit.py:195"
}
```

**Campos:**

- `timestamp` - ISO8601 com timezone UTC
- `level` - Nível do log (INFO, WARNING, ERROR, etc.)
- `logger` - Nome do módulo
- `message` - Mensagem do log
- `trace_id` - Identificador único da operação
- `location` - Arquivo e linha do código
- `exception` - Stacktrace (se presente)

---

### Uso em Produção

```bash
# Docker/Kubernetes
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO

# Systemd
Environment="LOG_FORMAT=json"
Environment="LOG_LEVEL=WARNING"

# GitHub Actions
- name: Run audit
  env:
    LOG_FORMAT: json
    LOG_LEVEL: INFO
  run: python scripts/cli/audit.py
```

---

### Parsing de Logs JSON

#### Com `jq`

```bash
# Filtrar por Trace ID
cat audit.log | jq 'select(.trace_id == "5d21eb17-a504")'

# Filtrar por nível ERROR
cat audit.log | jq 'select(.level == "ERROR")'

# Contar logs por logger
cat audit.log | jq '.logger' | sort | uniq -c

# Extrair apenas mensagens
cat audit.log | jq -r '.message'
```

#### Com Python

```python
import json

with open("audit.log") as f:
    for line in f:
        log = json.loads(line)
        if log["level"] == "ERROR":
            print(f"{log['timestamp']}: {log['message']}")
```

---

## 🔍 Troubleshooting e Debug

### Rastreando uma Operação Específica

**Cenário:** Usuário reporta erro com Trace ID `a1b2c3d4-5678`.

```bash
# Formato texto
grep "a1b2c3d4-5678" cortex.log

# Formato JSON
cat cortex.log | jq 'select(.trace_id | startswith("a1b2c3d4"))'
```

**Resultado:** Todos os logs dessa operação, em ordem cronológica.

---

### Debug de Fluxo Completo

```bash
# Ativar modo DEBUG + JSON
LOG_LEVEL=DEBUG LOG_FORMAT=json python scripts/cli/cortex.py map

# Processar output
cat cortex.log | jq 'select(.level == "DEBUG")' > debug_flow.json
```

---

### Identificar Gargalos

```bash
# Timestamp de cada operação
cat audit.log | jq -r '[.timestamp, .trace_id, .message] | @tsv' | sort
```

---

## 📚 Exemplos Práticos

### Exemplo 1: CLI com Logging Estruturado

```python
#!/usr/bin/env python3
"""My CLI with structured logging."""

import typer
from scripts.utils.context import trace_context
from scripts.utils.logger import setup_logging

app = typer.Typer()
logger = setup_logging(__name__, log_file="mycli.log")

@app.command()
def process(file_path: str):
    """Process a file with automatic tracing."""
    logger.info("Processing file: %s", file_path)

    try:
        # Processar arquivo
        result = do_processing(file_path)
        logger.info("Processing completed successfully")
        return result

    except Exception as e:
        logger.exception("Processing failed: %s", str(e))
        raise typer.Exit(1)

def main():
    """Entry point with trace context."""
    with trace_context():
        app()

if __name__ == "__main__":
    with trace_context():
        app()
```

---

### Exemplo 2: Propagação entre Módulos

**`main.py`:**

```python
from scripts.utils.context import trace_context
from scripts.utils.logger import setup_logging
from my_module import process_data

logger = setup_logging(__name__)

with trace_context() as trace_id:
    logger.info("Starting batch job")
    process_data()
    logger.info("Batch job completed")
```

**`my_module.py`:**

```python
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__)

def process_data():
    """Esta função herda o Trace ID automaticamente."""
    logger.info("Processing data")
    # Trabalho...
    logger.info("Data processed")
```

**Output (mesmo Trace ID):**

```
2025-12-03 19:40:21,340 - [abc-123] - __main__ - INFO - Starting batch job
2025-12-03 19:40:21,341 - [abc-123] - my_module - INFO - Processing data
2025-12-03 19:40:21,342 - [abc-123] - my_module - INFO - Data processed
2025-12-03 19:40:21,343 - [abc-123] - __main__ - INFO - Batch job completed
```

---

### Exemplo 3: Integração com CI/CD

**`.github/workflows/test.yml`:**

```yaml
name: Tests with Structured Logging

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run tests with JSON logging
        env:
          LOG_FORMAT: json
          LOG_LEVEL: DEBUG
        run: |
          python -m pytest tests/ -v

      - name: Upload logs as artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-logs
          path: "*.log"
```

---

## 🏗️ Arquitetura Técnica

### Componentes

```
┌─────────────────────────────────────────────────────┐
│  scripts/utils/context.py                           │
│  ├─ ContextVar storage (thread-safe)                │
│  ├─ get_trace_id() → UUID4 ou contexto              │
│  ├─ set_trace_id(custom_id)                         │
│  └─ trace_context() → Context Manager               │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  scripts/utils/logger.py                            │
│  ├─ TraceIDFilter → Injeta trace_id em LogRecord    │
│  ├─ JSONFormatter → Formata como JSON               │
│  ├─ InfoHandler → stdout (INFO/DEBUG)               │
│  ├─ ErrorHandler → stderr (WARNING/ERROR)           │
│  └─ setup_logging() → Configura tudo                │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  Entry Points (CLIs)                                │
│  └─ with trace_context(): app()                     │
└─────────────────────────────────────────────────────┘
```

---

### Thread Safety

O sistema usa `contextvars.ContextVar` (Python 3.7+), que é:

- ✅ **Thread-safe**: Cada thread tem seu próprio contexto
- ✅ **Async-safe**: Funciona com `asyncio` e `async/await`
- ✅ **Propagation-aware**: Herda contexto em tarefas filhas

**Exemplo Async:**

```python
import asyncio
from scripts.utils.context import trace_context
from scripts.utils.logger import setup_logging

logger = setup_logging(__name__)

async def async_task(name):
    logger.info("Task %s started", name)
    await asyncio.sleep(1)
    logger.info("Task %s completed", name)

async def main():
    with trace_context():
        # Todas as tasks compartilham o mesmo Trace ID
        await asyncio.gather(
            async_task("A"),
            async_task("B"),
            async_task("C"),
        )

asyncio.run(main())
```

---

## 🚨 Boas Práticas

### ✅ DO

- ✅ Sempre use `with trace_context()` em entry points
- ✅ Use `logger.info("Message: %s", value)` ao invés de f-strings
- ✅ Configure JSON logging em produção
- ✅ Use `LOG_LEVEL=DEBUG` apenas em desenvolvimento
- ✅ Inclua contexto relevante nas mensagens de log

### ❌ DON'T

- ❌ Não use `print()` - sempre use logger
- ❌ Não logue senhas ou dados sensíveis
- ❌ Não use f-strings em logs (lazy evaluation é melhor)
- ❌ Não crie múltiplos `trace_context()` sem necessidade
- ❌ Não ignore exceptions sem logar

---

## 🔗 Links Relacionados

- **Código:** [`scripts/utils/logger.py`](../../scripts/utils/logger.py)
- **Contexto:** [`scripts/utils/context.py`](../../scripts/utils/context.py)
- **Exemplo:** [`demo_logging.py`](../../demo_logging.py)
- **Arquitetura:** [`docs/architecture/CORTEX_INDICE.md`](../architecture/CORTEX_INDICE.md)

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Consulte este guia primeiro
2. Execute `demo_logging.py` para exemplos práticos
3. Verifique os logs em modo DEBUG
4. Abra uma issue no repositório

---

**Última atualização:** 2025-12-03
**Versão:** 1.0.0
**Mantido por:** DevOps Engineering Team
