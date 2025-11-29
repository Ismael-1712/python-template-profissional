#!/usr/bin/env python3
"""🔧 Version Governor - Automação de Manutenção de Versões Python.

Este script automatiza a atualização do `.python-version` para os patches
mais recentes disponíveis no pyenv, garantindo paridade com o GitHub Actions.

Arquitetura:
    1. Consulta pyenv install --list
    2. Extrai o patch mais recente de cada minor version (3.10, 3.11, 3.12)
    3. Atualiza .python-version se necessário
    4. Instala as novas versões via pyenv

Uso:
    python scripts/maintain_versions.py
    make upgrade-python
"""

import re
import subprocess
import sys
from pathlib import Path

# ======================================================================
# CONFIGURAÇÃO
# ======================================================================
TARGET_VERSIONS = ["3.10", "3.11", "3.12"]
PYTHON_VERSION_FILE = Path(".python-version")


# Cores ANSI para output
class Colors:
    """Constantes de cores ANSI para formatação de terminal."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# ======================================================================
# FUNÇÕES AUXILIARES
# ======================================================================
def print_header(message: str) -> None:
    """Imprime cabeçalho formatado."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(message: str) -> None:
    """Imprime mensagem de sucesso."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    """Imprime mensagem informativa."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Imprime mensagem de aviso."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Imprime mensagem de erro."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def run_command(cmd: list[str], check: bool = True) -> tuple[int, str, str]:
    """Executa comando e retorna (returncode, stdout, stderr).

    Args:
        cmd: Lista com comando e argumentos
        check: Se True, levanta exceção em caso de erro

    Returns:
        Tupla (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


# ======================================================================
# LÓGICA DE CORE
# ======================================================================
def get_available_versions() -> list[str]:
    """Consulta pyenv install --list e retorna todas as versões disponíveis.

    Returns:
        Lista de versões (ex: ['3.10.19', '3.11.14', '3.12.12'])
    """
    print_info("Consultando versões disponíveis no pyenv...")

    returncode, stdout, stderr = run_command(["pyenv", "install", "--list"])

    if returncode != 0:
        print_error(f"Erro ao executar pyenv: {stderr}")
        sys.exit(1)

    # Regex para capturar apenas versões estáveis (ex: 3.12.1)
    # Ignora dev, rc, beta, alpha
    version_pattern = re.compile(r"^\s+(3\.\d+\.\d+)$")

    versions = []
    for line in stdout.split("\n"):
        match = version_pattern.match(line)
        if match:
            versions.append(match.group(1))

    print_success(f"Encontradas {len(versions)} versões estáveis do Python")
    return versions


def find_latest_patch(versions: list[str], minor: str) -> str | None:
    """Encontra o maior patch numérico para uma minor version específica.

    Args:
        versions: Lista de todas as versões disponíveis
        minor: Minor version alvo (ex: '3.12')

    Returns:
        Versão com maior patch (ex: '3.12.12') ou None se não encontrada
    """
    # Filtra versões que correspondem ao minor
    matching = [v for v in versions if v.startswith(f"{minor}.")]

    if not matching:
        return None

    # Ordena por (major, minor, patch) numericamente
    def version_key(v: str) -> tuple[int, int, int]:
        parts = v.split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    matching.sort(key=version_key, reverse=True)
    return matching[0]


def get_latest_versions() -> dict[str, str]:
    """Retorna um dicionário com as versões mais recentes para cada minor alvo.

    Returns:
        Dict no formato {'3.10': '3.10.19', '3.11': '3.11.14', ...}
    """
    available = get_available_versions()
    latest = {}

    for minor in TARGET_VERSIONS:
        version = find_latest_patch(available, minor)
        if version:
            latest[minor] = version
            print_info(f"Versão mais recente para Python {minor}: {version}")
        else:
            print_warning(f"Nenhuma versão encontrada para Python {minor}")

    return latest


def read_current_versions() -> list[str]:
    """Lê o arquivo .python-version atual.

    Returns:
        Lista de versões no arquivo (uma por linha)
    """
    if not PYTHON_VERSION_FILE.exists():
        print_warning(f"Arquivo {PYTHON_VERSION_FILE} não encontrado")
        return []

    content = PYTHON_VERSION_FILE.read_text().strip()
    versions = [line.strip() for line in content.split("\n") if line.strip()]

    print_info(f"Versões atuais no {PYTHON_VERSION_FILE}:")
    for v in versions:
        print(f"  • {v}")

    return versions


def write_versions(versions: list[str]) -> None:
    """Escreve versões no arquivo .python-version (ordenadas do maior para menor).

    Args:
        versions: Lista de versões para escrever
    """

    # Ordena do maior para menor (3.12 -> 3.11 -> 3.10)
    def version_key(v: str) -> tuple[int, int, int]:
        parts = v.split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    sorted_versions = sorted(versions, key=version_key, reverse=True)
    content = "\n".join(sorted_versions) + "\n"

    PYTHON_VERSION_FILE.write_text(content)
    print_success(f"Arquivo {PYTHON_VERSION_FILE} atualizado:")
    for v in sorted_versions:
        print(f"  • {v}")


def install_version(version: str) -> bool:
    """Instala uma versão Python via pyenv (skip se já existir).

    Args:
        version: Versão para instalar (ex: '3.12.12')

    Returns:
        True se instalação bem-sucedida, False caso contrário
    """
    print_info(f"Instalando Python {version} (skip se já existir)...")

    returncode, stdout, stderr = run_command(
        ["pyenv", "install", version, "--skip-existing"],
        check=False,
    )

    if returncode == 0:
        print_success(f"Python {version} instalado/verificado")
        return True
    print_error(f"Erro ao instalar Python {version}:")
    print(f"  {stderr}")
    return False


# ======================================================================
# FLUXO PRINCIPAL
# ======================================================================
def main() -> int:
    """Fluxo principal de execução.

    Returns:
        0 se sucesso, 1 se erro
    """
    print_header("🔧 Version Governor - Automação de Manutenção de Versões")

    # 1. Buscar versões mais recentes
    print_header("📋 Fase 1: Análise de Versões Disponíveis")
    latest_versions = get_latest_versions()

    if not latest_versions:
        print_error("Nenhuma versão disponível encontrada")
        return 1

    # 2. Ler versões atuais
    print_header("📂 Fase 2: Leitura do .python-version Atual")
    current_versions = read_current_versions()

    # 3. Detectar mudanças
    print_header("🔍 Fase 3: Detecção de Atualizações")
    new_versions = list(latest_versions.values())
    updates_needed = set(new_versions) != set(current_versions)

    if not updates_needed:
        print_success("✨ Todas as versões já estão atualizadas!")
        print_info("Versões atuais:")
        for v in current_versions:
            print(f"  • Python {v}")
        return 0

    # Mostrar o que será atualizado
    print_warning("Atualizações detectadas:")
    current_dict = {
        v.rsplit(".", 1)[0]: v
        for v in current_versions
        if "." in v and v.count(".") >= 2
    }

    for minor, latest in sorted(latest_versions.items(), reverse=True):
        current = current_dict.get(minor, "não instalada")
        if current != latest:
            arrow = f"{Colors.OKGREEN}{latest}{Colors.ENDC}"
            print(f"  • Python {minor}: {current} → {arrow}")
        else:
            print(f"  • Python {minor}: {current} (sem mudanças)")

    # 4. Atualizar arquivo
    print_header("📝 Fase 4: Atualização do .python-version")
    write_versions(new_versions)

    # 5. Instalar novas versões
    print_header("⬇️  Fase 5: Instalação das Versões via Pyenv")
    all_success = True
    for version in new_versions:
        if not install_version(version):
            all_success = False

    # 6. Resultado final
    print_header("✅ Fase 6: Resumo Final")
    if all_success:
        print_success("🎉 Todas as versões foram atualizadas com sucesso!")
        print_info("\nPróximos passos recomendados:")
        print("  1. Execute: pyenv rehash")
        print("  2. Verifique: pyenv versions")
        print("  3. Teste: tox")
        return 0
    print_warning("⚠️  Algumas versões não puderam ser instaladas")
    print_info("Verifique os logs acima para mais detalhes")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_error("\n\nOperação cancelada pelo usuário")
        sys.exit(130)
    except Exception as e:
        print_error(f"\n\nErro inesperado: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
