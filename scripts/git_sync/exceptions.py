"""Custom exceptions for Smart Git Sync.

This module defines all custom exception classes used throughout the
git_sync package for precise error handling and reporting.
"""


class SyncError(Exception):
    """Base exception for synchronization errors.

    This is the parent class for all sync-related exceptions.
    Use this for general synchronization failures that don't fit
    into more specific categories.
    """


class GitOperationError(SyncError):
    """Exception for Git operation failures.

    Raised when Git commands fail, including:
    - Subprocess execution errors
    - Git command timeouts
    - Invalid Git state
    - Merge conflicts
    - Push/pull failures
    """


class AuditError(SyncError):
    """Exception for audit failures.

    Raised when code quality or security audits fail,
    particularly when strict_audit mode is enabled.
    """
