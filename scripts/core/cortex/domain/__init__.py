"""CORTEX Domain Layer.

This package contains the core domain models for the CORTEX system,
following the Hexagonal Architecture (Ports & Adapters) pattern.

Domain models are pure data structures with minimal behavior,
free from external dependencies and infrastructure concerns.
"""

from scripts.core.cortex.domain.validator_types import (
    AnomalyReport,
    BrokenLinkDetail,
    HealthMetrics,
    NodeRanking,
    ValidationReport,
)

__all__ = [
    "AnomalyReport",
    "BrokenLinkDetail",
    "HealthMetrics",
    "NodeRanking",
    "ValidationReport",
]
