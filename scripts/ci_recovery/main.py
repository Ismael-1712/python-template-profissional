#!/usr/bin/env python3
"""Sistema de Recuperação de Falhas de CI (SRE) - Ponto de Entrada Principal.

Este módulo contém o orquestrador (CIFailureRecoverySystem) e o
entrypoint (main) para o sistema de recuperação, refatorado
seguindo os princípios S.O.L.I.D. (P8.7).
"""

import gettext
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Importações S.O.L.I.D. (Relativas ao Pacote) ---
from scripts.ci_recovery import analyzer, reporter, runner, validator
from scripts.ci_recovery.models import (
    RecoveryReport,
    RecoveryStatus,
    RecoveryStep,
)

# --- Fim das Importações S.O.L.I.D. ---

# i18n setup
_locale_dir = Path(__file__).parent.parent.parent / "locales"
try:
    _translation = gettext.translation(
        "messages",
        localedir=str(_locale_dir),
        languages=[os.getenv("LANGUAGE", "pt_BR")],
        fallback=True,
    )
    _ = _translation.gettext
except Exception:
    # Fallback se não encontrar traduções
    def _(message: str) -> str:
        return message


# Configuração do Logger
# (Esta configuração deve permanecer com o entrypoint)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ci_recovery.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class CIFailureRecoverySystem:
    """Professional CI/CD failure recovery system.

    Implements industry best practices:
    - Idempotent operations
    - Secure subprocess execution
    - Structured logging
    - Comprehensive error handling
    - Portable POSIX compliance
    """

    def __init__(
        self,
        repository_path: Path | None = None,
        commit_hash: str | None = None,
        dry_run: bool = False,
    ) -> None:
        """Initialize the recovery system.

        Args:
            repository_path: Path to git repository (defaults to current directory)
            commit_hash: Specific commit to analyze (defaults to HEAD)
            dry_run: If True, only simulate operations without making changes

        """
        self.repository_path = repository_path or Path.cwd()
        self.commit_hash = commit_hash
        self.dry_run = dry_run
        self.report = RecoveryReport(
            timestamp=datetime.now(timezone.utc),
            commit_hash="",
            repository_path=self.repository_path,
        )

        # Validate repository
        if not validator.is_git_repository(
            repository_path=self.repository_path,
            dry_run=self.dry_run,
        ):
            raise ValueError(f"Not a git repository: {self.repository_path}")

        # Get actual commit hash
        self.commit_hash = self.commit_hash or validator.get_current_commit_hash(
            repository_path=self.repository_path,
            dry_run=self.dry_run,
        )
        self.report.commit_hash = self.commit_hash

        logger.info(
            f"Initialized CI Recovery System - Repository: {self.repository_path}, "
            f"Commit: {self.commit_hash}, Dry Run: {self.dry_run}",
        )

    def _log_step(
        self,
        step_name: str,
        status: RecoveryStatus,
        details: str = "",
        error_message: str = "",
        duration: float = 0.0,
    ) -> None:
        """Log a recovery step and add to report."""
        step = RecoveryStep(
            name=step_name,
            status=status,
            timestamp=datetime.now(timezone.utc),
            details=details,
            error_message=error_message,
            duration_seconds=duration,
        )

        self.report.steps.append(step)

        # Log with appropriate level
        emoji_map = {
            RecoveryStatus.SUCCESS: "✅",
            RecoveryStatus.FAILED: "❌",
            RecoveryStatus.IN_PROGRESS: "🔄",
            RecoveryStatus.PARTIAL_SUCCESS: "⚠️",
            RecoveryStatus.PENDING: "⏳",
        }

        emoji = emoji_map.get(status, "📋")
        log_message = f"{emoji} {step_name}"

        if details:
            log_message += f" - {details}"

        if status == RecoveryStatus.SUCCESS:
            logger.info(log_message)
        elif status == RecoveryStatus.FAILED:
            logger.error(f"{log_message} - Error: {error_message}")
        elif status == RecoveryStatus.IN_PROGRESS:
            logger.info(log_message)
        else:
            logger.warning(log_message)

    def execute_recovery(self) -> bool:
        """Execute the complete CI failure recovery process.

        Returns:
            True if recovery was successful, False otherwise

        """
        start_time = datetime.now()

        logger.info(
            _("🚨 Starting CI/CD Failure Recovery for commit {commit}").format(
                commit=self.commit_hash
            )
        )
        logger.info("=" * 70)

        try:
            # Phase 1: File Analysis
            logger.info(_("🔍 Phase 1: File Risk Analysis"))
            analyzer.analyze_changed_files(
                report=self.report,
                log_step_callback=self._log_step,
                commit_hash=self.commit_hash,
                repository_path=self.repository_path,
                dry_run=self.dry_run,
            )

            # Phase 2: Code Quality Checks
            logger.info(_("🔧 Phase 2: Code Quality Checks"))
            quality_passed = runner.run_code_quality_checks(
                log_step_callback=self._log_step,
                repository_path=self.repository_path,
                dry_run=self.dry_run,
            )

            # Phase 3: Test Execution
            logger.info(_("🧪 Phase 3: Test Execution"))
            tests_passed = runner.run_tests(
                log_step_callback=self._log_step,
                repository_path=self.repository_path,
                dry_run=self.dry_run,
            )

            # Phase 4: Generate Suggestions
            logger.info(_("💡 Phase 4: Recovery Suggestions"))
            suggestions = reporter.generate_recovery_suggestions(report=self.report)

            for suggestion in suggestions:
                logger.info(f"   • {suggestion}")

            # Determine final status
            if quality_passed and tests_passed:
                self.report.final_status = RecoveryStatus.SUCCESS
                logger.info(_("✅ Recovery completed successfully"))
                success = True
            elif quality_passed or tests_passed:
                self.report.final_status = RecoveryStatus.PARTIAL_SUCCESS
                logger.warning(_("⚠️ Recovery partially successful"))
                success = False
            else:
                self.report.final_status = RecoveryStatus.FAILED
                logger.error(_("❌ Recovery failed"))
                success = False

            # Calculate total duration
            end_time = datetime.now()
            self.report.total_duration_seconds = (end_time - start_time).total_seconds()

            # Save report
            reporter.save_report(
                report=self.report,
                repository_path=self.repository_path,
                commit_hash=self.commit_hash,
            )

            logger.info("=" * 70)
            logger.info(
                _("🎯 CI Recovery completed in {duration:.2fs}").format(
                    duration=self.report.total_duration_seconds,
                ),
            )

            return success

        except Exception as e:
            logger.error(f"Recovery process failed with exception: {e}")
            self.report.final_status = RecoveryStatus.FAILED
            self._log_step(
                "Recovery Process",
                RecoveryStatus.FAILED,
                error_message=str(e),
            )

            try:
                reporter.save_report(
                    report=self.report,
                    repository_path=self.repository_path,
                    commit_hash=self.commit_hash,
                )
            except Exception:
                logger.error("Failed to save error report")

            return False


def main() -> None:
    """Main entry point for the CI recovery system."""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Professional CI/CD Failure Recovery System",
    )
    parser.add_argument(
        "--commit",
        help="Specific commit hash to analyze (defaults to HEAD)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operations without making changes",
    )
    parser.add_argument(
        "--repository",
        type=Path,
        help="Path to git repository (defaults to current directory)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level",
    )

    args = parser.parse_args()

    # Configure logging level
    log_level = getattr(logging, args.log_level)
    logging.getLogger().setLevel(log_level)

    # Check for environment variable overrides
    dry_run = args.dry_run or os.getenv("CI_RECOVERY_DRY_RUN", "").lower() == "true"

    try:
        recovery_system = CIFailureRecoverySystem(
            repository_path=args.repository,
            commit_hash=args.commit,
            dry_run=dry_run,
        )

        success = recovery_system.execute_recovery()
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Failed to initialize recovery system: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
