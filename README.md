# Blast Radius — Dependency Impact Analysis for GitLab

**Don't guess what breaks. Mention. Analyze. Ship.**

Blast Radius maps the dependency chain before every code change. One mention — `@blast-radius src/auth/tokens.py` — and the agent traces every file that depends on your change: direct, transitive, across projects. GitLab-native, powered by Orbit's knowledge graph.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Hackathon: GitLab Transcend](https://img.shields.io/badge/hackathon-GitLab%20Transcend-orange)](https://gitlab-transcend.devpost.com/)

## The Visual

```
                  DIRECT (12 files)
                 /    |    \    \
              api   db   ui   sdk
             /  \   |    |    /  \
        cli  server  ·   ·  tests  worker
        ·     ·     ·   ·    ·      ·
      (Transitive: 47 files across 3 projects)
```

The tool's value is visual — the blast diagram IS the product. See the [website](https://perseus.observer/blast-radius/) for the interactive SVG.

## How It Works

```
@blast-radius src/auth/tokens.py --function checkToken
```

| Layer | Count | Example |
|---|---|---|
| **Direct Impact** | 12 files | `api/middleware.py` imports checkToken, `db/sessions.py` calls it on init |
| **Transitive Impact** | 47 files | `cli/main.py` depends on middleware, `server/app.py` depends on sessions |
| **Project Impact** | 3 projects | core-api, billing-service, notifications-service |
| **Risk Score** | HIGH | 59 total dependents |

## GitLab Native

Blast Radius plugs directly into GitLab Duo. No external services, no API keys.

- **Orbit Knowledge Graph** — traverses `gl_definition` nodes and `gl_reference` edges to map every dependency
- **MR Comment Integration** — results posted as structured comments in the MR thread
- **CI/CD Pipeline** — run in CI with a single include in `.gitlab-ci.yml`

```yaml
# .gitlab-ci.yml
include:
  - template: Workflows/MergeRequest-Pipelines.gitlab-ci.yml

blast_radius:
  stage: test
  script:
    - blast-radius $CI_MERGE_REQUEST_DIFF_BASE_SHA..$CI_MERGE_REQUEST_SOURCE_BRANCH_SHA
```

## Offline Fixture Mode

Blast Radius bundles an offline fixture mode. The dependency graph is pre-computed from a snapshot — demos run identically every time, regardless of network availability or Orbit API status. **This is a feature, not a workaround.** Hackathon judges see exactly the same thing every time — no live service dependency.

| Mode | How |
|---|---|
| **Live Orbit Query** | Real-time dependency traversal across active projects. Cypher-style `query_graph` and `get_graph_schema` tools. |
| **Offline Fixture** | Pre-computed graph snapshot. Zero network calls. Identical output every run. |

## Quick Start

```bash
# Install
pip install blast-radius-agent

# Scan with Orbit CLI
blast-radius src/auth/tokens.py --function checkToken

# Offline mode (no Orbit needed)
blast-radius src/auth/tokens.py --graph tests/fixtures/sample_graph.json --json

# In GitLab: add agent to AI Catalog (Project → AI → Agents)
# Then mention in any issue or MR: @blast-radius src/models/user.py
```

## Repository Structure

```
blast-radius-agent/
├── blast_radius/          # Local engine (Orbit CLI wrapper, cycle-safe traversal, risk scoring)
├── skills/blast-radius/   # Reusable agent skill (SKILL.md)
├── agent.yml              # GitLab Duo agent manifest
├── docs/                  # Architecture, Orbit contract, submission content
├── tests/                 # pytest suite + graph fixture
└── demo/                  # Demo script + terminal simulation
```

## License

MIT — see [LICENSE](LICENSE)

---

Built for the **GitLab Transcend Hackathon** — Showcase Track · [Website](https://perseus.observer/blast-radius/)
