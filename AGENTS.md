# Blast Radius Analyzer — Project Context

## Purpose

This is the managing project for the **Blast Radius Analyzer** — a GitLab Duo custom agent that uses GitLab Orbit's knowledge graph to map dependency chains before code changes.

The agent is published to the GitLab AI Catalog and can be enabled on any project.

## How the Agent Works

When a developer mentions `@blast-radius <file-path>` in an issue or MR comment:

1. Agent receives the mention with the file path
2. Agent queries GitLab Orbit's knowledge graph:
   - Uses `query_graph` to find the file's `gl_definition` node
   - Traverses `gl_reference` edges to find all dependents
   - Recursively traverses for transitive dependents
3. Assembles a structured risk report with direct impact, transitive impact, project impact, and risk score
4. Posts the report as a comment on the issue/MR

## Orbit Integration

### Remote (GitLab.com with Orbit enabled)

The agent connects to Orbit's MCP interface at the group level:
- Tool: `query_graph` — traverses the knowledge graph using Cypher-style queries
- Tool: `get_graph_schema` — lists available node types and relationships

Key graph relationships:
- `gl_definition` nodes represent files, functions, classes, modules
- `gl_reference` edges connect definitions (source → target)
- Reverse traversal on `gl_reference` reveals everything that depends on a given definition

### Local (Orbit CLI fallback)

When Orbit Remote isn't available, the bundled local engine wraps the Orbit CLI.
It emits the SQL dialect (not Cypher — see `docs/ORBIT_CONTRACT.md`) and adds
cycle-safe traversal, exclude filtering, and deterministic risk scoring:
```bash
# High-level (recommended): resolves the target, traverses, scores risk
blast-radius src/auth/tokens.py --function checkToken

# Low-level (what the engine runs under the hood):
orbit sql "SELECT t2.path FROM gl_definition t1 JOIN gl_reference ON t1.id = gl_reference.target_id JOIN gl_definition t2 ON gl_reference.source_id = t2.id WHERE t1.path LIKE '%target_file%'"
```

## Agent Configuration

The agent is created in the GitLab UI: Project → AI → Agents → New Agent

**System Prompt** (see the agent definition in the GitLab AI Catalog):
```
You are a dependency analysis expert. Your job is to help developers understand
the blast radius of code changes before they make them.

When a developer gives you a file path or function name, use GitLab Orbit's
knowledge graph to trace all dependencies:
1. Call get_graph_schema to understand available node types
2. Use query_graph to find where this file/function is defined and what depends on it
3. Summarize findings in a clear risk report

Organize your response as:
- DIRECT IMPACT: Files that directly reference the changed code
- TRANSITIVE IMPACT: Files that depend on direct dependents
- PROJECT IMPACT: Projects affected
- RISK SCORE: Low/Medium/High/Critical based on dependency depth
```

**Tools Enabled:** Create issue comment (to post findings)

## Skill

The reusable blast-radius skill is at `skills/blast-radius/SKILL.md`. It follows the [Agent Skills specification](https://agentskills.io/specification) and can be loaded by any agent that needs to perform dependency analysis.

## Development

- The agent skill file is versioned in this repo
- Changes to `SKILL.md` require a new conversation/flow to avoid context confusion
- Test the agent in the GitLab Duo sidebar by selecting it and querying sample file paths

## Submission

This project is submitted to the **GitLab Transcend Hackathon** — Showcase Track.
- Devpost: https://gitlab-transcend.devpost.com/
- GitLab Contributor Platform: https://contributors.gitlab.com/transcend-hackathon
- AI Catalog: https://gitlab.com/explore/ai-catalog/agents/
