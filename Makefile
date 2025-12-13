# =============================================================================
# CONFIGURAÇÃO DO AMBIENTE (VENV AWARE)
# =============================================================================

# Define o shell explicitamente para garantir compatibilidade com sintaxe avançada
SHELL := /bin/bash

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

# i18n Configuration
LOCALES_DIR := locales
BABEL_CFG := babel.cfg
POT_FILE := $(LOCALES_DIR)/messages.pot

# =============================================================================
# TARGETS (COMANDOS)
# =============================================================================

.PHONY: help setup install-dev build lint format audit test test-verbose test-coverage clean clean-all check all version info release doctor upgrade-python i18n-extract i18n-init i18n-update i18n-compile i18n-stats

## help: Exibe esta mensagem de ajuda com todos os comandos disponíveis
help:
	@echo "📋 Comandos Disponíveis:"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  make /' | column -t -s ':'

## doctor: Executa diagnóstico preventivo do ambiente de desenvolvimento
doctor:
	@$(PYTHON) $(SCRIPTS_DIR)/doctor.py

## upgrade-python: Atualiza versões Python para os patches mais recentes (via pyenv)
upgrade-python:
	@$(PYTHON) $(SCRIPTS_DIR)/maintain_versions.py

## setup: Alias para install-dev (configura ambiente completo)
setup: install-dev

## install-dev: Instala ambiente de desenvolvimento (Cria .venv se necessário)
install-dev:
	@echo "🔧 Verificando ambiente virtual..."
	@REQUIREMENTS_IN="requirements/dev.in"; \
	HASH_FILE="$(VENV)/.install_complete"; \
	if [ ! -f "$$REQUIREMENTS_IN" ]; then \
		echo "❌ Erro: $$REQUIREMENTS_IN não encontrado!"; \
		exit 1; \
	fi; \
	CURRENT_HASH=$$(sha256sum "$$REQUIREMENTS_IN" 2>/dev/null | cut -d' ' -f1 || md5sum "$$REQUIREMENTS_IN" 2>/dev/null | cut -d' ' -f1); \
	if [ -z "$$CURRENT_HASH" ]; then \
		echo "⚠️  Aviso: Comando de hash não disponível. Usando validação baseada em timestamp."; \
		CURRENT_HASH=$$(stat -c %Y "$$REQUIREMENTS_IN" 2>/dev/null || stat -f %m "$$REQUIREMENTS_IN" 2>/dev/null); \
	fi; \
	NEEDS_INSTALL=false; \
	if [ ! -f "$$HASH_FILE" ]; then \
		echo "📦 Marcador de instalação não encontrado. Instalação necessária."; \
		NEEDS_INSTALL=true; \
	else \
		STORED_HASH=$$(cat "$$HASH_FILE" 2>/dev/null); \
		if [ "$$CURRENT_HASH" != "$$STORED_HASH" ]; then \
			echo "🔄 Dependências alteradas detectadas (hash: $${CURRENT_HASH:0:12}...). Atualizando ambiente..."; \
			NEEDS_INSTALL=true; \
		else \
			echo "✅ Ambiente sincronizado (hash: $${CURRENT_HASH:0:12}...). Nenhuma ação necessária."; \
		fi; \
	fi; \
	if [ "$$NEEDS_INSTALL" = "true" ]; then \
		echo "🚀 Iniciando instalação/atualização do ambiente..."; \
		rm -rf $(VENV); \
		$(SYSTEM_PYTHON) -m venv $(VENV); \
		echo "📥 Instalando dependências via install_dev.py..."; \
		$(VENV)/bin/python $(SCRIPTS_DIR)/cli/install_dev.py && \
		echo "$$CURRENT_HASH" > "$$HASH_FILE" && \
		echo "✅ Instalação concluída. Hash armazenado: $${CURRENT_HASH:0:12}..."; \
	fi

## build: Constrói pacote distribuível (wheel + sdist)
build:
	$(PYTHON) -m build

## release: Publica release semântico (CI/CD apenas)
release:
	$(VENV)/bin/semantic-release publish

## lint: Executa verificação de código com ruff (check apenas)
lint:
	PYTHONPATH=. $(PYTHON) -m ruff check .

## type-check: Executa verificação de tipos com mypy
type-check:
	$(PYTHON) -m mypy scripts/ src/ tests/

## validate: Executa validação completa (lint + type-check + test)
validate: lint type-check test
	@echo "✅ Validação completa concluída"

## format: Formata código automaticamente com ruff
format:
	$(PYTHON) -m ruff format .

## save: Formata código, adiciona todas as alterações e faz commit. Uso: make save m="Mensagem do commit"
save: format
	@git add .
	@git commit -m "$(m)"

## audit: Executa auditoria completa do código (análise estática avançada)
audit: doctor
	PYTHONPATH=. $(PYTHON) $(SCRIPTS_DIR)/code_audit.py

## test: Executa suite completa de testes com pytest
test: doctor
	PYTHONPATH=. $(PYTHON) -m pytest $(TEST_DIR)

## test-verbose: Executa testes em modo verboso
test-verbose:
	PYTHONPATH=. $(PYTHON) -m pytest -v $(TEST_DIR)

## test-coverage: Executa testes com relatório de cobertura
test-coverage:
	PYTHONPATH=. $(PYTHON) -m pytest --cov=$(SRC_DIR) $(TEST_DIR)

## docs-serve: Inicia servidor local de documentação (http://127.0.0.1:8000)
docs-serve:
	$(VENV)/bin/mkdocs serve

## docs-build: Gera site estático de documentação (pasta site/)
docs-build:
	$(VENV)/bin/mkdocs build

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
	rm -rf site 2>/dev/null || true

## clean-all: Limpeza profunda incluindo dependências compiladas e ambiente virtual
clean-all: clean
	rm -f requirements/dev.txt
	rm -rf $(VENV)

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

# =============================================================================
# INTERNATIONALIZATION (i18n) TARGETS
# =============================================================================

## i18n-extract: Extract translatable strings to messages.pot template
i18n-extract:
	@echo "🌍 Extracting translatable strings..."
	@$(VENV)/bin/pybabel extract -F $(BABEL_CFG) -o $(POT_FILE) .
	@echo "✅ Extraction complete: $(POT_FILE)"

## i18n-init: Initialize new language catalog (usage: make i18n-init LOCALE=en_US)
i18n-init:
	@if [ -z "$(LOCALE)" ]; then \
		echo "❌ Error: LOCALE not specified. Usage: make i18n-init LOCALE=en_US"; \
		exit 1; \
	fi
	@echo "🌍 Initializing catalog for locale: $(LOCALE)..."
	@$(VENV)/bin/pybabel init -i $(POT_FILE) -d $(LOCALES_DIR) -l $(LOCALE)
	@echo "✅ Catalog initialized: $(LOCALES_DIR)/$(LOCALE)/LC_MESSAGES/messages.po"

## i18n-update: Update existing language catalogs with new strings
i18n-update:
	@echo "🌍 Updating existing catalogs..."
	@$(VENV)/bin/pybabel update -i $(POT_FILE) -d $(LOCALES_DIR)
	@echo "✅ Catalogs updated"

## i18n-compile: Compile .po files to .mo binary format
i18n-compile:
	@echo "🌍 Compiling message catalogs..."
	@$(VENV)/bin/pybabel compile -d $(LOCALES_DIR)
	@echo "✅ Compilation complete"

## i18n-stats: Show translation statistics
i18n-stats:
	@echo "🌍 Translation Statistics:"
	@for po_file in $(LOCALES_DIR)/*/LC_MESSAGES/*.po; do \
		if [ -f "$$po_file" ]; then \
		echo ""; \
		echo "📄 $$po_file:"; \
		$(VENV)/bin/msgfmt --statistics $$po_file 2>&1 | head -1; \
	fi \
done

## test-matrix: Run tests across multiple Python versions (requires tox)
test-matrix:
	$(PYTHON) -m tox
## commit: Intelligent commit with auto-staging of volatile files (OPTIONAL)
commit:
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Usage: make commit MSG='your commit message'"; \
		echo "   Example: make commit MSG='feat: add new feature'"; \
		exit 1; \
	fi
	@echo "🔄 Executing intelligent commit workflow..."
	@git add -u
	@MAX_TRIES=2; \
	for i in $$(seq 1 $$MAX_TRIES); do \
		echo "🔄 Attempt $$i of $$MAX_TRIES"; \
		git commit -m "$(MSG)" && break || \
		if [ $$i -eq $$MAX_TRIES ]; then \
			echo "❌ Commit failed after validation"; \
			exit 1; \
		fi; \
		echo "⏳ Re-staging files modified by hooks..."; \
		git add audit_metrics.json docs/reference/CLI_COMMANDS.md 2>/dev/null || true; \
	done
	@echo "✅ Commit completed successfully!"

## commit-amend: Amend last commit with auto-staging of volatile files
commit-amend:
	@echo "🔄 Amending last commit..."
	@git add -u
	@git add audit_metrics.json docs/reference/CLI_COMMANDS.md 2>/dev/null || true
	@git commit --amend --no-edit
	@echo "✅ Commit amended!"
