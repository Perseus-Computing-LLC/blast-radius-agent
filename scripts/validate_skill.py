#!/usr/bin/env python3
"""Lightweight validation for skill frontmatter, the agent manifest, and the
Orbit fixture (issue #9). Exits non-zero on any problem so CI can gate on it.

No third-party dependencies: parses the small YAML frontmatter by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def validate_skill_frontmatter() -> None:
    skill = ROOT / "skills" / "blast-radius" / "SKILL.md"
    if not skill.exists():
        fail(f"missing {skill}")
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---"):
        fail("SKILL.md must start with YAML frontmatter (---)")
    _, fm, _ = text.split("---", 2)
    keys = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            keys[k.strip()] = v.strip()
    for required in ("name", "description"):
        if required not in keys or not keys[required]:
            fail(f"SKILL.md frontmatter missing '{required}'")
    if keys["name"] != "blast-radius":
        fail(f"SKILL.md name should be 'blast-radius', got {keys['name']!r}")
    print("ok: SKILL.md frontmatter")


def validate_manifest() -> None:
    manifest = ROOT / "agent.yml"
    if not manifest.exists():
        fail("missing agent.yml manifest")
    text = manifest.read_text(encoding="utf-8")
    for needed in ("get_graph_schema", "query_graph", "create_issue_comment"):
        if needed not in text:
            fail(f"agent.yml does not declare required tool {needed!r}")
    print("ok: agent.yml manifest")


def validate_fixture() -> None:
    fx = ROOT / "tests" / "fixtures" / "sample_graph.json"
    if not fx.exists():
        fail("missing tests/fixtures/sample_graph.json")
    data = json.loads(fx.read_text(encoding="utf-8"))
    if "definitions" not in data or "references" not in data:
        fail("fixture must have 'definitions' and 'references'")
    ids = {d["id"] for d in data["definitions"]}
    for ref in data["references"]:
        for side in ("source_id", "target_id"):
            if ref[side] not in ids:
                fail(f"reference {side}={ref[side]} has no matching definition")
    print("ok: fixture integrity")


def main() -> int:
    validate_skill_frontmatter()
    validate_manifest()
    validate_fixture()
    print("All validations passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
