#!/usr/bin/env python3
"""Exemplo de uso do Visibility Guardian Scanner.

Demonstra como usar o scanner para detectar configurações no projeto.
"""

from __future__ import annotations

from pathlib import Path

from scripts.core.guardian.models import ConfigFinding
from scripts.core.guardian.scanner import ConfigScanner


def main() -> None:
    """Executa exemplo de scan do projeto."""
    print("=== Visibility Guardian Scanner - Exemplo de Uso ===\n")

    # Inicializa o scanner
    scanner = ConfigScanner()

    # Define o diretório raiz do projeto
    project_root = Path(__file__).parent.parent

    print(f"Escaneando projeto: {project_root}\n")

    # Escaneia apenas o diretório scripts/ para o exemplo
    scripts_dir = project_root / "scripts"
    result = scanner.scan_project(scripts_dir, pattern="**/*.py")

    # Exibe resultados
    print("=" * 70)
    print(result.summary())
    print("=" * 70)
    print()

    if result.has_errors():
        print("⚠️  Erros encontrados durante o scan:")
        for error in result.errors:
            print(f"  - {error}")
        print()

    # Agrupa por arquivo
    findings_by_file: dict[Path, list[ConfigFinding]] = {}
    for finding in result.findings:
        if finding.source_file not in findings_by_file:
            findings_by_file[finding.source_file] = []
        findings_by_file[finding.source_file].append(finding)

    # Exibe configurações encontradas
    print(f"\n📋 Configurações encontradas ({len(result.findings)}):\n")

    for file_path, findings in sorted(findings_by_file.items()):
        rel_path = file_path.relative_to(project_root)
        print(f"\n📁 {rel_path}")
        print("-" * 70)

        for finding in findings:
            required_mark = "🔴" if finding.required else "🟢"
            default_info = (
                f" [default: {finding.default_value}]" if finding.default_value else ""
            )
            context_info = f" (in {finding.context})" if finding.context else ""

            print(
                f"  {required_mark} {finding.key}{default_info} "
                f"@ linha {finding.line_number}{context_info}",
            )

    # Estatísticas
    print("\n" + "=" * 70)
    print("📊 Estatísticas:")
    print("=" * 70)
    print(f"  Total de variáveis de ambiente: {len(result.env_vars)}")

    # Calcula estatísticas
    required_count = sum(1 for f in result.findings if f.required)
    optional_count = sum(1 for f in result.findings if not f.required)

    print(f"  Variáveis obrigatórias (sem default): {required_count}")
    print(f"  Variáveis opcionais (com default): {optional_count}")
    print(f"  Arquivos escaneados: {result.files_scanned}")
    print(f"  Tempo de scan: {result.scan_duration_ms:.2f}ms")

    # Alerta sobre configurações órfãs
    print("\n" + "=" * 70)
    print("⚠️  Próximo passo: Validar documentação")
    print("=" * 70)
    print(
        "\nO Visibility Guardian pode verificar se todas essas "
        "configurações estão\ndocumentadas em docs/ e README.md.",
    )
    print("\nComandos futuros:")
    print("  - cortex guardian check    # Valida documentação")
    print("  - cortex guardian report   # Gera relatório completo")


if __name__ == "__main__":
    main()
