"""Visibility Guardian - Scanner AST para configurações não documentadas.

Este módulo implementa um scanner AST que identifica:
- Variáveis de ambiente (os.getenv, os.environ)
- Argumentos CLI (typer, argparse)
- Feature flags e outras configurações

Garante que toda configuração no código tenha documentação correspondente.
"""

from __future__ import annotations

from scripts.core.guardian.models import ConfigFinding, ScanResult
from scripts.core.guardian.scanner import ConfigScanner

__all__ = [
    "ConfigFinding",
    "ConfigScanner",
    "ScanResult",
]
