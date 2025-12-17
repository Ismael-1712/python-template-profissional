# Changelog

## [Unreleased]

## [0.1.0] - 2025-12-17

### Added

- **Estrutura de Aplica\u00e7\u00e3o Modular**: Nova arquitetura em `src/app/` seguindo princ\u00edpios de 12-Factor App
  - M\u00f3dulo principal em `src/app/main.py` com FastAPI
  - Configura\u00e7\u00f5es centralizadas em `src/app/core/config.py`
  - Suporte a vari\u00e1veis de ambiente via arquivo `.env` com `pydantic-settings`
- **Endpoint de Redirecionamento Autom\u00e1tico**: Ra\u00edz `/` agora redireciona para `/docs`
  - Melhora significativa na experi\u00eancia do usu\u00e1rio (UX)
  - Documenta\u00e7\u00e3o interativa imediatamente acess\u00edvel
- **Comando `make run`**: Servidor de desenvolvimento com hot-reload
  - Execu\u00e7\u00e3o simplificada: `make run`
  - Hot-reload autom\u00e1tico para desenvolvimento \u00e1gil
  - Servidor dispon\u00edvel em `http://localhost:8000`
- **Endpoint de Metadados**: Novo endpoint `/api/v1/meta`
  - Retorna informa\u00e7\u00f5es do projeto (nome, vers\u00e3o, API prefix)
  - \u00datil para healthchecks e descoberta de servi\u00e7o
- **Health Check Expl\u00edcito**: Endpoint `/health` para monitoramento
  - Retorna `{\"status\": \"ok\"}` para checks de disponibilidade

### Changed

- **Refatora\u00e7\u00e3o do Entrypoint Principal**: Migrado de `src/main.py` para `src/app/main.py`
  - Melhor organiza\u00e7\u00e3o modular do c\u00f3digo
  - Separa\u00e7\u00e3o clara entre aplica\u00e7\u00e3o e ferramentas
- **Atualiza\u00e7\u00e3o de Depend\u00eancias**: Novas depend\u00eancias para a stack FastAPI
  - `fastapi`: Framework web moderno
  - `uvicorn[standard]`: Servidor ASGI de alta performance
  - `pydantic-settings`: Gerenciamento de configura\u00e7\u00f5es com valida\u00e7\u00e3o
  - `python-dotenv`: Suporte a arquivos `.env`
- **Configura\u00e7\u00f5es Centralizadas**: Todas as configura\u00e7\u00f5es agora em `config.py`
  - Valida\u00e7\u00e3o autom\u00e1tica via Pydantic
  - Suporte a m\u00faltiplos ambientes (dev, staging, prod)
  - Type safety completo

### Documentation

- **README.md**: Atualizado para refletir nova arquitetura
  - Se\u00e7\u00e3o \"Executar a Aplica\u00e7\u00e3o\" com `make run`
  - Documenta\u00e7\u00e3o da estrutura modular `src/app/`
  - Refer\u00eancias aos princ\u00edpios de 12-Factor App
- **Estrutura de Diret\u00f3rios**: Atualizada no README
  - Reflete organiza\u00e7\u00e3o em `src/app/core/`
  - Documenta prop\u00f3sito de cada m\u00f3dulo

---

## [Unreleased - Prior to Sprint 1]

### Added

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
