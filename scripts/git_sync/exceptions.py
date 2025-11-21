"""Custom exceptions for the Git synchronization system."""


class SyncError(Exception):
    """Base exception for synchronization errors."""


class GitOperationError(SyncError):
    """Exception for Git operation failures."""


class AuditError(SyncError):
    """Exception for audit failures."""
