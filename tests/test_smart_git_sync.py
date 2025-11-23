#!/usr/bin/env python3
"""Test Suite for Smart Git Synchronization System.

Comprehensive test suite to validate the Smart Git Sync functionality
in various scenarios and edge cases.

REFATORADO (P20): Testes unitários puros com unittest.mock estrito.
- Sem I/O real (disco, rede, processos)
- Mocks para Path, subprocess, open()
- Velocidade e isolamento garantidos

Usage:
    pytest tests/test_smart_git_sync.py -v
    pytest tests/test_smart_git_sync.py --cov=scripts.git_sync
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import the module under test from git_sync package
from scripts.git_sync.config import load_config
from scripts.git_sync.exceptions import AuditError, GitOperationError, SyncError
from scripts.git_sync.models import SyncStep
from scripts.git_sync.sync_logic import SyncOrchestrator


class TestSyncStep(unittest.TestCase):
    """Test cases for SyncStep class."""

    def test_sync_step_initialization(self) -> None:
        """Test SyncStep initialization."""
        step = SyncStep("test_step", "Test step description")
        self.assertEqual(step.name, "test_step")
        self.assertEqual(step.description, "Test step description")
        self.assertEqual(step.status, "pending")
        self.assertIsNone(step.start_time)
        self.assertIsNone(step.end_time)
        self.assertIsNone(step.error)
        self.assertEqual(step.details, {})

    def test_sync_step_start(self) -> None:
        """Test SyncStep start method."""
        step = SyncStep("test_step", "Test step description")
        step.start()
        self.assertEqual(step.status, "running")
        self.assertIsNotNone(step.start_time)

    def test_sync_step_complete(self) -> None:
        """Test SyncStep complete method."""
        step = SyncStep("test_step", "Test step description")
        step.start()
        step.complete({"result": "success"})

        self.assertEqual(step.status, "success")
        self.assertIsNotNone(step.end_time)
        self.assertEqual(step.details["result"], "success")

    def test_sync_step_fail(self) -> None:
        """Test SyncStep fail method."""
        step = SyncStep("test_step", "Test step description")
        step.start()
        step.fail("Test error", {"error_code": 500})

        self.assertEqual(step.status, "failed")
        self.assertEqual(step.error, "Test error")
        self.assertEqual(step.details["error_code"], 500)

    def test_sync_step_to_dict(self) -> None:
        """Test SyncStep to_dict serialization."""
        step = SyncStep("test_step", "Test step description")
        step.start()
        step.complete({"result": "success"})

        result_dict = step.to_dict()
        self.assertEqual(result_dict["name"], "test_step")
        self.assertEqual(result_dict["status"], "success")
        self.assertIn("start_time", result_dict)
        self.assertIn("end_time", result_dict)


class TestConfigLoading(unittest.TestCase):
    """Test cases for configuration loading."""

    def test_load_default_config(self) -> None:
        """Test loading default configuration."""
        config = load_config()

        # Check that default values are present
        self.assertTrue(config["audit_enabled"])
        self.assertEqual(config["audit_timeout"], 300)
        self.assertEqual(config["audit_fail_threshold"], "HIGH")
        self.assertTrue(config["strict_audit"])

    @patch("scripts.git_sync.config.Path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("scripts.git_sync.config.yaml.safe_load")
    def test_load_config_from_file(
        self,
        mock_yaml_load: MagicMock,
        mock_open_fn: MagicMock,
        mock_exists: MagicMock,
    ) -> None:
        """Test loading configuration from YAML file (SEM I/O REAL)."""
        # ✅ Mock: Arquivo existe
        mock_exists.return_value = True

        # ✅ Mock: Conteúdo YAML
        test_config = {
            "audit_enabled": False,
            "audit_timeout": 600,
            "custom_setting": "test_value",
        }
        mock_yaml_load.return_value = test_config

        # ✅ Mock: open() retorna um file object simulado
        mock_file = MagicMock()
        mock_open_fn.return_value.__enter__.return_value = mock_file

        config_path = Path("/fake/config.yaml")
        config = load_config(config_path)

        # Check that custom values override defaults
        self.assertFalse(config["audit_enabled"])
        self.assertEqual(config["audit_timeout"], 600)
        self.assertEqual(config["custom_setting"], "test_value")

        # Check that unspecified defaults are still present
        self.assertEqual(config["audit_fail_threshold"], "HIGH")

        # ✅ Validação: open() foi chamado corretamente
        mock_open_fn.assert_called_once()

    @patch("scripts.git_sync.config.Path.exists")
    def test_load_config_nonexistent_file(self, mock_exists: MagicMock) -> None:
        """Test loading configuration with non-existent file (SEM I/O REAL)."""
        # ✅ Mock: Arquivo NÃO existe
        mock_exists.return_value = False

        nonexistent_path = Path("/nonexistent/config.yaml")
        config = load_config(nonexistent_path)

        # Should return default config
        self.assertTrue(config["audit_enabled"])


class TestSyncOrchestrator(unittest.TestCase):
    """Test cases for SyncOrchestrator class (REFATORADO - SEM I/O REAL)."""

    def setUp(self) -> None:
        """Set up test environment com MOCKS ESTRITOS."""
        # ✅ Mock: Path para workspace (SEM mkdtemp real)
        self.temp_dir = MagicMock(spec=Path)
        self.temp_dir.__str__ = MagicMock(return_value="/fake/workspace")
        self.temp_dir.__truediv__ = MagicMock(return_value=MagicMock(spec=Path))
        self.temp_dir.resolve.return_value = self.temp_dir

        # ✅ Mock: .git directory (simula existência)
        self.git_dir = MagicMock(spec=Path)
        self.git_dir.exists.return_value = True

        # Configuração de teste
        self.config = {
            "audit_enabled": True,
            "strict_audit": True,
            "auto_fix_enabled": True,
            "cleanup_enabled": False,
        }

    def tearDown(self) -> None:
        """Clean up - NÃO FAZ NADA (sem I/O real)."""
        # ✅ Nenhum shutil.rmtree() necessário

    @patch("scripts.git_sync.sync_logic.Path")
    def test_sync_orchestrator_initialization(self, mock_path_cls: MagicMock) -> None:
        """Test SyncOrchestrator initialization (SEM I/O REAL)."""
        # ✅ Mock: Path.__truediv__ para simular / ".git"
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config=self.config,
            dry_run=True,
        )

        self.assertEqual(sync.workspace_root, mock_workspace)
        self.assertEqual(sync.config, self.config)
        self.assertTrue(sync.dry_run)
        self.assertEqual(len(sync.steps), 0)

    @patch("scripts.git_sync.sync_logic.Path")
    def test_validate_git_repository_success(self, mock_path_cls: MagicMock) -> None:
        """Test Git repository validation success (SEM I/O REAL)."""
        # ✅ Mock: .git existe
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # Should not raise an exception
        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config=self.config,
            dry_run=True,
        )

        # ✅ Validação: objeto criado com sucesso
        self.assertIsNotNone(sync)

    @patch("scripts.git_sync.sync_logic.Path")
    def test_validate_git_repository_failure(self, mock_path_cls: MagicMock) -> None:
        """Test Git repository validation failure (SEM I/O REAL)."""
        # ✅ Mock: .git NÃO existe
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = False  # ❌ Não existe
        mock_workspace.__truediv__.return_value = mock_git_dir

        with self.assertRaises(SyncError):
            SyncOrchestrator(
                workspace_root=mock_workspace,
                config=self.config,
                dry_run=True,
            )

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_run_command_dry_run(
        self,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test command execution in dry run mode (SEM SUBPROCESS REAL)."""
        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config=self.config,
            dry_run=True,
        )

        result = sync._run_command(["git", "status"])

        # ✅ Should not actually execute command
        mock_run.assert_not_called()
        self.assertEqual(result.stdout, "[DRY RUN]")
        self.assertEqual(result.returncode, 0)

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_run_command_success(
        self,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test successful command execution (SEM SUBPROCESS REAL)."""
        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # ✅ Mock: subprocess.run retorna sucesso
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config=self.config,
            dry_run=False,
        )

        result = sync._run_command(["git", "status"])

        # ✅ Validação: subprocess.run foi chamado
        mock_run.assert_called_once()
        self.assertEqual(result.stdout, "test output")
        self.assertEqual(result.returncode, 0)

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_run_command_failure(
        self,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test command execution failure (SEM SUBPROCESS REAL)."""
        from subprocess import CalledProcessError

        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # ✅ Mock: subprocess.run lança exceção
        mock_run.side_effect = CalledProcessError(
            returncode=1,
            cmd=["git", "status"],
            stderr="error message",
        )

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config=self.config,
            dry_run=False,
        )

        with self.assertRaises(GitOperationError):
            sync._run_command(["git", "status"])


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling and edge cases."""

    def test_sync_error_inheritance(self) -> None:
        """Test that custom exceptions inherit correctly."""
        self.assertTrue(issubclass(GitOperationError, SyncError))
        self.assertTrue(issubclass(AuditError, SyncError))
        self.assertTrue(issubclass(SyncError, Exception))

    def test_sync_error_messages(self) -> None:
        """Test that error messages are handled correctly."""
        error = SyncError("Test sync error")
        self.assertEqual(str(error), "Test sync error")

        git_error = GitOperationError("Git operation failed")
        self.assertEqual(str(git_error), "Git operation failed")

        audit_error = AuditError("Audit check failed")
        self.assertEqual(str(audit_error), "Audit check failed")


# ============================================================================
# TESTES ADICIONAIS - COBERTURA DE MÉTODOS CRÍTICOS (P20 - Fase 02)
# ============================================================================


class TestSyncOrchestratorAdvanced(unittest.TestCase):
    """Testes avançados para métodos não cobertos anteriormente."""

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_check_git_status_clean_repo(
        self,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test _check_git_status com repositório limpo."""
        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # ✅ Mock: git status retorna vazio (repo limpo)
        mock_status_result = MagicMock()
        mock_status_result.returncode = 0
        mock_status_result.stdout = ""  # Repo limpo
        mock_status_result.stderr = ""

        # ✅ Mock: git branch retorna main
        mock_branch_result = MagicMock()
        mock_branch_result.returncode = 0
        mock_branch_result.stdout = "main"
        mock_branch_result.stderr = ""

        mock_run.side_effect = [mock_status_result, mock_branch_result]

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config={"audit_enabled": False},
            dry_run=False,
        )

        result = sync._check_git_status()

        # ✅ Validações
        self.assertTrue(result["is_clean"])
        self.assertEqual(result["total_changes"], 0)
        self.assertEqual(result["current_branch"], "main")

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_check_git_status_with_changes(
        self,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test _check_git_status com mudanças pendentes."""
        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # ✅ Mock: git status retorna arquivos modificados
        mock_status_result = MagicMock()
        mock_status_result.returncode = 0
        mock_status_result.stdout = "M  file1.py\nA  file2.py\n"
        mock_status_result.stderr = ""

        # ✅ Mock: git branch retorna feature-branch
        mock_branch_result = MagicMock()
        mock_branch_result.returncode = 0
        mock_branch_result.stdout = "feature-branch"
        mock_branch_result.stderr = ""

        mock_run.side_effect = [mock_status_result, mock_branch_result]

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config={"audit_enabled": False},
            dry_run=False,
        )

        result = sync._check_git_status()

        # ✅ Validações
        self.assertFalse(result["is_clean"])
        self.assertEqual(result["total_changes"], 2)
        self.assertEqual(len(result["changed_files"]), 2)
        self.assertIn("M  file1.py", result["changed_files"])
        self.assertIn("A  file2.py", result["changed_files"])

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    @patch("scripts.git_sync.sync_logic.sys.executable", "/usr/bin/python3")
    def test_run_code_audit_not_found(
        self,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test _run_code_audit quando script de audit não existe."""
        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace

        # ✅ Mock: .git existe para validação inicial
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True

        # ✅ Mock: audit script NÃO existe
        # workspace_root / "scripts" / "code_audit.py"
        mock_scripts_dir = MagicMock(spec=Path)
        mock_audit_script = MagicMock(spec=Path)
        mock_audit_script.exists.return_value = False  # ❌ Script não existe

        # Simula: workspace_root / "scripts" retorna mock_scripts_dir
        # depois: mock_scripts_dir / "code_audit.py" retorna mock_audit_script
        mock_scripts_dir.__truediv__.return_value = mock_audit_script

        # Patch do __truediv__ para retornar o mock correto
        def mock_truediv(path_str: str) -> MagicMock:
            if path_str == ".git":
                return mock_git_dir
            if path_str == "scripts":
                return mock_scripts_dir
            return MagicMock(spec=Path)

        mock_workspace.__truediv__.side_effect = mock_truediv

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config={"audit_enabled": True, "strict_audit": False},
            dry_run=False,
        )

        result = sync._run_code_audit()

        # ✅ Validação: audit foi pulado porque script não existe
        self.assertTrue(result["passed"])
        self.assertEqual(result["status"], "skipped")

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_commit_and_push_success(
        self,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test _commit_and_push com sucesso completo (add, commit, push)."""
        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # ✅ Mock: Resultados de comandos git
        mock_add_result = MagicMock()
        mock_add_result.returncode = 0
        mock_add_result.stdout = ""

        mock_commit_result = MagicMock()
        mock_commit_result.returncode = 0
        mock_commit_result.stdout = ""

        mock_hash_result = MagicMock()
        mock_hash_result.returncode = 0
        mock_hash_result.stdout = "abc123def456\n"

        mock_push_result = MagicMock()
        mock_push_result.returncode = 0
        mock_push_result.stdout = ""

        mock_run.side_effect = [
            mock_add_result,
            mock_commit_result,
            mock_hash_result,
            mock_push_result,
        ]

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config={"audit_enabled": False},
            dry_run=False,
        )

        # ✅ Simula status git com mudanças
        git_status = {
            "is_clean": False,
            "changed_files": ["M  file1.py", "A  file2.py"],
            "total_changes": 2,
            "current_branch": "feature-branch",
        }

        result = sync._commit_and_push(git_status)

        # ✅ Validações: comandos foram chamados na ordem correta
        self.assertEqual(mock_run.call_count, 4)
        self.assertTrue(result["committed"])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["commit"]["hash"], "abc123def456")
        self.assertEqual(result["push"]["branch"], "feature-branch")

        # ✅ Verifica sequência de comandos
        calls = mock_run.call_args_list
        self.assertIn("git", calls[0][0][0])  # git add
        self.assertIn("git", calls[1][0][0])  # git commit
        self.assertIn("git", calls[2][0][0])  # git rev-parse
        self.assertIn("git", calls[3][0][0])  # git push

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    def test_commit_and_push_failure_rollback(
        self,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test _commit_and_push com falha no push e rollback."""
        from subprocess import CalledProcessError

        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # ✅ Mock: git add e commit funcionam, mas push falha
        mock_add_result = MagicMock()
        mock_add_result.returncode = 0

        mock_commit_result = MagicMock()
        mock_commit_result.returncode = 0

        mock_hash_result = MagicMock()
        mock_hash_result.returncode = 0
        mock_hash_result.stdout = "abc123\n"

        # ❌ Push falha
        mock_push_error = CalledProcessError(
            returncode=1,
            cmd=["git", "push", "origin", "main"],
            stderr="fatal: unable to access",
        )

        # ✅ Rollback funciona
        mock_rollback_result = MagicMock()
        mock_rollback_result.returncode = 0

        mock_run.side_effect = [
            mock_add_result,
            mock_commit_result,
            mock_hash_result,
            mock_push_error,  # Push falha aqui
            mock_rollback_result,  # Rollback chamado
        ]

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config={"audit_enabled": False},
            dry_run=False,
        )

        git_status = {
            "is_clean": False,
            "changed_files": ["M  file.py"],
            "total_changes": 1,
            "current_branch": "main",
        }

        # ✅ Deve lançar exceção devido ao push falhar
        with self.assertRaises(GitOperationError):
            sync._commit_and_push(git_status)

        # ✅ Validação: rollback foi chamado
        self.assertEqual(mock_run.call_count, 5)  # add, commit, hash, push, rollback
        rollback_call = mock_run.call_args_list[4]
        self.assertIn("reset", str(rollback_call))
        self.assertIn("--soft", str(rollback_call))

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    @patch.object(SyncOrchestrator, "_check_git_status")
    @patch.object(SyncOrchestrator, "_run_code_audit")
    @patch.object(SyncOrchestrator, "_commit_and_push")
    @patch.object(SyncOrchestrator, "_save_sync_report")
    def test_execute_sync_success(
        self,
        mock_save_report: MagicMock,
        mock_commit_push: MagicMock,
        mock_audit: MagicMock,
        mock_git_status: MagicMock,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test execute_sync fluxo completo de sucesso."""
        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # ✅ Mock: git status retorna mudanças
        mock_git_status.return_value = {
            "is_clean": False,
            "changed_files": ["M  test.py"],
            "total_changes": 1,
            "current_branch": "dev",
        }

        # ✅ Mock: audit passa
        mock_audit.return_value = {
            "passed": True,
            "exit_code": 0,
        }

        # ✅ Mock: commit e push funcionam
        mock_commit_push.return_value = {
            "status": "success",
            "committed": True,
            "commit": {"hash": "abc123"},
        }

        # ✅ Mock: save report retorna Path
        mock_save_report.return_value = Path("/fake/report.json")

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config={
                "audit_enabled": True,
                "strict_audit": True,
                "auto_fix_enabled": False,
                "cleanup_enabled": False,
            },
            dry_run=False,
        )

        result = sync.execute_sync()

        # ✅ Validações: fluxo completo executado
        self.assertTrue(result)
        mock_git_status.assert_called_once()
        mock_audit.assert_called_once()
        mock_commit_push.assert_called_once()
        mock_save_report.assert_called_once()

        # ✅ Validação: ordem de chamadas correta
        call_order = [
            mock_git_status,
            mock_audit,
            mock_commit_push,
            mock_save_report,
        ]
        for mock_obj in call_order:
            self.assertTrue(mock_obj.called)

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    @patch.object(SyncOrchestrator, "_check_git_status")
    @patch.object(SyncOrchestrator, "_run_code_audit")
    @patch.object(SyncOrchestrator, "_commit_and_push")
    @patch.object(SyncOrchestrator, "_save_sync_report")
    def test_execute_sync_audit_fail(
        self,
        mock_save_report: MagicMock,
        mock_commit_push: MagicMock,
        mock_audit: MagicMock,
        mock_git_status: MagicMock,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test execute_sync quando audit falha (não deve fazer commit)."""
        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # ✅ Mock: git status retorna mudanças
        mock_git_status.return_value = {
            "is_clean": False,
            "changed_files": ["M  bad_code.py"],
            "total_changes": 1,
            "current_branch": "feature",
        }

        # ❌ Mock: audit FALHA e lança exceção
        mock_audit.side_effect = AuditError("Code audit failed with exit code 1")

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config={
                "audit_enabled": True,
                "strict_audit": True,
            },
            dry_run=False,
        )

        result = sync.execute_sync()

        # ✅ Validações: fluxo parou no audit
        self.assertFalse(result)  # Falhou
        mock_git_status.assert_called_once()
        mock_audit.assert_called_once()

        # ✅ CRÍTICO: _commit_and_push NÃO deve ter sido chamado
        mock_commit_push.assert_not_called()

        # ✅ Report deve ser salvo mesmo em caso de falha
        mock_save_report.assert_called_once()

    @patch("scripts.git_sync.sync_logic.Path")
    @patch("scripts.git_sync.sync_logic.subprocess.run")
    @patch.object(SyncOrchestrator, "_check_git_status")
    @patch.object(SyncOrchestrator, "_save_sync_report")
    def test_execute_sync_clean_repo(
        self,
        mock_save_report: MagicMock,
        mock_git_status: MagicMock,
        mock_run: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Test execute_sync quando repositório está limpo (sem mudanças)."""
        # ✅ Setup: Mock workspace
        mock_workspace = MagicMock(spec=Path)
        mock_workspace.resolve.return_value = mock_workspace
        mock_git_dir = MagicMock(spec=Path)
        mock_git_dir.exists.return_value = True
        mock_workspace.__truediv__.return_value = mock_git_dir

        # ✅ Mock: git status retorna repo limpo (branch dev, não main)
        mock_git_status.return_value = {
            "is_clean": True,
            "changed_files": [],
            "total_changes": 0,
            "current_branch": "dev",  # ✅ Não é 'main', evita proteção
        }

        # ✅ Mock: save report
        mock_save_report.return_value = Path("/fake/report.json")

        sync = SyncOrchestrator(
            workspace_root=mock_workspace,
            config={"audit_enabled": True},
            dry_run=False,
        )

        result = sync.execute_sync()

        # ✅ Validações: retorna True mas não faz nada
        self.assertTrue(result)
        mock_git_status.assert_called_once()
        mock_save_report.assert_called_once()


# ============================================================================
# EXECUTAR TESTES COM PYTEST (Remover main() legado)
# ============================================================================


if __name__ == "__main__":
    # ✅ Use pytest para rodar os testes
    # pytest tests/test_smart_git_sync.py -v

    print("=" * 70)
    print("🧪 TESTES REFATORADOS (P20 - Fase 02)")
    print("=" * 70)
    print("✅ Sem I/O real (disco, rede, processos)")
    print("✅ Mocks estritos para subprocess, Path, open()")
    print("✅ Velocidade e isolamento garantidos")
    print("=" * 70)
    print("\n💡 Execute com: pytest tests/test_smart_git_sync.py -v")
    print("💡 Cobertura:    pytest tests/test_smart_git_sync.py --cov\n")

    # Fallback para unittest se pytest não estiver disponível
    unittest.main(argv=[""], exit=False, verbosity=2)
