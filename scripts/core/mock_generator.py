"""Mock Generator Core - Test Mock Generation Engine.

This module contains the core business logic for automatic test mock generation.
It analyzes Python test files and suggests appropriate mocks for external
dependencies that could fail in CI/CD environments.

Classes:
    TestMockGenerator: Main engine for mock generation and application

Note:
    MockPattern migrated to scripts.core.mock_ci.models_pydantic (P08)
    Uses lazy import to avoid circular dependency with checker.py

Author: DevOps Engineering Team
License: MIT
Version: 2.1.0 (Pydantic Migration - P08)
"""

from __future__ import annotations

import ast
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scripts.core.mock_ci.models_pydantic import MockCIConfig, MockPattern
    from scripts.utils.filesystem import FileSystemAdapter
    from scripts.utils.platform_strategy import PlatformStrategy
else:
    # Lazy imports para evitar dependências circulares em tempo de execução
    FileSystemAdapter = None
    PlatformStrategy = None

logger = logging.getLogger(__name__)


def _get_mock_pattern_class() -> type[MockPattern]:
    """Lazy import to avoid circular dependency."""
    from scripts.core.mock_ci.models_pydantic import MockPattern

    return MockPattern


class TestMockGenerator:
    """Gerador de sugestões automáticas de mocks para testes Python.

    Implementa padrões de DevOps:
    - Idempotência: pode ser executado múltiplas vezes
    - Logging estruturado
    - Tratamento robusto de erros
    - Backup automático de arquivos
    """

    def __init__(
        self,
        workspace_root: Path,
        config: MockCIConfig,
        fs: FileSystemAdapter | None = None,
        platform: PlatformStrategy | None = None,
    ):
        """Inicializa o gerador de mocks.

        Args:
            workspace_root: Caminho raiz do workspace
            config: Configuração validada do Mock CI (Pydantic model)
            fs: FileSystemAdapter para operações de I/O (default: RealFileSystem)
            platform: PlatformStrategy para operações específicas de plataforma
                     (default: detecção automática via get_platform_strategy)

        Note:
            A injeção de dependências permite:
            - Testes unitários com MemoryFileSystem (sem I/O real)
            - Compatibilidade retroativa (defaults mantêm comportamento original)
            - Extensibilidade para mock de operações de plataforma

            **BREAKING CHANGE (Fase 03 - Integração):**
            - config_path (Path) substituído por config (MockCIConfig)
            - Validação de YAML movida para CLI (Top-Down Injection)
        """
        # Lazy imports para evitar overhead em tempo de importação
        if fs is None:
            from scripts.utils.filesystem import RealFileSystem

            fs = RealFileSystem()
        if platform is None:
            from scripts.utils.platform_strategy import get_platform_strategy

            platform = get_platform_strategy()

        self.fs = fs
        self.platform = platform
        self.workspace_root = workspace_root.resolve()
        self.config = config  # Agora é MockCIConfig ao invés de dict
        self.backup_dir = self.workspace_root / ".test_mock_backups"
        self.suggestions: list[dict[str, Any]] = []

        # Parse dos padrões de mock a partir do config validado
        self.MOCK_PATTERNS = self._parse_patterns_from_config()

        if not self.MOCK_PATTERNS:
            logger.error("Nenhum padrão de mock foi carregado. Verifique o config.")

        logger.info(
            f"Inicializando TestMockGenerator para workspace: {self.workspace_root}",
        )

    def _parse_patterns_from_config(self) -> dict[str, MockPattern]:
        """Converte os padrões do config Pydantic em dicionário de MockPattern.

        Note:
            **BREAKING CHANGE (Fase 03 - Integração):**
            - Agora usa self.config.mock_patterns (MockPatternsConfig Pydantic model)
            - Acesso type-safe ao invés de dict[str, Any]
            - Eliminada lógica de parsing manual - Pydantic já validou
        """
        patterns_dict: dict[str, MockPattern] = {}

        # Acesso type-safe aos padrões validados
        mock_patterns = self.config.mock_patterns

        # Coleta todos os padrões de diferentes categorias
        all_patterns: list[MockPattern] = []
        all_patterns.extend(mock_patterns.http_patterns)
        all_patterns.extend(mock_patterns.subprocess_patterns)
        all_patterns.extend(mock_patterns.filesystem_patterns)
        all_patterns.extend(mock_patterns.database_patterns)

        # Converte lista em dict usando 'pattern' como chave
        for pattern_obj in all_patterns:
            patterns_dict[pattern_obj.pattern] = pattern_obj

        logger.debug(f"Carregados {len(patterns_dict)} padrões de mock.")
        return patterns_dict

    def _create_backup(self, file_path: Path) -> Path:
        """Cria backup de um arquivo antes de modificá-lo.

        Args:
            file_path: Caminho do arquivo para backup

        Returns:
            Caminho do arquivo de backup criado

        Note:
            Refatorado para usar FileSystemAdapter injetado (P10 - Fase 02 Passo 3).
            Usa self.fs.copy() ao invés de shutil.copy2().
        """
        if not self.fs.exists(self.backup_dir):
            self.fs.mkdir(self.backup_dir, parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name

        self.fs.copy(file_path, backup_path)
        logger.debug(f"Backup criado: {backup_path}")

        return backup_path

    def _parse_python_file(self, file_path: Path) -> ast.AST | None:
        """Parse seguro de arquivo Python usando AST.

        Args:
            file_path: Caminho do arquivo Python

        Returns:
            AST do arquivo ou None se houver erro

        Note:
            Refatorado para usar FileSystemAdapter injetado (P10 - Fase 02 Passo 2).
            Permite testes sem I/O real usando MemoryFileSystem.
        """
        try:
            content = self.fs.read_text(file_path, encoding="utf-8")
            return ast.parse(content, filename=str(file_path))

        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"Erro ao fazer parse de {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao processar {file_path}: {e}")
            return None

    def _analyze_test_function(
        self,
        func_node: ast.FunctionDef,
        file_path: Path,
        file_content: str,
    ) -> list[dict[str, Any]]:
        """Analisa uma função de teste em busca de padrões que precisam de mock.

        Args:
            func_node: Nó AST da função
            file_path: Caminho do arquivo
            file_content: Conteúdo completo do arquivo

        Returns:
            Lista de sugestões para a função

        """
        suggestions = []

        try:
            func_source = ast.unparse(func_node)

            for pattern_key, mock_pattern in self.MOCK_PATTERNS.items():
                if mock_pattern.pattern in func_source:
                    # Verifica se já existe mock para esse padrão
                    if self._has_existing_mock(file_content, mock_pattern.pattern):
                        logger.debug(
                            f"Mock já existe para {pattern_key} em {func_node.name}",
                        )
                        continue

                    suggestion = {
                        "file": str(file_path.relative_to(self.workspace_root)),
                        "function": func_node.name,
                        "line": func_node.lineno,
                        "pattern": pattern_key,
                        "mock_type": mock_pattern.mock_type,
                        "severity": mock_pattern.severity,
                        "description": mock_pattern.description,
                        "mock_template": mock_pattern.mock_template.format(
                            func_name=func_node.name,
                        ),
                        "required_imports": mock_pattern.required_imports.copy(),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    suggestions.append(suggestion)
                    logger.debug(f"Sugestão gerada: {pattern_key} em {func_node.name}")

        except Exception as e:
            logger.error(f"Erro ao analisar função {func_node.name}: {e}")

        return suggestions

    def _has_existing_mock(self, file_content: str, pattern: str) -> bool:
        """Verifica se já existe mock para o padrão especificado.

        Args:
            file_content: Conteúdo do arquivo
            pattern: Padrão a verificar

        Returns:
            True se mock já existe

        """
        # Estratégias para detectar mocks existentes
        mock_indicators = [
            f'@patch("{pattern.replace("(", "").replace(")", "")}")',
            "unittest.mock",
            "from unittest.mock import",
            "@patch(",
            "@mock.patch",
        ]

        return any(indicator in file_content for indicator in mock_indicators)

    def scan_test_files(self) -> dict[str, Any]:
        """Escaneia todos os arquivos de teste no workspace.

        Returns:
            Dicionário com todas as sugestões geradas

        Note:
            Refatorado para usar FileSystemAdapter injetado (P10 - Fase 02 Passo 2).
            Usa self.fs.glob() para permitir testes com MemoryFileSystem.
        """
        logger.info("Iniciando escaneamento de arquivos de teste...")

        # Localiza arquivos de teste
        test_patterns = [
            "tests/**/*.py",
            "test_*.py",
            "*_test.py",
        ]

        test_files: set[Path] = set()
        for pattern in test_patterns:
            # FileSystemAdapter.glob retorna list[Path]
            matched_files = self.fs.glob(self.workspace_root, pattern)
            test_files.update(matched_files)

        test_files_list = [
            f for f in test_files if self.fs.is_file(f) and f.name != "__init__.py"
        ]

        logger.info(f"Encontrados {len(test_files_list)} arquivos de teste")

        all_suggestions = []
        required_imports: set[str] = set()

        for test_file in test_files_list:
            file_suggestions = self._analyze_test_file(test_file)
            all_suggestions.extend(file_suggestions)

            # Coleta imports necessários
            for suggestion in file_suggestions:
                required_imports.update(suggestion["required_imports"])

        # Prepara relatório final
        report = {
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "workspace_root": str(self.workspace_root),
            "files_scanned": len(test_files),
            "suggestions": all_suggestions,
            "required_imports": sorted(list(required_imports)),
            "summary": {
                "total_suggestions": len(all_suggestions),
                "high_priority": len(
                    [s for s in all_suggestions if s["severity"] == "HIGH"],
                ),
                "medium_priority": len(
                    [s for s in all_suggestions if s["severity"] == "MEDIUM"],
                ),
                "low_priority": len(
                    [s for s in all_suggestions if s["severity"] == "LOW"],
                ),
                "files_with_issues": len(set(s["file"] for s in all_suggestions)),
            },
        }

        self.suggestions = all_suggestions

        summary = report.get("summary")
        assert isinstance(summary, dict), "Report summary must be a dict"
        total_suggestions = summary["total_suggestions"]
        logger.info(f"Escaneamento concluído: {total_suggestions} sugestões geradas")

        return report

    def _analyze_test_file(self, test_file: Path) -> list[dict[str, Any]]:
        """Analisa um arquivo de teste específico.

        Args:
            test_file: Caminho do arquivo de teste

        Returns:
            Lista de sugestões para o arquivo

        Note:
            Refatorado para usar FileSystemAdapter injetado (P10 - Fase 02 Passo 2).
            Permite testes sem I/O real usando MemoryFileSystem.
        """
        logger.debug(f"Analisando arquivo: {test_file}")

        # Parse do arquivo
        tree = self._parse_python_file(test_file)
        if tree is None:
            return []

        # Lê conteúdo para verificações adicionais
        try:
            file_content = self.fs.read_text(test_file, encoding="utf-8")
        except Exception as e:
            logger.error(f"Erro ao ler {test_file}: {e}")
            return []

        suggestions = []

        # Analisa funções de teste
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                func_suggestions = self._analyze_test_function(
                    node,
                    test_file,
                    file_content,
                )
                suggestions.extend(func_suggestions)

        logger.debug(f"Arquivo {test_file.name}: {len(suggestions)} sugestões")

        return suggestions

    def apply_suggestions(self, dry_run: bool = False) -> dict[str, Any]:
        """Aplica as sugestões de mock nos arquivos.

        Args:
            dry_run: Se True, apenas simula as mudanças

        Returns:
            Relatório das aplicações

        """
        if not self.suggestions:
            logger.warning(
                "Nenhuma sugestão disponível. Execute scan_test_files() primeiro.",
            )
            return {"applied": 0, "failed": 0, "skipped": 0}

        logger.info(f"Aplicando sugestões {'(DRY RUN)' if dry_run else '(REAL)'}...")

        applied = 0
        failed = 0
        skipped = 0

        # Aplica apenas sugestões de alta prioridade por segurança
        high_priority = [s for s in self.suggestions if s["severity"] == "HIGH"]

        for suggestion in high_priority:
            try:
                file_path = self.workspace_root / suggestion["file"]

                if not file_path.exists():
                    logger.warning(f"Arquivo não encontrado: {file_path}")
                    skipped += 1
                    continue

                if self._apply_single_suggestion(suggestion, file_path, dry_run):
                    applied += 1
                else:
                    skipped += 1

            except Exception as e:
                logger.error(f"Erro ao aplicar sugestão em {suggestion['file']}: {e}")
                failed += 1

        result = {
            "applied": applied,
            "failed": failed,
            "skipped": skipped,
            "total_suggestions": len(high_priority),
            "dry_run": dry_run,
        }

        logger.info(
            f"Aplicação {'simulada' if dry_run else 'real'} concluída: "
            f"{applied} aplicadas, {failed} falharam, {skipped} ignoradas",
        )

        return result

    def _apply_single_suggestion(
        self,
        suggestion: dict[str, Any],
        file_path: Path,
        dry_run: bool,
    ) -> bool:
        """Aplica uma sugestão específica em um arquivo.

        Args:
            suggestion: Dicionário com dados da sugestão
            file_path: Caminho do arquivo
            dry_run: Se True, apenas simula

        Returns:
            True se aplicada com sucesso

        Note:
            Refatorado para usar FileSystemAdapter injetado (P10 - Fase 02 Passo 3).
            Usa self.fs para leitura e escrita de arquivos.
        """
        try:
            # Lê arquivo atual
            content = self.fs.read_text(file_path, encoding="utf-8")

            # Verifica se mock já existe
            if self._has_existing_mock(content, suggestion["pattern"]):
                logger.debug(f"Mock já existe em {file_path.name}")
                return False

            if dry_run:
                func_name = suggestion["function"]
                msg = f"[DRY RUN] Aplicaria mock em {file_path.name}:{func_name}"
                logger.info(msg)
                return True

            # Cria backup
            self._create_backup(file_path)

            # Aplica modificações
            modified_content = self._inject_mock_code(content, suggestion)

            # Salva arquivo modificado
            self.fs.write_text(file_path, modified_content, encoding="utf-8")

            logger.info(f"Mock aplicado: {file_path.name}:{suggestion['function']}")
            return True

        except Exception as e:
            logger.error(f"Erro ao aplicar mock em {file_path}: {e}")
            return False

    def _inject_mock_code(self, content: str, suggestion: dict[str, Any]) -> str:
        """Injeta código de mock no conteúdo do arquivo.

        Args:
            content: Conteúdo original do arquivo
            suggestion: Sugestão com dados do mock

        Returns:
            Conteúdo modificado com mock injetado

        """
        lines = content.splitlines()

        # Adiciona imports necessários
        modified_lines = self._add_required_imports(
            lines,
            suggestion["required_imports"],
        )

        # Encontra e modifica a função de teste
        modified_lines = self._add_mock_decorator(modified_lines, suggestion)

        return "\n".join(modified_lines)

    def _add_required_imports(
        self,
        lines: list[str],
        required_imports: list[str],
    ) -> list[str]:
        """Adiciona imports necessários se não existirem.

        Args:
            lines: Linhas do arquivo
            required_imports: Lista de imports necessários

        Returns:
            Linhas modificadas com imports

        """
        existing_imports = [
            line.strip()
            for line in lines
            if line.strip().startswith(("import ", "from "))
        ]

        # Encontra posição para inserir imports
        import_insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ", '"""', "'''")):
                import_insert_pos = i + 1

        # Adiciona imports que não existem
        new_lines = lines.copy()
        for import_stmt in required_imports:
            if not any(
                import_stmt.split("import")[1].strip() in existing
                for existing in existing_imports
            ):
                new_lines.insert(import_insert_pos, import_stmt)
                import_insert_pos += 1

        return new_lines

    def _add_mock_decorator(
        self,
        lines: list[str],
        suggestion: dict[str, Any],
    ) -> list[str]:
        """Adiciona decorator de mock na função específica.

        Args:
            lines: Linhas do arquivo
            suggestion: Sugestão com dados do mock

        Returns:
            Linhas modificadas com decorator

        """
        func_name = suggestion["function"]
        mock_template = suggestion["mock_template"]

        # Substitui função existente pelo template de mock
        for i, line in enumerate(lines):
            if f"def {func_name}(" in line:
                # Encontra indentação
                indent = len(line) - len(line.lstrip())
                indent_str = " " * indent

                # Prepara linhas do mock
                mock_lines = []
                for mock_line in mock_template.splitlines():
                    if mock_line.strip():
                        mock_lines.append(f"{indent_str}{mock_line}")
                    else:
                        mock_lines.append("")

                # Substitui função
                lines[i : i + 1] = mock_lines
                break

        return lines

    def generate_report(self, output_file: Path | None = None) -> Path:
        """Gera relatório em JSON das sugestões.

        Args:
            output_file: Caminho do arquivo de saída (opcional)

        Returns:
            Caminho do arquivo de relatório gerado

        Note:
            Refatorado para usar FileSystemAdapter injetado (P10 - Fase 02 Passo 3).
            Usa self.fs.write_text() com json.dumps().
        """
        if output_file is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = self.workspace_root / f"test_mock_report_{timestamp}.json"

        report_data = self.scan_test_files()

        try:
            json_content = json.dumps(report_data, indent=2, ensure_ascii=False)
            self.fs.write_text(output_file, json_content, encoding="utf-8")

            logger.info(f"Relatório gerado: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            raise

    def print_summary(self) -> None:
        """Imprime resumo das sugestões encontradas."""
        if not self.suggestions:
            print("🔍 Nenhuma sugestão de mock encontrada.")
            return

        print("🔧 RELATÓRIO DE SUGESTÕES DE MOCK")
        print("=" * 50)

        # Estatísticas
        high_priority = [s for s in self.suggestions if s["severity"] == "HIGH"]
        medium_priority = [s for s in self.suggestions if s["severity"] == "MEDIUM"]

        print(f"📊 Total de sugestões: {len(self.suggestions)}")
        print(f"🔴 Alta prioridade: {len(high_priority)}")
        print(f"🟡 Média prioridade: {len(medium_priority)}")

        # Mostra sugestões de alta prioridade
        if high_priority:
            print("\n🚨 SUGESTÕES DE ALTA PRIORIDADE:")
            for i, suggestion in enumerate(high_priority[:5], 1):  # Limita a 5
                print(f"\n{i}. {suggestion['file']}:{suggestion['line']}")
                print(f"   Função: {suggestion['function']}")
                print(f"   Problema: {suggestion['description']}")
                print(f"   Padrão: {suggestion['pattern']}")

        print("\n💡 Use --apply --dry-run para ver as modificações propostas")
        print("💡 Use --apply para aplicar as correções de alta prioridade")


__all__ = ["MockPattern", "TestMockGenerator"]
