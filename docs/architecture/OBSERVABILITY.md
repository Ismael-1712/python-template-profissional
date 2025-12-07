---
id: arch-observability
title: Padrões de Observabilidade
type: arch
status: active
version: 1.0.0
author: SRE Team
date: 2025-12-07
tags: [observability, tracing, metrics, http, distributed-systems]
related:
  - docs/guides/logging.md
  - docs/guides/ENGINEERING_STANDARDS.md
---

# Padrões de Observabilidade

Este documento define os padrões arquiteturais para observabilidade de sistemas distribuídos no projeto. A observabilidade é construída sobre três pilares: **Logs**, **Métricas** e **Traces**.

---

## 📚 Índice

1. [Visão Geral](#visão-geral)
2. [Sistema de Trace ID](#sistema-de-trace-id)
3. [Padrão de Chamadas Externas (HTTP)](#padrão-de-chamadas-externas-http)
4. [Sistema de Métricas](#sistema-de-métricas)
5. [Casos de Uso](#casos-de-uso)
6. [Referências](#referências)

---

## 🎯 Visão Geral

### Três Pilares da Observabilidade

```
┌─────────────────────────────────────────────────────────┐
│                   OBSERVABILIDADE                        │
├─────────────────┬─────────────────┬─────────────────────┤
│      LOGS       │    METRICS      │      TRACES         │
├─────────────────┼─────────────────┼─────────────────────┤
│ • Eventos       │ • Contadores    │ • Trace IDs         │
│ • Contexto      │ • Histogramas   │ • Spans             │
│ • Timestamps    │ • Gauges        │ • Correlação        │
└─────────────────┴─────────────────┴─────────────────────┘
```

### Estado Atual de Implementação

| Componente | Status | Localização |
|-----------|--------|-------------|
| **Trace ID Infrastructure** | ✅ **Implementado** | `scripts/utils/context.py` |
| **Structured Logging** | ✅ **Implementado** | `scripts/utils/logger.py` |
| **HTTP Client Wrapper** | 📋 **Planejado** | `scripts/utils/http_client.py` (futuro) |
| **Metrics System** | 📋 **Planejado** | `scripts/utils/metrics.py` (futuro) |

> **⚠️ Nota Importante:**
> O sistema de Trace ID já está **100% funcional**. Os componentes marcados como "Planejados" devem ser implementados **apenas quando houver necessidade real** (princípio YAGNI - You Aren't Gonna Need It).

---

## 🔍 Sistema de Trace ID

### Arquitetura

O sistema de Trace ID usa `contextvars` (PEP 567) para propagação automática em ambientes thread-safe e async-safe.

```python
┌──────────────────────────────────────────────┐
│  Entry Point (CLI/API)                       │
│  with trace_context():                       │
│    ├─ Trace ID: a1b2c3d4-...                │
│    ├─ function_a()                           │
│    │   └─ logger.info() [a1b2c3d4]          │
│    ├─ function_b()                           │
│    │   ├─ external_http_call()              │
│    │   │   └─ Header: X-Trace-ID            │
│    │   └─ logger.warning() [a1b2c3d4]       │
│    └─ function_c()                           │
│        └─ logger.error() [a1b2c3d4]         │
└──────────────────────────────────────────────┘
```

### API Disponível

```python
from scripts.utils.context import (
    get_trace_id,      # Obter Trace ID atual
    set_trace_id,      # Definir Trace ID customizado
    trace_context,     # Context manager (recomendado)
)

# 1. Geração automática
with trace_context():
    trace_id = get_trace_id()  # UUID4 auto-gerado
    do_work()

# 2. Propagação de Trace ID externo (ex: HTTP header)
incoming_trace_id = request.headers.get("X-Trace-ID")
if incoming_trace_id:
    set_trace_id(incoming_trace_id)
```

### Características Técnicas

| Atributo | Valor |
|----------|-------|
| **Implementação** | `contextvars.ContextVar` |
| **Thread-safe** | ✅ Sim |
| **Async-safe** | ✅ Sim |
| **Formato** | UUID4 (RFC 4122) |
| **Propagação** | Automática dentro do contexto |
| **Overhead** | Negligível (<1µs per access) |

**Documentação Completa:** `docs/guides/logging.md`

---

## 🌐 Padrão de Chamadas Externas (HTTP)

### Princípio Fundamental

> **REGRA DE OURO:**
> Toda requisição HTTP externa DEVE carregar o header `X-Trace-ID` para permitir rastreabilidade distribuída.

### Status de Implementação

⚠️ **Este padrão está DOCUMENTADO, mas NÃO IMPLEMENTADO.**

O projeto atualmente **não realiza chamadas HTTP externas**. Quando essa necessidade surgir, siga os padrões abaixo.

### Arquitetura Proposta

```
┌────────────────────────────────────────────────────┐
│  Application Code                                  │
│  from scripts.utils.http_client import HttpClient │
│                                                    │
│  client = HttpClient()                            │
│  response = client.get("https://api.example.com") │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  HttpClient Wrapper (scripts/utils/http_client.py)│
│  1. Injeta X-Trace-ID                             │
│  2. Registra métricas                             │
│  3. Adiciona logging                              │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  requests/httpx (Biblioteca Base)                 │
│  Executa requisição HTTP real                     │
└────────────────────────────────────────────────────┘
```

### Template de Implementação

**Arquivo:** `scripts/utils/http_client.py` (CRIAR QUANDO NECESSÁRIO)

```python
"""HTTP Client com Observabilidade Integrada.

AVISO: Este módulo ainda NÃO está implementado.
Este é um TEMPLATE para implementação futura.

Quando implementar:
1. Adicionar dependência 'requests' ou 'httpx' em pyproject.toml
2. Implementar as classes abaixo
3. Adicionar testes em tests/test_http_client.py
4. Atualizar documentação

Autor: SRE Team
Versão: 0.0.0 (Template)
Status: NOT_IMPLEMENTED
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests import Response

from scripts.utils.context import get_trace_id
from scripts.utils.metrics import HttpMetrics

logger = logging.getLogger(__name__)


class HttpClient:
    """Cliente HTTP com observabilidade automática.

    Features:
    - Injeção automática de X-Trace-ID
    - Métricas de sucesso/falha
    - Logging estruturado
    - Retry automático (opcional)

    Example:
        >>> client = HttpClient()
        >>> response = client.get("https://api.example.com/data")
        >>> assert "X-Trace-ID" in response.request.headers
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 30,
        enable_metrics: bool = True,
    ) -> None:
        """Inicializa o cliente HTTP.

        Args:
            base_url: URL base para requisições relativas
            timeout: Timeout padrão em segundos
            enable_metrics: Se True, registra métricas
        """
        self.base_url = base_url
        self.timeout = timeout
        self.metrics = HttpMetrics() if enable_metrics else None
        self.session = requests.Session()

    def _inject_headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        """Injeta headers obrigatórios de observabilidade.

        Args:
            headers: Headers fornecidos pelo usuário

        Returns:
            Headers enriquecidos com X-Trace-ID
        """
        headers = headers or {}

        # Injeta Trace ID do contexto atual
        trace_id = get_trace_id()
        headers["X-Trace-ID"] = trace_id

        # Headers adicionais (user-agent, etc.)
        headers.setdefault("User-Agent", "ObservableHttpClient/1.0")

        return headers

    def _build_url(self, path: str) -> str:
        """Constrói URL completa a partir do base_url.

        Args:
            path: Caminho relativo ou URL absoluta

        Returns:
            URL completa
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path

        if self.base_url:
            return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

        return path

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Response:
        """Executa requisição HTTP GET com observabilidade.

        Args:
            url: URL ou caminho relativo
            params: Query parameters
            headers: Headers customizados
            **kwargs: Argumentos adicionais para requests.get

        Returns:
            Response object

        Raises:
            requests.RequestException: Em caso de falha na requisição

        Example:
            >>> client = HttpClient(base_url="https://api.example.com")
            >>> response = client.get("/users", params={"page": 1})
            >>> assert response.status_code == 200
        """
        full_url = self._build_url(url)
        headers = self._inject_headers(headers)

        logger.debug(f"HTTP GET {full_url}", extra={"params": params})

        try:
            response = self.session.get(
                full_url,
                params=params,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )

            # Registra sucesso
            if self.metrics:
                self.metrics.record_success("GET", full_url, response.status_code)

            logger.info(
                f"HTTP GET {full_url} -> {response.status_code}",
                extra={"status_code": response.status_code},
            )

            return response

        except requests.RequestException as e:
            # Registra falha
            if self.metrics:
                self.metrics.record_failure("GET", full_url, str(e))

            logger.error(f"HTTP GET {full_url} failed: {e}")
            raise

    def post(
        self,
        url: str,
        data: Any | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Response:
        """Executa requisição HTTP POST com observabilidade.

        Args:
            url: URL ou caminho relativo
            data: Form data
            json: JSON payload
            headers: Headers customizados
            **kwargs: Argumentos adicionais para requests.post

        Returns:
            Response object

        Example:
            >>> client = HttpClient()
            >>> response = client.post(
            ...     "https://api.example.com/users",
            ...     json={"name": "Alice"}
            ... )
        """
        full_url = self._build_url(url)
        headers = self._inject_headers(headers)

        logger.debug(f"HTTP POST {full_url}")

        try:
            response = self.session.post(
                full_url,
                data=data,
                json=json,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )

            if self.metrics:
                self.metrics.record_success("POST", full_url, response.status_code)

            logger.info(f"HTTP POST {full_url} -> {response.status_code}")

            return response

        except requests.RequestException as e:
            if self.metrics:
                self.metrics.record_failure("POST", full_url, str(e))

            logger.error(f"HTTP POST {full_url} failed: {e}")
            raise

    def put(
        self,
        url: str,
        data: Any | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Response:
        """Executa requisição HTTP PUT."""
        # Implementação similar ao POST
        ...

    def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Response:
        """Executa requisição HTTP DELETE."""
        # Implementação similar ao GET
        ...

    def __enter__(self) -> HttpClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit - fecha sessão."""
        self.session.close()
```

### Regras de Uso

#### ✅ Padrão CORRETO

```python
from scripts.utils.http_client import HttpClient

# Usar wrapper com observabilidade
client = HttpClient()
response = client.get("https://api.example.com/data")

# Trace ID propagado automaticamente!
assert "X-Trace-ID" in response.request.headers
```

#### ❌ Padrão INCORRETO

```python
import requests

# NÃO usar requests diretamente!
response = requests.get("https://api.example.com/data")

# ❌ Sem Trace ID
# ❌ Sem métricas
# ❌ Sem logging padronizado
```

### Checklist de Implementação

Quando for implementar chamadas HTTP pela primeira vez:

- [ ] Criar `scripts/utils/http_client.py` baseado no template
- [ ] Criar `scripts/utils/metrics.py` (veja seção abaixo)
- [ ] Adicionar dependência em `pyproject.toml`
- [ ] Criar testes em `tests/test_http_client.py`
- [ ] Validar injeção de `X-Trace-ID`
- [ ] Validar registro de métricas
- [ ] Atualizar `ENGINEERING_STANDARDS.md`
- [ ] Executar auditoria de código (`dev-audit`)

---

## 📊 Sistema de Métricas

### Status de Implementação

⚠️ **NÃO IMPLEMENTADO** - Template para implementação futura.

### Arquitetura Proposta

```
┌─────────────────────────────────────────────────────┐
│  HttpClient / Other Components                      │
│  metrics.record_success("GET", url, 200)           │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  MetricsCollector (scripts/utils/metrics.py)       │
│  • Contadores (success/failure)                    │
│  • Histogramas (latência)                          │
│  • Gauges (conexões ativas)                        │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  Exporters (Futuro)                                 │
│  • Prometheus                                       │
│  • StatsD                                           │
│  • CloudWatch                                       │
└─────────────────────────────────────────────────────┘
```

### Template de Implementação

**Arquivo:** `scripts/utils/metrics.py` (CRIAR QUANDO NECESSÁRIO)

```python
"""Sistema de Métricas para Observabilidade.

AVISO: Este módulo ainda NÃO está implementado.
Este é um TEMPLATE para implementação futura.

Autor: SRE Team
Versão: 0.0.0 (Template)
Status: NOT_IMPLEMENTED
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricCounter:
    """Contador simples de eventos.

    Example:
        >>> counter = MetricCounter("http_requests_total")
        >>> counter.increment(labels={"method": "GET", "status": "200"})
    """

    name: str
    help_text: str = ""
    values: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def increment(self, value: int = 1, labels: dict[str, str] | None = None) -> None:
        """Incrementa o contador.

        Args:
            value: Valor a incrementar (padrão: 1)
            labels: Labels para dimensionar a métrica
        """
        key = self._make_key(labels or {})
        self.values[key] += value
        logger.debug(f"Metric {self.name}[{key}] += {value}")

    def get(self, labels: dict[str, str] | None = None) -> int:
        """Obtém valor atual do contador."""
        key = self._make_key(labels or {})
        return self.values[key]

    def _make_key(self, labels: dict[str, str]) -> str:
        """Cria chave única a partir das labels."""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


@dataclass
class MetricHistogram:
    """Histograma para medir distribuição de valores.

    Example:
        >>> histogram = MetricHistogram("http_request_duration_seconds")
        >>> histogram.observe(0.123, labels={"method": "GET"})
    """

    name: str
    help_text: str = ""
    observations: dict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Registra uma observação.

        Args:
            value: Valor observado
            labels: Labels para dimensionar a métrica
        """
        key = self._make_key(labels or {})
        self.observations[key].append(value)

    def get_percentile(
        self,
        percentile: float,
        labels: dict[str, str] | None = None,
    ) -> float:
        """Calcula percentil das observações."""
        key = self._make_key(labels or {})
        values = sorted(self.observations[key])

        if not values:
            return 0.0

        index = int(len(values) * percentile / 100)
        return values[min(index, len(values) - 1)]

    def _make_key(self, labels: dict[str, str]) -> str:
        """Cria chave única a partir das labels."""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class HttpMetrics:
    """Coletor de métricas específico para HTTP.

    Métricas coletadas:
    - http_requests_total (counter)
    - http_request_duration_seconds (histogram)
    - http_request_size_bytes (histogram)

    Example:
        >>> metrics = HttpMetrics()
        >>> metrics.record_success("GET", "https://api.example.com", 200)
        >>> metrics.record_failure("POST", "https://api.example.com", "timeout")
    """

    def __init__(self) -> None:
        """Inicializa coletores de métricas."""
        self.requests_total = MetricCounter(
            name="http_requests_total",
            help_text="Total de requisições HTTP",
        )

        self.request_duration = MetricHistogram(
            name="http_request_duration_seconds",
            help_text="Duração das requisições HTTP",
        )

    def record_success(
        self,
        method: str,
        url: str,
        status_code: int,
        duration: float | None = None,
    ) -> None:
        """Registra requisição bem-sucedida.

        Args:
            method: Método HTTP (GET, POST, etc.)
            url: URL da requisição
            status_code: Código HTTP de resposta
            duration: Duração em segundos (opcional)
        """
        labels = {
            "method": method,
            "status": str(status_code),
            "result": "success",
        }

        self.requests_total.increment(labels=labels)

        if duration is not None:
            self.request_duration.observe(duration, labels=labels)

        logger.debug(
            f"HTTP metric recorded: {method} {url} -> {status_code}",
            extra={"labels": labels},
        )

    def record_failure(
        self,
        method: str,
        url: str,
        error: str,
    ) -> None:
        """Registra requisição com falha.

        Args:
            method: Método HTTP
            url: URL da requisição
            error: Mensagem de erro
        """
        labels = {
            "method": method,
            "status": "error",
            "result": "failure",
        }

        self.requests_total.increment(labels=labels)

        logger.warning(
            f"HTTP metric failure: {method} {url} - {error}",
            extra={"labels": labels, "error": error},
        )

    def get_summary(self) -> dict[str, Any]:
        """Retorna resumo das métricas coletadas.

        Returns:
            Dicionário com estatísticas agregadas
        """
        return {
            "total_requests": sum(self.requests_total.values.values()),
            "p50_duration": self.request_duration.get_percentile(50),
            "p95_duration": self.request_duration.get_percentile(95),
            "p99_duration": self.request_duration.get_percentile(99),
        }
```

### Métricas HTTP Recomendadas

| Métrica | Tipo | Descrição | Labels |
|---------|------|-----------|--------|
| `http_requests_total` | Counter | Total de requisições | `method`, `status`, `result` |
| `http_request_duration_seconds` | Histogram | Latência das requisições | `method`, `status` |
| `http_request_size_bytes` | Histogram | Tamanho do payload | `method`, `direction` |
| `http_requests_in_flight` | Gauge | Requisições em andamento | `method` |

### Exportação para APM Tools

Quando necessário integrar com ferramentas de monitoramento:

```python
# Exemplo: Exportar para Prometheus
from prometheus_client import Counter, Histogram

http_requests = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'status']
)

http_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method']
)
```

---

## 🎯 Casos de Uso

### Caso 1: API REST Client

**Cenário:** Projeto precisa consultar API externa de terceiros.

**Implementação:**

```python
from scripts.utils.http_client import HttpClient
from scripts.utils.context import trace_context

def fetch_user_data(user_id: str) -> dict:
    """Busca dados de usuário em API externa."""
    with trace_context():  # Cria contexto com Trace ID
        client = HttpClient(base_url="https://api.example.com")

        response = client.get(f"/users/{user_id}")
        response.raise_for_status()

        return response.json()

# Trace ID propagado automaticamente!
# Logs correlacionados via UUID único
# Métricas de sucesso/falha registradas
```

### Caso 2: Microserviços Distribuídos

**Cenário:** Serviço A chama Serviço B, que chama Serviço C.

**Implementação:**

```python
# Serviço A (entry point)
@app.post("/api/process")
def process_request(request: Request):
    # Extrai Trace ID do header (se existir)
    trace_id = request.headers.get("X-Trace-ID")

    with trace_context(trace_id):  # Propaga ou cria novo
        client = HttpClient()

        # Chama Serviço B - Trace ID propagado!
        response_b = client.post(
            "http://service-b/api/step1",
            json={"data": "..."}
        )

        # Serviço B fará o mesmo com Serviço C
        # Todos os logs compartilham o mesmo Trace ID!

        return {"status": "ok"}
```

### Caso 3: Batch Processing com HTTP Calls

**Cenário:** Script batch que processa milhares de itens com chamadas HTTP.

```python
from scripts.utils.context import trace_context
from scripts.utils.http_client import HttpClient

def process_batch(items: list[str]) -> None:
    """Processa batch de itens com observabilidade."""

    with trace_context():  # Um Trace ID para todo o batch
        client = HttpClient()

        for item in items:
            try:
                response = client.post("/api/process", json={"item": item})
                logger.info(f"Item {item} processed successfully")
            except Exception as e:
                logger.error(f"Failed to process {item}: {e}")
                # Métricas de falha registradas automaticamente

        # Ao final, pode-se consultar métricas agregadas
        summary = client.metrics.get_summary()
        logger.info(f"Batch completed: {summary}")
```

---

## 📚 Referências

### Documentação Interna

- **Logging e Trace ID:** `docs/guides/logging.md`
- **Padrões de Engenharia:** `docs/guides/ENGINEERING_STANDARDS.md`
- **Contexto (Código):** `scripts/utils/context.py`
- **Logger (Código):** `scripts/utils/logger.py`

### Padrões Externos

- [OpenTelemetry - Distributed Tracing](https://opentelemetry.io/docs/concepts/observability-primer/#distributed-tracing)
- [The Twelve-Factor App - Logs](https://12factor.net/logs)
- [Google SRE Book - Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Prometheus - Best Practices](https://prometheus.io/docs/practices/naming/)

### RFCs e Standards

- [RFC 7231 - HTTP/1.1 Semantics](https://datatracker.ietf.org/doc/html/rfc7231)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [OpenTracing Specification](https://opentracing.io/specification/)

---

## 🤝 Contribuição

### Quando Implementar Este Padrão

✅ **Implementar quando:**

- Primeira chamada HTTP externa for necessária
- Integração com APIs de terceiros for planejada
- Sistema começar a ter características distribuídas

❌ **NÃO implementar se:**

- Projeto não faz chamadas HTTP
- Apenas para "prever o futuro" (YAGNI)

### Como Contribuir

Se você for o primeiro a implementar chamadas HTTP:

1. **Copie os templates** deste documento para os arquivos corretos
2. **Adicione testes** em `tests/test_http_client.py`
3. **Valide métricas** com testes de integração
4. **Atualize este documento** com exemplos reais
5. **Execute auditoria** com `dev-audit`

---

**Última Atualização:** 2025-12-07
**Versão:** 1.0.0
**Autores:** SRE Team
**Status:** ✅ Documentado | 📋 Aguardando Implementação
