# meu_projeto_placeholder

> 🚀 Template Python Profissional com Pipeline de Qualidade Integrado

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Quality](https://img.shields.io/badge/code%20quality-enforced-brightgreen.svg)]()

---

## 📚 Bem-vindo à Documentação

Este é um template Python profissional que fornece uma base sólida para desenvolvimento de projetos com:

- ✅ **Pipeline de Qualidade Integrado** - CI/CD automatizado com GitHub Actions
- ✅ **Ferramentas Modernas** - Ruff (linting + formatação), pytest, semantic-release
- ✅ **Documentação Automatizada** - MkDocs Material + mkdocstrings
- ✅ **Segurança e Auditoria** - Sistema de code audit integrado
- ✅ **Git Sync Inteligente** - Sincronização automatizada com validação

---

## ⚡ Quick Start

```bash
# 1. Clone o repositório
git clone https://github.com/usuario/meu_projeto_placeholder.git
cd meu_projeto_placeholder

# 2. Configure o ambiente (cria venv + instala dependências)
make setup

# 3. Ative o ambiente virtual
source .venv/bin/activate

# 4. Valide a instalação
make test
```

**Pronto!** Você está preparado para desenvolver. 🎉

---

## 🛠️ Comandos de Engenharia

Todos os comandos do projeto são gerenciados via **Makefile** para consistência e automação:

| Comando | Descrição |
|:--------|:----------|
| `make setup` | Configura ambiente completo (alias para `install-dev`) |
| `make test` | Executa suite completa de testes com pytest |
| `make test-coverage` | Testes com relatório de cobertura |
| `make lint` | Verifica código com ruff (análise estática) |
| `make format` | Formata código automaticamente com ruff |
| `make audit` | Auditoria completa de segurança e qualidade |
| `make check` | Validação rápida (lint + test) - **use antes do push!** |
| `make docs-serve` | Servidor de documentação local |
| `make docs-build` | Build de documentação para produção |
| `make release` | **(CI Only)** Publica versão e gera changelog |
| `make clean` | Remove artefatos de build e cache |
| `make help` | Exibe todos os comandos disponíveis |

---

## 🎯 Comandos Mais Usados

```bash
# Desenvolvimento do dia a dia
make format        # Formatar código
make test          # Rodar testes
make check         # Validação completa antes do commit

# Pipeline de Qualidade Completo
make audit         # Análise profunda de segurança
make test-coverage # Verificar cobertura de testes

# Documentação
make docs-serve    # Visualizar docs localmente
make docs-build    # Gerar site estático
```

---

## 🤝 Fluxo de Trabalho & Branches

### Política de Qualidade

!!! warning "Regra de Ouro"
    Nenhum código é aceito sem passar pelo `make audit` com sucesso.

### 🔄 Estratégia de Branches (Automated Flow)

Este projeto utiliza um sistema de **Auto-Propagação** para manter as variantes sincronizadas.

1. **`main`**: A fonte da verdade (Branch Protegida).
2. **`api` / `cli`**: Variantes geradas automaticamente.

---

## 📖 Navegação da Documentação

### Documentação Técnica

- **[Referência da API](reference/git_sync.md)** - Documentação automática do código
- **[Guias e Tutoriais](SMART_GIT_SYNC_GUIDE.md)** - Documentação técnica detalhada
- **[Code Audit](CODE_AUDIT.md)** - Sistema de auditoria de código
- **[Contributing](../CONTRIBUTING.md)** - Como contribuir para o projeto

### 📊 Sprint 1 - Refatoração de Logging e Ambiente

!!! info "Nova Documentação - Sprint 1"
    Documentação completa da auditoria e refatoração do sistema de logs e detecção de ambiente.

- **[Sprint 1 - Relatório de Auditoria Completo](SPRINT1_AUDITORIA_FASE01.md)** - Análise detalhada de logging, drift e hardcoding
- **[Sprint 1 - Sumário Executivo](SPRINT1_AUDITORIA_SUMARIO.md)** - Visão rápida dos achados principais
- **[Sprint 1 - Guia de Migração](SPRINT1_MIGRATION_GUIDE.md)** - Exemplos práticos de migração para novo sistema

---

## 🚀 Sobre este Template

Este template foi desenvolvido com foco em:

- **Qualidade de Código**: Análise estática rigorosa com Ruff
- **Testes Automatizados**: Cobertura de testes com pytest
- **CI/CD Robusto**: Pipeline completo com GitHub Actions
- **Documentação Viva**: Docs as Code com MkDocs Material
- **Segurança**: Auditoria preventiva antes de commits
- **Developer Experience**: Comandos simples e consistentes via Makefile

---

*Documentação gerada com ❤️ por [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)*
