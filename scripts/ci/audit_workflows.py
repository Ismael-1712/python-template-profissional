#!/usr/bin/env python3
"""GitHub Actions Workflow Auditor.

Validates GitHub Actions workflows for:
1. Modernidade: Proíbe Actions obsoletas (Node 16: v1/v2/v3)
2. Cache Limpo: Detecta conflitos entre cache automático e manual

Exit codes:
    0: All workflows compliant
    1: Violations detected
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Violation:
    """Workflow validation violation."""

    file: str
    job: str
    step: str
    rule: str
    message: str


class WorkflowAuditor:
    """Auditor for GitHub Actions workflows."""

    # Actions que devem usar v4 ou v5 (Node 20+)
    REQUIRED_MODERN_ACTIONS = {
        "actions/checkout": {"min_version": 4, "name": "checkout"},
        "actions/setup-python": {"min_version": 5, "name": "setup-python"},
        "actions/cache": {"min_version": 4, "name": "cache"},
    }

    def __init__(self, workflows_dir: Path) -> None:
        """Initialize auditor.

        Args:
            workflows_dir: Path to .github/workflows directory
        """
        self.workflows_dir = workflows_dir
        self.violations: list[Violation] = []

    def audit_all(self) -> bool:
        """Audit all workflow files.

        Returns:
            True if all workflows are compliant, False otherwise
        """
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(
            self.workflows_dir.glob("*.yaml"),
        )

        if not workflow_files:
            print("⚠️  Warning: No workflow files found")
            return True

        for workflow_file in workflow_files:
            self._audit_file(workflow_file)

        return len(self.violations) == 0

    def _audit_file(self, file_path: Path) -> None:
        """Audit a single workflow file.

        Args:
            file_path: Path to workflow file
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                workflow = yaml.safe_load(f)
        except Exception as e:
            self.violations.append(
                Violation(
                    file=file_path.name,
                    job="N/A",
                    step="N/A",
                    rule="PARSE_ERROR",
                    message=f"Failed to parse YAML: {e}",
                ),
            )
            return

        if not isinstance(workflow, dict) or "jobs" not in workflow:
            return

        for job_name, job_config in workflow["jobs"].items():
            self._audit_job(file_path.name, job_name, job_config)

    def _audit_job(
        self,
        file_name: str,
        job_name: str,
        job_config: dict[str, Any],
    ) -> None:
        """Audit a single job.

        Args:
            file_name: Name of workflow file
            job_name: Name of job
            job_config: Job configuration dictionary
        """
        if "steps" not in job_config:
            return

        cache_info = self._analyze_cache_strategy(job_config["steps"])
        self._check_cache_conflicts(file_name, job_name, cache_info)

        # Verificar versões de actions em cada step
        for step_idx, step in enumerate(job_config["steps"]):
            if not isinstance(step, dict):
                continue

            step_name = step.get("name", f"Step {step_idx + 1}")
            uses = step.get("uses", "")
            self._check_action_version(file_name, job_name, step_name, uses)

    def _analyze_cache_strategy(
        self,
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze caching strategy in job steps.

        Args:
            steps: List of job steps

        Returns:
            Dictionary with cache analysis results
        """
        has_setup_python_cache = False
        has_manual_pip_cache = False
        setup_python_step = None

        for step_idx, step in enumerate(steps):
            if not isinstance(step, dict):
                continue

            step_name = step.get("name", f"Step {step_idx + 1}")
            uses = step.get("uses", "")

            # Rastrear configuração de cache
            if "actions/setup-python" in uses:
                setup_python_step = step_name
                with_config = step.get("with", {})
                if with_config.get("cache") == "pip":
                    has_setup_python_cache = True

            if "actions/cache" in uses:
                path = step.get("with", {}).get("path", "")
                if self._is_pip_cache_path(path):
                    has_manual_pip_cache = True

        return {
            "has_setup_python_cache": has_setup_python_cache,
            "has_manual_pip_cache": has_manual_pip_cache,
            "setup_python_step": setup_python_step,
        }

    def _is_pip_cache_path(self, path: str) -> bool:
        """Check if path is a pip cache path.

        Args:
            path: Cache path string

        Returns:
            True if path is for pip cache
        """
        patterns = ["~/.cache/pip", ".cache/pip", "pip", "wheels"]
        return any(pattern in path for pattern in patterns)

    def _check_cache_conflicts(
        self,
        file_name: str,
        job_name: str,
        cache_info: dict[str, Any],
    ) -> None:
        """Check for cache conflicts.

        Args:
            file_name: Name of workflow file
            job_name: Name of job
            cache_info: Cache analysis results
        """
        if cache_info["has_setup_python_cache"] and cache_info["has_manual_pip_cache"]:
            self.violations.append(
                Violation(
                    file=file_name,
                    job=job_name,
                    step=cache_info["setup_python_step"] or "setup-python",
                    rule="CACHE_CONFLICT",
                    message=(
                        "Cache conflict detected: setup-python has 'cache: pip' "
                        "AND manual actions/cache for pip. Use only ONE strategy."
                    ),
                ),
            )

    def _check_action_version(
        self,
        file_name: str,
        job_name: str,
        step_name: str,
        uses: str,
    ) -> None:
        """Check if action uses modern version.

        Args:
            file_name: Name of workflow file
            job_name: Name of job
            step_name: Name of step
            uses: Action 'uses' string
        """
        for action_name, requirements in self.REQUIRED_MODERN_ACTIONS.items():
            if action_name not in uses:
                continue

            # Extrair versão (formato: owner/action@vX ou owner/action@commitsha)
            if "@" not in uses:
                continue

            version_part = uses.split("@")[1]

            # Se for SHA de commit (40 chars hex), permitir
            if len(version_part) == 40 and all(
                c in "0123456789abcdef" for c in version_part.lower()
            ):
                continue

            # Validar versão tag (v1, v2, v3, v4, v5)
            if not version_part.startswith("v"):
                continue

            try:
                major_version = int(version_part[1:].split(".")[0])
            except (ValueError, IndexError):
                continue

            min_version: int = requirements["min_version"]  # type: ignore[assignment]
            if major_version < min_version:
                self.violations.append(
                    Violation(
                        file=file_name,
                        job=job_name,
                        step=step_name,
                        rule="OBSOLETE_ACTION",
                        message=(
                            f"{requirements['name']} uses obsolete "
                            f"version {version_part} (requires v{min_version}+). "
                            f"Upgrade to avoid Node 16 deprecation."
                        ),
                    ),
                )

    def print_violations(self) -> None:
        """Print all violations to stderr."""
        if not self.violations:
            print("✅ All workflows are compliant")
            return

        print("❌ Workflow violations detected:\n", file=sys.stderr)

        for violation in self.violations:
            print(
                f"  • {violation.file} → {violation.job} → {violation.step}",
                file=sys.stderr,
            )
            print(f"    Rule: {violation.rule}", file=sys.stderr)
            print(f"    {violation.message}\n", file=sys.stderr)

        print(
            f"Total violations: {len(self.violations)}",
            file=sys.stderr,
        )


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = success, 1 = violations found)
    """
    workflows_dir = Path(".github/workflows")

    if not workflows_dir.exists():
        print(
            f"⚠️  Warning: {workflows_dir} not found. Skipping workflow audit.",
            file=sys.stderr,
        )
        return 0

    print("🔍 Auditing GitHub Actions workflows...")

    auditor = WorkflowAuditor(workflows_dir)
    is_compliant = auditor.audit_all()

    auditor.print_violations()

    return 0 if is_compliant else 1


if __name__ == "__main__":
    sys.exit(main())
