
### 📄 Arquivo Corrigido: `README.md` (v2.1 - Final)

**Copie e substitua todo o conteúdo do seu arquivo `README.md`:**

````markdown
# meu_projeto_placeholder

> 🚀 Template Python Profissional com Pipeline de Qualidade Integrado

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Quality](https://img.shields.io/badge/code%20quality-enforced-brightgreen.svg)](https://github.com/Ismael-1712/python-template-profissional/actions/workflows/ci.yml)
````

---

## ⚡ Quick Start

```bash
# 1. Clone o repositório
git clone [https://github.com/usuario/meu_projeto_placeholder.git](https://github.com/usuario/meu_projeto_placeholder.git)
cd meu_projeto_placeholder

# 2. Configure o ambiente (cria venv + instala dependências)
make setup

# 3. Ative o ambiente virtual
source .venv/bin/activate

# 4. Valide a instalação
make test
````

**Pronto\!** Você está preparado para desenvolver. 🎉

-----

## 📊 Dashboard Interativo

O projeto inclui um **Dashboard de Auditoria** que permite visualizar métricas de qualidade de código em formato HTML interativo.

### Como Usar

```bash
# Exibir métricas no console
python3 scripts/audit_dashboard.py

# Gerar relatório HTML standalone (recomendado)
python3 scripts/audit_dashboard.py --export-html
```

O arquivo HTML gerado (`audit_dashboard_YYYYMMDD_HHMMSS.html`) pode ser:

- ✅ Aberto em qualquer navegador (sem necessidade de servidor)
- ✅ Compartilhado com a equipe via e-mail ou repositório
- ✅ Integrado em pipelines CI/CD para tracking de métricas

**Métricas Disponíveis:**

- 📊 Auditorias realizadas
- 🛡️ Falhas evitadas
- ⏱️ Tempo economizado
- 📈 Taxa de sucesso

-----

## 🌍 Internationalization (i18n)

O projeto suporta nativamente **Português (pt_BR)** e **Inglês (en_US)**.
O idioma é detectado automaticamente via variável de ambiente.

**Como usar (Linux/WSL):**

```bash
# Para rodar em Inglês (Sessão única)
LANGUAGE=en_US python3 scripts/smart_git_sync.py

# Para configurar permanentemente
export LANGUAGE=en_US
```

-----

## 🛠️ Comandos de Engenharia

Todos os comandos do projeto são gerenciados via **Makefile** para consistência e automação:

| Comando | Descrição |
|:---|:---|
| `make setup` | Configura ambiente completo (alias para `install-dev`) |
| `make test` | Executa suite completa de testes com pytest |
| `make test-coverage` | Testes com relatório de cobertura |
| `make lint` | Verifica código com ruff (análise estática) |
| `make format` | Formata código automaticamente com ruff |
| `make audit` | Auditoria completa de segurança e qualidade |
| `make check` | Validação rápida (lint + test) - **use antes do push\!** |
| `make release` | **(CI Only)** Publica versão e gera changelog |
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

-----

## 🤝 Fluxo de Trabalho & Branches

### Política de Qualidade

**⚠️ Regra de Ouro:** Nenhum código é aceito sem passar pelo `make audit` com sucesso.

### 🔄 Estratégia de Branches (Automated Flow)

Este projeto utiliza um sistema de **Auto-Propagação** para manter as variantes sincronizadas.

1. **`main`**: A fonte da verdade (Branch Protegida).
2. **`api` / `cli`**: Variantes geradas automaticamente.

**🛑 NÃO faça merge manual para `api` ou `cli`\!**
Sempre que um Pull Request é aceito na `main`, um robô (GitHub Actions) propaga as mudanças automaticamente para as branches filhas, respeitando as diferenças de cada template.

### Pipeline de Desenvolvimento

```bash
# 1. Crie uma branch para sua feature
git checkout -b feat/minha-melhoria

# 2. Desenvolva e Formate
make format

# 3. Execute validação local
make check

# 4. Commit e Push
git add .
git commit -m "feat: descrição seguindo conventional commits"
git push origin feat/minha-melhoria

# 5. Abra o PR para a 'main'. O resto é automático.
```

-----

## 📦 Estrutura do Projeto

```text
.
├── src/                    # Código-fonte principal
├── tests/                  # Testes unitários e de integração
├── scripts/                # Scripts de automação e ferramentas
│   ├── install_dev.py      # Instalador do ambiente de dev
│   └── code_audit.py       # Sistema de auditoria
├── requirements/           # Dependências pinned (pip-tools)
├── docs/                   # Documentação técnica
├── .github/workflows/      # Pipelines CI/CD (Testes, Release, Propagação)
├── Makefile                # Automação de comandos
└── pyproject.toml          # Configuração do projeto
```

-----

## 🔧 Troubleshooting

### Problema: `make: command not found`

**Solução:** Instale o `make` (build-essential no Linux ou Xcode tools no Mac).

### Problema: Ambiente virtual não ativa

**Solução:** Certifique-se de executar o comando de ativação:

```bash
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### Problema: Erro no `semantic-release` localmente

**Causa:** O comando `make release` é otimizado para rodar no GitHub Actions.
**Solução:** Não execute release localmente. Deixe o CI cuidar disso após o merge.

-----

## 📚 Documentação Adicional

- [🔍 Sistema de Auditoria](https://www.google.com/search?q=docs/CODE_AUDIT.md) - Análise estática avançada
- [🧪 Sistema de Mocks](https://www.google.com/search?q=docs/README_test_mock_system.md) - Geração automática de mocks
- [🔄 Smart Git Sync](https://www.google.com/search?q=docs/SMART_GIT_SYNC_GUIDE.md) - Detalhes da sincronização

-----

## 📄 Licença

Este projeto está sob a licença especificada no arquivo [LICENSE](https://www.google.com/search?q=LICENSE).

-----

## 🙏 Agradecimentos

Desenvolvido com ❤️ usando as melhores práticas de engenharia de software Python.

**Stack de Qualidade:**

- 🔍 **ruff** - Linting e formatação ultra-rápidos
- 🧪 **pytest** - Framework de testes moderno
- 🛡️ **Sistema de Auditoria Customizado** - Análise profunda
- 🔧 **pip-tools** - Gestão determinística de dependências

<!-- end list -->
