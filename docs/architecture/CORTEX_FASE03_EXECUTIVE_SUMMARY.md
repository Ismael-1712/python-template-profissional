---
id: cortex-fase03-executive-summary
type: arch
status: draft
version: 0.1.0
author: Engineering Team
date: '2025-12-14'
context_tags: [cortex, phase-3, executive-summary]
linked_code: []
related_docs:
  - docs/architecture/CORTEX_FASE03_LINK_SCANNER_DESIGN.md
---

# 🧠 CORTEX Fase 3 - Resumo Executivo (1 Página)

**Data:** 14 de Dezembro de 2025
**Missão:** [006] - The Link Scanner
**Status:** 🔵 Design em Aprovação

---

## 🎯 PROBLEMA

**Situação Atual (Fase 2):**

- ✅ Sistema lê arquivos Markdown e armazena conteúdo em `cached_content`
- ❌ Conteúdo **não é analisado** semanticamente
- ❌ Links entre documentos (`[[Fase 01]]`, `[Guide](docs/guide.md)`) são **invisíveis**
- ❌ **Não há grafo de conhecimento** para navegação

**Impacto:** Temos "nós isolados", não um "grafo conectado".

---

## 💡 SOLUÇÃO PROPOSTA

**Novo Componente:** `LinkAnalyzer` (+ `LinkResolver`)

**Capacidades:**

1. 🔍 **Extrai** links de 3 tipos:
   - Markdown: `[Label](target)`
   - Wikilinks: `[[target]]` ou `[[target|alias]]`
   - Code References: `[[code:path/to/file.py::Symbol]]`

2. 🔗 **Resolve** referências para IDs canônicos:
   - Por ID: `cortex-fase01-design` → `cortex-fase01-design`
   - Por título fuzzy: `Fase 01` → `cortex-fase01-design`
   - Por caminho: `../architecture/CORTEX_FASE01_DESIGN.md` → `cortex-fase01-design`

3. 🌐 **Constrói** grafo bidirecional:
   - `outbound_links`: Links que saem do documento
   - `inbound_link_ids`: Backlinks (quem me referencia)

4. ✅ **Valida** links quebrados (CI/CD integration)

---

## 🏗️ ARQUITETURA

### Decisão de Design: **Composição sobre Herança**

```
✅ LinkAnalyzer (novo componente dedicado)
   ↓ usa
✅ LinkResolver (resolve referências)
   ↓ consulta
✅ KnowledgeIndex (busca rápida)
```

**Vantagens:**

- Single Responsibility Principle
- Testabilidade isolada
- Reusabilidade (pode ser usado em CI, PRs, etc.)

---

## 📊 MODELO DE DADOS

### Novo Modelo: `KnowledgeLink`

```python
class KnowledgeLink(BaseModel):
    source_id: str           # "kno-001"
    target_raw: str          # "[[Fase 01]]"
    target_resolved: str     # "cortex-fase01-design"
    type: LinkType           # WIKILINK
    line_number: int         # 42
    context: str             # "...conforme [[Fase 01]]..."
    is_valid: bool           # True
```

### Extensão de `KnowledgeEntry`

```python
class KnowledgeEntry(BaseModel):
    # Campos existentes (Fase 2)
    id: str
    cached_content: str | None

    # 🆕 Novos campos (Fase 3)
    outbound_links: list[KnowledgeLink]  # Saída
    inbound_link_ids: list[str]          # Entrada (backlinks)
```

---

## 🔍 REGEX PATTERNS

### 1. Markdown Links

```python
PATTERN = r'\[([^\]]+)\]\(([^)]+)\)'
```

**Captura:** `[Guide](docs/guide.md)` → `("Guide", "docs/guide.md")`

### 2. Wikilinks

```python
PATTERN = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
```

**Captura:**

- `[[Fase 01]]` → `("Fase 01", None)`
- `[[Fase 01|Docs]]` → `("Fase 01", "Docs")`

### 3. Code References

```python
PATTERN = r'\[\[code:([^\]]+?)(?:::([^\]]+))?\]\]'
```

**Captura:**

- `[[code:scripts/core/cortex/models.py]]` → `("scripts/...", None)`
- `[[code:models.py::KnowledgeEntry]]` → `("models.py", "KnowledgeEntry")`

---

## 🖥️ CLI INTEGRATION

### Novo Comando: `cortex knowledge-graph`

```bash
# Análise básica
cortex knowledge-graph

# Output:
# 🧠 Analyzing knowledge graph: docs/knowledge
# 📦 Found 15 knowledge nodes
# 🔗 Total links: 42
# ✅ Broken links: 0

# Mostrar apenas links quebrados
cortex knowledge-graph --show-broken

# Export como JSON (para CI/CD)
cortex knowledge-graph --export json > graph.json

# Export como Graphviz DOT (visualização)
cortex knowledge-graph --export dot | dot -Tpng > graph.png
```

---

## 📅 ROADMAP DE IMPLEMENTAÇÃO

### Fase 3.1: Link Extraction (MVP) - **1 semana**

- [ ] `LinkAnalyzer` com 3 regex patterns
- [ ] `KnowledgeLink` model (Pydantic)
- [ ] Testes unitários (100% cobertura regex)

### Fase 3.2: Link Resolution - **1 semana**

- [ ] `LinkResolver` com 4 estratégias
- [ ] `KnowledgeIndex` para busca rápida
- [ ] Testes de resolução (edge cases)

### Fase 3.3: Graph Building - **3 dias**

- [ ] Extensão de `KnowledgeEntry`
- [ ] Algoritmo de backlinks
- [ ] Testes de grafo bidirecional

### Fase 3.4: CLI Integration - **2 dias**

- [ ] Comando `cortex knowledge-graph`
- [ ] Export JSON/DOT
- [ ] Testes E2E

### Fase 3.5: Documentation - **1 dia**

- [ ] Finalizar design doc
- [ ] Docstrings completas
- [ ] Atualizar manual do usuário

**Total:** ~2,5 semanas

---

## ✅ CRITÉRIOS DE ACEITAÇÃO

### Funcional

- [ ] Extrai 3 tipos de links com 95%+ precisão
- [ ] Resolve links por ID, título, caminho
- [ ] Constrói grafo bidirecional correto
- [ ] Detecta broken links com 100% recall
- [ ] CLI funciona com export JSON/DOT

### Técnico

- [ ] Cobertura de testes ≥ 90%
- [ ] Type hints completos (mypy strict)
- [ ] Docstrings em todos os componentes
- [ ] Performance: < 2s para 100 documentos

### Documentação

- [ ] Design doc aprovado
- [ ] ADR registrando decisões arquiteturais
- [ ] Exemplos de uso no manual

---

## 🚨 RISCOS

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| Regex com falsos positivos | 🟡 Média | 🟢 Baixo | Testes extensivos + validação manual |
| Performance em grandes bases | 🟢 Baixa | 🟡 Médio | Indexação + caching |
| Ambiguidade na resolução | 🟡 Média | 🟡 Médio | Logging + relatório de conflitos |

---

## 📊 MÉTRICAS DE SUCESSO

1. **Precisão de Extração:** ≥ 95% dos links são capturados corretamente
2. **Taxa de Resolução:** ≥ 90% dos links são resolvidos para IDs válidos
3. **Broken Links Detection:** 100% dos links quebrados são detectados
4. **Adoção:** ≥ 50% dos Knowledge Nodes usam links semânticos após 1 mês

---

## 🎬 PRÓXIMOS PASSOS

1. ✅ **Revisar este design** com stakeholders
2. ✅ **Aprovar** arquitetura e padrões propostos
3. 🔵 **Criar branch** `feature/cortex-phase3-link-scanner`
4. 🔵 **Iniciar Sprint 1:** Fase 3.1 (MVP - Link Extraction)
5. 🔵 **Demo** após cada fase para validação incremental

---

**Documento Completo:** [CORTEX_FASE03_LINK_SCANNER_DESIGN.md](./CORTEX_FASE03_LINK_SCANNER_DESIGN.md)
**Protótipo:** [link_analyzer_prototype.py](../../scripts/core/cortex/link_analyzer_prototype.py)
**Testes:** [test_link_analyzer_prototype.py](../../tests/test_link_analyzer_prototype.py)

**Status:** 🔵 Aguardando Aprovação
**Responsável:** Engineering Team
