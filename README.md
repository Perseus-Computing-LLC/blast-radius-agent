# Blast Radius Analyzer

**Trace cross-file dependencies before you break things.**

Every developer has shipped a change that broke something downstream — a function signature change that killed an import three projects away, a moved constant that crashed a service you forgot depended on it. CI caught it hours later.

Blast Radius Analyzer fixes this. It's a GitLab Duo custom agent powered by **GitLab Orbit's knowledge graph** that maps every dependency chain before you change code.

Mention `@blast-radius` with a file path in any issue or MR comment, and the agent traverses Orbit's dependency graph to show you:

- **Direct impact** — every file that imports your changed code
- **Transitive impact** — every file that depends on those dependents
- **Project impact** — which projects are in the blast radius
- **Risk score** — Low/Medium/High/Critical

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

```bash
# Install Orbit CLI (v1.x)
curl -fsSL "https://gitlab.com/gitlab-org/orbit/knowledge-graph/-/raw/v1.0.0/install.sh" | bash

# Index your project
orbit index /path/to/your/project

# Analyze blast radius
./bin/blast-radius-local.sh src/auth/tokens.py 3

# Or query manually
orbit sql "SELECT t2.name FROM gl_definition t1 JOIN gl_reference ON t1.id = gl_reference.target_id JOIN gl_definition t2 ON gl_reference.source_id = t2.id WHERE t1.path LIKE '%auth.py'"
```

## Repository Structure

```
blast-radius-agent/
├── README.md                    # This file
├── AGENTS.md                    # Context for AI agents working on this project
├── skills/
│   └── blast-radius/
│       └── SKILL.md             # Reusable blast-radius agent skill
├── docs/
│   ├── ARCHITECTURE.md          # Architecture diagrams and flow
│   └── SUBMISSION.md            # Devpost submission content
├── demo/
│   ├── demo_script.md           # 3-minute video script
│   └── demo_terminal.html       # Terminal simulation for demo video
└── assets/
    └── thumbnail.png            # Architecture diagram thumbnail
```

## License

MIT — see [LICENSE](LICENSE)

---

Built for the **GitLab Transcend Hackathon** — Showcase Track.  
Deadline: June 24, 2026 @ 2pm EDT.  
Devpost: [gitlab-transcend.devpost.com](https://gitlab-transcend.devpost.com/)
