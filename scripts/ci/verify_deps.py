"""Tool for verifying dependency synchronization.

This script ensures that requirements.txt files are perfectly synchronized
with their corresponding .in files, acting as an auto-immune mechanism
against dependency drift.

Features:
- Python baseline awareness (uses PYTHON_BASELINE env var)
- Comment-aware comparison (ignores pip-compile metadata)
- CI/CD compatible (venv detection)
- Detailed error reporting with remediation steps
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


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
                "--strip-extras --allow-unsafe",
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


if __name__ == "__main__":
    if check_sync("dev"):
        sys.exit(0)
    else:
        sys.exit(1)
