"""Orbit graph client.

Defines the tool contract the engine relies on (issue #5) and provides two
implementations:

  - OrbitCLIClient: shells out to `orbit sql` and parses JSON rows.
  - InMemoryOrbitClient: a fixture-backed client used by tests and for offline
    demos, implementing the exact same contract.

Contract (see docs/ORBIT_CONTRACT.md):
  A graph node (gl_definition) is a dict with at least:
      id (int), name (str), path (str), language (str), project_path (str)
  An edge (gl_reference) is a dict with at least:
      source_id (int), target_id (int), relationship_type (str)
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Dict, Iterable, List, Optional, Protocol


class OrbitClient(Protocol):
    """The minimal interface the engine depends on."""

    def find_definitions(
        self, path: Optional[str] = None, name: Optional[str] = None
    ) -> List[dict]:
        """Return gl_definition rows matching path and/or name (exact-aware)."""
        ...

    def dependents_of(self, target_ids: Iterable[int]) -> List[dict]:
        """Return gl_definition rows that reference any of target_ids (reverse edge)."""
        ...


def _sql_literal(value: str) -> str:
    """Escape a string for safe inclusion in a single-quoted SQL literal."""
    return value.replace("'", "''")


def _escape_like(value: str) -> str:
    """Escape LIKE metacharacters and return (escaped_value, escape_char)."""
    # B-1: LIKE wildcards unescaped would silently change match semantics
    v = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return v


class OrbitCLIClient:
    """Talks to a real Orbit index via the `orbit sql` command."""

    def __init__(self, cli_path: str = "orbit", timeout: int = 60) -> None:
        self.cli_path = cli_path
        self.timeout = timeout

    def available(self) -> bool:
        return shutil.which(self.cli_path) is not None

    def _run_sql(self, sql: str) -> List[dict]:
        proc = subprocess.run(
            [self.cli_path, "sql", "--format", "json", sql],
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"orbit sql failed (exit {proc.returncode}): {proc.stderr.strip()}"
            )
        out = proc.stdout.strip()
        if not out:
            return []
        data = json.loads(out)
        # Orbit may return either a bare list or {"rows": [...]}.
        if isinstance(data, dict) and "rows" in data:
            return list(data["rows"])
        if isinstance(data, list):
            return data
        raise ValueError(f"Unexpected orbit sql output shape: {type(data)!r}")

    def find_definitions(
        self, path: Optional[str] = None, name: Optional[str] = None
    ) -> List[dict]:
        clauses: List[str] = []
        # Prefer an exact path match; fall back to suffix match for convenience.
        if path:
            p = _sql_literal(path)
            p_like = _escape_like(p)
            clauses.append(f"(path = '{p}' OR path LIKE '%/{p_like}' ESCAPE '\\\\' )")
        if name:
            clauses.append(f"name = '{_sql_literal(name)}'")
        if not clauses:
            raise ValueError("find_definitions requires path and/or name")
        where = " AND ".join(clauses)
        sql = (
            "SELECT id, name, path, language, project_path "
            f"FROM gl_definition WHERE {where}"
        )
        return self._run_sql(sql)

    def dependents_of(self, target_ids: Iterable[int]) -> List[dict]:
        ids = sorted({int(i) for i in target_ids})
        if not ids:
            return []

        # B-2: chunk large IN (...) lists to avoid megabyte SQL strings
        # on monorepo-scale graphs. 500 ids per query is conservative.
        CHUNK_SIZE = 500
        results: dict[int, dict] = {}  # dedupe by id
        for i in range(0, len(ids), CHUNK_SIZE):
            chunk = ids[i:i + CHUNK_SIZE]
            id_list = ",".join(str(i) for i in chunk)
            sql = (
                "SELECT DISTINCT t2.id AS id, t2.name AS name, t2.path AS path, "
                "t2.language AS language, t2.project_path AS project_path "
                "FROM gl_definition t1 "
                "JOIN gl_reference ON t1.id = gl_reference.target_id "
                "JOIN gl_definition t2 ON gl_reference.source_id = t2.id "
                f"WHERE t1.id IN ({id_list})"
            )
            for row in self._run_sql(sql):
                rid = int(row["id"])
                if rid not in results:
                    results[rid] = row

        return list(results.values())


class InMemoryOrbitClient:
    """Fixture-backed client implementing the same contract.

    Accepts a graph of the form:
        {
          "definitions": [{id, name, path, language, project_path}, ...],
          "references":  [{source_id, target_id, relationship_type}, ...],
        }
    """

    def __init__(self, graph: Dict[str, list]) -> None:
        self._defs: Dict[int, dict] = {int(d["id"]): d for d in graph["definitions"]}
        self._refs: List[dict] = list(graph.get("references", []))

    def find_definitions(
        self, path: Optional[str] = None, name: Optional[str] = None
    ) -> List[dict]:
        if not path and not name:
            raise ValueError("find_definitions requires path and/or name")
        out = []
        for d in self._defs.values():
            if path is not None:
                dp = d["path"]
                if not (dp == path or dp.endswith("/" + path) or dp.endswith(path)):
                    continue
            if name is not None and d.get("name") != name:
                continue
            out.append(dict(d))
        return out

    def dependents_of(self, target_ids: Iterable[int]) -> List[dict]:
        targets = {int(i) for i in target_ids}
        source_ids = {
            int(r["source_id"]) for r in self._refs if int(r["target_id"]) in targets
        }
        return [dict(self._defs[s]) for s in sorted(source_ids) if s in self._defs]
