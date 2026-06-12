"""End-to-end CLI test against the offline fixture (#9)."""

import json
from pathlib import Path

from blast_radius.cli import main

FIXTURE = str(Path(__file__).parent / "fixtures" / "sample_graph.json")


def test_cli_text_output(capsys):
    rc = main(["src/auth/tokens.py", "--graph", FIXTURE, "--max-depth", "3"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "BLAST RADIUS: src/auth/tokens.py" in out
    assert "RISK SCORE:" in out


def test_cli_json_output(capsys):
    rc = main(["src/auth/tokens.py", "--graph", FIXTURE, "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert payload["target_path"] == "src/auth/tokens.py"
    assert "risk" in payload
    assert payload["total_dependents"] >= 3


def test_cli_zero_match_exit_code(capsys):
    rc = main(["nope.py", "--graph", FIXTURE])
    assert rc == 3
