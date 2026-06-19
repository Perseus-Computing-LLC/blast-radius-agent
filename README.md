# Blast Radius Analyzer

[![CI](https://github.com/Perseus-Computing-LLC/blast-radius-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Perseus-Computing-LLC/blast-radius-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Trace cross-file dependencies before you break things.**

### Links

- **Demo video:** https://youtube.com/watch?v=3tibXa-1udE
- **GitLab AI Catalog agent:** https://gitlab.com/gitlab-ai-hackathon/transcend/39104977/-/automate/agents/1010753/
- **GitLab project:** https://gitlab.com/gitlab-ai-hackathon/transcend/39104977

Every developer has shipped a change that broke something downstream — a function signature change that killed an import three projects away, a moved constant that crashed a service you forgot depended on it. CI caught it hours later.

Blast Radius Analyzer fixes this. It's a GitLab Duo custom agent powered by **GitLab Orbit's knowledge graph** that maps every dependency chain before you change code.

Mention `@blast-radius` with a file path in any issue or MR comment, and the agent traverses Orbit's dependency graph to show you:

- **Direct impact** — every file that imports your changed code
- **Transitive impact** — every file that depends on those dependents
- **Project impact** — which projects are in the blast radius
- **Risk score** — Low/Medium/High/Critical

## How It Runs

Blast Radius Analyzer has two run modes, and both ship in this repo:

- **Demo / evaluation mode (default, no Orbit needed):** the engine runs against
  an in-memory graph fixture (`tests/fixtures/sample_graph.json`). This is what
  the test suite and the demo path exercise, so reviewers can clone and run the
  full analysis offline with zero external services. The demo video uses a
  terminal *simulation* (`demo/demo_terminal.html`) for a clean recording — it
  is clearly labeled as such.
- **Live mode:** the same engine shells out to `orbit sql` against an
  Orbit-indexed repository (`blast_radius/orbit_client.py` → `OrbitCLIClient`).
  Point it at a real Orbit graph and it traverses production dependency data.

The traversal, cycle handling, and risk scoring are identical in both modes —
only the graph source changes. Offline-first is a deliberate choice so the
project is fully evaluable without provisioning Orbit.

## Demo

```
Developer: @blast-radius src/auth/tokens.py -- checkToken function

@blast-radius:
  DIRECT IMPACT (3 files):
  - src/api/middleware.ts:47 — imports checkToken
  - src/graphql/resolvers.ts:112 — calls checkToken via auth middleware
  - src/webhooks/stripe.ts:89 — validates webhook tokens

  TRANSITIVE IMPACT (12 files):
  - src/api/routes/*.ts — all routes use middleware
  - src/graphql/schema/*.ts — schema files import resolvers
  - 3 downstream microservices import the webhook handler

  PROJECT IMPACT: core-api, billing-service, notifications-service
  RISK SCORE: HIGH — 15 dependents across 3 projects

  Recommended: notify @backend-team before landing this change.
```

## How It Works

Blast Radius Analyzer is a **custom agent** on the GitLab Duo Agent Platform. It uses GitLab Orbit's knowledge graph to traverse code dependencies:

1. Developer mentions `@blast-radius <file-path>` in a GitLab issue or MR
2. Agent queries Orbit's `query_graph` to find all `gl_definition` nodes for the target file
3. Traverses `gl_reference` edges backwards to find all callers and importers
4. Recursively traverses to find transitive dependents
5. Assembles a risk report and posts it as a comment

## Tech Stack

- **GitLab Duo Agent Platform** — custom agent hosting and invocation
- **GitLab Orbit** — knowledge graph of the codebase (definitions, references, relationships)
- **Agent Skills** — reusable skill files following the [Agent Skills spec](https://agentskills.io/specification)
- **Orbit CLI** — local fallback using `orbit sql` for projects without Orbit Remote

## Quick Start

### Prerequisites

- GitLab account with access to a group that has Orbit enabled (or Orbit CLI installed locally)
- A project with the Blast Radius Analyzer agent enabled

### Setup

1. **Enable the agent** in your GitLab project: Project → AI → Agents → Enable "Blast Radius Analyzer"
2. **Use in any issue or MR**: Comment `@blast-radius src/components/Auth.tsx`
3. **Read the report**: Agent posts a dependency analysis as a comment

### Run Locally with Orbit CLI

The repo ships a real local engine (`blast_radius/`) that wraps the Orbit CLI
and implements cycle-safe, depth-limited traversal with deterministic risk
scoring. It has zero third-party runtime dependencies.

```bash
# 1. Install the local engine
pip install -e .

# 2. Install the Orbit CLI from a pinned release (do NOT pipe curl to bash from
#    a mutable branch). Use the official package or a versioned release asset:
#    https://gitlab.com/gitlab-org/orbit/knowledge-graph/-/releases
#    e.g. download the release for your platform, verify its checksum, then:
#    chmod +x orbit && sudo mv orbit /usr/local/bin/
# Install Orbit CLI (v1.x)
curl -fsSL "https://gitlab.com/gitlab-org/orbit/knowledge-graph/-/raw/v1.0.0/install.sh" | bash

# 3. Index your project
orbit index /path/to/your/project

# 4. Analyze blast radius
blast-radius src/auth/tokens.py --function checkToken
#   or, fully offline against a graph fixture (no Orbit needed):
blast-radius src/auth/tokens.py --graph tests/fixtures/sample_graph.json --json
# Analyze blast radius
./bin/blast-radius-local.sh src/auth/tokens.py 3

# Or query manually
orbit sql "SELECT t2.name FROM gl_definition t1 JOIN gl_reference ON t1.id = gl_reference.target_id JOIN gl_definition t2 ON gl_reference.source_id = t2.id WHERE t1.path LIKE '%auth.py'"
```

Configuration is read from `.env` (see `.env.example`): Orbit mode, CLI path,
max traversal depth, risk thresholds, and exclude patterns.

## Repository Structure

```
blast-radius-agent/
├── README.md                    # This file
├── AGENTS.md                    # Context for AI agents working on this project
├── agent.yml                    # Deployable GitLab Duo agent manifest
├── pyproject.toml               # Package metadata + `blast-radius` entrypoint
├── blast_radius/                # Local engine (Orbit CLI wrapper, traversal, risk)
│   ├── cli.py                   # `blast-radius` / `python -m blast_radius`
│   ├── engine.py                # Cycle-safe, depth-limited traversal
│   ├── orbit_client.py          # Orbit CLI + in-memory fixture clients
│   ├── risk.py                  # Deterministic risk classification
│   └── config.py                # .env-driven configuration
├── skills/
│   └── blast-radius/
│       └── SKILL.md             # Reusable blast-radius agent skill
├── docs/
│   ├── ARCHITECTURE.md          # Architecture diagrams and flow
│   ├── ORBIT_CONTRACT.md        # Orbit/Duo tool contract (SQL vs Cypher modes)
│   └── SUBMISSION.md            # Devpost submission content
├── scripts/
│   └── validate_skill.py        # CI validation for skill/manifest/fixture
├── tests/                       # pytest suite + graph fixture
├── demo/
│   ├── demo_script.md           # 3-minute video script
│   └── demo_terminal.html       # Terminal SIMULATION for demo video
└── assets/
    └── thumbnail.png            # Architecture diagram thumbnail
```



## Future: GitHub + Local Support

Blast Radius currently requires GitLab Orbit for code graph data. Tree-sitter support
is planned (see [#45](https://github.com/tcconnally/blast-radius-agent/issues/45))
to enable analysis on any codebase without GitLab:

- Walk local file tree with tree-sitter
- Extract symbol definitions and references
- Build in-memory graph matching the Orbit contract
- Works on GitHub, Bitbucket, and local-only repos

### Docker

```bash
docker build -t blast-radius .
docker run blast-radius src/myfile.py --function main
```

## License

MIT — see [LICENSE](LICENSE)

---

Built for the **GitLab Transcend Hackathon** — Showcase Track.  
Deadline: June 24, 2026 @ 2pm EDT.  
Devpost: [gitlab-transcend.devpost.com](https://gitlab-transcend.devpost.com/)
