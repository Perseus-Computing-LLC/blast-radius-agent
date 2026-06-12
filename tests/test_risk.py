"""Deterministic boundary tests for risk classification (issues #6, #9)."""

import pytest

from blast_radius.config import RiskThresholds
from blast_radius.risk import RiskLevel, classify_risk

T = RiskThresholds()  # medium_min=3, high_min=11, critical_min=51


@pytest.mark.parametrize(
    "total,expected",
    [
        (0, RiskLevel.LOW),
        (2, RiskLevel.LOW),
        (3, RiskLevel.MEDIUM),   # inclusive lower bound, no overlap
        (10, RiskLevel.MEDIUM),  # was both Medium and High in old table
        (11, RiskLevel.HIGH),
        (50, RiskLevel.HIGH),    # was both High and Critical in old table
        (51, RiskLevel.CRITICAL),
        (500, RiskLevel.CRITICAL),
    ],
)
def test_single_classification_per_count(total, expected):
    assert classify_risk(total, 0, 1, thresholds=T) == expected


def test_every_count_has_exactly_one_level():
    for total in range(0, 120):
        level = classify_risk(total, 0, 1, thresholds=T)
        assert isinstance(level, RiskLevel)


def test_cross_project_forces_critical():
    # Small count, but spread across the cross-project critical threshold.
    assert classify_risk(2, 0, 3, thresholds=T) == RiskLevel.CRITICAL


def test_direct_plus_transitive_summed():
    assert classify_risk(6, 6, 1, thresholds=T) == RiskLevel.HIGH  # total 12


def test_thresholds_must_increase():
    with pytest.raises(ValueError):
        RiskThresholds(medium_min=10, high_min=10, critical_min=50)


def test_negative_counts_rejected():
    with pytest.raises(ValueError):
        classify_risk(-1, 0, 0, thresholds=T)
