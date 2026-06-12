"""Engine tests: target resolution (#7) and cycle-safe traversal (#8)."""

import json
from pathlib import Path

import pytest

from blast_radius.config import Config
from blast_radius.engine import BlastRadiusEngine, TargetResolutionError
from blast_radius.orbit_client import InMemoryOrbitClient

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph.json"


def make_engine(max_depth=3, excludes=None):
    graph = json.loads(FIXTURE.read_text(encoding="utf-8"))
    client = InMemoryOrbitClient(graph)
    config = Config(max_depth=max_depth, exclude_patterns=excludes or [])
    return BlastRadiusEngine(client, config)


def test_direct_dependents_resolved():
    engine = make_engine(max_depth=1)
    report = engine.analyze(path="src/auth/tokens.py")
    paths = {d.path for d in report.direct}
    # middleware, resolvers, stripe, tokens_test, cycleA all reference checkToken
    assert "src/api/middleware.ts" in paths
    assert "src/graphql/resolvers.ts" in paths
    assert "src/webhooks/stripe.ts" in paths


def test_exclude_patterns_filter_tests():
    engine = make_engine(max_depth=1, excludes=["*test*"])
    report = engine.analyze(path="src/auth/tokens.py")
    paths = {d.path for d in report.direct}
    assert "src/auth/tokens_test.py" not in paths


def test_transitive_traversal_is_deduplicated_and_cycle_safe():
    # The fixture contains a 10<->11 cycle; traversal must terminate and not
    # double-count any node.
    engine = make_engine(max_depth=5)
    report = engine.analyze(path="src/auth/tokens.py")
    all_ids = [d.id for d in report.direct + report.transitive]
    assert len(all_ids) == len(set(all_ids)), "no node may appear twice"
    # Target itself (id 1) is never a dependent.
    assert 1 not in set(all_ids)


def test_depth_is_respected():
    shallow = make_engine(max_depth=1).analyze(path="src/auth/tokens.py")
    deep = make_engine(max_depth=3).analyze(path="src/auth/tokens.py")
    assert len(deep.transitive) >= len(shallow.transitive)
    assert shallow.transitive == []  # depth 1 = direct only


def test_zero_match_raises():
    engine = make_engine()
    with pytest.raises(TargetResolutionError):
        engine.analyze(path="does/not/exist.py")


def test_ambiguous_path_requires_disambiguation():
    # Two distinct files share the "a.py"/"b.py" suffix pattern? Use cycle dir.
    graph = {
        "definitions": [
            {"id": 1, "name": "x", "path": "src/one/util.py", "language": "python", "project_path": "p"},
            {"id": 2, "name": "y", "path": "src/two/util.py", "language": "python", "project_path": "p"},
        ],
        "references": [],
    }
    engine = BlastRadiusEngine(InMemoryOrbitClient(graph), Config())
    with pytest.raises(TargetResolutionError):
        engine.analyze(path="util.py")  # matches two files, no name given


def test_ambiguous_resolved_by_function_name():
    graph = {
        "definitions": [
            {"id": 1, "name": "alpha", "path": "src/one/util.py", "language": "python", "project_path": "p"},
            {"id": 2, "name": "beta", "path": "src/two/util.py", "language": "python", "project_path": "p"},
        ],
        "references": [],
    }
    engine = BlastRadiusEngine(InMemoryOrbitClient(graph), Config())
    report = engine.analyze(path="util.py", name="alpha")
    assert report.target_name == "alpha"


def test_projects_collected_distinct():
    report = make_engine(max_depth=3).analyze(path="src/auth/tokens.py")
    assert "core-api" in report.projects
    assert "billing-service" in report.projects
    assert len(report.projects) == len(set(report.projects))
