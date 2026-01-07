"""Dev Doctor - Environment Health Diagnostics."""

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

# Initialize Rich console
console = Console()


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    name: str
    passed: bool
    details: str
    critical: bool = False

    @property
    def message(self) -> str:
        """Alias for details (backward compatibility)."""
        return self.details


class DevDoctor:
    """Diagnoses development environment health."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize the doctor.

        Args:
            project_root: Optional project root path. If None,
                auto-detects from script location.
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = project_root
        self.venv_path = self.project_root / ".venv"
        self.venv_bin = self.venv_path / "bin"
        self.results: list[DiagnosticResult] = []

    def check_platform(self) -> DiagnosticResult:
        """Check platform strategy."""
        try:
            # Import here to avoid circular imports if strategy is broken
            from scripts.utils.platform_strategy import get_platform_strategy

            strategy = get_platform_strategy()
            git_cmd = strategy.get_git_command()
            fs_sync = strategy.ensure_durability(Path())

            fs_icon = "✓" if fs_sync else "✗"
            details = (
                f"🖥️  Platform: {strategy.__class__.__name__} | "
                f"Git: {git_cmd} | {fs_icon} fsync"
            )

            return DiagnosticResult("Platform Strategy", True, details)
        except Exception as e:
            return DiagnosticResult("Platform Strategy", False, str(e), critical=True)

    def check_python_version(self) -> DiagnosticResult:
        """Check if Python version matches .python-version."""
        try:
            version_file = self.project_root / ".python-version"
            if not version_file.exists():
                return DiagnosticResult(
                    "Python Version",
                    False,
                    ".python-version missing",
                    critical=True,
                )

            required = version_file.read_text().strip()
            v = sys.version_info
            current = f"{v.major}.{v.minor}.{v.micro}"

            if current == required:
                return DiagnosticResult(
                    "Python Version",
                    True,
                    f"Python {current} (Sincronizado)",
                )
            return DiagnosticResult(
                "Python Version",
                False,
                f"Expected {required}, got {current}",
                critical=True,
            )
        except Exception as e:
            return DiagnosticResult("Python Version", False, str(e), critical=True)

    def check_virtual_environment(self) -> DiagnosticResult:
        """Check if running in correct virtual environment."""
        # Check based on executable path relative to project
        # We check if sys.executable starts with the venv path
        is_venv = str(sys.executable).startswith(str(self.venv_path))

        # Fallback: Check VIRTUAL_ENV env var (common in activated shells)
        if not is_venv and "VIRTUAL_ENV" in os.environ:
            is_venv = os.environ["VIRTUAL_ENV"] == str(self.venv_path)

        if is_venv:
            return DiagnosticResult(
                "Virtual Environment",
                True,
                f"Virtual environment ativo: {self.venv_path}",
            )

        return DiagnosticResult(
            "Virtual Environment",
            False,
            (
                f"Executando fora do venv esperado.\n"
                f"  Esperado: {self.venv_path}\n"
                f"  Atual: {sys.executable}"
            ),
            critical=True,
        )

    def check_tool_paths(self) -> DiagnosticResult:
        """Check if tools are running from venv (Pyenv-Aware & CI-Safe)."""
        tools = ["pre-commit", "tox"]
        misaligned = []

        for tool in tools:
            # 1. Check if tool exists in .venv/bin explicitly
            venv_tool_path = self.venv_bin / tool
            if not venv_tool_path.exists():
                misaligned.append(f"{tool} missing in .venv/bin")
                continue

            # 2. Check resolution order
            resolved_path = shutil.which(tool)

            # Smart Check: If it resolves to a pyenv shim, we trust it IF
            # the venv tool exists. This avoids false positives when running
            # via Make without activating venv in shell.
            is_shim = resolved_path and ".pyenv/shims" in resolved_path

            # CI-Safe: If tool is not in PATH but exists in venv, that's OK
            # (CI environments often don't add .venv/bin to PATH)
            if not resolved_path:
                # Tool not in PATH, but it exists in venv (checked above)
                # This is acceptable - tools can be executed via full path
                continue
            if not str(resolved_path).startswith(str(self.venv_bin)) and not is_shim:
                # It's not in venv AND not a shim (e.g., /usr/bin/pre-commit)
                misaligned.append(f"{tool} -> {resolved_path}")

        if not misaligned:
            return DiagnosticResult(
                "Tool Alignment",
                True,
                "Ferramentas (pre-commit, tox) rodando do venv correto",
            )

        return DiagnosticResult(
            "Tool Alignment",
            False,
            (
                "⚠️  TOOL MISALIGNMENT detectado!\n"
                "  Ferramentas instaladas fora do venv:\n    - "
                + "\n    - ".join(misaligned)
                + "\n  💊 Prescrição: pip install -r requirements/dev.txt "
                "&& pre-commit clean && pre-commit install"
            ),
            critical=True,
        )

    def check_vital_dependencies(self) -> DiagnosticResult:
        """Check if vital packages are importable."""
        vital = ["yaml", "tox", "pre_commit", "pytest"]
        missing = []
        for package in vital:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)

        if not missing:
            return DiagnosticResult(
                "Vital Dependencies",
                True,
                f"Todas as dependências vitais instaladas ({', '.join(vital)})",
            )

        return DiagnosticResult(
            "Vital Dependencies",
            False,
            f"Missing: {', '.join(missing)}",
            critical=True,
        )

    def check_platform_specifics(self) -> DiagnosticResult:
        """Run platform specific checks."""
        # Placeholder for future windows/linux specific checks
        return DiagnosticResult("Platform Specifics", True, "Checks passed")

    def check_git_hooks(self) -> DiagnosticResult:
        """Check if git hooks are installed."""
        # Skip in CI environment
        if os.environ.get("CI"):
            return DiagnosticResult(
                "Git Hooks",
                True,
                "CI environment detected - hooks check skipped",
            )

        hook_path = self.project_root / ".git" / "hooks" / "pre-commit"

        if hook_path.exists() and os.access(hook_path, os.X_OK):
            return DiagnosticResult(
                "Git Hooks",
                True,
                "Git hooks instalados e executáveis",
            )

        # Missing or non-executable hooks are CRITICAL security issues
        if not hook_path.exists():
            message = (
                "Git hooks não encontrados. Execute 'pre-commit install' para instalar."
            )
        else:
            message = (
                "Git hooks não é executável. "
                "Execute 'chmod +x .git/hooks/pre-commit' ou 'pre-commit install'."
            )

        return DiagnosticResult(
            "Git Hooks",
            False,
            message,
            critical=True,  # Changed from False to True - security critical
        )

    def check_type_stubs(self) -> DiagnosticResult:
        """Check for type stubs."""
        stubs = ["types-requests", "types-PyYAML"]
        found = []

        # Use importlib.metadata if available (Python 3.8+)
        # This is more robust than importlib.util for stub packages
        try:
            from importlib.metadata import distributions

            installed = {dist.metadata["Name"].lower() for dist in distributions()}
            for stub in stubs:
                if stub.lower() in installed:
                    found.append(stub)
        except ImportError:
            # Fallback for very old environments
            import importlib.util

            for stub in stubs:
                pkg_name = stub.replace("-", "_")
                if importlib.util.find_spec(pkg_name) or importlib.util.find_spec(stub):
                    found.append(stub)

        if len(found) > 0:
            return DiagnosticResult(
                "Type Stubs",
                True,
                f"Stubs de tipagem verificados ({len(found)} pacotes)",
            )
        return DiagnosticResult(
            "Type Stubs",
            False,
            "No type stubs found",
            critical=False,
        )

    def check_lockfile_sync(self) -> DiagnosticResult:
        """Check if requirements.txt is synchronized with .in file.

        This is a CRITICAL check that prevents development with
        desynchronized dependency files.

        Returns:
            DiagnosticResult: Critical failure if files are desynchronized.
        """
        try:
            # Import verification logic
            from scripts.ci.verify_deps import check_sync

            # Check dev requirements (primary lockfile)
            if check_sync("dev"):
                return DiagnosticResult(
                    "Lockfile Sync",
                    True,
                    "requirements/dev.txt sincronizado com dev.in ✓",
                )

            return DiagnosticResult(
                "Lockfile Sync",
                False,
                (
                    "❌ requirements/dev.txt está DESSINCRONIZADO com dev.in!\n"
                    "  🔒 RISCO: Dependências incorretas podem estar instaladas.\n"
                    "  💊 PRESCRIÇÃO:\n"
                    "     1. Execute: make requirements\n"
                    "     2. Ou: pip-compile requirements/dev.in "
                    "-o requirements/dev.txt\n"
                    "     3. Depois: git add requirements/dev.txt"
                ),
                critical=True,
            )
        except ImportError as e:
            return DiagnosticResult(
                "Lockfile Sync",
                False,
                f"Erro ao importar verify_deps: {e}",
                critical=True,
            )
        except Exception as e:
            return DiagnosticResult(
                "Lockfile Sync",
                False,
                f"Erro inesperado ao verificar lockfile: {e}",
                critical=True,
            )

    def run_diagnostics(self) -> bool:
        """Run all diagnostic checks.

        Returns:
            bool: True if all checks passed, False if critical failures detected.
        """
        print("🔍 Dev Doctor - Diagnóstico de Ambiente\n")
        print(f"Projeto: {self.project_root}\n")

        checks = [
            self.check_platform(),
            self.check_python_version(),
            self.check_virtual_environment(),
            self.check_tool_paths(),
            self.check_vital_dependencies(),
            self.check_type_stubs(),
            self.check_git_hooks(),
            self.check_lockfile_sync(),  # CRITICAL: Dependency autoimmunity
        ]

        critical_failure = False

        for result in checks:
            icon = "✓" if result.passed else "✗"
            color = "green" if result.passed else "red"

            console.print(f"[{color}]{icon} {result.name}[/]")
            if result.details:
                console.print(f"  {result.details}\n")

            if not result.passed and result.critical:
                critical_failure = True

        console.print("────────────────────────────────────────────────────────────")
        if critical_failure:
            console.print(
                "[red bold]✗ Ambiente DOENTE - 1 problema(s) crítico(s) "
                "detectado(s)! 🚨[/]",
            )
            console.print("\nExecute as correções sugeridas acima antes de continuar.")
            return False
        console.print(
            "[green bold]✓ Ambiente SAUDÁVEL - Pronto para desenvolvimento! 🎉[/]",
        )
        return True


def main() -> None:
    """CLI Entrypoint."""
    doctor = DevDoctor()
    success = doctor.run_diagnostics()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
