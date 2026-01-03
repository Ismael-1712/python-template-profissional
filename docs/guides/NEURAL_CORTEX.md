---
id: guide-neural-cortex
title: Neural Cortex - AI-Powered Semantic Search
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: '2026-01-03'
context_tags: [neural, ai, semantic-search, chromadb, embeddings, rag]
linked_code:
  - scripts/cli/neural.py
  - scripts/core/cortex/neural/vector_bridge.py
  - scripts/core/cortex/neural/ports.py
  - scripts/core/cortex/neural/adapters/sentence_transformer.py
  - scripts/core/cortex/neural/adapters/chroma.py
  - scripts/core/cortex/neural/adapters/memory.py
related_docs:
  - docs/architecture/HEXAGONAL_DIAGRAMS.md
  - docs/architecture/CORTEX_FASE04_VECTOR_STORE_DESIGN.md
---

# 🧠 Neural Cortex - Guia Completo

## 📋 Introdução

O **Neural Cortex** é o sistema de busca semântica e memória de longo prazo do CORTEX Template. Ele permite encontrar documentação, código e conhecimento através de conceitos e significado, não apenas palavras-chave exatas.

### Por Que Busca Semântica?

**Busca Tradicional (Keyword-based):**

```bash
grep -r "authentication" docs/
# Encontra apenas docs com a palavra exata "authentication"
```

**Busca Semântica (Neural):**

```bash
cortex neural ask "Como fazer login de usuários?"
# Encontra docs sobre: authentication, login, user sessions, JWT, OAuth
# Entende que "fazer login" ≈ "authentication" ≈ "user sessions"
```

## 🚀 Quick Start

### 1. Instalar Dependências

```bash
# Ambiente completo (já inclui IA)
make install-dev

# Ou instalar manualmente
pip install sentence-transformers chromadb torch
```

### 2. Indexar Documentação

```bash
# Indexar com ChromaDB (persistente)
cortex neural index

# Ou usar RAM (volátil + JSON)
cortex neural index --memory-type ram
```

**Output Esperado:**

```
🧠 CORTEX Neural System Status
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Motor Cognitivo: 🟢 SentenceTransformers ┃
┃                   (Real AI)              ┃
┃ Memória:         🟢 ChromaDB (Persistent)┃
┃ Modelo:          all-MiniLM-L6-v2        ┃
┃ Caminho:         .cortex/memory          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Found 127 documents to index.
Indexing documents... ━━━━━━━━━━━━━━━━━━━━ 100%

✓ Successfully indexed 127/127 documents
```

### 3. Fazer Perguntas

```bash
cortex neural ask "Como rodar testes?"

# Com mais resultados
cortex neural ask "Exemplos de dependency injection" --top 10

# Especificar banco de dados customizado
cortex neural ask "query" --db .custom/memory
```

**Output Esperado (Nova Interface com Rastreabilidade):**

```
🧠 CORTEX Neural System Status
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Motor Cognitivo: 🟢 SentenceTransformers ┃
┃                   (Real AI)              ┃
┃ Memória:         🟢 ChromaDB (Persistent)┃
┃ Modelo:          all-MiniLM-L6-v2        ┃
┃ Caminho:         .cortex/memory          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Query: Como rodar testes?

        🎯 Resultados da Busca Semântica
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃  # ┃ Confiança  ┃ Fonte                 ┃ Snippet            ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│  1 │ 0.92       │ CONTRIBUTING.md:145   │ Para rodar testes  │
│    │            │                       │ locais, execute:   │
│    │            │                       │ make test...       │
│  2 │ 0.87       │ README.md:78          │ ## Testes Execute  │
│    │            │                       │ a suite completa   │
│    │            │                       │ com pytest...      │
│  3 │ 0.74       │ docs/testing.md:12    │ Framework de testes│
│    │            │                       │ usa pytest com...  │
└────┴────────────┴───────────────────────┴────────────────────┘

✓ 3 resultados relevantes encontrados
```

**Novo Formato de Saída:**

- **Coluna "Confiança"**: Score formatado (0.00 a 1.00) com cores:
  - 🟢 **Verde** (≥ 0.80): Alta confiança
  - 🟡 **Amarelo** (≥ 0.60): Confiança moderada
  - 🔴 **Vermelho** (< 0.60): Confiança baixa
- **Coluna "Fonte"**: Rastreabilidade completa `arquivo:linha`
- **Coluna "Snippet"**: Primeiros 147 caracteres com truncamento inteligente
- **Mensagem final**: Texto em português com emoji de confirmação

## 🏗️ Arquitetura

### Componentes Principais

```
┌──────────────────────────────────────────────┐
│              CLI Commands                    │
│  (cortex neural index / ask)                 │
└─────────────────┬────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────┐
│          VectorBridge (Core)                 │
│  - index_document()                          │
│  - query_similar()                           │
│  - Business Logic (Pure)                     │
└─────────┬────────────────────┬───────────────┘
          │                    │
     ┌────▼────┐          ┌────▼──────┐
     │Embedding│          │ Vector    │
     │  Port   │          │Store Port │
     └────┬────┘          └────┬──────┘
          │                    │
    ┌─────▼──────┐      ┌──────▼────────┐
    │ Adapters   │      │   Adapters    │
    │────────────│      │───────────────│
    │Sentence    │      │ ChromaDB      │
    │Transformer │      │ InMemory      │
    │Placeholder │      │ (Future)      │
    │OpenAI (fut)│      │ Pinecone (fut)│
    └────────────┘      └───────────────┘
```

### Ports (Interfaces)

**EmbeddingPort:**

```python
class EmbeddingPort(Protocol):
    """Contrato para serviços de embedding."""

    def embed(self, text: str) -> list[float]:
        """Gera embedding para um texto."""
        ...

    def batch_embed(self, texts: list[str]) -> list[list[float]]:
        """Gera embeddings em lote."""
        ...
```

**VectorStorePort:**

```python
class VectorStorePort(Protocol):
    """Contrato para armazenamento de vetores."""

    def index(self, chunk: DocumentChunk) -> None:
        """Armazena chunk com embedding."""
        ...

    def query(self, embedding: list[float], limit: int) -> list[SearchResult]:
        """Busca por similaridade."""
        ...

    def persist(self) -> None:
        """Persiste dados no disco."""
        ...
```

### Adapters (Implementações)

| Adapter | Port | Tecnologia | Status |
|---------|------|------------|--------|
| `SentenceTransformerAdapter` | `EmbeddingPort` | sentence-transformers | ✅ Production |
| `PlaceholderEmbeddingService` | `EmbeddingPort` | Dummy (zeros) | ⚠️ Fallback |
| `ChromaDBVectorStore` | `VectorStorePort` | ChromaDB | ✅ Production |
| `InMemoryVectorStore` | `VectorStorePort` | RAM + JSON | ✅ Production |

## 🎛️ Modos de Operação

### 1. Modo Produção (Recomendado)

**Configuração:**

- Motor Cognitivo: SentenceTransformers (Real AI)
- Memória: ChromaDB (Persistente)

**Características:**

- ✅ Embeddings semânticos reais (384 dimensões)
- ✅ Persistência em disco (`.cortex/memory/`)
- ✅ Performance otimizada (índices vetoriais)
- ✅ Busca < 100ms para 1000+ docs

**Comando:**

```bash
cortex neural index --memory-type chroma
```

### 2. Modo RAM (Desenvolvimento)

**Configuração:**

- Motor Cognitivo: SentenceTransformers
- Memória: InMemory (RAM + JSON)

**Características:**

- ✅ Embeddings semânticos reais
- ⚠️ Persistência via JSON (mais lento)
- ⚠️ Carrega tudo na RAM
- ✅ Útil para testes/debug

**Comando:**

```bash
cortex neural index --memory-type ram
```

### 3. Modo Fallback (Emergência)

**Configuração:**

- Motor Cognitivo: Placeholder (Dummy)
- Memória: InMemory (RAM + JSON)

**Características:**

- ❌ Embeddings falsos (zeros)
- ❌ Busca não funcional
- ✅ Sistema não quebra
- ⚠️ Alerta visual no banner

**Quando ocorre:**

- `sentence-transformers` não instalado
- Erro ao carregar modelo de IA

**Output:**

```
⚠️  Could not load AI model. Using placeholder service.
   For production use, ensure sentence-transformers is installed.
```

## 📊 Banner de Status (Verbose by Default)

### Por Que Verbose?

**Problema:** "Cegueira de Ferramenta" - usuário não sabe se IA está ativa ou degradada.

**Solução:** Todo comando Neural exibe status completo ANTES de operar:

```
🧠 CORTEX Neural System Status
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Motor Cognitivo: 🟢 SentenceTransformers ┃
┃                   (Real AI)              ┃
┃ Memória:         🟢 ChromaDB (Persistent)┃
┃ Modelo:          all-MiniLM-L6-v2        ┃
┃ Caminho:         .cortex/memory          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Interpretação de Ícones

| Ícone | Status | Significado |
|-------|--------|-------------|
| 🟢 | Optimal | Configuração de produção (IA real + persistência) |
| ⚠️ | Degraded | Fallback ativo (placeholder ou RAM) |
| ❌ | Error | Sistema não funcional (não deve ocorrer) |

### Interpretação de Scores de Confiança

Os scores de confiança indicam a similaridade semântica entre sua consulta e os resultados encontrados:

| Score | Cor | Interpretação | Ação Recomendada |
|-------|-----|---------------|------------------|
| **0.80 - 1.00** | 🟢 Verde | **Alta Confiança** - Resultado altamente relevante, semântica muito próxima da consulta | Use com confiança, ideal para RAG |
| **0.60 - 0.79** | 🟡 Amarelo | **Confiança Moderada** - Resultado relacionado, mas pode não ser exatamente o que busca | Revise o contexto antes de usar |
| **< 0.60** | 🔴 Vermelho | **Confiança Baixa** - Resultado tangencialmente relacionado ou potencialmente irrelevante | Refine sua consulta ou considere outras fontes |

**Exemplo Prático:**

```bash
cortex neural ask "autenticação JWT"

# Score 0.92 (Verde)  → "Como implementar JWT authentication"
# Score 0.75 (Amarelo) → "Segurança em APIs REST"
# Score 0.55 (Vermelho) → "Configuração de banco de dados"
```

**Dica:** Se todos os resultados aparecem em vermelho, considere:

- Reformular a consulta com termos mais específicos
- Verificar se a documentação relevante foi indexada
- Executar `cortex neural index` novamente

## 🎯 Casos de Uso

### 1. RAG (Retrieval-Augmented Generation)

**Problema:** Chatbot precisa de contexto do projeto para responder.

**Solução:**

```python
from scripts.core.cortex.neural.vector_bridge import VectorBridge
from scripts.core.cortex.neural.adapters.sentence_transformer import SentenceTransformerAdapter
from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

# Setup
embedding = SentenceTransformerAdapter()
vector_store = ChromaDBVectorStore(persist_directory=".cortex/memory")
bridge = VectorBridge(embedding_service=embedding, vector_store=vector_store)

# Buscar contexto
results = bridge.query_similar("Como testar APIs?", limit=3)
context = "\n\n".join([r.chunk.content for r in results])

# Passar para LLM
prompt = f"""
Contexto do projeto:
{context}

Pergunta do usuário: Como testar APIs neste projeto?
"""
# Send to GPT-4/Claude...
```

### 2. Descoberta de Padrões

**Problema:** Novo desenvolvedor não sabe como implementar feature X.

**Solução:**

```bash
cortex neural ask "Exemplos de dependency injection"
cortex neural ask "Como estruturar testes?"
cortex neural ask "Padrão observer implementation"
```

### 3. Onboarding Automatizado

**Problema:** Onboarding manual consome tempo de seniors.

**Solução:** Bot que responde perguntas comuns:

```bash
cortex neural ask "Como configurar ambiente de dev?"
cortex neural ask "Onde estão as configurações de CI?"
cortex neural ask "Como fazer deploy?"
```

### 4. Code Review Assistido

**Problema:** Revisor não lembra de padrões do projeto.

**Solução:**

```bash
cortex neural ask "Qual padrão de error handling usamos?"
cortex neural ask "Como estruturar logging?"
```

## ⚙️ Configuração Avançada

### Customizar Diretórios

```bash
# Indexar docs customizados
cortex neural index --docs /custom/docs/path

# Salvar em local customizado
cortex neural index --db /data/vectors

# Usar ambos
cortex neural index --docs ./wiki --db ./wiki-vectors
```

### Performance Tuning

**Indexação em Lote:**

```bash
# Indexar apenas arquivos modificados (futuro)
cortex neural index --incremental

# Rebuild completo
cortex neural index --rebuild
```

**Busca Otimizada:**

```bash
# Menos resultados = mais rápido
cortex neural ask "query" --top 3

# Mais resultados = maior cobertura
cortex neural ask "query" --top 20
```

## 🐛 Troubleshooting

### Erro: "Using placeholder embedding service"

**Causa:** `sentence-transformers` não instalado.

**Solução:**

```bash
pip install sentence-transformers torch
```

**Verificar:**

```bash
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
```

### Erro: "ChromaDB not installed"

**Causa:** `chromadb` não instalado.

**Solução:**

```bash
pip install chromadb
```

**Fallback automático para RAM:**

```
⚠️  ChromaDB not installed. Using RAM storage instead.
   Install with: pip install chromadb
```

### Banco de Dados Corrompido

**Sintomas:**

- Erro ao carregar ChromaDB
- Resultados vazios após indexação

**Solução:**

```bash
# Deletar banco e re-indexar
rm -rf .cortex/memory
cortex neural index
```

### Performance Lenta

**Causas Comuns:**

1. **Modelo não carregado em GPU:**

```python
# Verificar se CUDA disponível
python -c "import torch; print(torch.cuda.is_available())"

# Se True, SentenceTransformer usará GPU automaticamente
```

1. **Muitos documentos (> 10k):**

```bash
# Considerar Pinecone/Weaviate para scale
# (Implementar adapter para VectorStorePort)
```

## 📚 Próximos Passos

- [ ] Implementar `cortex neural ask --interactive` (chat loop)
- [ ] Suporte a `--filters` (buscar apenas em docs/guides/)
- [ ] Integração com GitHub Copilot via `.copilot-context.json`
- [ ] Dashboard web para visualizar embeddings (t-SNE plot)
- [ ] Auto-indexação via pre-commit hook

## 📖 Referências

- [SentenceTransformers Documentation](https://www.sbert.net/)
- [ChromaDB Guide](https://docs.trychroma.com/)
- [Hexagonal Architecture Diagrams](../architecture/HEXAGONAL_DIAGRAMS.md)
- [CORTEX Fase 04 - Vector Store Design](../architecture/CORTEX_FASE04_VECTOR_STORE_DESIGN.md)

---

**Última Atualização**: 2026-01-03 (v0.2.0 - The AI Update)
**Mantido por**: Engineering Team
