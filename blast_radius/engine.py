"""Blast Radius traversal engine.

Implements the corrected algorithm:

  - Exact-aware target resolution with explicit zero/multiple-match handling
    (issue #7).
  - Cycle-safe, deduplicated, depth-accurate BFS where `visited` is seeded with
    the target AND each level is filtered before recursion, so counts are not
    inflated and cycles cannot loop forever (issue #8).
  - Exclude-pattern filtering for tests/generated code.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set

from .config import Config
from .orbit_client import OrbitClient
from .risk import RiskLevel, classify_risk


class TargetResolutionError(Exception):
    """Raised when a target cannot be resolved to exactly one definition set."""

    def __init__(self, message: str, candidates: Optional[List[dict]] = None) -> None:
        super().__init__(message)
        self.candidates = candidates or []


@dataclass
class Dependent:
    id: int
    name: str
    path: str
    language: str
    project_path: str
    depth: int  # 1 = direct, 2+ = transitive

    @classmethod
    def from_row(cls, row: dict, depth: int) -> "Dependent":
        return cls(
            id=int(row["id"]),
            name=row.get("name", ""),
            path=row.get("path", ""),
            language=row.get("language", ""),
            project_path=row.get("project_path", ""),
            depth=depth,
        )


@dataclass
class BlastRadiusReport:
    target_path: str
    target_name: Optional[str]
    direct: List[Dependent] = field(default_factory=list)
    transitive: List[Dependent] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    risk: RiskLevel = RiskLevel.LOW
    max_depth: int = 3

    @property
    def total_dependents(self) -> int:
        return len(self.direct) + len(self.transitive)


class BlastRadiusEngine:
    def __init__(self, client: OrbitClient, config: Optional[Config] = None) -> None:
        self.client = client
        self.config = config or Config()

    def _excluded(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pat) for pat in self.config.exclude_patterns)

    def resolve_target(
        self, path: Optional[str], name: Optional[str]
    ) -> List[dict]:
        """Resolve a target to its definition rows.

        Raises TargetResolutionError on zero matches, or on multiple matches
        across distinct files when no function name was given to disambiguate.
        """
        if not path and not name:
            raise TargetResolutionError("Provide a file path and/or a function name.")

        matches = self.client.find_definitions(path=path, name=name)
        if not matches:
            raise TargetResolutionError(
                f"No definition matched path={path!r} name={name!r}.", candidates=[]
            )

        distinct_paths = {m["path"] for m in matches}
        # Ambiguous only when the path resolves to multiple distinct files and
        # the caller did not pin a specific function name.
        if len(distinct_paths) > 1 and not name:
            raise TargetResolutionError(
                "Target is ambiguous across multiple files; pass a function "
                "name or a more specific path.",
                candidates=matches,
            )
        return matches

    def analyze(
        self, path: Optional[str] = None, name: Optional[str] = None
    ) -> BlastRadiusReport:
        targets = self.resolve_target(path, name)
        target_ids = {int(t["id"]) for t in targets}

        visited: Set[int] = set(target_ids)
        report = BlastRadiusReport(
            target_path=path or (targets[0]["path"] if targets else ""),
            target_name=name,
            max_depth=self.config.max_depth,
        )

        # Level 1: direct dependents.
        frontier: Set[int] = set()
        for row in self.client.dependents_of(target_ids):
            did = int(row["id"])
            if did in visited or self._excluded(row.get("path", "")):
                continue
            visited.add(did)
            frontier.add(did)
            report.direct.append(Dependent.from_row(row, depth=1))

        # Levels 2..max_depth: transitive dependents (BFS, cycle-safe).
        depth = 2
        while frontier and depth <= self.config.max_depth:
            next_frontier: Set[int] = set()
            for row in self.client.dependents_of(frontier):
                did = int(row["id"])
                if did in visited or self._excluded(row.get("path", "")):
                    continue
                visited.add(did)
                next_frontier.add(did)
                report.transitive.append(Dependent.from_row(row, depth=depth))
            frontier = next_frontier
            depth += 1

        report.projects = self._distinct_projects(report.direct + report.transitive)
        report.risk = classify_risk(
            direct_count=len(report.direct),
            transitive_count=len(report.transitive),
            project_count=len(report.projects),
            thresholds=self.config.thresholds,
            cross_project_critical=self.config.cross_project_critical,
        )
        return report

    @staticmethod
    def _distinct_projects(deps: Sequence[Dependent]) -> List[str]:
        seen: Dict[str, None] = {}
        for d in deps:
            if d.project_path:
                seen.setdefault(d.project_path, None)
        return list(seen.keys())
