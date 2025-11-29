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
        """Verifica se a versão do Python é compatível com .python-version."""
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
            allowed_versions = [v.strip() for v in content.split() if v.strip()]

            current_major = sys.version_info.major
            current_minor = sys.version_info.minor
            current_full = f"{current_major}.{current_minor}.{sys.version_info.micro}"
            current_mm = f"{current_major}.{current_minor}"

            match = False
            for allowed in allowed_versions:
                parts = allowed.split(".")
                if len(parts) >= 2:
                    allowed_mm = f"{parts[0]}.{parts[1]}"
                    if allowed_mm == current_mm:
                        match = True
                        break

            if match:
                return DiagnosticResult(
                    "Python Version",
                    True,
                    f"Python {current_full} compatível com {allowed_versions}",
                )

            if os.environ.get("CI"):
                return DiagnosticResult(
                    "Python Version",
                    True,
                    f"Python {current_full} (CI Environment - Bypass strict check)",
                )

            return DiagnosticResult(
                "Python Version",
                False,
                f"Python {current_full} detectado, mas .python-version requer: "
                f"{', '.join(allowed_versions)}",
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
                "Não está em um virtual environment! Use 'python -m venv .venv' "
                "e ative-o.",
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
                f"Dependências faltando: {', '.join(missing_deps)}. "
                "Execute 'make install-dev'",
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
                    "Hook pre-commit existe mas não é executável",
                    critical=True,
                )
        else:
            return DiagnosticResult(
                "Git Hooks",
                False,
                "Hooks não instalados. O pre-commit pode não rodar.",
                critical=False,
            )

    def run_diagnostics(self) -> bool:
        """Executa todas as verificações diagnósticas."""
        print(f"{BOLD}{BLUE}🔍 Dev Doctor - Diagnóstico de Ambiente{RESET}\n")
        print(f"Projeto: {self.project_root}\n")

        self.results.append(self.check_python_version())
        self.results.append(self.check_virtual_environment())
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
