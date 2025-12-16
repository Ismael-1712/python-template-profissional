"""Testes de governança estrutural do projeto.

Este módulo implementa verificações automáticas para garantir que a estrutura
de pastas do projeto siga os padrões definidos. Previne:
- Arquivos Python (.py) dentro de docs/
- Diretórios de teste aninhados indevidamente

Author: SRE Team
License: MIT
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


def test_no_python_files_in_docs() -> None:
    """Verifica que não há arquivos .py dentro de docs/.

    Arquivos Python devem estar em src/, scripts/ ou tests/.
    A pasta docs/ é exclusiva para documentação em Markdown.
    """
    docs_dir = PROJECT_ROOT / "docs"
    if not docs_dir.exists():
        pytest.skip("Diretório docs/ não existe")

    python_files: list[Path] = list(docs_dir.rglob("*.py"))

    if python_files:
        files_list = "\n".join(
            f"  - {f.relative_to(PROJECT_ROOT)}" for f in python_files
        )
        pytest.fail(
            f"❌ Encontrados {len(python_files)} arquivo(s) "
            f"Python em docs/:\n{files_list}\n\n"
            "📋 AÇÃO REQUERIDA:\n"
            "  - Mova scripts executáveis para scripts/\n"
            "  - Mova código-fonte para src/\n"
            "  - Converta documentação técnica para Markdown\n",
        )


def test_no_nested_test_directories() -> None:
    """Verifica que não há diretórios tests/ aninhados.

    O único diretório de testes válido é tests/ na raiz.
    """
    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        pytest.skip("Diretório tests/ não existe")

    # Procura por qualquer subdiretório chamado "tests"
    nested_test_dirs: list[Path] = [p for p in tests_dir.rglob("tests") if p.is_dir()]

    if nested_test_dirs:
        dirs_list = "\n".join(
            f"  - {d.relative_to(PROJECT_ROOT)}" for d in nested_test_dirs
        )
        pytest.fail(
            f"❌ Encontrados {len(nested_test_dirs)} diretório(s) "
            f"de teste aninhado(s):\n{dirs_list}\n\n"
            "📋 AÇÃO REQUERIDA:\n"
            "  - Mova arquivos de teste para tests/ raiz\n"
            "  - Remova diretórios vazios com 'rmdir <dir>'\n",
        )


def test_no_duplicate_test_prefixes() -> None:
    """Verifica que não há diretórios iniciando com 'test_' fora de tests/.

    Esta convenção evita confusão com módulos de teste.
    """
    src_dir = PROJECT_ROOT / "src"
    scripts_dir = PROJECT_ROOT / "scripts"

    suspicious_dirs: list[Path] = []

    for base_dir in [src_dir, scripts_dir]:
        if not base_dir.exists():
            continue

        suspicious_dirs.extend(p for p in base_dir.rglob("test_*") if p.is_dir())

    if suspicious_dirs:
        dirs_list = "\n".join(
            f"  - {d.relative_to(PROJECT_ROOT)}" for d in suspicious_dirs
        )
        pytest.fail(
            f"⚠️  Encontrados {len(suspicious_dirs)} diretório(s) "
            f"com nome suspeito:\n{dirs_list}\n\n"
            "📋 SUGESTÃO:\n"
            "  - Renomeie para evitar confusão com módulos de teste\n"
            "  - Use prefixos como 'testing_utils' ao invés de 'test_utils'\n",
        )
