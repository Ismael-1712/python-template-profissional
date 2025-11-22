# =============================================================================
# CONFIGURAÇÃO DO AMBIENTE (VENV AWARE)
# =============================================================================

# Define o caminho do ambiente virtual
VENV := .venv
SYSTEM_PYTHON := python3

# Lógica de Detecção:
# Se o binário do python existir dentro do .venv, usa ele.
# Caso contrário, usa o do sistema (mas a maioria dos targets falhará ou criará o venv).
ifneq ($(wildcard $(VENV)/bin/python),)
	PYTHON := $(VENV)/bin/python
else
	PYTHON := $(SYSTEM_PYTHON)
endif

# Diretórios do Projeto
SRC_DIR := src
TEST_DIR := tests
SCRIPTS_DIR := scripts

# Artefatos para limpeza
BUILD_ARTIFACTS := build dist *.egg-info

# =============================================================================
# TARGETS (COMANDOS)
# =============================================================================

.PHONY: help setup install-dev build lint format audit test test-verbose test-coverage clean clean-all check all version info release

## help: Exibe esta mensagem de ajuda com todos os comandos disponíveis
help:
	@echo "📋 Comandos Disponíveis:"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  make /' | column -t -s ':'

## setup: Alias para install-dev (configura ambiente completo)
setup: install-dev

## install-dev: Instala ambiente de desenvolvimento (Cria .venv se necessário)
install-dev:
	@echo "🔧 Verificando ambiente virtual..."
	@if [ ! -f "$(VENV)/bin/python" ]; then \
		echo "📦 Criando .venv..."; \
		$(SYSTEM_PYTHON) -m venv $(VENV); \
	fi
	@echo "🚀 Instalando dependências no ambiente virtual..."
	@# Forçamos o uso do Python do Venv aqui para garantir que o pip instale no lugar certo
	@$(VENV)/bin/python $(SCRIPTS_DIR)/install_dev.py

## build: Constrói pacote distribuível (wheel + sdist)
build:
	$(PYTHON) -m build

## release: Publica release semântico (CI/CD apenas)
release:
	$(VENV)/bin/semantic-release publish

## lint: Executa verificação de código com ruff (check apenas)
lint:
	PYTHONPATH=. $(PYTHON) -m ruff check .

## format: Formata código automaticamente com ruff
format:
	$(PYTHON) -m ruff format .

## audit: Executa auditoria completa do código (análise estática avançada)
audit:
	PYTHONPATH=. $(PYTHON) $(SCRIPTS_DIR)/code_audit.py

## test: Executa suite completa de testes com pytest
test:
	PYTHONPATH=. $(PYTHON) -m pytest $(TEST_DIR)

## test-verbose: Executa testes em modo verboso
test-verbose:
	PYTHONPATH=. $(PYTHON) -m pytest -v $(TEST_DIR)

## test-coverage: Executa testes com relatório de cobertura
test-coverage:
	PYTHONPATH=. $(PYTHON) -m pytest --cov=$(SRC_DIR) $(TEST_DIR)

## clean: Remove artefatos de build, cache e arquivos temporários
clean:
	rm -rf $(BUILD_ARTIFACTS)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov .coverage 2>/dev/null || true
	rm -f audit_report_*.json sync_report_*.json 2>/dev/null || true

## clean-all: Limpeza profunda incluindo dependências compiladas
clean-all: clean
	rm -f requirements/dev.txt

## check: Executa verificação rápida (lint + test)
check: lint test

## all: Executa pipeline completo (install-dev + lint + test)
all: install-dev lint test

## version: Exibe versões do Python e ferramentas
version:
	@echo "🐍 Python: $$($(PYTHON) --version)"
	@echo "📦 Pip:    $$($(PYTHON) -m pip --version)"

## info: Exibe informações sobre o ambiente atual
info:
	@echo "Environment:"
	@echo "  PYTHON: $(PYTHON)"
	@echo "  VENV:   $(VENV)"
