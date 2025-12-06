"""Scanner AST para detectar configurações no código Python.

Usa o módulo ast nativo do Python para analisar código-fonte e extrair:
- Chamadas a os.getenv("VAR")
- Acessos a os.environ.get("VAR")
- Subscrições a os.environ["VAR"]
"""

from __future__ import annotations

import ast
import time
from pathlib import Path

import yaml

from scripts.core.guardian.models import ConfigFinding, ConfigType, ScanResult

# Constantes para detecção de argumentos
MIN_ARGS_WITH_DEFAULT = 2  # Mínimo de args para ter valor default


def load_whitelist(project_root: Path) -> set[str]:
    """Carrega whitelist de variáveis de ambiente a ignorar.

    Args:
        project_root: Diretório raiz do projeto

    Returns:
        Conjunto de variáveis de ambiente na whitelist
    """
    whitelist_file = project_root / ".guardian-whitelist.yaml"
    if not whitelist_file.exists():
        return set()

    try:
        with whitelist_file.open(encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return set(config.get("whitelist", []))
    except Exception:  # noqa: BLE001 - Captura intencional
        return set()


class EnvVarVisitor(ast.NodeVisitor):
    """Visitor AST para detectar variáveis de ambiente.

    Detecta os seguintes padrões:
    - os.getenv("VAR_NAME")
    - os.getenv("VAR_NAME", "default")
    - os.environ.get("VAR_NAME")
    - os.environ.get("VAR_NAME", "default")
    - os.environ["VAR_NAME"]
    """

    def __init__(self, source_file: Path) -> None:
        """Inicializa o visitor.

        Args:
            source_file: Caminho do arquivo sendo analisado
        """
        self.source_file = source_file
        self.findings: list[ConfigFinding] = []
        self._current_function = ""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Rastreia contexto da função atual."""
        prev_function = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = prev_function

    def visit_Call(self, node: ast.Call) -> None:
        """Visita chamadas de função procurando por os.getenv()."""
        # Detecta os.getenv("VAR_NAME") ou os.getenv("VAR_NAME", "default")
        if self._is_os_getenv(node):
            self._extract_getenv_config(node)

        # Detecta os.environ.get("VAR_NAME") ou os.environ.get("VAR_NAME", "default")  # noqa: E501
        elif self._is_environ_get(node):
            self._extract_environ_get_config(node)

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Visita subscripts procurando por os.environ["VAR_NAME"]."""
        if self._is_environ_subscript(node):
            self._extract_environ_subscript_config(node)

        self.generic_visit(node)

    def _is_os_getenv(self, node: ast.Call) -> bool:
        """Verifica se é uma chamada a os.getenv()."""
        return (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "getenv"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
        )

    def _is_environ_get(self, node: ast.Call) -> bool:
        """Verifica se é uma chamada a os.environ.get()."""
        return (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "environ"
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "os"
        )

    def _is_environ_subscript(self, node: ast.Subscript) -> bool:
        """Verifica se é um acesso a os.environ["VAR"]."""
        return (
            isinstance(node.value, ast.Attribute)
            and node.value.attr == "environ"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "os"
        )

    def _extract_getenv_config(self, node: ast.Call) -> None:
        """Extrai configuração de os.getenv()."""
        if not node.args or not isinstance(node.args[0], ast.Constant):
            return

        var_name = str(node.args[0].value)  # Converte para string
        default_value = None
        required = True

        # Verifica se há valor padrão (segundo argumento)
        if len(node.args) >= MIN_ARGS_WITH_DEFAULT and isinstance(
            node.args[1],
            ast.Constant,
        ):
            default_value = str(node.args[1].value)
            required = False

        finding = ConfigFinding(
            key=var_name,
            config_type=ConfigType.ENV_VAR,
            source_file=self.source_file,
            line_number=node.lineno,
            default_value=default_value,
            required=required,
            context=self._current_function,
        )
        self.findings.append(finding)

    def _extract_environ_get_config(self, node: ast.Call) -> None:
        """Extrai configuração de os.environ.get()."""
        if not node.args or not isinstance(node.args[0], ast.Constant):
            return

        var_name = str(node.args[0].value)  # Converte para string
        default_value = None
        required = True

        # Verifica se há valor padrão (segundo argumento)
        if len(node.args) >= MIN_ARGS_WITH_DEFAULT and isinstance(
            node.args[1],
            ast.Constant,
        ):
            default_value = str(node.args[1].value)
            required = False

        finding = ConfigFinding(
            key=var_name,
            config_type=ConfigType.ENV_VAR,
            source_file=self.source_file,
            line_number=node.lineno,
            default_value=default_value,
            required=required,
            context=self._current_function,
        )
        self.findings.append(finding)

    def _extract_environ_subscript_config(self, node: ast.Subscript) -> None:
        """Extrai configuração de os.environ["VAR"]."""
        if not isinstance(node.slice, ast.Constant):
            return

        var_name = str(node.slice.value)  # Converte para string

        finding = ConfigFinding(
            key=var_name,
            config_type=ConfigType.ENV_VAR,
            source_file=self.source_file,
            line_number=node.lineno,
            default_value=None,
            required=True,  # Subscript sempre é required (lança KeyError se não existir)  # noqa: E501
            context=self._current_function,
        )
        self.findings.append(finding)


class ConfigScanner:
    """Scanner principal para análise de configurações.

    Escaneia arquivos Python usando AST para detectar configurações.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Inicializa o scanner com whitelist.

        Args:
            project_root: Diretório raiz do projeto (para carregar whitelist)
        """
        self.whitelist = load_whitelist(project_root) if project_root else set()

    def scan_file(self, file_path: Path) -> list[ConfigFinding]:
        """Analisa um arquivo Python e retorna configurações encontradas.

        Args:
            file_path: Caminho do arquivo a ser analisado

        Returns:
            Lista de ConfigFinding encontradas (excluindo itens na whitelist)

        Raises:
            SyntaxError: Se o arquivo tem erros de sintaxe
            FileNotFoundError: Se o arquivo não existe
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))

            visitor = EnvVarVisitor(file_path)
            visitor.visit(tree)

            # Filtra findings usando whitelist
            return [f for f in visitor.findings if f.key not in self.whitelist]

        except SyntaxError as e:
            error_msg = f"Erro de sintaxe em {file_path}: {e}"
            raise SyntaxError(error_msg) from e

    def scan_project(
        self,
        root: Path,
        pattern: str = "**/*.py",
    ) -> ScanResult:
        """Escaneia todo o projeto recursivamente.

        Args:
            root: Diretório raiz do projeto
            pattern: Padrão glob para arquivos (padrão: "**/*.py")

        Returns:
            ScanResult com todas as configurações encontradas
        """
        start_time = time.time()
        result = ScanResult()

        python_files = list(root.glob(pattern))

        for file_path in python_files:
            # Ignora arquivos em __pycache__, .venv, .tox e site-packages
            path_parts = file_path.parts
            if any(
                part in path_parts
                for part in ["__pycache__", ".venv", ".tox", "site-packages"]
            ):
                continue

            try:
                findings = self.scan_file(file_path)
                result.findings.extend(findings)
                result.files_scanned += 1

            except SyntaxError as e:
                result.errors.append(str(e))

            except Exception as e:  # noqa: BLE001 - Captura intencional para não interromper scan
                error_msg = f"Erro ao processar {file_path}: {type(e).__name__}: {e}"
                result.errors.append(error_msg)

        end_time = time.time()
        result.scan_duration_ms = (end_time - start_time) * 1000

        return result
