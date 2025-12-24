#!/usr/bin/env python3
"""Script de migração: doc_type/doc_status -> type/status.

Este script varre todos os arquivos Markdown do projeto e migra
automaticamente o padrão antigo de metadados para o novo padrão.

Migração:
- doc_type -> type
- doc_status -> status

Uso:
    python scripts/maintenance/migrate_frontmatter.py [--dry-run]
"""

import re
import sys
from pathlib import Path
from typing import Any

import yaml

# Diretórios que devem ser ignorados na varredura
EXCLUDED_DIRS = {
    ".venv",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "dist",
    "build",
    ".tox",
    "node_modules",
    ".cortex",
    "locales",
}


def extract_frontmatter(content: str) -> tuple[dict[str, Any] | None, str, str]:
    """Extrai o frontmatter YAML de um arquivo Markdown.

    Args:
        content: Conteúdo completo do arquivo Markdown.

    Returns:
        Tupla contendo:
        - metadata: Dicionário com metadados (ou None se não houver frontmatter)
        - frontmatter_raw: String do frontmatter original (sem delimitadores)
        - body: Resto do conteúdo após o frontmatter
    """
    frontmatter_pattern = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n",
        re.DOTALL | re.MULTILINE,
    )
    match = frontmatter_pattern.match(content)

    if not match:
        return None, "", content

    frontmatter_raw = match.group(1)
    body = content[match.end() :]

    try:
        metadata = yaml.safe_load(frontmatter_raw)
        if not isinstance(metadata, dict):
            return None, frontmatter_raw, body
        return metadata, frontmatter_raw, body
    except yaml.YAMLError:
        return None, frontmatter_raw, body


def migrate_metadata(metadata: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Migra metadados do padrão antigo para o novo.

    Args:
        metadata: Dicionário de metadados original.

    Returns:
        Tupla contendo:
        - metadata: Dicionário migrado
        - changed: Flag indicando se houve mudança
    """
    changed = False
    migrated = metadata.copy()

    # Migrar doc_type -> type
    if "doc_type" in migrated and "type" not in migrated:
        migrated["type"] = migrated.pop("doc_type")
        changed = True

    # Migrar doc_status -> status
    if "doc_status" in migrated and "status" not in migrated:
        migrated["status"] = migrated.pop("doc_status")
        changed = True

    return migrated, changed


def reconstruct_frontmatter(metadata: dict[str, Any]) -> str:
    """Reconstrói o frontmatter YAML a partir do dicionário de metadados.

    Args:
        metadata: Dicionário de metadados.

    Returns:
        String do frontmatter formatado (sem delimitadores ---)
    """
    # Usar dump com configurações para manter legibilidade
    return yaml.dump(
        metadata,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    ).strip()


def migrate_file(file_path: Path, dry_run: bool = False) -> bool:
    """Migra um arquivo Markdown do padrão antigo para o novo.

    Args:
        file_path: Caminho do arquivo a migrar.
        dry_run: Se True, apenas simula a migração sem escrever.

    Returns:
        True se o arquivo foi migrado (ou seria migrado em dry-run).
    """
    content = file_path.read_text(encoding="utf-8")
    metadata, frontmatter_raw, body = extract_frontmatter(content)

    if metadata is None:
        return False

    migrated_metadata, changed = migrate_metadata(metadata)

    if not changed:
        return False

    # Reconstruir arquivo com metadados migrados
    new_frontmatter = reconstruct_frontmatter(migrated_metadata)
    new_content = f"---\n{new_frontmatter}\n---\n{body}"

    if not dry_run:
        file_path.write_text(new_content, encoding="utf-8")

    return True


def main() -> int:
    """Função principal do script de migração."""
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 Modo DRY-RUN ativado (nenhum arquivo será modificado)\n")
    else:
        print("🚀 Iniciando migração de metadados...\n")

    project_root = Path()
    all_md_files = list(project_root.rglob("*.md"))

    # Filtrar arquivos que estão em diretórios excluídos
    filtered_files = []
    for md_file in all_md_files:
        parts = md_file.parts
        if not any(excluded_dir in parts for excluded_dir in EXCLUDED_DIRS):
            filtered_files.append(md_file)

    # Executar migração
    migrated_files = []
    for md_file in filtered_files:
        if migrate_file(md_file, dry_run=dry_run):
            migrated_files.append(md_file)
            status = "[DRY-RUN]" if dry_run else "[MIGRADO]"
            print(f"{status} {md_file}")

    # Relatório final
    print(f"\n{'=' * 60}")
    if dry_run:
        print(
            f"✅ {len(migrated_files)} arquivo(s) SERIAM migrados "
            f"(de {len(filtered_files)} analisados)",
        )
        print("\nExecute sem --dry-run para aplicar as mudanças.")
    else:
        print(
            f"✅ {len(migrated_files)} arquivo(s) migrados com sucesso "
            f"(de {len(filtered_files)} analisados)",
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
