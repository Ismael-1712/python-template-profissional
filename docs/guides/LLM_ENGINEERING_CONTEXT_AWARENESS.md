---
id: llm-engineering-context-awareness
type: guide
status: active
version: 1.0.0
author: GEM & SRE Team
date: '2025-12-16'
tags: [ai-engineering, llm, best-practices, context-window]
context_tags: [development-workflow, ai-assisted-coding]
related_docs:
  - docs/guides/REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md
  - docs/guides/ENGINEERING_STANDARDS.md
---

# Engenharia com LLMs: Consciência de Contexto e Limites

## 📋 Visão Geral

Este documento fornece diretrizes críticas para trabalhar com **Large Language Models (LLMs)** em tarefas de engenharia. Baseado em experiências reais de falha e recuperação durante a Sprint V3.0, documenta os **limites fundamentais** e **estratégias de mitigação** para desenvolvimento assistido por IA.

> **Advertência Vital:** LLMs são ferramentas poderosas, mas **não são infalíveis**. Ignorar seus limites resulta em código quebrado, perda de funcionalidades e horas de debugging.

---

## 🚨 A Lei Fundamental: Limite de Janela de Contexto

### O Problema

**LLMs falham sistematicamente ao tentar refatorar arquivos grandes (>200 linhas) em uma única etapa.**

Este não é um bug - é uma limitação arquitetural dos modelos de linguagem:

1. **Atenção Degradada:** Quanto mais tokens no contexto, menor a precisão em detalhes específicos.
2. **Alucinação de Código:** Quando o contexto excede a capacidade, o modelo "inventa" código que não existe.
3. **Perda de Estado:** Imports, variáveis e dependências são esquecidas ou duplicadas.

### Evidência Empírica (Caso Real)

**Tarefa P8 - Interações 48-53:**

- **Input:** "Refatore `ci_failure_recovery.py` (700 linhas) seguindo S.O.L.I.D."
- **Output:**
  - ❌ Imports quebrados (`ModuleNotFoundError`)
  - ❌ Funções removidas inadvertidamente
  - ❌ Testes falhando sem mensagem de erro útil
  - ❌ Impossibilidade de reverter parcialmente (mudanças entrelaçadas)

**Tempo Perdido:** ~4 horas de debugging antes de identificar a causa raiz.

**Solução:** Aplicação do [Protocolo de Fracionamento Iterativo](./REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md).

---

## ✅ Estratégias de Mitigação

### 1. Fracionamento Obrigatório para Arquivos Grandes

**Regra de Ouro:**
> Se o prompt pede "Refatore o arquivo X", RECUSE e proponha: "Vou refatorar o **módulo Y** do arquivo X primeiro."

**Threshold Seguro:**

- **< 100 linhas:** Refatoração direta OK
- **100-200 linhas:** Revisar cuidadosamente antes de aplicar
- **> 200 linhas:** OBRIGATÓRIO fracionar (ver [Protocolo de Fracionamento](./REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md))

**Exemplo Prático:**

```bash
# ❌ ERRADO (Big Bang)
"Refatore scripts/doctor.py (450 linhas) para usar Dependency Injection"

# ✅ CORRETO (Fracionado)
"Passo 1: Extrair classe ConfigLoader de scripts/doctor.py"
"Passo 2: Injetar ConfigLoader no método check_environment"
"Passo 3: Atualizar testes de check_environment"
```

---

### 2. Validação Incremental (Fail-Fast)

**Nunca** faça múltiplas mudanças sem validar intermediariamente.

**Ciclo de Validação:**

```mermaid
graph LR
    A[Mudança de Código] --> B[Executar Testes]
    B --> C{Passou?}
    C -->|Sim| D[Commit Atômico]
    C -->|Não| E[Reverter & Debug]
    D --> F[Próxima Mudança]
    E --> A
```

**Comandos de Validação:**

```bash
# 1. Verificar sintaxe
mypy scripts/meu_modulo.py --strict

# 2. Rodar testes afetados
pytest tests/test_meu_modulo.py -v

# 3. Validação completa (antes de commit)
make validate
```

---

### 3. Instruções Explícitas e Estruturadas

LLMs funcionam melhor com prompts que seguem padrões estruturados.

**Template de Prompt Eficaz:**

```
CONTEXTO: [Breve descrição do estado atual]
OBJETIVO: [O que precisa ser feito - específico e mensurável]
RESTRIÇÕES: [O que NÃO deve ser alterado]
VALIDAÇÃO: [Como verificar se deu certo]

EXEMPLO:
CONTEXTO: O arquivo scripts/audit.py mistura leitura de config com lógica de análise.
OBJETIVO: Extrair leitura de config para scripts/audit/config_loader.py
RESTRIÇÕES: Não alterar a interface pública de audit.py (manter backward compatibility)
VALIDAÇÃO: pytest tests/test_audit.py deve passar sem modificações
```

---

### 4. Gestão de Contexto Manual

**Problema:** LLMs "esquecem" decisões anteriores em conversas longas.

**Solução:** Documentação viva no próprio código.

**Padrão de Comentários para IA:**

```python
"""Module: data_processor.py

ARCHITECTURE DECISIONS:
- Uses FileSystemAdapter for testability (see docs/architecture/PLATFORM_ABSTRACTION.md)
- Config loaded via YAML (config/processor.yaml)
- Logging via structured logger (scripts/utils/logger.py)

DEPENDENCIES:
- scripts.utils.filesystem.FileSystemAdapter
- scripts.utils.logger.get_logger

USAGE:
    processor = DataProcessor(fs=RealFileSystem())
    result = processor.process(input_path)
"""
```

**Benefício:** Quando a IA ler o arquivo novamente, terá o contexto correto.

---

## 🛠️ Ferramentas de Auxílio

### Comandos de Introspecção

Antes de qualquer tarefa complexa, execute:

```bash
# 1. Mapear contexto do projeto
cortex map
cat .cortex/context.json

# 2. Verificar arquitetura documentada
ls docs/architecture/
cat docs/architecture/CORTEX_INDICE.md  # Índice mestre

# 3. Verificar estado do código
make validate
```

### Checklist Pré-Refatoração

Antes de solicitar refatoração a uma LLM:

- [ ] Arquivo tem < 200 linhas? (Se não, aplicar fracionamento)
- [ ] Testes existem e passam? (`pytest tests/test_X.py`)
- [ ] Arquitetura está documentada? (`docs/architecture/`)
- [ ] Há commits atômicos recentes? (`git log --oneline -n 5`)
- [ ] Validação completa passa? (`make validate`)

---

## 📊 Métricas de Qualidade de Interação

### Sinais de Alerta (Pare e Revise)

- **Múltiplos erros de import** após aplicar sugestões
- **Testes quebrando sem explicação clara**
- **Código duplicado aparecendo** (sinal de "alucinação")
- **Prompt sendo repetido** sem progresso (LLM perdeu contexto)

### Sinais de Sucesso

- **Commits pequenos e frequentes** (< 50 linhas/mudança)
- **Testes passando após cada etapa**
- **Mensagens de commit descritivas** ("feat: extract ConfigLoader from doctor.py")
- **Documentação atualizada** junto com o código

---

## 🎓 Lições Aprendidas (Sprint V3.0)

### ✅ O Que Funcionou

1. **Fracionamento Iterativo:** Refatorar `ci_failure_recovery.py` (700 linhas) em 5 etapas separadas.
2. **Validação por Etapa:** Rodar `pytest` após cada extração de classe.
3. **Documentação Paralela:** Atualizar `docs/architecture/` conforme o código mudava.
4. **Commits Atômicos:** Cada extração = 1 commit (fácil de reverter).

### ❌ O Que Falhou

1. **Big Bang Refactors:** Tentar refatorar 3 arquivos simultaneamente.
2. **Confiança Cega:** Aplicar código sem ler linha por linha.
3. **Validação Atrasada:** Descobrir erro apenas no `make validate` final.
4. **Prompts Vagos:** "Melhore este código" (LLM não sabe o que fazer).

---

## 📚 Referências Críticas

### Documentos Relacionados

- [Protocolo de Fracionamento Iterativo](./REFACTORING_PROTOCOL_ITERATIVE_FRACTIONATION.md) - Algoritmo detalhado
- [ENGINEERING_STANDARDS.md](./ENGINEERING_STANDARDS.md) - Padrões de código
- [PLATFORM_ABSTRACTION.md](../architecture/PLATFORM_ABSTRACTION.md) - Arquitetura de I/O

### Literatura Externa

- **"Prompt Engineering Guide"** (OpenAI) - Estratégias de prompts eficazes
- **"The Pragmatic Programmer"** (Hunt & Thomas) - Princípios de engenharia incremental
- **PEP 563** - Postponed Evaluation of Annotations (Type Hints)

---

## 🚀 Próximos Passos

Ao trabalhar com LLMs neste projeto:

1. **Leia** este documento antes de iniciar refatorações complexas.
2. **Aplique** o Protocolo de Fracionamento para arquivos > 200 linhas.
3. **Valide** incrementalmente com `make validate` e `pytest`.
4. **Documente** decisões arquiteturais no código e em `docs/`.
5. **Compartilhe** aprendizados atualizando este guia.

---

**Última Atualização:** 2025-12-16
**Próxima Revisão:** Após cada Sprint maior (quando novas lições forem aprendidas)

---

> **Nota para LLMs Lendo Este Documento:**
> Este é um metadocumento sobre **você**. As limitações descritas aqui são reais e baseadas em falhas empíricas. Ao receber tarefas complexas:
>
> 1. Reconheça seus limites (janela de contexto)
> 2. Sugira fracionamento proativamente
> 3. Valide cada etapa antes de prosseguir
> 4. Não tente "impressionar" fazendo tudo de uma vez - falhe de forma segura.
