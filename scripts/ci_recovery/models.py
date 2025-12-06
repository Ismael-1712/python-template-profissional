#!/usr/bin/env python3

"""Módulo de Modelos de Dados (Dataclasses e Enums).

Para o Sistema de Recuperação de CI.
(Extraído do monólito P8.1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class RecoveryStatus(Enum):
    """Recovery operation status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class RiskLevel(Enum):
    """File change risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RecoveryStep:
    """Represents a single recovery step."""

    name: str
    status: RecoveryStatus
    timestamp: datetime
    details: str = ""
    error_message: str = ""
    duration_seconds: float = 0.0


@dataclass
class FileRiskAnalysis:
    """Analysis of file changes and associated risks."""

    low_risk: list[str] = field(default_factory=list)
    medium_risk: list[str] = field(default_factory=list)
    high_risk: list[str] = field(default_factory=list)
    critical_risk: list[str] = field(default_factory=list)
    overall_risk: RiskLevel = RiskLevel.LOW


@dataclass
class RecoveryReport:
    """Complete recovery operation report."""

    timestamp: datetime
    commit_hash: str
    repository_path: Path
    steps: list[RecoveryStep] = field(default_factory=list)
    file_analysis: FileRiskAnalysis | None = None
    fixes_applied: list[str] = field(default_factory=list)
    final_status: RecoveryStatus = RecoveryStatus.PENDING
    total_duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
