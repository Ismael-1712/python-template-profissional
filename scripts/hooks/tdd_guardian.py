#!/usr/bin/env python3
"""TDD Guardian - Garante que código novo tenha testes correspondentes.

Este script é executado como um hook de pre-commit e valida que todos os
arquivos Python em diretórios monitorados tenham seus respectivos testes.

Suporta múltiplos diretórios e modos de operação (strict/warn-only).

Uso:
    # Modo padrão (strict, apenas src/)
    python scripts/hooks/tdd_guardian.py file1.py file2.py ...

    # Monitorar múltiplos diretórios
    python scripts/hooks/tdd_guardian.py --dirs src scripts -- file1.py file2.py

    # Modo warn-only (não bloqueia commit)
    python scripts/hooks/tdd_guardian.py --warn-only file1.py file2.py

Exit codes:
    0: Todos os arquivos possuem testes correspondentes (ou modo warn-only)
    1: Um ou mais arquivos não possuem testes (apenas em strict mode)
"""

import argparse
import sys
from pathlib import Path


class TDDGuardian:
    """Guardião que impõe a presença de testes para código novo.

    Responsabilidades:
    - Mapear arquivos de diretórios monitorados para tests/
    - Ignorar arquivos especiais (__init__.py)
    - Ignorar arquivos fora de diretórios monitorados
    - Validar existência de testes
    - Suportar modo strict (bloqueia) ou warn-only (apenas avisa)
    """

    def __init__(
        self,
        project_root: Path | None = None,
        monitored_dirs: list[str] | None = None,
        strict: bool = True,
    ) -> None:
        """Inicializa o TDD Guardian.

        Args:
            project_root: Raiz do projeto. Se None, usa o diretório atual.
            monitored_dirs: Lista de diretórios a monitorar (ex: ['src', 'scripts']).
                          Padrão: ['src']
            strict: Se True, bloqueia commit quando testes faltam.
                   Se False, apenas emite warnings (modo permissivo).
        """
        self.project_root = project_root or Path.cwd()
        self.monitored_dirs = monitored_dirs or ["src"]
        self.strict = strict

    def should_ignore(self, file_path: Path) -> bool:
        """Determina se um arquivo deve ser ignorado na validação.

        Args:
            file_path: Caminho do arquivo a verificar

        Returns:
            True se o arquivo deve ser ignorado, False caso contrário

        Regras de ignoramento:
        - Arquivos fora dos diretórios monitorados
        - Arquivos __init__.py
        - Arquivos não-Python (.md, .txt, etc)
        """
        # Normaliza o caminho para Path
        path = Path(file_path)

        # Ignora arquivos não-Python
        if path.suffix != ".py":
            return True

        # Ignora __init__.py
        if path.name == "__init__.py":
            return True

        # Ignora arquivos fora dos diretórios monitorados
        try:
            # Verifica se algum diretório monitorado está no caminho
            parts = path.parts
            if not any(monitored_dir in parts for monitored_dir in self.monitored_dirs):
                return True
        except ValueError:
            # Caminho relativo que não contém nenhum diretório monitorado
            return True

        return False

    def get_test_path(self, source_file: Path) -> Path:
        """Mapeia um arquivo fonte para seu arquivo de teste correspondente.

        Args:
            source_file: Caminho do arquivo fonte (ex: src/main.py ou scripts/deploy.py)

        Returns:
            Caminho do teste correspondente
            (ex: tests/test_main.py ou tests/scripts/test_deploy.py)

        Exemplos:
            src/main.py          -> tests/test_main.py
            src/core/utils.py    -> tests/core/test_utils.py
            scripts/deploy.py    -> tests/scripts/test_deploy.py
            scripts/cli/doctor.py -> tests/scripts/cli/test_doctor.py
        """
        # Normaliza o caminho
        path = Path(source_file)
        parts = list(path.parts)

        # Identifica qual diretório monitorado está presente
        monitored_dir: str | None = None
        dir_index = -1

        for i, part in enumerate(parts):
            if part in self.monitored_dirs:
                monitored_dir = part
                dir_index = i
                break

        # Se não encontrou diretório monitorado, assume primeiro componente
        if monitored_dir is None:
            # Fallback: assume primeiro componente como diretório
            monitored_dir = parts[0] if parts else "src"
            relative_parts = parts
        else:
            # Pega todos os componentes após o diretório monitorado
            relative_parts = parts[dir_index + 1 :]

        # Constrói o caminho do teste
        # Se for src/, comportamento original (tests/...)
        # Se for scripts/, adiciona subdiretório (tests/scripts/...)
        if monitored_dir == "src":
            # src/core/utils.py -> tests/core/test_utils.py
            if len(relative_parts) > 1:
                test_parts = (
                    ["tests"] + relative_parts[:-1] + [f"test_{relative_parts[-1]}"]
                )
            else:
                # src/main.py -> tests/test_main.py
                test_parts = ["tests", f"test_{relative_parts[0]}"]
        # scripts/deploy.py -> tests/scripts/test_deploy.py
        # scripts/cli/doctor.py -> tests/scripts/cli/test_doctor.py
        elif len(relative_parts) > 1:
            test_parts = (
                ["tests", monitored_dir]
                + relative_parts[:-1]
                + [f"test_{relative_parts[-1]}"]
            )
        else:
            # scripts/deploy.py -> tests/scripts/test_deploy.py
            test_parts = ["tests", monitored_dir, f"test_{relative_parts[0]}"]

        return Path(*test_parts)

    def validate(self, files: list[Path]) -> tuple[bool, list[Path]]:
        """Valida se todos os arquivos possuem testes correspondentes.

        Args:
            files: Lista de arquivos a validar

        Returns:
            Tupla (sucesso, arquivos_sem_teste)
            - sucesso: True se todos os testes existem (ou warn-only),
                      False caso contrário
            - arquivos_sem_teste: Lista de arquivos que não possuem teste
        """
        missing_tests: list[Path] = []

        for file_path in files:
            # Ignora arquivos que não requerem testes
            if self.should_ignore(file_path):
                continue

            # Obtém o caminho do teste esperado
            test_path = self.get_test_path(file_path)

            # Verifica se o teste existe
            # Resolve o caminho relativo ao project_root
            full_test_path = self.project_root / test_path

            if not full_test_path.exists():
                missing_tests.append(file_path)

        # Em modo warn-only, sempre retorna sucesso (mas registra missing)
        if not self.strict:
            return True, missing_tests

        # Em modo strict, bloqueia se houver testes faltando
        success = len(missing_tests) == 0
        return success, missing_tests

    def run(self, files: list[str]) -> int:
        """Executa a validação e imprime resultados.

        Args:
            files: Lista de caminhos de arquivos (strings)

        Returns:
            Exit code (0 = sucesso, 1 = falha)
        """
        # Converte strings para Path
        file_paths = [Path(f) for f in files]

        # Executa validação
        success, missing = self.validate(file_paths)

        if not success or (self.strict is False and len(missing) > 0):
            # Determina o tipo de mensagem (erro ou warning)
            if self.strict:
                icon = "❌"
                level = "ERRO"
                color = "\033[91m"  # Vermelho
            else:
                icon = "⚠️"
                level = "AVISO"
                color = "\033[93m"  # Amarelo

            reset_color = "\033[0m"

            # Imprime cabeçalho
            dirs_str = ", ".join(self.monitored_dirs)
            print(
                f"{color}{icon} TDD Guardian [{level}]: "
                f"Arquivos sem testes detectados!{reset_color}\n",
            )
            print(f"Os seguintes arquivos em {dirs_str} não possuem testes:\n")

            # Lista arquivos faltantes
            for file_path in missing:
                test_path = self.get_test_path(file_path)
                print(f"  {icon}  {file_path}")
                print(f"      Esperado: {test_path}\n")

            # Dica de ação
            if self.strict:
                print("💡 Dica: Crie os testes antes de fazer commit (TDD).")
                print(
                    f"   Cada arquivo em {dirs_str} deve ter um teste "
                    f"correspondente em tests/.\n",
                )
                return 1
            print(
                "💡 Modo WARN-ONLY ativado: Commit permitido, "
                "mas considere adicionar testes.",
            )
            print(
                f"   Recomendação: Adicione testes para {dirs_str} quando possível.\n",
            )
            return 0

        # Validação passou
        return 0


def main() -> int:
    """Ponto de entrada do script.

    Returns:
        Exit code (0 = sucesso, 1 = falha)
    """
    # Configuração de argumentos CLI
    parser = argparse.ArgumentParser(
        description=(
            "TDD Guardian - Garante que código novo tenha testes correspondentes"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Modo padrão (strict, apenas src/)
  %(prog)s file1.py file2.py

  # Monitorar múltiplos diretórios
  %(prog)s --dirs src scripts -- file1.py file2.py

  # Modo warn-only (não bloqueia commit)
  %(prog)s --warn-only file1.py file2.py

  # Combinar opções
  %(prog)s --dirs src scripts --warn-only -- file1.py file2.py
        """,
    )

    parser.add_argument(
        "--dirs",
        nargs="+",
        default=["src"],
        help="Diretórios a monitorar (padrão: src)",
    )

    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Modo permissivo: emite avisos mas não bloqueia commits",
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="Arquivos a validar",
    )

    args = parser.parse_args()

    # Se nenhum arquivo fornecido, considera sucesso
    if not args.files:
        return 0

    # Cria instância do guardian com configuração
    guardian = TDDGuardian(
        monitored_dirs=args.dirs,
        strict=not args.warn_only,
    )

    return guardian.run(args.files)


if __name__ == "__main__":
    sys.exit(main())
