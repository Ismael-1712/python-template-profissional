---
id: dependency-management
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-21'
context_tags: [dependencies, ci, workflow, best-practices]
linked_code: []
title: Guia de Gerenciamento de Dependências
---

# 📦 Guia de Gerenciamento de Dependências

> **O Caminho Feliz para Adicionar e Manter Dependências no Projeto**

Este guia explica a arquitetura de dependências do projeto e como operar o sistema de "CI Pinning" (Hardening de Dependências) sem frustração.

---

## 🎯 Por Que Três Arquivos de Dependências?

O projeto utiliza uma arquitetura de três camadas para gerenciamento de dependências:

```
┌─────────────────────────────────────────────────────────────┐
│                  ARQUITETURA DE DEPENDÊNCIAS                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📄 pyproject.toml                                          │
│  ├─ Dependências abstratas (produção)                      │
│  ├─ Sem versões fixas (compatibilidade Copier)             │
│  └─ Ex: fastapi, uvicorn[standard], typer[all]             │
│                                                             │
│  📝 requirements/dev.in                                     │
│  ├─ Dependências de desenvolvimento (entrada)              │
│  ├─ Versões pinadas explicitamente                         │
│  └─ Ex: ruff==0.14.10, pytest==9.0.2                       │
│                                                             │
│  🔒 requirements/dev.txt                                    │
│  ├─ Lockfile completo (output do pip-compile)              │
│  ├─ Inclui TODAS as dependências transitivas               │
│  └─ Garante builds 100% determinísticos                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Por Que Essa Separação?

1. **`pyproject.toml`**: Dependências de **produção** (API, CLI). Mantidas abstratas para funcionar como template Copier.
2. **`dev.in`**: Dependências de **desenvolvimento** (pytest, ruff, mypy). Versões fixas para estabilidade.
3. **`dev.txt`**: **Lockfile exato** com hash SHA256 de cada pacote. Garante builds idênticos em qualquer máquina.

---

## ✅ Fluxo de Trabalho: Como Adicionar uma Biblioteca

### Cenário 1: Adicionar Dependência de Produção

**Quando usar:** Bibliotecas que fazem parte da aplicação final (API, CLI, modelos).

```bash
# 1. Edite pyproject.toml manualmente
vim pyproject.toml

# Adicione na seção [project.dependencies]:
dependencies = [
    "fastapi",
    "requests>=2.31.0",  # ← Nova lib
    # ...
]

# 2. Reinstale o ambiente
make install-dev

# 3. Commit ambos os arquivos
git add pyproject.toml
git commit -m "deps: add requests for external API integration"
```

### Cenário 2: Adicionar Dependência de Desenvolvimento

**Quando usar:** Ferramentas de teste, linters, type checkers.

```bash
# 1. Adicione no requirements/dev.in
echo "black==24.1.0" >> requirements/dev.in

# 2. Recompile o lockfile
pip-compile --output-file requirements/dev.txt requirements/dev.in

# 3. Instale as novas dependências
make install-dev

# 4. Commit AMBOS os arquivos (.in e .txt)
git add requirements/dev.in requirements/dev.txt
git commit -m "deps: add black for code formatting"
```

**⚠️ IMPORTANTE:** Se você commitar apenas o `dev.in` sem atualizar o `dev.txt`, o **CI vai falhar**!

---

## 🚨 Por Que o CI Falha Se Não Atualizar o Lockfile?

O sistema de **CI Pinning** implementa verificações de integridade:

```python
# Verificação automática no CI:
def validate_lockfile():
    """Garante que dev.txt foi regenerado após mudanças em dev.in."""
    hash_atual = hash_file("requirements/dev.txt")
    hash_esperado = recompile("requirements/dev.in")

    if hash_atual != hash_esperado:
        raise Error("❌ Lockfile desatualizado! Rode: pip-compile ...")
```

**Objetivo:** Evitar "works on my machine" — todos os desenvolvedores e o CI usam **exatamente as mesmas versões**.

### Exemplo de Erro no CI

```
❌ CI Failed: Dependency Check
Detected changes in requirements/dev.in, but dev.txt is outdated.

Action Required:
  pip-compile --output-file requirements/dev.txt requirements/dev.in
  git add requirements/dev.txt
  git commit --amend --no-edit
```

---

## 🛠️ Comandos Úteis

### Atualizar Todas as Dependências

```bash
# Atualizar para versões mais recentes (respeitando constraints)
pip-compile --upgrade --output-file requirements/dev.txt requirements/dev.in
```

### Adicionar Dependência com Compilação Automática

```bash
# Adicionar + compilar em um comando
echo "httpx==0.25.0" >> requirements/dev.in && \
pip-compile --output-file requirements/dev.txt requirements/dev.in
```

### Verificar Dependências Obsoletas

```bash
# Ver quais pacotes têm updates disponíveis
pip list --outdated
```

### Sincronizar Ambiente com Lockfile

```bash
# Forçar ambiente a refletir exatamente o dev.txt
pip-sync requirements/dev.txt
```

---

## 🔍 Troubleshooting

### Problema 1: `make install-dev` Não Atualiza Dependências

**Sintoma:** Adicionei lib no `dev.in`, mas `pip list` não mostra.

**Solução:**

```bash
# 1. Recompile o lockfile
pip-compile --output-file requirements/dev.txt requirements/dev.in

# 2. Reinstale
make install-dev
```

### Problema 2: CI Falha com "Lockfile Outdated"

**Sintoma:** Push foi rejeitado pelo CI.

**Solução:**

```bash
# Recompile e adicione ao commit
pip-compile --output-file requirements/dev.txt requirements/dev.in
git add requirements/dev.txt
git commit --amend --no-edit
git push --force-with-lease
```

### Problema 3: Conflitos de Versão

**Sintoma:** `pip-compile` falha com erro de resolução.

**Solução:**

```bash
# Ver árvore de dependências
pip install pipdeptree
pipdeptree --warn conflict

# Ajuste versões conflitantes manualmente no dev.in
```

---

## 📊 Benefícios do Sistema

| Benefício | Explicação |
|-----------|------------|
| **Determinismo** | Builds idênticos em qualquer ambiente (local, CI, produção) |
| **Segurança** | Hashes SHA256 previnem ataques de supply chain |
| **Visibilidade** | Dependências transitivas explícitas no lockfile |
| **Manutenibilidade** | Upgrades controlados com `pip-compile --upgrade` |

---

## 🎓 Referências

- **[pip-tools Documentation](https://pip-tools.readthedocs.io/)** - Ferramenta de compilação
- **[PEP 621](https://peps.python.org/pep-0621/)** - Metadados de projetos Python
- **[Dependency Confusion Attacks](https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610)** - Por que pinning importa

---

## 🔗 Documentos Relacionados

- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Fluxo de trabalho de desenvolvimento
- [CODE_AUDIT.md](../CODE_AUDIT.md) - Sistema de auditoria de dependências
- [CI/CD Pipeline](../architecture/) - Arquitetura de integração contínua
