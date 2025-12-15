---
id: design-task-010-vector-bridge
type: arch
title: "Task [010]: The Vector Bridge Design"
status: active
author: CORTEX Architect
date: 2025-12-15
version: 1.0.0
tags: [architecture, design, neural, vectors, rag]
---

# 🧬 Task [010]: The Vector Bridge (Design)

## 1. Visão Geral

A **Fase 4 (Neural Interface)** visa dotar o CORTEX de capacidades de Busca Semântica.
A **Tarefa [010]** implementa a camada de persistência vetorial usando `ChromaDB` (local) e `sentence-transformers`.

## 2. Stack Tecnológico

* **Embeddings:** `sentence-transformers` (Modelo: `all-MiniLM-L6-v2`)
* **Vector Store:** `ChromaDB` (Embedded/Local)
* **Chunking:** Markdown Header Splitter

## 3. Arquitetura

Fluxo: Markdown -> KnowledgeEntry -> Hash Check -> Chunking -> Embeddings -> ChromaDB.

## 4. Estratégia de Dependências

* Adicionar `chromadb` e `sentence-transformers` ao `pyproject.toml`.
* Usar lazy loading para não impactar a performance de comandos CLI simples.
