# Changelog

## [Unreleased]

### Added

- **Pydantic v2 Unification - Fase 3 (Git Sync)**: Implementado padrão Hybrid DTO para serialização
  - **Novo**: `SyncStepModel` (Pydantic v2) - DTO imutável para validação de dados de sincronização
  - **Mantido**: `SyncStep` (classe legacy) - Lógica mutável preservada para workflows imperativos
  - Método `to_dict()` agora usa `SyncStepModel.model_dump()` para serialização validada
  - Validação de `status` com `Literal["pending", "running", "success", "failed"]`
  - Validação de `duration >= 0.0` via Pydantic Field
  - **100% Cobertura**: CORTEX, Guardian e Git Sync agora padronizados com Pydantic v2
- **Pydantic v2 Unification - Fase 1 & 2**: Migração completa dos modelos CORTEX e Guardian para Pydantic v2
  - **CORTEX**: Convertidos `DocumentMetadata`, `ValidationResult`, `LinkCheckResult` de `@dataclass` para `BaseModel`
  - **Guardian**: Convertidos `ConfigFinding`, `ScanResult` de `@dataclass` para `BaseModel`
  - Benefícios: Imutabilidade (`frozen=True`), validação automática, serialização uniforme via `model_dump()`
  - Validações adicionadas: `line_number: int = Field(gt=0)` no Guardian
  - Campo `source_file` no CORTEX agora usa `Field(exclude=True)` para evitar problemas de serialização
  - Properties nativas mantidas em `ScanResult` (compatíveis com Pydantic)
- **CLI: Comando `cortex config`**: Novo comando para visualização e validação de configurações
  - Flag `--show`: Exibe configuração atual formatada com estatísticas
  - Flag `--validate`: Valida sintaxe YAML e chaves obrigatórias
  - Flag `--path`: Permite especificar arquivo de configuração customizado
  - Leitura segura de YAML com tratamento robusto de erros
  - Integração completa com `audit_config.yaml`
- **Docs: Arquitetura Interna do Mock CI**: Documentação completa do pipeline Detector → Checker → Fixer
  - Diagrama visual do fluxo de execução
  - Documentação detalhada de cada componente (`detector.py`, `checker.py`, `fixer.py`, `git_ops.py`)
  - Exemplos de código e casos de uso
  - Decisões de design e padrões arquiteturais
  - Adicionado em `docs/guides/MOCK_SYSTEM.md`
- **Docs: Catálogo de Plugins de Auditoria**: Documentação completa dos plugins disponíveis
  - Plugin `check_mock_coverage`: Análise de cobertura de mocks em testes
  - Plugin `simulate_ci`: Simulação de ambiente CI/CD local
  - Templates para desenvolvimento de novos plugins
  - Best practices de integração e uso programático
  - Adicionado em `docs/architecture/CODE_AUDIT.md`
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

- Refatoração completa dos modelos Pydantic (`mock_ci`, `audit`) para usar `Enum` nativo em vez de strings ([P29])
- Introduzido `SecurityCategory` e `SecuritySeverity` para tipagem forte em auditorias de segurança
- Eliminados validadores manuais em favor da validação nativa do Pydantic v2
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
