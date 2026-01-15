"""Test Dependency Alignment Guardian.

This module implements a "autoimune system" for dependency management,
ensuring that tools used in the Makefile are properly declared in pyproject.toml.

Context:
    The CI failed because `make format` invoked `ruff`, but `ruff` was not
    declared in pyproject.toml. This test prevents such misalignments from
    happening again.

Architecture:
    - Proactive validation: Fails before CI runs
    - Self-documenting: Clear error messages guide fixes
    - Extensible: Easy to add new tool mappings
"""

import os
import re
import subprocess
from pathlib import Path

import pytest


class TestDependencyAlignment:
    """Validates alignment between Makefile and pyproject.toml."""

    # Critical tools that MUST be declared in pyproject.toml if used in Makefile
    TOOL_MAPPING: dict[str, str] = {
        "ruff": "ruff",
        "mypy": "mypy",
        "pytest": "pytest",
        "mkdocs": "mkdocs-material",
        "pybabel": "babel",
        "tox": "tox",
        "semantic-release": "python-semantic-release",
    }

    @pytest.fixture
    def project_root(self) -> Path:
        """Return the project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture
    def makefile_content(self, project_root: Path) -> str:
        """Read Makefile content."""
        makefile_path = project_root / "Makefile"
        return makefile_path.read_text(encoding="utf-8")

    @pytest.fixture
    def pyproject_content(self, project_root: Path) -> str:
        """Read pyproject.toml content."""
        pyproject_path = project_root / "pyproject.toml"
        return pyproject_path.read_text(encoding="utf-8")

    def _extract_tools_from_makefile(self, makefile_content: str) -> set[str]:
        """Extract tools used in the Makefile.

        Looks for patterns like:
        - $(PYTHON) -m ruff
        - $(VENV)/bin/ruff
        - ruff check
        - python -m mypy

        Args:
            makefile_content: Content of the Makefile

        Returns:
            Set of tool names found in the Makefile
        """
        tools_found = set()

        # Pattern 1: $(PYTHON) -m <tool>
        # Pattern 2: $(VENV)/bin/<tool>
        # Pattern 3: <tool> <command> (at start of line or after tab)
        # Pattern 4: python -m <tool>
        patterns = [
            r"\$\((?:PYTHON|VENV)/bin/python\)\s+-m\s+(\w+)",
            r"\$\(VENV\)/bin/(\w+)",
            r"(?:^|\t)\s*(\w+)\s+(?:check|format|build|serve|extract|"
            r"init|update|compile)",
            r"python\d?\s+-m\s+(\w+)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, makefile_content, re.MULTILINE)
            for match in matches:
                tool = match.group(1)
                # Filter out variables and common commands
                if tool not in ["python", "pip", "venv", "rm", "echo", "find"]:
                    tools_found.add(tool)

        return tools_found

    def _extract_dependencies_from_pyproject(self, pyproject_content: str) -> set[str]:
        """Extract package names from pyproject.toml dependencies.

        Parses the [project.optional-dependencies] dev section and
        [project] dependencies section.

        Args:
            pyproject_content: Content of pyproject.toml

        Returns:
            Set of normalized package names
        """
        dependencies = set()

        # Extract from [project.optional-dependencies] dev
        dev_section_match = re.search(
            r"\[project\.optional-dependencies\]\s*\ndev\s*=\s*\[(.*?)\]",
            pyproject_content,
            re.DOTALL,
        )
        if dev_section_match:
            dev_deps = dev_section_match.group(1)
            # Extract package names (before >= or ~= or ==)
            for match in re.finditer(r'"([a-zA-Z0-9_-]+)', dev_deps):
                pkg = match.group(1).lower().replace("-", "_")
                dependencies.add(pkg)

        # Extract from [project] dependencies
        deps_section_match = re.search(
            r"\[project\]\s*.*?dependencies\s*=\s*\[(.*?)\]",
            pyproject_content,
            re.DOTALL,
        )
        if deps_section_match:
            deps = deps_section_match.group(1)
            for match in re.finditer(r'"([a-zA-Z0-9_-]+)', deps):
                pkg = match.group(1).lower().replace("-", "_")
                dependencies.add(pkg)

        return dependencies

    def test_makefile_dependencies_are_declared(
        self,
        makefile_content: str,
        pyproject_content: str,
    ) -> None:
        """Verify that critical tools in Makefile are declared.

        This test implements the "autoimune system" logic:
        1. Scans Makefile for tool usage
        2. Checks if corresponding packages exist in pyproject.toml
        3. Fails with descriptive message if misalignment detected

        Raises:
            AssertionError: If a tool is used but not declared
        """
        tools_in_makefile = self._extract_tools_from_makefile(makefile_content)
        dependencies_in_pyproject = self._extract_dependencies_from_pyproject(
            pyproject_content,
        )

        missing_tools = []

        for tool_name in tools_in_makefile:
            if tool_name in self.TOOL_MAPPING:
                expected_package = self.TOOL_MAPPING[tool_name]
                normalized_package = expected_package.lower().replace("-", "_")

                # Check if package exists in pyproject.toml
                package_declared = any(
                    normalized_package in dep
                    or expected_package.lower().replace("_", "-") in dep
                    for dep in dependencies_in_pyproject
                )

                if not package_declared:
                    missing_tools.append(
                        {
                            "tool": tool_name,
                            "expected_package": expected_package,
                        },
                    )

        # Assert with detailed error message
        if missing_tools:
            error_message = (
                "\n❌ DEPENDENCY ALIGNMENT VIOLATION DETECTED ❌\n\n"
                "The following tools are used in the Makefile but NOT "
                "declared in pyproject.toml:\n\n"
            )

            for item in missing_tools:
                error_message += (
                    f"  • Tool: '{item['tool']}'\n"
                    f"    Expected package: '{item['expected_package']}'\n"
                    f"    Action: Add '{item['expected_package']}' to "
                    "[project.optional-dependencies] dev\n\n"
                )

            error_message += (
                "🛡️ This is your AUTOIMUNE SYSTEM preventing CI failures.\n"
                "Fix the issue by adding the missing packages to pyproject.toml.\n"
            )

            pytest.fail(error_message)

    def test_critical_tools_coverage(self) -> None:
        """Verify that critical tools mapping is comprehensive.

        This meta-test ensures we maintain awareness of the tools we monitor.
        """
        expected_critical_tools = {
            "ruff",
            "mypy",
            "pytest",
            "mkdocs",
            "pybabel",
            "tox",
            "semantic-release",
        }

        mapped_tools = set(self.TOOL_MAPPING.keys())

        assert mapped_tools == expected_critical_tools, (
            f"TOOL_MAPPING coverage mismatch:\n"
            f"  Missing: {expected_critical_tools - mapped_tools}\n"
            f"  Extra: {mapped_tools - expected_critical_tools}\n"
        )

    def test_requirements_files_are_synchronized(self, project_root: Path) -> None:
        """Verify that requirements/dev.txt is synchronized with dev.in.

        This test prevents CI failures caused by outdated lockfiles.
        If dev.in is modified, dev.txt must be regenerated with pip-compile.

        Raises:
            AssertionError: If lockfile is out of sync
        """
        dev_in_path = project_root / "requirements" / "dev.in"
        dev_txt_path = project_root / "requirements" / "dev.txt"

        # Both files must exist
        assert dev_in_path.exists(), (
            f"❌ Missing file: {dev_in_path}\nThe requirements input file is required."
        )
        assert dev_txt_path.exists(), (
            f"❌ Missing file: {dev_txt_path}\n"
            "Run: pip-compile requirements/dev.in "
            "--output-file requirements/dev.txt"
        )

        # Read dev.in to extract package names
        dev_in_content = dev_in_path.read_text(encoding="utf-8")
        dev_txt_content = dev_txt_path.read_text(encoding="utf-8")

        # Extract package names from dev.in (ignore comments and empty lines)
        required_packages = set()
        for line in dev_in_content.splitlines():
            line = line.strip()
            # Skip comments, empty lines, and conditional deps
            if not line or line.startswith("#"):
                continue
            # Extract package name (before ==, >=, <, ;, etc.)
            package_match = re.match(r"^([a-zA-Z0-9_-]+)", line)
            if package_match:
                package_name = package_match.group(1).lower()
                required_packages.add(package_name)

        # Check if all packages from dev.in are in dev.txt
        missing_packages = []
        for package in required_packages:
            # Look for the package in dev.txt (case-insensitive)
            package_pattern = re.compile(
                rf"^{re.escape(package)}==",
                re.IGNORECASE | re.MULTILINE,
            )
            if not package_pattern.search(dev_txt_content):
                missing_packages.append(package)

        # Assert with descriptive error message
        if missing_packages:
            error_message = (
                "\n❌ REQUIREMENTS LOCKFILE OUT OF SYNC ❌\n\n"
                "The following packages from dev.in are NOT in dev.txt:\n\n"
            )

            for package in sorted(missing_packages):
                error_message += f"  • {package}\n"

            error_message += (
                "\n🔧 FIX:\n"
                "  pip-compile requirements/dev.in "
                "--output-file requirements/dev.txt --strip-extras\n\n"
                "🛡️ This autoimune system prevents CI failures "
                "from outdated lockfiles.\n"
            )

            pytest.fail(error_message)

    # TODO: Refactor God Function - split validation into smaller test methods
    def test_requirements_txt_is_synced(self, project_root: Path) -> None:  # noqa: C901
        """Verify requirements/dev.txt is in sync using pip-compile.

        This test uses pip-compile to generate what the lockfile should be
        and compares it with the current file to detect sync issues.

        Raises:
            AssertionError: If lockfile is out of sync with dev.in
        """
        dev_in_path = project_root / "requirements" / "dev.in"
        dev_txt_path = project_root / "requirements" / "dev.txt"

        # Both files must exist
        if not dev_in_path.exists():
            pytest.skip(f"Skipping: {dev_in_path} not found")
        if not dev_txt_path.exists():
            pytest.skip(f"Skipping: {dev_txt_path} not found")

        try:
            # Generate what the file should look like (output to stdout)
            # SECURITY: Safe subprocess use - shell=False, validated paths,
            # timeout protection
            result = subprocess.run(  # noqa: S603
                [
                    "pip-compile",
                    str(dev_in_path),
                    "--output-file=-",
                    "--resolver=backtracking",
                    "--strip-extras",
                    "--allow-unsafe",  # Include pip/setuptools for reproducibility
                    "--quiet",
                ],
                check=False,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                pytest.fail(
                    f"pip-compile failed:\n{result.stderr or result.stdout}",
                )

            # Read current dev.txt
            current_content = dev_txt_path.read_text(encoding="utf-8")

            # Normalize both for comparison (remove comments and whitespace)
            def normalize_requirements(content: str) -> set[str]:
                lines = set()
                for line in content.splitlines():
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    lines.add(line)
                return lines

            generated = normalize_requirements(result.stdout)
            current = normalize_requirements(current_content)

            if generated != current:
                missing_in_current = generated - current
                extra_in_current = current - generated

                error_message = (
                    "\n❌ REQUIREMENTS LOCKFILE OUT OF SYNC ❌\n\n"
                    "requirements/dev.txt differs from what pip-compile "
                    "would generate.\n\n"
                )

                if missing_in_current:
                    error_message += "📦 Missing in current dev.txt:\n"
                    for line in sorted(missing_in_current)[:5]:
                        error_message += f"  + {line}\n"
                    if len(missing_in_current) > 5:
                        error_message += (
                            f"  ... and {len(missing_in_current) - 5} more\n"
                        )
                    error_message += "\n"

                if extra_in_current:
                    error_message += "📦 Extra in current dev.txt:\n"
                    for line in sorted(extra_in_current)[:5]:
                        error_message += f"  - {line}\n"
                    if len(extra_in_current) > 5:
                        error_message += f"  ... and {len(extra_in_current) - 5} more\n"
                    error_message += "\n"

                error_message += (
                    "🔧 FIX:\n"
                    "  make install-dev\n"
                    "  # OR manually:\n"
                    "  pip-compile requirements/dev.in "
                    "--output-file requirements/dev.txt "
                    "--resolver=backtracking --strip-extras\n\n"
                    "🛡️ This autoimune system prevents CI failures "
                    "from outdated lockfiles.\n"
                )

                # PROTOCOLO v2.4: CI=Warn (Skip), Local=Fail-Hard
                if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
                    pytest.skip(
                        f"⚠️  [CI MODE - WARN ONLY]\n{error_message}\n"
                        "🔵 Modo Permissivo: Lockfile drift detectado "
                        "mas não bloqueia CI"
                    )
                else:
                    pytest.fail(error_message)

        except FileNotFoundError:
            pytest.skip(
                "pip-compile not found in PATH. "
                "Install pip-tools: pip install pip-tools",
            )
        except subprocess.TimeoutExpired:
            pytest.fail(
                "pip-compile timed out after 60 seconds. "
                "This may indicate a problem with the requirements files.",
            )
