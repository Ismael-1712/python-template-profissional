"""Security utilities for safe subprocess execution.

This module provides functions for sanitizing environment variables
and other security-related operations to prevent data leakage.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def sanitize_env(original_env: dict[str, str]) -> dict[str, str]:
    """Sanitize environment variables to prevent leaking sensitive data.

    Implements a whitelist-based approach with explicit blocklist for secrets.
    Only safe and necessary variables are propagated to subprocesses.

    Args:
        original_env: Original environment dictionary from os.environ

    Returns:
        Sanitized environment dictionary safe for subprocess execution

    Security:
        - Blocks: TOKEN, KEY, SECRET, PASSWORD, CREDENTIAL, API patterns
        - Allows: Essential system vars + Safe Python-specific vars
        - Hardened: Only explicitly safe PYTHON* vars (no PYTHONSTARTUP)

    Examples:
        >>> import os
        >>> env = {"PATH": "/usr/bin", "MY_TOKEN": "secret123"}
        >>> safe_env = sanitize_env(env)
        >>> "PATH" in safe_env
        True
        >>> "MY_TOKEN" in safe_env
        False
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

    # Hardened Python variables (explicit safe list)
    # PYTHONSTARTUP, PYTHONHOME, PYTHONINSPECT deliberately excluded
    safe_python_vars = {
        "PYTHONPATH",  # Already in allowed_keys, but explicit here
        "PYTHONUNBUFFERED",
        "PYTHONHASHSEED",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONIOENCODING",
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

        # Allow only explicitly safe Python variables (HARDENED)
        if key in safe_python_vars:
            sanitized[key] = value
            continue

        # Allow PY* prefix (shorter Python vars like PYTEST_*)
        if key.startswith("PY") and not key.startswith("PYTHON"):
            sanitized[key] = value
            continue

        # Implicitly deny everything else (Least Privilege principle)
        logger.debug("Filtered environment variable: %s", key)

    return sanitized
