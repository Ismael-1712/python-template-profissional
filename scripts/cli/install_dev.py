#!/usr/bin/env python3
# ruff: noqa: RUF100
"""Development Environment Installation Script.

Performs complete installation of the development environment with dependency
pinning using pip-tools.

Operation Sequence:
1. Install project in editable mode with dev dependencies
2. Compile dependencies with pip-compile (with fallback) - ATOMIC WRITES
3. Install pinned dependencies from requirements/dev.txt

Usage:
    python3 scripts/cli/install_dev.py
    make install-dev  # Via Makefile
"""

# Standard library imports
import logging
import subprocess
import sys
from pathlib import Path

# --- BOOTSTRAP FIX: Adiciona raiz ao path ANTES de imports locais ---
# Necessário porque este script roda antes do pacote estar instalado via pip.
# Estrutura: root/scripts/cli/install_dev.py -> sobe 3 níveis para root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# -------------------------------------------------------------------

# Standard library imports (continued after sys.path fix)
import gettext  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402

# Local application imports
from scripts.utils.banner import print_startup_banner  # noqa: E402
from scripts.utils.safe_pip import safe_pip_compile  # noqa: E402

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


def _setup_direnv(workspace_root: Path) -> None:
    """Setup direnv configuration by copying template if .envrc doesn't exist.

    Args:
        workspace_root: Project root directory

    Note:
        Creates .envrc from .envrc.template if it doesn't exist.
        Provides instructions for activating direnv.
    """
    envrc_path = workspace_root / ".envrc"
    template_path = workspace_root / ".envrc.template"

    if envrc_path.exists():
        logger.info("ℹ️  .envrc já existe, mantendo configuração atual.")
        return

    if not template_path.exists():
        logger.warning(
            "⚠️  .envrc.template não encontrado. Pulando configuração do direnv.",
        )
        return

    try:
        # Copy template to .envrc
        shutil.copy2(template_path, envrc_path)
        logger.info("✅ Direnv configurado! Execute 'direnv allow' para ativar.")
    except Exception as e:
        logger.warning("⚠️  Não foi possível copiar .envrc.template: %s", e)


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

    👉 OU ative automaticamente com direnv:
       direnv allow

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

    Note:
        # TODO(P02): Review for atomic writes - Currently no direct file writes
        # This function only calls subprocess operations, no critical file I/O
    """
    try:
        # ========== STEP 1: Install project + pip-tools ==========
        logger.info("Step 1/3: Installing project and pip-tools...")
        result1 = subprocess.run(  # nosec # noqa: subprocess
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
            cwd=workspace_root,
            shell=False,  # Security: prevent shell injection
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug("Output pip install: %s", result1.stdout.strip())

        # ========== STEP 2: Compile dependencies (ATOMIC) ==========
        logger.info("Step 2/3: Compiling dependencies with pip-compile...")

        # Try to find pip-compile in PATH
        pip_compile_path = shutil.which("pip-compile")

        if not pip_compile_path:
            # Fallback: execute pip-compile via Python module
            logger.warning(
                "pip-compile not found in PATH. Using module fallback.",
            )
            # Create a temporary wrapper script for module execution
            pip_compile_cmd = [
                sys.executable,
                "-m",
                "piptools",
                "compile",
            ]
            # Use safe_pip_compile by manually constructing the command
            # This is a workaround since safe_pip expects an executable path
            try:
                result2 = subprocess.run(  # nosec # noqa: subprocess
                    pip_compile_cmd
                    + [
                        "--output-file",
                        str(workspace_root / "requirements" / "dev.txt.tmp"),
                        str(workspace_root / "requirements" / "dev.in"),
                    ],
                    cwd=workspace_root,
                    shell=False,  # Security: prevent shell injection
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Manual atomic replace for fallback mode
                tmp_file = workspace_root / "requirements" / "dev.txt.tmp"
                target_file = workspace_root / "requirements" / "dev.txt"
                if tmp_file.exists():
                    tmp_file.replace(target_file)
            except subprocess.CalledProcessError as e:
                logger.error("pip-compile fallback failed: %s", e)
                raise
        else:
            # Use pip-compile from PATH with atomic writes
            logger.debug("Using pip-compile: %s", pip_compile_path)
            result2 = safe_pip_compile(
                input_file=workspace_root / "requirements" / "dev.in",
                output_file=workspace_root / "requirements" / "dev.txt",
                pip_compile_path=pip_compile_path,
                workspace_root=workspace_root,
            )
        logger.debug("Output pip-compile: %s", result2.stdout.strip())

        # ========== STEP 3: Install pinned dependencies ==========
        logger.info("Step 3/3: Installing pinned dependencies...")
        result3 = subprocess.run(  # nosec # noqa: subprocess
            [sys.executable, "-m", "pip", "install", "-r", "requirements/dev.txt"],
            cwd=workspace_root,
            shell=False,  # Security: prevent shell injection
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug("Output pip install -r: %s", result3.stdout.strip())

        # ========== STEP 4: Setup direnv configuration ==========
        logger.info("Step 4/4: Setting up direnv configuration...")
        _setup_direnv(workspace_root)

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
    # Banner de inicialização
    print_startup_banner(
        tool_name="Dev Environment Installer",
        version="2.0.0",
        description="Development Dependencies Installation and Setup",
        script_path=Path(__file__),
    )

    # Detect workspace root (parent directory of scripts/)
    workspace_root = Path(__file__).parent.parent.parent.resolve()

    logger.info("Starting development environment installation")
    logger.info("Workspace: %s", workspace_root)
    logger.info("Python: %s", sys.executable)

    return install_dev_environment(workspace_root)


if __name__ == "__main__":
    sys.exit(main())
