"""Blast Radius Analyzer — local engine.

A runnable implementation of the dependency blast-radius analysis described in
the project docs and skill. Wraps the Orbit CLI (`orbit sql`) in local mode and
implements cycle-safe, deduplicated, depth-accurate transitive traversal with
deterministic risk classification.
"""

from .config import Config, RiskThresholds
from .risk import RiskLevel, classify_risk
from .engine import BlastRadiusEngine, BlastRadiusReport, Dependent

__all__ = [
    "Config",
    "RiskThresholds",
    "RiskLevel",
    "classify_risk",
    "BlastRadiusEngine",
    "BlastRadiusReport",
    "Dependent",
]

__version__ = "0.1.0"
