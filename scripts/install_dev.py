#!/usr/bin/env python3
"""Development Environment Installation Script.

Performs complete installation of the development environment with dependency
pinning using pip-tools.

Operation Sequence:
1. Install project in editable mode with dev dependencies
2. Compile dependencies with pip-compile (with fallback)
3. Install pinned dependencies from requirements/dev.txt

Usage:
    python3 scripts/install_dev.py
    ./scripts/install_dev.py  # If it has execute permission
"""

import gettext
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

# i18n configuration
localedir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
translation = gettext.translation(
    "messages",
    localedir=localedir,
    languages=[os.getenv("LANGUAGE", "pt_BR")],
    fallback=True,
)
_ = translation.gettext

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _display_success_panel() -> None:
    """Display formatted success panel with next steps."""
    panel = """
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        {success_msg}                  ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

🔧 ATIVAR O AMBIENTE VIRTUAL:

    source .venv/bin/activate

📋 PRÓXIMOS PASSOS RECOMENDADOS:

    1️⃣  Executar testes:              make test
    2️⃣  Verificar segurança:          make audit
    3️⃣  Validação rápida (CI local):  make check
    4️⃣  Ver todos os comandos:        make help

💡 DICA: Use 'make check' antes de fazer push para garantir qualidade!

════════════════════════════════════════════════════════════════════
""".format(
        success_msg=_("✅  AMBIENTE CONFIGURADO COM SUCESSO!"),
    )
    print(panel)


def install_dev_environment(workspace_root: Path) -> int:
    """Execute complete development environment installation sequence.

    Args:
        workspace_root: Project root directory

    Returns:
        Exit code (0 = success, 1 = error)

    Raises:
        subprocess.CalledProcessError: If any installation step fails
    """
    try:
        # ========== STEP 1: Install project + pip-tools ==========
        logger.info("Step 1/3: Installing project and pip-tools...")
        result1 = subprocess.run(  # noqa: subprocess
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug("Output pip install: %s", result1.stdout.strip())

        # ========== STEP 2: Compile dependencies ==========
        logger.info("Step 2/3: Compiling dependencies with pip-compile...")

        # Try to find pip-compile in PATH
        pip_compile_path = shutil.which("pip-compile")

        if not pip_compile_path:
            # Fallback: execute pip-compile via Python module
            logger.warning(
                "pip-compile not found in PATH. Using module fallback.",
            )
            result2 = subprocess.run(  # noqa: subprocess
                [
                    sys.executable,
                    "-c",
                    "import sys; from piptools.scripts import compile; "
                    "sys.argv = ['pip-compile', '--output-file', 'requirements/dev.txt', "  # noqa: E501
                    "'requirements/dev.in']; compile.cli()",
                ],
                cwd=workspace_root,
                capture_output=True,
                text=True,
                check=True,
            )
        else:
            # Use pip-compile from PATH
            logger.debug("Usando pip-compile: %s", pip_compile_path)
            result2 = subprocess.run(  # noqa: subprocess
                [
                    pip_compile_path,
                    "--output-file",
                    "requirements/dev.txt",
                    "requirements/dev.in",
                ],
                cwd=workspace_root,
                capture_output=True,
                text=True,
                check=True,
            )
        logger.debug("Output pip-compile: %s", result2.stdout.strip())

        # ========== STEP 3: Install pinned dependencies ==========
        logger.info("Step 3/3: Installing pinned dependencies...")
        result3 = subprocess.run(  # noqa: subprocess
            [sys.executable, "-m", "pip", "install", "-r", "requirements/dev.txt"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug("Output pip install -r: %s", result3.stdout.strip())

        # ========== SUCCESS: FORMATTED PANEL ==========
        _display_success_panel()
        return 0

    except subprocess.CalledProcessError as e:
        logger.error("❌ Installation failed with exit code %s", e.returncode)
        logger.error("Failed command: %s", " ".join(e.cmd))
        if e.stderr:
            logger.error("Error: %s", e.stderr)
        return 1
    except Exception as e:
        logger.error("❌ Unexpected error: %s", e)
        return 1


def main() -> int:
    """Main script entrypoint."""
    # Detect workspace root (parent directory of scripts/)
    workspace_root = Path(__file__).parent.parent.resolve()

    logger.info("Starting development environment installation")
    logger.info("Workspace: %s", workspace_root)
    logger.info("Python: %s", sys.executable)

    return install_dev_environment(workspace_root)


if __name__ == "__main__":
    sys.exit(main())
