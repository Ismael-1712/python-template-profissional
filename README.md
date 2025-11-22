# meu_projeto_placeholder

> 🚀 Template Python Profissional com Pipeline de Qualidade Integrado

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Quality](https://img.shields.io/badge/code%20quality-enforced-brightgreen.svg)]()

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
|---------|-----------|
| `make setup` | Configura ambiente completo (alias para `install-dev`) |
| `make test` | Executa suite completa de testes com pytest |
| `make test-coverage` | Testes com relatório de cobertura |
| `make lint` | Verifica código com ruff (análise estática) |
| `make format` | Formata código automaticamente com ruff |
| `make audit` | Auditoria completa de segurança e qualidade |
| `make check` | Validação rápida (lint + test) - **use antes do push!** |
| `make clean` | Remove artefatos de build e cache |
| `make help` | Exibe todos os comandos disponíveis |

### 🎯 Comandos Mais Usados

```bash
# Desenvolvimento do dia a dia
make format        # Formatar código
make test          # Rodar testes
make check         # Validação completa antes do commit

# Pipeline de Qualidade Completo
make audit         # Análise profunda de segurança
make test-coverage # Verificar cobertura de testes
```

---

## 🤝 Fluxo de Trabalho

### Política de Qualidade

**⚠️ Regra de Ouro:** Nenhum código é aceito sem passar pelo `make audit` com sucesso.

### Pipeline Recomendado

```bash
# 1. Desenvolva sua feature
# ... código ...

# 2. Formate o código
make format

# 3. Execute validação local (CI local)
make check

# 4. Auditoria de segurança (obrigatório)
make audit

# 5. Se tudo passar, faça o commit
git add .
git commit -m "feat: minha nova feature"
git push
```

### Integração Contínua

O projeto possui validação automática que executa:

- ✅ Testes unitários (`make test`)
- ✅ Análise estática (`make lint`)
- ✅ Auditoria de segurança (`make audit`)

**Dica:** Execute `make check` localmente antes do push para evitar falhas no CI.

---

## 📦 Estrutura do Projeto

```
.
├── src/                    # Código-fonte principal
├── tests/                  # Testes unitários e de integração
├── scripts/                # Scripts de automação e ferramentas
│   ├── install_dev.py      # Instalador do ambiente de dev
│   ├── code_audit.py       # Sistema de auditoria
│   └── lint_fix.py         # Correção automática de lint
├── requirements/           # Dependências pinned (pip-tools)
├── docs/                   # Documentação técnica
├── Makefile                # Automação de comandos
└── pyproject.toml          # Configuração do projeto
```

---

## 🔧 Troubleshooting

### Problema: `make: command not found`

**Solução:** Instale o `make`:

```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Fedora
sudo dnf install make
```

### Problema: Ambiente virtual não ativa

**Solução:** Certifique-se de executar o comando de ativação:

```bash
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### Problema: Dependências desatualizadas

**Solução:** Reinstale o ambiente:

```bash
make clean-all
make setup
```

---

## 📚 Documentação Adicional

- [🔍 Sistema de Auditoria](docs/CODE_AUDIT.md) - Análise estática avançada
- [🐛 Correção Automática de Lint](docs/LINT_FIX_SYSTEM.md) - Sistema inteligente de fixes
- [🧪 Sistema de Mocks](docs/README_test_mock_system.md) - Geração automática de mocks
- [🔄 Smart Git Sync](docs/SMART_GIT_SYNC_GUIDE.md) - Sincronização inteligente

---

## 🤝 Contribuindo

1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'feat: Add some AmazingFeature'`)
4. Execute `make audit` para validar
5. Push para a branch (`git push origin feature/AmazingFeature`)
6. Abra um Pull Request

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

---

## 📄 Licença

Este projeto está sob a licença especificada no arquivo [LICENSE](LICENSE).

---

## 🙏 Agradecimentos

Desenvolvido com ❤️ usando as melhores práticas de engenharia de software Python.

**Stack de Qualidade:**

- 🔍 **ruff** - Linting e formatação ultra-rápidos
- 🧪 **pytest** - Framework de testes moderno
- 🛡️ **Sistema de Auditoria Customizado** - Análise profunda
- 🔧 **pip-tools** - Gestão determinística de dependências
