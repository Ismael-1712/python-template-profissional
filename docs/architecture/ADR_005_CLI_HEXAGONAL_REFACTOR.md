---
type: arch
status: active
id: adr-005-cli-hexagonal-refactor
title: Hexagonal CLI Architecture Refactoring
author: Engenheiro-Academico
date: '2025-12-30'
version: 1.0.0
context_tags:
  - architecture
  - cli
  - refactoring
linked_code:
  - scripts/cortex/cli.py
  - scripts/cortex/adapters/ui.py
---

# Architecture Decision Record 005: Hexagonal CLI

## Status
Accepted

## Context
The previous CLI implementation in `scripts/cortex/cli.py` was a monolithic script (1700+ lines) mixing:
1. Argument parsing (Typer)
2. Business logic instantiations
3. UI presentation logic (print/echo)
4. Global state configuration (`_project_root`)

This violation of Separation of Concerns made unit testing impossible without heavy mocking of the entire filesystem and stdout.

## Decision
We decided to refactor the CLI towards a **Hexagonal Architecture** approach:

1.  **Adapter Pattern for UI:** Extracted all presentation logic to `scripts/cortex/adapters/ui.py` (UIPresenter class).
2.  **Dependency Injection:** Removed global state and implemented `typer.Context` injection for `project_root`.
3.  **Thin CLI:** The CLI commands now only handle orchestration and delegation, containing zero business logic.

## Consequences
### Positive
* **Testability:** Created a dedicated test suite `tests/test_ui_adapter.py` with 100% coverage for UI logic.
* **Maintainability:** CLI file size reduced by ~20%.
* **Safety:** Strict typing (Mypy) enabled across the entire module.

### Negative
* **Verbosity:** Slightly more boilerplate code to instantiate the Presenter and Context.

## Compliance
* **Linting:** 100% Green (Ruff).
* **Typing:** 100% Green (Mypy Strict).
* **Tests:** 100% Pass.
