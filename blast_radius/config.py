"""Configuration loading for the Blast Radius engine.

Reads from environment variables (optionally populated from a .env file) so the
documented .env.example keys actually drive behavior. See issue #4.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no external dependency).

    Only sets keys that are not already present in the environment, so real
    environment variables always win over the file.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class RiskThresholds:
    """Deterministic, non-overlapping risk boundaries.

    Boundaries are interpreted as inclusive lower bounds for the *next* level,
    so there is exactly one classification for any integer count. See issue #6.
    """

    # A total dependent count strictly below medium_min is Low.
    medium_min: int = 3
    high_min: int = 11
    critical_min: int = 51

    def __post_init__(self) -> None:
        if not (self.medium_min < self.high_min < self.critical_min):
            raise ValueError(
                "Risk thresholds must be strictly increasing: "
                f"medium_min={self.medium_min}, high_min={self.high_min}, "
                f"critical_min={self.critical_min}"
            )

    @classmethod
    def from_env(cls) -> "RiskThresholds":
        # Backwards compatible with the legacy RISK_*_THRESHOLD names while
        # treating them as the inclusive lower bound of the named level.
        medium = int(os.environ.get("RISK_MEDIUM_THRESHOLD", "3"))
        high = int(os.environ.get("RISK_HIGH_THRESHOLD", "11"))
        critical = int(os.environ.get("RISK_CRITICAL_THRESHOLD", "51"))
        return cls(medium_min=medium, high_min=high, critical_min=critical)


@dataclass(frozen=True)
class Config:
    orbit_mode: str = "local"
    orbit_cli_path: str = "orbit"
    gitlab_url: str = "https://gitlab.com"
    gitlab_token: Optional[str] = None
    max_depth: int = 3
    exclude_patterns: List[str] = field(default_factory=list)
    thresholds: RiskThresholds = field(default_factory=RiskThresholds)
    cross_project_critical: int = 3
    max_dependents: int = 0  # 0 = no cap; set to short-circuit at N dependents

    @classmethod
    def load(cls, dotenv_path: Optional[str] = None) -> "Config":
        if dotenv_path:
            _load_dotenv(Path(dotenv_path))
        else:
            default = Path(".env")
            if default.exists():
                _load_dotenv(default)

        excludes_raw = os.environ.get(
            "EXCLUDE_PATTERNS",
            "*test*,*spec*,*.generated.*,__generated__/*,node_modules/*,.venv/*",
        )
        excludes = [p.strip() for p in excludes_raw.split(",") if p.strip()]

        return cls(
            orbit_mode=os.environ.get("ORBIT_MODE", "local"),
            orbit_cli_path=os.environ.get("ORBIT_CLI_PATH", "orbit"),
            gitlab_url=os.environ.get("GITLAB_URL", "https://gitlab.com"),
            gitlab_token=os.environ.get("GITLAB_TOKEN") or None,
            max_depth=int(os.environ.get("BLAST_RADIUS_MAX_DEPTH", "3")),
            max_dependents=int(os.environ.get("BLAST_RADIUS_MAX_DEPENDENTS", "0")),
            exclude_patterns=excludes,
            thresholds=RiskThresholds.from_env(),
            cross_project_critical=int(
                os.environ.get("RISK_CROSS_PROJECT_CRITICAL", "3")
            ),
        )
