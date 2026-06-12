# Architecture

## System Overview

```
Developer mentions @blast-radius in issue comment
  ↓
GitLab Duo Agent Platform routes mention to agent
  ↓
Agent receives file path + project context from AGENTS.md + skill
  ↓
Agent calls Orbit MCP: get_graph_schema → query_graph
  ↓
Orbit traverses knowledge graph (definitions → references → transitive)
  ↓
Agent assembles dependency chain + risk classification
  ↓
Agent posts risk report as issue comment via Create Issue Comment tool
```

## Component Architecture

```mermaid
graph TB
    DEV[👤 Developer]
    GL[GitLab Duo Agent Platform]
    AGENT[Blast Radius Analyzer Agent]
    SKILL[blast-radius SKILL.md]
    ORBIT[GitLab Orbit Knowledge Graph]
    CATALOG[GitLab AI Catalog]
    ISSUE[Issue/MR Comment]

    DEV -->|"@blast-radius src/auth.py"| ISSUE
    ISSUE -->|mentions agent| GL
    GL -->|routes to| AGENT
    AGENT -->|loads| SKILL
    AGENT -->|query_graph| ORBIT
    ORBIT -->|gl_definition nodes| AGENT
    ORBIT -->|gl_reference edges| AGENT
    AGENT -->|risk report| GL
    GL -->|"Create issue comment"| ISSUE
    ISSUE -->|report visible| DEV
    AGENT -.->|published to| CATALOG
```

## Data Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Issue as GitLab Issue
    participant Platform as Duo Agent Platform
    participant Agent as Blast Radius Agent
    participant Orbit as GitLab Orbit

    Dev->>Issue: "@blast-radius src/components/Auth.tsx"
    Issue->>Platform: mention event
    Platform->>Agent: dispatch with file path
    Agent->>Orbit: get_graph_schema()
    Orbit-->>Agent: {nodes: [gl_definition, gl_reference, ...]}
    Agent->>Orbit: query_graph("MATCH (d:gl_definition {path: 'src/components/Auth.tsx'})")
    Orbit-->>Agent: {definition: {id: 42, name: "Auth", ...}}
    Agent->>Orbit: query_graph("MATCH (s)-[r:gl_reference]->(d) WHERE d.id = 42")
    Orbit-->>Agent: {references: [{source: 55, target: 42}, ...]}
    Agent->>Orbit: query_graph("MATCH chain with transitive")
    Orbit-->>Agent: {transitive: [{source: 89, target: 55}, ...]}
    Agent->>Agent: assemble risk report + classify
    Agent->>Issue: Create issue comment with report
    Issue-->>Dev: View blast radius analysis
```

## Knowledge Graph Schema

Orbit represents code as a graph:

### Node Types

| Label | Description |
|---|---|
| `gl_definition` | A code definition: file, function, class, module, interface |
| `gl_documentation` | Documentation associated with a definition |

### Edge Types

| Label | Description |
|---|---|
| `gl_reference` | Source file references/depends on target file |
| `gl_documents` | Documentation relationship |

### gl_definition Properties

| Property | Type | Description |
|---|---|---|
| `id` | int | Unique identifier |
| `name` | string | Human-readable name (function/class name) |
| `path` | string | File path within the repository |
| `language` | string | Programming language (python, typescript, etc.) |
| `project_path` | string | GitLab project path |

### gl_reference Properties

| Property | Type | Description |
|---|---|---|
| `source_id` | int | The file doing the importing/referencing |
| `target_id` | int | The file being imported/referenced |
| `relationship_type` | string | import, call, extend, implement |

## Blast Radius Traversal Algorithm

```
function blast_radius(target_query, max_depth=3):
    # Phase 1: Resolve target
    targets = query_graph(
        "MATCH (d:gl_definition) WHERE d.path CONTAINS target_query " +
        "OR d.name = target_query RETURN d.id, d.path"
    )
    if targets is empty:
        return {error: "No matching definition found for '" + target_query + "'"}
    if len(targets) > 1:
        return {error: "Multiple matches (" + len(targets) + "). Use a more specific path: " +
                join([t.path for t in targets])}
    
    target = targets[0]
    visited = Set(target.id)
    all_dependents = List()
    
    # Phase 2: Direct dependents (depth 1)
    direct = query_graph(
        "MATCH (s)-[r:gl_reference]->(d:gl_definition) " +
        "WHERE d.id = " + target.id + " " +
        "RETURN DISTINCT s.id, s.path, s.project_path"
    )
    all_dependents = direct
    visited = visited + {d.id for d in direct}
    current_level = direct
    
    # Phase 3: Transitive dependents (depth 2..max_depth)
    for depth in 2 to max_depth:
        if current_level is empty:
            break  # No more dependents to traverse
        
        next_level = query_graph(
            "MATCH (s)-[r:gl_reference]->(d:gl_definition) " +
            "WHERE d.id IN " + [n.id for n in current_level] + " " +
            "AND NOT s.id IN " + visited + " " +  # Cycle detection
            "RETURN DISTINCT s.id, s.path, s.project_path"
        )
        
        all_dependents.extend(next_level)
        visited = visited + {n.id for n in next_level}
        current_level = next_level
    
    # Phase 4: Separate into direct vs transitive
    direct_set = {d.id for d in direct}
    transitive = [d for d in all_dependents if d.id not in direct_set]
    
    # Phase 5: Project impact
    projects = distinct(d.project_path for d in all_dependents)
    
    return classify_risk(direct, transitive, all_dependents, projects)
```

## Deployment

### GitLab AI Catalog

The agent is published to the GitLab AI Catalog as a public agent:
- Created via Project → AI → Agents → New Agent
- Visibility: Public (required for catalog publishing)
- Published to: [gitlab.com/explore/ai-catalog/agents/](https://gitlab.com/explore/ai-catalog/agents/)

### GitLab Duo Agent Platform Integration

- The agent is invoked through mentions in GitLab issues and MRs
- It has the "Create issue comment" tool enabled to post findings
- AGENTS.md provides project-level context loaded by the agent
- The blast-radius skill (SKILL.md) teaches the agent how to query Orbit

### Orbit Dependency

- **Remote**: GitLab.com group with Orbit Premium/Ultimate feature enabled
- **Local fallback**: Orbit CLI (`orbit index` + `orbit sql` queries)
- The agent detects available Orbit mode and adjusts queries accordingly
