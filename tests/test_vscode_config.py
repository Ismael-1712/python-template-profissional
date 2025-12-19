"""Testes para configuração do VS Code.

Verifica a integridade e validade dos arquivos de configuração do VS Code,
garantindo que as tasks de automação Git estejam corretamente configuradas.
"""

import json
from pathlib import Path

import pytest


class TestVSCodeConfiguration:
    """Testes para configuração do VS Code."""

    @pytest.fixture
    def vscode_dir(self) -> Path:
        """Retorna o diretório .vscode do projeto."""
        return Path(__file__).parent.parent / ".vscode"

    @pytest.fixture
    def tasks_json_path(self, vscode_dir: Path) -> Path:
        """Retorna o caminho para tasks.json."""
        return vscode_dir / "tasks.json"

    def test_vscode_directory_exists(self, vscode_dir: Path) -> None:
        """Verifica se o diretório .vscode existe."""
        assert vscode_dir.exists(), "Diretório .vscode não encontrado"
        assert vscode_dir.is_dir(), ".vscode deve ser um diretório"

    def test_tasks_json_exists(self, tasks_json_path: Path) -> None:
        """Verifica se o arquivo tasks.json existe."""
        assert tasks_json_path.exists(), (
            "Arquivo .vscode/tasks.json não encontrado. "
            "Este arquivo é necessário para integração com VS Code."
        )

    def test_tasks_json_valid_json(self, tasks_json_path: Path) -> None:
        """Verifica se tasks.json é um JSON válido."""
        with open(tasks_json_path, encoding="utf-8") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"tasks.json não é um JSON válido: {e}")

    def test_tasks_json_structure(self, tasks_json_path: Path) -> None:
        """Verifica a estrutura básica do tasks.json."""
        with open(tasks_json_path, encoding="utf-8") as f:
            config = json.load(f)

        assert "version" in config, "tasks.json deve conter campo 'version'"
        assert config["version"] == "2.0.0", (
            "version deve ser '2.0.0' (VS Code Tasks v2)"
        )
        assert "tasks" in config, "tasks.json deve conter campo 'tasks'"
        assert isinstance(config["tasks"], list), "'tasks' deve ser uma lista"

    def test_git_direct_push_main_task_exists(
        self,
        tasks_json_path: Path,
    ) -> None:
        """Verifica se a task 'Git: Direct Push Main' existe."""
        with open(tasks_json_path, encoding="utf-8") as f:
            config = json.load(f)

        tasks = config.get("tasks", [])
        task_labels = [task.get("label") for task in tasks]

        assert "Git: Direct Push Main" in task_labels, (
            "Task 'Git: Direct Push Main' não encontrada em tasks.json"
        )

    def test_git_pr_cleanup_task_exists(self, tasks_json_path: Path) -> None:
        """Verifica se a task 'Git: PR Cleanup' existe."""
        with open(tasks_json_path, encoding="utf-8") as f:
            config = json.load(f)

        tasks = config.get("tasks", [])
        task_labels = [task.get("label") for task in tasks]

        assert "Git: PR Cleanup" in task_labels, (
            "Task 'Git: PR Cleanup' não encontrada em tasks.json"
        )

    def test_direct_push_main_task_configuration(
        self,
        tasks_json_path: Path,
    ) -> None:
        """Verifica a configuração da task 'Git: Direct Push Main'."""
        with open(tasks_json_path, encoding="utf-8") as f:
            config = json.load(f)

        tasks = config.get("tasks", [])
        direct_push_task = next(
            (t for t in tasks if t.get("label") == "Git: Direct Push Main"),
            None,
        )

        assert direct_push_task is not None, (
            "Task 'Git: Direct Push Main' não encontrada"
        )

        # Validar campos obrigatórios
        assert direct_push_task.get("type") == "shell", "Task deve ser do tipo 'shell'"
        assert "./scripts/direct-push-main.sh" in direct_push_task.get(
            "command",
            "",
        ), "Comando deve referenciar o script correto"

    def test_pr_cleanup_task_configuration(
        self,
        tasks_json_path: Path,
    ) -> None:
        """Verifica a configuração da task 'Git: PR Cleanup'."""
        with open(tasks_json_path, encoding="utf-8") as f:
            config = json.load(f)

        tasks = config.get("tasks", [])
        pr_cleanup_task = next(
            (t for t in tasks if t.get("label") == "Git: PR Cleanup"),
            None,
        )

        assert pr_cleanup_task is not None, "Task 'Git: PR Cleanup' não encontrada"

        # Validar campos obrigatórios
        assert pr_cleanup_task.get("type") == "shell", "Task deve ser do tipo 'shell'"
        assert "./scripts/post-pr-cleanup.sh" in pr_cleanup_task.get(
            "command",
            "",
        ), "Comando deve referenciar o script correto"

    def test_scripts_referenced_exist(self, tasks_json_path: Path) -> None:
        """Verifica se os scripts referenciados nas tasks existem."""
        project_root = Path(__file__).parent.parent

        scripts = [
            project_root / "scripts" / "direct-push-main.sh",
            project_root / "scripts" / "post-pr-cleanup.sh",
        ]

        for script in scripts:
            assert script.exists(), f"Script {script.name} não encontrado em scripts/"
            assert script.is_file(), f"{script.name} deve ser um arquivo"

    def test_scripts_are_executable(self, tasks_json_path: Path) -> None:
        """Verifica se os scripts possuem permissões de execução."""
        project_root = Path(__file__).parent.parent

        scripts = [
            project_root / "scripts" / "direct-push-main.sh",
            project_root / "scripts" / "post-pr-cleanup.sh",
        ]

        for script in scripts:
            # No Unix, verificar se tem permissão de execução
            import os
            import stat

            if os.name != "nt":  # Não Windows
                st = script.stat()
                is_executable = bool(st.st_mode & stat.S_IXUSR)
                assert is_executable, (
                    f"Script {script.name} não tem permissão de execução. "
                    f"Execute: chmod +x {script}"
                )
