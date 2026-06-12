# Devpost Submission — Blast Radius Analyzer

## Project Name

Blast Radius Analyzer

## Elevator Pitch (200 chars max)

See exactly what breaks before you change code. Blast Radius Analyzer uses GitLab Orbit's knowledge graph to map every dependency chain — from your file to every project that depends on it.

## What It Does

Blast Radius Analyzer is a GitLab Duo custom agent that helps developers understand the downstream impact of code changes before they make them. When a developer mentions `@blast-radius` with a file path in a GitLab issue or MR comment, the agent:

1. Queries GitLab Orbit's knowledge graph to locate the file's definition
2. Traverses all `gl_reference` edges to find every file, function, and module that depends on it
3. Recursively traces transitive dependencies — files that depend on the direct dependents
4. Identifies cross-project impact across the entire codebase
5. Classifies risk as Low/Medium/High/Critical based on dependency depth and spread
6. Posts a structured risk report as an issue comment, including direct impact, transitive impact, project impact, and actionable recommendations

## The Problem

Every developer has broken something by missing a downstream dependency. A function signature change crashes an import three projects away. A moved constant kills a service you forgot depended on it. CI catches it hours later — after you've moved on to other work.

Study data shows that cross-file dependency breaks are a leading cause of production incidents in microservice architectures. With monorepos and microservice architectures becoming standard, the blast radius of any single change has grown exponentially. Existing tools (IDE find-references, code search) show immediate callers but collapse under transitive chains and cross-project dependencies.

There is no tool that answers the question every developer asks before landing a change: "What will this break?"

## How I Built It

**Platform:** GitLab Duo Agent Platform — custom agent hosting, invocation via issue/MR mentions, and tool enablement for posting comments.

**Knowledge Graph:** GitLab Orbit — the structured, queryable codebase representation. The agent uses two MCP tools:
- `get_graph_schema` — discovers available node types (gl_definition, gl_reference) and their properties
- `query_graph` — traverses the dependency graph using Cypher-style graph queries to find definitions, trace references forward and backward, and compute transitive closure

**Agent Skill:** A reusable skill file (`skills/blast-radius/SKILL.md`) following the Agent Skills specification. This teaches any Duo agent how to perform blast-radius analysis using Orbit's graph interface. The skill includes precise query patterns for direct dependencies, transitive traversal, cross-project impact assessment, and risk classification rules.

**Agent Configuration:** Created via the GitLab AI → Agents interface with a system prompt that establishes the agent as a dependency analysis expert. The AGENTS.md file provides project-level context about Orbit query patterns and graph traversal strategies.

**Architecture:**
- Developer mentions `@blast-radius <file-path>` in an issue or MR
- GitLab Duo Agent Platform routes the mention to the Blast Radius Analyzer agent
- Agent loads the blast-radius skill and queries Orbit's knowledge graph
- Traversal algorithm finds definitions → direct references → transitive references (depth-limited to prevent cycles)
- Risk classifier assigns Low/Medium/High/Critical based on dependency count and project spread
- Report is formatted and posted back to the issue via the "Create issue comment" tool

## Why GitLab Orbit

GitLab Orbit is the critical enabler that makes blast radius analysis possible at scale. Before Orbit, dependency analysis required:
- Grep/search for import statements (misses transitive chains, dynamic references, cross-project links)
- IDE "find all references" (limited to open projects, no cross-repository awareness)
- Manual code review (slow, error-prone, doesn't scale)

Orbit's knowledge graph provides a single, queryable source of truth for all code relationships across all projects. Its graph structure (gl_definition nodes connected by gl_reference edges) maps perfectly to the dependency traversal problem. A reverse graph walk from any definition reveals everything that depends on it — exactly what blast radius analysis needs.

The agent uses Orbit meaningfully — not just surface-level search, but recursive graph traversal with depth control, cycle detection, and cross-project scope awareness. This is the kind of analysis that only becomes practical when code is represented as a queryable graph.

## Design and Usability

The design principle is **zero-friction**. There is no UI to learn, no configuration file, no setup beyond enabling the agent. The developer's workflow doesn't change:

1. They write code (or plan to)
2. They mention `@blast-radius` with a file path
3. They get a report

The interaction happens where developers already spend their time — in GitLab issues and MRs. The response format is structured and scannable: direct impact first (what you need to know immediately), then transitive impact (what's behind it), then project scope and risk classification.

The risk score system (Low/Medium/High/Critical) maps to developer intuition. Low risk means "ship it." High risk means "notify the team." Critical means "this touches a shared library used by half the org — plan the rollout."

## What's Next

1. **Visual dependency graph** — Render the blast radius as a Mermaid/Graphviz diagram in the issue comment, showing nodes and edges so developers can see the structure at a glance
2. **CI gate integration** — Add a CI job that runs blast radius analysis on every MR and blocks merge if risk is Critical without explicit review
3. **IDE integration** — Surface blast radius in-editor (VS Code extension) so developers see dependency impact as they type
4. **Historical analysis** — Track blast radius changes over time to identify files that are becoming dangerous hubs (the "hotspot" pattern)
5. **Scheduled audits** — Weekly blast radius scans of high-churn directories to surface risky dependency patterns before they become incidents

## Open Source

MIT License — see [GitHub repository](https://github.com/tcconnally/blast-radius-agent).

## Built For

**GitLab Transcend Hackathon — Showcase Track**  
[gitlab-transcend.devpost.com](https://gitlab-transcend.devpost.com/)
