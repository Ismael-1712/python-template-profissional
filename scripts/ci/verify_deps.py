"""Tool for verifying dependency synchronization with cryptographic integrity.

This script ensures that requirements.txt files are perfectly synchronized
with their corresponding .in files, acting as an auto-immune mechanism
against dependency drift with SHA-256 cryptographic sealing.

Features:
- Python baseline awareness (uses PYTHON_BASELINE env var)
- Comment-aware comparison (ignores pip-compile metadata)
- CI/CD compatible (venv detection)
- Detailed error reporting with remediation steps
- Auto-fix capability (--fix flag) for self-healing
- Cryptographic integrity seals (v2.2 Autoimunity Protocol)

Exit Codes:
- 0: Lockfile synchronized or successfully fixed
- 1: Lockfile desynchronized (without --fix) or fix failed
- 2: Integrity seal validation failed (critical security breach)
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _ensure_piptools_installed(python_exec: str, project_root: Path) -> bool:
    """Ensure pip-tools is installed in the target Python interpreter.

    This implements the auto-immune mechanism: before attempting to use
    piptools, we verify it's available. If not, we install it on-the-fly.

    Args:
        python_exec: Path to Python interpreter to check/install pip-tools
        project_root: Project root directory for working directory context

    Returns:
        bool: True if pip-tools is available (or was successfully installed)
    """
    # Check if piptools is already available
    check_result = subprocess.run(  # nosec # noqa: S603
        [python_exec, "-m", "pip", "show", "pip-tools"],
        cwd=str(project_root),
        capture_output=True,
        check=False,
    )

    if check_result.returncode == 0:
        return True  # Already installed

    # Auto-immune response: install pip-tools
    print("\n  💉 AUTOIMUNIDADE: Instalando pip-tools...", end="", flush=True)
    try:
        subprocess.check_call(  # nosec # noqa: S603
            [python_exec, "-m", "pip", "install", "pip-tools", "--quiet"],
            cwd=str(project_root),
        )
        print(" ✅")
        return True
    except subprocess.CalledProcessError:
        print(" ❌")
        return False


def check_sync(req_name: str) -> bool:
    """Verify if a requirements file is synchronized with its input file.

    Args:
        req_name: The name of the requirements file (e.g., 'dev', 'prod').

    Returns:
        bool: True if synchronized, False otherwise.
    """
    project_root = Path(__file__).parent.parent.parent.resolve()
    in_file = Path("requirements") / f"{req_name}.in"
    txt_file = Path("requirements") / f"{req_name}.txt"

    print(f"🔍 Verificando integridade de {req_name}...", end=" ", flush=True)

    # Python Selection Strategy (Priority Order):
    # 1. PYTHON_BASELINE env var (e.g., "3.10" for CI compatibility)
    # 2. .venv/bin/python (local development)
    # 3. sys.executable (fallback)
    baseline_version = os.getenv("PYTHON_BASELINE")
    python_exec = sys.executable  # Default fallback

    if baseline_version:
        # Try to use baseline Python (e.g., python3.10)
        baseline_exec = shutil.which(f"python{baseline_version}")
        if baseline_exec:
            python_exec = baseline_exec
            print(
                f"\n  🎯 Usando Python {baseline_version} (baseline) para pip-compile",
            )
        else:
            print(
                f"\n  ⚠️  PYTHON_BASELINE={baseline_version} definido, mas "
                f"python{baseline_version} não encontrado no PATH",
            )
            print(f"  ⚠️  Usando fallback: {sys.executable}")
    else:
        # Try venv Python first for local dev
        venv_python = project_root / ".venv" / "bin" / "python"
        if venv_python.exists():
            python_exec = str(venv_python)

    # AUTO-IMMUNE CHECK: Ensure pip-tools is installed
    if not _ensure_piptools_installed(python_exec, project_root):
        print("\n❌ ERRO: Não foi possível instalar pip-tools")
        return False

    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Execute pip-compile from root using RELATIVE paths
        subprocess.check_call(
            [
                python_exec,
                "-m",
                "piptools",
                "compile",
                str(in_file),
                "--output-file",
                tmp_path,
                "--resolver=backtracking",
                "--strip-extras",
                "--allow-unsafe",  # Include pip/setuptools for reproducible builds
                "--quiet",
            ],
            cwd=str(project_root),
        )

        if _compare_files_content(project_root / txt_file, Path(tmp_path)):
            print("✅ Sincronizado")
            return True

        print("❌ DESSINCRONIZADO")
        print("\n💊 PRESCRIÇÃO DE CORREÇÃO:")
        print("   1. Execute: make requirements")
        print(f"   2. Ou: python{baseline_version or ''} -m piptools compile \\")
        print(f"          {in_file} --output-file {txt_file} \\")
        print("          --resolver=backtracking --strip-extras --allow-unsafe")
        print("   3. Depois: git add requirements/dev.txt")
        print("\n--- Diff (apenas dependências, ignorando comentários) ---")
        try:
            # Using check_call to match project pattern (shell=False, validated inputs)
            subprocess.check_call(
                ["diff", "-I", "^#", str(project_root / txt_file), tmp_path],
            )
        except subprocess.CalledProcessError:
            pass  # diff returns non-zero when files differ (expected)
        return False

    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERRO FATAL ao executar pip-compile (Exit Code {e.returncode}).")
        return False
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _compare_files_content(path_a: Path, path_b: Path) -> bool:
    if not path_a.exists():
        return False
    with open(path_a) as fa, open(path_b) as fb:
        # Ignore ALL lines starting with # (comments, paths, timestamps)
        lines_a = [
            line.strip()
            for line in fa
            if line.strip() and not line.strip().startswith("#")
        ]
        lines_b = [
            line.strip()
            for line in fb
            if line.strip() and not line.strip().startswith("#")
        ]
    return lines_a == lines_b


def fix_sync(req_name: str) -> bool:
    """Auto-fix desynchronization by recompiling with pip-compile.

    This function implements the self-healing mechanism: it recompiles
    the requirements.txt file using the Python baseline to ensure
    compatibility with CI environments.

    Args:
        req_name: The name of the requirements file (e.g., 'dev', 'prod').

    Returns:
        bool: True if fix succeeded, False otherwise.

    Strategy:
        1. Detect Python baseline from PYTHON_BASELINE env var
        2. Ensure pip-tools is installed in baseline Python
        3. Run pip-compile with exact CI-compatible flags
        4. Validate output and report success
    """
    project_root = Path(__file__).parent.parent.parent.resolve()
    in_file = Path("requirements") / f"{req_name}.in"
    txt_file = Path("requirements") / f"{req_name}.txt"

    print(f"\n🔧 MODO AUTOCURA ATIVADO: Corrigindo {req_name}.txt...", flush=True)

    # Python Selection (same strategy as check_sync)
    baseline_version = os.getenv("PYTHON_BASELINE")
    python_exec = sys.executable  # Default fallback

    if baseline_version:
        baseline_exec = shutil.which(f"python{baseline_version}")
        if baseline_exec:
            python_exec = baseline_exec
            print(
                f"  ✅ Usando Python {baseline_version} (baseline CI-compatible)",
            )
        else:
            print(
                f"  ⚠️  PYTHON_BASELINE={baseline_version} definido, mas "
                f"python{baseline_version} não encontrado",
            )
            print(f"  ⚠️  Usando fallback: {sys.executable}")
    else:
        # Try venv Python for local dev
        venv_python = project_root / ".venv" / "bin" / "python"
        if venv_python.exists():
            python_exec = str(venv_python)

    print(f"  📦 Executor: {python_exec}")

    # AUTO-IMMUNE CHECK: Ensure pip-tools is installed
    if not _ensure_piptools_installed(python_exec, project_root):
        print("\n❌ ERRO: Não foi possível instalar pip-tools")
        return False

    try:
        # Execute pip-compile with CI-compatible flags
        print(f"  ⚙️  Recompilando {in_file}...", end=" ", flush=True)
        subprocess.check_call(
            [
                python_exec,
                "-m",
                "piptools",
                "compile",
                str(in_file),
                "--output-file",
                str(txt_file),
                "--resolver=backtracking",
                "--strip-extras",
                "--allow-unsafe",
                "--quiet",
            ],
            cwd=str(project_root),
        )
        print("✅")

        print(f"\n✅ AUTOCURA COMPLETA: {txt_file} sincronizado com sucesso!")
        print("\n💡 PRÓXIMO PASSO:")
        print(f"   git add {txt_file}")
        print("   git commit -m 'build: sync requirements lockfile'")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERRO FATAL: Falha ao executar autocura (Exit Code {e.returncode})")
        return False


if __name__ == "__main__":
    # Argument parsing for --fix and --validate-seal flags
    parser = argparse.ArgumentParser(
        description="Dependency Synchronization Validator with Cryptographic Integrity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detection only (CI mode)
  python scripts/ci/verify_deps.py

  # Auto-fix mode (local development)
  PYTHON_BASELINE=3.10 python scripts/ci/verify_deps.py --fix

  # Validate cryptographic seal only
  python scripts/ci/verify_deps.py --validate-seal

Exit Codes:
  0 - Lockfile synchronized or successfully fixed
  1 - Lockfile desynchronized (without --fix) or fix failed
  2 - Integrity seal validation failed (security breach)
        """,
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix desynchronization by recompiling with pip-compile",
    )
    parser.add_argument(
        "--validate-seal",
        action="store_true",
        help="Validate cryptographic integrity seal (v2.2 Protocol)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent.resolve()

    # If seal validation requested, check and exit
    if args.validate_seal:
        try:
            # Import Guardian for seal validation
            sys.path.insert(0, str(project_root))
            from scripts.core.dependency_guardian import DependencyGuardian

            guardian = DependencyGuardian(project_root / "requirements")

            print(
                "🔐 Validando selo de integridade criptográfico...",
                end=" ",
                flush=True,
            )
            is_valid = guardian.validate_seal("dev")

            if is_valid:
                print("✅ VÁLIDO")
                print(
                    "✅ Protocolo v2.2: Lockfile protegido contra adulteração",
                )
                sys.exit(0)
            else:
                print("❌ FALHOU")
                print(
                    "\n🚨 ALERTA: Selo de integridade inválido ou ausente!",
                )
                print("   Possível adulteração detectada no lockfile.")
                print("\n💊 REMEDIAÇÃO:")
                print("   make deps-fix")
                sys.exit(2)
        except Exception as e:
            print(f"\n❌ ERRO: Falha na validação do selo: {e}")
            sys.exit(2)

    # Execute check
    is_synced = check_sync("dev")

    if is_synced:
        sys.exit(0)
    # Desynchronized detected
    elif args.fix:
        # Attempt auto-fix
        if fix_sync("dev"):
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # No fix requested, exit with error
        sys.exit(1)
        sys.exit(1)
