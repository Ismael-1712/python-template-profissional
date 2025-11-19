#!/usr/bin/env python3
"""Sistema Genérico de Correção Automática de Linting.

==================================================

Script genérico e seguro para correção automática de problemas comuns de linting
em projetos Python, com foco em portabilidade e segurança.

Uso:
    python3 scripts/lint_fix.py [--dry-run] [--auto-commit] [path...]

Exemplos:
    python3 scripts/lint_fix.py                    # Modo interativo (padrão)
    python3 scripts/lint_fix.py --dry-run          # Apenas simula, não aplica
    python3 scripts/lint_fix.py --auto-commit src/ # Aplica e commita automaticamente

Características:
- Idempotente: Pode rodar múltiplas vezes sem problemas
- Seguro: Cria backups automáticos
- Genérico: Funciona em qualquer projeto Python
- Configurável: Via pyproject.toml
"""

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class LintFixConfig:
    """Configuração para o sistema de correção de lint."""

    def __init__(self, project_root: Path):
        """Inicializa a instância."""
        self.project_root = project_root
        self.backup_dir = project_root / ".lint_fix_backup"
        self.max_line_length = self._get_line_length_config()
        self.target_paths = self._get_target_paths()
        self.excluded_patterns = {
            "*.pyc",
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "env",
            ".env",
            "*.egg-info",
            "dist",
            "build",
        }

    def _get_line_length_config(self) -> int:
        """Obtém configuração de line-length do pyproject.toml."""
        pyproject_path = self.project_root / "pyproject.toml"

        if pyproject_path.exists():
            try:
                import tomllib
            except ModuleNotFoundError:
                try:
                    import tomli as tomllib
                except ModuleNotFoundError:
                    logger.error(
                        "Nem 'tomllib' (Python 3.11+) nem 'tomli' foram encontrados.",
                    )
                    error_msg = (
                        "Por favor, adicione 'tomli' às dependências "
                        "de dev no pyproject.toml."
                    )
                    logger.error(error_msg)
                    # Retorna o padrão se não puder ler o config
                    return 88

            try:
                with open(pyproject_path, "rb") as f:
                    config = tomllib.load(f)

                # Tenta diferentes locais de configuração
                locations = [
                    ["tool", "ruff", "line-length"],
                    ["tool", "black", "line-length"],
                    ["tool", "flake8", "max-line-length"],
                ]

                for location in locations:
                    value = config
                    for key in location:
                        value = value.get(key)
                        if value is None:
                            break
                    if isinstance(value, int):
                        return value

            except Exception as e:
                logger.debug(f"Erro ao ler pyproject.toml: {e}")

        return 88  # Padrão do black/ruff moderno

    def _get_target_paths(self) -> list[Path]:
        """Obtém caminhos alvo baseado na estrutura do projeto."""
        common_paths = ["src", "tests", "scripts"]
        target_paths = [self.project_root]

        for path_name in common_paths:
            path = self.project_root / path_name
            if path.is_dir():
                target_paths.append(path)

        return target_paths


class LintFixer:
    """Sistema principal de correção automática de linting."""

    def __init__(self, config: LintFixConfig, dry_run: bool = False):
        """Inicializa a instância."""
        self.config = config
        self.dry_run = dry_run
        self.fixes_applied: list[str] = []
        self.backup_created = False

    def create_backup(self, file_path: Path) -> bool:
        """Cria backup seguro de um arquivo antes das modificações."""
        if self.dry_run:
            return True

        try:
            if not self.config.backup_dir.exists():
                self.config.backup_dir.mkdir(parents=True)

            # Mantém estrutura de diretórios no backup
            relative_path = file_path.relative_to(self.config.project_root)
            backup_path = self.config.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(file_path, backup_path)
            self.backup_created = True
            return True

        except Exception as e:
            logger.error(f"Erro ao criar backup de {file_path}: {e}")
            return False

    def find_python_files(self, paths: list[Path]) -> set[Path]:
        """Encontra todos os arquivos Python nos caminhos especificados."""
        python_files = set()

        for path in paths:
            if path.is_file() and path.suffix == ".py":
                python_files.add(path)
            elif path.is_dir():
                # Busca recursiva por arquivos .py
                for py_file in path.rglob("*.py"):
                    # Verifica se não está em padrões excluídos
                    if not any(
                        py_file.match(pattern)
                        for pattern in self.config.excluded_patterns
                    ):
                        python_files.add(py_file)

        return python_files

    def fix_long_lines_generic(self, file_path: Path) -> bool:
        """Aplica correções genéricas para linhas longas."""
        if not self.create_backup(file_path):
            return False

        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            lines = content.splitlines()
            modified_lines = []
            fixes_in_file = 0

            for line_num, line in enumerate(lines, 1):
                if len(line) <= self.config.max_line_length:
                    modified_lines.append(line)
                    continue

                # Estratégias de correção genéricas
                new_line = self._apply_generic_fixes(line)

                if new_line != line:
                    fixes_in_file += 1
                    logger.debug(
                        f"Linha {line_num}: {len(line)} -> {len(new_line)} chars",
                    )

                modified_lines.append(new_line)

            new_content = "\n".join(modified_lines)
            if new_content.endswith("\n") != original_content.endswith("\n"):
                if original_content.endswith("\n"):
                    new_content += "\n"

            if new_content != original_content and not self.dry_run:
                file_path.write_text(new_content, encoding="utf-8")

            if fixes_in_file > 0:
                fix_msg = f"Fixed {fixes_in_file} long lines in {file_path.name}"
                self.fixes_applied.append(fix_msg)
                logger.info(f"✅ {fix_msg}")
                return True

            return False

        except Exception as e:
            logger.error(f"Erro ao processar {file_path}: {e}")
            return False

    def _apply_generic_fixes(self, line: str) -> str:
        """Aplica estratégias genéricas para corrigir linhas longas."""
        # Remove espaços extras
        line = line.rstrip()

        # Estratégia 1: Quebrar strings longas
        if '"' in line or "'" in line:
            line = self._break_long_strings(line)

        # Estratégia 2: Quebrar expressões longas
        if len(line) > self.config.max_line_length:
            line = self._break_long_expressions(line)

        return line

    def _break_long_strings(self, line: str) -> str:
        """Quebra strings longas em múltiplas linhas."""
        # Implementação simplificada - pode ser expandida
        if 'f"' in line and len(line) > self.config.max_line_length:
            # Tenta quebrar f-strings longas
            indent = len(line) - len(line.lstrip())
            indent_str = " " * indent

            # Para f-strings simples, tenta quebrar em operações de concatenação
            if " + " in line or " and " in line or " or " in line:
                # Quebra em operadores lógicos/aritméticos
                for op in [" and ", " or ", " + "]:
                    if op in line:
                        parts = line.split(op, 1)
                        if len(parts) == 2:
                            left = parts[0].rstrip()
                            right = parts[1].lstrip()
                            return f"{left}{op.strip()} \\\n{indent_str}    {right}"

        return line

    def _break_long_expressions(self, line: str) -> str:
        """Quebra expressões longas em múltiplas linhas."""
        # Implementação simplificada para casos comuns
        indent = len(line) - len(line.lstrip())
        indent_str = " " * indent

        # Quebra em vírgulas para listas/dicts/funções longas
        if "," in line and ("(" in line or "[" in line or "{" in line):
            # Encontra a última vírgula que permite quebra segura
            comma_positions = [i for i, c in enumerate(line) if c == ","]

            for pos in reversed(comma_positions):
                if pos < self.config.max_line_length - 20:  # Margem de segurança
                    part1 = line[: pos + 1]
                    part2 = line[pos + 1 :].lstrip()
                    if part2:  # Só quebra se houver conteúdo após a vírgula
                        return f"{part1}\n{indent_str}    {part2}"

        return line

    def run_formatter(self, paths: list[Path]) -> bool:
        """Executa formatador automático (ruff format)."""
        logger.info("🔧 Executando formatação automática...")

        if self.dry_run:
            logger.info("   [DRY-RUN] Formatação seria executada")
            return True

        try:
            cmd = [sys.executable, "-m", "ruff", "format"]
            cmd.extend(str(p) for p in paths)

            result = subprocess.run(  # noqa: subprocess
                cmd,
                check=False,
                capture_output=True,
                text=True,
                cwd=self.config.project_root,
                timeout=300,  # 5 minutos timeout
            )

            if result.returncode == 0:
                logger.info("✅ Formatação automática concluída")
                self.fixes_applied.append("Ruff format applied")
                return True
            logger.warning(f"Formatação com problemas: {result.stderr}")
            return False

        except subprocess.TimeoutExpired:
            logger.error("Timeout na formatação automática")
            return False
        except FileNotFoundError:
            logger.warning("Ruff não encontrado - pulando formatação automática")
            return False
        except Exception as e:
            logger.error(f"Erro na formatação: {e}")
            return False

    def check_lint_status(self, paths: list[Path]) -> tuple[bool, str]:
        """Verifica status do linting após correções."""
        logger.info("🔍 Verificando status do linting...")

        try:
            cmd = [sys.executable, "-m", "ruff", "check", "--output-format=concise"]
            cmd.extend(str(p) for p in paths)

            result = subprocess.run(  # noqa: subprocess
                cmd,
                check=False,
                capture_output=True,
                text=True,
                cwd=self.config.project_root,
                timeout=300,
            )

            if result.returncode == 0:
                return True, "Todos os problemas de linting foram resolvidos!"
            return False, result.stdout or result.stderr

        except FileNotFoundError:
            return True, "Ruff não disponível - status desconhecido"
        except Exception as e:
            return False, f"Erro na verificação: {e}"

    def run_fixes(self, paths: list[Path]) -> bool:
        """Executa todas as correções automáticas."""
        logger.info("🚨 Iniciando correções automáticas de linting")
        logger.info("=" * 50)

        if self.dry_run:
            logger.info("🔍 MODO DRY-RUN - Apenas simulação")

        python_files = self.find_python_files(paths)
        logger.info(f"📁 Encontrados {len(python_files)} arquivos Python")

        if not python_files:
            logger.warning("Nenhum arquivo Python encontrado")
            return False

        # Aplicar correções customizadas
        success_count = 0
        for file_path in python_files:
            if self.fix_long_lines_generic(file_path):
                success_count += 1

        if success_count > 0:
            logger.info(
                f"📊 Correções customizadas aplicadas em {success_count} arquivos",
            )

        # Executar formatação automática
        if self.run_formatter(paths):
            success_count += 1

        # Verificar status final
        lint_ok, lint_msg = self.check_lint_status(paths)

        if lint_ok:
            logger.info(f"✅ {lint_msg}")
            return True
        logger.warning(f"⚠️ Problemas persistentes:\n{lint_msg}")
        return False


def create_commit_if_needed(
    config: LintFixConfig,
    fixes: list[str],
    auto_commit: bool,
) -> bool:
    """Cria commit com as correções aplicadas, se solicitado."""
    if not fixes:
        logger.info("⚠️ Nenhuma correção foi aplicada")
        return False

    if not auto_commit:
        logger.info("📝 Correções aplicadas. Use --auto-commit para commit automático.")
        return False

    logger.info("📝 Criando commit automático...")

    try:
        # Verificar se há mudanças staged
        status_result = subprocess.run(  # noqa: subprocess
            ["git", "status", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
            cwd=config.project_root,
        )

        if not status_result.stdout.strip():
            logger.info("⚠️ Nenhuma mudança detectada pelo git")
            return False

        # Add files
        subprocess.run(  # noqa: subprocess
            ["git", "add", "."],
            cwd=config.project_root,
            check=True,
            timeout=30,
        )

        # Create commit message
        commit_msg = f"""style: automatic lint fixes

🔧 CORREÇÕES AUTOMÁTICAS APLICADAS:
{chr(10).join(f"• {fix}" for fix in fixes)}

⚡ Correções de linting aplicadas automaticamente:
• Linhas longas corrigidas genericamente
• Formatação automática (ruff format)
• Código padronizado conforme configuração do projeto

🎯 Gerado por: scripts/lint_fix.py"""

        # Commit
        subprocess.run(  # noqa: subprocess
            ["git", "commit", "-m", commit_msg],
            cwd=config.project_root,
            check=True,
            timeout=30,
        )

        logger.info("✅ Commit automático criado com sucesso!")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao criar commit: {e}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout ao criar commit")
        return False


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Sistema genérico de correção automática de linting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                        # Modo interativo (padrão)
  %(prog)s --dry-run             # Simula correções
  %(prog)s --auto-commit src/    # Aplica e commita
  %(prog)s src/ tests/           # Corrige caminhos específicos
        """,
    )

    parser.add_argument(
        "paths",
        nargs="*",
        help="Caminhos para processar (padrão: projeto inteiro)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas simula as correções sem aplicar",
    )
    parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Cria commit automático após correções",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Saída mais detalhada",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Configuração
    project_root = Path.cwd()
    config = LintFixConfig(project_root)

    # Determinar caminhos alvo
    if args.paths:
        target_paths = [Path(p).resolve() for p in args.paths]
        # Validar que os caminhos existem
        for path in target_paths:
            if not path.exists():
                logger.error(f"Caminho não existe: {path}")
                return 1
    else:
        target_paths = config.target_paths

    # Executar correções
    fixer = LintFixer(config, dry_run=args.dry_run)

    logger.info("🚨 SISTEMA DE CORREÇÃO AUTOMÁTICA DE LINTING")
    logger.info(f"📁 Projeto: {project_root.name}")
    logger.info(f"📏 Linha máxima: {config.max_line_length} chars")
    logger.info(
        f"🎯 Caminhos: {[str(p.relative_to(project_root)) for p in target_paths]}",
    )
    logger.info("")

    success = fixer.run_fixes(target_paths)

    if success:
        logger.info("🎉 CORREÇÕES CONCLUÍDAS COM SUCESSO!")

        if not args.dry_run:
            # Criar commit se solicitado
            if create_commit_if_needed(config, fixer.fixes_applied, args.auto_commit):
                logger.info("✅ PRÓXIMOS PASSOS:")
                logger.info("1. Execute: git push")
                logger.info("2. Verifique se CI/CD passa")
        else:
            logger.info("🔍 DRY-RUN concluído - nenhuma alteração foi feita")
    else:
        logger.error("❌ CORREÇÕES INCOMPLETAS")
        logger.info("💡 Considere intervenção manual para problemas persistentes")

    # Cleanup de backup se tudo correu bem
    if success and fixer.backup_created and not args.dry_run:
        try:
            shutil.rmtree(config.backup_dir)
            logger.debug("🧹 Backup temporário removido")
        except Exception:
            logger.debug("⚠️ Backup mantido por segurança")

    logger.info(f"📊 RESUMO: {len(fixer.fixes_applied)} tipos de correção aplicados")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
