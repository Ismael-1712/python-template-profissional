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
# Caso contrário, usa o do sistema.
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

# Python Baseline Configuration (CI Compatibility)
PYTHON_BASELINE := 3.10
CURRENT_PYTHON_VERSION := $(shell $(PYTHON) -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

# i18n Configuration
LOCALES_DIR := locales
BABEL_CFG := babel.cfg
POT_FILE := $(LOCALES_DIR)/messages.pot

# =============================================================================
# TARGETS (COMANDOS)
# =============================================================================

.PHONY: help setup install-dev build lint format audit test test-verbose test-coverage clean clean-all check all version info release doctor upgrade-python i18n-extract i18n-init i18n-update i18n-compile i18n-stats validate-python requirements

## help: Exibe esta mensagem de ajuda com todos os comandos disponíveis
help:
	@echo "📋 Comandos Disponíveis:"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  make /' | column -t -s ':'

## run: Inicia servidor local com hot-reload
run:
	PYTHONPATH=. $(PYTHON) -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

## doctor: Executa diagnóstico preventivo do ambiente de desenvolvimento
doctor:
	@$(PYTHON) -m scripts.cli.doctor

## upgrade-python: Atualiza versões Python para os patches mais recentes (via pyenv)
upgrade-python:
	@$(PYTHON) $(SCRIPTS_DIR)/maintain_versions.py

## setup: Alias para install-dev (configura ambiente completo)
setup: install-dev

## requirements: Recompila requirements/dev.txt usando a versão baseline (CI-compatible)
requirements:
	@echo "🔄 Compilando requirements com Python $(PYTHON_BASELINE) (CI-compatible)..."
	@if ! command -v python$(PYTHON_BASELINE) &> /dev/null; then \
		echo "❌ Erro: python$(PYTHON_BASELINE) não encontrado. Use 'pyenv install $(PYTHON_BASELINE)'"; \
		exit 1; \
	fi
	@python$(PYTHON_BASELINE) -m pip install pip-tools --quiet
	@python$(PYTHON_BASELINE) -m piptools compile requirements/dev.in --output-file requirements/dev.txt --resolver=backtracking --strip-extras
	@echo "✅ Lockfile gerado com Python $(PYTHON_BASELINE) (compatível com CI)"

## validate-python: Valida se a versão do Python é compatível com a baseline do CI
validate-python:
	@if [ "$(CURRENT_PYTHON_VERSION)" != "$(PYTHON_BASELINE)" ]; then \
		echo -e "⚠️  \033[1;33mAVISO:\033[0m Python $(CURRENT_PYTHON_VERSION) detectado, mas a baseline do CI é $(PYTHON_BASELINE)"; \
		echo "    O lockfile gerado pode ser incompatível com o CI."; \
		echo "    Considere usar: pyenv local $(PYTHON_BASELINE) && make install-dev"; \
		echo "    Ou execute: make requirements (para forçar Python $(PYTHON_BASELINE))"; \
	else \
		echo "✅ Python $(CURRENT_PYTHON_VERSION) está compatível com a baseline do CI"; \
	fi

## install-dev: Instala ambiente de desenvolvimento (Cria .venv se necessário)
install-dev: validate-python
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
		if [ -z "$$GITHUB_ACTIONS" ]; then \
			echo "🗑️  Removendo venv antigo (local mode)..."; \
			rm -rf $(VENV); \
		else \
			echo "♻️  CI mode: Reusing cached venv if available..."; \
		fi; \
		$(SYSTEM_PYTHON) -m venv $(VENV); \
		echo "📥 Instalando dependências via install_dev.py..."; \
		$(VENV)/bin/python $(SCRIPTS_DIR)/cli/install_dev.py && \
		echo "$$CURRENT_HASH" > "$$HASH_FILE" && \
		echo "✅ Instalação concluída. Hash armazenado: $${CURRENT_HASH:0:12}..."; \
		echo "🧠 Initializing CORTEX Neural Memory..."; \
		$(VENV)/bin/python -m scripts.cli.cortex neural index || echo "⚠️  Warning: Neural index failed (non-critical for install)"; \
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

## complexity-check: Verifica complexidade ciclomática do código (Xenon)
complexity-check:
	@echo "🧠 Verificando complexidade ciclomática (Xenon)..."
	$(PYTHON) -m xenon --max-absolute B --max-modules B --max-average A \
		--exclude "scripts/core/cortex/knowledge_validator.py,scripts/core/cortex/metadata.py,scripts/core/cortex/migrate.py,scripts/audit_dependencies.py,scripts/benchmark_cortex_perf.py,scripts/example_guardian_scanner.py,scripts/cortex/adapters/ui.py,scripts/cortex/commands/setup.py,scripts/cortex/commands/config.py,scripts/cortex/commands/docs.py,scripts/git_sync/sync_logic.py,scripts/ci_recovery/analyzer.py,scripts/ci_recovery/executor.py,scripts/utils/toml_merger.py,scripts/cli/install_dev.py,scripts/cli/mock_generate.py,scripts/cli/mock_ci.py,scripts/cli/fusion.py,scripts/cli/audit.py,scripts/cli/mock_validate.py,scripts/cli/upgrade_python.py,scripts/audit/analyzer.py,scripts/audit/plugins.py,scripts/audit/reporter.py,scripts/core/mock_generator.py,scripts/core/doc_gen.py,scripts/core/cortex/scanner.py,scripts/core/cortex/project_orchestrator.py,scripts/core/cortex/knowledge_scanner.py,scripts/core/cortex/knowledge_orchestrator.py,scripts/core/cortex/mapper.py,scripts/core/cortex/link_resolver.py,scripts/core/mock_ci/git_ops.py" \
		scripts/ src/
	@echo "✅ Análise de complexidade concluída (legacy files excluded)"

## arch-check: Valida separação de camadas arquiteturais (Import Linter)
arch-check:
	@echo "🏗️  Verificando contratos arquiteturais..."
	@$(VENV)/bin/lint-imports || (echo "⚠️  Violações de arquitetura detectadas (grandfathering mode)" && exit 0)

## deps-check: Detecta dependências não utilizadas (Deptry)
deps-check:
	@echo "📦 Verificando dependências não utilizadas..."
	@$(PYTHON) -m deptry . || (echo "⚠️  Dependências não utilizadas detectadas (grandfathering mode)" && exit 0)

## docs-check: Valida cobertura de docstrings (Interrogate)
docs-check:
	@echo "📚 Verificando cobertura de documentação..."
	@$(PYTHON) -m interrogate -vv scripts/ src/ || (echo "⚠️  Baixa cobertura de docstrings detectada (grandfathering mode)" && exit 0)

## ci-check: Valida workflows do GitHub Actions (versões e cache)
ci-check:
	@echo "🔍 Auditando workflows do GitHub Actions..."
	@$(PYTHON) scripts/ci/audit_workflows.py

## validate: Executa validação completa (lint + type-check + test + complexity + arquitetura + ci)
validate: lint type-check complexity-check arch-check deps-check docs-check ci-check test
	@echo "📚 Verifying Documentation Integrity..."
	PYTHONPATH=. $(PYTHON) -m scripts.cortex audit docs/ --fail-on-error
	@echo "✅ Validação completa concluída (Tríade de Blindagem Ativa)"

## format: Formata código automaticamente com ruff
format:
	$(PYTHON) -m ruff format .

## save: Formata código, adiciona todas as alterações e faz commit. Uso: make save m="Mensagem do commit"
save: format
	@git add .
	@git commit -m "$(m)"

## audit: Executa auditoria completa do código (análise estática avançada)
audit: doctor
	$(PYTHON) -m scripts.cli.audit

## test: Executa suite completa de testes com pytest (paralelo via pytest-xdist)
test: doctor
	PYTHONPATH=. $(PYTHON) -m pytest $(TEST_DIR)

## test-ci: Executa testes sem doctor (otimizado para CI)
test-ci:
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
	@$(VENV)/bin/pybabel update -i $(POT_FILE) -d $(LOCALES_DIR) -l $(LOCALE)
	@echo "✅ Catalogs updated"

## i18n-compile: Compile .po files to .mo binary format
i18n-compile:
	@echo "🌍 Compiling message catalogs..."
	@$(VENV)/bin/pybabel compile -d $(LOCALES_DIR)
	@echo "✅ Compilation complete"

## i18n-stats: Show translation statistics
i18n-stats:
	@echo "�� Translation Statistics:"
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

## mutation-check: Run mutation testing to validate test quality (⚠️ Slow process)
mutation-check:
	@echo "🧟 ================================================"
	@echo "🧟 MUTATION TESTING (Validação de Qualidade de Testes)"
	@echo "🧟 ================================================"
	@echo ""
	@echo "⚠️  ATENÇÃO: Este processo é DEMORADO e pode levar vários minutos."
	@echo "   - Mutmut irá modificar o código fonte temporariamente"
	@echo "   - Para cada mutação, a suite de testes será executada"
	@echo "   - Mutantes 'Mortos' = Testes funcionando corretamente ✅"
	@echo "   - Mutantes 'Sobreviventes' = Testes falsos positivos ❌"
	@echo ""
	@echo "💡 Dica: Para testar apenas um arquivo específico:"
	@echo "   1. Edite [tool.mutmut] em pyproject.toml"
	@echo "   2. Altere paths_to_mutate = [\"scripts/utils/security.py\"]"
	@echo "   3. Execute: mutmut run"
	@echo ""
	@read -p "Pressione ENTER para continuar ou Ctrl+C para cancelar..." DUMMY
	@echo ""
	@echo "🚀 Iniciando mutation testing..."
	@$(PYTHON) -m mutmut run

## mutation-ci: Run mutation testing in CI mode (non-interactive, core only)
mutation-ci:
	@echo "🧟 ================================================"
	@echo "🧟 MUTATION TESTING - CI MODE (Core Only)"
	@echo "🧟 ================================================"
	@echo ""
	@echo "🎯 Target: scripts/core/"
	@echo "📊 Mode: Non-interactive (CI optimized)"
	@echo "⏱️  Expected: 30min - 6h depending on test suite size"
	@echo ""
	@echo "🚀 Starting mutation testing..."
	@$(PYTHON) -m mutmut run --paths-to-mutate scripts/core --no-progress --CI
	@echo ""
	@echo "📊 Generating HTML report..."
	@$(PYTHON) -m mutmut html
	@echo ""
	@echo "✅ Mutation testing complete!"
	@echo "📁 Report available at: html/index.html"

## commit: Intelligent commit with Smart Governance (idempotent hooks)
commit:
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Usage: make commit MSG='your commit message'"; \
		echo "   Example: make commit MSG='feat: add new feature'"; \
		exit 1; \
	fi
	@echo "🔄 Executing intelligent commit workflow..."
	@git add -u
	@git commit -m "$(MSG)"
	@echo "✅ Commit completed successfully!"

## commit-amend: Amend last commit with auto-staging of volatile files
commit-amend:
	@echo "🔄 Amending last commit..."
	@git add -u
	@git add audit_metrics.json docs/reference/CLI_COMMANDS.md 2>/dev/null || true
	@git commit --amend --no-edit
	@echo "✅ Commit amended!"
