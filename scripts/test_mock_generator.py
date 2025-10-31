#!/usr/bin/env python3
"""
Test Mock Generator - Sistema de Auto-Correção para Testes
=========================================================

Analisa arquivos de teste Python e gera sugestões automáticas de mocks
para dependências externas que podem falhar no CI/CD.

Este script é idempotente e segue padrões de DevOps para automação robusta.

Uso:
    python scripts/test_mock_generator.py [--scan] [--apply] [--dry-run]
    python scripts/test_mock_generator.py --help

Exemplos:
    # Apenas escanear e mostrar sugestões
    python scripts/test_mock_generator.py --scan
    
    # Aplicar correções com preview (recomendado)
    python scripts/test_mock_generator.py --apply --dry-run
    
    # Aplicar correções efetivamente
    python scripts/test_mock_generator.py --apply

Autor: DevOps Template Generator
Versão: 1.0.0
"""

import argparse
import ast
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configuração de logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("test_mock_generator")


class MockPattern:
    """Representa um padrão de código que precisa de mock."""
    
    def __init__(
        self,
        pattern: str,
        mock_type: str,
        mock_template: str,
        required_imports: List[str],
        description: str,
        severity: str = "MEDIUM"
    ):
        self.pattern = pattern
        self.mock_type = mock_type
        self.mock_template = mock_template
        self.required_imports = required_imports
        self.description = description
        self.severity = severity


class TestMockGenerator:
    """
    Gerador de sugestões automáticas de mocks para testes Python.
    
    Implementa padrões de DevOps:
    - Idempotência: pode ser executado múltiplas vezes
    - Logging estruturado
    - Tratamento robusto de erros
    - Backup automático de arquivos
    """
    
    # Padrões de mock configuráveis e extensíveis
    MOCK_PATTERNS = {
        "httpx.get(": MockPattern(
            pattern="httpx.get(",
            mock_type="HTTP_REQUEST",
            mock_template='''@patch("httpx.get")
def {func_name}(self, mock_get, *args, **kwargs):
    """Test with mocked HTTP GET request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {{"status": "success", "data": "mocked"}}
    mock_get.return_value = mock_response
    
    # Your test logic here''',
            required_imports=["from unittest.mock import Mock, patch"],
            description="HTTP GET request detected - needs mocking for CI stability",
            severity="HIGH"
        ),
        
        "httpx.post(": MockPattern(
            pattern="httpx.post(",
            mock_type="HTTP_REQUEST",
            mock_template='''@patch("httpx.post")
def {func_name}(self, mock_post, *args, **kwargs):
    """Test with mocked HTTP POST request."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {{"id": "mock_id", "status": "created"}}
    mock_post.return_value = mock_response
    
    # Your test logic here''',
            required_imports=["from unittest.mock import Mock, patch"],
            description="HTTP POST request detected - needs mocking for CI stability",
            severity="HIGH"
        ),
        
        "subprocess.run(": MockPattern(
            pattern="subprocess.run(",
            mock_type="SUBPROCESS",
            mock_template='''@patch("subprocess.run")
def {func_name}(self, mock_subprocess_run, *args, **kwargs):
    """Test with mocked subprocess execution."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "mocked output"
    mock_result.stderr = ""
    mock_subprocess_run.return_value = mock_result
    
    # Your test logic here''',
            required_imports=["from unittest.mock import Mock, patch"],
            description="Subprocess execution detected - needs mocking for CI portability",
            severity="HIGH"
        ),
        
        "requests.get(": MockPattern(
            pattern="requests.get(",
            mock_type="HTTP_REQUEST",
            mock_template='''@patch("requests.get")
def {func_name}(self, mock_get, *args, **kwargs):
    """Test with mocked requests GET."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {{"result": "mocked"}}
    mock_get.return_value = mock_response
    
    # Your test logic here''',
            required_imports=["from unittest.mock import Mock, patch"],
            description="Requests GET detected - needs mocking for CI stability",
            severity="HIGH"
        ),
    }
    
    def __init__(self, workspace_root: Path):
        """
        Inicializa o gerador de mocks.
        
        Args:
            workspace_root: Caminho raiz do workspace
        """
        self.workspace_root = workspace_root.resolve()
        self.backup_dir = self.workspace_root / ".test_mock_backups"
        self.suggestions: List[Dict[str, Any]] = []
        
        logger.info(f"Inicializando TestMockGenerator para workspace: {self.workspace_root}")
        
    def _create_backup(self, file_path: Path) -> Path:
        """
        Cria backup de um arquivo antes de modificá-lo.
        
        Args:
            file_path: Caminho do arquivo para backup
            
        Returns:
            Caminho do arquivo de backup criado
        """
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Backup criado: {backup_path}")
        
        return backup_path
        
    def _parse_python_file(self, file_path: Path) -> Optional[ast.AST]:
        """
        Parse seguro de arquivo Python usando AST.
        
        Args:
            file_path: Caminho do arquivo Python
            
        Returns:
            AST do arquivo ou None se houver erro
        """
        try:
            with file_path.open("r", encoding="utf-8") as f:
                content = f.read()
                
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
        file_content: str
    ) -> List[Dict[str, Any]]:
        """
        Analisa uma função de teste em busca de padrões que precisam de mock.
        
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
                        logger.debug(f"Mock já existe para {pattern_key} em {func_node.name}")
                        continue
                        
                    suggestion = {
                        "file": str(file_path.relative_to(self.workspace_root)),
                        "function": func_node.name,
                        "line": func_node.lineno,
                        "pattern": pattern_key,
                        "mock_type": mock_pattern.mock_type,
                        "severity": mock_pattern.severity,
                        "description": mock_pattern.description,
                        "mock_template": mock_pattern.mock_template.format(func_name=func_node.name),
                        "required_imports": mock_pattern.required_imports.copy(),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    
                    suggestions.append(suggestion)
                    logger.debug(f"Sugestão gerada: {pattern_key} em {func_node.name}")
                    
        except Exception as e:
            logger.error(f"Erro ao analisar função {func_node.name}: {e}")
            
        return suggestions
        
    def _has_existing_mock(self, file_content: str, pattern: str) -> bool:
        """
        Verifica se já existe mock para o padrão especificado.
        
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
        
    def scan_test_files(self) -> Dict[str, Any]:
        """
        Escaneia todos os arquivos de teste no workspace.
        
        Returns:
            Dicionário com todas as sugestões geradas
        """
        logger.info("Iniciando escaneamento de arquivos de teste...")
        
        # Localiza arquivos de teste
        test_patterns = [
            "tests/**/*.py",
            "test_*.py",
            "*_test.py",
        ]
        
        test_files = set()
        for pattern in test_patterns:
            test_files.update(self.workspace_root.glob(pattern))
            
        test_files = [f for f in test_files if f.is_file() and f.name != "__init__.py"]
        
        logger.info(f"Encontrados {len(test_files)} arquivos de teste")
        
        all_suggestions = []
        required_imports: Set[str] = set()
        
        for test_file in test_files:
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
                "high_priority": len([s for s in all_suggestions if s["severity"] == "HIGH"]),
                "medium_priority": len([s for s in all_suggestions if s["severity"] == "MEDIUM"]),
                "low_priority": len([s for s in all_suggestions if s["severity"] == "LOW"]),
                "files_with_issues": len(set(s["file"] for s in all_suggestions)),
            },
        }
        
        self.suggestions = all_suggestions
        
        logger.info(f"Escaneamento concluído: {report['summary']['total_suggestions']} sugestões geradas")
        
        return report
        
    def _analyze_test_file(self, test_file: Path) -> List[Dict[str, Any]]:
        """
        Analisa um arquivo de teste específico.
        
        Args:
            test_file: Caminho do arquivo de teste
            
        Returns:
            Lista de sugestões para o arquivo
        """
        logger.debug(f"Analisando arquivo: {test_file}")
        
        # Parse do arquivo
        tree = self._parse_python_file(test_file)
        if tree is None:
            return []
            
        # Lê conteúdo para verificações adicionais
        try:
            with test_file.open("r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            logger.error(f"Erro ao ler {test_file}: {e}")
            return []
            
        suggestions = []
        
        # Analisa funções de teste
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                func_suggestions = self._analyze_test_function(node, test_file, file_content)
                suggestions.extend(func_suggestions)
                
        logger.debug(f"Arquivo {test_file.name}: {len(suggestions)} sugestões")
        
        return suggestions
        
    def apply_suggestions(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Aplica as sugestões de mock nos arquivos.
        
        Args:
            dry_run: Se True, apenas simula as mudanças
            
        Returns:
            Relatório das aplicações
        """
        if not self.suggestions:
            logger.warning("Nenhuma sugestão disponível. Execute scan_test_files() primeiro.")
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
            f"{applied} aplicadas, {failed} falharam, {skipped} ignoradas"
        )
        
        return result
        
    def _apply_single_suggestion(
        self, 
        suggestion: Dict[str, Any], 
        file_path: Path, 
        dry_run: bool
    ) -> bool:
        """
        Aplica uma sugestão específica em um arquivo.
        
        Args:
            suggestion: Dicionário com dados da sugestão
            file_path: Caminho do arquivo
            dry_run: Se True, apenas simula
            
        Returns:
            True se aplicada com sucesso
        """
        try:
            # Lê arquivo atual
            with file_path.open("r", encoding="utf-8") as f:
                content = f.read()
                
            # Verifica se mock já existe
            if self._has_existing_mock(content, suggestion["pattern"]):
                logger.debug(f"Mock já existe em {file_path.name}")
                return False
                
            if dry_run:
                logger.info(f"[DRY RUN] Aplicaria mock em {file_path.name}:{suggestion['function']}")
                return True
                
            # Cria backup
            self._create_backup(file_path)
            
            # Aplica modificações
            modified_content = self._inject_mock_code(content, suggestion)
            
            # Salva arquivo modificado
            with file_path.open("w", encoding="utf-8") as f:
                f.write(modified_content)
                
            logger.info(f"Mock aplicado: {file_path.name}:{suggestion['function']}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar mock em {file_path}: {e}")
            return False
            
    def _inject_mock_code(self, content: str, suggestion: Dict[str, Any]) -> str:
        """
        Injeta código de mock no conteúdo do arquivo.
        
        Args:
            content: Conteúdo original do arquivo
            suggestion: Sugestão com dados do mock
            
        Returns:
            Conteúdo modificado com mock injetado
        """
        lines = content.splitlines()
        
        # Adiciona imports necessários
        modified_lines = self._add_required_imports(lines, suggestion["required_imports"])
        
        # Encontra e modifica a função de teste
        modified_lines = self._add_mock_decorator(modified_lines, suggestion)
        
        return "\n".join(modified_lines)
        
    def _add_required_imports(self, lines: List[str], required_imports: List[str]) -> List[str]:
        """
        Adiciona imports necessários se não existirem.
        
        Args:
            lines: Linhas do arquivo
            required_imports: Lista de imports necessários
            
        Returns:
            Linhas modificadas com imports
        """
        existing_imports = [line.strip() for line in lines if line.strip().startswith(("import ", "from "))]
        
        # Encontra posição para inserir imports
        import_insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ", '"""', "'''")):
                import_insert_pos = i + 1
                
        # Adiciona imports que não existem
        new_lines = lines.copy()
        for import_stmt in required_imports:
            if not any(import_stmt.split("import")[1].strip() in existing for existing in existing_imports):
                new_lines.insert(import_insert_pos, import_stmt)
                import_insert_pos += 1
                
        return new_lines
        
    def _add_mock_decorator(self, lines: List[str], suggestion: Dict[str, Any]) -> List[str]:
        """
        Adiciona decorator de mock na função específica.
        
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
                lines[i:i+1] = mock_lines
                break
                
        return lines
        
    def generate_report(self, output_file: Optional[Path] = None) -> Path:
        """
        Gera relatório em JSON das sugestões.
        
        Args:
            output_file: Caminho do arquivo de saída (opcional)
            
        Returns:
            Caminho do arquivo de relatório gerado
        """
        if output_file is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = self.workspace_root / f"test_mock_report_{timestamp}.json"
            
        report_data = self.scan_test_files()
        
        try:
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
                
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
            print(f"\n🚨 SUGESTÕES DE ALTA PRIORIDADE:")
            for i, suggestion in enumerate(high_priority[:5], 1):  # Limita a 5
                print(f"\n{i}. {suggestion['file']}:{suggestion['line']}")
                print(f"   Função: {suggestion['function']}")
                print(f"   Problema: {suggestion['description']}")
                print(f"   Padrão: {suggestion['pattern']}")
                
        print(f"\n💡 Use --apply --dry-run para ver as modificações propostas")
        print(f"💡 Use --apply para aplicar as correções de alta prioridade")


def main() -> int:
    """
    Função principal CLI.
    
    Returns:
        Código de saída (0 = sucesso, 1 = erro)
    """
    parser = argparse.ArgumentParser(
        description="Test Mock Generator - Sistema de Auto-Correção para Testes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s --scan                    # Escanear e mostrar sugestões
  %(prog)s --apply --dry-run         # Preview das correções
  %(prog)s --apply                   # Aplicar correções
  %(prog)s --scan --report report.json  # Gerar relatório JSON
        """
    )
    
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Escanear arquivos de teste em busca de padrões problemáticos"
    )
    
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplicar correções de alta prioridade automaticamente"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular aplicação sem modificar arquivos (usar com --apply)"
    )
    
    parser.add_argument(
        "--report",
        type=Path,
        help="Gerar relatório JSON no arquivo especificado"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ativar logging verboso"
    )
    
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Caminho do workspace (padrão: diretório atual)"
    )
    
    args = parser.parse_args()
    
    # Configura logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Valida argumentos
    if not args.scan and not args.apply:
        parser.error("Especifique --scan ou --apply")
        
    if args.dry_run and not args.apply:
        parser.error("--dry-run só pode ser usado com --apply")
        
    try:
        # Inicializa gerador
        workspace = args.workspace.resolve()
        if not workspace.exists():
            logger.error(f"Workspace não encontrado: {workspace}")
            return 1
            
        generator = TestMockGenerator(workspace)
        
        # Executa ações solicitadas
        if args.scan:
            report = generator.scan_test_files()
            generator.print_summary()
            
            if args.report:
                generator.generate_report(args.report)
                
        if args.apply:
            if not generator.suggestions:
                generator.scan_test_files()
                
            result = generator.apply_suggestions(dry_run=args.dry_run)
            
            if result["applied"] > 0 and not args.dry_run:
                print(f"\n✅ {result['applied']} correções aplicadas com sucesso!")
                print("💡 Recomenda-se executar os testes para validar as correções:")
                print("   python -m pytest tests/")
                
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())