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

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

# Adiciona raiz do projeto ao sys.path para imports
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.utils.banner import print_startup_banner  # noqa: E402
from scripts.utils.context import trace_context  # noqa: E402
from scripts.utils.logger import get_colors, setup_logging  # noqa: E402
from scripts.utils.platform_strategy import get_platform_strategy  # noqa: E402

# Configure structured logging
logger = setup_logging(__name__)

# Obtém cores com detecção automática de terminal
colors = get_colors()
RED = colors.RED
GREEN = colors.GREEN
YELLOW = colors.YELLOW
BLUE = colors.BLUE
BOLD = colors.BOLD
RESET = colors.RESET


class DiagnosticResult:
    """Resultado de uma verificação diagnóstica."""

    def __init__(
        self,
        name: str,
        passed: bool,
        message: str,
        critical: bool = True,
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

    def check_python_version(self, *, strict: bool = False) -> DiagnosticResult:
        """Verifica compatibilidade da versão Python e detecta Drift.

        Args:
            strict: Se True, exige match exato. Se False (padrão),
                   aceita diferenças no patch level se major.minor batem.

        Returns:
            DiagnosticResult com status da verificação
        """
        # CI: Confia na matriz de versões do GitHub Actions
        if os.environ.get("CI"):
            current_version = sys.version.split()[0]
            return DiagnosticResult(
                "Python Version",
                True,
                f"Python {current_version} (CI Environment - Matriz Ativa)",
            )

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

            # Parse expected version
            exp_parts = expected_version.split(".")
            if len(exp_parts) < 3:
                return DiagnosticResult(
                    "Python Version",
                    False,
                    f"Formato inválido em .python-version: {expected_version}",
                    critical=True,
                )

            exp_major = int(exp_parts[0])
            exp_minor = int(exp_parts[1])
            exp_micro = int(exp_parts[2])

            # Check major.minor (sempre deve bater)
            if (current_major, current_minor) != (exp_major, exp_minor):
                return DiagnosticResult(
                    "Python Version",
                    False,
                    f"⚠️  INCOMPATIBILIDADE DE VERSÃO!\n"
                    f"  Versão ativa:   {current_full}\n"
                    f"  Versão esperada: {expected_version}\n"
                    f"  💊 Prescrição: Instale Python {exp_major}.{exp_minor}:\n"
                    f"      pyenv install {expected_version} && "
                    f"pyenv local {expected_version}",
                    critical=True,
                )

            # Major.minor batem, verificar patch
            if current_micro == exp_micro:
                return DiagnosticResult(
                    "Python Version",
                    True,
                    f"Python {current_full} (Sincronizado)",
                )

            # Patch diferente
            if strict:
                # Modo estrito: exige patch exato
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

            # Modo flexível (padrão): aceita patch >= ou avisa
            if current_micro > exp_micro:
                return DiagnosticResult(
                    "Python Version",
                    True,
                    f"Python {current_full} (Patch mais novo que {expected_version}, "
                    f"compatível)",
                )

            # current_micro < exp_micro
            return DiagnosticResult(
                "Python Version",
                True,  # Não falhar, mas avisar
                f"Python {current_full} (Patch mais antigo que {expected_version}, "
                f"mas compatível. Considere atualizar)",
            )

        except Exception as e:
            return DiagnosticResult(
                "Python Version",
                False,
                f"Erro ao ler versão: {e}",
                critical=True,
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
                "Tool Paths",
                True,
                "Ambiente CI detectado (Tool check skipped)",
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
        vital_deps = ["yaml", "tox", "pre_commit", "pytest"]

        # No CI, ferramentas de dev local (tox, pre-commit) não são vitais
        # pois os testes rodam diretamente via pytest e linters em jobs separados
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            vital_deps = [d for d in vital_deps if d not in ["tox", "pre_commit"]]

        missing_deps = []

        import_map = {
            "yaml": "yaml",
            "tox": "tox",
            "pre_commit": "pre_commit",
            "pytest": "pytest",
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
        return DiagnosticResult(
            "Vital Dependencies",
            False,
            f"Dependências faltando: {', '.join(missing_deps)}.\n"
            "  💊 Prescrição: make install-dev",
            critical=True,
        )

    def check_platform(self) -> DiagnosticResult:
        """Verifica a estratégia de plataforma e comando git resolvido."""
        try:
            strategy = get_platform_strategy()
            strategy_name = strategy.__class__.__name__
            git_cmd = strategy.get_git_command()

            # Verifica se fsync está disponível
            has_fsync = hasattr(strategy, "ensure_durability")
            fsync_status = "✓ fsync" if has_fsync else "⚠ no fsync"

            # Identifica plataforma base
            platform_display = "Linux/Unix" if "Unix" in strategy_name else "Windows"

            # Localiza git no sistema (se possível)
            git_path = shutil.which(git_cmd) or git_cmd

            return DiagnosticResult(
                "Platform Strategy",
                True,
                f"🖥️  Platform: {platform_display} ({strategy_name}) | "
                f"Git: {git_path} | {fsync_status}",
            )
        except Exception as e:
            return DiagnosticResult(
                "Platform Strategy",
                False,
                f"Erro ao detectar estratégia de plataforma: {e}",
                critical=False,
            )

    def check_git_hooks(self) -> DiagnosticResult:
        """Verifica se os Git hooks estão instalados e executáveis."""
        if os.environ.get("CI"):
            return DiagnosticResult(
                "Git Hooks",
                True,
                "Ambiente CI detectado (Hooks check skipped)",
            )

        git_hooks_dir = self.project_root / ".git" / "hooks"
        pre_commit_hook = git_hooks_dir / "pre-commit"

        if pre_commit_hook.exists():
            if os.access(pre_commit_hook, os.X_OK):
                return DiagnosticResult(
                    "Git Hooks",
                    True,
                    "Git hooks instalados e executáveis",
                )
            return DiagnosticResult(
                "Git Hooks",
                False,
                "Hook pre-commit existe mas não é executável\n"
                "  💊 Prescrição: chmod +x .git/hooks/pre-commit",
                critical=True,
            )
        return DiagnosticResult(
            "Git Hooks",
            False,
            "🚨 SEGURANÇA: Hooks não instalados. Ambiente VULNERÁVEL!\n"
            "  Desenvolvedores podem commitar código sem verificações de qualidade.\n"
            "  💊 Prescrição: pre-commit install",
            critical=True,  # BLOQUEADOR: sem hooks = ambiente inseguro
        )

    def check_type_stubs(self) -> DiagnosticResult:
        """Verifica se os stubs vitais para o MyPy estão instalados (Autoimunidade)."""
        required_stubs = [
            "types-PyYAML",
            "types-requests",
            "pydantic-settings",
        ]

        missing = []
        import json
        import subprocess

        # Verificação robusta via pip list
        try:
            result = subprocess.run(  # noqa: subprocess
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Normaliza para lowercase para comparação
            installed_packages = {
                pkg["name"].lower() for pkg in json.loads(result.stdout)
            }

            for stub in required_stubs:
                if stub.lower() not in installed_packages:
                    missing.append(stub)

        except Exception as e:
            return DiagnosticResult(
                "Type Stubs",
                False,
                f"⚠️ Erro ao verificar pacotes: {e}\n"
                "  💊 Prescrição: Reinstale o ambiente com 'make install-dev'",
                critical=True,
            )

        if missing:
            return DiagnosticResult(
                "Type Stubs",
                False,
                f"🚨 AUTOIMUNIDADE: Stubs/Libs faltantes: {', '.join(missing)}\n"
                "  Sem esses stubs, o type-check FALHARÁ silenciosamente!\n"
                "  💊 Prescrição: make install-dev",
                critical=True,
            )

        return DiagnosticResult(
            "Type Stubs",
            True,
            f"Stubs de tipagem verificados ({len(required_stubs)} pacotes)",
        )

    def run_diagnostics(self) -> bool:
        """Executa todas as verificações diagnósticas."""
        print(f"{BOLD}{BLUE}🔍 Dev Doctor - Diagnóstico de Ambiente{RESET}\n")
        print(f"Projeto: {self.project_root}\n")

        self.results.append(self.check_platform())
        self.results.append(self.check_python_version())
        self.results.append(self.check_virtual_environment())
        self.results.append(self.check_tool_paths())
        self.results.append(self.check_vital_dependencies())
        self.results.append(self.check_type_stubs())
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
                "Pronto para desenvolvimento! 🎉\n",
            )
            return True

        if critical_failures > 0:
            print(
                f"{RED}{BOLD}✗ Ambiente DOENTE{RESET} - "
                f"{critical_failures} problema(s) crítico(s) detectado(s)! 🚨",
            )
            if warnings > 0:
                print(f"  (Também foram encontrados {warnings} avisos)")
            print("\nExecute as correções sugeridas acima antes de continuar.")
            return False

        if warnings > 0:
            print(
                f"{YELLOW}{BOLD}⚠  Ambiente COM AVISOS{RESET} - "
                f"{warnings} aviso(s) detectado(s)",
            )
            print("  (Não-críticos, mas recomenda-se corrigir)\n")
            return True

        return True


def main() -> int:
    """Função principal."""
    # Banner de inicialização
    print_startup_banner(
        tool_name="Dev Doctor",
        version="2.0.0",
        description="Environment Health Diagnostics and Drift Detection",
        script_path=Path(__file__),
    )

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    doctor = DevDoctor(project_root)
    success = doctor.run_diagnostics()

    return 0 if success else 1


if __name__ == "__main__":
    with trace_context():
        sys.exit(main())
