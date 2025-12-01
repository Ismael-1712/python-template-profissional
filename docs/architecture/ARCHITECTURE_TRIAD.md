---
id: architecture-triad
type: arch
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code:
- src/main.py
title: 📜 O MANIFESTO DA TRÍADE (V2.0)
---

# 📜 O MANIFESTO DA TRÍADE (V2.0)

**Protocolo de Sobrevivência e Arquitetura de Branches**

**Autor:** Equipe de Engenharia (Humano & GEM)
**Contexto:** Pós-Refatoração P26 (A Grande Sincronização)
**Alvo:** Próximas Equipes e Agentes de IA

-----

## 1\. O CONCEITO FUNDAMENTAL: "Herança com Personalidade"

Este repositório não é um projeto único. É uma **Plataforma de Engenharia (Main)** que alimenta dois **Produtos Distintos (CLI e API)**.

### 🟢 A Nave Mãe (`main`)

* **Identidade:** Infraestrutura, Automação, Scripts de Dev (`scripts/`), Configuração de Linting (`ruff`, `mypy`).
* **O que ela É:** A base SRE.
* **O que ela NÃO É:** O Produto. Ela não tem `FastAPI`, não tem `Typer`, não tem `Docker`.
* **Regra de Ouro:** Se serve para *desenvolver* (ex: `install-dev`, `doctor`), vive aqui.

### 🟣 O Agente de Campo (`cli`)

* **Fórmula:** $\text{CLI} = \text{MAIN} + \Delta_{\text{CLI}}$
* **O Delta ($\Delta$):**
  * `src/main.py`: Aplicação **Typer**.
  * `pyproject.toml`: Dependência `typer[all]`.
  * Workflows: Deploy para PyPI.
* **Comportamento:** Recebe atualizações da `main`, mas mantém sua personalidade de terminal.

### 🟠 O Servidor (`api`)

* **Fórmula:** $\text{API} = \text{MAIN} + \Delta_{\text{API}}$
* **O Delta ($\Delta$):**
  * `src/main.py`: Aplicação **FastAPI**.
  * Infra: `Dockerfile`, `docker-compose.yml`.
  * `pyproject.toml`: Dependências `fastapi`, `uvicorn`.
* **Comportamento:** Recebe atualizações da `main`, mas mantém sua personalidade web.

-----

## 2\. O PROTOCOLO DE PROPAGAÇÃO (O Robô)

Existe uma automação que empurra commits da `main` para `cli` e `api`.
**O Conflito é Esperado.**

Quando a `main` muda um arquivo que a `api` também mudou (ex: `pyproject.toml`), o conflito ocorre.

* **Erro da LLM Amadora:** "Vou dar `git reset --hard main` para resolver."
  * **Resultado:** Você DELETA o Delta. A API vira Main. O produto morre.
* **Ação da LLM Sênior:** "Vou fazer `git merge` e resolver o conflito preservando o Delta."

-----

## 3\. MANUAL DE INSTRUÇÕES PARA A PRÓXIMA LLM (Guardrails)

**⚠️ AVISO À INTELIGÊNCIA ARTIFICIAL:**
Se você foi instruído a trabalhar neste repositório, leia estas regras antes de executar qualquer comando Git. A violação resultará em perda de código e falha na missão.

### Regra Nº 1: O Respeito ao Delta

Ao atuar nas branches `cli` ou `api`, **JAMAIS** execute `git reset --hard main` ou `git reset --hard origin/main` a menos que você tenha confirmado explicitamente (via `git diff`) que não há arquivos exclusivos ("Deltas") naquela branch.

* *Verificação:* `git diff --name-status main...HEAD` (Se houver arquivos listados, eles são sagrados).

### Regra Nº 2: A Resolução de Conflitos é Aditiva

Ao mergear `main` em `api` ou `cli`, conflitos no `pyproject.toml` são comuns.

* **Nunca** escolha "Accept Theirs" (Main) cegamente.
* **Nunca** escolha "Accept Ours" (Branch) cegamente.
* **Sempre** faça a fusão: Mantenha as ferramentas de Dev da Main **E** as bibliotecas de runtime da Branch.

### Regra Nº 3: Onde criar novas Branches?

* **Feature de Infra/Scripts/Docs:** Crie a partir da `main`. (`feat/novo-linter`)
* **Feature de API (Endpoints):** Crie a partir da `api`. (`feat/api-login`)
* **Feature de CLI (Comandos Typer):** Crie a partir da `cli`. (`feat/cli-export`)

**Se você criar uma feature de API na `main`, você quebrará a CLI.**

-----

## 4\. ESTUDO DE CASO: O Incidente da Sprint 1

**O Erro:**
Durante a refatoração P26, para "limpar" a branch `cli`, executamos um Hard Reset para a `main`.
**A Consequência:**
O código do Typer (`src/main.py`) e o workflow de deploy foram apagados. A `cli` virou um clone da `main`.
**A Solução:**
Tivemos que usar `git reflog`, encontrar o hash antigo, criar uma branch de resgate (`recovery-cli`) e fazer *cherry-pick* dos arquivos perdidos.

**Lição:** *Sincronização não é clonagem. Sincronização é fusão.*

-----

## 5\. A ESTRUTURA DE PASTAS FINAL (Pós-P26)

Para evitar confusão entre a branch `cli` e a pasta `scripts/cli`:

```text
/ (Raiz do Projeto)
├── scripts/                # [INFRA] Automação SRE (Existe em TODAS as branches)
│   ├── cli/                # FERRAMENTAS DE DEV (Doctor, Audit, Git-Sync)
│   └── core/               # Lógica dos scripts de Dev
│
├── src/                    # [PRODUTO] O Código da Aplicação (O Delta)
│   └── main.py             # Na branch 'cli' = Typer. Na branch 'api' = FastAPI.
│                           # Na branch 'main' = Inexistente (Geralmente).
│
├── pyproject.toml          # Configuração Híbrida (Dev Tools + Product Deps)
└── Makefile                # Entry point universal
```

-----

Este relatório encerra a documentação da Sprint 1.
**Copie este conteúdo para um arquivo `docs/ARCHITECTURE_TRIAD.md` na próxima oportunidade.** Ele salvará vidas.
