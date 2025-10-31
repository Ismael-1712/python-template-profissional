#!/usr/bin/env python3
"""
Pre-commit Hook Integration Script

This script integrates the code auditor with git pre-commit hooks
to ensure security standards are met before every commit.

Usage:
    # Install as pre-commit hook
    python3 scripts/pre_commit_audit.py install

    # Manual pre-commit check (this is what the hook will run)
    python3 scripts/pre_commit_audit.py
"""

import logging
import subprocess
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def install_pre_commit_hook() -> bool:
    """Install the auditor as a git pre-commit hook."""
    try:
        git_dir = Path(".git")
        if not git_dir.exists():
            logger.error("Not in a git repository")
            return False

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        pre_commit_hook = hooks_dir / "pre-commit"

        # --- INÍCIO DA CORREÇÃO ---
        # 1. Obter o caminho absoluto para o interpretador Python em execução
        python_executable = sys.executable

        # 2. Obter o caminho para este script (assumindo que está em 'scripts/')
        # Usamos Path(__file__) para robustez, caso o script mude de nome
        script_path = Path(__file__).name

        # 3. Criar um hook robusto que chama este script
        hook_content = f'''#!/bin/bash
# Auto-generated pre-commit hook for code security audit

echo "🔍 Running security audit before commit..."

# Chama o script de auditoria principal usando o interpretador Python correto
# Isso executará o bloco 'else' da função main() deste script.
"{python_executable}" "scripts/{script_path}"

RESULT=$?
if [ $RESULT -ne 0 ]; then
    # A mensagem de erro já foi impressa pelo script Python
    exit 1
fi

# A mensagem de sucesso é impressa pelo script Python, mas podemos adicionar uma aqui.
# A função 'run_pre_commit_audit' já imprime "✅ Pre-commit audit passed"
'''
        # --- FIM DA CORREÇÃO ---

        with open(pre_commit_hook, "w") as f:
            f.write(hook_content)

        # Make executable
        pre_commit_hook.chmod(0o755)

        logger.info(f"✅ Pre-commit hook installed at {pre_commit_hook}")
        return True

    except Exception as e:
        logger.error(f"Failed to install pre-commit hook: {e}")
        return False


def run_pre_commit_audit() -> bool:
    """Run the audit as part of pre-commit check."""
    try:
        logger.info("🔍 Running pre-commit security audit...")

        # Get list of staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.warning("Could not get staged files, running full audit")
        else:
            staged_files = result.stdout.strip().split("\n")
            python_files = [f for f in staged_files if f.endswith(".py")]

            if not python_files:
                logger.info("✅ No Python files staged, skipping audit")
                return True

            logger.info(f"📄 Auditing {len(python_files)} staged Python files")

        # Run the auditor
        # Esta parte já estava correta, usando sys.executable
        audit_result = subprocess.run([
            sys.executable,
            "scripts/code_audit.py",
            "--config", "scripts/audit_config.yaml", # O script de auditoria principal
            "--fail-on", "HIGH",
            "--quiet"
        ])

        if audit_result.returncode == 0:
            logger.info("✅ Pre-commit audit passed")
            return True
        else:
            logger.error("❌ Pre-commit audit failed")
            logger.info("💡 Run 'python3 scripts/code_audit.py' for detailed report")
            return False

    except Exception as e:
        logger.error(f"Pre-commit audit error: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        success = install_pre_commit_hook()
        sys.exit(0 if success else 1)
    else:
        success = run_pre_commit_audit()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
