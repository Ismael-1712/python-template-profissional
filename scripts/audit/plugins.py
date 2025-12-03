"""Audit plugins for external dependency analysis.

This module provides plugin functions for analyzing test coverage
and simulating CI environments.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _sanitize_env(original_env: dict[str, str]) -> dict[str, str]:
    """Sanitize environment variables to prevent leaking sensitive data.

    Implements a whitelist-based approach with explicit blocklist for secrets.
    Only safe and necessary variables are propagated to subprocesses.

    Args:
        original_env: Original environment dictionary from os.environ

    Returns:
        Sanitized environment dictionary safe for subprocess execution

    Security:
        - Blocks: TOKEN, KEY, SECRET, PASSWORD, CREDENTIAL patterns
        - Allows: Essential system vars + Python-specific vars
    """
    # Whitelist: Essential system and Python variables
    allowed_keys = {
        "PATH",
        "PYTHONPATH",
        "HOME",
        "LANG",
        "LC_ALL",
        "TZ",
        "USER",
        "VIRTUAL_ENV",
        "TMPDIR",
        "TEMP",
        "TMP",
    }

    # Blocklist patterns for sensitive data (case-insensitive)
    blocked_patterns = ("TOKEN", "KEY", "SECRET", "PASSWORD", "CREDENTIAL", "API")

    sanitized: dict[str, str] = {}

    for key, value in original_env.items():
        # Explicit block: reject any key containing sensitive patterns
        if any(pattern in key.upper() for pattern in blocked_patterns):
            logger.debug("Blocked sensitive environment variable: %s", key)
            continue

        # Allow whitelisted keys
        if key in allowed_keys:
            sanitized[key] = value
            continue

        # Allow Python-specific variables (PYTHON*, PY*)
        if key.startswith(("PYTHON", "PY")):
            sanitized[key] = value
            continue

        # Implicitly deny everything else (Least Privilege principle)
        logger.debug("Filtered environment variable: %s", key)

    return sanitized


def check_mock_coverage(
    workspace_root: Path,
    scan_paths: list[str],
) -> dict[str, Any]:
    """Analyze test files for proper mocking of external dependencies.

    Args:
        workspace_root: Root directory of the workspace
        scan_paths: List of paths to scan for test files

    Returns:
        Dictionary containing mock coverage statistics
    """
    test_files: list[Path] = []
    for scan_path in scan_paths:
        if "test" in scan_path.lower():
            test_dir = workspace_root / scan_path
            if test_dir.exists():
                test_files.extend(test_dir.rglob("test_*.py"))
                test_files.extend(test_dir.rglob("*_test.py"))

    mock_coverage: dict[str, Any] = {
        "total_test_files": len(test_files),
        "files_with_mocks": 0,
        "files_needing_mocks": [],
    }

    mock_indicators = [
        "@patch",
        "Mock()",
        "mocker.patch",
        "mock_",
        "pytest-httpx",
        "httpx_mock",
    ]
    external_indicators = ["requests.", "httpx.", "subprocess.", "socket."]

    for test_file in test_files:
        try:
            with test_file.open(encoding="utf-8") as f:
                content = f.read()

            has_external = any(
                indicator in content for indicator in external_indicators
            )
            has_mock = any(indicator in content for indicator in mock_indicators)

            if has_external and has_mock:
                mock_coverage["files_with_mocks"] += 1
            elif has_external and not has_mock:
                mock_coverage["files_needing_mocks"].append(
                    str(test_file.relative_to(workspace_root)),
                )

        except OSError:
            logger.exception("Error analyzing test file %s", test_file)

    return mock_coverage


def simulate_ci(
    workspace_root: Path,
    ci_timeout: int,
) -> dict[str, Any]:
    """Simulate CI environment by running critical tests.

    Args:
        workspace_root: Root directory of the workspace
        ci_timeout: Timeout in seconds for the CI simulation

    Returns:
        Dictionary containing CI simulation results
    """
    logger.info("Simulating CI environment...")

    # Security: Sanitize environment to prevent leaking sensitive credentials
    # Only safe, whitelisted variables are propagated to pytest subprocess
    ci_env = {
        **_sanitize_env(dict(os.environ)),
        "CI": "true",
        "PYTEST_TIMEOUT": str(ci_timeout),
    }

    try:
        # Run pytest with CI-appropriate flags
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--tb=short",
            "--maxfail=5",
            "--timeout=60",
            "--quiet",
            "tests/",
        ]

        result = subprocess.run(  # noqa: subprocess
            cmd,
            check=False,
            env=ci_env,
            shell=False,  # Security: prevent shell injection
            capture_output=True,
            text=True,
            timeout=ci_timeout,
            cwd=workspace_root,
        )

        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": "within_timeout",
        }

    except subprocess.TimeoutExpired:
        logger.exception("CI simulation timed out after %s seconds", ci_timeout)
        return {
            "exit_code": -1,
            "passed": False,
            "stdout": "",
            "stderr": f"Tests exceeded {ci_timeout}s timeout",
            "duration": "timeout",
        }
    except FileNotFoundError:
        logger.warning("pytest not found - skipping CI simulation")
        return {
            "exit_code": -2,
            "passed": False,
            "stdout": "",
            "stderr": "pytest not installed",
            "duration": "error",
        }
    except OSError:
        logger.exception("CI simulation failed")
        return {
            "exit_code": -3,
            "passed": False,
            "stdout": "",
            "stderr": "CI simulation error",
            "duration": "error",
        }
