#!/usr/bin/env python3
"""Script de Instalação de Ambiente de Desenvolvimento.

Realiza instalação completa do ambiente de desenvolvimento com pinning de
dependências usando pip-tools.

Sequência de Operações:
1. Instala o projeto em modo editável com dependências dev
2. Compila dependências com pip-compile (com fallback)
3. Instala dependências pinned do requirements/dev.txt

Uso:
    python3 scripts/install_dev.py
    ./scripts/install_dev.py  # Se tiver permissão de execução
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _display_success_panel() -> None:
    """Exibe painel formatado de sucesso com próximos passos."""
    panel = """
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        ✅  AMBIENTE CONFIGURADO COM SUCESSO!                  ║
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
"""
    print(panel)


def install_dev_environment(workspace_root: Path) -> int:
    """Executa sequência completa de instalação do ambiente de desenvolvimento.

    Args:
        workspace_root: Diretório raiz do projeto

    Returns:
        Código de saída (0 = sucesso, 1 = erro)

    Raises:
        subprocess.CalledProcessError: Se algum passo da instalação falhar
    """
    try:
        # ========== PASSO 1: Instalar projeto + pip-tools ==========
        logger.info("Passo 1/3: Instalando projeto e pip-tools...")
        result1 = subprocess.run(  # noqa: subprocess
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug("Saída pip install: %s", result1.stdout.strip())

        # ========== PASSO 2: Compilar dependências ==========
        logger.info("Passo 2/3: Compilando dependências com pip-compile...")

        # Tentar encontrar pip-compile no PATH
        pip_compile_path = shutil.which("pip-compile")

        if not pip_compile_path:
            # Fallback: executar pip-compile via módulo Python
            logger.warning(
                "pip-compile não encontrado no PATH. Usando fallback via módulo.",
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
            # Usar pip-compile do PATH
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
        logger.debug("Saída pip-compile: %s", result2.stdout.strip())

        # ========== PASSO 3: Instalar dependências pinned ==========
        logger.info("Passo 3/3: Instalando dependências pinned...")
        result3 = subprocess.run(  # noqa: subprocess
            [sys.executable, "-m", "pip", "install", "-r", "requirements/dev.txt"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug("Saída pip install -r: %s", result3.stdout.strip())

        # ========== SUCESSO: PAINEL FORMATADO ==========
        _display_success_panel()
        return 0

    except subprocess.CalledProcessError as e:
        logger.error("❌ Instalação falhou com código de saída %s", e.returncode)
        logger.error("Comando que falhou: %s", " ".join(e.cmd))
        if e.stderr:
            logger.error("Erro: %s", e.stderr)
        return 1
    except Exception as e:
        logger.error("❌ Erro inesperado: %s", e)
        return 1


def main() -> int:
    """Entrypoint principal do script."""
    # Detectar workspace root (diretório pai do scripts/)
    workspace_root = Path(__file__).parent.parent.resolve()

    logger.info("Iniciando instalação do ambiente de desenvolvimento")
    logger.info("Workspace: %s", workspace_root)
    logger.info("Python: %s", sys.executable)

    return install_dev_environment(workspace_root)


if __name__ == "__main__":
    sys.exit(main())
