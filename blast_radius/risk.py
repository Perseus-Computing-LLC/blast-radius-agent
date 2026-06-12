"""Deterministic risk classification.

Fixes the overlapping thresholds described in issue #6. The previous table made
e.g. exactly 10 dependents both Medium and High. Here, a single total count maps
to exactly one level via inclusive lower bounds.
"""

from __future__ import annotations

import enum

from .config import RiskThresholds


class RiskLevel(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


def classify_risk(
    direct_count: int,
    transitive_count: int,
    project_count: int,
    thresholds: RiskThresholds | None = None,
    cross_project_critical: int = 3,
) -> RiskLevel:
    """Classify blast-radius risk from dependent counts.

    Rules (deterministic, non-overlapping):
      - Total = direct + transitive dependents.
      - total >= critical_min            -> Critical
      - project_count >= cross_project_critical -> Critical (shared hub)
      - total >= high_min                -> High
      - total >= medium_min              -> Medium
      - otherwise                        -> Low
    """
    if thresholds is None:
        thresholds = RiskThresholds()

    if direct_count < 0 or transitive_count < 0 or project_count < 0:
        raise ValueError("counts must be non-negative")

    total = direct_count + transitive_count

    if total >= thresholds.critical_min:
        return RiskLevel.CRITICAL
    if project_count >= cross_project_critical:
        return RiskLevel.CRITICAL
    if total >= thresholds.high_min:
        return RiskLevel.HIGH
    if total >= thresholds.medium_min:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
