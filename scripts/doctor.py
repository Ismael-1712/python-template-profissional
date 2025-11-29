#!/usr/bin/env python3
"""Dev Doctor - Diagnóstico Preventivo de Ambiente de Desenvolvimento.

===================================================================
Script para detectar problemas de ambiente (Drift) antes de executar
comandos críticos. Usa APENAS a Standard Library para rodar em ambientes
quebrados.

Exit Codes:
    0 - Ambiente saudável
    1 - Problemas detectados
"""

import importlib.util
import os
import shutil
import sys
from pathlib import Path

# Códigos de Cores ANSI (para não depender de libs externas)
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


class DiagnosticResult:
    """Resultado de uma verificação diagnóstica."""

    def __init__(
        self, name: str, passed: bool, message: str, critical: bool = True
    ) -> None:
        """Inicializa o resultado do diagnóstico."""
        self.name = name
        self.passed = passed
        self.message = message
        self.critical = critical


class DevDoctor:
    """Diagnosticador de ambiente de desenvolvimento."""

    def __init__(self, project_root: Path) -> None:
        """Inicializa o DevDoctor com a raiz do projeto."""
        self.project_root = project_root
        self.results: list[DiagnosticResult] = []

    def check_python_version(self) -> DiagnosticResult:
        """Verifica compatibilidade da versão Python e detecta Drift."""
        python_version_file = self.project_root / ".python-version"

        if not python_version_file.exists():
            return DiagnosticResult(
                "Python Version",
                False,
                "Arquivo .python-version não encontrado",
                critical=False,
            )

        try:
            content = python_version_file.read_text().strip()
            # Pega primeira versão (principal) do arquivo
            expected_version = content.split()[0].strip()

            current_major = sys.version_info.major
            current_minor = sys.version_info.minor
            current_micro = sys.version_info.micro
            current_full = f"{current_major}.{current_minor}.{current_micro}"

            # Drift Check: A versão exata deve bater com a esperada
            # (Ex: se .python-version diz 3.12.12, e estamos no 3.12.2, é Drift)
            exact_match = current_full == expected_version

            if exact_match:
                return DiagnosticResult(
                    "Python Version",
                    True,
                    f"Python {current_full} (Sincronizado)",
                )

            # Se não bate exato, verifica se estamos no CI (flexível)
            if os.environ.get("CI"):
                return DiagnosticResult(
                    "Python Version",
                    True,
                    f"Python {current_full} (CI Environment - Drift ignorado)",
                )

            # Se for local, é um erro crítico de Drift
            return DiagnosticResult(
                "Python Version",
                False,
                f"⚠️  ENVIRONMENT DRIFT DETECTADO!\n"
                f"  Versão ativa:   {current_full}\n"
                f"  Versão esperada: {expected_version}\n"
                f"  💊 Prescrição: Reinstale o venv com a versão correta:\n"
                f"      rm -rf .venv && python{expected_version} -m venv .venv "
                f"&& source .venv/bin/activate && make install-dev",
                critical=True,
            )

        except Exception as e:
            return DiagnosticResult(
                "Python Version", False, f"Erro ao ler versão: {e}", critical=True
            )

    def check_virtual_environment(self) -> DiagnosticResult:
        """Verifica se está rodando dentro de um virtual environment."""
        if os.environ.get("CI"):
            return DiagnosticResult(
                "Virtual Environment",
                True,
                "Ambiente CI detectado (Venv check skipped)",
            )

        in_venv = sys.prefix != sys.base_prefix

        if in_venv:
            return DiagnosticResult(
                "Virtual Environment",
                True,
                f"Virtual environment ativo: {sys.prefix}",
            )
        else:
            return DiagnosticResult(
                "Virtual Environment",
                False,
                "Não está em um virtual environment!\n"
                "  💊 Prescrição: python -m venv .venv && "
                "source .venv/bin/activate && make install-dev",
                critical=True,
            )

    def check_tool_paths(self) -> DiagnosticResult:
        """Verifica se ferramentas críticas estão no ambiente correto."""
        if os.environ.get("CI"):
            return DiagnosticResult(
                "Tool Paths", True, "Ambiente CI detectado (Tool check skipped)"
            )

        # Se não estiver em venv, já falhou no check anterior
        if sys.prefix == sys.base_prefix:
            return DiagnosticResult("Tool Paths", False, "Skipped (No Venv)", False)

        venv_bin = Path(sys.prefix) / "bin"
        tools_to_check = ["pre-commit", "tox"]
        misaligned_tools = []

        for tool in tools_to_check:
            tool_path = shutil.which(tool)
            if not tool_path:
                misaligned_tools.append(f"{tool} (não encontrado)")
                continue

            # Verifica se o caminho da ferramenta começa com o caminho do venv
            # Resolve symlinks para garantir
            try:
                tool_path_obj = Path(tool_path).resolve()
                venv_bin_obj = venv_bin.resolve()
                if not str(tool_path_obj).startswith(str(venv_bin_obj)):
                    misaligned_tools.append(f"{tool} -> {tool_path}")
            except Exception:
                misaligned_tools.append(f"{tool} (erro ao resolver path)")

        if not misaligned_tools:
            return DiagnosticResult(
                "Tool Alignment",
                True,
                "Ferramentas (pre-commit, tox) rodando do venv correto",
            )
        else:
            tools_info = "\n".join([f"    - {t}" for t in misaligned_tools])
            return DiagnosticResult(
                "Tool Alignment",
                False,
                f"⚠️  TOOL MISALIGNMENT detectado!\n"
                f"  Ferramentas instaladas fora do venv ({venv_bin}):\n{tools_info}\n"
                f"  💊 Prescrição: pip install -r requirements/dev.txt && "
                f"pre-commit clean && pre-commit install",
                critical=True,
            )

    def check_vital_dependencies(self) -> DiagnosticResult:
        """Verifica se dependências vitais estão instaladas."""
        vital_deps = ["yaml", "tox", "pre_commit"]
        missing_deps = []

        import_map = {
            "yaml": "yaml",
            "tox": "tox",
            "pre_commit": "pre_commit",
        }

        for dep in vital_deps:
            module_name = import_map.get(dep, dep)
            if importlib.util.find_spec(module_name) is None:
                missing_deps.append(dep)

        if not missing_deps:
            return DiagnosticResult(
                "Vital Dependencies",
                True,
                f"Todas as dependências vitais instaladas ({', '.join(vital_deps)})",
            )
        else:
            return DiagnosticResult(
                "Vital Dependencies",
                False,
                f"Dependências faltando: {', '.join(missing_deps)}.\n"
                "  💊 Prescrição: make install-dev",
                critical=True,
            )

    def check_git_hooks(self) -> DiagnosticResult:
        """Verifica se os Git hooks estão instalados e executáveis."""
        if os.environ.get("CI"):
            return DiagnosticResult(
                "Git Hooks", True, "Ambiente CI detectado (Hooks check skipped)"
            )

        git_hooks_dir = self.project_root / ".git" / "hooks"
        pre_commit_hook = git_hooks_dir / "pre-commit"

        if pre_commit_hook.exists():
            if os.access(pre_commit_hook, os.X_OK):
                return DiagnosticResult(
                    "Git Hooks", True, "Git hooks instalados e executáveis"
                )
            else:
                return DiagnosticResult(
                    "Git Hooks",
                    False,
                    "Hook pre-commit existe mas não é executável\n"
                    "  💊 Prescrição: chmod +x .git/hooks/pre-commit",
                    critical=True,
                )
        else:
            return DiagnosticResult(
                "Git Hooks",
                False,
                "Hooks não instalados. O pre-commit pode não rodar.\n"
                "  💊 Prescrição: pre-commit install",
                critical=False,  # Warning apenas
            )

    def run_diagnostics(self) -> bool:
        """Executa todas as verificações diagnósticas."""
        print(f"{BOLD}{BLUE}🔍 Dev Doctor - Diagnóstico de Ambiente{RESET}\n")
        print(f"Projeto: {self.project_root}\n")

        self.results.append(self.check_python_version())
        self.results.append(self.check_virtual_environment())
        self.results.append(self.check_tool_paths())
        self.results.append(self.check_vital_dependencies())
        self.results.append(self.check_git_hooks())

        critical_failures = 0
        warnings = 0

        for result in self.results:
            if result.passed:
                print(f"{GREEN}✓ {result.name}{RESET}")
                print(f"  {result.message}\n")
            else:
                if result.critical:
                    print(f"{RED}✗ {result.name} (CRÍTICO){RESET}")
                    critical_failures += 1
                else:
                    print(f"{YELLOW}! {result.name} (aviso){RESET}")
                    warnings += 1
                print(f"  {result.message}\n")

        print("────────────────────────────────────────────────────────────")

        if critical_failures == 0 and warnings == 0:
            print(
                f"{GREEN}{BOLD}✓ Ambiente SAUDÁVEL{RESET} - "
                "Pronto para desenvolvimento! 🎉\n"
            )
            return True

        if critical_failures > 0:
            print(
                f"{RED}{BOLD}✗ Ambiente DOENTE{RESET} - "
                f"{critical_failures} problema(s) crítico(s) detectado(s)! 🚨"
            )
            if warnings > 0:
                print(f"  (Também foram encontrados {warnings} avisos)")
            print("\nExecute as correções sugeridas acima antes de continuar.")
            return False

        if warnings > 0:
            print(
                f"{YELLOW}{BOLD}⚠  Ambiente COM AVISOS{RESET} - "
                f"{warnings} aviso(s) detectado(s)"
            )
            print("  (Não-críticos, mas recomenda-se corrigir)\n")
            return True

        return True


def main() -> int:
    """Função principal."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    doctor = DevDoctor(project_root)
    success = doctor.run_diagnostics()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
