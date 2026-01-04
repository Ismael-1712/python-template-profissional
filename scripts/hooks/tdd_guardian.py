#!/usr/bin/env python3
"""TDD Guardian - Garante que código novo tenha testes correspondentes.

Este script é executado como um hook de pre-commit e valida que todos os
arquivos Python em src/ tenham seus respectivos testes em tests/.

Uso:
    python scripts/hooks/tdd_guardian.py file1.py file2.py ...

Exit codes:
    0: Todos os arquivos possuem testes correspondentes
    1: Um ou mais arquivos não possuem testes
"""

import sys
from pathlib import Path


class TDDGuardian:
    """Guardião que impõe a presença de testes para código novo.

    Responsabilidades:
    - Mapear arquivos src/*.py para tests/test_*.py
    - Ignorar arquivos especiais (__init__.py)
    - Ignorar arquivos fora de src/
    - Validar existência de testes
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Inicializa o TDD Guardian.

        Args:
            project_root: Raiz do projeto. Se None, usa o diretório atual.
        """
        self.project_root = project_root or Path.cwd()

    def should_ignore(self, file_path: Path) -> bool:
        """Determina se um arquivo deve ser ignorado na validação.

        Args:
            file_path: Caminho do arquivo a verificar

        Returns:
            True se o arquivo deve ser ignorado, False caso contrário

        Regras de ignoramento:
        - Arquivos fora de src/
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

        # Ignora arquivos fora de src/
        try:
            # Verifica se "src" está no caminho
            parts = path.parts
            if "src" not in parts:
                return True
        except ValueError:
            # Caminho relativo que não contém src/
            return True

        return False

    def get_test_path(self, source_file: Path) -> Path:
        """Mapeia um arquivo fonte para seu arquivo de teste correspondente.

        Args:
            source_file: Caminho do arquivo fonte (ex: src/main.py)

        Returns:
            Caminho do teste correspondente (ex: tests/test_main.py)

        Exemplos:
            src/main.py          -> tests/test_main.py
            src/core/utils.py    -> tests/core/test_utils.py
            src/app/api/routes.py -> tests/app/api/test_routes.py
        """
        # Normaliza o caminho
        path = Path(source_file)

        # Extrai a parte após "src/"
        parts = list(path.parts)
        try:
            src_index = parts.index("src")
        except ValueError:
            # Se não encontrar "src", assume que é o caminho completo
            src_index = 0

        # Pega todos os componentes após "src/"
        relative_parts = parts[src_index + 1 :]

        # Constrói o caminho do teste
        # Se houver subdiretórios, mantém a estrutura
        if len(relative_parts) > 1:
            # src/core/utils.py -> tests/core/test_utils.py
            test_parts = (
                ["tests"] + relative_parts[:-1] + [f"test_{relative_parts[-1]}"]
            )
        else:
            # src/main.py -> tests/test_main.py
            test_parts = ["tests", f"test_{relative_parts[0]}"]

        return Path(*test_parts)

    def validate(self, files: list[Path]) -> tuple[bool, list[Path]]:
        """Valida se todos os arquivos possuem testes correspondentes.

        Args:
            files: Lista de arquivos a validar

        Returns:
            Tupla (sucesso, arquivos_sem_teste)
            - sucesso: True se todos os testes existem, False caso contrário
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

        if not success:
            print("❌ TDD Guardian: Arquivos sem testes correspondentes detectados!\n")
            print("Os seguintes arquivos em src/ não possuem testes:\n")

            for file_path in missing:
                test_path = self.get_test_path(file_path)
                print(f"  ⚠️  {file_path}")
                print(f"      Esperado: {test_path}\n")

            print("💡 Dica: Crie os testes antes de fazer commit (TDD).")
            print(
                "   Cada arquivo em src/ deve ter um teste correspondente em tests/.\n"
            )

            return 1

        # Validação passou
        return 0


def main() -> int:
    """Ponto de entrada do script.

    Returns:
        Exit code (0 = sucesso, 1 = falha)
    """
    # Obtém lista de arquivos dos argumentos de linha de comando
    files = sys.argv[1:]

    if not files:
        # Nenhum arquivo fornecido, considera sucesso
        return 0

    # Cria instância do guardian e executa validação
    guardian = TDDGuardian()
    return guardian.run(files)


if __name__ == "__main__":
    sys.exit(main())
