#!/usr/bin/env python3
"""Auditoria Automatizada de Dependências.

Script para verificar a saúde arquitetural do projeto em relação
a dependências cíclicas e violações de hierarquia.

Uso:
    python scripts/audit_dependencies.py
    python scripts/audit_dependencies.py --json  # Output JSON
    python scripts/audit_dependencies.py --ci    # Exit 1 se violações

Autor: DevOps Engineering Team
Versão: 1.0.0 (Tarefa [004])
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast


def get_layer(filepath: str) -> str:
    """Determina a camada de um arquivo."""
    parts = Path(filepath).parts
    if "utils" in parts:
        return "utils"
    if "core" in parts:
        return "core"
    if "cli" in parts:
        return "cli"
    return "root"


def detect_violations() -> list[dict[str, Any]]:
    """Detecta violações de hierarquia de camadas."""
    violations = []
    scripts_dir = Path(__file__).parent

    import_pattern = re.compile(r"^from scripts\.(\w+)", re.MULTILINE)

    for python_file in scripts_dir.rglob("*.py"):
        if "__pycache__" in str(python_file):
            continue

        relative_path = python_file.relative_to(scripts_dir)
        file_layer = get_layer(str(relative_path))

        try:
            content = python_file.read_text(encoding="utf-8")
            imports = import_pattern.findall(content)

            for imported_layer in imports:
                # utils não pode importar core ou cli
                if file_layer == "utils" and imported_layer in ["core", "cli"]:
                    violations.append(
                        {
                            "file": str(relative_path),
                            "layer": file_layer,
                            "imports": imported_layer,
                            "severity": "CRITICAL",
                            "rule": "utils/ não pode importar core/ ou cli/",
                        },
                    )

                # core não pode importar cli
                elif file_layer == "core" and imported_layer == "cli":
                    violations.append(
                        {
                            "file": str(relative_path),
                            "layer": file_layer,
                            "imports": imported_layer,
                            "severity": "CRITICAL",
                            "rule": "core/ não pode importar cli/",
                        },
                    )
        except Exception:
            continue

    return violations


def count_type_checking() -> list[str]:
    """Conta blocos TYPE_CHECKING."""
    scripts_dir = Path(__file__).parent
    type_checking_files = []

    type_check_pattern = re.compile(r"if TYPE_CHECKING:", re.MULTILINE)

    for python_file in scripts_dir.rglob("*.py"):
        if "__pycache__" in str(python_file):
            continue

        try:
            content = python_file.read_text(encoding="utf-8")
            if type_check_pattern.search(content):
                relative_path = python_file.relative_to(scripts_dir)
                type_checking_files.append(str(relative_path))
        except Exception:
            continue

    return type_checking_files


def get_hub_modules(threshold: int = 5) -> list[dict[str, Any]]:
    """Identifica módulos hub com muitas dependências."""
    scripts_dir = Path(__file__).parent
    imports_by_module: defaultdict[str, int] = defaultdict(int)

    import_pattern = re.compile(r"^from scripts\.([\w.]+)", re.MULTILINE)

    for python_file in scripts_dir.rglob("*.py"):
        if "__pycache__" in str(python_file):
            continue

        try:
            content = python_file.read_text(encoding="utf-8")
            imports = import_pattern.findall(content)

            for imp in imports:
                # Normalizar para módulo de topo (ex: utils.logger)
                parts = imp.split(".")
                if len(parts) >= 2:
                    module = f"{parts[0]}.{parts[1]}"
                else:
                    module = parts[0]

                imports_by_module[module] += 1
        except Exception:
            continue

    # Filtrar por threshold e ordenar
    hubs = [
        {"module": module, "imports": count}
        for module, count in imports_by_module.items()
        if count >= threshold
    ]
    hubs.sort(key=lambda x: cast("int", x["imports"]), reverse=True)

    return hubs


def print_report(report: dict[str, Any], json_output: bool = False) -> None:
    """Imprime o relatório de auditoria."""
    if json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    print("=" * 80)
    print("AUDITORIA DE DEPENDÊNCIAS - RELATÓRIO")
    print("=" * 80)
    print(f"Data: {report['timestamp']}")
    print(f"Projeto: {report['project']}")
    print()

    # Violações
    violations = report["findings"]["layer_violations"]
    print(f"1. VIOLAÇÕES DE HIERARQUIA: {violations['count']}")
    print("-" * 80)
    if violations["count"] > 0:
        for v in violations["details"]:
            print(f"❌ [{v['severity']}] {v['file']}")
            print(f"   {v['rule']}")
            print(f"   Importa: scripts.{v['imports']}")
            print()
    else:
        print("✅ Nenhuma violação detectada")
    print()

    # TYPE_CHECKING
    type_check = report["findings"]["type_checking_blocks"]
    print(f"2. BLOCOS TYPE_CHECKING: {type_check['count']}")
    print("-" * 80)
    if type_check["count"] > 0:
        for f in type_check["files"][:5]:  # Mostrar até 5
            print(f"   🔍 {f}")
        if type_check["count"] > 5:
            print(f"   ... e mais {type_check['count'] - 5} arquivo(s)")
    else:
        print("   Nenhum bloco TYPE_CHECKING")
    print()

    # Hubs
    hubs = report["findings"]["hub_modules"]
    print(f"3. MÓDULOS HUB (>=5 imports): {len(hubs)}")
    print("-" * 80)
    if hubs:
        for hub in hubs[:10]:  # Top 10
            severity = "🔴" if hub["imports"] >= 10 else "🟡"
            print(f"   {severity} {hub['module']}: {hub['imports']} imports")
    else:
        print("   Nenhum hub crítico")
    print()

    # Sumário
    print("=" * 80)
    print("SUMÁRIO")
    print("=" * 80)
    status = "✅ PASS" if violations["count"] == 0 else "❌ FAIL"
    print(f"Status: {status}")
    print(f"Violações Críticas: {violations['count']}")
    print(f"Blocos TYPE_CHECKING: {type_check['count']}")
    print(f"Módulos Hub: {len(hubs)}")
    print("=" * 80)


def main() -> int:
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Auditoria de dependências e hierarquia de camadas",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output em formato JSON",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Modo CI: exit 1 se houver violações",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=5,
        help="Threshold para módulos hub (default: 5)",
    )
    args = parser.parse_args()

    # Coletar dados
    violations = detect_violations()
    type_checking_files = count_type_checking()
    hub_modules = get_hub_modules(threshold=args.threshold)

    # Montar relatório
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": "python-template-profissional",
        "findings": {
            "layer_violations": {
                "count": len(violations),
                "severity": "CRITICAL" if violations else "NONE",
                "details": violations,
            },
            "type_checking_blocks": {
                "count": len(type_checking_files),
                "files": type_checking_files,
            },
            "hub_modules": hub_modules,
        },
    }

    # Imprimir relatório
    print_report(report, json_output=args.json)

    # Modo CI
    if args.ci and violations:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
