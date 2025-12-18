# Changelog

## [Unreleased]

### Added

- **User Control for Parallel Processing**: Exposed experimental parallel mode via CLI
  - Added `--parallel` / `--experimental-parallel` flag to `cortex knowledge-scan` command
  - Allows users with high-performance hardware to opt-in to parallel processing
  - New `force_parallel` parameter in `KnowledgeScanner.__init__()`
  - Implements clear UX feedback: shows mode (sequential vs parallel) and worker count
  - Addresses "Tool Blindness" problem: hidden features now discoverable
  - Maintains backward compatibility (default: sequential processing)

### Changed

- **Dynamic Parallelism Threshold**: Refactored hardcoded threshold to user-controlled flag
  - `parallel_threshold` now respects `force_parallel` parameter
  - If `force_parallel=True`: threshold = 10 files (original behavior)
  - If `force_parallel=False` (default): threshold = sys.maxsize (sequential)
  - Enhanced logging with mode indicators and performance warnings
  - Preserves GIL overhead protection while enabling user autonomy

- **Performance Benchmark Script**: Created `scripts/benchmark_cortex_perf.py` for measuring KnowledgeScanner performance
  - Automated benchmarking with 5 iterations per scenario (10, 50, 100, 500 files)
  - Generates temporary isolated datasets with realistic Markdown + YAML frontmatter
  - Measures sequential vs parallel processing modes
  - Outputs markdown-formatted results ready for documentation
  - **Critical Finding:** Parallel mode shows 34% performance regression (speedup 0.66x)
  - Reveals that threading overhead + GIL contention exceed I/O gains
- **Empirical Performance Metrics**: Updated `docs/architecture/PERFORMANCE_NOTES.md` with real benchmark data
  - Hardware specs: Linux WSL2, 16 cores, Python 3.12.12
  - Sequential mode consistently outperforms parallel across all dataset sizes
  - Added root cause analysis: GIL contention + CPU-bound parsing dominates I/O
  - Documented action items: P0 = disable parallel, P1 = use multiprocessing instead
  - Added performance regression insights for future optimization (Etapa 3)

### Fixed

- **Thread-Safety for MemoryFileSystem**: Implemented `threading.RLock` to prevent race conditions
  - Added internal lock to all MemoryFileSystem operations (read, write, exists, mkdir, glob, copy)
  - Updated docstring to reflect thread-safety guarantees (removed "not thread-safe" limitation)
  - Protects concurrent access in parallel test execution and KnowledgeScanner parallel processing
  - Zero performance impact on sequential operations (~100ns overhead per lock acquisition)

### Added

- **Concurrency Stress Tests**: Comprehensive test suite for parallel processing validation
  - New `tests/test_cortex_concurrency.py` with 9 test scenarios
  - Tests parallel integrity (50 files → 50 entries, no duplicates)
  - Tests concurrent scans on shared filesystem (4 simultaneous scans)
  - Tests determinism across 10 runs (same IDs every time)
  - Tests parallelization threshold (9 files = sequential, 50 files = parallel)
  - Direct MemoryFileSystem thread-safety tests (100 concurrent writes, 50 concurrent reads)
- **Performance Documentation**: Created `docs/architecture/PERFORMANCE_NOTES.md`
  - Documents KnowledgeScanner parallelization strategy (threshold, worker count)
  - Thread-safety guarantees for MemoryFileSystem and RealFileSystem
  - Benchmark methodology (to be populated in Etapa 2)
  - Known limitations and future optimization roadmap
  - Testing strategy and execution instructions

### Changed

- **KnowledgeScanner Docstring**: Enhanced `scan()` method documentation
  - Added "Performance Notes" section documenting automatic parallelization
  - Added thread-safety guarantees and version information
  - Added reference to PERFORMANCE_NOTES.md for detailed benchmarks

### Performance

- **CORTEX Scanners Performance Optimization**: Implemented caching and parallelism for improved scan performance
  - **AST Caching**: Added `@functools.lru_cache` to `CodeLinkScanner.analyze_python_exports()` to cache Python AST parsing
    - Cache size: 128 entries (sufficient for typical project scans)
    - 5-50x speedup expected for repeated analysis of the same files
    - Static method `_parse_ast_cached()` prevents memory leaks from instance references
  - **Parallel Knowledge Scanning**: Implemented `ThreadPoolExecutor` in `KnowledgeScanner.scan()`
    - Automatic threshold: parallel processing activates for ≥10 files (avoids overhead for small scans)
    - Worker count: `min(4, os.cpu_count())` for optimal I/O-bound performance
    - Thread-safe wrapper `_parse_knowledge_file_safe()` ensures resilient error handling
    - Expected speedup: 2-3x for repositories with 50+ knowledge files
  - Both optimizations maintain backward compatibility and existing error handling behavior

### Added

- **Integration Tests for CORTEX Pipeline**: Comprehensive end-to-end tests for Scan → Resolve → Context flow
  - New test suite `tests/test_cortex_integration.py` covering complete pipeline
  - Tests JSON serialization/deserialization roundtrip with `model_dump()` and `model_validate()`
  - Tests broken link detection and multi-node cross-referencing
  - Tests ProjectMapper context generation with knowledge entries statistics
  - Validates that link resolution correctly identifies VALID vs BROKEN status
- **Strict Schema Validation for Knowledge Nodes**: Enhanced metadata validation in `scripts/core/cortex/metadata.py`
  - Knowledge Nodes now MUST have `golden_paths` field (cannot be missing or empty)
  - Added conditional validation: `if metadata.get("type") == "knowledge"` checks for required field
  - Error messages: "Knowledge Nodes MUST have 'golden_paths' field" and "non-empty 'golden_paths' list"
  - Centralizes business rule enforcement at parser level, protecting entire system
  - Non-knowledge documents (guide, arch, reference) remain unaffected

### Refactored

- **CORTEX Scanners Unification**: Eliminada duplicação de lógica de parsing e migração completa para Pydantic v2
  - **KnowledgeScanner**: Refatorado para usar `FrontmatterParser` central em vez de `frontmatter.loads()` direto
  - **Mapper Models**: Migrados `CLICommand`, `Document` e `ProjectContext` de `@dataclass` para Pydantic `BaseModel`
  - Substituído `asdict(context)` por `context.model_dump(mode="json")` no método `save_context`
  - Benefícios: DRY (Single Source of Truth para parsing YAML), validação consistente, serialização uniforme
  - **100% Pydantic v2**: Todos os modelos de dados do CORTEX agora utilizam Pydantic v2

### Added

- **Rich UI for Audit Reports**: Modernized audit report visualization using Rich library
  - Replaced manual string concatenation with Rich components (Panel, Table, Markdown)
  - Professional-grade tables for Severity Distribution and Top Findings
  - Color-coded status panels (Green=PASS, Yellow=WARNING, Red=FAIL)
  - Maintained backward compatibility - `format()` method still returns string
  - Improved readability with structured layouts and semantic color coding
  - Uses `Console(force_terminal=True)` for ANSI color preservation
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
