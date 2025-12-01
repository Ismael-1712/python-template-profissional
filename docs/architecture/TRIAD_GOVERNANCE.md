---
id: triad-governance
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code:
- scripts/smart_git_sync.py
- scripts/doctor.py
title: 'MANIFESTO DA TRÍADE: Governança Arquitetural'
---

# MANIFESTO DA TRÍADE: Governança Arquitetural

## 🏛️ Constituição do Projeto

Este documento estabelece os princípios fundamentais de organização e governança do projeto Python Template Profissional, baseado no modelo da **Tríade Arquitetural**.

## 🤖 O Robô de Propagação Inteligente

### Conceito

Um sistema automatizado (`smart_git_sync.py`) que propaga mudanças entre branches seguindo regras rígidas de governança.

### Regras de Propagação

#### ✅ Fluxos Permitidos

```
main → cli     (fundação para ferramentas)
main → api     (fundação para aplicação)
```

#### ❌ Fluxos Proibidos

```
cli  ⇏  main   (ferramentas não voltam ao núcleo)
cli  ⇏  api    (ferramentas não vão para produção)
api  ⇏  main   (aplicação não volta ao núcleo)
api  ⇏  cli    (aplicação não contamina ferramentas)
```

### Princípio da Não-Contaminação

> **"O núcleo permanece puro. As especializações permanecem isoladas."**

- **main** pode doar para todos, mas não recebe de ninguém
- **cli** e **api** são ramos independentes que divergem de `main`
- Mudanças em `cli` ou `api` **NUNCA** retornam a `main`
- `cli` e `api` **NUNCA** se comunicam diretamente

## 🔒 Garantias Arquiteturais

### Imutabilidade do Núcleo

- `main` é protegida contra contaminação
- Apenas mudanças intencionais e revisadas entram em `main`
- `main` evolui lentamente e com propósito

### Independência das Especializações

- `cli` e `api` evoluem independentemente
- Não há acoplamento entre ferramentas e aplicação
- Cada branch pode ter seu próprio ritmo de desenvolvimento

### Rastreabilidade

- Todas as propagações são registradas
- Histórico claro de origem de cada mudança
- Auditoria completa de merges automáticos

## 📚 Referências

- **Implementação**: `scripts/smart_git_sync.py`
- **Configuração**: `scripts/smart_git_sync_config.yaml`
- **Documentação Técnica**: `docs/reference/git_sync.md`
- **Histórico**: `docs/history/sprint_1_foundation/`

**Data de Estabelecimento**: Sprint 1 - Foundation Phase
**Versão**: 1.0
**Status**: Constituição Ativa
**Última Atualização**: Novembro 2025
