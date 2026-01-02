"""Testes unitários blindados usando MemoryFileSystem."""

from pathlib import Path

from scripts.core.cortex.mapper import ProjectMapper
from scripts.utils.filesystem import MemoryFileSystem


class TestProjectMapperIntegration:
    """Testa a lógica real do Mapper isolando apenas o I/O."""

    def test_map_project_real_logic_killed(self) -> None:
        """Mata mutantes executando a lógica real contra um FileSystem em memória."""
        # 1. Setup do Ambiente Falso (Em Memória)
        fake_root = Path("/app")
        mem_fs = MemoryFileSystem()

        # 2. Criar os arquivos que o código vai ler (Real Input)
        # Se o mutmut alterar a lógica de como ler 'project.name', este teste vai pegar.
        mem_fs.write_text(
            str(fake_root / "pyproject.toml"),
            """
            [project]
            name = "mutant-hunter"
            version = "1.0.0"
            description = "Hunting mutants"
            requires-python = ">=3.10"
            dependencies = ["fastapi"]

            [project.scripts]
            start = "main:app"
            """,
        )

        # Criar estrutura de pastas para scanners
        mem_fs.mkdir(str(fake_root / "scripts" / "cli"))
        mem_fs.mkdir(str(fake_root / "docs"))

        # 3. Instanciar o Mapper com o FileSystem Falso
        # AQUI ESTÁ O TRUQUE: Não mockamos métodos internos!
        mapper = ProjectMapper(fake_root, fs=mem_fs)

        # 4. Executar (Vai rodar o código real de _load_pyproject, _scan_cli, etc)
        # Desligamos o knowledge para focar na estrutura básica primeiro
        context = mapper.map_project(include_knowledge=False)

        # 5. Asserções (Kill Zone)
        assert (
            context.project_name == "mutant-hunter"
        )  # Mata mutantes em _load_pyproject
        assert context.version == "1.0.0"  # Mata mutantes de versão
        assert context.description == "Hunting mutants"  # Mata mutantes de descrição
        assert "fastapi" in context.dependencies  # Mata mutantes de dependência
        assert context.python_version == ">=3.10"  # Mata mutantes de python_version
