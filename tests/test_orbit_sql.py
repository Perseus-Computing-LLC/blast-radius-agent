"""Regression tests for OrbitCLIClient SQL construction.

The generated SQL is executed against a real SQLite engine (same dialect
family as Orbit's SQL surface for the constructs used here), so these
tests verify behavior — not just string shape.
"""

import sqlite3

import pytest

from blast_radius.orbit_client import OrbitCLIClient, _like_literal


ROWS = [
    (1, "login", "src/auth_session.py", "python", "proj-a"),
    (2, "login", "src/authXsession.py", "python", "proj-a"),
    (3, "login", "src/auth%session.py", "python", "proj-a"),
    (4, "render", "lib/render.py", "python", "proj-b"),
]


@pytest.fixture()
def sql_client(monkeypatch):
    """OrbitCLIClient whose _run_sql executes against in-memory SQLite."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE gl_definition "
        "(id INTEGER, name TEXT, path TEXT, language TEXT, project_path TEXT)"
    )
    conn.executemany("INSERT INTO gl_definition VALUES (?,?,?,?,?)", ROWS)

    client = OrbitCLIClient()
    monkeypatch.setattr(
        client, "_run_sql", lambda sql: [dict(r) for r in conn.execute(sql)]
    )
    yield client
    conn.close()


def test_underscore_in_path_is_not_a_wildcard(sql_client):
    matches = sql_client.find_definitions(path="auth_session.py")
    assert [m["path"] for m in matches] == ["src/auth_session.py"]


def test_percent_in_path_is_not_a_wildcard(sql_client):
    matches = sql_client.find_definitions(path="auth%session.py")
    assert [m["path"] for m in matches] == ["src/auth%session.py"]


def test_exact_and_suffix_matching_still_work(sql_client):
    assert len(sql_client.find_definitions(path="src/auth_session.py")) == 1
    assert len(sql_client.find_definitions(path="render.py")) == 1


def test_quote_in_path_does_not_break_query(sql_client):
    # No injection and no syntax error — just zero matches.
    assert sql_client.find_definitions(path="x'; DROP TABLE gl_definition;--") == []
    # Table still intact afterwards.
    assert len(sql_client.find_definitions(path="render.py")) == 1


def test_like_literal_escapes_metacharacters():
    assert _like_literal("a_b%c\\d'e") == "a\\_b\\%c\\\\d''e"
