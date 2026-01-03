"""Tool for verifying dependency synchronization.

This script ensures that requirements.txt files are perfectly synchronized
with their corresponding .in files, acting as an auto-immune mechanism
against dependency drift.
"""

import os
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

    # Use venv Python if available to avoid dependency conflicts
    venv_python = project_root / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

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
                "--quiet",
            ],
            cwd=str(project_root),
        )

        if _compare_files_content(project_root / txt_file, Path(tmp_path)):
            print("✅ Sincronizado")
            return True

        print("❌ DESSINCRONIZADO")
        # Show filtered diff (only real lines)
        print("--- Diff (ignoring comments) ---")
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
