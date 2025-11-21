"""Smart Git Synchronization Package.

A modular package for intelligent Git synchronization with preventive audit
capabilities, branch protection, and Pull Request automation.

Modules:
    exceptions: Custom exception classes
    models: Data models and classes
    config: Configuration management
    git_wrapper: Git operations wrapper
    branch_protector: Branch protection validation
    pr_manager: Pull Request management
    sync_logic: Synchronization orchestration
"""

__version__ = "2.0.0"
__author__ = "DevOps Engineering Team"

from scripts.git_sync.branch_protector import BranchProtector
from scripts.git_sync.exceptions import AuditError, GitOperationError, SyncError
from scripts.git_sync.git_wrapper import GitWrapper
from scripts.git_sync.models import SyncStep
from scripts.git_sync.pr_manager import PRManager

__all__ = [
    "AuditError",
    "BranchProtector",
    "GitOperationError",
    "GitWrapper",
    "PRManager",
    "SyncError",
    "SyncStep",
]
