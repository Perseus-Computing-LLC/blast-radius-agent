# Orbit / Duo Tool Contract

This document defines the exact contract the agent and the local engine rely on,
so automation can be built and validated against it (issue #5). It also settles
the dialect confusion between the SQL and Cypher examples (issue #2).

## Two modes, two dialects

The agent runs in one of two modes. They use different query dialects, and the
docs previously mixed them. The rule is:

| Mode | Backend | Dialect | Tools |
|---|---|---|---|
| **Remote** | Orbit on GitLab.com (Premium/Ultimate) | Cypher-style via `query_graph` | `get_graph_schema`, `query_graph`, `create_issue_comment` |
| **Local** | Orbit CLI on disk | Orbit **SQL** via `orbit sql` | `blast-radius` CLI (`python -m blast_radius`) |

- In **Remote** mode the agent passes Cypher-style `MATCH` strings to
  `query_graph`. These are illustrative; confirm the accepted grammar against
  your Orbit version.
- In **Local** mode the engine emits the SQL shown in the skill and runs it via
  `orbit sql --format json`. This is the dialect that is fully specified and
  tested here.

Demo/terminal output uses Cypher-style strings purely for illustration and is
labeled as simulated (issue #12). Do not treat demo strings as an executable
contract.

## Graph schema

### Node: `gl_definition`

| Property | Type | Notes |
|---|---|---|
| `id` | int | Unique within an index |
| `name` | string | Function/class/module name |
| `path` | string | File path within the project |
| `language` | string | e.g. `python`, `typescript` |
| `project_path` | string | GitLab project path |

### Edge: `gl_reference`

| Property | Type | Notes |
|---|---|---|
| `source_id` | int | The definition doing the referencing |
| `target_id` | int | The definition being referenced |
| `relationship_type` | string | `import`, `call`, `extend`, `implement` |

**Direction:** `source` depends on `target`. To find *dependents* of a target,
walk edges **backward**: `gl_reference.target_id = <target>` → collect
`source_id`.

## `query_graph` / `orbit sql` row shape

Both backends must return rows as JSON objects with the `gl_definition`
properties above. The local engine accepts either a bare JSON list or
`{"rows": [...]}`.

## Required tools (Remote mode)

| Tool | Provider | Purpose |
|---|---|---|
| `get_graph_schema` | orbit | Discover node/edge types |
| `query_graph` | orbit | Traverse the graph |
| `create_issue_comment` | gitlab | Post the report |

## Fixtures

`tests/fixtures/sample_graph.json` is a canonical fixture implementing this
contract, including a deliberate cycle to exercise cycle-safety. The test suite
and the offline demo (`--graph`) both run against it, so the contract is
executable, not just documented.
