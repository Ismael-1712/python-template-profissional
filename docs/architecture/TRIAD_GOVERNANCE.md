# MANIFESTO DA TRÍADE: Governança Arquitetural

## 🏛️ Constituição do Projeto

Este documento estabelece os princípios fundamentais de organização e governança do projeto Python Template Profissional, baseado no modelo da **Tríade Arquitetural**.

---

## 🎯 Visão Geral

O projeto é estruturado em **três branches principais**, cada uma com propósito e responsabilidades distintas:

### 1. **Branch `main`** - Núcleo Estável

- **Propósito**: Núcleo minimalista e estável do projeto
- **Conteúdo**: Estrutura básica de pacote Python, configurações essenciais
- **Filosofia**: Menos é mais - mantém apenas o essencial
- **Proteção**: Base imutável que serve de fundação para as demais branches

### 2. **Branch `cli`** - Ferramental de Desenvolvimento

- **Propósito**: Scripts, ferramentas de automação e utilitários DevOps
- **Conteúdo**:
  - Scripts de auditoria de código
  - Ferramentas de sincronização Git
  - Geradores de mocks para testes
  - Dashboards de métricas
  - Utilitários de CI/CD
- **Filosofia**: Produtividade através de automação
- **Isolamento**: Não contamina `main` ou `api`

### 3. **Branch `api`** - Aplicação de Produção

- **Propósito**: Código da aplicação final/API REST
- **Conteúdo**:
  - Endpoints da API
  - Lógica de negócio
  - Modelos de dados
  - Serviços de aplicação
- **Filosofia**: Código limpo e pronto para produção
- **Isolamento**: Não contamina `main` ou `cli`

---

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

---

## 📋 Diretrizes de Desenvolvimento

### Quando Trabalhar em Cada Branch

#### Trabalhe em `main` quando

- Modificar configurações base do projeto (pyproject.toml, .gitignore)
- Atualizar dependências core
- Ajustar estrutura de pastas fundamental
- Modificar documentação arquitetural

#### Trabalhe em `cli` quando

- Criar/modificar scripts de automação
- Desenvolver ferramentas de auditoria
- Implementar utilitários de desenvolvimento
- Adicionar comandos ao Makefile relacionados a DevOps

#### Trabalhe em `api` quando

- Desenvolver endpoints da API
- Implementar lógica de negócio
- Criar modelos de dados
- Adicionar serviços de aplicação

### Workflow de Desenvolvimento

```bash
# 1. Sempre comece de main
git checkout main
git pull

# 2. Para ferramentas
git checkout cli
git pull
# desenvolva suas ferramentas
git commit -m "feat(cli): adiciona nova ferramenta"

# 3. Para aplicação
git checkout api
git pull
# desenvolva sua aplicação
git commit -m "feat(api): adiciona novo endpoint"

# 4. Use o robô para propagar mudanças de main
python scripts/smart_git_sync.py
```

---

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

---

## 🎓 Princípios Filosóficos

### 1. **Separação de Preocupações**

Cada branch tem uma responsabilidade única e bem definida.

### 2. **Menor Privilégio**

Código especializado não tem acesso ao núcleo.

### 3. **Unidirecionalidade**

Mudanças fluem apenas de dentro (main) para fora (cli/api).

### 4. **Imutabilidade Relativa**

O núcleo muda raramente; as especializações evoluem rapidamente.

### 5. **Transparência**

Todas as propagações são explícitas e auditáveis.

---

## 📚 Referências

- **Implementação**: `scripts/smart_git_sync.py`
- **Configuração**: `scripts/smart_git_sync_config.yaml`
- **Documentação Técnica**: `docs/reference/git_sync.md`
- **Histórico**: `docs/history/sprint_1_foundation/`

---

## ✅ Validação da Arquitetura

Para verificar a integridade da Tríade:

```bash
# Verificar isolamento das branches
git log --oneline --graph --all --decorate

# Auditar propagações
python scripts/smart_git_sync.py --audit

# Validar estrutura
python scripts/doctor.py
```

---

**Data de Estabelecimento**: Sprint 1 - Foundation Phase
**Versão**: 1.0
**Status**: Constituição Ativa
**Última Atualização**: Novembro 2025
