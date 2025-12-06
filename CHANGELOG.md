# Changelog

## [Unreleased]

### Added

- **Root Lockdown**: Sistema de proteção da raiz do projeto implementado no CORTEX
  - Valida que apenas arquivos Markdown autorizados residam na raiz
  - Allowlist: `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`, `SECURITY.md`, `CODE_OF_CONDUCT.md`
  - Integrado ao comando `cortex audit` - falha automaticamente se encontrar arquivos não autorizados
  - Mensagens de erro descritivas indicando que documentação deve residir em `docs/`
- **Mecanismo de Backup e Rollback**: Sistema de proteção no `install_dev.py` ([P00.2])
  - Backup automático (`.bak`) de `requirements/dev.txt` antes da compilação
  - Rollback automático se `pip install` falhar
  - Mensagens de log orientadas a UX ("Rollback Ativado") para reduzir ansiedade do desenvolvedor
  - Validação consistente em ambos os modos (PATH e fallback)

### Changed

- Movido `IMPLEMENTATION_SUMMARY.md` para `docs/history/sprint_2_cortex/IMPLEMENTATION_SUMMARY.md`
- Renomeado e movido `docs/README_test_mock_system.md` para `docs/guides/MOCK_SYSTEM.md`
- Adicionado frontmatter YAML aos arquivos movidos para conformidade com CORTEX

### Fixed

- **Vulnerabilidade de Corrupção de Ambiente**: Corrigida condição de corrida no `install_dev.py` ([P00.2])
  - Anteriormente, falhas parciais no `pip install` deixavam `requirements/dev.txt` inconsistente
  - Ambiente agora é sempre restaurado para estado anterior em caso de falha
  - Cleanup automático de arquivos temporários (`.tmp`, `.bak`) após sucesso

## [0.1.0] - 2025-10-27

### Added

- Configuração inicial do projeto a partir do `python-template-profissional`.
